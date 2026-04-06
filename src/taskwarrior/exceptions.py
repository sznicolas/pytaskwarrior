"""Custom exceptions for pytaskwarrior.

This module defines the exception hierarchy used throughout the package.
All exceptions inherit from TaskWarriorError for easy catching.
"""


class TaskWarriorError(Exception):
    """Base exception for all TaskWarrior-related errors.

    All custom exceptions in pytaskwarrior inherit from this class,
    allowing you to catch all library errors with a single except clause.

    Example:
        >>> try:
        ...     tw.get_task("nonexistent-uuid")
        ... except TaskWarriorError as e:
        ...     print(f"TaskWarrior error: {e}")
    """

    pass


class TaskSyncError(TaskWarriorError):
    """Raised when a synchronization error occurs in TaskWarrior.

    This exception is used to signal errors encountered during sync operations.
    """

    pass


class TaskNotFound(TaskWarriorError):  # noqa: N818
    """Raised when a requested task does not exist.

    This exception is raised when attempting to retrieve, modify,
    delete, or perform any operation on a task that doesn't exist
    in the TaskWarrior database.

    Example:
        >>> try:
        ...     task = tw.get_task("nonexistent-uuid")
        ... except TaskNotFound:
        ...     print("Task not found")
    """

    pass


class TaskValidationError(TaskWarriorError):
    """Raised when task data validation fails.

    This exception is raised when:
    - Task description is empty
    - Required fields are missing
    - Field values are invalid
    - TaskWarrior rejects the task data

    Example:
        >>> try:
        ...     task = TaskInputDTO(description="")  # Empty description
        ... except TaskValidationError as e:
        ...     print(f"Invalid task: {e}")
    """

    pass


class TaskConfigurationError(TaskWarriorError):
    """Raised when a configuration or environment error is detected.

    This exception is raised when:
    - The TaskWarrior binary is not found in PATH
    - The taskrc configuration file is missing or unreadable
    - Required environment setup is invalid

    Example:
        >>> try:
        ...     tw = TaskWarrior(task_cmd="nonexistent-binary")
        ... except TaskConfigurationError as e:
        ...     print(f"Configuration error: {e}")
    """

    pass


class TaskOperationError(TaskWarriorError):
    """Raised when a task operation fails on an existing task.

    This exception is raised when a write operation (delete, complete, start,
    stop, annotate, purge, modify) fails, for reasons other than the task not
    being found. Examples:
    - Marking an already-completed task as done
    - Starting a task that is already active
    - Annotating with an empty annotation text

    Example:
        >>> try:
        ...     tw.done_task(uuid)
        ... except TaskOperationError as e:
        ...     print(f"Operation failed: {e}")
    """

    pass
