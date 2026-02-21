"""TaskWarrior Python API - Clean, user-friendly interface."""

# Main facade class
from .taskwarrior.dto.context_dto import ContextDTO

# Core DTOs
from .taskwarrior.dto.task_dto import TaskInputDTO, TaskOutputDTO
from .taskwarrior.dto.uda_dto import UdaConfig

# Enums
from .taskwarrior.enums import Priority, RecurrencePeriod, TaskStatus
from .taskwarrior.main import TaskWarrior

__all__ = [
    "TaskWarrior",
    "TaskInputDTO",
    "TaskOutputDTO",
    "ContextDTO",
    "UdaConfig",
    "TaskStatus",
    "Priority",
    "RecurrencePeriod",
]
