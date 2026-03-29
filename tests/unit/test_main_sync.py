"""Unit tests for TaskWarrior synchronization facade."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.taskwarrior.exceptions import TaskSyncError
from src.taskwarrior.main import TaskWarrior


def _taskwarrior_with_adapter(adapter: MagicMock | None = None) -> TaskWarrior:
    tw = TaskWarrior.__new__(TaskWarrior)
    tw.adapter = adapter or MagicMock()
    return tw


def test_is_sync_configured_delegates_to_adapter() -> None:
    adapter = MagicMock()
    adapter.is_sync_configured.return_value = True

    tw = _taskwarrior_with_adapter(adapter)

    assert tw.is_sync_configured() is True
    adapter.is_sync_configured.assert_called_once()


def test_synchronize_delegates_to_adapter() -> None:
    """synchronize() must delegate to the adapter (it is no longer a no-op)."""
    adapter = MagicMock()
    tw = _taskwarrior_with_adapter(adapter)

    tw.synchronize()

    adapter.synchronize.assert_called_once()


def test_synchronize_propagates_task_sync_error() -> None:
    """TaskSyncError raised by the adapter must propagate to the caller."""
    adapter = MagicMock()
    adapter.synchronize.side_effect = TaskSyncError("sync failed")

    tw = _taskwarrior_with_adapter(adapter)

    with pytest.raises(TaskSyncError, match="sync failed"):
        tw.synchronize()
