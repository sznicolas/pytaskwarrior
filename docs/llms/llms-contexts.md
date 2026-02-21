# Context Workflows

Contexts in TaskWarrior allow you to focus on specific subsets of tasks by applying filters automatically.

## Context Definition and Application

### Creating Contexts

```python
from taskwarrior import TaskWarrior

tw = TaskWarrior()

# Create contexts for different workflows
tw.define_context("work", "project:work or +urgent")
tw.define_context("home", "project:home or project:personal")
tw.define_context("errands", "+errand or +shopping")
```

### Applying Contexts

```python
# Switch to work context
tw.apply_context("work")

# Now get_tasks() only returns work-related tasks
work_tasks = tw.get_tasks()
print(f"Found {len(work_tasks)} work tasks")
```

### Checking Current Context

```python
current = tw.get_current_context()
if current:
    print(f"Current context: {current}")
else:
    print("No context active")
```

### Listing Contexts

```python
contexts = tw.get_contexts()
for ctx in contexts:
    print(f"{ctx.name}: {ctx.filter}")
```

## Context Switching Patterns

### Workflow-Based Context Switching

```python
def switch_to_work_context(tw):
    """Switch to work context if not already active"""
    if not tw.has_context("work"):
        tw.define_context("work", "project:work or +urgent")
    tw.apply_context("work")

def switch_to_home_context(tw):
    """Switch to home context if not already active"""
    if not tw.has_context("home"):
        tw.define_context("home", "project:home or project:personal")
    tw.apply_context("home")
```

### Context-Specific Operations

```python
# Work context operations
tw.apply_context("work")
work_tasks = tw.get_tasks()
for task in work_tasks:
    print(f"Work: {task.description}")

# Home context operations
tw.apply_context("home")
home_tasks = tw.get_tasks()
for task in home_tasks:
    print(f"Home: {task.description}")
```

## Predefined Context Examples

### Focus Context

```python
# Create a focus context for high-priority items
if not tw.has_context("focus"):
    tw.define_context("focus", "priority:H or +urgent")

# Morning routine: check high-priority items
tw.apply_context("focus")
urgent_tasks = tw.get_tasks()
print(f"🔥 {len(urgent_tasks)} urgent tasks today")
```

### Time-Based Contexts

```python
# Morning context (tasks due today)
tw.define_context("morning", "due.today or status:pending")

# Evening context (tasks due tomorrow)
tw.define_context("evening", "due.tomorrow or status:pending")
```

## Context Best Practices

### Keep Filters Simple

```python
# Good - simple and fast
tw.define_context("work", "project:work")

# Avoid - complex filters that slow down queries
tw.define_context("work", "project:work and (priority:H or +urgent) and not +done")
```

### Use Meaningful Names

```python
# Clear context names
tw.define_context("work", "project:work or +urgent")
tw.define_context("home", "project:home or project:personal")

# Less clear context names
tw.define_context("ctx1", "project:work or +urgent")
tw.define_context("ctx2", "project:home or project:personal")
```

### Combine with Projects

```python
# Project-specific contexts work well
tw.define_context("work.meetings", "project:work.meetings")
tw.define_context("work.research", "project:work.research")
```

### Test Before Applying

```python
# Test filter first before applying context
test_tasks = tw.get_tasks("project:work or +urgent")
print(f"Test found {len(test_tasks)} tasks")

# Then apply context
tw.define_context("work", "project:work or +urgent")
tw.apply_context("work")
```

## Advanced Filtering with Contexts

### Nested Contexts

```python
# Create a nested context for specific projects within work
tw.define_context("work.project1", "project:work.project1")
tw.define_context("work.project2", "project:work.project2")

# Switch between specific project contexts
tw.apply_context("work.project1")
project1_tasks = tw.get_tasks()
```

### Context Composition

```python
# Create a context that combines multiple filters
tw.define_context("urgent-work", "project:work and priority:H")
tw.define_context("pending-urgent", "status:pending and +urgent")

# Use composition for complex workflows
tw.apply_context("urgent-work")
urgent_work_tasks = tw.get_tasks()
```

## Related Documentation

- [Task Management Patterns](llms-task-patterns.md) - Common patterns for task management
- [UDA Implementation](llms-udas.md) - User Defined Attributes best practices
- [Task Dependencies](llms-dependencies.md) - Complex task relationships
