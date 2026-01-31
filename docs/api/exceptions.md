# Exceptions

Custom exceptions for error handling.

All exceptions inherit from `TaskWarriorError`, allowing you to catch
all library errors with a single except clause.

```python
from taskwarrior.exceptions import TaskWarriorError, TaskNotFound

try:
    task = tw.get_task("nonexistent-uuid")
except TaskNotFound:
    print("Task not found")
except TaskWarriorError as e:
    print(f"TaskWarrior error: {e}")
```

## TaskWarriorError

::: taskwarrior.exceptions.TaskWarriorError
    options:
      show_source: false
      heading_level: 3

## TaskNotFound

::: taskwarrior.exceptions.TaskNotFound
    options:
      show_source: false
      heading_level: 3

## TaskValidationError

::: taskwarrior.exceptions.TaskValidationError
    options:
      show_source: false
      heading_level: 3
