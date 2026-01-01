class TaskWarriorError(Exception):
    """Base exception for TaskWarrior related errors."""
    pass


class TaskNotFound(TaskWarriorError):
    """Raised when a task is not found."""
    pass


class TaskValidationError(TaskWarriorError):
    """Raised when a task validation fails."""
    pass
