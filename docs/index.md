# pytaskwarrior

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Python library for [TaskWarrior](https://taskwarrior.org/) task management.

**No `task` binary required.** pytaskwarrior reads and writes TaskWarrior's SQLite
database directly via [taskchampion-py](https://github.com/GothenburgBitFactory/taskchampion-py).

## Features

- ✅ **No binary required** — direct SQLite access via taskchampion-py
- ✅ **Full CRUD operations** — Create, read, update, delete tasks
- ✅ **Type-safe** — Pydantic models with full type hints
- ✅ **Context management** — reads/writes `.taskrc` directly
- ✅ **UDA support** — User Defined Attributes
- ✅ **Virtual tags** — `+OVERDUE`, `+DUE`, `+TODAY`, `+WEEK`, `+BLOCKED`, `+READY`, and 20+ more
- ✅ **Date expressions** — `due.before:tomorrow`, compound expressions (`now + P3D`)
- ✅ **Recurring tasks** — Full recurrence support
- ✅ **Optional CLI fallback** — pass `task_cmd="task"` for legacy CLI mode

!!! warning
    When using `TaskWarrior()` without parameters it reads/writes your default TaskWarrior
    database at `~/.task/`.  Use `data_location=` to point to an isolated directory for
    testing or automation.

## Quick Example

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

# No binary needed
tw = TaskWarrior()

# Create a task
task = tw.add_task(TaskInputDTO(
    description="Finish project report",
    priority=Priority.HIGH,
    project="work",
    tags=["urgent"],
    due="friday",
))
print(f"Created task: {task.uuid}")

# Get all pending tasks
for t in tw.get_tasks():
    print(f"[{t.priority or '-'}] {t.description}")

# Overdue tasks
for t in tw.get_tasks("+OVERDUE"):
    print(f"OVERDUE: {t.description}")

# Complete a task
tw.done_task(task.uuid)
```

## Next Steps

- [Getting Started](getting-started.md) — Installation and setup
- [API Reference](api/taskwarrior.md) — Full API documentation
- [TaskChampion Adapter](taskchampion-adapter.md) — Architecture details
- [Examples](examples/basic.md) — More usage examples
