#!/usr/bin/env python3
"""Date filter expressions example.

Runs entirely in memory — no files written, nothing touches ~/.task or ~/.taskrc.

Demonstrates:
  - due.before:X and due.after:X filter expressions
  - due.by:X (inclusive ≤)
  - Compound expressions: due.before:now + P7D
  - Virtual date tags: +OVERDUE, +DUE, +DUETODAY, +TODAY, +WEEK, +TOMORROW
  - Combining date filters with other tokens
"""

from datetime import UTC, datetime, timedelta

from taskwarrior import Priority, TaskInputDTO, TaskWarrior
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

# ---------------------------------------------------------------------------
# Setup — fully isolated, in-memory database
# ---------------------------------------------------------------------------
adapter = TaskChampionAdapter(data_location=None)
tw = TaskWarrior(adapter=adapter)

now = datetime.now(tz=UTC)


def iso(dt: datetime) -> str:
    """Return an ISO-8601 string accepted by TaskInputDTO date fields."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Seed tasks with a variety of due dates
# ---------------------------------------------------------------------------
print("=== Creating tasks with various due dates ===\n")
tasks_to_add = [
    TaskInputDTO(
        description="Overdue: fix the regression (3 days ago)",
        project="work",
        priority=Priority.HIGH,
        tags=["bug"],
        due=iso(now - timedelta(days=3)),
    ),
    TaskInputDTO(
        description="Overdue: send invoice (yesterday)",
        project="finance",
        priority=Priority.MEDIUM,
        due=iso(now - timedelta(hours=5)),
    ),
    TaskInputDTO(
        description="Due today: team standup",
        project="work",
        due=iso(now.replace(hour=9, minute=0, second=0, microsecond=0)),
    ),
    TaskInputDTO(
        description="Due tomorrow: review PR",
        project="work",
        due=iso(now + timedelta(days=1)),
    ),
    TaskInputDTO(
        description="Due in 5 days: prepare slides",
        project="work",
        due=iso(now + timedelta(days=5)),
    ),
    TaskInputDTO(
        description="Due in 12 days: quarterly report",
        project="finance",
        due=iso(now + timedelta(days=12)),
    ),
    TaskInputDTO(
        description="No due date: read a book",
        project="personal",
    ),
]

added = [tw.add_task(t) for t in tasks_to_add]
for t in added:
    due_label = t.due.strftime("%Y-%m-%d %H:%M UTC") if t.due else "—"
    print(f"  #{t.index:2d}  due={due_label:>22}  {t.description}")

# ---------------------------------------------------------------------------
# due.before: / due.after:  (strict < / >)
# ---------------------------------------------------------------------------
print("\n=== due.before:today  (strict: only tasks due before midnight today) ===")
results = tw.get_tasks("due.before:today")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== due.after:today  (due strictly after today's midnight) ===")
results = tw.get_tasks("due.after:today")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== due.before:tomorrow  (overdue + due-today tasks) ===")
results = tw.get_tasks("due.before:tomorrow")
for t in results:
    print(f"  #{t.index}  {t.description}")

# ---------------------------------------------------------------------------
# due.by: (inclusive ≤)
# ---------------------------------------------------------------------------
print("\n=== due.by:tomorrow  (≤ start of tomorrow midnight local time — same as due.before:tomorrow for most tasks) ===")
results = tw.get_tasks("due.by:tomorrow")
for t in results:
    print(f"  #{t.index}  {t.description}")

# ---------------------------------------------------------------------------
# Compound expressions (ISO 8601 duration)
# ---------------------------------------------------------------------------
print("\n=== due.before:now + P7D  (due within the next 7 days, overdue included) ===")
results = tw.get_tasks("due.before:now + P7D")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== due.after:now + P7D  (due more than a week away) ===")
results = tw.get_tasks("due.after:now + P7D")
for t in results:
    print(f"  #{t.index}  {t.description}")

# ---------------------------------------------------------------------------
# Virtual date tags
# ---------------------------------------------------------------------------
print("\n=== +OVERDUE  (past due, pending tasks only) ===")
results = tw.get_tasks("+OVERDUE")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== +DUE  (due within the next 7 days, overdue included) ===")
results = tw.get_tasks("+DUE")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== +DUETODAY  (due exactly today) ===")
results = tw.get_tasks("+DUETODAY")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== +TOMORROW  (due exactly tomorrow) ===")
results = tw.get_tasks("+TOMORROW")
for t in results:
    print(f"  #{t.index}  {t.description}")

print("\n=== +WEEK  (due on or before 7 days from today) ===")
results = tw.get_tasks("+WEEK")
for t in results:
    print(f"  #{t.index}  {t.description}")

# ---------------------------------------------------------------------------
# Combining date filters with other tokens
# ---------------------------------------------------------------------------
print("\n=== +OVERDUE project:work  (overdue work tasks only) ===")
results = tw.get_tasks("+OVERDUE project:work")
for t in results:
    print(f"  #{t.index}  {t.description}  (project: {t.project})")

print("\n=== due.before:now + P7D priority:H  (urgent + due soon) ===")
results = tw.get_tasks("due.before:now + P7D priority:H")
for t in results:
    print(f"  #{t.index}  {t.description}  (priority: {t.priority})")

print("\n=== -OVERDUE +WEEK  (coming up this week, not yet overdue) ===")
results = tw.get_tasks("-OVERDUE +WEEK")
for t in results:
    print(f"  #{t.index}  {t.description}")

# ---------------------------------------------------------------------------
# task_calc: resolve a date expression to an ISO timestamp
# ---------------------------------------------------------------------------
print("\n=== task_calc — resolve date expressions ===")
for expr in ("today", "tomorrow", "eom", "now + P7D", "eom - P1W"):
    resolved = tw.task_calc(expr)
    print(f"  {expr:>15}  →  {resolved}")

print("\nDone.")
