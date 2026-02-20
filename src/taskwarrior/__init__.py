"""pytaskwarrior - A modern Python wrapper for TaskWarrior.

This package provides a type-safe, Pythonic interface to TaskWarrior,
the command-line task management tool. It wraps the TaskWarrior CLI
and provides Pydantic models for task data validation.

Features:
    - Full CRUD operations for tasks
    - Type-safe DTOs with Pydantic validation
    - Context management (define, apply, switch)
    - User Defined Attributes (UDA) support
    - Recurring tasks support
    - Task annotations
    - Date calculations using TaskWarrior expressions

Example:
    Basic usage::

        from taskwarrior import TaskWarrior, TaskInputDTO, Priority

        tw = TaskWarrior()
        task = TaskInputDTO(
            description="Buy groceries",
            priority=Priority.HIGH,
            tags=["shopping"]
        )
        added = tw.add_task(task)
        print(f"Created task: {added.uuid}")

Requirements:
    - Python 3.12+
    - TaskWarrior 3.4+ installed and accessible via `task` command
"""

from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .dto.uda_dto import UdaConfig, UdaType
from .enums import Priority, RecurrencePeriod, TaskStatus
from .main import TaskWarrior
from .registry.uda_registry import UdaRegistry
from .utils.dto_converter import task_output_to_input

__version__ = "0.3.0"
__all__ = [
    "Priority",
    "RecurrencePeriod",
    "TaskStatus",
    "TaskInputDTO",
    "TaskOutputDTO",
    "TaskWarrior",
    "task_output_to_input",
    "UdaConfig",
    "UdaRegistry",
    "UdaType",
]

