"""Main TaskWarrior facade class.

This module provides the primary interface for interacting with TaskWarrior.
"""

from __future__ import annotations

import logging
import os
from uuid import UUID

from .adapters.taskwarrior_adapter import TaskWarriorAdapter
from .dto.context_dto import ContextDTO
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .dto.uda_dto import UdaConfig
from .enums import TaskStatus
from .services.context_service import ContextService
from .services.uda_service import UdaService

logger = logging.getLogger(__name__)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior.

    This class provides a high-level interface for interacting with TaskWarrior
    via CLI commands. It supports all common task operations, context management,
    and User Defined Attributes (UDAs).

    Attributes:
        adapter: The underlying TaskWarriorAdapter instance.
        context_service: Service for managing contexts.
        uda_service: Service for managing UDAs.

    Example:
        Basic usage::

            from taskwarrior import TaskWarrior, TaskInputDTO

            tw = TaskWarrior()
            task = TaskInputDTO(description="Buy groceries")
            added = tw.add_task(task)
            print(f"Added task: {added.uuid}")

        With custom configuration::

            tw = TaskWarrior(
                taskrc_file="/path/to/.taskrc",
                data_location="/path/to/data",
            )
    """

    def __init__(
        self,
        task_cmd: str = "task",
        taskrc_file: str | None = None,
        data_location: str | None = None,
    ):
        """Initialize the TaskWarrior wrapper.

        Args:
            task_cmd: Path or name of the TaskWarrior binary. Defaults to "task".
            taskrc_file: Path to the taskrc configuration file. If None, uses
                the TASKRC environment variable or defaults to ~/.taskrc.
            data_location: Path to the task data directory. If None, uses
                the TASKDATA environment variable or the value in taskrc.

        Raises:
            TaskValidationError: If the TaskWarrior binary is not found.
        """
        if taskrc_file is None:
            taskrc_file = os.environ.get("TASKRC", "$HOME/.taskrc")
        if data_location is None:
            data_location = os.environ.get("TASKDATA") #, "$HOME/.task")

        self.adapter: TaskWarriorAdapter = TaskWarriorAdapter(
            task_cmd=task_cmd, taskrc_file=taskrc_file, data_location=data_location
        )
        self.context_service: ContextService = ContextService(self.adapter)
        self.uda_service: UdaService = UdaService(self.adapter)

        # Auto-load UDA definitions from taskrc
        self.uda_service.load_udas_from_taskrc()

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Add a new task to TaskWarrior.

        Args:
            task: The task data to create.

        Returns:
            The created task with UUID and other fields populated.

        Raises:
            TaskValidationError: If the task data is invalid or creation fails.

        Example:
            >>> task = TaskInputDTO(description="Call mom", tags=["family"])
            >>> added = tw.add_task(task)
            >>> print(added.uuid)
        """
        return self.adapter.add_task(task)

    def modify_task(
        self, task: TaskInputDTO, task_id_or_uuid: str | int | UUID
    ) -> TaskOutputDTO:
        """Modify an existing task.

        Args:
            task: The new task data to apply.
            task_id_or_uuid: The task ID (integer) or UUID to modify.

        Returns:
            The updated task.

        Raises:
            TaskNotFound: If the task doesn't exist.
            TaskValidationError: If the modification fails.

        Example:
            >>> task = TaskInputDTO(description="Updated description")
            >>> updated = tw.modify_task(task, "abc-123-uuid")
        """
        return self.adapter.modify_task(task, task_id_or_uuid)

    def get_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Retrieve a single task by ID or UUID.

        Args:
            task_id_or_uuid: The task ID (integer) or UUID to retrieve.

        Returns:
            The requested task.

        Raises:
            TaskNotFound: If the task doesn't exist.

        Example:
            >>> task = tw.get_task(1)  # By ID
            >>> task = tw.get_task("abc-123-uuid")  # By UUID
        """
        return self.adapter.get_task(task_id_or_uuid)

    def get_tasks(
        self,
        filter_args: str = f"(status.not:{TaskStatus.DELETED.value} and status.not:{TaskStatus.COMPLETED.value})",
    ) -> list[TaskOutputDTO]:
        """Retrieve multiple tasks matching a filter.

        By default, returns all pending and waiting tasks (excludes deleted
        and completed tasks).

        Args:
            filter_args: TaskWarrior filter expression. Defaults to excluding
                deleted and completed tasks.

        Returns:
            List of tasks matching the filter.

        Raises:
            TaskWarriorError: If the query fails.

        Example:
            >>> tasks = tw.get_tasks()  # All pending tasks
            >>> tasks = tw.get_tasks("project:work +urgent")
            >>> tasks = tw.get_tasks("status:completed")
        """
        return self.adapter.get_tasks(filter_args)

    def get_recurring_task(self, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
        """Get the parent recurring task template.

        Args:
            task_id_or_uuid: The UUID of a recurring task or one of its instances.

        Returns:
            The parent recurring task template.

        Raises:
            TaskNotFound: If the task doesn't exist.
        """
        return self.adapter.get_recurring_task(task_id_or_uuid)

    def get_recurring_instances(
        self, task_id_or_uuid: str | int | UUID
    ) -> list[TaskOutputDTO]:
        """Get all instances of a recurring task.

        Args:
            task_id_or_uuid: The UUID of the parent recurring task.

        Returns:
            List of task instances created from the recurring template.

        Raises:
            TaskNotFound: If the parent task doesn't exist.
        """
        return self.adapter.get_recurring_instances(task_id_or_uuid)

    def delete_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as deleted.

        The task is not permanently removed; use `purge_task` for that.

        Args:
            task_id_or_uuid: The task ID or UUID to delete.

        Raises:
            TaskNotFound: If the task doesn't exist.
        """
        return self.adapter.delete_task(task_id_or_uuid)

    def purge_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Permanently remove a task from the database.

        Unlike `delete_task`, this cannot be undone.

        Args:
            task_id_or_uuid: The task ID or UUID to purge.

        Raises:
            TaskNotFound: If the task doesn't exist.
        """
        return self.adapter.purge_task(task_id_or_uuid)

    def done_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as completed.

        Args:
            task_id_or_uuid: The task ID or UUID to complete.

        Raises:
            TaskNotFound: If the task doesn't exist.

        Example:
            >>> tw.done_task(1)
            >>> tw.done_task("abc-123-uuid")
        """
        return self.adapter.done_task(task_id_or_uuid)

    def start_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Start working on a task.

        Sets the task's start time to now, indicating active work.

        Args:
            task_id_or_uuid: The task ID or UUID to start.

        Raises:
            TaskNotFound: If the task doesn't exist.
        """
        return self.adapter.start_task(task_id_or_uuid)

    def stop_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Stop working on a task.

        Clears the task's start time.

        Args:
            task_id_or_uuid: The task ID or UUID to stop.

        Raises:
            TaskNotFound: If the task doesn't exist.
        """
        return self.adapter.stop_task(task_id_or_uuid)

    def annotate_task(self, task_id_or_uuid: str | int | UUID, annotation: str) -> None:
        """Add an annotation (note) to a task.

        Annotations are timestamped notes attached to tasks.

        Args:
            task_id_or_uuid: The task ID or UUID to annotate.
            annotation: The annotation text to add.

        Raises:
            TaskNotFound: If the task doesn't exist.

        Example:
            >>> tw.annotate_task(1, "Discussed with team, need more info")
        """
        return self.adapter.annotate_task(task_id_or_uuid, annotation)

    def define_context(self, context: str, filter_str: str) -> None:
        """Define a new context with the given filter.

        Contexts allow you to focus on a subset of tasks by applying
        filters automatically.

        Args:
            context: Name of the context to create.
            filter_str: TaskWarrior filter expression for this context.

        Raises:
            TaskWarriorError: If context creation fails.

        Example:
            >>> tw.define_context("work", "project:work or +urgent")
        """
        self.context_service.define_context(context, filter_str)

    def apply_context(self, context: str) -> None:
        """Activate a context.

        Once applied, all task queries will be filtered by this context.

        Args:
            context: Name of the context to apply.

        Raises:
            TaskWarriorError: If the context doesn't exist or application fails.

        Example:
            >>> tw.apply_context("work")
        """
        self.context_service.apply_context(context)

    def unset_context(self) -> None:
        """Deactivate the current context.

        Returns to showing all tasks without context filtering.

        Raises:
            TaskWarriorError: If unsetting fails.
        """
        self.context_service.unset_context()

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts.

        Returns:
            List of context definitions with names and filters.

        Raises:
            TaskWarriorError: If retrieval fails.
        """
        return self.context_service.get_contexts()

    def get_current_context(self) -> str | None:
        """Get the name of the currently active context.

        Returns:
            The context name, or None if no context is active.

        Raises:
            TaskWarriorError: If retrieval fails.
        """
        return self.context_service.get_current_context()

    def delete_context(self, context: str) -> None:
        """Delete a defined context.

        Args:
            context: Name of the context to delete.

        Raises:
            TaskWarriorError: If the context doesn't exist or deletion fails.
        """
        self.context_service.delete_context(context)

    def has_context(self, context: str) -> bool:
        """Check if a context exists.

        Args:
            context: Name of the context to check.

        Returns:
            True if the context exists, False otherwise.
        """
        return self.context_service.has_context(context)

    def get_info(self) -> dict[str, object]:
        """Get comprehensive TaskWarrior configuration information.

        Returns:
            Dictionary containing task_cmd path, taskrc_file path,
            options, and TaskWarrior version.

        Example:
            >>> info = tw.get_info()
            >>> print(info["version"])
        """
        return self.adapter.get_info()

    def task_calc(self, date_str: str) -> str:
        """Calculate a TaskWarrior date expression.

        Uses TaskWarrior's date calculation engine to evaluate
        date expressions like "today + 2weeks".

        Args:
            date_str: The date expression to calculate.

        Returns:
            The calculated date as an ISO format string.

        Raises:
            TaskWarriorError: If calculation fails.

        Example:
            >>> result = tw.task_calc("today + 2weeks")
            >>> print(result)  # "2026-02-14T00:00:00"
        """
        return self.adapter.task_calc(date_str)

    def date_validator(self, date_str: str) -> bool:
        """Validate a TaskWarrior date expression.

        Checks if a string is a valid TaskWarrior date format.

        Args:
            date_str: The date expression to validate.

        Returns:
            True if valid, False otherwise.

        Example:
            >>> tw.date_validator("next monday")  # True
            >>> tw.date_validator("invalid")  # False
        """
        return self.adapter.task_date_validator(date_str)

    def reload_udas(self) -> None:
        """Reload UDA definitions from the taskrc file.

        Use this method to refresh UDA definitions if they have been
        modified externally (e.g., by another program or manual edit).

        Example:
            >>> tw.reload_udas()
            >>> names = tw.get_uda_names()
        """
        self.uda_service.load_udas_from_taskrc()

    def get_uda_names(self) -> set[str]:
        """Get all defined UDA names.

        Returns:
            Set of UDA names currently defined in taskrc.

        Example:
            >>> names = tw.get_uda_names()
            >>> print(names)  # {"severity", "estimate", "customer"}
        """
        return self.uda_service.registry.get_uda_names()

    def get_uda_config(self, name: str) -> UdaConfig | None:
        """Get the configuration for a specific UDA.

        Args:
            name: The name of the UDA to retrieve.

        Returns:
            The UdaConfig if found, None otherwise.

        Example:
            >>> config = tw.get_uda_config("severity")
            >>> if config:
            ...     print(config.type)  # UdaType.STRING
            ...     print(config.values)  # ["low", "medium", "high"]
        """
        return self.uda_service.registry.get_uda(name)
