"""Main TaskWarrior facade class.

This module provides the primary interface for interacting with TaskWarrior.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .adapters import AdapterProtocol
from .adapters.taskchampion_adapter import TaskChampionAdapter
from .adapters.taskwarrior_adapter import TaskWarriorAdapter
from .dto.context_dto import ContextDTO
from .dto.task_dto import TaskInputDTO, TaskOutputDTO
from .dto.task_id import TaskRef
from .dto.uda_dto import UdaConfig
from .enums import TaskStatus  # noqa: F401 — re-exported for public API
from .services.context_service import ContextService
from .services.uda_service import UdaService

logger = logging.getLogger(__name__)


class TaskWarrior:
    """A Python API wrapper for TaskWarrior.

    By default uses :class:`~taskwarrior.adapters.taskchampion_adapter.TaskChampionAdapter`
    for direct SQLite access — no ``task`` binary required.  Pass
    ``task_cmd="task"`` (or any path to the binary) to use the classic CLI
    adapter instead.

    Attributes:
        adapter: The underlying adapter instance (TaskChampion or CLI).
        context_service: Service for managing contexts.
        uda_service: Service for managing UDAs.

    Example:
        Basic usage (no binary needed)::

            from taskwarrior import TaskWarrior, TaskInputDTO

            tw = TaskWarrior()
            task = TaskInputDTO(description="Buy groceries")
            added = tw.add_task(task)
            print(f"Added task: {added.uuid}")

        Explicit CLI adapter::

            tw = TaskWarrior(task_cmd="task")

        Custom paths::

            tw = TaskWarrior(
                taskrc_file="/path/to/.taskrc",
                data_location="/path/to/data",
            )
    """

    def __init__(
        self,
        task_cmd: str | None = None,
        taskrc_file: str | None = None,
        data_location: str | None = None,
        adapter: AdapterProtocol | None = None,
    ):
        """Initialize the TaskWarrior wrapper.

        Args:
            task_cmd: Path or name of the TaskWarrior binary.  When ``None``
                (the default) the :class:`~taskwarrior.adapters.taskchampion_adapter.TaskChampionAdapter`
                is used and no ``task`` binary is required.  Pass ``"task"``
                (or an absolute path) to use the CLI adapter instead.
            taskrc_file: Path to the taskrc configuration file. If None, uses
                the TASKRC environment variable or defaults to ~/.taskrc.
            data_location: Path to the TaskWarrior data directory. If None,
                uses the TASKDATA environment variable, the value from taskrc,
                or ``~/.task`` as a last resort.
            adapter: Explicit adapter instance.  Overrides *task_cmd* for CRUD
                operations.  Useful for injecting a custom or in-memory adapter
                (e.g. ``TaskChampionAdapter(data_location=None)`` for tests).
        """
        if taskrc_file is None:
            taskrc_file = os.environ.get("TASKRC", "$HOME/.taskrc")

        if data_location is None:
            data_location = os.environ.get("TASKDATA", None)

        from .config.config_store import ConfigStore

        self.config_store = ConfigStore(taskrc_file, data_location)

        _cli: TaskWarriorAdapter | None = None

        if adapter is not None:
            # Caller supplied an explicit adapter — use it directly.
            if isinstance(adapter, TaskWarriorAdapter):
                _cli = adapter
            self.adapter: AdapterProtocol = adapter

        elif task_cmd is not None:
            # Explicit CLI mode: build a TaskWarriorAdapter.
            _cli = TaskWarriorAdapter(task_cmd=task_cmd, config_store=self.config_store)
            self.adapter = _cli

        else:
            # Default mode: TaskChampionAdapter — no binary required.
            import uuid as _uuid

            sync_cfg = self.config_store.get_sync_config()
            sync_server_url = sync_cfg.get("sync.server.origin")
            sync_local_dir = sync_cfg.get("sync.local.server_dir")
            sync_client_id = sync_cfg.get("sync.server.client_id")
            sync_encryption_secret = sync_cfg.get("sync.encryption.secret")

            # Persist a stable client_id if remote sync is configured but none is set.
            if sync_server_url and not sync_client_id:
                sync_client_id = str(_uuid.uuid4())
                self.config_store.set_value("sync.server.client_id", sync_client_id)

            self.adapter = TaskChampionAdapter(
                data_location=self.config_store.data_location,
                sync_server_url=sync_server_url,
                sync_client_id=sync_client_id,
                sync_encryption_secret=sync_encryption_secret,
                sync_local_server_dir=sync_local_dir,
            )

        self._cli_adapter: TaskWarriorAdapter | None = _cli

        # Services write directly to .taskrc — no CLI needed.
        self._context_service: ContextService = ContextService(self.config_store)
        self._uda_service: UdaService = UdaService(self.config_store)
        self._uda_service.load_udas_from_store()

    # ------------------------------------------------------------------
    # Public task API
    # ------------------------------------------------------------------

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

    def modify_task(self, task: TaskInputDTO, task_id: TaskRef) -> TaskOutputDTO:
        """Modify an existing task.

        Args:
            task: The new task data to apply.
            task_id: The task ID (integer) or UUID to modify.

        Returns:
            The updated task.

        Raises:
            TaskNotFound: If the task doesn't exist.
            TaskValidationError: If the modification fails.

        Example:
            >>> task = TaskInputDTO(description="Updated description")
            >>> updated = tw.modify_task(task, "abc-123-uuid")
        """
        return self.adapter.modify_task(task, task_id)

    def get_task(self, task_id: TaskRef) -> TaskOutputDTO:
        """Retrieve a single task by ID or UUID.

        Args:
            task_id: The task ID (integer) or UUID to retrieve.

        Returns:
            The requested task.

        Raises:
            TaskNotFound: If the task doesn't exist.

        Example:
            >>> task = tw.get_task(1)  # By ID
            >>> task = tw.get_task("abc-123-uuid")  # By UUID
            >>> task = tw.get_task(TaskID(1))  # Using TaskID
        """
        return self.adapter.get_task(task_id)

    def get_tasks(
        self,
        filter: str = "",
        include_completed: bool = False,
        include_deleted: bool = False,
        apply_context: bool = True,
    ) -> list[TaskOutputDTO]:
        """Retrieve multiple tasks matching a filter.

        The filter expression is automatically wrapped in parentheses so
        compound expressions (e.g. ``"project:a or project:b"``) work
        correctly without needing manual parentheses.

        Deleted and completed tasks are excluded by default; use
        *include_completed* / *include_deleted* to override.

        If a context is active and *apply_context* is ``True`` (the default),
        its read_filter is applied in addition to the provided filter
        (combined with AND).  Pass ``apply_context=False`` to bypass context
        injection and query raw tasks regardless of the active context.

        Args:
            filter: TaskWarrior filter expression.  Examples::

                tw.get_tasks()                                  # pending only
                tw.get_tasks("project:work +urgent")            # project filter
                tw.get_tasks("project:dmc or project:pro")      # OR — works!
                tw.get_tasks("project:work", include_completed=True)
                tw.get_tasks(apply_context=False)               # bypass context

            include_completed: Include completed tasks (default ``False``).
            include_deleted: Include deleted tasks (default ``False``).
            apply_context: When ``True`` (default), the active context's
                read_filter is automatically prepended to the query.  Set to
                ``False`` to query tasks without any context filter.

        Returns:
            List of tasks matching the filter.

        Raises:
            TaskWarriorError: If the query fails.
        """
        combined_filter = filter or ""
        if apply_context:
            try:
                current_context = self.get_current_context()
                if current_context:
                    contexts = self._context_service.get_contexts()
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

    def get_recurring_task(self, task_id: TaskRef) -> TaskOutputDTO:
        """Get the parent recurring task template.

        Args:
            task_id: The UUID of a recurring task or one of its instances.

        Returns:
            The parent recurring task template.

        Raises:
            TaskNotFound: If the task doesn't exist.
        """
        return self.adapter.get_recurring_task(task_id)

    def get_recurring_instances(self, task_id: TaskRef) -> list[TaskOutputDTO]:
        """Get all instances of a recurring task.

        Args:
            task_id: The UUID of the parent recurring task.

        Returns:
            List of task instances created from the recurring template.

        Raises:
            TaskNotFound: If the parent task doesn't exist.
        """
        return self.adapter.get_recurring_instances(task_id)

    def delete_task(self, task_id: TaskRef) -> None:
        """Mark a task as deleted.

        The task is not permanently removed; use `purge_task` for that.

        Args:
            task_id: The task ID or UUID to delete.

        Raises:
            TaskOperationError: If the operation fails (e.g., task already deleted).
        """
        self.adapter.delete_task(task_id)

    def purge_task(self, task_id: TaskRef) -> None:
        """Permanently remove a task from the database.

        Unlike `delete_task`, this cannot be undone.

        Args:
            task_id: The task ID or UUID to purge.

        Raises:
            TaskOperationError: If the operation fails (e.g., task was not deleted first).
        """
        self.adapter.purge_task(task_id)

    def done_task(self, task_id: TaskRef) -> None:
        """Mark a task as completed.

        Args:
            task_id: The task ID or UUID to complete.

        Raises:
            TaskOperationError: If the operation fails (e.g., task is already completed).

        Example:
            >>> tw.done_task(1)
            >>> tw.done_task("abc-123-uuid")
            >>> tw.done_task(TaskID(1))
        """
        self.adapter.done_task(task_id)

    def start_task(self, task_id: TaskRef) -> None:
        """Start working on a task.

        Sets the task's start time to now, indicating active work.

        Args:
            task_id: The task ID or UUID to start.

        Raises:
            TaskOperationError: If the operation fails (e.g., task is already started).
        """
        self.adapter.start_task(task_id)

    def stop_task(self, task_id: TaskRef) -> None:
        """Stop working on a task.

        Clears the task's start time.

        Args:
            task_id: The task ID or UUID to stop.

        Raises:
            TaskOperationError: If the operation fails (e.g., task was not started).
        """
        self.adapter.stop_task(task_id)

    def annotate_task(self, task_id: TaskRef, annotation: str) -> None:
        """Add an annotation (note) to a task.

        Annotations are timestamped notes attached to tasks.

        Args:
            task_id: The task ID or UUID to annotate.
            annotation: The annotation text to add.

        Raises:
            TaskOperationError: If the operation fails (e.g., task not found).

        Example:
            >>> tw.annotate_task(1, "Discussed with team, need more info")
        """
        self.adapter.annotate_task(task_id, annotation)

    def define_context(self, context: ContextDTO) -> None:
        """Define a new context from a ContextDTO.

        The context argument must be a ContextDTO instance containing
        name, read_filter and write_filter.

        Args:
            context: ContextDTO instance with the context definition.

        Raises:
            TaskWarriorError: If context creation fails.
        """
        self._context_service.define_context(context)

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
        self._context_service.apply_context(context)

    def unset_context(self) -> None:
        """Deactivate the current context.

        Returns to showing all tasks without context filtering.

        Raises:
            TaskWarriorError: If unsetting fails.
        """
        self._context_service.unset_context()

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts.

        Returns:
            List of context definitions with names and filters.

        Raises:
            TaskWarriorError: If retrieval fails.
        """
        return self._context_service.get_contexts()

    def get_current_context(self) -> str | None:
        """Get the name of the currently active context.

        Returns:
            The context name, or None if no context is active.

        Raises:
            TaskWarriorError: If retrieval fails.
        """
        return self._context_service.get_current_context()

    def delete_context(self, context: str) -> None:
        """Delete a defined context.

        Args:
            context: Name of the context to delete.

        Raises:
            TaskWarriorError: If the context doesn't exist or deletion fails.
        """
        self._context_service.delete_context(context)

    def has_context(self, context: str) -> bool:
        """Check if a context exists.

        Args:
            context: Name of the context to check.

        Returns:
            True if the context exists, False otherwise.
        """
        return self._context_service.has_context(context)

    def is_sync_configured(self) -> bool:
        """Return True if synchronization is configured for this TaskWarrior instance."""
        return self.adapter.is_sync_configured()

    def has_local_changes(self) -> bool:
        """Return ``True`` if there are local changes not yet pushed to the sync server.

        For the :class:`~taskwarrior.adapters.taskchampion_adapter.TaskChampionAdapter`
        this queries the real pending-operations count from the SQLite replica.
        For the CLI adapter this always returns ``False`` (the CLI manages sync
        state internally).

        .. note::
            This only reflects the *local* side.  New tasks or changes on the
            remote server cannot be detected without calling :meth:`synchronize`.

        Example:
            >>> tw = TaskWarrior()
            >>> tw.add_task(TaskInputDTO(description="Buy milk"))
            >>> tw.has_local_changes()   # True — not yet synced
            >>> tw.synchronize()
            >>> tw.has_local_changes()   # False — fully synced
        """
        return self.adapter.has_local_changes()

    def pending_local_ops_count(self) -> int:
        """Return the number of local operations pending synchronization.

        Useful for logging or progress display.  ``0`` means the local replica
        is fully synced (from the local side).
        Returns ``0`` for the CLI adapter.
        """
        return self.adapter.pending_local_ops_count()

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
            Dictionary with the following keys:

            * ``backend_type`` — ``"taskchampion"`` or ``"taskwarrior-cli"``
            * ``backend_version`` — version string of the active backend
            * ``task_cmd`` — path to the ``task`` binary (``None`` for TC adapter)
            * ``taskrc_file`` — path to the active ``.taskrc``
            * ``data_location`` — resolved path to the data directory, or ``None``
              when an in-memory database is used
            * ``options`` — CLI options list (``None`` for TC adapter)
            * ``sync_configured`` — ``True`` when a sync backend is active
            * ``sync_backend`` — ``"remote"``, ``"local"``, or ``None``
              (TC adapter only; absent for CLI adapter)
            * ``sync_server_url`` — remote sync server URL (TC adapter only)
            * ``sync_local_server_dir`` — local sync server directory (TC adapter only)
            * ``sync_client_id`` — client UUID used for remote sync (TC adapter only)
            * ``current_context`` — name of the active context, or ``None``
            * ``current_context_details`` — dict with context details, or ``None``

        Example:
            >>> info = tw.get_info()
            >>> print(info["backend_type"])
            >>> print(info["data_location"])
        """
        _cli: TaskWarriorAdapter | None = self._cli_adapter

        info: dict[str, Any] = {
            "backend_type": (
                "taskwarrior-cli" if isinstance(self.adapter, TaskWarriorAdapter)
                else "taskchampion"
            ),
            "backend_version": self.adapter.get_version(),
            "task_cmd": str(_cli.task_cmd) if _cli else None,
            "taskrc_file": str(self.config_store.taskrc_path),
            "data_location": self.adapter.get_data_location(),
            "options": _cli.cli_options if _cli else None,
        }

        # Sync information — detailed keys for TC adapter, basic flag for CLI.
        sync_info: dict[str, Any] = {
            "sync_configured": self.adapter.is_sync_configured(),
        }
        if isinstance(self.adapter, TaskChampionAdapter):
            sync_info.update(self.adapter.get_sync_info())
        info.update(sync_info)

        # Add current context information (name and details) if available.
        current_context: str | None = None
        current_context_details: dict[str, Any] | None = None
        try:
            current_context = self.get_current_context()
            if current_context:
                contexts = self._context_service.get_contexts()
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

        info.update(
            {
                "current_context": current_context,
                "current_context_details": current_context_details,
            }
        )

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
        self._uda_service.load_udas_from_store()

    def get_uda_names(self) -> set[str]:
        """Get all defined UDA names.

        Returns:
            Set of UDA names currently defined in taskrc.

        Example:
            >>> names = tw.get_uda_names()
            >>> print(names)  # {"severity", "estimate", "customer"}
        """
        return self._uda_service.registry.get_uda_names()

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
        return self._uda_service.registry.get_uda(name)

    def get_udas(self) -> list[UdaConfig]:
        """Get full UDA definitions.

        Returns:
            List of UdaConfig objects for all defined UDAs.
        """
        return self._uda_service.registry.get_udas()

    def define_uda(self, uda: UdaConfig) -> None:
        """Define a new UDA via the TaskWarrior facade.

        Delegates to UdaService.define_uda which performs the necessary
        TaskWarrior config writes and registers the UDA in the local registry.

        Args:
            uda: The UdaConfig describing the UDA to create.

        Raises:
            TaskOperationError: If creating the UDA via the underlying adapter fails.
        """
        self._uda_service.define_uda(uda)

    def update_uda(self, uda: UdaConfig) -> None:
        """Update an existing UDA via the TaskWarrior facade.

        Args:
            uda: The UdaConfig with updated fields.

        Raises:
            TaskOperationError: If applying the update fails.
        """
        self._uda_service.define_uda(uda)

    def delete_uda(self, uda: UdaConfig) -> None:
        """Delete a UDA via the TaskWarrior facade.

        Delegates to UdaService.delete_uda which removes TaskWarrior config
        keys and the UDA from the local registry.

        Args:
            uda: The UdaConfig identifying the UDA to remove.

        Raises:
            TaskOperationError: If deletion fails for reasons other than missing keys.
        """
        self._uda_service.delete_uda(uda)

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

    def get_tags(self, include_virtual_tags: bool = False) -> list[str]:
        """Get all tags defined in TaskWarrior.

        Args:
            include_virtual_tags: If ``True``, include TaskWarrior virtual tags
                such as ``TODAY`` and ``READY``.

        Returns:
            List of tag names.
        """
        return self.adapter.get_tags(include_virtual_tags=include_virtual_tags)

    def get_context_tags(self) -> list[str]:
        """Return tags that follow the ``@`` context convention.

        This is a convenience filter for user-defined tags such as ``@work``.
        """
        return [tag for tag in self.get_tags() if tag.startswith("@")]
