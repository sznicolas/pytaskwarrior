"""Unit tests for TaskWarriorAdapter synchronization via `task sync`."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.taskwarrior.exceptions import TaskSyncError
from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter


def _make_adapter(sync_configured: bool = True) -> TaskWarriorAdapter:
    """Build an adapter stub without touching the filesystem."""
    adapter = TaskWarriorAdapter.__new__(TaskWarriorAdapter)
    adapter.task_cmd = Path("task")
    adapter._cli_options = []
    adapter._sync_configured = sync_configured
    return adapter


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestIsSyncConfigured:
    def test_true_when_sync_keys_present(self) -> None:
        adapter = _make_adapter(sync_configured=True)
        assert adapter.is_sync_configured() is True

    def test_false_when_no_sync_keys(self) -> None:
        adapter = _make_adapter(sync_configured=False)
        assert adapter.is_sync_configured() is False

    def test_reflects_taskrc_at_init(self, tmp_path: Path) -> None:
        """is_sync_configured() returns True only when sync.* keys exist in taskrc."""
        import src.taskwarrior.adapters.taskwarrior_adapter as adapter_mod
        from src.taskwarrior.config.config_store import ConfigStore

        # taskrc with sync config
        taskrc_sync = tmp_path / "sync.taskrc"
        taskrc_sync.write_text("sync.local.server_dir=/tmp/server\n")
        with patch.object(adapter_mod.TaskWarriorAdapter, "_check_binary_path", return_value=Path("task")):
            cfg = ConfigStore(str(taskrc_sync))
            adapter = adapter_mod.TaskWarriorAdapter(cfg, task_cmd="task")
        assert adapter.is_sync_configured() is True

        # taskrc without sync config
        taskrc_no_sync = tmp_path / "nosync.taskrc"
        taskrc_no_sync.write_text("rc.confirmation=off\n")
        with patch.object(adapter_mod.TaskWarriorAdapter, "_check_binary_path", return_value=Path("task")):
            cfg2 = ConfigStore(str(taskrc_no_sync))
            adapter2 = adapter_mod.TaskWarriorAdapter(cfg2, task_cmd="task")
        assert adapter2.is_sync_configured() is False


class TestSynchronize:
    def test_raises_when_not_configured(self) -> None:
        adapter = _make_adapter(sync_configured=False)
        with pytest.raises(TaskSyncError, match="No sync server is configured"):
            adapter.synchronize()

    def test_calls_task_sync_command(self) -> None:
        adapter = _make_adapter(sync_configured=True)
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=0)) as mock_run:
            adapter.synchronize()
        mock_run.assert_called_once_with(["sync"])

    def test_raises_on_nonzero_returncode(self) -> None:
        adapter = _make_adapter(sync_configured=True)
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=1, stderr="sync error")):
            with pytest.raises(TaskSyncError, match="Synchronization failed"):
                adapter.synchronize()

    def test_error_message_includes_stderr(self) -> None:
        adapter = _make_adapter(sync_configured=True)
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=1, stderr="server unreachable")):
            with pytest.raises(TaskSyncError, match="server unreachable"):
                adapter.synchronize()

    def test_uses_stdout_when_stderr_empty(self) -> None:
        """If stderr is empty, the error message should include stdout."""
        adapter = _make_adapter(sync_configured=True)
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=1, stdout="bad state", stderr="")):
            with pytest.raises(TaskSyncError, match="bad state"):
                adapter.synchronize()

    def test_succeeds_silently_on_zero_returncode(self) -> None:
        adapter = _make_adapter(sync_configured=True)
        with patch.object(adapter, "run_task_command", return_value=_completed(returncode=0, stdout="Sync successful.")):
            adapter.synchronize()  # must not raise
