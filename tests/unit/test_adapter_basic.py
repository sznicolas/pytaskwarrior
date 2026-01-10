from __future__ import annotations

import json
import subprocess
from uuid import uuid4

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.task_dto import TaskInputDTO
from src.taskwarrior.enums import Priority, RecurrencePeriod
from src.taskwarrior.exceptions import (
    TaskNotFound,
    TaskValidationError,
    TaskWarriorError,
)


class TestTaskWarriorAdapterBasic:
    """Test cases for basic TaskWarriorAdapter functionality."""

    @pytest.fixture
    def adapter(self, taskwarrior_config: str):
        """Create a TaskWarriorAdapter instance for testing."""
        return TaskWarriorAdapter(task_cmd="task", taskrc_path=taskwarrior_config)

    @pytest.fixture
    def sample_task(self):
        """Create a sample TaskInputDTO for testing."""
        return TaskInputDTO(
            description="Test task",
            priority=Priority.HIGH,
            project="TestProject",
            tags=["tag1", "tag2"],
            due="2023-12-31T23:59:59Z",
            scheduled="2023-12-30T00:00:00Z",
            wait="2023-12-29T00:00:00Z",
            until="2024-12-31T23:59:59Z",
            recur=RecurrencePeriod.WEEKLY,
        )

    def test_validate_date_string_edge_cases(self, adapter: TaskWarriorAdapter):
        """Test _validate_date_string with edge cases."""
        # Test valid dates
        assert adapter._validate_date_string("today") is True
        assert adapter._validate_date_string("tomorrow") is True
        assert adapter._validate_date_string("2023-12-31") is True

        # Test invalid dates
        assert adapter._validate_date_string("") is False
        assert adapter._validate_date_string("not_a_date") is False
        assert adapter._validate_date_string("2023-13-45") is False

    def test_build_args_minimal(self, adapter: TaskWarriorAdapter):
        """Test _build_args with minimal TaskInputDTO."""
        task = TaskInputDTO(description="Minimal task")
        args = adapter._build_args(task)

        assert "description='Minimal task'" in args
        assert len(args) == 1

    def test_build_args_all_fields(self, adapter: TaskWarriorAdapter, sample_task: TaskInputDTO):
        """Test _build_args with all fields populated."""
        args = adapter._build_args(sample_task)

        assert "description='Test task'" in args
        assert "priority=H" in args
        assert "project=TestProject" in args
        assert "tags=tag1,tag2" in args
        assert "due=2023-12-31T23:59:59Z" in args
        assert "scheduled=2023-12-30T00:00:00Z" in args
        assert "wait=2023-12-29T00:00:00Z" in args
        assert "until=2024-12-31T23:59:59Z" in args
        assert "recur=weekly" in args

    def test_build_args_tags_handling(self, adapter: TaskWarriorAdapter):
        """Test _build_args with tags handling."""
        task = TaskInputDTO(description="Task with tags", tags=["tag1", "tag2", "tag3"])
        args = adapter._build_args(task)

        assert "tags=tag1,tag2,tag3" in args

    def test_build_args_depends_handling(self, adapter: TaskWarriorAdapter):
        """Test _build_args with depends field handling."""
        dep_uuid = uuid4()
        task = TaskInputDTO(description="Task with depends", depends=[dep_uuid])
        args = adapter._build_args(task)

        assert f"depends+={str(dep_uuid)}" in args

    def test_build_args_uuid_fields(self, adapter: TaskWarriorAdapter):
        """Test _build_args with UUID fields."""
        task_uuid = uuid4()
        task = TaskInputDTO(description="Task with UUID", parent=task_uuid)
        args = adapter._build_args(task)

        assert f"parent={str(task_uuid)}" in args

    def test_add_task_validation_errors(self, adapter: TaskWarriorAdapter):
        """Test add_task validation errors."""
        # Test empty description
        with pytest.raises(TaskValidationError, match="Task description cannot be empty"):
            TaskInputDTO(description="")

        # Test invalid date format
        task = TaskInputDTO(description="Test task", due="invalid_date")
        with pytest.raises(TaskValidationError, match="Invalid date format for due"):
            adapter.add_task(task)

    def test_modify_task_validation_errors(self, adapter: TaskWarriorAdapter):
        """Test modify_task validation errors."""
        # Test invalid date format
        task = TaskInputDTO(description="Test task", due="invalid_date")
        with pytest.raises(TaskValidationError, match="Invalid date format for due"):
            adapter.modify_task(task, "test-uuid")

    def test_get_task_errors(self, adapter: TaskWarriorAdapter):
        """Test get_task error conditions."""
        # Test non-existent task
        with pytest.raises(TaskNotFound):
            adapter.get_task("nonexistent-uuid")

    def test_get_tasks_errors(self, monkeypatch, adapter: TaskWarriorAdapter):
        """Test get_tasks error conditions."""
        # Test malformed JSON response
        def mock_run(*args, **kwargs):
            result = subprocess.CompletedProcess(args[0], 0, '{"invalid": json}', "")
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        # This should raise TaskNotFound
        with pytest.raises(TaskNotFound):
            adapter.get_tasks([])

    def test_get_info_comprehensive(self, adapter: TaskWarriorAdapter):
        """Test get_info with comprehensive information retrieval."""
        info = adapter.get_info()

        assert "task_cmd" in info
        assert "taskrc_path" in info
        assert "options" in info
        assert "version" in info

        # Verify types
        assert isinstance(info["task_cmd"], str)
        assert isinstance(info["taskrc_path"], (str, type(None)))
        assert isinstance(info["options"], list)
        assert isinstance(info["version"], str)

    def test_get_info_with_custom_params(self, taskwarrior_config: str):
        """Test get_info with custom parameters."""
        adapter = TaskWarriorAdapter(
            task_cmd="task", taskrc_path=taskwarrior_config, data_location="/tmp/test"
        )

        info = adapter.get_info()

        assert info["task_cmd"] == "task"
        assert info["taskrc_path"] == taskwarrior_config
        assert "rc.data.location=/tmp/test" in adapter._options

    def test_complex_datetime_fields(self, adapter: TaskWarriorAdapter):
        """Test with complex datetime fields."""
        task = TaskInputDTO(
            description="Task with complex dates",
            due="2026-12-31T23:59:59Z",
            scheduled="2026-01-15T00:00:00Z",
            wait="2026-01-10T12:30:45Z",
            until="2027-01-01T00:00:00Z",
        )
        args = adapter._build_args(task)

        assert "due=2026-12-31T23:59:59Z" in args
        assert "scheduled=2026-01-15T00:00:00Z" in args
        assert "wait=2026-01-10T12:30:45Z" in args
        assert "until=2027-01-01T00:00:00Z" in args

    def test_add_task_with_various_date_formats(self, adapter: TaskWarriorAdapter):
        """Test add_task with various date formats."""
        # Test with different valid date formats
        task1 = TaskInputDTO(
            description="Task with ISO date", due="2026-12-31T23:59:59Z"
        )
        result1 = adapter.add_task(task1)
        assert result1.due is not None

        task2 = TaskInputDTO(description="Task with simple date", due="2026-12-31")
        result2 = adapter.add_task(task2)
        assert result2.due is not None
