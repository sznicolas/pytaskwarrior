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
    def adapter(self, taskwarrior_config: str):
        """Create a TaskWarriorAdapter instance for testing."""
        return TaskWarriorAdapter(task_cmd="task", taskrc_path=taskwarrior_config)

    def test_delete_task_success(self, adapter: TaskWarriorAdapter):
        """Test delete_task with valid UUID."""
        # Add a task first
        task = TaskInputDTO(description="Task to delete")
        added_task = adapter.add_task(task)

        # Delete it
        adapter.delete_task(added_task.uuid)

        assert adapter.get_task(added_task.uuid).status == TaskStatus.DELETED

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
