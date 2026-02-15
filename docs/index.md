# pytaskwarrior

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A modern Python wrapper for [TaskWarrior](https://taskwarrior.org/), the command-line task management tool.

## Features

- ✅ **Full CRUD operations** - Create, read, update, delete tasks
- ✅ **Type-safe** - Pydantic models with full type hints
- ✅ **Context management** - Define, apply, and switch contexts
- ✅ **UDA support** - User Defined Attributes
- ✅ **Recurring tasks** - Full recurrence support
- ✅ **Annotations** - Add notes to tasks
- ✅ **Date calculations** - Use TaskWarrior's date expressions

## Quick Example

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

# Initialize TaskWarrior
tw = TaskWarrior()

# Create a task
task = TaskInputDTO(
    description="Finish project report",
    priority=Priority.HIGH,
    project="work",
    tags=["urgent"],
    due="friday",
)
added = tw.add_task(task)
print(f"Created task: {added.uuid}")

# Get all pending tasks
for task in tw.get_tasks():
    print(f"[{task.priority or '-'}] {task.description}")

# Complete a task
tw.done_task(added.uuid)
```

## Requirements

- Python 3.12+
- TaskWarrior 3.4+ installed and accessible via `task` command

## Next Steps

- [Getting Started](getting-started.md) - Installation and setup
- [API Reference](api/taskwarrior.md) - Full API documentation
- [Examples](examples/basic.md) - More usage examples
