import pytest

from taskwarrior import TaskInputDTO
from taskwarrior.exceptions import TaskValidationError


def test_add_task_empty_description():
    """Test that creating a task with empty description raises TaskValidationError."""
    with pytest.raises(TaskValidationError, match="Task description cannot be empty"):
        TaskInputDTO(description="")


def test_add_task_none_description():
    """Test that creating a task with None description is allowed (for modify use case)."""
    task = TaskInputDTO(description=None)
    assert task.description is None


def test_modify_task_without_description(tw):
    """Test that modifying a task works with non-description fields."""
    original_task = TaskInputDTO(description="Original task")
    added_task = tw.add_task(original_task)

    modified_task = TaskInputDTO(tags=["updated"])
    tw.modify_task(modified_task, added_task.uuid)

    updated_task = tw.get_task(added_task.uuid)
    assert "updated" in updated_task.tags
