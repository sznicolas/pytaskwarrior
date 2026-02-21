# Task Management Patterns

This document covers common patterns and workflows for effective task management using pytaskwarrior.

## Morning Routine Workflows

### Check Urgent Tasks

```python
from taskwarrior import TaskWarrior

tw = TaskWarrior()

# Focus on high-priority items
tw.apply_context("urgent")
urgent_tasks = tw.get_tasks()
print(f"🔥 {len(urgent_tasks)} urgent tasks today")

for task in urgent_tasks[:5]:
    print(f"  - {task.description}")
```

### Daily Planning

```python
# Get all pending tasks for the day
all_tasks = tw.get_tasks()
print(f"Today you have {len(all_tasks)} tasks")

# Categorize by priority
high_priority = [t for t in all_tasks if t.priority == 'H']
medium_priority = [t for t in all_tasks if t.priority == 'M']
low_priority = [t for t in all_tasks if t.priority == 'L']

print(f"High priority: {len(high_priority)}")
print(f"Medium priority: {len(medium_priority)}")
print(f"Low priority: {len(low_priority)}")
```

## Project Management Patterns

### Work Projects

```python
# Define project context
tw.define_context("work", "project:work or +urgent")

# Switch to work context
tw.apply_context("work")
work_tasks = tw.get_tasks()
```

### Personal Projects

```python
# Define personal context
tw.define_context("personal", "project:home or project:personal")

# Switch to personal context
tw.apply_context("personal")
personal_tasks = tw.get_tasks()
```

## Time Tracking with Start/Stop

### Track Work Sessions

```python
# Start working on a task
tw.start_task(uuid)

# Stop tracking time
tw.stop_task(uuid)

# Check if a task is currently being tracked
task = tw.get_task(uuid)
if task.start:
    print("Task is currently active")
```

## Batch Operations

### Process Multiple Tasks

```python
# Complete multiple tasks at once
tasks_to_complete = tw.get_tasks("project:work and status:pending")
for task in tasks_to_complete:
    tw.done_task(task.uuid)

# Update multiple tasks
tasks_to_update = tw.get_tasks("project:work and priority:L")
for task in tasks_to_update:
    input_dto = task_output_to_input(task)
    input_dto.priority = Priority.MEDIUM
    tw.modify_task(input_dto, task.uuid)
```

### Bulk Task Creation

```python
from taskwarrior import TaskInputDTO

tasks = [
    TaskInputDTO(description="Task 1", project="work"),
    TaskInputDTO(description="Task 2", project="work"),
    TaskInputDTO(description="Task 3", project="personal")
]

for task in tasks:
    tw.add_task(task)
```

## Filtering Strategies

### Complex Filters

```python
# Get overdue tasks
overdue = tw.get_tasks("due.before:today status:pending")

# Get tasks due this week
this_week = tw.get_tasks("due.after:today and due.before:next week status:pending")

# Get tasks with specific tags
tagged = tw.get_tasks("+urgent and +work")
```

### Dynamic Filtering

```python
def get_filtered_tasks(tw, project=None, priority=None, status=None):
    filters = []
    
    if project:
        filters.append(f"project:{project}")
    if priority:
        filters.append(f"priority:{priority}")
    if status:
        filters.append(f"status:{status}")
    
    filter_string = " and ".join(filters)
    return tw.get_tasks(filter_string) if filter_string else tw.get_tasks()

# Usage
work_tasks = get_filtered_tasks(tw, project="work")
urgent_work = get_filtered_tasks(tw, project="work", priority="H")
```
