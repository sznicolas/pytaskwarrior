# Working with Contexts

Contexts allow you to focus on specific subsets of tasks by applying
filters automatically.

## Defining Contexts

```python
from taskwarrior import TaskWarrior

tw = TaskWarrior()

# Create contexts for different workflows
tw.define_context("work", read_filter="project:work or +urgent", write_filter="project:work or +urgent")
tw.define_context("home", read_filter="project:home or project:personal", write_filter="project:home or project:personal")
tw.define_context("errands", read_filter="+errand or +shopping", write_filter="+errand or +shopping")
```

## Applying Contexts

```python
# Switch to work context
tw.apply_context("work")

# Now get_tasks() only returns work-related tasks
work_tasks = tw.get_tasks()
print(f"Found {len(work_tasks)} work tasks")
```

## Checking Current Context

```python
current = tw.get_current_context()
if current:
    print(f"Current context: {current}")
else:
    print("No context active")
```

## Listing Contexts

```python
contexts = tw.get_contexts()
for ctx in contexts:
    print(f"{ctx.name}: read={ctx.read_filter} write={ctx.write_filter}")
```

## Removing Context

```python
# Deactivate current context (show all tasks again)
tw.unset_context()
```

## Deleting Contexts

```python
# Remove a context definition
tw.delete_context("errands")
```

## Checking Context Existence

```python
if tw.has_context("work"):
    tw.apply_context("work")
else:
    tw.define_context("work", read_filter="project:work", write_filter="project:work")
    tw.apply_context("work")
```

## Example Workflow

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

tw = TaskWarrior()

# Setup contexts once
if not tw.has_context("focus"):
    tw.define_context("focus", read_filter="priority:H or +urgent", write_filter="priority:H or +urgent")

# Morning routine: check high-priority items
tw.apply_context("focus")
urgent_tasks = tw.get_tasks()
print(f"🔥 {len(urgent_tasks)} urgent tasks today")

for task in urgent_tasks[:5]:
    print(f"  - {task.description}")

# Switch to normal view
tw.unset_context()
```

## Context Best Practices

1. **Keep filters simple** - Complex filters can be slow
2. **Use meaningful names** - `work`, `home`, `urgent` are clear
3. **Combine with projects** - `project:work.meetings` works well
4. **Test before applying** - Use `tw.get_tasks(filter)` first
