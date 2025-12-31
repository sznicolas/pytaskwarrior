from typing import List, Optional, Union

from .adapters.taskwarrior_adapter import TaskWarriorAdapter

from .services.date_calculation_service import DateCalculationService
from .services.task_service import TaskService
from .task import Task


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""

    def __init__(self, task_cmd: str = "task", taskrc_path: Optional[str] = None):
        """
        Initialize the TaskWarrior API wrapper.

        Args:
            taskrc_path: Path to the taskrc configuration file
        """
        self.taskrc_path = taskrc_path
        self.date_service = DateCalculationService()
        self.adapter = TaskWarriorAdapter(task_cmd=task_cmd, taskrc_path=self.taskrc_path)
        self.task_service = TaskService(self.adapter)

    def add_task(self, task) -> Task:
        """Add a new task."""
        return self.task_service.add_task(task)

    def modify_task(self, task) -> Task:
        """Modify an existing task."""
        return self.task_service.modify_task(task)

    def get_task(self, task_id_or_uuid: Union[str, int]) -> "Task":
        """Get a specific task by ID or UUID."""
        return self.task_service.get_task(task_id_or_uuid)

    def get_tasks(self, filter_args: List[str]) -> List["Task"]:
        """Get tasks matching the given filters."""
        return self.task_service.get_tasks(filter_args)

    def get_recurring_task(self, uuid) -> "Task":
        """Get a recurring task by UUID."""
        return self.task_service.get_recurring_task(uuid)

    def get_recurring_instances(self, uuid) -> List["Task"]:
        """Get instances of a recurring task."""
        return self.task_service.get_recurring_instances(uuid)

    def delete_task(self, uuid) -> None:
        """Delete a task."""
        self.task_service.delete_task(uuid)

    def purge_task(self, uuid) -> None:
        """Purge a task."""
        self.task_service.purge_task(uuid)

    def done_task(self, uuid) -> None:
        """Mark a task as done."""
        self.task_service.done_task(uuid)

    def start_task(self, uuid) -> None:
        """Start a task."""
        self.task_service.start_task(uuid)

    def stop_task(self, uuid) -> None:
        """Stop a task."""
        self.task_service.stop_task(uuid)

    def annotate_task(self, uuid, annotation: str) -> None:
        """Add an annotation to a task."""
        self.task_service.annotate_task(uuid, annotation)
