from __future__ import annotations

import logging
import os
from uuid import UUID

from .adapters.taskwarrior_adapter import TaskWarriorAdapter
from .dto.context_dto import ContextDTO
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .enums import TaskStatus
from .services.context_service import ContextService
from .utils.dto_converter import task_output_to_input
from .services.uda_service import UdaService

logger = logging.getLogger(__name__)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""

    def __init__(
        self,
        task_cmd: str = "task",
        taskrc_file: str | None = None,
        data_location: str | None = None,
    ):
        if taskrc_file is None:
            taskrc_file = os.environ.get("TASKRC", "$HOME/.taskrc")
        if data_location is None:
            data_location = os.environ.get("TASKDATA") #, "$HOME/.task")

        self.adapter: TaskWarriorAdapter = TaskWarriorAdapter(
            task_cmd=task_cmd, taskrc_file=taskrc_file, data_location=data_location
        )
        self.context_service: ContextService = ContextService(self.adapter)
        self.uda_service: UdaService = UdaService(self.adapter)

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Add a new task."""
        return self.adapter.add_task(task)

    def modify_task(
        self, task: TaskInputDTO, task_id_or_uuid: str | int | UUID
    ) -> TaskOutputDTO:
        """Modify an existing task."""
        # Set the UUID on the task object
        return self.adapter.modify_task(task, task_id_or_uuid)

    def get_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Retrieve a task by ID or UUID."""
        return self.adapter.get_task(task_id_or_uuid)

    def get_tasks(
        self,
        filter_args: str = f"(status.not:{TaskStatus.DELETED.value} and status.not:{TaskStatus.COMPLETED.value})",
    ) -> list[TaskOutputDTO]:
        """Get multiple tasks based on filters."""
        return self.adapter.get_tasks(filter_args)

    def get_recurring_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Get the recurring task (parent) by its UUID."""
        return self.adapter.get_recurring_task(task_id_or_uuid)

    def get_recurring_instances(
        self, task_id_or_uuid: str | int | UUID
    ) -> list[TaskOutputDTO]:
        """Get all instances of a recurring task."""
        return self.adapter.get_recurring_instances(task_id_or_uuid)

    def delete_task(self, uuid: str | int | UUID) -> None:
        """Delete a task."""
        return self.adapter.delete_task(uuid)

    def purge_task(self, uuid: str | int | UUID) -> None:
        """Purge a task permanently."""
        return self.adapter.purge_task(uuid)

    def done_task(self, uuid: str | int | UUID) -> None:
        """Mark a task as done."""
        return self.adapter.done_task(uuid)

    def start_task(self, uuid: str | int | UUID) -> None:
        """Start a task."""
        return self.adapter.start_task(uuid)

    def stop_task(self, uuid: str | int | UUID) -> None:
        """Stop a task."""
        return self.adapter.stop_task(uuid)

    def annotate_task(self, uuid: str | int | UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        return self.adapter.annotate_task(uuid, annotation)

    def define_context(self, context: str, filter_str: str) -> None:
        """Define a new context with the given filter."""
        self.context_service.define_context(context, filter_str)

    def apply_context(self, context: str) -> None:
        """Apply a context (set it as current)."""
        self.context_service.apply_context(context)

    def unset_context(self) -> None:
        """Remove the current context (set to none)."""
        self.context_service.unset_context()

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts."""
        return self.context_service.get_contexts()

    def get_current_context(self) -> str | None:
        """Show the current context."""
        return self.context_service.get_current_context()

    def delete_context(self, context: str) -> None:
        """Delete a defined context."""
        self.context_service.delete_context(context)

    def has_context(self, context: str) -> None:
        """Return True if a context is active."""
        self.context_service.has_context(context)

    def get_info(self) -> dict:
        """Get comprehensive TaskWarrior information."""
        return self.adapter.get_info()

    def task_calc(self, date_str) -> str:
        """Calculate a TaskWarrior date string and return the result."""
        return self.adapter.task_calc(date_str)

    def date_validator(self, date_str) -> str:
        """Validate TaskWarrior date string format."""
        return self.adapter.task_date_validator(date_str)
