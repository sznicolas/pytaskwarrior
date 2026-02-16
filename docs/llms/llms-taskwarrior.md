# TaskWarrior Integration

This guide covers how to integrate pytaskwarrior into your projects and use its core features.

## Installation and Setup

Install pytaskwarrior using pip:

```bash
pip install pytaskwarrior
```

Ensure TaskWarrior 3.4+ is installed and accessible via the `task` command:

```bash
task --version
```

## Basic Usage

Initialize TaskWarrior with default settings (uses `~/.taskrc`):

```python
from taskwarrior import TaskWarrior

tw = TaskWarrior()
```

Initialize with custom configuration:

```python
tw = TaskWarrior(
    taskrc_file="/path/to/.taskrc",
    data_location="/path/to/task/data",
    task_cmd="task"
)
```

## Environment Variables

pytaskwarrior respects these environment variables:

- `TASKRC` - Path to taskrc file (default: `~/.taskrc`)
- `TASKDATA` - Path to task data directory

## Quick Start Example

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

## Core CRUD Operations

### Create Tasks

```python
from taskwarrior import TaskInputDTO

task = TaskInputDTO(
    description="Buy groceries",
    project="home",
    due="today"
)
added = tw.add_task(task)
```

### Read Tasks

```python
# Get all pending tasks
tasks = tw.get_tasks()

# Get tasks with filter
work_tasks = tw.get_tasks("project:work")

# Get a specific task
task = tw.get_task(uuid_or_id)
```

### Update Tasks

```python
from taskwarrior import task_output_to_input, Priority

# Get the task
task = tw.get_task(uuid)

# Convert to input DTO for modification
input_dto = task_output_to_input(task)
input_dto.priority = Priority.HIGH

# Save changes
tw.modify_task(input_dto, uuid)
```

### Delete Tasks

```python
# Soft delete
tw.delete_task(uuid)

# Permanent delete
tw.purge_task(uuid)
```

## Configuration Options

### Custom TaskWarrior Configuration

```python
tw = TaskWarrior(
    taskrc_file="/custom/path/.taskrc",
    data_location="/custom/data/location"
)
```

### Task Command Path

```python
tw = TaskWarrior(task_cmd="/usr/local/bin/task")
```
