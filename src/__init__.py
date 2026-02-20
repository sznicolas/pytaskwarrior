"""TaskWarrior Python API - Clean, user-friendly interface."""

# Main facade class
from .taskwarrior.main import TaskWarrior
# Core DTOs
from .taskwarrior.dto.task_dto import TaskInputDTO, TaskOutputDTO
from .taskwarrior.dto.context_dto import ContextDTO
from .taskwarrior.dto.uda_dto import UdaConfig

# Enums
from .taskwarrior.enums import TaskStatus, Priority, RecurrencePeriod

__all__ = [
    'TaskWarrior',
    'TaskInputDTO',
    'TaskOutputDTO',
    'ContextDTO',
    'UdaConfig',
    'TaskStatus',
    'Priority',
    'RecurrencePeriod'
]
#from .taskwarrior import (
#    Priority,
#    RecurrencePeriod,
#    TaskInputDTO,
#    TaskOutputDTO,
#    TaskStatus,
#    TaskWarrior,
#)
#
#__all__ = ['TaskStatus', 'Priority', 'RecurrencePeriod', 'TaskWarrior', 'TaskInputDTO', 'TaskOutputDTO']
