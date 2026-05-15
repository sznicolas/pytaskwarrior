"""TaskChampion adapter for pytaskwarrior (Eval 1, taskchampion-py 2.0.2).

Replaces subprocess calls to the ``task`` CLI with direct SQLite access via
the :pypi:`taskchampion-py` PyO3 bindings.

Usage::

    from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

    adapter = TaskChampionAdapter(data_location="~/.local/share/task")
    dto = adapter.add_task(TaskInputDTO(description="Buy milk"))
    print(dto.uuid, dto.index)

Limitations vs :class:`~taskwarrior.adapters.taskwarrior_adapter.TaskWarriorAdapter`
-------------------------------------------------------------------------------------
* :meth:`task_calc` raises :exc:`NotImplementedError` — no TW date parser.
* :meth:`task_date_validator` only validates ISO 8601 strings.
* TW filter expressions (``due.before:tomorrow``, virtual tags, …) are not
  supported; see :mod:`~taskwarrior.adapters.tc_filter` for what is.
* Urgency is always ``None`` (not computed).
* UDA config / context support requires separate configuration.
* Sync requires ``sync_server_url`` (remote) or ``sync_local_server_dir`` (local directory).
"""

from __future__ import annotations

import logging
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from taskchampion import Annotation, Operations, Replica, Status

from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..dto.task_id import TaskID, TaskRef
from ..exceptions import (
    TaskNotFound,
    TaskOperationError,
    TaskSyncError,
    TaskValidationError,
    TaskWarriorError,
)
from .tc_converter import apply_input_dto_to_task, tc_task_to_output_dto
from .tc_filter import apply_filter

logger = logging.getLogger(__name__)

_VERSION = "taskchampion-py/3.0.1"


def _to_taskid(value: TaskRef) -> TaskID:
    return value if isinstance(value, TaskID) else TaskID(value)


