# Basic Usage

Common patterns for working with pytaskwarrior.

## Creating Tasks

### Simple Task

```python
from taskwarrior import TaskWarrior, TaskInputDTO

tw = TaskWarrior()

task = TaskInputDTO(description="Buy groceries")
added = tw.add_task(task)
print(f"Created: {added.uuid}")
```

### Task with Priority and Tags

```python
from taskwarrior import TaskInputDTO, Priority

task = TaskInputDTO(
    description="Finish report",
    priority=Priority.HIGH,
    tags=["work", "urgent"],
)
tw.add_task(task)
```

### Task with Due Date

```python
task = TaskInputDTO(
    description="Submit proposal",
    due="friday",  # TaskWarrior date expression
    project="sales",
)
tw.add_task(task)
```

TaskWarrior supports many date expressions:

- `tomorrow`, `yesterday`, `today`
- `monday`, `friday` (next occurrence)
- `eom` (end of month), `eoy` (end of year)
- `now + 2weeks`, `today + 3days`

## Retrieving Tasks

### All Pending Tasks

```python
tasks = tw.get_tasks()
for task in tasks:
    print(f"[{task.priority or '-'}] {task.description}")
```

### Filtered Tasks

```python
# By project
work_tasks = tw.get_tasks("project:work")

# By tag
urgent = tw.get_tasks("+urgent")

# Complex filter
overdue = tw.get_tasks("due.before:today status:pending")
```

### Single Task

```python
# By ID (integer)
task = tw.get_task(1)

# By UUID
task = tw.get_task("abc123-def456-...")
```

## Modifying Tasks

```python
from taskwarrior import task_output_to_input, Priority

# Get the task
task = tw.get_task(uuid)

# Convert to input DTO
input_dto = task_output_to_input(task)

# Make changes
input_dto.priority = Priority.HIGH
input_dto.tags.append("reviewed")

# Save
tw.modify_task(input_dto, uuid)
```

## Task Lifecycle

```python
# Start working on a task (sets start time)
tw.start_task(uuid)

# Stop working (clears start time)
tw.stop_task(uuid)

# Mark as complete
tw.done_task(uuid)

# Delete (soft delete, can be undone)
tw.delete_task(uuid)

# Purge (permanent deletion)
tw.purge_task(uuid)
```

## Annotations

Add notes to tasks:

```python
task = tw.add_task(TaskInputDTO(description="Research topic"))

tw.annotate_task(task.uuid, "Found good article at example.com")
tw.annotate_task(task.uuid, "Discussed with team")

# Retrieve annotations
task = tw.get_task(task.uuid)
for ann in task.annotations:
    print(f"{ann.entry}: {ann.description}")
```

## Date Calculations

Use TaskWarrior's date calculation engine:

```python
# Calculate a date expression
result = tw.task_calc("today + 2weeks")
print(result)  # "2026-02-14T00:00:00"

# Validate a date expression
if tw.date_validator("next monday"):
    print("Valid date expression")
```
