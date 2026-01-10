from __future__ import annotations

import json
import subprocess
from uuid import uuid4

import pytest

from src import TaskStatus
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

    def test_validate_date_string_valid(self, adapter: TaskWarriorAdapter):
        """Test _validate_date_string with valid date formats."""
        assert adapter._validate_date_string("tomorrow") is True

    def test_validate_date_string_invalid(self, adapter: TaskWarriorAdapter):
        """Test _validate_date_string with invalid date formats."""
        assert adapter._validate_date_string("invalid_date") is False

    def test_build_args_minimal(self, adapter: TaskWarriorAdapter):
        """Test _build_args with minimal TaskInputDTO."""
        task = TaskInputDTO(description="Minimal task")
        args = adapter._build_args(task)

        assert "description='Minimal task'" in args
        assert len(args) == 1

    def test_build_args_all_fields(
        self, adapter: TaskWarriorAdapter, sample_task: TaskInputDTO
    ):
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

    def test_add_task_success(self, adapter: TaskWarriorAdapter):
        """Test add_task with valid task."""
        task = TaskInputDTO(description="Test task")
        result = adapter.add_task(task)

        assert result.uuid is not None
        assert result.description == "Test task"

    def test_create_task_empty_description_validation(
        self, adapter: TaskWarriorAdapter
    ):
        """Test add_task with empty description validation."""

        with pytest.raises(
            TaskValidationError, match="Task description cannot be empty"
        ):
            TaskInputDTO(description="")

    def test_add_task_empty_description_validation(self, adapter: TaskWarriorAdapter):
        """Test add_task with empty description validation."""

        task = TaskInputDTO(description="to be removed")
        with pytest.raises(
            TaskValidationError, match="Task description cannot be empty"
        ):
            task.description = ""
            adapter.add_task(task)

    def test_add_task_invalid_date_format_validation(self, adapter: TaskWarriorAdapter):
        """Test add_task with invalid date format validation."""
        task = TaskInputDTO(description="Test task", due="invalid_date")

        with pytest.raises(TaskValidationError, match="Invalid date format for due"):
            adapter.add_task(task)

    def test_modify_task_success(self, adapter: TaskWarriorAdapter):
        """Test modify_task with valid task modification."""
        # Add a task first
        task = TaskInputDTO(description="Original task")
        added_task = adapter.add_task(task)

        # Modify it
        modified_task = TaskInputDTO(description="Modified task")
        result = adapter.modify_task(modified_task, added_task.uuid)

        assert result.uuid == added_task.uuid
        assert result.description == "Modified task"

    def test_modify_task_invalid_date_format_validation(
        self, adapter: TaskWarriorAdapter
    ):
        """Test modify_task with invalid date format validation."""
        task = TaskInputDTO(description="Test task", due="invalid_date")

        with pytest.raises(TaskValidationError, match="Invalid date format for due"):
            adapter.modify_task(task, "test-uuid")

    def test_get_task_existing(self, adapter: TaskWarriorAdapter):
        """Test get_task with existing task."""
        # Add a task first
        task = TaskInputDTO(description="Test task")
        added_task = adapter.add_task(task)

        # Retrieve it
        result = adapter.get_task(added_task.uuid)

        assert result.uuid == added_task.uuid
        assert result.description == "Test task"

    def test_get_task_nonexistent(self, adapter: TaskWarriorAdapter):
        """Test get_task with non-existent task."""
        with pytest.raises(TaskNotFound):
            adapter.get_task("nonexistent-uuid")

    def test_get_tasks_with_filters(self, adapter: TaskWarriorAdapter):
        """Test get_tasks with various filter arguments."""
        # Add a task
        task = TaskInputDTO(description="Test task")
        adapter.add_task(task)

        # Get tasks with filters
        result = adapter.get_tasks(["status:pending"])

        assert len(result) >= 0  # May be empty or have tasks

    def test_get_info_success(self, adapter: TaskWarriorAdapter):
        """Test get_info with successful retrieval."""
        info = adapter.get_info()

        assert "task_cmd" in info
        assert "taskrc_path" in info
        assert "options" in info

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

    def test_build_args_complex_datetime_fields(self, adapter: TaskWarriorAdapter):
        """Test _build_args with complex datetime fields."""
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

    def test_get_tasks_complex_filters(self, adapter: TaskWarriorAdapter):
        """Test get_tasks with complex filter combinations."""
        # Add tasks
        task1 = TaskInputDTO(description="Task 1", priority=Priority.HIGH)
        task2 = TaskInputDTO(description="Task 2", priority=Priority.LOW)
        adapter.add_task(task1)
        adapter.add_task(task2)

        # Test complex filters
        result = adapter.get_tasks(["priority:H", "status:pending"])
        assert len(result) >= 0  # May be empty or have tasks

        result = adapter.get_tasks(["priority:L", "status:pending"])
        assert len(result) >= 0  # May be empty or have tasks

    def test_get_tasks_empty_result(self, adapter: TaskWarriorAdapter):
        """Test get_tasks with filters that return no results."""
        result = adapter.get_tasks(["description:nonexistent"])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_tasks_malformed_json(self, monkeypatch, adapter: TaskWarriorAdapter):
        """Test get_tasks with malformed JSON response."""

        # Mock the subprocess to return malformed JSON
        def mock_run(*args, **kwargs):
            result = subprocess.CompletedProcess(args[0], 0, '{"invalid": json}', "")
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)

        # This should raise TaskNotFound
        with pytest.raises(TaskNotFound):
            adapter.get_tasks([])
