# Date Fields and Date Calculations

pytaskwarrior passes date strings directly to TaskWarrior. TaskWarrior accepts a rich variety of formats: ISO-8601 strings, named synonyms (`"eom"`, `"friday"`), and relative expressions (`"due+2d"`). Returned dates are parsed into Python `datetime` objects on `TaskOutputDTO`.

---

## Date Fields

### TaskInputDTO — input fields (strings)

| Field | Description |
|-------|-------------|
| `due` | Latest date by which the task must be completed |
| `scheduled` | Earliest date the task can be started |
| `wait` | Task is hidden from pending list until this date |
| `until` | Task auto-deletes on this date (use with care) |

All four fields accept the same date formats listed below. They are `str | None` — pass any TaskWarrior-valid date string.

```python
from pytaskwarrior import TaskWarrior, TaskInputDTO

tw = TaskWarrior()

task = TaskInputDTO(
    description="Send birthday card to Alice",
    due="2026-11-08",
    scheduled="2026-11-04",   # earliest I can work on it
    wait="november",          # hidden until 2026-11-01
    until="2026-11-10",       # auto-deletes if not done by then
)
tw.add_task(task)
```

### TaskOutputDTO — returned fields (datetime objects)

| Field | Description |
|-------|-------------|
| `due` | Due date as `datetime \| None` |
| `scheduled` | Scheduled date as `datetime \| None` |
| `wait` | Wait date as `datetime \| None` |
| `until` | Until date as `datetime \| None` |
| `entry` | Creation timestamp (read-only) |
| `start` | When the task was started (read-only) |
| `end` | When the task was completed or deleted (read-only) |
| `modified` | Last modification timestamp (read-only) |

```python
task = tw.get_task(uuid)

if task.due:
    days_left = (task.due - datetime.now()).days
    print(f"Due in {days_left} days")

if task.scheduled and task.scheduled > datetime.now():
    print("Task is not yet ready to start")
```

---

## Accepted Date Formats

### ISO-8601

The most explicit format. Recommended for programmatic use.

```python
task = TaskInputDTO(description="Meeting", due="2026-06-15")
task = TaskInputDTO(description="Meeting", due="2026-06-15T09:30:00")
task = TaskInputDTO(description="Meeting", due="2026-06-15T09:30:00+02:00")  # with timezone
```

Common ISO patterns:

| Pattern | Example | Meaning |
|---------|---------|---------|
| `YYYY-MM-DD` | `2026-06-15` | Date, time 00:00:00 local |
| `YYYY-MM-DDThh:mm:ss` | `2026-06-15T09:30:00` | Date + time, local |
| `YYYY-MM-DDThh:mm:ssZ` | `2026-06-15T09:30:00Z` | Date + time, UTC |
| `YYYY-MM-DDThh:mm:ss+hh:mm` | `2026-06-15T09:30:00+02:00` | Date + time, with offset |
| `YYYY-Www` | `2026-W24` | First day of ISO week |
| `YYYY-MM` | `2026-06` | First day of month |

### Duration / Offset Expressions

TaskWarrior accepts ISO 8601 duration strings as relative offsets from now.

| Expression | Meaning |
|------------|---------|
| `P1D` | 1 day from now |
| `P1W` | 1 week from now |
| `P2W` | 2 weeks from now |
| `P1M` | 1 month from now |
| `P1Y` | 1 year from now |
| `PT2H` | 2 hours from now |
| `P1DT4H` | 1 day and 4 hours from now |

```python
task = TaskInputDTO(description="Follow-up", due="P2W")     # due in 2 weeks
task = TaskInputDTO(description="Reminder", wait="P3D")     # hidden for 3 days
```

### Named Synonyms

Human-friendly date names that TaskWarrior resolves at task creation/modification time.

**Relative days / weeks:**

| Synonym | Meaning |
|---------|---------|
| `now` | Current date and time |
| `today` | Today at 00:00:00 |
| `sod` | Start of day (= today) |
| `eod` | Today at 23:59:59 |
| `yesterday` | Yesterday at 00:00:00 |
| `tomorrow` | Tomorrow at 00:00:00 |

**Days of the week** — resolves to the *next* occurrence of that day:

```python
task = TaskInputDTO(description="Weekly review", due="friday")
task = TaskInputDTO(description="Stand-up", due="monday")
# Abbreviated forms also work: "mon", "tue", "wed", "thu", "fri", "sat", "sun"
```

**Month boundaries:**

| Synonym | Meaning |
|---------|---------|
| `som` | Start of current month |
| `eom` | End of current month (23:59:59) |
| `sonm` | Start of next month |
| `eonm` | End of next month |
| `sopm` | Start of previous month |
| `eopm` | End of previous month |

**Quarter / year:**

| Synonym | Meaning |
|---------|---------|
| `soq` / `eoq` | Start / end of current quarter |
| `soy` / `eoy` | Start / end of current year |
| `sonq` / `eonq` | Start / end of next quarter |
| `sony` / `eony` | Start / end of next year |

**Week:**

