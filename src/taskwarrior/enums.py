from enum import Enum


class TaskStatus(str, Enum):
    """Task status values as defined by TaskWarrior.

    TaskWarrior assigns a status to each task that reflects its current
    state in the task lifecycle.

    Attributes:
        PENDING: Task is active and waiting to be completed.
        COMPLETED: Task has been marked as done.
        DELETED: Task has been deleted (but not purged).
        WAITING: Task is hidden until its wait date.
        RECURRING: Task is a recurring task template.

    Example:
        >>> from taskwarrior import TaskStatus
        >>> task = tw.get_task(uuid)
        >>> if task.status == TaskStatus.PENDING:
        ...     print("Task is still pending")
    """

    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    WAITING = "waiting"
    RECURRING = "recurring"


class Priority(str, Enum):
    """Task priority levels in TaskWarrior.

    Priority affects the urgency score of a task. Higher priority
    tasks appear first in task listings.

    Attributes:
        HIGH: High priority ("H"). Highest urgency boost.
        MEDIUM: Medium priority ("M"). Moderate urgency boost.
        LOW: Low priority ("L"). Minimal urgency boost.
        NONE: No priority set (""). No urgency impact.

    Example:
        >>> from taskwarrior import TaskInputDTO, Priority
        >>> task = TaskInputDTO(
        ...     description="Urgent task",
        ...     priority=Priority.HIGH
        ... )
    """

    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""


class RecurrencePeriod(str, Enum):
    """Supported recurrence periods for recurring tasks.

    TaskWarrior supports both standard keywords and custom duration expressions.

    Standard Keywords (Recommended):
        - DAILY, WEEKLY, MONTHLY, YEARLY
        - QUARTERLY, SEMIANNUALLY
        - HOURLY, MINUTELY, SECONDLY

    Custom Expressions (Also Valid):
        - "2weeks" (Every two weeks)
        - "3days" (Every three days)
        - "every 10 days"
        - "2months"
        - "6months"

    Example (Standard):
        >>> task = TaskInputDTO(description="Daily standup", recur=RecurrencePeriod.DAILY)

    Example (Custom):
        >>> task = TaskInputDTO(description="Bi-weekly report", recur="2weeks")
        # Note: Passing a string directly bypasses the Enum but is fully supported by TaskWarrior.
    """

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"
    HOURLY = "hourly"
    MINUTELY = "minutely"
    SECONDLY = "secondly"
