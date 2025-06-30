from datetime import datetime, timedelta
from uuid import UUID
import os
from pathlib import Path
import subprocess

import pytest
from pydantic import ValidationError
from taskwarrior import TaskWarrior, Task, TaskStatus, Priority, RecurrencePeriod


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
    tw.purge_task(added_task.uuid)
    with pytest.raises(RuntimeError, match=f'Task {str(added_task.uuid)} not found.'):
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
    recurring_task = tw.add_task(sample_task)
    assert recurring_task.recur == "weekly"
    assert recurring_task.status == TaskStatus.RECURRING
    assert recurring_task.until is not None
    tasks = tw.get_tasks([f'parent:{str(recurring_task.uuid)}'])
    assert len(tasks) == 1
#    assert tw.delete_task(tasks[0].uuid) is None
#    assert tw.delete_task(recurring_task.uuid) is None
#    with pytest.raises(RuntimeError, match=r"Task .* not found."):
#        tw.get_task([str(recurring_task.uuid)])
#    with pytest.raises(RuntimeError, match=r"Task .* not found."):
#        tw.get_tasks([f'parent:{str(recurring_task.uuid)}'])


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

def test_run_task_command_failure(tw: TaskWarrior) -> None:
    """Test handling of Taskwarrior command failure."""
    with pytest.raises(RuntimeError, match=r'TaskWarrior command failed: .*'):
        tw._run_task_command(['; cat /etc/passwd'])
