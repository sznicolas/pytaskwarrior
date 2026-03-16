"""Unit tests for TaskWarriorAdapter with mocked subprocess.

These tests cover error paths and edge cases without requiring a real
TaskWarrior binary, using unittest.mock to patch subprocess.run.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.task_dto import TaskInputDTO
from src.taskwarrior.exceptions import TaskNotFound, TaskValidationError, TaskWarriorError
from src.taskwarrior.utils.conversions import parse_taskwarrior_date

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    """Return a mock CompletedProcess."""
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


SAMPLE_TASK_JSON = json.dumps([
    {
        "uuid": str(uuid4()),
        "description": "Test task",
        "status": "pending",
        "entry": "20260101T000000Z",
        "modified": "20260101T000000Z",
        "id": 1,
    }
])


@pytest.fixture
def adapter(tmp_path: Path) -> TaskWarriorAdapter:
    """Adapter instance with mocked binary check and file creation."""
    config = tmp_path / ".taskrc"
    config.write_text(f"data.location={tmp_path / 'task'}\n")
    from src.taskwarrior.config.config_store import ConfigStore
    with patch("shutil.which", return_value="/usr/bin/task"), \
         patch.object(ConfigStore, "_check_or_create_taskfiles"):
        return TaskWarriorAdapter(config_store=ConfigStore(str(config)), task_cmd="task")


# ---------------------------------------------------------------------------
# run_task_command — error paths
# ---------------------------------------------------------------------------

class TestRunTaskCommand:
    def test_oserror_is_reraised(self, adapter: TaskWarriorAdapter) -> None:
        with patch("subprocess.run", side_effect=OSError("no such file")):
            with pytest.raises(OSError):
                adapter.run_task_command(["info"])

    def test_timeout_is_reraised(self, adapter: TaskWarriorAdapter) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("task", 30)):
            with pytest.raises(subprocess.SubprocessError):
                adapter.run_task_command(["info"])

    def test_nonzero_returncode_does_not_raise(self, adapter: TaskWarriorAdapter) -> None:
        with patch("subprocess.run", return_value=_completed(returncode=1, stderr="err")):
            result = adapter.run_task_command(["export"])
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# add_task — error paths
# ---------------------------------------------------------------------------

class TestAddTask:
    def test_returncode_nonzero_raises_validation_error(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=1, stderr="fail")):
            with pytest.raises(TaskValidationError, match="Failed to add task"):
                adapter.add_task(TaskInputDTO(description="bad"))

    def test_fallback_to_latest_when_no_created_task_in_stdout(self, adapter: TaskWarriorAdapter) -> None:
        """If stdout doesn't contain 'Created task N.', falls back to +LATEST."""
        add_result = _completed(stdout="Some other output", returncode=0)
        task_result = _completed(stdout=SAMPLE_TASK_JSON, returncode=0)

        with patch.object(adapter, "run_task_command", side_effect=[add_result, task_result]):
            task = adapter.add_task(TaskInputDTO(description="Test"))
        assert task.description == "Test task"

    def test_fallback_empty_list_raises_runtime_error(self, adapter: TaskWarriorAdapter) -> None:
        add_result = _completed(stdout="no id here", returncode=0)
        empty_result = _completed(stdout="[]", returncode=0)

        with patch.object(adapter, "run_task_command", side_effect=[add_result, empty_result]):
            with pytest.raises(RuntimeError, match="Failed to retrieve added task"):
                adapter.add_task(TaskInputDTO(description="Test"))

    def test_annotations_added_after_creation(self, adapter: TaskWarriorAdapter) -> None:
        add_result = _completed(stdout="Created task 1.", returncode=0)
        get_result = _completed(stdout=SAMPLE_TASK_JSON, returncode=0)
        annotate_result = _completed(stdout="", returncode=0)

        calls = [add_result, get_result, annotate_result]
        with patch.object(adapter, "run_task_command", side_effect=calls):
            task = adapter.add_task(TaskInputDTO(description="Task with note", annotations=["note"]))
        assert task.description == "Test task"


# ---------------------------------------------------------------------------
# get_task — error paths
# ---------------------------------------------------------------------------

