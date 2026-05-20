# pytaskwarrior

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests](https://github.com/sznicolas/pytaskwarrior/workflows/CI/badge.svg)](https://github.com/sznicolas/pytaskwarrior/actions)

A modern Python library for [TaskWarrior](https://taskwarrior.org/) v3.x task management.

**No `task` binary required.** pytaskwarrior uses
[taskchampion-py](https://github.com/GothenburgBitFactory/taskchampion-py) — Rust bindings
to the taskchampion storage engine — for direct, high-performance SQLite access.

## Features

- **No external binary** — reads/writes TaskWarrior's SQLite database directly
- **Full CRUD operations** — Create, read, update, delete tasks
- **Type-safe** — Pydantic models with full type hints
- **Context management** — Define, apply, and switch contexts (reads/writes `.taskrc`)
- **UDA support** — User Defined Attributes
- **Virtual tags** — `+OVERDUE`, `+DUE`, `+TODAY`, `+WEEK`, `+BLOCKED`, `+READY`, and 20+ more
- **Date expressions** — `due.before:tomorrow`, `due.after:eom`, compound expressions (`now + P3D`)
- **Recurring tasks** — Full recurrence support
- **Annotations** — Add notes to tasks
- **Optional CLI fallback** — Pass `task_cmd="task"` to use the classic CLI adapter

## Requirements

- Python 3.12+
- `taskchampion-py` >= 3.0.1.1 (installed automatically)

The `task` binary is **not required** for the default adapter.

## Installation

```bash
pip install pytaskwarrior
```

Or install from source:

```bash
git clone https://github.com/sznicolas/pytaskwarrior.git
cd pytaskwarrior
uv sync
```

## Quick Start

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

# No binary needed — uses taskchampion SQLite backend directly
tw = TaskWarrior()

# Create a task
task = tw.add_task(TaskInputDTO(
    description="Finish project report",
    priority=Priority.HIGH,
    project="work",
    tags=["urgent"],
    due="friday",
))
print(f"Created: {task.uuid}")

# Query tasks
for t in tw.get_tasks("project:work"):
    print(f"[{t.priority or '-'}] {t.description}")

# Virtual tag filtering
overdue = tw.get_tasks("+OVERDUE")
due_soon = tw.get_tasks("due.before:eow")

# Complete a task
tw.done_task(task.uuid)
```

### Using the CLI adapter (optional)

```python
# Explicit CLI mode — requires the task binary
tw = TaskWarrior(task_cmd="task")

# Custom paths
tw = TaskWarrior(
    taskrc_file="/path/to/.taskrc",
    data_location="/path/to/task/data",
)
```

### Live configuration updates

`config_store` is the live interface to the taskrc file.  Changes made via
`set_value()` or `set_sync_config()` are immediately effective on the next
adapter call — no restart or adapter recreation required.

```python
tw = TaskWarrior()

# Configure remote sync at runtime
tw.config_store.set_value("sync.server.origin", "https://sync.example.com")
tw.config_store.set_value("sync.encryption.secret", "my-passphrase")
tw.synchronize()  # uses the new config immediately

# Or replace the whole sync block at once
tw.config_store.set_sync_config({
    "sync.local.server_dir": "/mnt/shared/taskserver",
})
tw.synchronize()
```

> **Note:** Changing `data_location` at runtime is not supported.  Create a
> new `TaskWarrior` instance if you need a different data directory.

## Architecture

```
TaskWarrior (facade)
├── TaskChampionAdapter  ← default: direct SQLite via taskchampion-py
│   ├── CRUD operations (add/get/modify/delete tasks)
│   ├── Filtering (tc_filter.py — Python reimplementation of TW filters)
│   └── Date resolution (date_resolver.py — Python reimplementation of TW dates)
├── ConfigStore          ← reads/writes ~/.taskrc
│   ├── ContextService   ← define/apply/delete contexts
│   └── UdaService       ← define/delete UDAs
└── TaskWarriorAdapter   ← optional CLI fallback (task_cmd="task")
```

## Supported Filter Syntax

| Token | Example | Description |
|-------|---------|-------------|
| `+tag` / `-tag` | `+urgent -someday` | Include / exclude by tag |
| `+VIRTUAL` | `+OVERDUE`, `+DUE`, `+TODAY` | Virtual tags (computed) |
| `status:X` | `status:pending` | Status filter |
| `project:X` | `project:work` | Project (hierarchical) |
| `priority:X` | `priority:H` | Priority |
| `due.before:X` | `due.before:tomorrow` | Date range |
| `due.after:X` | `due.after:eom` | Date range |
| `due.by:X` | `due.by:friday` | Date range (inclusive) |

## Next Steps

- [Getting Started](docs/getting-started.md) — Installation and setup
- [TaskChampion Adapter](docs/taskchampion-adapter.md) — Technical details
- [API Reference](docs/api/taskwarrior.md) — Full API documentation
- [Examples](docs/examples/basic.md) — More usage examples
