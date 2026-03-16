"""Unit tests for TaskWarrior synchronization facade."""

from __future__ import annotations

from unittest.mock import MagicMock

import logging
import pytest

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


def test_synchronize_is_noop_when_disabled() -> None:
    adapter = MagicMock()
    tw = _taskwarrior_with_adapter(adapter)

    tw.synchronize()

    adapter.synchronize.assert_not_called()


def test_synchronize_logs_warning_when_disabled(caplog) -> None:
    adapter = MagicMock()
    tw = _taskwarrior_with_adapter(adapter)

    with caplog.at_level(logging.WARNING):
        tw.synchronize()

    assert "Synchronization disabled (temporary)" in caplog.text