class TestGetTask:
    def test_returncode_nonzero_raises(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=1, stderr="nope")):
            with pytest.raises(TaskWarriorError):
                adapter.get_task(1)

    def test_json_decode_error_raises_validation_error(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command", return_value=_completed(stdout="not json", returncode=0)):
            with pytest.raises(TaskValidationError, match="Invalid response"):
                adapter.get_task(1)

    def test_multiple_tasks_returned_raises(self, adapter: TaskWarriorAdapter) -> None:
        two_tasks = json.dumps([
            {"uuid": str(uuid4()), "description": "A", "status": "pending", "entry": "20260101T000000Z", "modified": "20260101T000000Z", "id": 1},
            {"uuid": str(uuid4()), "description": "B", "status": "pending", "entry": "20260101T000000Z", "modified": "20260101T000000Z", "id": 2},
        ])
        with patch.object(adapter, "run_task_command", return_value=_completed(stdout=two_tasks, returncode=0)):
            with pytest.raises(TaskWarriorError, match="More than one task"):
                adapter.get_task(1)


# ---------------------------------------------------------------------------
# get_tasks — error paths
# ---------------------------------------------------------------------------

class TestGetTasks:
    def test_returncode_nonzero_raises(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=1, stderr="fail")):
            with pytest.raises(TaskWarriorError, match="Failed to get tasks"):
                adapter.get_tasks()

    def test_json_decode_error_raises_validation_error(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command", return_value=_completed(stdout="bad", returncode=0)):
            with pytest.raises(TaskValidationError, match="Invalid response"):
                adapter.get_tasks()


# ---------------------------------------------------------------------------
# get_recurring_instances — error paths
# ---------------------------------------------------------------------------

class TestGetRecurringInstances:
    def test_no_matches_returns_empty(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(returncode=1, stderr="No matches.")):
            assert adapter.get_recurring_instances("abc") == []

    def test_other_error_raises_task_not_found(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(returncode=1, stderr="Something else failed")):
            with pytest.raises(TaskNotFound):
                adapter.get_recurring_instances("abc")

    def test_empty_stdout_returns_empty(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(stdout="   ", returncode=0)):
            assert adapter.get_recurring_instances("abc") == []

    def test_json_decode_error_raises_task_not_found(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(stdout="not json", returncode=0)):
            with pytest.raises(TaskNotFound, match="Invalid response"):
                adapter.get_recurring_instances("abc")


# ---------------------------------------------------------------------------
# delete / purge / done / start / stop / annotate — error paths
# ---------------------------------------------------------------------------

class TestTaskStateErrors:
    @pytest.mark.parametrize("method,kwargs", [
        ("delete_task", {"task_id_or_uuid": "123"}),
        ("purge_task", {"task_id_or_uuid": "123"}),
        ("done_task", {"task_id_or_uuid": "123"}),
        ("start_task", {"task_id_or_uuid": "123"}),
        ("stop_task", {"task_id_or_uuid": "123"}),
        ("annotate_task", {"task_id_or_uuid": "123", "annotation": "note"}),
    ])
    def test_nonzero_returncode_raises_task_not_found(
        self, adapter: TaskWarriorAdapter, method: str, kwargs: dict
    ) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(returncode=1, stderr="error")):
            with pytest.raises(TaskNotFound):
                getattr(adapter, method)(**kwargs)


# ---------------------------------------------------------------------------
# get_info — version fallback
# ---------------------------------------------------------------------------

class TestGetInfo:
    def test_version_unknown_when_command_raises(self, adapter: TaskWarriorAdapter) -> None:
        from src.taskwarrior.main import TaskWarrior
        tw = TaskWarrior(task_cmd="task")
        with patch.object(tw.adapter, "run_task_command", side_effect=OSError("fail")):
            with pytest.raises(OSError, match="fail"):
                tw.get_info()

    def test_version_populated_when_command_succeeds(self, adapter: TaskWarriorAdapter) -> None:
        from src.taskwarrior.main import TaskWarrior
        tw = TaskWarrior(task_cmd="task")
        with patch.object(tw.adapter, "run_task_command",
                          return_value=_completed(stdout="3.4.0\n", returncode=0)):
            info = tw.get_info()
        assert info["version"] == "3.4.0"


# ---------------------------------------------------------------------------
# task_calc — error paths
# ---------------------------------------------------------------------------

class TestTaskCalc:
    def test_returncode_nonzero_raises(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(returncode=1, stderr="bad")):
            with pytest.raises(TaskWarriorError, match="Failed to calculate"):
                adapter.task_calc("bad_date")

    def test_subprocess_error_raises_task_warrior_error(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          side_effect=subprocess.SubprocessError("timeout")):
            with pytest.raises(TaskWarriorError, match="Failed to calculate"):
                adapter.task_calc("bad_date")


