"""TaskChampion adapter for pytaskwarrior (Eval 1, taskchampion-py 2.0.2).

Replaces subprocess calls to the ``task`` CLI with direct SQLite access via
the :pypi:`taskchampion-py` PyO3 bindings.

Usage::

    from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

    adapter = TaskChampionAdapter(data_location="~/.local/share/task")
    dto = adapter.add_task(TaskInputDTO(description="Buy milk"))
    print(dto.uuid, dto.index)

Live configuration updates
--------------------------
Pass a :class:`~taskwarrior.config.config_store.ConfigStore` instance to keep
sync parameters in sync with the taskrc file at all times::

    adapter = TaskChampionAdapter(config_store=my_config_store)
    # Later — no adapter recreation required:
    my_config_store.set_value("sync.server.origin", "https://sync.example.com")
    adapter.synchronize()  # picks up the new URL automatically

Limitations vs :class:`~taskwarrior.adapters.taskwarrior_adapter.TaskWarriorAdapter`
-------------------------------------------------------------------------------------
* :meth:`task_calc` raises :exc:`NotImplementedError` — no TW date parser.
* :meth:`task_date_validator` only validates ISO 8601 strings.
* TW filter expressions (``due.before:tomorrow``, virtual tags, …) are not
  supported; see :mod:`~taskwarrior.adapters.tc_filter` for what is.
* Urgency is always ``None`` (not computed).
* UDA config / context support requires separate configuration.
* Changing ``data_location`` at runtime requires creating a new adapter instance.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid as _uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

from taskchampion import AccessMode, Annotation, Operations, Replica, Status

from ..config.config_store import ConfigStore
from ..dto.task_dto import TaskInputDTO, TaskOutputDTO
from ..dto.task_id import TaskRef, to_taskid
from ..exceptions import (
    TaskNotFound,
    TaskOperationError,
    TaskSyncError,
    TaskValidationError,
    TaskWarriorError,
)
from ..utils.date_resolver import resolve_date
from .tc_converter import apply_input_dto_to_task, tc_task_to_output_dto
from .tc_filter import apply_filter

logger = logging.getLogger(__name__)

_VERSION = "taskchampion-py/3.0.1"
_AVOID_SNAPSHOTS: bool = False
_LOCK_TIMEOUT: float = 30.0
_T = TypeVar("_T")


@dataclass
class AdapterMetrics:
    """Thread-safe metrics for :class:`TaskChampionAdapter` operations.

    Attributes track cumulative counts and timings across all calls made
    through :meth:`TaskChampionAdapter._locked_call`.  All fields are
    updated atomically behind an internal lock.
    """

    calls_total: int = 0
    errors_total: int = 0
    wait_seconds_total: float = 0.0
    run_seconds_total: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def record(self, wait: float, run: float, *, error: bool = False) -> None:
        """Record timing and error status for one completed call."""
        with self._lock:
            self.calls_total += 1
            self.wait_seconds_total += wait
            self.run_seconds_total += run
            if error:
                self.errors_total += 1

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time copy of the metrics."""
        with self._lock:
            avg_wait = (
                round(self.wait_seconds_total / self.calls_total, 3)
                if self.calls_total
                else 0.0
            )
            return {
                "calls_total": self.calls_total,
                "errors_total": self.errors_total,
                "avg_wait_seconds": avg_wait,
            }


