"""Tests for TaskChampionAdapter (Eval 1 — taskchampion-py 2.0.2).

All tests use ``Replica.new_in_memory()`` via ``TaskChampionAdapter(data_location=None)``,
so no filesystem I/O is required and tests are fully isolated.
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

import pytest

from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
from taskwarrior.dto.task_dto import TaskInputDTO, TaskOutputDTO
from taskwarrior.enums import Priority, RecurrencePeriod, TaskStatus
from taskwarrior.exceptions import (
    TaskNotFound,
    TaskOperationError,
    TaskSyncError,
    TaskValidationError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter() -> TaskChampionAdapter:
    """Fresh in-memory adapter for each test."""
    return TaskChampionAdapter()


@pytest.fixture
def simple_task(adapter: TaskChampionAdapter) -> TaskOutputDTO:
    """One pending task created in the adapter."""
    return adapter.add_task(TaskInputDTO(description="Buy milk"))


# ---------------------------------------------------------------------------
# add_task
# ---------------------------------------------------------------------------


class TestAddTask:
    def test_returns_dto_with_uuid(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="test task"))
        assert dto.uuid is not None
        assert isinstance(dto.uuid, uuid.UUID)

    def test_description_stored(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="Buy milk"))
        assert dto.description == "Buy milk"

    def test_status_is_pending(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="test"))
        assert dto.status == TaskStatus.PENDING

    def test_working_set_index_assigned(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="test"))
        assert dto.index >= 1

    def test_empty_description_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises(TaskValidationError):
            adapter.add_task(TaskInputDTO(description="   "))

    def test_none_description_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises((TaskValidationError, Exception)):
            adapter.add_task(TaskInputDTO(description=None))

    def test_priority(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(
            TaskInputDTO(description="urgent", priority=Priority.HIGH)
        )
        assert dto.priority == Priority.HIGH

    def test_project(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="task", project="work"))
        assert dto.project == "work"

    def test_tags(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="tag test", tags=["foo", "bar"]))
        assert set(dto.tags) == {"foo", "bar"}

    def test_due_iso(self, adapter: TaskChampionAdapter) -> None:
        due = "2030-01-01T00:00:00+00:00"
        dto = adapter.add_task(TaskInputDTO(description="due task", due=due))
        assert dto.due is not None
        assert dto.due.year == 2030

    def test_scheduled_iso(self, adapter: TaskChampionAdapter) -> None:
        sched = "2030-06-01T12:00:00+00:00"
        dto = adapter.add_task(TaskInputDTO(description="sched", scheduled=sched))
        assert dto.scheduled is not None
        assert dto.scheduled.year == 2030

    def test_wait_iso(self, adapter: TaskChampionAdapter) -> None:
        wait_str = "2038-01-19T03:14:07+00:00"
        dto = adapter.add_task(TaskInputDTO(description="waiting", wait=wait_str))
        assert dto.status == TaskStatus.WAITING
        assert dto.wait is not None

    def test_annotations_added(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(
            TaskInputDTO(description="annotated", annotations=["note one", "note two"])
        )
        assert len(dto.annotations) == 2
        descs = {a.description for a in dto.annotations}
        assert descs == {"note one", "note two"}

    def test_udas(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(
            TaskInputDTO(description="uda task", udas={"severity": "high"})
        )
        assert dto.udas.get("severity") == "high"

    def test_depends(self, adapter: TaskChampionAdapter) -> None:
        dep = adapter.add_task(TaskInputDTO(description="dependency"))
        dto = adapter.add_task(
            TaskInputDTO(description="blocked", depends=[dep.uuid])
        )
        assert dep.uuid in dto.depends


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------


class TestGetTask:
    def test_by_uuid(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        fetched = adapter.get_task(simple_task.uuid)
        assert fetched.uuid == simple_task.uuid
        assert fetched.description == simple_task.description

    def test_by_index(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        fetched = adapter.get_task(simple_task.index)
        assert fetched.uuid == simple_task.uuid

    def test_by_uuid_string(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        fetched = adapter.get_task(str(simple_task.uuid))
        assert fetched.uuid == simple_task.uuid

    def test_not_found_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises(TaskNotFound):
            adapter.get_task(str(uuid.uuid4()))

    def test_invalid_ref_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises(TaskNotFound):
            adapter.get_task("not-a-uuid")

    def test_bad_index_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises(TaskNotFound):
            adapter.get_task(999)


# ---------------------------------------------------------------------------
# modify_task
# ---------------------------------------------------------------------------


class TestModifyTask:
    def test_update_description(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        updated = adapter.modify_task(
            TaskInputDTO(description="Updated desc"), simple_task.uuid
        )
        assert updated.description == "Updated desc"

    def test_set_priority(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        updated = adapter.modify_task(
            TaskInputDTO(priority=Priority.MEDIUM), simple_task.uuid
        )
        assert updated.priority == Priority.MEDIUM

    def test_add_tag(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        updated = adapter.modify_task(
            TaskInputDTO(tags=["urgent"]), simple_task.uuid
        )
        assert "urgent" in updated.tags

    def test_remove_tag(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(TaskInputDTO(description="tagged", tags=["keep", "drop"]))
        updated = adapter.modify_task(TaskInputDTO(tags=["keep"]), dto.uuid)
        assert "keep" in updated.tags
        assert "drop" not in updated.tags

    def test_set_project(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        updated = adapter.modify_task(
            TaskInputDTO(project="home"), simple_task.uuid
        )
        assert updated.project == "home"

    def test_update_uda(self, adapter: TaskChampionAdapter) -> None:
        dto = adapter.add_task(
            TaskInputDTO(description="uda", udas={"severity": "low"})
        )
        updated = adapter.modify_task(
            TaskInputDTO(udas={"severity": "high"}), dto.uuid
        )
        assert updated.udas.get("severity") == "high"


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    def test_done_task(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.done_task(simple_task.uuid)
        fetched = adapter.get_task(simple_task.uuid)
        assert fetched.status == TaskStatus.COMPLETED

    def test_delete_task(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.delete_task(simple_task.uuid)
        fetched = adapter.get_task(simple_task.uuid)
        assert fetched.status == TaskStatus.DELETED

    def test_purge_task(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.purge_task(simple_task.uuid)
        with pytest.raises(TaskNotFound):
            adapter.get_task(simple_task.uuid)

    def test_start_stop(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.start_task(simple_task.uuid)
        started = adapter.get_task(simple_task.uuid)
        assert started.start is not None

        adapter.stop_task(simple_task.uuid)
        stopped = adapter.get_task(simple_task.uuid)
        assert stopped.start is None

    def test_start_by_index(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.start_task(simple_task.index)
        started = adapter.get_task(simple_task.uuid)
        assert started.start is not None

    def test_done_not_found_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises(TaskNotFound):
            adapter.done_task(str(uuid.uuid4()))

    def test_delete_not_found_raises(self, adapter: TaskChampionAdapter) -> None:
        with pytest.raises(TaskNotFound):
            adapter.delete_task(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# annotate_task
# ---------------------------------------------------------------------------


class TestAnnotateTask:
    def test_annotation_added(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.annotate_task(simple_task.uuid, "important note")
        fetched = adapter.get_task(simple_task.uuid)
        assert any(a.description == "important note" for a in fetched.annotations)

    def test_multiple_annotations(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        adapter.annotate_task(simple_task.uuid, "first")
        adapter.annotate_task(simple_task.uuid, "second")
        fetched = adapter.get_task(simple_task.uuid)
        descs = {a.description for a in fetched.annotations}
        assert "first" in descs
        assert "second" in descs

    def test_empty_annotation_raises(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        with pytest.raises(TaskOperationError):
            adapter.annotate_task(simple_task.uuid, "")


# ---------------------------------------------------------------------------
# get_tasks
# ---------------------------------------------------------------------------


class TestGetTasks:
    def test_returns_pending_by_default(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="p1"))
        adapter.add_task(TaskInputDTO(description="p2"))
        tasks = adapter.get_tasks()
        assert len(tasks) == 2
        assert all(t.status == TaskStatus.PENDING for t in tasks)

    def test_excludes_deleted_by_default(self, adapter: TaskChampionAdapter) -> None:
        t = adapter.add_task(TaskInputDTO(description="to delete"))
        adapter.delete_task(t.uuid)
        tasks = adapter.get_tasks()
        uuids = [x.uuid for x in tasks]
        assert t.uuid not in uuids

    def test_includes_deleted_when_requested(
        self, adapter: TaskChampionAdapter
    ) -> None:
        t = adapter.add_task(TaskInputDTO(description="to delete"))
        adapter.delete_task(t.uuid)
        tasks = adapter.get_tasks(include_deleted=True)
        uuids = [x.uuid for x in tasks]
        assert t.uuid in uuids

    def test_includes_completed_when_requested(
        self, adapter: TaskChampionAdapter
    ) -> None:
        t = adapter.add_task(TaskInputDTO(description="to complete"))
        adapter.done_task(t.uuid)
        tasks = adapter.get_tasks(include_completed=True)
        uuids = [x.uuid for x in tasks]
        assert t.uuid in uuids

    def test_filter_by_tag(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="tagged", tags=["work"]))
        adapter.add_task(TaskInputDTO(description="untagged"))
        tasks = adapter.get_tasks(filter="+work")
        assert len(tasks) == 1
        assert "work" in tasks[0].tags

    def test_filter_exclude_tag(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="tagged", tags=["personal"]))
        adapter.add_task(TaskInputDTO(description="untagged"))
        tasks = adapter.get_tasks(filter="-personal")
        assert all("personal" not in t.tags for t in tasks)

    def test_filter_by_project(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="work task", project="work"))
        adapter.add_task(TaskInputDTO(description="home task", project="home"))
        tasks = adapter.get_tasks(filter="project:work")
        assert all(t.project == "work" for t in tasks)

    def test_filter_by_project_prefix(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(
            TaskInputDTO(description="sub task", project="work.reports")
        )
        adapter.add_task(TaskInputDTO(description="home task", project="home"))
        tasks = adapter.get_tasks(filter="project:work")
        assert len(tasks) == 1
        assert tasks[0].project == "work.reports"

    def test_filter_status(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="p"))
        tasks = adapter.get_tasks(
            filter="status:pending", include_completed=True, include_deleted=True
        )
        assert all(t.status == TaskStatus.PENDING for t in tasks)

    def test_filter_latest(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="first"))
        adapter.add_task(TaskInputDTO(description="second"))
        tasks = adapter.get_tasks(filter="+LATEST")
        assert len(tasks) == 1

    def test_filter_by_uuid(self, adapter: TaskChampionAdapter) -> None:
        t1 = adapter.add_task(TaskInputDTO(description="t1"))
        adapter.add_task(TaskInputDTO(description="t2"))
        tasks = adapter.get_tasks(
            filter=f"uuid:{t1.uuid}", include_completed=True, include_deleted=True
        )
        assert len(tasks) == 1
        assert tasks[0].uuid == t1.uuid


# ---------------------------------------------------------------------------
# get_projects / get_tags
# ---------------------------------------------------------------------------


class TestProjectsAndTags:
    def test_get_projects(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="a", project="alpha"))
        adapter.add_task(TaskInputDTO(description="b", project="beta"))
        adapter.add_task(TaskInputDTO(description="c"))
        projects = adapter.get_projects()
        assert "alpha" in projects
        assert "beta" in projects

    def test_get_tags(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="t", tags=["foo", "bar"]))
        tags = adapter.get_tags()
        assert "foo" in tags
        assert "bar" in tags

    def test_get_tags_excludes_virtual_by_default(
        self, adapter: TaskChampionAdapter
    ) -> None:
        adapter.add_task(TaskInputDTO(description="t", tags=["user_tag"]))
        tags = adapter.get_tags()
        assert "PENDING" not in tags

    def test_get_tags_includes_virtual_when_requested(
        self, adapter: TaskChampionAdapter
    ) -> None:
        adapter.add_task(TaskInputDTO(description="t"))
        tags = adapter.get_tags(include_virtual_tags=True)
        # Synthetic PENDING tag should appear for pending tasks
        assert "PENDING" in tags


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------


class TestRecurring:
    def test_get_recurring_instances(self, adapter: TaskChampionAdapter) -> None:
        parent = adapter.add_task(
            TaskInputDTO(
                description="recurring template",
                recur=RecurrencePeriod.DAILY,
            )
        )
        # Manually create a child instance with parent UUID
        child = adapter.add_task(
            TaskInputDTO(
                description="child instance",
                parent=parent.uuid,
            )
        )
        instances = adapter.get_recurring_instances(parent.uuid)
        assert any(i.uuid == child.uuid for i in instances)

    def test_get_recurring_task(
        self, adapter: TaskChampionAdapter, simple_task: TaskOutputDTO
    ) -> None:
        # get_recurring_task on a normal task simply returns it
        fetched = adapter.get_recurring_task(simple_task.uuid)
        assert fetched.uuid == simple_task.uuid


# ---------------------------------------------------------------------------
# Utility methods
# ---------------------------------------------------------------------------


class TestUtilityMethods:
    def test_get_version(self, adapter: TaskChampionAdapter) -> None:
        version = adapter.get_version()
        assert "taskchampion" in version.lower()

    def test_task_calc_resolves_known_expression(self, adapter: TaskChampionAdapter) -> None:
        result = adapter.task_calc("tomorrow")
        assert "T" in result  # ISO 8601 datetime string

    def test_task_calc_raises_unknown_expression(self, adapter: TaskChampionAdapter) -> None:
        from taskwarrior.exceptions import TaskWarriorError

        with pytest.raises(TaskWarriorError):
            adapter.task_calc("not-a-date-at-all")

    def test_task_date_validator_valid(self, adapter: TaskChampionAdapter) -> None:
        assert adapter.task_date_validator("2030-01-01T00:00:00+00:00") is True
        assert adapter.task_date_validator("2030-01-01T00:00:00Z") is True
        assert adapter.task_date_validator("tomorrow") is True
        assert adapter.task_date_validator("eom") is True

    def test_task_date_validator_invalid(self, adapter: TaskChampionAdapter) -> None:
        assert adapter.task_date_validator("not-a-date") is False
        assert adapter.task_date_validator("today + 2weeks") is False

    def test_is_sync_configured_false(self, adapter: TaskChampionAdapter) -> None:
        assert adapter.is_sync_configured() is False

    def test_is_sync_configured_true_remote(self) -> None:
        a = TaskChampionAdapter(sync_server_url="https://sync.example.com")
        assert a.is_sync_configured() is True

    def test_is_sync_configured_true_local(self) -> None:
        a = TaskChampionAdapter(sync_local_server_dir="/tmp/server")
        assert a.is_sync_configured() is True

    def test_synchronize_raises_without_config(
        self, adapter: TaskChampionAdapter
    ) -> None:
        with pytest.raises(TaskSyncError):
            adapter.synchronize()

    def test_synchronize_remote_calls_sync_to_remote(self) -> None:
        """synchronize() with a remote URL must call replica.sync_to_remote."""
        from unittest.mock import MagicMock

        a = TaskChampionAdapter(
            sync_server_url="https://sync.example.com",
            sync_client_id="11111111-2222-3333-4444-555555555555",
            sync_encryption_secret="secret",
        )
        a._replica = MagicMock()
        a.synchronize()
        a._replica.sync_to_remote.assert_called_once_with(
            "https://sync.example.com",
            "11111111-2222-3333-4444-555555555555",
            "secret",
            False,
        )

    def test_synchronize_local_calls_sync_to_local(self, tmp_path: Path) -> None:
        """synchronize() with a local dir must call replica.sync_to_local."""
        from unittest.mock import MagicMock

        a = TaskChampionAdapter(sync_local_server_dir=str(tmp_path / "server"))
        a._replica = MagicMock()
        a.synchronize()
        a._replica.sync_to_local.assert_called_once_with(str(tmp_path / "server"), False)

    def test_synchronize_local_takes_precedence(self, tmp_path: Path) -> None:
        """sync_local_server_dir takes precedence over sync_server_url."""
        from unittest.mock import MagicMock

        a = TaskChampionAdapter(
            sync_server_url="https://sync.example.com",
            sync_local_server_dir=str(tmp_path / "server"),
        )
        a._replica = MagicMock()
        a.synchronize()
        a._replica.sync_to_local.assert_called_once()
        a._replica.sync_to_remote.assert_not_called()

    def test_synchronize_wraps_exception_as_task_sync_error(self) -> None:
        """Exceptions from the replica sync call must be wrapped in TaskSyncError."""
        from unittest.mock import MagicMock

        a = TaskChampionAdapter(sync_server_url="https://sync.example.com")
        a._replica = MagicMock()
        a._replica.sync_to_remote.side_effect = RuntimeError("network error")
        with pytest.raises(TaskSyncError, match="network error"):
            a.synchronize()

    def test_has_local_changes_false_on_empty_replica(
        self, adapter: TaskChampionAdapter
    ) -> None:
        """Fresh in-memory replica has no pending operations."""
        assert adapter.has_local_changes() is False
        assert adapter.pending_local_ops_count() == 0

    def test_has_local_changes_true_after_add(
        self, adapter: TaskChampionAdapter
    ) -> None:
        """Adding a task creates pending local operations."""
        adapter.add_task(TaskInputDTO(description="Unpushed task"))
        assert adapter.has_local_changes() is True
        assert adapter.pending_local_ops_count() > 0

    def test_has_local_changes_false_after_local_sync(self, tmp_path) -> None:
        """After a successful local sync, pending operations should be 0."""
        server_dir = tmp_path / "srv"
        server_dir.mkdir()
        data_dir = tmp_path / "data"

        a = TaskChampionAdapter(
            data_location=str(data_dir),
            sync_local_server_dir=str(server_dir),
        )
        a.add_task(TaskInputDTO(description="Will be synced"))
        assert a.has_local_changes() is True

        a.synchronize()
        assert a.has_local_changes() is False
        assert a.pending_local_ops_count() == 0


# ---------------------------------------------------------------------------
# AdapterProtocol compliance
# ---------------------------------------------------------------------------


class TestProtocolCompliance:
    def test_satisfies_adapter_protocol(self, adapter: TaskChampionAdapter) -> None:
        from taskwarrior.adapters import AdapterProtocol

        assert isinstance(adapter, AdapterProtocol)


# ---------------------------------------------------------------------------
# Facade injection
# ---------------------------------------------------------------------------


class TestFacadeInjection:
    """Tests for TaskWarrior(adapter=TaskChampionAdapter(...)) injection."""

    @pytest.fixture
    def tw_tc(self, tmp_path: object) -> object:
        """TaskWarrior facade using an in-memory TaskChampionAdapter."""
        from taskwarrior.main import TaskWarrior

        return TaskWarrior(adapter=TaskChampionAdapter())

    def test_add_and_get_task(self, tw_tc: object) -> None:
        from taskwarrior.main import TaskWarrior

        tw: TaskWarrior = tw_tc  # type: ignore[assignment]
        added = tw.add_task(TaskInputDTO(description="Facade test"))
        retrieved = tw.get_task(added.uuid)
        assert retrieved.description == "Facade test"

    def test_get_tasks_returns_pending(self, tw_tc: object) -> None:
        from taskwarrior.main import TaskWarrior

        tw: TaskWarrior = tw_tc  # type: ignore[assignment]
        tw.add_task(TaskInputDTO(description="Task A"))
        tw.add_task(TaskInputDTO(description="Task B"))
        tasks = tw.get_tasks()
        assert len(tasks) == 2

    def test_backend_type_in_get_info(self, tw_tc: object) -> None:
        from taskwarrior.main import TaskWarrior

        tw: TaskWarrior = tw_tc  # type: ignore[assignment]
        info = tw.get_info()
        assert info["backend_type"] == "taskchampion"
        assert "taskchampion" in info["backend_version"]

    def test_get_info_data_location_in_memory(self, tw_tc: object) -> None:
        """In-memory adapter reports data_location as None."""
        from taskwarrior.main import TaskWarrior

        tw: TaskWarrior = tw_tc  # type: ignore[assignment]
        info = tw.get_info()
        assert info["data_location"] is None

    def test_get_info_data_location_on_disk(self, tmp_path) -> None:
        """On-disk adapter reports the resolved data directory."""
        from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
        from taskwarrior.main import TaskWarrior

        data_dir = tmp_path / "task_data"
        tw = TaskWarrior(adapter=TaskChampionAdapter(data_location=str(data_dir)))
        info = tw.get_info()
        assert info["data_location"] == str(data_dir)

    def test_get_info_sync_no_sync(self, tw_tc: object) -> None:
        """No sync configured → sync_configured False, all sync keys None/absent."""
        from taskwarrior.main import TaskWarrior

        tw: TaskWarrior = tw_tc  # type: ignore[assignment]
        info = tw.get_info()
        assert info["sync_configured"] is False
        assert info["sync_backend"] is None
        assert info["sync_server_url"] is None
        assert info["sync_local_server_dir"] is None
        assert info["sync_client_id"] is None

    def test_get_info_sync_remote(self, tmp_path) -> None:
        """Remote sync configured → correct keys populated."""
        from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
        from taskwarrior.main import TaskWarrior

        tw = TaskWarrior(adapter=TaskChampionAdapter(
            data_location=None,
            sync_server_url="https://sync.example.com",
            sync_client_id="test-uuid",
            sync_encryption_secret="secret",
        ))
        info = tw.get_info()
        assert info["sync_configured"] is True
        assert info["sync_backend"] == "remote"
        assert info["sync_server_url"] == "https://sync.example.com"
        assert info["sync_client_id"] == "test-uuid"
        assert info["sync_local_server_dir"] is None

    def test_get_info_sync_local(self, tmp_path) -> None:
        """Local sync configured → sync_backend is 'local'."""
        from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
        from taskwarrior.main import TaskWarrior

        server_dir = tmp_path / "srv"
        server_dir.mkdir()
        tw = TaskWarrior(adapter=TaskChampionAdapter(
            data_location=None,
            sync_local_server_dir=str(server_dir),
        ))
        info = tw.get_info()
        assert info["sync_configured"] is True
        assert info["sync_backend"] == "local"
        assert info["sync_local_server_dir"] == str(server_dir)
        assert info["sync_server_url"] is None
        assert info["sync_client_id"] is None

    def test_delete_and_done(self, tw_tc: object) -> None:
        from taskwarrior.main import TaskWarrior

        tw: TaskWarrior = tw_tc  # type: ignore[assignment]
        t1 = tw.add_task(TaskInputDTO(description="Delete me"))
        t2 = tw.add_task(TaskInputDTO(description="Complete me"))
        tw.delete_task(t1.uuid)
        tw.done_task(t2.uuid)
        pending = tw.get_tasks()
        assert all(t.uuid not in (t1.uuid, t2.uuid) for t in pending)


# ---------------------------------------------------------------------------
# Thread affinity
# ---------------------------------------------------------------------------


class TestThreadAffinity:
    def test_wrong_thread_raises_runtime_error(self) -> None:
        """Accessing the adapter from a foreign thread raises RuntimeError, not a Rust panic."""
        adapter = TaskChampionAdapter()
        error: list[BaseException] = []

        def worker() -> None:
            try:
                adapter.get_tasks()
            except RuntimeError as exc:
                error.append(exc)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert len(error) == 1
        assert "thread" in str(error[0]).lower()

    def test_same_thread_does_not_raise(self, adapter: TaskChampionAdapter) -> None:
        """Calling the adapter on the creator thread is always allowed."""
        tasks = adapter.get_tasks()
        assert isinstance(tasks, list)

    def test_error_message_contains_thread_ids(self) -> None:
        """The RuntimeError message identifies both owner and caller thread IDs."""
        adapter = TaskChampionAdapter()
        error: list[RuntimeError] = []

        def worker() -> None:
            try:
                adapter.get_tasks()
            except RuntimeError as exc:
                error.append(exc)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert error
        msg = str(error[0])
        assert str(adapter._owner_thread_id) in msg


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class TestAdapterMetrics:
    def test_calls_total_increments(self, adapter: TaskChampionAdapter) -> None:
        adapter.add_task(TaskInputDTO(description="m1"))
        adapter.add_task(TaskInputDTO(description="m2"))
        metrics = adapter.get_metrics()
        assert metrics["calls_total"] >= 2

    def test_errors_total_increments_on_failure(self, adapter: TaskChampionAdapter) -> None:
        from taskwarrior.exceptions import TaskNotFound

        with pytest.raises(TaskNotFound):
            adapter.get_task(str(uuid.uuid4()))  # non-existent UUID goes through _locked_call
        metrics = adapter.get_metrics()
        assert metrics["errors_total"] >= 1

    def test_avg_wait_seconds_is_non_negative(self, adapter: TaskChampionAdapter) -> None:
        adapter.get_tasks()
        metrics = adapter.get_metrics()
        assert metrics["avg_wait_seconds"] >= 0.0

    def test_metrics_snapshot_keys(self, adapter: TaskChampionAdapter) -> None:
        adapter.get_tasks()
        metrics = adapter.get_metrics()
        assert set(metrics) == {"calls_total", "errors_total", "avg_wait_seconds"}
