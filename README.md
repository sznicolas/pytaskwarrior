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

## Requirements

- Python 3.12+
- TaskWarrior 3.4+ installed and accessible via `task` command

## Installation

```bash
pip install pytaskwarrior==1.0.0rc1
```

Or install from source:

```bash
git clone https://github.com/sznicolas/pytaskwarrior.git
cd pytaskwarrior
pip install -e .
```

## Quick Start

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

# Initialize TaskWarrior (uses default ~/.taskrc)
tw = TaskWarrior()

# Create a simple task
task = TaskInputDTO(description="Buy groceries")
added_task = tw.add_task(task)
print(f"Created task #{added_task.index}: {added_task.uuid}")

# Create a task with more details
urgent_task = TaskInputDTO(
    description="Finish project report",
    priority=Priority.HIGH,
    project="work",
    tags=["urgent", "report"],
    due="friday",  # TaskWarrior date expressions work!
)
tw.add_task(urgent_task)

# Get all pending tasks
tasks = tw.get_tasks()
for t in tasks:
    print(f"[{t.priority or '-'}] {t.description}")

# Complete a task
tw.done_task(added_task.uuid)
```

## API Reference

### TaskWarrior

The main class for interacting with TaskWarrior.

```python
from taskwarrior import TaskWarrior

# With defaults (uses ~/.taskrc)
tw = TaskWarrior()

# With custom configuration
tw = TaskWarrior(
    taskrc_file="/path/to/.taskrc",
    data_location="/path/to/task/data",
    task_cmd="task"  # Path to task binary
)
```

#### Task Operations

| Method | Description |
|--------|-------------|
| `add_task(task: TaskInputDTO)` | Create a new task |
| `get_task(uuid)` | Get a single task by UUID or ID |
| `get_tasks(filter_args="")` | Get tasks matching filter |
| `modify_task(uuid, task: TaskInputDTO)` | Modify an existing task |
| `delete_task(uuid)` | Mark task as deleted |
| `purge_task(uuid)` | Permanently remove task |
| `done_task(uuid)` | Mark task as completed |
| `start_task(uuid)` | Start working on task |
| `stop_task(uuid)` | Stop working on task |
| `annotate_task(uuid, annotation)` | Add annotation to task |

#### Context Operations

| Method | Description |
|--------|-------------|
| `define_context(name, filter)` | Create a context with filter |
| `apply_context(name)` | Activate a context |
| `unset_context()` | Deactivate current context |
| `get_contexts()` | List all contexts |
| `get_current_context()` | Get active context name |
| `delete_context(name)` | Remove a context |
| `has_context(name)` | Check if context exists |

### Data Models

#### TaskInputDTO

Used for creating and modifying tasks.

```python
from taskwarrior import TaskInputDTO, Priority, RecurrencePeriod

task = TaskInputDTO(
    description="Task description",      # Required
    priority=Priority.HIGH,              # H, M, L or None
    project="project.subproject",
    tags=["tag1", "tag2"],
    due="2024-12-31",                    # ISO date or TW expression
    scheduled="monday",
    wait="tomorrow",
    until="2025-01-01",
    recur=RecurrencePeriod.WEEKLY,       # daily, weekly, monthly, yearly
    depends=[uuid1, uuid2],              # Task dependencies
)
```

#### TaskOutputDTO

Returned when retrieving tasks. Includes all input fields plus:

```python
task = tw.get_task(uuid)

task.uuid        # Task UUID
task.index       # Task ID number
task.status      # TaskStatus.PENDING, COMPLETED, DELETED, etc.
task.entry       # Creation datetime
task.modified    # Last modification datetime
task.urgency     # Calculated urgency score
task.annotations # List of annotations
```

### Enums

```python
from taskwarrior import Priority, TaskStatus, RecurrencePeriod

# Priority levels
Priority.HIGH    # "H"
Priority.MEDIUM  # "M"
Priority.LOW     # "L"

# Task statuses
TaskStatus.PENDING
TaskStatus.COMPLETED
TaskStatus.DELETED
TaskStatus.WAITING
TaskStatus.RECURRING

# Recurrence periods
RecurrencePeriod.DAILY
RecurrencePeriod.WEEKLY
RecurrencePeriod.MONTHLY
RecurrencePeriod.YEARLY
```

## Advanced Examples

### Working with Contexts

```python
# Define contexts for different workflows
tw.define_context("work", "project:work or +urgent")
tw.define_context("home", "project:home or project:personal")

# Switch to work context
tw.apply_context("work")

# Now get_tasks() only returns work-related tasks
work_tasks = tw.get_tasks()

# Switch back to no context
tw.unset_context()
```

### Recurring Tasks

```python
from taskwarrior import TaskInputDTO, RecurrencePeriod

# Create a weekly recurring task
weekly_review = TaskInputDTO(
    description="Weekly project review",
    due="monday",
    recur=RecurrencePeriod.WEEKLY,
    project="reviews",
)
tw.add_task(weekly_review)

# Get the parent recurring task
recurring = tw.get_recurring_task(task.uuid)

# Get all instances
instances = tw.get_recurring_instances(task.uuid)
```

### Task Annotations

```python
# Add notes to a task
task = tw.add_task(TaskInputDTO(description="Research topic"))

tw.annotate_task(task.uuid, "Found useful article at example.com")
tw.annotate_task(task.uuid, "Discussed with team, need more info")

# Annotations are included when retrieving tasks
task = tw.get_task(task.uuid)
for ann in task.annotations:
    print(f"{ann.entry}: {ann.description}")
```

### Date Calculations

```python
# Use TaskWarrior's date calculation
result = tw.task_calc("today + 2weeks")
print(result)  # "2024-02-14T00:00:00"

# Validate a date expression
if tw.date_validator("next monday"):
    print("Valid date expression")
```

## Configuration

### Environment Variables

- `TASKRC` - Path to taskrc file (default: `~/.taskrc`)
- `TASKDATA` - Path to task data directory

### Automatic Configuration

If no `.taskrc` exists at the specified path, pytaskwarrior creates one with sensible defaults:

```ini
# Auto-generated by pytaskwarrior
rc.data.location=~/.task
rc.confirmation=off
rc.bulk=0
```

## Development

### Setup

```bash
git clone https://github.com/sznicolas/pytaskwarrior.git
cd pytaskwarrior
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/taskwarrior --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_dto.py -v
```

### Code Quality

```bash
# Linting and formatting
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/taskwarrior
```

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [TaskWarrior](https://taskwarrior.org/) - The underlying task management tool
- [GitHub Repository](https://github.com/sznicolas/pytaskwarrior/)
- [PyPI Package](https://pypi.org/project/pytaskwarrior/)

