# Getting Started

## Installation

### From PyPI

```bash
pip install pytaskwarrior
```

### From Source

```bash
git clone https://github.com/sznicolas/pytaskwarrior.git
cd pytaskwarrior
uv sync
```

## Requirements

- **Python 3.12+**
- **taskchampion-py >= 3.0.1.1** (installed automatically)

The `task` binary is **not required** for the default backend.

## Quick Start

### Default mode (no binary)

```python
from taskwarrior import TaskWarrior, TaskInputDTO

# Uses taskchampion SQLite backend — no task binary needed
tw = TaskWarrior()

task = TaskInputDTO(description="Buy groceries")
added = tw.add_task(task)
print(f"Created task #{added.index}: {added.uuid}")
```

### Custom paths

```python
tw = TaskWarrior(
    taskrc_file="/path/to/.taskrc",
    data_location="/path/to/task/data",
)
```

### CLI mode (optional, requires `task` binary)

```python
tw = TaskWarrior(task_cmd="task")
# or explicit path
tw = TaskWarrior(task_cmd="/usr/local/bin/task")
```

### Environment Variables

pytaskwarrior respects these environment variables:

- `TASKRC` — Path to taskrc file (default: `~/.taskrc`)
- `TASKDATA` — Path to task data directory

## Data & Configuration

### Where data is stored

| File / Directory | Default path | Purpose |
|-----------------|-------------|---------|
| `.taskrc` | `~/.taskrc` | Configuration (contexts, UDAs, sync, …) |
| Task database | `~/.task/taskchampion.sqlite` | All tasks (SQLite, written by taskchampion) |

Both are **created automatically** on first use if they don't exist.

### Resolution order

`data_location` is resolved in this order:

1. `data_location=` argument passed to `TaskWarrior()`
2. `TASKDATA` environment variable
3. `rc.data.location` key in `.taskrc`
4. `~/.task` (default)

`taskrc_file` is resolved as:

1. `taskrc_file=` argument passed to `TaskWarrior()`
2. `TASKRC` environment variable
3. `~/.taskrc` (default)

### Inspecting the active configuration

```python
tw = TaskWarrior()
print(tw.config_store.taskrc_path)     # Path to .taskrc
print(tw.config_store.data_location)   # Resolved data directory
print(tw.config_store.config)          # All key-value pairs from .taskrc
print(tw.get_info())                   # Backend type, version, paths
```



### Simple Task

```python
task = TaskInputDTO(description="Call mom")
tw.add_task(task)
```

### Task with Details

```python
from taskwarrior import TaskInputDTO, Priority, RecurrencePeriod

task = TaskInputDTO(
    description="Weekly team meeting",
    priority=Priority.MEDIUM,
    project="work.meetings",
    tags=["team", "recurring"],
    due="monday 10:00",
    recur=RecurrencePeriod.WEEKLY,
)
tw.add_task(task)
```

## Retrieving Tasks

```python
# All pending tasks
tasks = tw.get_tasks()

# Filter by project (hierarchical: "work" matches "work.reports" too)
work_tasks = tw.get_tasks("project:work")

# Virtual tag filters
overdue = tw.get_tasks("+OVERDUE")
due_this_week = tw.get_tasks("+WEEK")
ready = tw.get_tasks("+READY")

# Date-range filters
due_soon = tw.get_tasks("due.before:tomorrow")
scheduled_after_eom = tw.get_tasks("scheduled.after:eom")

# Get a specific task
task = tw.get_task(uuid_or_id)
```

## Modifying Tasks

```python
from taskwarrior import task_output_to_input

task = tw.get_task(uuid)
input_dto = task_output_to_input(task)
input_dto.priority = Priority.HIGH
tw.modify_task(input_dto, uuid)
```

## Task Lifecycle

```python
tw.start_task(uuid)   # Start working
tw.stop_task(uuid)    # Pause
tw.done_task(uuid)    # Complete
tw.delete_task(uuid)  # Soft delete
tw.purge_task(uuid)   # Permanently remove
```

## Date Expressions

pytaskwarrior resolves TaskWarrior-style date expressions in Python
(no CLI needed):

```python
tw.add_task(TaskInputDTO(description="Report", due="eom"))        # end of month
tw.add_task(TaskInputDTO(description="Follow-up", due="now+3d"))  # 3 days from now
tw.add_task(TaskInputDTO(description="Meeting", due="monday"))    # next Monday
tw.add_task(TaskInputDTO(description="Sprint", due="now + P2W"))  # ISO duration compound

# Validate / resolve
tw.task_calc("eow")           # → ISO 8601 string
tw.date_validator("tomorrow") # → True
```

## Virtual Tags

All 30 TaskWarrior virtual tags are supported in filters (28 computed in pure Python):

| Tag | Meaning |
|-----|---------|
| `+OVERDUE` | Due date in the past |
| `+DUE` | Due within 7 days |
| `+DUETODAY` | Due today |
| `+TODAY` | Due or scheduled today |
| `+TOMORROW` | Due tomorrow |
| `+YESTERDAY` | Due yesterday |
| `+WEEK` | Due within 7 days |
| `+MONTH` | Due this month |
| `+QUARTER` | Due this quarter |
| `+YEAR` | Due this year |
| `+BLOCKED` | Depends on incomplete tasks |
| `+UNBLOCKED` | No blocking dependencies |
| `+BLOCKING` | Other tasks depend on this one |
| `+READY` | Pending, not blocked, not scheduled in future |
| `+SCHEDULED` | Has a scheduled date |
| `+UNTIL` | Has an expiry date |
| `+ACTIVE` | Currently started |
| `+WAITING` | Wait date in the future |
| `+PENDING` | Status is pending |
| `+COMPLETED` | Status is completed |
| `+DELETED` | Status is deleted |
| `+TAGGED` | Has at least one user tag |
| `+ANNOTATED` | Has at least one annotation |
| `+PRIORITY` | Has a priority set |
| `+PROJECT` | Belongs to a project |
| `+PARENT` | Is a recurrence template |
| `+CHILD` | Is a recurrence instance |
| `+UDA` | Has at least one UDA value set |
| `+ORPHAN` | ⚠ not computed (always `False`; use CLI for full support) |
| `+LATEST` | Keep only the most recently created task in results |

## Next Steps

- [API Reference](api/taskwarrior.md) — Full API documentation
- [TaskChampion Adapter](taskchampion-adapter.md) — Architecture details
- [Examples](examples/basic.md) — More usage examples
- [Contexts](examples/contexts.md) — Working with contexts
