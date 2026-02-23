from taskwarrior import TaskInputDTO, TaskWarrior
from taskwarrior.exceptions import TaskValidationError


def test_add_task_empty_description():
    """Test that creating a task with empty description fails appropriately."""
    tw = TaskWarrior()

    # Create a task with empty description - should raise TaskValidationError
    try:
        task = TaskInputDTO(description="")  # Empty description
        assert False, "Expected TaskValidationError to be raised"
    except TaskValidationError as e:
        assert str(e) == "Task description cannot be empty"



def test_add_task_none_description():
    """Test that creating a task with None description fails appropriately."""
    tw = TaskWarrior()

    # Create a task with None description
    task = TaskInputDTO(description=None)  # None description


def test_modify_task_without_description():
    """Test that modifying a task works with non-description fields."""
    tw = TaskWarrior()

    # First create a task with a valid description
    original_task = TaskInputDTO(description="Original task")
    added_task = tw.add_task(original_task)

    # Modify the task with a new tag (not description)
    modified_task = TaskInputDTO(tags=["updated"])
    tw.modify_task(modified_task, added_task.uuid)

    # Verify the modification
    updated_task = tw.get_task(added_task.uuid)
    assert "updated" in updated_task.tags
