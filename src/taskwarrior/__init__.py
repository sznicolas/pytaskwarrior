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

import importlib.metadata

from .dto.annotation_dto import AnnotationDTO
from .dto.context_dto import ContextDTO
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .dto.uda_dto import UdaConfig, UdaType
from .enums import Priority, RecurrencePeriod, TaskStatus
from .exceptions import (
    TaskConfigurationError,
    TaskNotFound,
    TaskOperationError,
    TaskSyncError,
    TaskValidationError,
    TaskWarriorError,
)
from .main import TaskWarrior
from .registry.uda_registry import UdaRegistry
from .utils.dto_converter import task_output_to_input

__version__ = importlib.metadata.version("pytaskwarrior")
# Backwards-compatible alias
version = __version__

__all__ = [
    "AnnotationDTO",
    "ContextDTO",
    "version",
    "Priority",
    "RecurrencePeriod",
    "TaskStatus",
    "TaskConfigurationError",
    "TaskInputDTO",
    "TaskNotFound",
    "TaskOperationError",
    "TaskOutputDTO",
    "TaskSyncError",
    "TaskValidationError",
    "TaskWarrior",
    "TaskWarriorError",
    "task_output_to_input",
    "UdaConfig",
    "UdaRegistry",
    "UdaType",
]