| Synonym | Meaning |
|---------|---------|
| `sow` / `eow` | Start / end of current week (Mon–Sun) |
| `soww` / `eoww` | Start / end of current *work* week (Mon–Fri) |
| `sonw` / `eonw` | Start / end of next week |
| `sopw` / `eopw` | Start / end of previous week |

**Month names** — resolves to the 1st of the *next* month with that name:

```python
task = TaskInputDTO(description="Holiday prep", wait="november")  # 2026-11-01
task = TaskInputDTO(description="Tax filing", due="january")       # next January 1st
# Abbreviated: "jan", "feb", "mar", "apr", "may", "jun",
#              "jul", "aug", "sep", "oct", "nov", "dec"
```

**Day ordinals** — next occurrence of that day-of-month:

```python
task = TaskInputDTO(description="Pay rent", due="1st")    # next 1st of the month
task = TaskInputDTO(description="Review", due="15th")     # next 15th
```

**Special:**

| Synonym | Meaning |
|---------|---------|
| `later` / `someday` | December 30, 9999 — indefinitely deferred |
| `easter` | Next Easter Sunday |
| `goodfriday` | Next Good Friday |

---

## Relative Expressions (DOM-based)

At task creation, you can define dates relative to other date fields using arithmetic. This is evaluated only once at creation time.

```python
# All relative to the due date — evaluated at add time
task = TaskInputDTO(
    description="Project deliverable",
    due="2026-09-30",
    scheduled="due-7d",    # 1 week before due
    wait="due-14d",        # start appearing 2 weeks before due
    until="due+3d",        # auto-delete 3 days after due if not done
)
tw.add_task(task)
```

**Important:** If you later change `due`, the other dates are **not** recalculated automatically. You must update them explicitly with `tw.modify_task(...)`.

---

## task_calc() — Evaluating Date Expressions

Use `task_calc()` to resolve any date expression to an ISO datetime string, using TaskWarrior's own engine.

```python
tw = TaskWarrior()

# Resolve named synonyms
print(tw.task_calc("eom"))           # e.g. "2026-02-28T23:59:59"
print(tw.task_calc("friday"))        # e.g. "2026-03-06T00:00:00"
print(tw.task_calc("now + 2weeks"))  # e.g. "2026-03-13T09:15:00"
print(tw.task_calc("P1M"))           # e.g. "2026-03-28T09:15:00"

# Arithmetic on dates
print(tw.task_calc("2026-06-15 + 30d"))  # "2026-07-15T00:00:00"
print(tw.task_calc("2026-06-15 - 1w"))   # "2026-06-08T00:00:00"
```

Useful to preview exactly which date a synonym resolves to, or to calculate deadlines dynamically before building a `TaskInputDTO`.

```python
from datetime import datetime

raw = tw.task_calc("eom")
end_of_month = datetime.fromisoformat(raw)
days_remaining = (end_of_month - datetime.now()).days
print(f"{days_remaining} days left in this month")
```

---

## date_validator() — Validating Date Strings

Use `date_validator()` to check whether a string is a valid TaskWarrior date expression before using it in a DTO.

```python
tw.date_validator("2026-06-15")      # True  — valid ISO date
tw.date_validator("friday")          # True  — valid synonym
tw.date_validator("eom")             # True  — valid synonym
tw.date_validator("P2W")             # True  — valid ISO duration
tw.date_validator("next monday")     # True  — valid expression
tw.date_validator("invalid-date")    # False — not recognized
tw.date_validator("32nd")            # False — no 32nd day
```

Typical use: validate user-supplied input before creating a task.

```python
user_input = input("Due date: ")
if tw.date_validator(user_input):
    task = TaskInputDTO(description="Task", due=user_input)
    tw.add_task(task)
else:
    print(f"'{user_input}' is not a valid date expression.")
```

---

## Filtering Tasks by Date

Use TaskWarrior filter syntax in `get_tasks()`:

```python
# Tasks due today
tw.get_tasks("due:today")

# Tasks due this week
tw.get_tasks("due.before:eow")

# Tasks due in the next 7 days
tw.get_tasks("due.before:now+7d")

# Overdue tasks
tw.get_tasks("+OVERDUE")

# Tasks with any due date
tw.get_tasks("due.any:")

# Tasks with no due date
tw.get_tasks("due.none:")

# Tasks due in a specific month
tw.get_tasks("due.after:2026-03-01 due.before:2026-04-01")
```

---

## Semantic Summary of the Four Date Fields

```
Timeline ──────────────────────────────────────────────────────────►

  [wait] ──► task becomes visible
                [scheduled] ──► task becomes READY
                                      ... work on it ...
                                                    [due] ──► OVERDUE
                                                                  [until] ──► auto-DELETE
```

| Field | Task is hidden? | Task is ready? | Urgency effect |
|-------|----------------|---------------|----------------|
| `wait` | Yes, until date | — | None while waiting |
| `scheduled` | No | Only after date | Elevated when ready |
| `due` | No | — | Increases as deadline approaches |
| `until` | No | — | None (hard expiry) |
