import pytest
from uuid import UUID

from src.taskwarrior import TaskWarrior, Task, Priority


def test_taskwarrior_init(taskwarrior_config: str) -> None:
    """Test TaskWarrior initialization."""
    tw = TaskWarrior(taskrc_path=taskwarrior_config)
    assert tw.taskrc_path == taskwarrior_config


def test_add_task(tw: TaskWarrior, sample_task: Task) -> None:
    """Test adding a task."""
    added_task = tw.add_task(sample_task)
    assert added_task.description == sample_task.description
    assert isinstance(added_task.uuid, UUID)  # Ensure valid UUID
    # Verify task exists in Taskwarrior
    task = tw.get_task(added_task.uuid)
    #assert any(t.uuid == sample_task.uuid for t in tasks["pending"])
    assert task.description == sample_task.description


def test_modify_task(tw: TaskWarrior, sample_task: Task) -> None:
    """Test updating a task."""
    added_task = tw.add_task(sample_task)
    added_task.project = "UpdatedProject"
    updated_task = tw.modify_task(added_task)
    assert updated_task.project == "UpdatedProject"
    assert updated_task.modified is not None
    assert sample_task.tags == ["test", "urgent"]


def test_task_delete_and_purge(tw: TaskWarrior, sample_task: Task) -> None:
    """Test deleting a task."""
    added_task = tw.add_task(sample_task)
    tw.delete_task(added_task.uuid)
    task = tw.get_task(added_task.uuid)
    assert task.status == 'deleted'
    # After purging, the task should not be retrievable
    tw.purge_task(added_task.uuid)
    
    # Try to get the task after purge - should raise TaskNotFound
    with pytest.raises(Exception, match=f'Task {str(added_task.uuid)} not found.'):
        task = tw.get_task(added_task.uuid)


def test_task_done(tw: TaskWarrior, sample_task: Task) -> None:
    """Test marking a task as done."""
    added_task = tw.add_task(sample_task)
    tw.done_task(added_task.uuid)
    task = tw.get_task(added_task.uuid)
    assert task.status == 'completed'
    assert task.end is not None


def test_task_start_stop(tw: TaskWarrior, sample_task: Task) -> None:
    """Test starting and stopping a task. Also test filters"""
    added_task = tw.add_task(sample_task)
    tw.start_task(added_task.uuid)
    started_task = tw.get_tasks(['+ACTIVE', added_task.uuid])[0]
    assert started_task.status == 'pending'
    assert started_task.start is not None
    tw.stop_task(added_task.uuid)
    stopped_task = tw.get_tasks(['-ACTIVE', added_task.uuid])[0]
    assert stopped_task.status == 'pending'


def test_filter_tasks(tw: TaskWarrior, sample_task: Task) -> None:
    """Test filtering tasks."""
    added_task = tw.add_task(sample_task)
    filtered_tasks = tw.get_tasks(['-ACTIVE', added_task.uuid])
    assert filtered_tasks
    filtered_tasks = tw.get_tasks(['+test', 'due:tomorrow'])
    assert filtered_tasks
    filtered_tasks = tw.get_tasks(['/.*est *Task/'])
    assert filtered_tasks
    filtered_tasks = tw.get_tasks(['+test', 'due:P1W'])
    assert filtered_tasks == []


def test_shell_injection_protection(tw: TaskWarrior) -> None:
    """Test that shell injection is properly handled in task descriptions."""
    # Test with potentially dangerous characters in description
    dangerous_description = "Test task; rm  /tmp/toto_123"
    
    # This should not execute the command, but rather add a task with that description
    sample_task = Task(
        description=dangerous_description,
        priority=Priority.HIGH,
        project="Test"
    )
    
    # Add the task
    added_task = tw.add_task(sample_task)
    assert added_task.description == dangerous_description
    
    # Verify the task was actually created with that description
    retrieved_task = tw.get_task(added_task.uuid)
    assert retrieved_task.description == dangerous_description
    
    # Clean up
    tw.delete_task(added_task.uuid)


def test_run_task_command_failure(tw: TaskWarrior, taskwarrior_config: str) -> None:
    """Test handling of Taskwarrior command failure."""
    # Test with a truly invalid executable that doesn't exist
    # This should fail at the subprocess level, not just return "No matches"
    
    # Create a new TaskWarrior instance with invalid task_cmd
    tw_invalid = TaskWarrior(task_cmd="/opt/homebrew/bin/task", taskrc_path=taskwarrior_config)
    
    # This should fail at the subprocess level
    with pytest.raises(FileNotFoundError):
        result = tw_invalid.adapter._run_task_command(["version"])


def test_validate_assigment(tw: TaskWarrior, sample_task: Task) -> None:

    with pytest.raises(Exception):
        sample_task.until = 'arheuh'
