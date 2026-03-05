# Tips & Tricks

## Renaming Project Parents for Multiple Tasks

To rename the project parent for all matching tasks:

```bash
# Rename project "old-project" to "new-project"
task project:old-project modify project:new-project
```

## Bulk Task Operations

### Complete all tasks in a project:
```bash
task project:work done
```

### Modify multiple tasks at once:
```bash
task project:work +urgent modify priority:H
```

## Working with UDAs

### Update all tasks with a specific UDA value:
```bash
task uda:severity=high modify severity=medium
```

## Context Management

### Create a context that filters by urgency:
```bash
task context add urgent "priority:H or +urgent"
```

## Date Handling

### Find tasks due today:
```bash
task due:today
```

### Find tasks due tomorrow:
```bash
task due:tomorrow
```

## Performance Tips

### Use filters efficiently:
Instead of getting all tasks and filtering in Python, use TaskWarrior's built-in filtering:

```python
# Good - let TaskWarrior do the filtering
tasks = tw.get_tasks("project:work +urgent")

# Less efficient - get all tasks then filter
all_tasks = tw.get_tasks()
filtered_tasks = [t for t in all_tasks if t.project == "work" and t.priority == "H"]
```

## Advanced Task Manipulation

### Change task priority for all tasks in a project:
```bash
task project:work modify priority:M
```

### Archive completed tasks:
```bash
task status:completed modify project:archived
```

## Working with Dependencies

### Find tasks that depend on a specific task:
```bash
task depends:123
```

### Remove dependencies from a task:
```bash
task 123 modify depends:
```

## Task Filtering Patterns

### Find tasks with no project:
```bash
task project: none
```

### Find tasks with tags but no priority:
```bash
task +tag1 -priority
```

## Configuration Tips

### Reload UDA definitions after editing taskrc:
```python
tw.reload_udas()
```

### Get all defined projects:
```python
projects = tw.get_projects()
```
```