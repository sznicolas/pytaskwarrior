"""Main TaskWarrior facade class.

This module provides the primary interface for interacting with TaskWarrior.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from uuid import UUID

from .adapters.taskwarrior_adapter import TaskWarriorAdapter
from .dto.context_dto import ContextDTO
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .dto.uda_dto import UdaConfig
from .enums import TaskStatus  # noqa: F401 — re-exported for public API
from .services.context_service import ContextService
from .services.uda_service import UdaService

logger = logging.getLogger(__name__)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior.

    This class provides a high-level interface for interacting with TaskWarrior
    via CLI commands. It supports all common task operations, context management,
    and User Defined Attributes (UDAs).

    Note:
        When creating tasks with empty or None descriptions, the behavior depends
        on the underlying TaskWarrior CLI validation. Empty descriptions may be
        rejected with a TaskValidationError or passed through to TaskWarrior,
        which might reject them with a CLI error. The TaskInputDTO validation
        will reject empty or None descriptions before they reach TaskWarrior.

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
            data_location: Optional path to TaskWarrior data directory. If None,
                TASKDATA environment variable or taskrc value will be used.

        Raises:
            TaskConfigurationError: If the TaskWarrior binary is not found.
        """
        if taskrc_file is None:
            taskrc_file = os.environ.get("TASKRC", "$HOME/.taskrc")

        if data_location is None:
            data_location = os.environ.get("TASKDATA", None)

        from .config.config_store import ConfigStore

        self.config_store = ConfigStore(taskrc_file, data_location)
        self.adapter: TaskWarriorAdapter = TaskWarriorAdapter(
            task_cmd=task_cmd, config_store=self.config_store
        )
        self.context_service: ContextService = ContextService(self.adapter, self.config_store)
        self.uda_service: UdaService = UdaService(self.adapter, self.config_store)

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

    def modify_task(self, task: TaskInputDTO, task_id_or_uuid: str | int | UUID) -> TaskOutputDTO:
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
        filter: str = "",
        include_completed: bool = False,
        include_deleted: bool = False,
    ) -> list[TaskOutputDTO]:
        """Retrieve multiple tasks matching a filter.

        The filter expression is automatically wrapped in parentheses so
        compound expressions (e.g. ``"project:a or project:b"``) work
        correctly without needing manual parentheses.

        Deleted and completed tasks are excluded by default; use
        *include_completed* / *include_deleted* to override.

        If a context is active, its read_filter is applied in addition to the
        provided filter (combined with AND).

        Args:
            filter: TaskWarrior filter expression.  Examples::

                tw.get_tasks()                                  # pending only
                tw.get_tasks("project:work +urgent")            # project filter
                tw.get_tasks("project:dmc or project:pro")      # OR — works!
                tw.get_tasks("project:work", include_completed=True)

            include_completed: Include completed tasks (default ``False``).
            include_deleted: Include deleted tasks (default ``False``).

        Returns:
            List of tasks matching the filter.

        Raises:
            TaskWarriorError: If the query fails.
        """
        # Combine the user-provided filter with the active context's read_filter
        combined_filter = filter or ""
        try:
            current_context = self.get_current_context()
            if current_context:
                contexts = self.context_service.get_contexts()
                active = next((c for c in contexts if c.active or c.name == current_context), None)
                if active and active.read_filter:
                    ctx_read = active.read_filter.strip()
                    if combined_filter.strip():
                        combined_filter = f"{ctx_read} and ({combined_filter})"
                    else:
                        combined_filter = ctx_read
        except Exception as e:
            # Do not fail listing due to context lookup issues — log and proceed
            logger.debug("Failed to apply context read_filter to get_tasks(): %s", e)

        return self.adapter.get_tasks(
            filter=combined_filter,
            include_completed=include_completed,
            include_deleted=include_deleted,
        )

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

    def get_recurring_instances(self, task_id_or_uuid: str | int | UUID) -> list[TaskOutputDTO]:
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
            TaskOperationError: If the operation fails (e.g., task already deleted).
        """
        self.adapter.delete_task(task_id_or_uuid)

    def purge_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Permanently remove a task from the database.

        Unlike `delete_task`, this cannot be undone.

        Args:
            task_id_or_uuid: The task ID or UUID to purge.

        Raises:
            TaskOperationError: If the operation fails (e.g., task was not deleted first).
        """
        self.adapter.purge_task(task_id_or_uuid)

    def done_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Mark a task as completed.

        Args:
            task_id_or_uuid: The task ID or UUID to complete.

        Raises:
            TaskOperationError: If the operation fails (e.g., task is already completed).

        Example:
            >>> tw.done_task(1)
            >>> tw.done_task("abc-123-uuid")
        """
        self.adapter.done_task(task_id_or_uuid)

    def start_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Start working on a task.

        Sets the task's start time to now, indicating active work.

        Args:
            task_id_or_uuid: The task ID or UUID to start.

        Raises:
            TaskOperationError: If the operation fails (e.g., task is already started).
        """
        self.adapter.start_task(task_id_or_uuid)

    def stop_task(self, task_id_or_uuid: str | int | UUID) -> None:
        """Stop working on a task.

        Clears the task's start time.

        Args:
            task_id_or_uuid: The task ID or UUID to stop.

        Raises:
            TaskOperationError: If the operation fails (e.g., task was not started).
        """
        self.adapter.stop_task(task_id_or_uuid)

    def annotate_task(self, task_id_or_uuid: str | int | UUID, annotation: str) -> None:
        """Add an annotation (note) to a task.

        Annotations are timestamped notes attached to tasks.

        Args:
            task_id_or_uuid: The task ID or UUID to annotate.
            annotation: The annotation text to add.

        Raises:
            TaskOperationError: If the operation fails (e.g., task not found).

        Example:
            >>> tw.annotate_task(1, "Discussed with team, need more info")
        """
        self.adapter.annotate_task(task_id_or_uuid, annotation)

    def define_context(self, context: str, read_filter: str, write_filter: str) -> None:
        """Define a new context with explicit read and write filters.

        Both filters are required. Use an empty string for write_filter
        if you want a read-only context (new tasks won't inherit a project).

        Args:
            context:      Name of the context to create.
            read_filter:  Filter applied when listing/querying tasks.
            write_filter: Filter applied when creating or modifying tasks.

        Raises:
            TaskWarriorError: If context creation fails.

        Example:
            >>> tw.define_context("work", read_filter="project:work", write_filter="project:work")
            >>> tw.define_context("review", read_filter="+urgent or priority:H", write_filter="")
        """
        self.context_service.define_context(context, read_filter, write_filter)

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

    def is_sync_configured(self) -> bool:
        """Return True if synchronization is configured for this TaskWarrior instance."""
        return self.adapter.is_sync_configured()

    def synchronize(self) -> None:
        """Run TaskWarrior synchronization via ``task sync``.

        Delegates to the TaskWarrior CLI's built-in sync command. Synchronization
        settings (server address, credentials, or local path) must be configured
        in the taskrc file before calling this method.

        Raises:
            TaskSyncError: If no sync backend is configured or synchronization fails.

        Example:
            >>> tw = TaskWarrior(taskrc_file="/path/to/.taskrc")
            >>> tw.synchronize()  # requires sync.* settings in taskrc
        """
        self.adapter.synchronize()

    def get_info(self) -> dict[str, Any]:
        """Get comprehensive TaskWarrior configuration information.

        Returns:
            Dictionary containing task_cmd path, taskrc_file path,
            options, TaskWarrior version, and active context information.

        Example:
            >>> info = tw.get_info()
            >>> print(info["version"])
        """
        # Compose info from TaskWarrior instance, not adapter
        info: dict[str, Any] = {
            "task_cmd": str(self.adapter.task_cmd),
            "taskrc_file": str(self.config_store.taskrc_path),
            "options": self.adapter.cli_options,
            "version": self.adapter.get_version(),
        }

        # Add current context information (name and details) if available.
        current_context: str | None = None
        current_context_details: dict[str, Any] | None = None
        try:
            current_context = self.get_current_context()
            if current_context:
                contexts = self.context_service.get_contexts()
                active = next((c for c in contexts if c.active or c.name == current_context), None)
                if active:
                    current_context_details = {
                        "name": active.name,
                        "read_filter": active.read_filter,
                        "write_filter": active.write_filter,
                        "active": active.active,
                    }
        except Exception as e:
            # Do not fail get_info() for context lookup issues — log and return None fields
            logger.debug("Failed to retrieve current context for get_info(): %s", e)
            current_context = None
            current_context_details = None

        info.update({
            "current_context": current_context,
            "current_context_details": current_context_details,
        })

        return info

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

    def get_projects(self) -> list[str]:
        """Get all projects defined in TaskWarrior.

        Returns:
            List of project names.

        Example:
            >>> projects = tw.get_projects()
            >>> print(projects)
            ['dmc.fil.aretordre', 'dmc.fil.adérouler', 'perso', 'perso.orl', 'pro']
        """
        return self.adapter.get_projects()
