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
pip install -e .
```

## Requirements

- **Python 3.12+**
- **TaskWarrior 3.4+** installed and accessible via `task` command

To verify TaskWarrior is installed:

```bash
task --version
```

## Quick Start

### Basic Usage

```python
from taskwarrior import TaskWarrior, TaskInputDTO

# Initialize with defaults (uses ~/.taskrc)
tw = TaskWarrior()

# Create a simple task
task = TaskInputDTO(description="Buy groceries")
added = tw.add_task(task)
print(f"Created task #{added.index}: {added.uuid}")
```

### Custom Configuration

```python
tw = TaskWarrior(
    taskrc_file="/path/to/.taskrc",
    data_location="/path/to/task/data",
    task_cmd="task"  # Path to task binary
)
```

### Environment Variables

pytaskwarrior respects these environment variables:

- `TASKRC` - Path to taskrc file (default: `~/.taskrc`)
- `TASKDATA` - Path to task data directory

## Creating Tasks

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
# Get all pending tasks
tasks = tw.get_tasks()

# Get tasks with filter
work_tasks = tw.get_tasks("project:work")

# Get a specific task
task = tw.get_task(uuid_or_id)
```

## Modifying Tasks

```python
from taskwarrior import task_output_to_input

# Get the task
task = tw.get_task(uuid)

# Convert to input DTO for modification
input_dto = task_output_to_input(task)
input_dto.priority = Priority.HIGH

# Save changes
tw.modify_task(input_dto, uuid)
```

## Task Lifecycle

```python
# Start working on a task
tw.start_task(uuid)

# Stop working
tw.stop_task(uuid)

# Complete a task
tw.done_task(uuid)

# Delete a task (soft delete)
tw.delete_task(uuid)

# Permanently remove
tw.purge_task(uuid)
```

## Next Steps

- [API Reference](api/taskwarrior.md) - Full API documentation
- [Examples](examples/basic.md) - More usage examples
- [Contexts](examples/contexts.md) - Working with contexts
