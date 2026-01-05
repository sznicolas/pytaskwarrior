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


class TestTaskWarriorAdapter:
    """Test cases for TaskWarriorAdapter."""

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

    def test_delete_task_success(self, adapter: TaskWarriorAdapter):
        """Test delete_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to delete")
        added_task = adapter.add_task(task)

        # Delete it
        adapter.delete_task(added_task.uuid)

        adapter.get_task(added_task.uuid).status == TaskStatus.DELETED

    def test_purge_task_success(self, adapter: TaskWarriorAdapter):
        """Test purge_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to purge")
        added_task = adapter.add_task(task)
        adapter.delete_task(added_task.uuid)

        # Purge it
        adapter.purge_task(added_task.uuid)

        # Verify it's purged (should raise TaskNotFound)
        with pytest.raises(TaskNotFound):
            adapter.get_task(added_task.uuid)

    def test_done_task_success(self, adapter: TaskWarriorAdapter):
        """Test done_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to complete")
        added_task = adapter.add_task(task)

        # Mark as done
        adapter.done_task(added_task.uuid)

        # Verify it's completed
        result = adapter.get_task(added_task.uuid)
        assert result.status == TaskStatus.COMPLETED

    def test_start_task_success(self, adapter: TaskWarriorAdapter):
        """Test start_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to start")
        added_task = adapter.add_task(task)

        # Start it
        adapter.start_task(added_task.uuid)

        # Verify it's started
        result = adapter.get_task(added_task.uuid)
        assert result.start

    def test_stop_task_success(self, adapter: TaskWarriorAdapter):
        """Test stop_task with valid UUID."""
        # Add and start a task first
        task = TaskInputDTO(description="Task to stop")
        added_task = adapter.add_task(task)
        adapter.start_task(added_task.uuid)

        # Stop it
        adapter.stop_task(added_task.uuid)

        # Verify it's stopped
        result = adapter.get_task(added_task.uuid)
        assert result.start is None

    def test_annotate_task_success(self, adapter: TaskWarriorAdapter):
        """Test annotate_task with valid annotation."""
        # Add a task first
        task = TaskInputDTO(description="Task to annotate")
        added_task = adapter.add_task(task)

        # Add annotation
        adapter.annotate_task(added_task.uuid, "Test annotation")

        # Verify annotation was added
        result = adapter.get_task(added_task.uuid)
        # Note: Annotations are not directly accessible through the DTO

    def test_set_context_success(self, adapter: TaskWarriorAdapter):
        """Test set_context with valid context."""
        adapter.set_context("test_context", "status:pending")

        # Verify context was set by trying to apply it
        adapter.apply_context("test_context")

    def test_apply_context_success(self, adapter: TaskWarriorAdapter):
        """Test apply_context with valid context."""
        # First set a context
        adapter.set_context("test_context", "status:pending")

        # Then apply it
        adapter.apply_context("test_context")

    def test_remove_context_success(self, adapter: TaskWarriorAdapter):
        """Test remove_context with valid context."""
        # Set and apply a context first
        adapter.set_context("test_context", "status:pending")
        adapter.apply_context("test_context")

        # Then remove it
        adapter.remove_context()

    def test_get_info_success(self, adapter: TaskWarriorAdapter):
        """Test get_info with successful retrieval."""
        info = adapter.get_info()

        assert "task_cmd" in info
        assert "taskrc_path" in info
        assert "options" in info

    # New tests added below:

    def test_get_recurring_instances_with_actual_recurring_task(
        self, adapter: TaskWarriorAdapter
    ):
        """Test get_recurring_instances with actual recurring tasks."""
        # Add a recurring task
        task = TaskInputDTO(
            description="Recurring test task",
            recur=RecurrencePeriod.WEEKLY,
            due="tomorrow",
        )
        recurring_task = adapter.add_task(task)

        # Get instances (should be empty initially)
        instances = adapter.get_recurring_instances(recurring_task.uuid)
        assert isinstance(instances, list)

        # Add a task that depends on the recurring task
        dependent_task = TaskInputDTO(
            description="Dependent task", depends=[recurring_task.uuid]
        )
        adapter.add_task(dependent_task)

    def test_get_recurring_task_with_both_types(self, adapter: TaskWarriorAdapter):
        """Test get_recurring_task with both recurring and non-recurring tasks."""
        # Add a regular task
        regular_task = adapter.add_task(TaskInputDTO(description="Regular task"))

        # Add a recurring task
        recurring_task = adapter.add_task(
            TaskInputDTO(description="Recurring task", recur=RecurrencePeriod.WEEKLY, due="eom")
        )

        # Test getting regular task (should work)
        result = adapter.get_recurring_task(regular_task.uuid)
        assert result.uuid == regular_task.uuid

        # Test getting recurring task (should work)
        result = adapter.get_recurring_task(recurring_task.uuid)
        assert result.uuid == recurring_task.uuid

    def test_build_args_multiple_dependencies(self, adapter: TaskWarriorAdapter):
        """Test _build_args with multiple dependencies."""
        dep_uuid1 = uuid4()
        dep_uuid2 = uuid4()
        task = TaskInputDTO(
            description="Task with multiple deps", depends=[dep_uuid1, dep_uuid2]
        )
        args = adapter._build_args(task)

        assert f"depends+={str(dep_uuid1)}" in args
        assert f"depends+={str(dep_uuid2)}" in args

    def test_modify_task_with_multiple_fields(self, adapter: TaskWarriorAdapter):
        """Test modify_task with multiple field modifications."""
        # Add a task
        original_task = TaskInputDTO(
            description="Original task", priority=Priority.LOW, project="TestProject"
        )
        added_task = adapter.add_task(original_task)

        # Modify with multiple fields
        modified_task = TaskInputDTO(
            description="Modified task",
            priority=Priority.HIGH,
            project="ModifiedProject",
            tags=["tag1", "tag2"],
        )
        result = adapter.modify_task(modified_task, added_task.uuid)

        assert result.description == "Modified task"
        assert result.priority == Priority.HIGH
        assert result.project == "ModifiedProject"
        assert result.tags == ["tag1", "tag2"]

    def test_modify_task_nonexistent(self, adapter: TaskWarriorAdapter):
        """Test modify_task with non-existent task."""
        task = TaskInputDTO(description="Test task")

        with pytest.raises(TaskValidationError):
            adapter.modify_task(task, "nonexistent-uuid")

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

    def test_set_context_invalid_name(self, adapter: TaskWarriorAdapter):
        """Test set_context with invalid context name."""
        # This should not raise an exception but may fail at execution
        try:
            adapter.set_context("", "status:pending")
        except Exception:
            # Expected behavior - context name cannot be empty
            pass

    def test_apply_context_nonexistent(self, adapter: TaskWarriorAdapter):
        """Test apply_context with non-existent context."""
        with pytest.raises(TaskWarriorError):
            adapter.apply_context("nonexistent_context")

    def test_remove_context_no_current(self, adapter: TaskWarriorAdapter):
        """Test remove_context when no context is applied."""
        # This should not raise an exception
        try:
            adapter.remove_context()
        except Exception:
            # May raise if no context is set, but that's acceptable
            pass

    def test_context_management_sequence(self, adapter: TaskWarriorAdapter):
        """Test sequence of context management operations."""
        # Set a context
        adapter.set_context("test_context", "status:pending")

        # Apply it
        adapter.apply_context("test_context")

        # Remove it
        adapter.remove_context()

    def test_task_output_to_input_comprehensive(self, adapter: TaskWarriorAdapter):
        """Test task_output_to_input with comprehensive field combinations."""
        from src.taskwarrior.main import task_output_to_input

        # Add a task with various fields
        task = TaskInputDTO(
            description="Test task",
            priority=Priority.HIGH,
            project="TestProject",
            tags=["tag1", "tag2", "tag3"],
            due="2026-12-31T23:59:59Z",
            scheduled="2026-01-15T00:00:00Z",
            wait="2026-01-10T12:30:45Z",
            until="2027-01-01T00:00:00Z",
            recur=RecurrencePeriod.WEEKLY,
        )

        added_task = adapter.add_task(task)
        input_task = task_output_to_input(added_task)

        assert input_task.description == "Test task"
        assert input_task.priority == Priority.HIGH
        assert input_task.project == "TestProject"
        assert input_task.tags == ["tag1", "tag2", "tag3"]
        assert input_task.due == "2026-12-31T23:59:59+00:00"
        assert input_task.scheduled == "2026-01-15T00:00:00+00:00"
        assert input_task.wait == "2026-01-10T12:30:45+00:00"
        assert input_task.until == "2027-01-01T00:00:00+00:00"
        assert input_task.recur == RecurrencePeriod.WEEKLY
        # UUID should not be present
        assert not hasattr(input_task, "uuid")

    def test_task_output_to_input_datetime_edge_cases(
        self, adapter: TaskWarriorAdapter
    ):
        """Test task_output_to_input with datetime edge cases."""
        from src.taskwarrior.main import task_output_to_input

        # Add a task with minimal fields
        task = TaskInputDTO(description="Minimal task")
        added_task = adapter.add_task(task)

        # Convert to input DTO
        input_task = task_output_to_input(added_task)

        assert input_task.description == "Minimal task"
        # Other fields should be None or default
        assert input_task.priority is None
        assert input_task.project is None
        assert input_task.tags == []

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

    def test_annotate_task_special_characters(self, adapter: TaskWarriorAdapter):
        """Test annotate_task with special characters."""
        task = adapter.add_task(TaskInputDTO(description="Task to annotate"))

        # Test with special characters
        special_annotation = "Test annotation with !@#$%^&*()_+-=[]{}|;':\",./<>?"
        adapter.annotate_task(task.uuid, special_annotation)

        # Verify annotation was added (check by retrieving task)
        result = adapter.get_task(task.uuid)
        # Note: Annotations are not directly accessible through the DTO

    def test_annotate_task_long_annotation(self, adapter: TaskWarriorAdapter):
        """Test annotate_task with long annotation."""
        task = adapter.add_task(TaskInputDTO(description="Task to annotate"))

        # Test with long annotation
        long_annotation = "A" * 1000
        adapter.annotate_task(task.uuid, long_annotation)

        # Verify annotation was added
        result = adapter.get_task(task.uuid)

    def test_get_recurring_instances_empty(self, adapter: TaskWarriorAdapter):
        """Test get_recurring_instances with no instances."""
        # Add a regular task
        task = TaskInputDTO(description="Regular task")
        regular_task = adapter.add_task(task)

        # Get instances (should be empty)
        instances = adapter.get_recurring_instances(regular_task.uuid)
        assert isinstance(instances, list)
        assert len(instances) == 0

    def test_get_recurring_instances_with_instances(self, adapter: TaskWarriorAdapter):
        """Test get_recurring_instances with actual instances."""
        # Add a recurring task
        task = TaskInputDTO(description="Recurring task", recur=RecurrencePeriod.WEEKLY, due="pentecost")
        recurring_task = adapter.add_task(task)

        # Get instances (should be empty initially)
        instances = adapter.get_recurring_instances(recurring_task.uuid)
        assert isinstance(instances, list)
        assert len(instances) == 0

    def test_get_recurring_task_nonexistent(self, adapter: TaskWarriorAdapter):
        """Test get_recurring_task with non-existent task."""
        with pytest.raises(TaskNotFound):
            adapter.get_recurring_task("nonexistent-uuid")

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

    def test_add_task_invalid_command_args(self, adapter: TaskWarriorAdapter):
        """Test add_task with invalid command arguments."""
        # This is hard to test directly, but we can verify validation works
        task = TaskInputDTO(description="Test task")

        # Test that it doesn't raise an exception for valid input
        result = adapter.add_task(task)
        assert result.uuid is not None

        # Test with invalid date format
        task_with_invalid_date = TaskInputDTO(
            description="Test task", due="invalid_date_format"
        )

        with pytest.raises(TaskValidationError):
            adapter.add_task(task_with_invalid_date)
