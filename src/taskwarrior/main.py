from __future__ import annotations

import logging
from uuid import UUID
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .adapters.taskwarrior_adapter import TaskWarriorAdapter
from .enums import TaskStatus

logger = logging.getLogger(__name__)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""

    def __init__(self, task_cmd: str = "task", taskrc_path: str | None = None, data_location: str | None = None):
        self.adapter = TaskWarriorAdapter(task_cmd, taskrc_path)

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
        filter_args: list[str] = [
            "status.not:" + TaskStatus.DELETED,
            "status.not:" + TaskStatus.COMPLETED,
        ],
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

    def set_context(self, context: str, filter_str: str) -> None:
        """Define a new context with the given filter."""
        return self.adapter.set_context(context, filter_str)

    def apply_context(self, context: str) -> None:
        """Apply a context (set it as current)."""
        return self.adapter.apply_context(context)

    def remove_context(self) -> None:
        """Remove the current context (set to none)."""
        return self.adapter.remove_context()

    def list_contexts(self) -> dict[str, str]:
        """List all defined contexts."""
        return self.adapter.list_contexts()

    def show_context(self) -> str | None:
        """Show the current context."""
        return self.adapter.show_context()

    def delete_context(self, context: str) -> None:
        """Delete a defined context."""
        return self.adapter.delete_context(context)

    def get_info(self) -> dict:
        """Get comprehensive TaskWarrior information."""
        return self.adapter.get_info()


def task_output_to_input(task_output: TaskOutputDTO) -> TaskInputDTO:
    """Convert TaskOutputDTO to TaskInputDTO for modification."""
    #data = task_output.model_dump(exclude={"uuid"})
    data = task_output.model_dump(exclude={"uuid", "id", "entry", "start", "end", "modified"})
    # Convert datetime fields to strings as required by TaskInputDTO
    datetime_fields = ["due", "scheduled", "wait", "until"]
    for field in datetime_fields:
        if field in data and data[field] is not None:
            data[field] = data[field].isoformat()
    return TaskInputDTO(**data)
