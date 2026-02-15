"""Priority tests to improve coverage to >90%.

These tests cover previously untested error paths and edge cases.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.exceptions import TaskValidationError, TaskWarriorError
from src.taskwarrior.services.context_service import ContextService


class TestBinaryPathNotFound:
    """Test 1: Exception when 'task' binary is not found."""

    def test_binary_not_in_path_raises_error(self):
        """TaskWarriorAdapter should raise TaskValidationError if task command not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(TaskValidationError) as exc_info:
                TaskWarriorAdapter(
                    task_cmd="nonexistent_task_cmd",
                    taskrc_file="/tmp/test_taskrc",
                )
            assert "not found in PATH" in str(exc_info.value)
            assert "nonexistent_task_cmd" in str(exc_info.value)

    def test_binary_found_succeeds(self, taskwarrior_config: str):
        """TaskWarriorAdapter should work when task command is found."""
        # This uses the real 'task' command if available
        try:
            adapter = TaskWarriorAdapter(taskrc_file=taskwarrior_config)
            assert adapter.task_cmd is not None
        except TaskValidationError:
            pytest.skip("TaskWarrior not installed")


class TestApplyContextCommandFailure:
    """Test 3: Context command failure handling."""

    def test_apply_context_nonexistent_raises_error(self, taskwarrior_config: str):
        """apply_context should raise error for non-existent context."""
        try:
            adapter = TaskWarriorAdapter(taskrc_file=taskwarrior_config)
        except TaskValidationError:
            pytest.skip("TaskWarrior not installed")

        service = ContextService(adapter)

        # Trying to apply a context that doesn't exist should fail
        with pytest.raises(TaskWarriorError) as exc_info:
            service.apply_context("nonexistent_context_xyz")
        assert "Failed to apply context" in str(exc_info.value)

    def test_apply_context_empty_name_raises_error(self, taskwarrior_config: str):
        """apply_context should raise error for empty context name."""
        try:
            adapter = TaskWarriorAdapter(taskrc_file=taskwarrior_config)
        except TaskValidationError:
            pytest.skip("TaskWarrior not installed")

        service = ContextService(adapter)

        with pytest.raises(TaskWarriorError) as exc_info:
            service.apply_context("")
        assert "cannot be empty" in str(exc_info.value)

    def test_apply_context_whitespace_name_raises_error(self, taskwarrior_config: str):
        """apply_context should raise error for whitespace-only context name."""
        try:
            adapter = TaskWarriorAdapter(taskrc_file=taskwarrior_config)
        except TaskValidationError:
            pytest.skip("TaskWarrior not installed")

        service = ContextService(adapter)

        with pytest.raises(TaskWarriorError) as exc_info:
            service.apply_context("   ")
        assert "cannot be empty" in str(exc_info.value)


class TestHasContextReturnValue:
    """Test 4: has_context should return bool correctly."""

    def test_has_context_returns_false_for_nonexistent(self, taskwarrior_config: str):
        """has_context should return False for non-existent context."""
        try:
            adapter = TaskWarriorAdapter(taskrc_file=taskwarrior_config)
        except TaskValidationError:
            pytest.skip("TaskWarrior not installed")

        service = ContextService(adapter)
        result = service.has_context("definitely_not_a_real_context")

        assert result is False
        assert isinstance(result, bool)

    def test_has_context_returns_true_for_existing(self, taskwarrior_config: str):
        """has_context should return True for existing context."""
        try:
            adapter = TaskWarriorAdapter(taskrc_file=taskwarrior_config)
        except TaskValidationError:
            pytest.skip("TaskWarrior not installed")

        service = ContextService(adapter)

        # Define a context first
        service.define_context("test_ctx", "+test")

        result = service.has_context("test_ctx")
        assert result is True
        assert isinstance(result, bool)

        # Cleanup
        service.delete_context("test_ctx")

    def test_has_context_handles_exception_gracefully(self):
        """has_context should return False when get_contexts fails."""
        mock_adapter = MagicMock()
        mock_adapter.run_task_command.side_effect = Exception("Simulated failure")

        service = ContextService(mock_adapter)
        result = service.has_context("any_context")

        assert result is False


class TestTaskrcFileCreation:
    """Test 5: Automatic .taskrc file creation."""

    def test_taskrc_created_if_not_exists(self, tmp_path: Path):
        """TaskWarriorAdapter should create .taskrc if it doesn't exist."""
        taskrc_path = tmp_path / "new_taskrc"
        data_path = tmp_path / "task_data"

        assert not taskrc_path.exists()
        assert not data_path.exists()

        with (
            patch("shutil.which", return_value="/usr/bin/task"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            TaskWarriorAdapter(
                taskrc_file=str(taskrc_path),
                data_location=str(data_path),
            )

            # Verify taskrc was created
            assert taskrc_path.exists()
            content = taskrc_path.read_text()
            assert "pytaskwarrior" in content
            assert "data.location" in content

    def test_data_location_created_if_not_exists(self, tmp_path: Path):
        """TaskWarriorAdapter should create data location directory."""
        taskrc_path = tmp_path / "taskrc"
        data_path = tmp_path / "custom_data_dir"

        assert not data_path.exists()

        with (
            patch("shutil.which", return_value="/usr/bin/task"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            TaskWarriorAdapter(
                taskrc_file=str(taskrc_path),
                data_location=str(data_path),
            )

            # Verify data directory was created
            assert data_path.exists()
            assert data_path.is_dir()

    def test_existing_taskrc_not_overwritten(self, tmp_path: Path):
        """TaskWarriorAdapter should not overwrite existing .taskrc."""
        taskrc_path = tmp_path / "existing_taskrc"
        original_content = "# My custom taskrc\nrc.custom=value\n"
        taskrc_path.write_text(original_content)

        with (
            patch("shutil.which", return_value="/usr/bin/task"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            TaskWarriorAdapter(taskrc_file=str(taskrc_path))

            # Verify original content preserved
            assert taskrc_path.read_text() == original_content