class TaskChampionAdapter:
    """taskchampion-py based adapter — no subprocess, direct SQLite access.

    Parameters
    ----------
    data_location:
        Path to the taskchampion data directory (the one that contains
        ``task.sqlite``).  Pass ``None`` to use a temporary in-memory
        database (useful for tests).  When *config_store* is supplied and
        *data_location* is omitted, ``config_store.data_location`` is used.
    create_if_missing:
        When *data_location* is given, create the directory / DB if absent.
    access_mode:
        ``AccessMode.ReadWrite`` (default) for full CRUD access.
        ``AccessMode.ReadOnly`` for read-only access, which is safe to use
        from multiple concurrent threads or processes (SQLite WAL allows
        many concurrent readers alongside a single writer).
    config_store:
        When provided, sync parameters (server URL, client ID, encryption
        secret, local server dir) are **read lazily** from the store on every
        :meth:`synchronize` call.  This means that a
        ``config_store.set_value(…)`` call is immediately reflected the next
        time sync is invoked — no adapter recreation required.  This is the
        recommended mode when the adapter is created via
        :class:`~taskwarrior.main.TaskWarrior`.
    sync_server_url:
        Remote taskchampion sync server URL (``sync.server.origin`` in taskrc).
        Used only when *config_store* is ``None``.
    sync_client_id:
        Client identifier sent to the sync server.  A random UUID is used
        when not supplied (not recommended — prefer persisting in taskrc).
        Used only when *config_store* is ``None``.
    sync_encryption_secret:
        Encryption secret for the remote sync server.
        Used only when *config_store* is ``None``.
    sync_local_server_dir:
        Local directory used as a sync server (``sync.local.server_dir`` in
        taskrc).  When set, :meth:`synchronize` will use ``sync_to_local``.
        Takes precedence over *sync_server_url*.
        Used only when *config_store* is ``None``.

    Note
    ----
    Changing ``data_location`` at runtime requires creating a new
    :class:`TaskChampionAdapter` instance because the underlying
    :class:`taskchampion.Replica` (SQLite connection) is opened once at
    construction time.

    Thread safety
    -------------
    Each :class:`TaskChampionAdapter` instance is **bound to the thread that
    created it**.  The underlying :class:`taskchampion.Replica` is
    ``unsendable`` (a PyO3 constraint): calling any method from a different
    thread raises a Rust-level :exc:`pyo3_runtime.PanicException`.

    To surface this early as a clear Python error, every method that accesses
    the :class:`~taskchampion.Replica` calls :meth:`_check_thread_affinity`
    on entry and raises :exc:`RuntimeError` immediately if the call originates
    from a foreign thread.  A :class:`threading.Lock` is also held during each
    operation for internal consistency (e.g. coroutines sharing the adapter on
    the same asyncio event loop).

    Concurrency patterns:

    * **FastAPI / asyncio** — use ``async def`` endpoints with a single
      shared adapter instance; the event loop runs on one thread so the
      constraint is automatically satisfied.
    * **FastAPI sync endpoints** (thread-pool execution) — create one
      :class:`TaskChampionAdapter` per request (or per thread) so each
      worker thread owns its own :class:`~taskchampion.Replica`.
    * **Read-only concurrent access** — pass ``access_mode=AccessMode.ReadOnly``
      and create one instance per thread; SQLite WAL allows many concurrent
      readers without blocking.
    * **In-memory mode** (``data_location=None``) — each instance is fully
      isolated; do not share between threads.

    Metrics
    -------
    Call :meth:`get_metrics` to retrieve a snapshot of operation counts,
    error counts, and average wait/run times recorded by the internal
    :class:`AdapterMetrics` instance.
    """

    def __init__(
        self,
        data_location: str | Path | None = None,
        create_if_missing: bool = True,
        access_mode: AccessMode = AccessMode.ReadWrite,
        config_store: ConfigStore | None = None,
        sync_server_url: str | None = None,
        sync_client_id: str | None = None,
        sync_encryption_secret: str | None = None,
        sync_local_server_dir: str | None = None,
    ) -> None:
        self._owner_thread_id = threading.current_thread().ident
        self._db_lock = threading.Lock()
        self._metrics = AdapterMetrics()

        # When a ConfigStore is provided it becomes the live source of truth for
        # sync parameters; they are re-read on every sync() call so that
        # config_store.set_value() changes take effect without recreating the adapter.
        self._config_store: ConfigStore | None = config_store

        effective_data_location = (
            config_store.data_location if (config_store is not None and data_location is None) else data_location
        )

        if effective_data_location is None:
            self._replica = Replica.new_in_memory()
            self._data_location: str | None = None
        else:
            resolved = str(Path(effective_data_location).expanduser())
            self._replica = Replica.new_on_disk(resolved, create_if_missing, access_mode)
            self._data_location = resolved

        # Legacy / direct-construction params (used when config_store is None).
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
        tid = to_taskid(task_id)
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

    def _check_thread_affinity(self) -> None:
        """Raise :exc:`RuntimeError` if called from a thread other than the owner.

        The underlying :class:`taskchampion.Replica` is PyO3 *unsendable*:
        calling it from a foreign thread would trigger a Rust-level panic.
        This method turns that panic into an explicit Python error.
        """
        if threading.current_thread().ident != self._owner_thread_id:
            raise RuntimeError(
                f"TaskChampionAdapter instance was created on thread "
                f"{self._owner_thread_id} but is being accessed from thread "
                f"{threading.current_thread().ident}. "
                "The underlying taskchampion.Replica is thread-bound "
                "(PyO3 unsendable constraint). "
                "Create a separate TaskChampionAdapter instance per thread, "
                "or adopt a per-request adapter pattern."
            )

    def _locked_call(self, fn: Callable[..., _T], /, *args: Any, **kwargs: Any) -> _T:
        """Run *fn* under the instance lock, recording metrics.

        Raises
        ------
        RuntimeError
            If called from a thread other than the owner thread.
        TaskOperationError
            If the lock cannot be acquired within :data:`_LOCK_TIMEOUT` seconds.
        """
        self._check_thread_affinity()
        t_wait_start = time.monotonic()
        acquired = self._db_lock.acquire(timeout=_LOCK_TIMEOUT)
        wait = time.monotonic() - t_wait_start
        if not acquired:
            self._metrics.record(wait=_LOCK_TIMEOUT, run=0.0, error=True)
            raise TaskOperationError(
                f"Lock timeout after {_LOCK_TIMEOUT}s waiting for {fn.__name__}"
            )
        error = False
        t_run_start = time.monotonic()
        try:
            return fn(*args, **kwargs)
        except Exception:
            error = True
            raise
        finally:
            run = time.monotonic() - t_run_start
            self._metrics.record(wait=wait, run=run, error=error)
            self._db_lock.release()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_task(self, task: TaskInputDTO) -> TaskOutputDTO:
        """Create a new task and return the persisted DTO."""
        return self._locked_call(self._add_task_internal, task)

    def _add_task_internal(self, task: TaskInputDTO) -> TaskOutputDTO:
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
        return self._locked_call(self._modify_task_internal, task, task_id)

    def _modify_task_internal(self, task: TaskInputDTO, task_id: TaskRef) -> TaskOutputDTO:
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)

        ops = Operations()
        apply_input_dto_to_task(tc_task, task, ops)
        self._replica.commit_operations(ops)

        self._rebuild_ws()
        logger.info("Modified task %s", uuid_str)
        return self._fetch_dto(uuid_str)

    def get_task(self, task_id: TaskRef) -> TaskOutputDTO:
        """Retrieve a single task by ID, index, or UUID."""
        return self._locked_call(self._get_task_internal, task_id)

    def _get_task_internal(self, task_id: TaskRef) -> TaskOutputDTO:
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
        return self._locked_call(
            self._get_tasks_internal, filter, include_completed, include_deleted
        )

    def _get_tasks_internal(
        self,
        filter: str = "",
        include_completed: bool = False,
        include_deleted: bool = False,
    ) -> list[TaskOutputDTO]:
        if not include_completed and not include_deleted:
            all_tasks = self._replica.pending_tasks()
        else:
            all_tasks = list(self._replica.all_tasks().values())
        filtered = apply_filter(all_tasks, filter, include_completed, include_deleted)
        ws = self._replica.working_set()
        return [tc_task_to_output_dto(t, ws) for t in filtered]

    def get_recurring_task(self, task_id: TaskRef) -> TaskOutputDTO:
        """Retrieve a recurring task template."""
        return self._locked_call(self._get_recurring_task_internal, task_id)

    def _get_recurring_task_internal(self, task_id: TaskRef) -> TaskOutputDTO:
        uuid_str = self._resolve_ref(task_id)
        return self._fetch_dto(uuid_str)

    def get_recurring_instances(self, task_id: TaskRef) -> list[TaskOutputDTO]:
        """Return all child instances of a recurring task template."""
        return self._locked_call(self._get_recurring_instances_internal, task_id)

    def _get_recurring_instances_internal(self, task_id: TaskRef) -> list[TaskOutputDTO]:
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
        self._locked_call(self._delete_task_internal, task_id)

    def _delete_task_internal(self, task_id: TaskRef) -> None:
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.set_status(Status.Deleted, ops)
        self._replica.commit_operations(ops)
        self._rebuild_ws()
        logger.info("Deleted task %s", uuid_str)

    def purge_task(self, task_id: TaskRef) -> None:
        """Permanently remove a task from the database."""
        self._locked_call(self._purge_task_internal, task_id)

    def _purge_task_internal(self, task_id: TaskRef) -> None:
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.into_task_data().delete(ops)
        self._replica.commit_operations(ops)
        self._rebuild_ws()
        logger.info("Purged task %s", uuid_str)

    def done_task(self, task_id: TaskRef) -> None:
        """Mark a task as completed."""
        self._locked_call(self._done_task_internal, task_id)

    def _done_task_internal(self, task_id: TaskRef) -> None:
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.done(ops)
        self._replica.commit_operations(ops)
        self._rebuild_ws()
        logger.info("Completed task %s", uuid_str)

    def start_task(self, task_id: TaskRef) -> None:
        """Start working on a task (set start timestamp)."""
        self._locked_call(self._start_task_internal, task_id)

    def _start_task_internal(self, task_id: TaskRef) -> None:
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.start(ops)
        self._replica.commit_operations(ops)
        logger.info("Started task %s", uuid_str)

    def stop_task(self, task_id: TaskRef) -> None:
        """Stop working on a task (clear start timestamp)."""
        self._locked_call(self._stop_task_internal, task_id)

    def _stop_task_internal(self, task_id: TaskRef) -> None:
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)
        ops = Operations()
        tc_task.stop(ops)
        self._replica.commit_operations(ops)
        logger.info("Stopped task %s", uuid_str)

    def annotate_task(self, task_id: TaskRef, annotation: str) -> None:
        """Add an annotation to a task."""
        self._locked_call(self._annotate_task_internal, task_id, annotation)

    def _annotate_task_internal(self, task_id: TaskRef, annotation: str) -> None:
        if not annotation or not annotation.strip():
            raise TaskOperationError("Annotation text cannot be empty")
        uuid_str = self._resolve_ref(task_id)
        tc_task = self._get_tc_task(uuid_str)

        # Use a timestamp that doesn't collide with existing annotations
        # (taskchampion uses the entry datetime as a key).
        existing_ts = {int(ann.entry.timestamp()) for ann in tc_task.get_annotations()}
        ts = int(datetime.now(tz=UTC).timestamp())
        while ts in existing_ts:
            ts += 1
        entry = datetime.fromtimestamp(ts, tz=UTC)

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
        self._locked_call(self._synchronize_internal)

    def _synchronize_internal(self) -> None:
        if self._config_store is not None:
            cfg = self._config_store.get_sync_config()
            sync_local = cfg.get("sync.local.server_dir")
            sync_url = cfg.get("sync.server.origin")
            sync_client_id = cfg.get("sync.server.client_id") or self._sync_client_id
            sync_secret = cfg.get("sync.encryption.secret") or ""
            is_configured = bool(sync_local or sync_url)
        else:
            sync_local = self._sync_local_server_dir
            sync_url = self._sync_server_url
            sync_client_id = self._sync_client_id
            sync_secret = self._sync_encryption_secret
            is_configured = self._sync_configured

        if not is_configured:
            raise TaskSyncError(
                "No sync server configured. "
                "Pass sync_local_server_dir or sync_server_url to TaskChampionAdapter()."
            )
        try:
            if sync_local:
                self._replica.sync_to_local(
                    str(Path(sync_local).expanduser()),
                    _AVOID_SNAPSHOTS,
                )
            else:
                self._replica.sync_to_remote(
                    sync_url,
                    sync_client_id,
                    sync_secret,
                    _AVOID_SNAPSHOTS,
                )
            logger.info("Sync completed")
        except Exception as exc:
            raise TaskSyncError(f"Sync failed: {exc}") from exc

    def is_sync_configured(self) -> bool:
        """Return ``True`` if a sync server URL was provided."""
        if self._config_store is not None:
            cfg = self._config_store.get_sync_config()
            return bool(cfg.get("sync.server.origin") or cfg.get("sync.local.server_dir"))
        return self._sync_configured

    def has_local_changes(self) -> bool:
        """Return ``True`` if there are local operations not yet pushed to the sync server.

        Uses :pymeth:`taskchampion.Replica.num_local_operations` to count
        pending operations.  A return value of ``True`` means a call to
        :meth:`synchronize` would push changes; ``False`` means the local
        replica is in sync with the last known server state.

        .. note::
            This method only reflects the *local* side.  There is no way to
            check whether the remote server has new operations without actually
            performing a sync.  Call :meth:`synchronize` to pull remote
            changes.
        """
        return self._locked_call(self._has_local_changes_internal)

    def _has_local_changes_internal(self) -> bool:
        return self._replica.num_local_operations() > 0

    def pending_local_ops_count(self) -> int:
        """Return the number of local operations not yet pushed to the sync server.

        Useful for logging or debugging.  ``0`` means fully synced (local side).
        See :meth:`has_local_changes` for the boolean shorthand.
        """
        return self._locked_call(self._pending_local_ops_count_internal)

    def _pending_local_ops_count_internal(self) -> int:
        return self._replica.num_local_operations()

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
        return resolve_date(date_str) is not None

    def get_version(self) -> str:
        """Return the adapter version string."""
        return _VERSION

    def get_data_location(self) -> str | None:
        """Return the resolved data directory path, or ``None`` for in-memory."""
        return self._data_location

    def get_sync_info(self) -> dict[str, str | None]:
        """Return sync configuration details."""
        if self._config_store is not None:
            cfg = self._config_store.get_sync_config()
            sync_url = cfg.get("sync.server.origin")
            sync_local = cfg.get("sync.local.server_dir")
            sync_client_id = cfg.get("sync.server.client_id")
        else:
            sync_url = self._sync_server_url
            sync_local = self._sync_local_server_dir
            sync_client_id = self._sync_client_id if self._sync_server_url else None

        if sync_local:
            sync_backend: str | None = "local"
        elif sync_url:
            sync_backend = "remote"
        else:
            sync_backend = None
        return {
            "sync_backend": sync_backend,
            "sync_server_url": sync_url,
            "sync_local_server_dir": sync_local,
            "sync_client_id": sync_client_id,
        }

    def get_projects(self) -> list[str]:
        """Return a sorted list of all project names across all tasks."""
        return self._locked_call(self._get_projects_internal)

    def _get_projects_internal(self) -> list[str]:
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
        return self._locked_call(self._get_tags_internal, include_virtual_tags)

    def _get_tags_internal(self, include_virtual_tags: bool = False) -> list[str]:
        tags: set[str] = set()
        for task in self._replica.all_tasks().values():
            for t in task.get_tags():
                if t.is_user():
                    tags.add(str(t))
        if include_virtual_tags:
            from ..utils.virtual_tags import TASKWARRIOR_VIRTUAL_TAGS

            tags.update(TASKWARRIOR_VIRTUAL_TAGS)
        return sorted(tags)

    def get_metrics(self) -> dict[str, Any]:
        """Return a snapshot of adapter operation metrics.

        Returns a dict with ``calls_total``, ``errors_total``, and
        ``avg_wait_seconds`` — useful for monitoring lock contention.
        """
        return self._metrics.snapshot()
