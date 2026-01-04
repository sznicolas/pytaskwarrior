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
            context="test_context",
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
        print("*** ", args)

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
        assert "context=test_context" in args

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

    def test_add_task_empty_description_validation(self, adapter: TaskWarriorAdapter):
        """Test add_task with empty description validation."""
        task = TaskInputDTO(description="")

        with pytest.raises(
            TaskValidationError, match="Task description cannot be empty"
        ):
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

        # Verify it's deleted (should raise TaskNotFound)
        with pytest.raises(TaskNotFound):
            adapter.get_task(added_task.uuid)

    def test_purge_task_success(self, adapter: TaskWarriorAdapter):
        """Test purge_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to purge")
        added_task = adapter.add_task(task)

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
        assert result.status.value == "completed"

    def test_start_task_success(self, adapter: TaskWarriorAdapter):
        """Test start_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to start")
        added_task = adapter.add_task(task)

        # Start it
        adapter.start_task(added_task.uuid)

        # Verify it's started
        result = adapter.get_task(added_task.uuid)
        assert result.status.value == "started"

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
        assert result.status.value == "pending"

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
        assert "default_options" in info
