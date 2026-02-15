# Advanced Usage

Advanced features including recurring tasks, UDAs, and more.

## Recurring Tasks

### Creating Recurring Tasks

```python
from taskwarrior import TaskInputDTO, RecurrencePeriod

# Weekly task
weekly = TaskInputDTO(
    description="Weekly team standup",
    due="monday 09:00",
    recur=RecurrencePeriod.WEEKLY,
    project="meetings",
)
tw.add_task(weekly)

# Monthly task
monthly = TaskInputDTO(
    description="Monthly report",
    due="eom",  # End of month
    recur=RecurrencePeriod.MONTHLY,
)
tw.add_task(monthly)
```

### Available Recurrence Periods

| Period | Description |
|--------|-------------|
| `DAILY` | Every day |
| `WEEKLY` | Every week |
| `MONTHLY` | Every month |
| `YEARLY` | Every year |
| `QUARTERLY` | Every 3 months |
| `SEMIANNUALLY` | Every 6 months |

### Working with Recurring Tasks

```python
# Get the parent template
parent = tw.get_recurring_task(uuid)

# Get all instances
instances = tw.get_recurring_instances(uuid)
for instance in instances:
    print(f"{instance.due}: {instance.description}")
```

## User Defined Attributes (UDAs)

UDAs extend TaskWarrior with custom fields.

### Defining UDAs

```python
from taskwarrior.dto.uda_dto import UdaConfig, UdaType

# String UDA with allowed values
severity = UdaConfig(
    name="severity",
    type=UdaType.STRING,
    label="Severity",
    values=["low", "medium", "high", "critical"],
    default="medium",
)
tw.uda_service.define_uda(severity)

# Numeric UDA for time estimates
estimate = UdaConfig(
    name="estimate",
    type=UdaType.NUMERIC,
    label="Hours",
    coefficient=1.0,  # Affects urgency
)
tw.uda_service.define_uda(estimate)
```

### Using UDAs in Tasks

```python
# Create a task with UDA values
task = TaskInputDTO(
    description="Fix critical bug",
    project="backend",
    udas={"severity": "critical", "estimate": 4},
)
added = tw.add_task(task)

# Read UDA values from a task
task = tw.get_task(uuid)
severity = task.get_uda("severity")  # "critical"
estimate = task.get_uda("estimate", default=0)  # 4
```

### Listing UDAs

```python
# Get all defined UDA names
names = tw.get_uda_names()
print(names)  # {"severity", "estimate"}

# Get configuration for a specific UDA
config = tw.get_uda_config("severity")
if config:
    print(config.type)    # UdaType.STRING
    print(config.values)  # ["low", "medium", "high", "critical"]
```

### Reloading UDAs

If UDAs are modified externally, reload them:

```python
tw.reload_udas()
```

## Task Dependencies

```python
from uuid import UUID

# Create tasks
task1 = tw.add_task(TaskInputDTO(description="Design API"))
task2 = tw.add_task(TaskInputDTO(description="Implement API"))
task3 = tw.add_task(TaskInputDTO(description="Write tests"))

# Create dependent task
dependent = TaskInputDTO(
    description="Deploy to production",
    depends=[task1.uuid, task2.uuid, task3.uuid],
)
tw.add_task(dependent)
```

## Waiting Tasks

Hide tasks until a specific date:

```python
task = TaskInputDTO(
    description="Follow up on proposal",
    wait="friday",  # Hidden until Friday
    due="next monday",
)
tw.add_task(task)
```

## Scheduled Tasks

Set the earliest start date:

```python
task = TaskInputDTO(
    description="Start quarterly review",
    scheduled="2026-04-01",
    due="2026-04-15",
)
tw.add_task(task)
```

## Getting TaskWarrior Info

```python
info = tw.get_info()
print(f"TaskWarrior version: {info['version']}")
print(f"Config file: {info['taskrc_file']}")
```

## Error Handling

```python
from taskwarrior.exceptions import (
    TaskWarriorError,
    TaskNotFound,
    TaskValidationError,
)

try:
    task = tw.get_task("nonexistent-uuid")
except TaskNotFound:
    print("Task not found")
except TaskValidationError as e:
    print(f"Invalid data: {e}")
except TaskWarriorError as e:
    print(f"TaskWarrior error: {e}")
```

## Converting Between DTOs

```python
from taskwarrior import task_output_to_input

# Get a task (returns TaskOutputDTO)
output = tw.get_task(uuid)

# Convert to TaskInputDTO for modification
input_dto = task_output_to_input(output)

# Modify and save
input_dto.priority = Priority.HIGH
tw.modify_task(input_dto, uuid)
```
