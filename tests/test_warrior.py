from datetime import datetime, timedelta
from uuid import UUID
import os
from pathlib import Path
import subprocess

import pytest
from pydantic import ValidationError
from src.taskwarrior import TaskWarrior, Task, TaskStatus, Priority, RecurrencePeriod


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
    return Task(
        description="Test Task",
        due=datetime.now() + timedelta(days=1),
        priority=Priority.HIGH,
        project="Test",
        tags=["test", "urgent"]
        # TODO: add other values like udas...
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
    assert tw.taskrc_path == taskwarrior_config
#    assert tw.config_overrides["confirmation"] in ["no", "off", "0"]


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


#def test_task_annotate(tw: TaskWarrior, sample_task: Task) -> None:
#    """Test annotating a task."""
#    added_task = tw.add_task(sample_task)
#    annotation = "Test note"
#    tw.task_annotate(added_task.uuid, annotation)
#    tasks = tw.load_tasks()
#    annotated_task = next((t for t in tasks["pending"] if t.uuid == added_task.uuid), None)
#    assert annotated_task is not None
#    assert any(a["description"] == annotation for a in annotated_task.annotations)


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
    sample_task.until = 'P3W'
    sample_task.recur = RecurrencePeriod.WEEKLY
    task = tw.add_task(sample_task)
    recurring_task = tw.get_recurring_task(task.parent)
    assert recurring_task.recur == "weekly"
    # Recurring tasks should have status 'recurring' when created
    assert recurring_task.status == TaskStatus.RECURRING
    # Check that the child task have status 'pending'
    instances = tw.get_recurring_instances(recurring_task.uuid)
    assert instances[0].parent == recurring_task.uuid
    assert instances[0].status == TaskStatus.PENDING
    assert len(instances) == 1


#def test_context_management(tw: TaskWarrior, sample_task: Task) -> None:
#    """Test setting, applying, and removing context."""
#    tw.task_add(sample_task)
#    tw.set_context("test", "project:Test")
#    tw.apply_context("test")
#    filtered_tasks = tw.filter_tasks(status="pending")
#    assert all(t.project == "Test" for t in filtered_tasks)
#    tw.remove_context()
#    # After removing context, all pending tasks should be visible
#    all_tasks = tw.filter_tasks(status="pending")
#    assert len(all_tasks) >= len(filtered_tasks)


def test_validate_assigment(tw: TaskWarrior, sample_task: Task) -> None:

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


def test_task_with_timedelta_fields() -> None:
    """Test that tasks with timedelta fields serialize correctly."""
    task = Task(
        description="Task with timedelta",
        due=timedelta(days=1, hours=2),
        scheduled=timedelta(hours=3)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict
    assert "scheduled" in task_dict


def test_task_with_uuid_fields() -> None:
    """Test that tasks with UUID fields serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with UUID",
        depends=[test_uuid]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "depends" in task_dict


def test_task_with_datetime_fields() -> None:
    """Test that tasks with datetime fields serialize correctly."""
    now = datetime.now()
    task = Task(
        description="Task with datetime",
        entry=now,
        start=now
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


def test_task_with_recurrence() -> None:
    """Test that tasks with recurrence periods serialize correctly."""
    task = Task(
        description="Recurring task",
        recur=RecurrencePeriod.WEEKLY
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "recur" in task_dict


def test_task_with_priority() -> None:
    """Test that tasks with priority serialize correctly."""
    task = Task(
        description="Task with priority",
        priority=Priority.LOW
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_status() -> None:
    """Test that tasks with status serialize correctly."""
    task = Task(
        description="Task with status",
        status=TaskStatus.COMPLETED
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "status" in task_dict


def test_task_with_project() -> None:
    """Test that tasks with project serialize correctly."""
    task = Task(
        description="Task with project",
        project="TestProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_parent() -> None:
    """Test that tasks with parent UUID serialize correctly."""
    parent_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with parent",
        parent=parent_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "parent" in task_dict


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
    task = Task(
        description="Task with due",
        due=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict


def test_task_with_scheduled_field() -> None:
    """Test that tasks with scheduled field serialize correctly."""
    task = Task(
        description="Task with scheduled",
        scheduled=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "scheduled" in task_dict


def test_task_with_wait_field() -> None:
    """Test that tasks with wait field serialize correctly."""
    task = Task(
        description="Task with wait",
        wait=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "wait" in task_dict


def test_task_with_until_field() -> None:
    """Test that tasks with until field serialize correctly."""
    task = Task(
        description="Task with until",
        until=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "until" in task_dict


def test_task_with_modified_field() -> None:
    """Test that tasks with modified field serialize correctly."""
    task = Task(
        description="Task with modified",
        modified=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "modified" in task_dict


def test_task_with_end_field() -> None:
    """Test that tasks with end field serialize correctly."""
    task = Task(
        description="Task with end",
        end=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "end" in task_dict


def test_task_with_start_field() -> None:
    """Test that tasks with start field serialize correctly."""
    task = Task(
        description="Task with start",
        start=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "start" in task_dict


def test_task_with_entry_field() -> None:
    """Test that tasks with entry field serialize correctly."""
    task = Task(
        description="Task with entry",
        entry=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "entry" in task_dict


def test_task_with_index_field() -> None:
    """Test that tasks with index field serialize correctly."""
    task = Task(
        description="Task with index",
        index=123
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "index" in task_dict


def test_task_with_uuid_field() -> None:
    """Test that tasks with uuid field serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with uuid",
        uuid=test_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "uuid" in task_dict


def test_task_with_depends_field() -> None:
    """Test that tasks with depends field serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with depends",
        depends=[test_uuid]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "depends" in task_dict


def test_task_with_tags_field() -> None:
    """Test that tasks with tags field serialize correctly."""
    task = Task(
        description="Task with tags",
        tags=["tag1", "tag2"]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "tags" in task_dict


def test_task_with_priority_field() -> None:
    """Test that tasks with priority field serialize correctly."""
    task = Task(
        description="Task with priority",
        priority=Priority.HIGH
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_status_field() -> None:
    """Test that tasks with status field serialize correctly."""
    task = Task(
        description="Task with status",
        status=TaskStatus.PENDING
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "status" in task_dict


def test_task_with_project_field() -> None:
    """Test that tasks with project field serialize correctly."""
    task = Task(
        description="Task with project",
        project="TestProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_parent_field() -> None:
    """Test that tasks with parent field serialize correctly."""
    parent_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with parent",
        parent=parent_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "parent" in task_dict


def test_task_with_context_field() -> None:
    """Test that tasks with context field serialize correctly."""
    task = Task(
        description="Task with context",
        context="test-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "context" in task_dict


def test_task_with_recur_field() -> None:
    """Test that tasks with recur field serialize correctly."""
    task = Task(
        description="Task with recur",
        recur=RecurrencePeriod.DAILY
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "recur" in task_dict


def test_task_with_due_field_serialization() -> None:
    """Test that tasks with due field serialize to correct format."""
    task = Task(
        description="Task with due",
        due=timedelta(days=1)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "due" in task_dict


def test_task_with_scheduled_field_serialization() -> None:
    """Test that tasks with scheduled field serialize to correct format."""
    task = Task(
        description="Task with scheduled",
        scheduled=timedelta(hours=2)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "scheduled" in task_dict


def test_task_with_wait_field_serialization() -> None:
    """Test that tasks with wait field serialize to correct format."""
    task = Task(
        description="Task with wait",
        wait=timedelta(days=1)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "wait" in task_dict


def test_task_with_until_field_serialization() -> None:
    """Test that tasks with until field serialize to correct format."""
    task = Task(
        description="Task with until",
        until=timedelta(weeks=1)
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "until" in task_dict


def test_task_with_modified_field_serialization() -> None:
    """Test that tasks with modified field serialize to correct format."""
    task = Task(
        description="Task with modified",
        modified=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "modified" in task_dict


def test_task_with_end_field_serialization() -> None:
    """Test that tasks with end field serialize to correct format."""
    task = Task(
        description="Task with end",
        end=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "end" in task_dict


def test_task_with_start_field_serialization() -> None:
    """Test that tasks with start field serialize to correct format."""
    task = Task(
        description="Task with start",
        start=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "start" in task_dict


def test_task_with_entry_field_serialization() -> None:
    """Test that tasks with entry field serialize to correct format."""
    task = Task(
        description="Task with entry",
        entry=datetime.now()
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "entry" in task_dict


def test_task_with_index_field_serialization() -> None:
    """Test that tasks with index field serialize to correct format."""
    task = Task(
        description="Task with index",
        index=456
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "index" in task_dict


def test_task_with_uuid_field_serialization() -> None:
    """Test that tasks with uuid field serialize to correct format."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with uuid",
        uuid=test_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "uuid" in task_dict


def test_task_with_depends_field_serialization() -> None:
    """Test that tasks with depends field serialize to correct format."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with depends",
        depends=[test_uuid]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "depends" in task_dict


def test_task_with_tags_field_serialization() -> None:
    """Test that tasks with tags field serialize to correct format."""
    task = Task(
        description="Task with tags",
        tags=["tag1", "tag2"]
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "tags" in task_dict


def test_task_with_priority_field_serialization() -> None:
    """Test that tasks with priority field serialize to correct format."""
    task = Task(
        description="Task with priority",
        priority=Priority.MEDIUM
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "priority" in task_dict


def test_task_with_status_field_serialization() -> None:
    """Test that tasks with status field serialize to correct format."""
    task = Task(
        description="Task with status",
        status=TaskStatus.COMPLETED
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "status" in task_dict


def test_task_with_project_field_serialization() -> None:
    """Test that tasks with project field serialize to correct format."""
    task = Task(
        description="Task with project",
        project="AnotherProject"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "project" in task_dict


def test_task_with_parent_field_serialization() -> None:
    """Test that tasks with parent field serialize to correct format."""
    parent_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Task with parent",
        parent=parent_uuid
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "parent" in task_dict


def test_task_with_context_field_serialization() -> None:
    """Test that tasks with context field serialize to correct format."""
    task = Task(
        description="Task with context",
        context="another-context"
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "context" in task_dict


def test_task_with_recur_field_serialization() -> None:
    """Test that tasks with recur field serialize to correct format."""
    task = Task(
        description="Task with recur",
        recur=RecurrencePeriod.MONTHLY
    )
    
    # Test serialization
    task_dict = task.model_dump()
    assert "recur" in task_dict


def test_task_with_all_fields() -> None:
    """Test that tasks with all fields serialize correctly."""
    test_uuid = UUID('12345678-1234-5678-1234-567812345678')
    task = Task(
        description="Complete task",
        index=1,
        uuid=test_uuid,
        status=TaskStatus.PENDING,
        priority=Priority.HIGH,
        due=datetime.now(),
        entry=datetime.now(),
        start=datetime.now(),
        end=datetime.now(),
        modified=datetime.now(),
        tags=["tag1", "tag2"],
        project="TestProject",
        depends=[test_uuid],
        parent=test_uuid,
        recur=RecurrencePeriod.WEEKLY,
        scheduled=datetime.now(),
        wait=datetime.now(),
        until=datetime.now(),
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
