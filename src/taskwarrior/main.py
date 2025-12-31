from typing import List, Optional

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
            task_cmd: Path to the task command (can be full path or just "task")
            taskrc_path: Path to the taskrc configuration file
        """
        self.task_cmd = task_cmd
        self.taskrc_path = taskrc_path
        self.date_service = DateCalculationService()
        self.adapter = TaskWarriorAdapter(task_cmd=task_cmd, taskrc_path=self.taskrc_path)
        self.task_service = TaskService(self.adapter)

    def add_task(self, task: Task) -> Task:
        """
        Add a new task.

        Args:
            task: The task to add

        Returns:
            The added task with UUID and other metadata populated

        Example:
            >>> task = Task(description="Buy groceries")
            >>> added_task = client.add_task(task)
        """
        return self.task_service.add_task(task)

    def modify_task(self, task: Task) -> Task:
        """
        Modify an existing task.

        Args:
            task: The task to modify (must include UUID)

        Returns:
            The modified task

        Example:
            >>> task.uuid = "123e4567-e89b-12d3-a456-426614174000"
            >>> task.description = "Buy groceries and milk"
            >>> modified_task = client.modify_task(task)
        """
        return self.task_service.modify_task(task)

    def get_task(self, task_id_or_uuid: str) -> Task:
        """
        Get a specific task by ID or UUID.

        Args:
            task_id_or_uuid: Task ID (integer) or UUID string

        Returns:
            The requested task

        Example:
            >>> task = client.get_task("123e4567-e89b-12d3-a456-426614174000")
        """
        return self.task_service.get_task(task_id_or_uuid)

    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """
        Get tasks matching the given filters.

        Args:
            filter_args: List of filter arguments (e.g., ["status:pending"])

        Returns:
            List of matching tasks

        Example:
            >>> pending_tasks = client.get_tasks(["status:pending"])
        """
        return self.task_service.get_tasks(filter_args)

    def get_recurring_task(self, uuid: str) -> Task:
        """
        Get a recurring task by UUID.

        Args:
            uuid: The UUID of the recurring task

        Returns:
            The recurring task

        Example:
            >>> recurring_task = client.get_recurring_task("123e4567-e89b-12d3-a456-426614174000")
        """
        return self.task_service.get_recurring_task(uuid)

    def get_recurring_instances(self, uuid: str) -> List[Task]:
        """
        Get instances of a recurring task.

        Args:
            uuid: The UUID of the parent recurring task

        Returns:
            List of recurring instances

        Example:
            >>> instances = client.get_recurring_instances("123e4567-e89b-12d3-a456-426614174000")
        """
        return self.task_service.get_recurring_instances(uuid)

    def delete_task(self, uuid: str) -> None:
        """
        Delete a task.

        Args:
            uuid: The UUID of the task to delete

        Example:
            >>> client.delete_task("123e4567-e89b-12d3-a456-426614174000")
        """
        self.task_service.delete_task(uuid)

    def purge_task(self, uuid: str) -> None:
        """
        Purge a task permanently.

        Args:
            uuid: The UUID of the task to purge

        Example:
            >>> client.purge_task("123e4567-e89b-12d3-a456-426614174000")
        """
        self.task_service.purge_task(uuid)

    def done_task(self, uuid: str) -> None:
        """
        Mark a task as done.

        Args:
            uuid: The UUID of the task to complete

        Example:
            >>> client.done_task("123e4567-e89b-12d3-a456-426614174000")
        """
        self.task_service.done_task(uuid)

    def start_task(self, uuid: str) -> None:
        """
        Start a task.

        Args:
            uuid: The UUID of the task to start

        Example:
            >>> client.start_task("123e4567-e89b-12d3-a456-426614174000")
        """
        self.task_service.start_task(uuid)

    def stop_task(self, uuid: str) -> None:
        """
        Stop a task.

        Args:
            uuid: The UUID of the task to stop

        Example:
            >>> client.stop_task("123e4567-e89b-12d3-a456-426614174000")
        """
        self.task_service.stop_task(uuid)

    def annotate_task(self, uuid: str, annotation: str) -> None:
        """
        Add an annotation to a task.

        Args:
            uuid: The UUID of the task to annotate
            annotation: The annotation text

        Example:
            >>> client.annotate_task("123e4567-e89b-12d3-a456-426614174000", "Called supplier")
        """
        self.task_service.annotate_task(uuid, annotation)