class TaskChampionAdapter:
    """taskchampion-py based adapter — no subprocess, direct SQLite access.

    Parameters
    ----------
    data_location:
        Path to the taskchampion data directory (the one that contains
        ``task.sqlite``).  Pass ``None`` to use a temporary in-memory
        database (useful for tests).
    create_if_missing:
        When *data_location* is given, create the directory / DB if absent.
    sync_server_url:
        Remote taskchampion sync server URL (``sync.server.origin`` in taskrc).
        When set, :meth:`synchronize` will use ``sync_to_remote``.
    sync_client_id:
        Client identifier sent to the sync server.  A random UUID is used
        when not supplied (not recommended — prefer persisting in taskrc).
    sync_encryption_secret:
        Encryption secret for the remote sync server.
    sync_local_server_dir:
        Local directory used as a sync server (``sync.local.server_dir`` in
        taskrc).  When set, :meth:`synchronize` will use ``sync_to_local``.
        Takes precedence over *sync_server_url*.
    """

    def __init__(
        self,
        data_location: str | Path | None = None,
        create_if_missing: bool = True,
        sync_server_url: str | None = None,
        sync_client_id: str | None = None,
        sync_encryption_secret: str | None = None,
        sync_local_server_dir: str | None = None,
    ) -> None:
        if data_location is None:
            self._replica = Replica.new_in_memory()
        else:
            self._replica = Replica.new_on_disk(
                str(Path(data_location).expanduser()), create_if_missing
            )

        self._sync_local_server_dir = sync_local_server_dir
        self._sync_server_url = sync_server_url
        self._sync_client_id = sync_client_id or str(_uuid.uuid4())
        self._sync_encryption_secret = sync_encryption_secret or ""
        self._sync_configured = bool(sync_local_server_dir or sync_server_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_ref(self, task_id: TaskRef) -> str:
        """Resolve any :class:`TaskRef` to a UUID string.

        An integer reference is looked up in the current working set.
        A string is first tried as an integer, then validated as a UUID.
        """
        tid = _to_taskid(task_id)
        ref_str = str(tid)

        try:
            idx = int(ref_str)
            ws = self._replica.working_set()
            uuid_str = ws.by_index(idx)
            if uuid_str is None:
                raise TaskNotFound(f"No task at working-set index {idx}")
            return uuid_str
        except ValueError:
            pass

        try:
            return str(UUID(ref_str))
        except ValueError:
            raise TaskNotFound(f"Invalid task reference: {ref_str!r}") from None

    def _get_tc_task(self, uuid_str: str):
        """Return the taskchampion Task for *uuid_str* or raise TaskNotFound."""
        task = self._replica.get_task(uuid_str)
        if task is None:
            raise TaskNotFound(f"Task {uuid_str} not found")
        return task

    def _rebuild_ws(self) -> None:
        """Rebuild the working set after mutations that alter pending counts."""
        self._replica.rebuild_working_set(False)

    def _fetch_dto(self, uuid_str: str) -> TaskOutputDTO:
        """Read a task from the DB and return a :class:`TaskOutputDTO`."""
        task = self._get_tc_task(uuid_str)
        ws = self._replica.working_set()
        return tc_task_to_output_dto(task, ws)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Create a new task and return the persisted DTO."""
        if not task.description or not task.description.strip():
            raise TaskValidationError("Task description cannot be empty")

        new_uuid = str(_uuid.uuid4())
        ops = Operations()
        tc_task = self._replica.create_task(new_uuid, ops)
        tc_task.set_status(Status.Pending, ops)
        apply_input_dto_to_task(tc_task, task, ops)
        self._replica.commit_operations(ops)

        self._rebuild_ws()
        logger.info("Added task %s: %r", new_uuid, task.description)
        return self._fetch_dto(new_uuid)

    def modify_task(self, task: TaskInputDTO, task_id: TaskRef) -> TaskOutputDTO:
        """Modify an existing task and return the updated DTO."""
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)

        ops = Operations()
        apply_input_dto_to_task(tc_task, task, ops)
        self._replica.commit_operations(ops)

        self._rebuild_ws()
        logger.info("Modified task %s", uuid_str)
        return self._fetch_dto(uuid_str)

    def get_task(self, task_id: TaskRef, filter_args: str = "") -> TaskOutputDTO:
        """Retrieve a single task by ID, index, or UUID."""
        uuid_str = self._resolve_ref(task_id)
        return self._fetch_dto(uuid_str)

    def get_tasks(
        self,
        filter: str = "",
        include_completed: bool = False,
        include_deleted: bool = False,
    ) -> list[TaskOutputDTO]:
        """Retrieve tasks matching *filter*.

        Uses ``pending_tasks()`` for the common case (no completed/deleted)
        to avoid scanning the full task history — O(pending) vs O(all).

        The filter is applied in Python; see :mod:`~taskwarrior.adapters.tc_filter`
        for the supported syntax.
        """
        if not include_completed and not include_deleted:
            all_tasks = self._replica.pending_tasks()
        else:
            all_tasks = list(self._replica.all_tasks().values())
        filtered = apply_filter(all_tasks, filter, include_completed, include_deleted)
        ws = self._replica.working_set()
        return [tc_task_to_output_dto(t, ws) for t in filtered]

    def get_recurring_task(self, task_id: TaskRef) -> TaskOutputDTO:
        """Retrieve a recurring task template."""
        uuid_str = self._resolve_ref(task_id)
        return self._fetch_dto(uuid_str)

    def get_recurring_instances(self, task_id: TaskRef) -> list[TaskOutputDTO]:
        """Return all child instances of a recurring task template."""
        uuid_str = self._resolve_ref(task_id)
        all_tasks = list(self._replica.all_tasks().values())
        ws = self._replica.working_set()
        instances = [t for t in all_tasks if t.get_value("parent") == uuid_str]
        return [tc_task_to_output_dto(t, ws) for t in instances]

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def delete_task(self, task_id: TaskRef) -> None:
        """Mark a task as deleted (soft delete)."""
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.set_status(Status.Deleted, ops)
        self._replica.commit_operations(ops)
        self._rebuild_ws()
        logger.info("Deleted task %s", uuid_str)

    def purge_task(self, task_id: TaskRef) -> None:
        """Permanently remove a task from the database."""
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.into_task_data().delete(ops)
        self._replica.commit_operations(ops)
        self._rebuild_ws()
        logger.info("Purged task %s", uuid_str)

    def done_task(self, task_id: TaskRef) -> None:
        """Mark a task as completed."""
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.done(ops)
        self._replica.commit_operations(ops)
        self._rebuild_ws()
        logger.info("Completed task %s", uuid_str)

    def start_task(self, task_id: TaskRef) -> None:
        """Start working on a task (set start timestamp)."""
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.start(ops)
        self._replica.commit_operations(ops)
        logger.info("Started task %s", uuid_str)

    def stop_task(self, task_id: TaskRef) -> None:
        """Stop working on a task (clear start timestamp)."""
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.stop(ops)
        self._replica.commit_operations(ops)
        logger.info("Stopped task %s", uuid_str)

    def annotate_task(self, task_id: TaskRef, annotation: str) -> None:
        """Add an annotation to a task."""
        if not annotation or not annotation.strip():
            raise TaskOperationError("Annotation text cannot be empty")
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)

        # Use a timestamp that doesn't collide with existing annotations
        # (taskchampion uses the entry datetime as a key).
        existing_ts = {int(ann.entry.timestamp()) for ann in tc_task.get_annotations()}
        ts = int(datetime.now(tz=timezone.utc).timestamp())
        while ts in existing_ts:
            ts += 1
        entry = datetime.fromtimestamp(ts, tz=timezone.utc)

        ops = Operations()
        tc_task.add_annotation(Annotation(entry, annotation), ops)
        self._replica.commit_operations(ops)
        logger.info("Annotated task %s", uuid_str)

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def synchronize(self) -> None:
        """Sync with a taskchampion sync server (remote or local).

        Dispatches to ``sync_to_local`` when *sync_local_server_dir* was
        supplied, otherwise to ``sync_to_remote``.

        Raises :exc:`~taskwarrior.exceptions.TaskSyncError` if no sync backend
        is configured or if the sync operation fails.
        """
        if not self._sync_configured:
            raise TaskSyncError(
                "No sync server configured. "
                "Pass sync_local_server_dir or sync_server_url to TaskChampionAdapter()."
            )
        try:
            if self._sync_local_server_dir:
                self._replica.sync_to_local(
                    str(Path(self._sync_local_server_dir).expanduser()),
                    False,  # avoid_snapshots
                )
            else:
                self._replica.sync_to_remote(
                    self._sync_server_url,
                    self._sync_client_id,
                    self._sync_encryption_secret,
                    False,  # avoid_snapshots
                )
            logger.info("Sync completed")
        except Exception as exc:
            raise TaskSyncError(f"Sync failed: {exc}") from exc

    def is_sync_configured(self) -> bool:
        """Return ``True`` if a sync server URL was provided."""
        return self._sync_configured

    # ------------------------------------------------------------------
    # Utility / metadata
    # ------------------------------------------------------------------

    def task_calc(self, date_str: str) -> str:
        """Resolve a TaskWarrior date expression and return an ISO 8601 string.

        Supports all expressions handled by
        :func:`~taskwarrior.utils.date_resolver.resolve_date`: named dates
        (``"today"``, ``"tomorrow"``, ``"eom"``), ISO 8601, compact relative
        (``"now+2w"``), ISO durations (``"P2W"``), weekday names, and
        compound expressions with spaces (``"today + P3D"``, ``"now + 1d"``).

        Raises:
            TaskWarriorError: If the expression cannot be resolved.
        """
        from ..utils.date_resolver import resolve_date

        result = resolve_date(date_str)
        if result is None:
            raise TaskWarriorError(
                f"Cannot resolve date expression {date_str!r}. "
                "Supported: ISO 8601, today/tomorrow/yesterday, eod/eow/eom/eoy, "
                "now+Nd/Nw/Nh/Nm, P2W/P3D, weekday names. "
                "For complex expressions, use a TaskWarriorAdapter."
            )
        return result.isoformat()

    def task_date_validator(self, date_str: str) -> bool:
        """Return ``True`` if *date_str* can be resolved to a datetime.

        Accepts ISO 8601 strings and the TaskWarrior date synonyms supported
        by :func:`~taskwarrior.utils.date_resolver.resolve_date`.
        """
        from ..utils.date_resolver import resolve_date

        return resolve_date(date_str) is not None

    def get_version(self) -> str:
        """Return the adapter version string."""
        return _VERSION

    def get_projects(self) -> list[str]:
        """Return a sorted list of all project names across all tasks."""
        projects: set[str] = set()
        for task in self._replica.all_tasks().values():
            proj = task.get_value("project")
            if proj:
                projects.add(proj)
        return sorted(projects)

    def get_tags(self, include_virtual_tags: bool = False) -> list[str]:
        """Return a sorted list of all tags across all tasks.

        Parameters
        ----------
        include_virtual_tags:
            When ``True``, TaskWarrior virtual tags (``TODAY``, ``READY``,
            ``OVERDUE``, …) are appended in addition to user-defined tags.
        """
        tags: set[str] = set()
        for task in self._replica.all_tasks().values():
            for t in task.get_tags():
                if t.is_user():
                    tags.add(str(t))
        if include_virtual_tags:
            from ..utils.virtual_tags import TASKWARRIOR_VIRTUAL_TAGS
            tags.update(TASKWARRIOR_VIRTUAL_TAGS)
        return sorted(tags)
