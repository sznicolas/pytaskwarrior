from __future__ import annotations

import pytest
from uuid import uuid4

from src.taskwarrior import TaskWarrior, TaskInputDTO, TaskOutputDTO
from src.taskwarrior.enums import Priority, TaskStatus, RecurrencePeriod
from src.taskwarrior.exceptions import (
    TaskNotFound,
    TaskValidationError,
    TaskWarriorError,
)


class TestTaskWarriorTasks:
    """Test cases for TaskWarrior task operations."""

    def test_add_task_success(self, tw: TaskWarrior):
        """Test add_task method with valid task."""
        task = TaskInputDTO(description="Test task")
        result = tw.add_task(task)

        assert result.uuid is not None
        assert result.description == "Test task"

    def test_modify_task_success(self, tw: TaskWarrior):
        """Test modify_task method with valid task modification."""
        # First add a task
        task = TaskInputDTO(description="Original task")
        added_task = tw.add_task(task)

        # Then modify it
        modified_task = TaskInputDTO(description="Modified task")
        result = tw.modify_task(modified_task, added_task.uuid)

        assert result.uuid == added_task.uuid
        assert result.description == "Modified task"

    def test_get_task_success(self, tw: TaskWarrior):
        """Test get_task method with valid UUID."""
        # First add a task
        task = TaskInputDTO(description="Test task")
        added_task = tw.add_task(task)

        # Then retrieve it
        result = tw.get_task(added_task.uuid)

        assert result.uuid == added_task.uuid
        assert result.description == "Test task"

    def test_get_tasks_success(self, tw: TaskWarrior):
        """Test get_tasks method with filters."""
        # Add a few tasks
        task1 = TaskInputDTO(description="Task 1")
        task2 = TaskInputDTO(description="Task 2")
        tw.add_task(task1)
        tw.add_task(task2)

        # Get all tasks
        result = tw.get_tasks()

        assert len(result) >= 2

    def test_delete_and_purge_task_success(self, tw: TaskWarrior):
        """Test purge_task method."""
        # Add a task
        task = TaskInputDTO(description="Task to delete then purge")
        added_task = tw.add_task(task)

        # Delete it
        tw.delete_task(added_task.uuid)
        # Verify it's not retreived by default
        tasks = tw.get_tasks()
        assert added_task.uuid not in [t.uuid for t in tasks]
        # Verify it's retrievable and the status is deleted
        deleted_task = tw.get_task(added_task.uuid)
        assert deleted_task.uuid == added_task.uuid
        assert deleted_task.status == TaskStatus.DELETED

        # Verify if it's not in default get_tasks
        tasks = tw.get_tasks()
        assert deleted_task.uuid not in [t.uuid for t in tasks]

        # Purge it
        tw.purge_task(added_task.uuid)

        # Verify it's purged (should raise TaskNotFound)
        with pytest.raises(TaskNotFound):
            tw.get_task(added_task.uuid)

    def test_done_task_success(self, tw: TaskWarrior):
        """Test done_task method."""
        # Add a task
        task = TaskInputDTO(description="Task to complete")
        added_task = tw.add_task(task)

        # Mark as done
        tw.done_task(added_task.uuid)

        # Verify it's completed
        result = tw.get_task(added_task.uuid)
        assert result.status == TaskStatus.COMPLETED

    def test_start_task_success(self, tw: TaskWarrior):
        """Test start_task method."""
        # Add a task
        task = TaskInputDTO(description="Task to start")
        added_task = tw.add_task(task)

        # Start it
        tw.start_task(added_task.uuid)

        # Verify it's started
        result = tw.get_task(added_task.uuid)
        assert result.status == TaskStatus.PENDING
        assert result.start is not None

    def test_stop_task_success(self, tw: TaskWarrior):
        """Test stop_task method."""
        # Add and start a task
        task = TaskInputDTO(description="Task to stop")
        added_task = tw.add_task(task)
        tw.start_task(added_task.uuid)

        # Stop it
        tw.stop_task(added_task.uuid)

        # Verify it's stopped
        result = tw.get_task(added_task.uuid)
        assert result.status == TaskStatus.PENDING

    def test_annotate_task_success(self, tw: TaskWarrior):
        """Test annotate_task method."""
        # Add a task
        task = TaskInputDTO(description="Task to annotate")
        added_task = tw.add_task(task)

        # Add annotation
        tw.annotate_task(added_task.uuid, "Test annotation")

        # Verify annotation was added
        annotated_task = tw.get_task(added_task.uuid)
        # Note: Annotations are not directly accessible through the DTO
        assert len(annotated_task.annotations) == 1
        assert annotated_task.annotations[0].description == "Test annotation"

    def test_get_recurring_task_success(self, tw: TaskWarrior):
        """Test get_recurring_task method."""
        # Add a recurring task
        task = TaskInputDTO(description="Recurring task", recur=RecurrencePeriod.WEEKLY, due="today")
        added_task = tw.add_task(task)

        # Get the recurring task
        result = tw.get_recurring_task(added_task.uuid)

        assert result.uuid == added_task.uuid
        # Get recurring instances (should be empty initially)
        result = tw.get_recurring_instances(added_task.uuid)
        assert isinstance(result, list)

    def test_get_tasks_not_found(self, tw: TaskWarrior):
        """Test that get_tasks works with no matching tasks."""
        result = tw.get_tasks(filter_args="description:nonexistent")

        assert len(result) == 0

    def test_get_task_not_found(self, tw: TaskWarrior):
        """Test that TaskNotFound is raised for non-existent task."""
        with pytest.raises(TaskNotFound):
            tw.get_task("nonexistent-uuid")