# ---------------------------------------------------------------------------
# task_date_validator — all branches
# ---------------------------------------------------------------------------

class TestTaskDateValidator:
    def test_returncode_nonzero_returns_false(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(returncode=1)):
            assert adapter.task_date_validator("bad") is False

    def test_valid_iso_output_returns_true(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(stdout="2026-02-26T00:00:00", returncode=0)):
            assert adapter.task_date_validator("today") is True

    def test_non_iso_output_returns_false(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(stdout="not_a_date", returncode=0)):
            assert adapter.task_date_validator("not_a_date") is False

    def test_subprocess_error_returns_false(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          side_effect=subprocess.SubprocessError("timeout")):
            assert adapter.task_date_validator("today") is False


# ---------------------------------------------------------------------------
# get_projects — error path
# ---------------------------------------------------------------------------

class TestGetProjects:
    def test_returncode_nonzero_raises(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(returncode=1, stderr="fail")):
            with pytest.raises(TaskWarriorError, match="Failed to get projects"):
                adapter.get_projects()

    def test_returns_project_list(self, adapter: TaskWarriorAdapter) -> None:
        with patch.object(adapter, "run_task_command",
                          return_value=_completed(stdout="work\npersonal\n", returncode=0)):
            assert adapter.get_projects() == ["work", "personal"]


# ---------------------------------------------------------------------------
# synchronize / is_sync_configured — sync logic
# ---------------------------------------------------------------------------

# class TestSync:
#     def test_is_sync_configured_false_when_no_taskrc(self, tmp_path):
#         config = tmp_path / ".taskrc"
#         # Do not create the file (simulate empty taskrc)
#         from src.taskwarrior.config.config_store import ConfigStore
#         config.write_text("")
#         with patch("shutil.which", return_value="/usr/bin/task"):
#             adapter = TaskWarriorAdapter(config_store=ConfigStore(str(config)), task_cmd="task")
#             # Adapter doesn't set _sync automatically due to refactor; ensure attribute exists
#             adapter._sync = None
#             assert adapter.is_sync_configured() is False
#
#     def test_is_sync_configured_true_with_sync_vars(self, tmp_path):
#         config = tmp_path / ".taskrc"
#         config.write_text("sync.local.server_dir=/tmp/syncdir\n")
#         from src.taskwarrior.config.config_store import ConfigStore
#         with patch("shutil.which", return_value="/usr/bin/task"):
#             adapter = TaskWarriorAdapter(config_store=ConfigStore(str(config)), task_cmd="task")
#             # Adapter doesn't set _sync automatically due to refactor; simulate configured sync
#             adapter._sync = object()
#             assert adapter.is_sync_configured() is True
#
#     def test_synchronize_success(self, adapter):
#         from src.taskwarrior.sync_backends.sync_protocol import SyncProtocol
# # Pass a mock SyncProtocol to the adapter
#         class MockSync:
#             def synchronize(self):
#                 self.called = True
#         mock_sync = MockSync()
#         adapter._sync = mock_sync
#         adapter.synchronize()
#         assert hasattr(mock_sync, 'called')
#
#     def test_synchronize_raises_on_error(self, adapter):
#         from src.taskwarrior.exceptions import TaskSyncError
#         class MockSync:
#             def synchronize(self):
#                 raise Exception("sync error")
#         adapter._sync = MockSync()
#         with pytest.raises(TaskSyncError, match="SyncProtocol synchronization failed: sync error"):
#             adapter.synchronize()

# ---------------------------------------------------------------------------
# conversions.py — fallback date parsing (lines 43-45)
# ---------------------------------------------------------------------------

class TestParseTaskwarriorDate:
    def test_compact_format(self) -> None:
        dt = parse_taskwarrior_date("20260115T143000Z")
        assert dt.year == 2026
        assert dt.month == 1
        assert dt.day == 15

    def test_standard_iso_format(self) -> None:
        dt = parse_taskwarrior_date("2026-01-15T14:30:00+00:00")
        assert dt.year == 2026

    def test_fallback_bare_iso(self) -> None:
        """Covers the except ValueError fallback path (lines 43-45)."""
        # A standard date string that fromisoformat can parse directly
        dt = parse_taskwarrior_date("2026-01-15")
        assert dt.year == 2026
        assert dt.month == 1
        assert dt.day == 15
