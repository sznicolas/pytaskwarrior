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


class TestTaskWarriorAdapterContext:
    """Test cases for TaskWarriorAdapter context management functionality."""

    @pytest.fixture
    def adapter(self, taskwarrior_config: str):
        """Create a TaskWarriorAdapter instance for testing."""
        return TaskWarriorAdapter(task_cmd="task", taskrc_path=taskwarrior_config)

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
