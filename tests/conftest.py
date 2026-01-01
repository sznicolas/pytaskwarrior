import pytest
from pathlib import Path
import os
import subprocess

from src.taskwarrior import TaskWarrior, TaskInputDTO as TaskInternal, Priority


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
def sample_task() -> TaskInternal:
    """Create a sample Task object."""
    return TaskInternal(
        description="Test Task",
        priority=Priority.HIGH,
        project="Test",
        tags=["test", "urgent"]
    )
