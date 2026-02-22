"""Test cases for handling empty task descriptions."""

import pytest
from taskwarrior import TaskWarrior, TaskInputDTO
from taskwarrior.exceptions import TaskValidationError


def test_add_task_empty_description():
    """Test that creating a task with empty description fails appropriately."""
    tw = TaskWarrior()
    
    # Create a task with empty description
    task = TaskInputDTO(description="")  # Empty description
    
    # Expect a validation error
    with pytest.raises(TaskValidationError):
        tw.add_task(task)


def test_add_task_none_description():
    """Test that creating a task with None description fails appropriately."""
    tw = TaskWarrior()
    
    # Create a task with None description
    task = TaskInputDTO(description=None)  # None description
    
    # Expect a validation error
    with pytest.raises(TaskValidationError):
        tw.add_task(task)
