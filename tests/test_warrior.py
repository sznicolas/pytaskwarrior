from datetime import datetime, timedelta
from uuid import UUID
import os
from pathlib import Path
import subprocess

import pytest
from pydantic import ValidationError

from src.taskwarrior import TaskWarrior, task_output_to_input

# Import DTOs
from src.taskwarrior.dto.task_dto import TaskInputDTO as Task, TaskStatus, Priority, RecurrencePeriod


@pytest.fixture
def taskwarrior_data(tmp_path: Path) -> Path:
    """Set up a temporary Taskwarrior data directory."""
    data_dir = tmp_path / "taskdata"
    data_dir.mkdir()
    os.environ['TASKDATA'] = str(data_dir)
    return data_dir


@pytest.fixture
def taskwarrior_config(tmp_path: Path, taskwarrior_data: Path) -> str:
    """Create a temporary taskrc file for testing."""
    config_path = tmp_path / ".taskrc"
    config_content = f"""
data.location={taskwarrior_data}
confirmation=off
json.array=TRUE
"""
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def tw(taskwarrior_config: str) -> TaskWarrior:
    """Create a TaskWarrior instance with a temporary config."""
    # Ensure Taskwarrior is installed
    try:
        subprocess.run(["task", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Taskwarrior is not installed or not found in PATH.")
    return TaskWarrior(taskrc_path=taskwarrior_config)


@pytest.fixture
def sample_task() -> Task:
    """Create a sample Task object."""
    now = datetime.now()
    return Task(
        description="Test Task",
        due=(now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        priority=Priority.HIGH,
        project="Test",
        tags=["test", "urgent"]
    )


def test_task_values(sample_task: Task) -> None:
    """Test Task.to_dict conversion."""
    assert sample_task.description == "Test Task"
    assert sample_task.priority == Priority.HIGH.value
    assert sample_task.project == "Test"
    assert sample_task.tags == ["test", "urgent"]


def test_taskwarrior_init(taskwarrior_config: str) -> None:
    """Test TaskWarrior initialization."""
    tw = TaskWarrior(taskrc_path=taskwarrior_config)
    assert tw.get_info()['taskrc_path'] == taskwarrior_config


def test_add_task(tw: TaskWarrior, sample_task: Task) -> None:
    """Test adding a task."""
    added_task = tw.add_task(sample_task)
    assert added_task.description == sample_task.description
    assert isinstance(added_task.uuid, UUID)  # Ensure valid UUID
    # Verify task exists in Taskwarrior
    task = tw.get_task(added_task.uuid)
    assert task.description == sample_task.description


def test_modify_task(tw: TaskWarrior, sample_task: Task) -> None:
    """Test updating a task."""
    added_task = tw.add_task(sample_task)
    task_to_update = task_output_to_input(added_task)
    task_to_update.project = "UpdatedProject"
    updated_task = tw.modify_task(task_to_update, added_task.uuid)
    assert updated_task.project == "UpdatedProject"
    assert updated_task.modified is not None


def test_task_delete_and_purge(tw: TaskWarrior, sample_task: Task) -> None:
    """Test deleting a task."""
    added_task = tw.add_task(sample_task)
    tw.delete_task(added_task.uuid)
    task = tw.get_task(added_task.uuid)
    assert task.status == TaskStatus.DELETED
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
    assert task.status == TaskStatus.COMPLETED
    assert task.end is not None


def test_task_start_stop(tw: TaskWarrior, sample_task: Task) -> None:
    """Test starting and stopping a task."""
    added_task = tw.add_task(sample_task)
    tw.start_task(added_task.uuid)
    started_task = tw.get_tasks(['+ACTIVE', added_task.uuid])[0]
    assert started_task.status == TaskStatus.PENDING
    assert started_task.start is not None
    tw.stop_task(added_task.uuid)
    stopped_task = tw.get_tasks(['-ACTIVE', added_task.uuid])[0]
    assert stopped_task.status == TaskStatus.PENDING


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


def test_recurring_task(tw: TaskWarrior, sample_task: Task) -> None:
    """Test adding a recurring task."""
    now = datetime.now()
    sample_task.until = (now + timedelta(weeks=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
    sample_task.recur = RecurrencePeriod.WEEKLY
    task = tw.add_task(sample_task)
    recurring_task = tw.get_recurring_task(task.parent)
    assert recurring_task.recur == RecurrencePeriod.WEEKLY
    # Recurring tasks should have status 'recurring' when created
    assert recurring_task.status == TaskStatus.RECURRING
    # Check that the child task have status 'pending'
    instances = tw.get_recurring_instances(recurring_task.uuid)
    assert instances[0].parent == recurring_task.uuid
    assert instances[0].status == TaskStatus.PENDING
    assert len(instances) == 1


def test_validate_assignment(tw: TaskWarrior, sample_task: Task) -> None:
    with pytest.raises(ValidationError):
        sample_task.until = 'arheuh'


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
    tw_invalid = TaskWarrior(task_cmd="invalid-file", taskrc_path=taskwarrior_config)
    
    # This should fail at the subprocess level
    with pytest.raises(FileNotFoundError):
        result = tw_invalid.adapter._run_task_command(["version"])



def test_empty_description_validation() -> None:
    """Test that empty task descriptions raise validation error."""
    with pytest.raises(ValidationError, match="Description cannot be empty"):
        Task(description="")


def test_task_serialization() -> None:
    """Test that task serialization works correctly."""
    task = Task(
        description="Test serialization",
        priority=Priority.HIGH,
        project="TestProject"
    )
    
    # Test that serialization works without errors
    task_dict = task.model_dump()
    assert "description" in task_dict
    assert "priority" in task_dict
    assert "project" in task_dict


def test_task_with_datetime_fields() -> None:
    """Test that tasks with datetime fields serialize correctly."""
    now = datetime.now()
    task = Task(
        description="Task with datetime",
        entry=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        start=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        end=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        modified=now.strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "entry" in task_dict
    assert "start" in task_dict


def test_task_with_tags() -> None:
    """Test that tasks with tags serialize correctly."""
    task = Task(
        description="Task with tags",
        tags=["tag1", "tag2"]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "tags" in task_dict


def test_task_with_priority() -> None:
    """Test that tasks with priority serialize correctly."""
    task = Task(
        description="Task with priority",
        priority=Priority.LOW
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_project() -> None:
    """Test that tasks with project serialize correctly."""
    task = Task(
        description="Task with project",
        project="TestProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_context() -> None:
    """Test that tasks with context serialize correctly."""
    task = Task(
        description="Task with context",
        context="test-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "context" in task_dict


def test_task_with_due_field() -> None:
    """Test that tasks with due field serialize correctly."""
    now = datetime.now()
    task = Task(
        description="Task with due",
        due=now.strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict


def test_task_with_scheduled_field() -> None:
    """Test that tasks with scheduled field serialize correctly."""
    now = datetime.now()
    task = Task(
        description="Task with scheduled",
        scheduled=now.strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "scheduled" in task_dict


def test_task_with_wait_field() -> None:
    """Test that tasks with wait field serialize correctly."""
    now = datetime.now()
    task = Task(
        description="Task with wait",
        wait=now.strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "wait" in task_dict


def test_task_with_until_field() -> None:
    """Test that tasks with until field serialize correctly."""
    now = datetime.now()
    task = Task(
        description="Task with until",
        until=now.strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "until" in task_dict


def test_task_with_all_fields() -> None:
    """Test that tasks with all fields serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    now = datetime.now()
    task = Task(
        description="Complete task",
        index=1,
        uuid=test_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        due=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        entry=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        start=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        end=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        modified=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        tags=["tag1", "tag2"],
        project="TestProject",
        depends=[test_uuid],
        parent=test_uuid,
        recur=RecurrencePeriod.WEEKLY,
        scheduled=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        wait=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        until=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        context="test-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert all(field in task_dict for field in [
        "description", "index", "uuid", "status", "priority",
        "due", "entry", "start", "end", "modified", "tags",
        "project", "depends", "parent", "recur", "scheduled",
        "wait", "until", "context"
    ])
