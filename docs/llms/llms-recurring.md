# Recurring Tasks Strategy

Recurring tasks in pytaskwarrior allow you to create tasks that repeat automatically based on defined patterns.

## Recurrence Period Usage

### Creating Recurring Tasks

```python
from taskwarrior import TaskWarrior, TaskInputDTO, RecurrencePeriod

tw = TaskWarrior()

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

### Recurrence with Specific Dates

```python
# Create a task that recurs every 2 weeks
task = TaskInputDTO(
    description="Bi-weekly check-in",
    due="monday 10:00",
    recur=RecurrencePeriod.WEEKLY,
    recur_spec="2 weeks"
)
tw.add_task(task)
```

## Template Management

### Working with Recurring Task Templates

```python
# Get the parent template of a recurring task
parent = tw.get_recurring_task(uuid)

# Get all instances of a recurring task
instances = tw.get_recurring_instances(uuid)
for instance in instances:
    print(f"{instance.due}: {instance.description}")
```

### Managing Recurring Task Instances

```python
# Get only upcoming instances
upcoming = tw.get_recurring_instances(uuid, status="pending")

# Get completed instances
completed = tw.get_recurring_instances(uuid, status="completed")
```

## Recurring Task Patterns

### Daily Standups

```python
# Create a daily standup task
daily_standup = TaskInputDTO(
    description="Daily team standup",
    due="9:00",
    recur=RecurrencePeriod.DAILY,
    project="meetings"
)
tw.add_task(daily_standup)
```

### Weekly Review Tasks

```python
# Create a weekly review task
weekly_review = TaskInputDTO(
    description="Weekly project review",
    due="friday 15:00",
    recur=RecurrencePeriod.WEEKLY,
    project="work"
)
tw.add_task(weekly_review)
```

### Monthly Billing Tasks

```python
# Create a monthly billing task
monthly_billing = TaskInputDTO(
    description="Process monthly invoices",
    due="eom 10:00",
    recur=RecurrencePeriod.MONTHLY,
    project="finance"
)
tw.add_task(monthly_billing)
```

## Scheduling Strategies

### Future Recurring Tasks

```python
# Create a task that starts in the future
future_task = TaskInputDTO(
    description="Quarterly planning session",
    due="2026-03-15 10:00",
    recur=RecurrencePeriod.QUARTERLY,
    project="planning"
)
tw.add_task(future_task)
```

### Conditional Recurrence

```python
# Create a task that recurs only on weekdays
weekday_task = TaskInputDTO(
    description="Daily check-in",
    due="9:00",
    recur=RecurrencePeriod.DAILY,
    project="daily"
)
tw.add_task(weekday_task)

# Set recurrence to only run on weekdays
# This would typically be handled by TaskWarrior's internal logic
```

### Recurrence with Dependencies

```python
# Create a recurring task that depends on another task
dependent_task = TaskInputDTO(
    description="Weekly report",
    due="friday 17:00",
    recur=RecurrencePeriod.WEEKLY,
    depends=["task-uuid-1", "task-uuid-2"]
)
tw.add_task(dependent_task)
```

## Advanced Recurrence Management

### Modifying Recurring Tasks

```python
from taskwarrior import task_output_to_input

# Get a recurring task
task = tw.get_task(uuid)

# Convert to input DTO for modification
input_dto = task_output_to_input(task)
input_dto.due = "monday 10:30"  # Change due time
input_dto.recur = RecurrencePeriod.WEEKLY  # Ensure recurrence

# Save changes
tw.modify_task(input_dto, uuid)
```

### Stopping Recurrence

```python
# Get a recurring task
task = tw.get_task(uuid)

# Convert to input DTO and remove recurrence
input_dto = task_output_to_input(task)
input_dto.recur = None  # Remove recurrence

# Save changes
tw.modify_task(input_dto, uuid)
```

### Creating One-Time Instances

```python
# Create a one-time instance of a recurring task
# This is typically handled by TaskWarrior's internal logic when you create
# a new task with the same description but different due date
```

### Recurrence Validation

```python
# Validate recurrence settings before creating tasks
def validate_recurrence(task_input):
    if task_input.recur and not task_input.due:
        raise ValueError("Due date is required for recurring tasks")
    
    if task_input.recur and task_input.recur not in [
        RecurrencePeriod.DAILY,
        RecurrencePeriod.WEEKLY,
        RecurrencePeriod.MONTHLY,
        RecurrencePeriod.YEARLY,
        RecurrencePeriod.QUARTERLY,
        RecurrencePeriod.SEMIANNUALLY
    ]:
        raise ValueError("Invalid recurrence period")
    
    return True

# Usage
try:
    validate_recurrence(task_input)
    tw.add_task(task_input)
except ValueError as e:
    print(f"Recurrence validation error: {e}")
```
