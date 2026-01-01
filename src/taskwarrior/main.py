from __future__ import annotations

import logging
from typing import List, Optional

from .task import TaskInternal
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .adapters.taskwarrior_adapter import TaskWarriorAdapter

logger = logging.getLogger(__name__)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""

    def __init__(self, task_cmd: str = "task", taskrc_path: Optional[str] = None):
        self.adapter = TaskWarriorAdapter(task_cmd, taskrc_path)

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Add a new task."""
        return self.adapter.add_task(task)

    def modify_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Modify an existing task."""
        return self.adapter.modify_task(task)

    def get_task(self, task_id_or_uuid: str) -> TaskOutputDTO:
        """Retrieve a task by ID or UUID."""
        return self.adapter.get_task(task_id_or_uuid)

    def get_tasks(self, filter_args: List[str] = ['status.not:deleted']) -> List[TaskOutputDTO]:
        """Get multiple tasks based on filters."""
        return self.adapter.get_tasks(filter_args)

    def get_recurring_task(self, uuid: str) -> TaskOutputDTO:
        """Get the recurring task (parent) by its UUID."""
        return self.adapter.get_recurring_task(uuid)

    def get_recurring_instances(self, uuid: str) -> List[TaskOutputDTO]:
        """Get all instances of a recurring task."""
        return self.adapter.get_recurring_instances(uuid)

    def delete_task(self, uuid: str) -> None:
        """Delete a task."""
        return self.adapter.delete_task(uuid)

    def purge_task(self, uuid: str) -> None:
        """Purge a task permanently."""
        return self.adapter.purge_task(uuid)

    def done_task(self, uuid: str) -> None:
        """Mark a task as done."""
        return self.adapter.done_task(uuid)

    def start_task(self, uuid: str) -> None:
        """Start a task."""
        return self.adapter.start_task(uuid)

    def stop_task(self, uuid: str) -> None:
        """Stop a task."""
        return self.adapter.stop_task(uuid)

    def annotate_task(self, uuid: str, annotation: str) -> None:
        """Add an annotation to a task."""
        return self.adapter.annotate_task(uuid, annotation)

    def set_context(self, context: str, filter_str: str) -> None:
        """Set a context."""
        return self.adapter.set_context(context, filter_str)

    def apply_context(self, context: str) -> None:
        """Apply a context."""
        return self.adapter.apply_context(context)

    def remove_context(self) -> None:
        """Remove the current context."""
        return self.adapter.remove_context()
