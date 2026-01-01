from .task import TaskInternal, Priority, RecurrencePeriod
from .dto.task_dto import TaskDTO
from .main import TaskWarrior

# Expose Task as an alias for TaskInternal to maintain backward compatibility
Task = TaskInternal

__all__ = ['Task', 'Priority', 'RecurrencePeriod', 'TaskDTO', 'TaskWarrior']
