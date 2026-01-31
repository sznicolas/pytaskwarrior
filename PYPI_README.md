# pytaskwarrior

A modern Python wrapper for [TaskWarrior](https://taskwarrior.org/), the command-line task management tool.

## Features

- ✅ Full CRUD operations for tasks
- ✅ Type-safe with Pydantic models
- ✅ Context management
- ✅ UDA (User Defined Attributes) support
- ✅ Recurring tasks and annotations

## Requirements

- Python 3.12+
- TaskWarrior 3.4+ installed

## Installation

```bash
pip install pytaskwarrior
```

## Quick Start

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

tw = TaskWarrior()

# Create a task
task = TaskInputDTO(
    description="Important meeting",
    priority=Priority.HIGH,
    project="work",
    due="friday"
)
added = tw.add_task(task)

# Get all pending tasks
for t in tw.get_tasks():
    print(f"[{t.priority or '-'}] {t.description}")

# Complete a task
tw.done_task(added.uuid)
```

## Documentation

Full documentation: [GitHub Repository](https://github.com/sznicolas/pytaskwarrior/)
