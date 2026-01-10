from __future__ import annotations

import pytest

from src.taskwarrior import TaskWarrior, TaskInputDTO


class TestTaskWarriorUtils:
    """Test cases for TaskWarrior utility functions."""

    def test_task_output_to_input_conversion(self, tw: TaskWarrior):
        """Test task_output_to_input conversion function."""
        from src.taskwarrior.main import task_output_to_input
        
        # Add a task
        task = TaskInputDTO(description="Test task")
        added_task = tw.add_task(task)
        
        # Convert to input DTO
        input_task = task_output_to_input(added_task)
        
        assert input_task.description == "Test task"
        # UUID should not be present in the input DTO
        assert not hasattr(input_task, "uuid")

    def test_get_info_success(self, tw: TaskWarrior):
        """Test get_info method."""
        result = tw.get_info()
        
        assert "version" in result
        assert "task_cmd" in result
