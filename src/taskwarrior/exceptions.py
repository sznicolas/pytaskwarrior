class TaskWarriorError(Exception):
    """Base exception for TaskWarrior errors."""
    pass

class TaskNotFound(TaskWarriorError):
    """Raised when a task is not found."""
    pass

class TaskValidationError(TaskWarriorError):
    """Raised when task validation fails."""
    pass
