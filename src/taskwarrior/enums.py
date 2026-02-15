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

    Defines how often a recurring task should repeat. When a recurring
    task is completed, TaskWarrior automatically creates the next instance.

    Attributes:
        DAILY: Task repeats every day.
        WEEKLY: Task repeats every week.
        MONTHLY: Task repeats every month.
        YEARLY: Task repeats every year.
        QUARTERLY: Task repeats every quarter (3 months).
        SEMIANNUALLY: Task repeats every 6 months.
        HOURLY: Task repeats every hour.
        MINUTELY: Task repeats every minute.
        SECONDLY: Task repeats every second.

    Example:
        >>> from taskwarrior import TaskInputDTO, RecurrencePeriod
        >>> weekly_task = TaskInputDTO(
        ...     description="Weekly review",
        ...     due="monday",
        ...     recur=RecurrencePeriod.WEEKLY
        ... )
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
