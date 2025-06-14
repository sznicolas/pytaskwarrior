import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json
import subprocess
import os
from pathlib import Path

from taskwarrior import TaskWarrior, Task, TaskStatus, TaskPriority  # Adjust import based on your module name

@pytest.fixture
def taskwarrior_config(tmp_path: Path) -> str:
    """Create a temporary taskrc file for testing."""
    config_path = tmp_path / ".taskrc"
    config_content = """
data.location={}/tasks
confirmation=no
json.array=TRUE
verbose=nothing
""".format(tmp_path)
    config_path.write_text(config_content)
    return str(config_path)

@pytest.fixture
def api(taskwarrior_config: str, mocker) -> TaskWarrior:
    """Create a TaskWarrior instance with a temporary config."""
    # Mock subprocess.run to simulate Taskwarrior version check
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "--version"], returncode=0, stdout="2.6.0", stderr=""
    ))
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
        "uda.custom": "value"
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
    assert task.udas == {"uda.custom": "value"}

def test_taskwarrior_init(taskwarrior_config: str, mocker) -> None:
    """Test TaskWarrior initialization."""
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "--version"], returncode=0, stdout="2.6.0", stderr=""
    ))
    api = TaskWarrior(taskrc_path=taskwarrior_config)
    assert api.taskrc_path == taskwarrior_config
    assert api.config_overrides["confirmation"] in ["off", "no", "0"]

def test_taskwarrior_init_failure(mocker) -> None:
    """Test TaskWarrior initialization failure when Taskwarrior is not installed."""
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["task", "--version"], stderr="task not found"))
    with pytest.raises(RuntimeError, match="Taskwarrior is not installed or not found in PATH."):
        TaskWarrior()

def test_task_add(api: TaskWarrior, sample_task: Task, mocker) -> None:
    """Test adding a task."""
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "import"], returncode=0, stdout="", stderr=""
    ))
    mocker.patch.object(api, "load_tasks", return_value={"pending": [sample_task]})
    added_task = api.task_add(sample_task)
    assert added_task.uuid == sample_task.uuid
    assert added_task.description == sample_task.description

#def test_task_update(api: TaskWarrior, sample_task: Task, mocker) -> None:
#    """Test updating a task."""
#    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
#        args=["task", "import"], returncode=0, stdout="", stderr=""
#    ))
#    updated_task = api.task_update(sample_task)
#    assert updated_task.modified is not None
#    assert updated_task.description == sample_task.description

def test_task_delete(api: TaskWarrior, mocker) -> None:
    """Test deleting a task."""
    uuid = uuid4()
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=[f"task {uuid} delete"], returncode=0, stdout="", stderr=""
    ))
    api.task_delete(uuid)  # Should not raise an error

def test_task_done(api: TaskWarrior, mocker) -> None:
    """Test marking a task as done."""
    uuid = uuid4()
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=[f"task {uuid} done"], returncode=0, stdout="", stderr=""
    ))
    api.task_done(uuid)  # Should not raise an error

def test_task_start_stop(api: TaskWarrior, mocker) -> None:
    """Test starting and stopping a task."""
    uuid = uuid4()
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=[f"task {uuid} start"], returncode=0, stdout="", stderr=""
    ))
    api.task_start(uuid)  # Should not raise an error
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=[f"task {uuid} stop"], returncode=0, stdout="", stderr=""
    ))
    api.task_stop(uuid)  # Should not raise an error

def test_task_annotate(api: TaskWarrior, mocker) -> None:
    """Test annotating a task."""
    uuid = uuid4()
    annotation = "Test note"
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=[f"task {uuid} annotate {annotation}"], returncode=0, stdout="", stderr=""
    ))
    api.task_annotate(uuid, annotation)  # Should not raise an error

def test_filter_tasks(api: TaskWarrior, sample_task: Task, mocker) -> None:
    """Test filtering tasks."""
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "status:pending", "project:Test", "export"], returncode=0,
        stdout=json.dumps([sample_task.to_dict()]), stderr=""
    ))
    filtered_tasks = api.filter_tasks(status="pending", project="Test")
    assert len(filtered_tasks) == 1
    assert filtered_tasks[0].description == sample_task.description

def test_add_recurring_task(api: TaskWarrior, sample_task: Task, mocker) -> None:
    """Test adding a recurring task."""
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "import"], returncode=0, stdout="", stderr=""
    ))
    mocker.patch.object(api, "load_tasks", return_value={"recurring": [sample_task]})
    recurring_task = api.add_recurring_task(sample_task, recur="weekly", until=datetime.now() + timedelta(days=30))
    assert recurring_task.recur == "weekly"
    assert recurring_task.status == TaskStatus.RECURRING
    assert recurring_task.until is not None

def test_context_management(api: TaskWarrior, mocker) -> None:
    """Test setting, applying, and removing context."""
    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "context", "define", "work", "project:Work"], returncode=0, stdout="", stderr=""
    ))
    api.set_context("work", "project:Work")  # Should not raise an error

    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "context", "work"], returncode=0, stdout="", stderr=""
    ))
    api.apply_context("work")  # Should not raise an error

    mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess(
        args=["task", "context", "none"], returncode=0, stdout="", stderr=""
    ))
    api.remove_context()  # Should not raise an error

def test_get_task(api: TaskWarrior, sample_task: Task, mocker) -> None:
    """Test retrieving a task by UUID."""
    mocker.patch.object(api, "load_tasks", return_value={"pending": [sample_task]})
    retrieved_task = api.get_task(sample_task.uuid)
    assert retrieved_task is not None
    assert retrieved_task.uuid == sample_task.uuid
    assert api.get_task(uuid4()) is None  # Non-existent UUID

def test_run_task_command_failure(api: TaskWarrior, mocker) -> None:
    """Test handling of Taskwarrior command failure."""
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(
        1, ["task", "invalid"], stderr="Invalid command"
    ))
    with pytest.raises(RuntimeError, match="Taskwarrior command failed: Invalid command"):
        api._run_task_command(["invalid"])
