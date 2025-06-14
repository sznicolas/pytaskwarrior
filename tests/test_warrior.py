import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json
import os
from pathlib import Path
from taskwarrior import TaskWarrior, Task, TaskStatus, TaskPriority
import subprocess

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
confirmation=no
json.array=TRUE
verbose=nothing
"""
    config_path.write_text(config_content)
    return str(config_path)

@pytest.fixture
def api(taskwarrior_config: str) -> TaskWarrior:
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
        priority=TaskPriority.HIGH,
        project="Test",
        tags=["test", "urgent"]
    )

def test_task_to_dict(sample_task: Task) -> None:
    """Test Task.to_dict conversion."""
    task_dict = sample_task.to_dict()
    assert task_dict["description"] == "Test Task"
    assert task_dict["status"] == TaskStatus.PENDING.value
    assert UUID(task_dict["uuid"])  # Ensure valid UUID
    assert task_dict["priority"] == TaskPriority.HIGH.value
    assert task_dict["project"] == "Test"
    assert task_dict["tags"] == ["test", "urgent"]
    assert "due" in task_dict
    assert "entry" in task_dict

def test_task_from_dict() -> None:
    """Test Task.from_dict creation."""
    task_data = {
        "description": "Test Task",
        "status": "pending",
        "uuid": str(uuid4()),
        "entry": datetime.now().isoformat(),
        "due": (datetime.now() + timedelta(days=1)).isoformat(),
        "priority": "H",
        "project": "Test",
        "tags": ["test"],
        "annotations": [{"entry": datetime.now().isoformat(), "description": "Note"}],
        "depends": [str(uuid4())],
        "recur": "weekly",
        "uda.custom": "mycustomvalue",
        "uda.custom2": "mycustomvalue2"
    }
    task = Task.from_dict(task_data)
    assert task.description == task_data["description"]
    assert task.status == TaskStatus.PENDING
    assert str(task.uuid) == task_data["uuid"]
    assert task.priority == TaskPriority.HIGH
    assert task.project == task_data["project"]
    assert task.tags == task_data["tags"]
    assert task.annotations == task_data["annotations"]
    assert len(task.depends) == 1
    assert task.recur == "weekly"
    assert task.udas == {
            "uda.custom": "mycustomvalue",
            'uda.custom2': 'mycustomvalue2'
    }

def test_taskwarrior_init(taskwarrior_config: str) -> None:
    """Test TaskWarrior initialization."""
    api = TaskWarrior(taskrc_path=taskwarrior_config)
    assert api.taskrc_path == taskwarrior_config
    assert api.config_overrides["confirmation"] in ["no", "off", "0"]

def test_task_add(api: TaskWarrior, sample_task: Task) -> None:
    """Test adding a task."""
    added_task = api.task_add(sample_task)
    assert added_task.uuid == sample_task.uuid
    assert added_task.description == sample_task.description
    # Verify task exists in Taskwarrior
    tasks = api.load_tasks()
    assert any(t.uuid == sample_task.uuid for t in tasks["pending"])

def test_task_update(api: TaskWarrior, sample_task: Task) -> None:
    """Test updating a task."""
    added_task = api.task_add(sample_task)
    added_task.project = "UpdatedProject"
    updated_task = api.task_update(added_task)
    assert updated_task.project == "UpdatedProject"
    assert updated_task.modified is not None
    # Verify update in Taskwarrior
    tasks = api.load_tasks()
    updated = next((t for t in tasks["pending"] if t.uuid == added_task.uuid), None)
    assert updated is not None
    assert updated.project == "UpdatedProject"

def test_task_delete(api: TaskWarrior, sample_task: Task) -> None:
    """Test deleting a task."""
    added_task = api.task_add(sample_task)
    api.task_delete(added_task.uuid)
    tasks = api.load_tasks()
    assert any(t.uuid == added_task.uuid for t in tasks["deleted"])
    assert not any(t.uuid == added_task.uuid for t in tasks["pending"])

def test_task_done(api: TaskWarrior, sample_task: Task) -> None:
    """Test marking a task as done."""
    added_task = api.task_add(sample_task)
    api.task_done(added_task.uuid)
    tasks = api.load_tasks()
    assert any(t.uuid == added_task.uuid for t in tasks["completed"])
    assert not any(t.uuid == added_task.uuid for t in tasks["pending"])

def test_task_start_stop(api: TaskWarrior, sample_task: Task) -> None:
    """Test starting and stopping a task."""
    added_task = api.task_add(sample_task)
    api.task_start(added_task.uuid)
    tasks = api.load_tasks()
    started_task = next((t for t in tasks["pending"] if t.uuid == added_task.uuid), None)
    assert started_task is not None
    assert started_task.start is not None
    api.task_stop(added_task.uuid)
    tasks = api.load_tasks()
    stopped_task = next((t for t in tasks["pending"] if t.uuid == added_task.uuid), None)
    assert stopped_task is not None
    assert stopped_task.start is None

def test_task_annotate(api: TaskWarrior, sample_task: Task) -> None:
    """Test annotating a task."""
    added_task = api.task_add(sample_task)
    annotation = "Test note"
    api.task_annotate(added_task.uuid, annotation)
    tasks = api.load_tasks()
    annotated_task = next((t for t in tasks["pending"] if t.uuid == added_task.uuid), None)
    assert annotated_task is not None
    assert any(a["description"] == annotation for a in annotated_task.annotations)

def test_filter_tasks(api: TaskWarrior, sample_task: Task) -> None:
    """Test filtering tasks."""
    api.task_add(sample_task)
    filtered_tasks = api.filter_tasks(status="pending", project="Test")
    assert len(filtered_tasks) >= 1
    assert any(t.uuid == sample_task.uuid for t in filtered_tasks)

def test_add_recurring_task(api: TaskWarrior, sample_task: Task) -> None:
    """Test adding a recurring task."""
    until = datetime.now() + timedelta(days=30)
    recurring_task = api.add_recurring_task(sample_task, recur="weekly", until=until)
    assert recurring_task.recur == "weekly"
    assert recurring_task.status == TaskStatus.RECURRING
    assert recurring_task.until is not None
    tasks = api.load_tasks()
    assert any(t.uuid == recurring_task.uuid for t in tasks["recurring"])

def test_context_management(api: TaskWarrior, sample_task: Task) -> None:
    """Test setting, applying, and removing context."""
    api.task_add(sample_task)
    api.set_context("test", "project:Test")
    api.apply_context("test")
    filtered_tasks = api.filter_tasks(status="pending")
    assert all(t.project == "Test" for t in filtered_tasks)
    api.remove_context()
    # After removing context, all pending tasks should be visible
    all_tasks = api.filter_tasks(status="pending")
    assert len(all_tasks) >= len(filtered_tasks)

def test_get_task(api: TaskWarrior, sample_task: Task) -> None:
    """Test retrieving a task by UUID."""
    added_task = api.task_add(sample_task)
    retrieved_task = api.get_task(added_task.uuid)
    assert retrieved_task is not None
    assert retrieved_task.uuid == added_task.uuid
    assert retrieved_task.description == added_task.description
    assert api.get_task(uuid4()) is None  # Non-existent UUID

def test_run_task_command_failure(api: TaskWarrior) -> None:
    """Test handling of Taskwarrior command failure."""
    with pytest.raises(RuntimeError, match="Taskwarrior command failed"):
        api._run_task_command(["invalid_command"])
