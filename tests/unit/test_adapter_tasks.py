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

class TestTaskWarriorAdapterTasks:
    """Test cases for TaskWarriorAdapter task management functionality."""

    @pytest.fixture
    def adapter(self, taskwarrior_config: str, taskwarrior_data: str):
        """Create a TaskWarriorAdapter instance for testing."""
        return TaskWarriorAdapter(task_cmd="task", taskrc_file=taskwarrior_config, data_location=taskwarrior_data)

    def test_task_management_errors(self, adapter: TaskWarriorAdapter):
        """Test task management error conditions."""
        # Test modify_task with non-existent task
        task = TaskInputDTO(description="Test task")
        with pytest.raises(TaskValidationError):
            adapter.modify_task(task, "nonexistent-uuid")

        # Test get_recurring_task with non-existent task
        with pytest.raises(TaskNotFound):
            adapter.get_recurring_task("nonexistent-uuid")

    def test_delete_and_purge_task(self, adapter: TaskWarriorAdapter):
        """Test delete and purge task functionality."""
        # Add a task first
        task = TaskInputDTO(description="Task to delete")
        added_task = adapter.add_task(task)

        # Delete it
        adapter.delete_task(added_task.uuid)
        assert adapter.get_task(added_task.uuid).status == TaskStatus.DELETED

        # Purge it
        adapter.purge_task(added_task.uuid)
        
        # Verify it's purged (should raise TaskNotFound)
        with pytest.raises(TaskNotFound):
            adapter.get_task(added_task.uuid)

    def test_complete_start_stop_task(self, adapter: TaskWarriorAdapter):
        """Test complete, start, and stop task functionality."""
        # Add a task first
        task = TaskInputDTO(description="Task to complete")
        added_task = adapter.add_task(task)

        # Mark as done
        adapter.done_task(added_task.uuid)
        result = adapter.get_task(added_task.uuid)
        assert result.status == TaskStatus.COMPLETED

        # Start it
        adapter.start_task(added_task.uuid)
        result = adapter.get_task(added_task.uuid)
        assert result.start

        # Stop it
        adapter.stop_task(added_task.uuid)
        result = adapter.get_task(added_task.uuid)
        assert result.start is None

    def test_annotate_task_edge_cases(self, adapter: TaskWarriorAdapter):
        """Test annotate_task with edge cases."""
        # Add a task first
        task = TaskInputDTO(description="Task to annotate")
        added_task = adapter.add_task(task)

        # Test with special characters
        special_annotation = "Test annotation with !@#$%^&*()_+-=[]{}|;':\",./<>?"
        adapter.annotate_task(added_task.uuid, special_annotation)

        # Test with long annotation
        long_annotation = "A" * 1000
        adapter.annotate_task(added_task.uuid, long_annotation)

    def test_recurring_task_functionality(self, adapter: TaskWarriorAdapter):
        """Test recurring task functionality."""
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

        # Test getting recurring task (should work)
        result = adapter.get_recurring_task(recurring_task.uuid)
        assert result.uuid == recurring_task.uuid

    def test_multiple_dependencies(self, adapter: TaskWarriorAdapter):
        """Test _build_args with multiple dependencies."""
        dep_uuid1 = uuid4()
        dep_uuid2 = uuid4()
        task = TaskInputDTO(
            description="Task with multiple deps", depends=[dep_uuid1, dep_uuid2]
        )
        args = adapter._build_args(task)

        assert f"depends+={str(dep_uuid1)}" in args
        assert f"depends+={str(dep_uuid2)}" in args

    def test_modify_task_multiple_fields(self, adapter: TaskWarriorAdapter):
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

    def test_get_recurring_instances_edge_cases(self, adapter: TaskWarriorAdapter):
        """Test get_recurring_instances edge cases."""
        # Add a regular task
        task = TaskInputDTO(description="Regular task")
        regular_task = adapter.add_task(task)

        # Get instances (should be empty)
        instances = adapter.get_recurring_instances(regular_task.uuid)
        assert isinstance(instances, list)
        assert len(instances) == 0

    def test_task_output_to_input_edge_cases(self, adapter: TaskWarriorAdapter):
        """Test task_output_to_input with edge cases."""
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
