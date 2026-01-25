from __future__ import annotations

import pytest
from pathlib import Path
import os
import subprocess

from src.taskwarrior import TaskWarrior, TaskInputDTO 
from src.taskwarrior.enums import Priority


@pytest.fixture
def taskwarrior_data(tmp_path: Path) -> str:
    """Set up a temporary Taskwarrior data directory."""
    data_dir = tmp_path / "taskdata"
    data_dir.mkdir()
    os.environ['TASKDATA'] = str(data_dir)
    return str(data_dir)


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
    os.environ['TASKRC'] = str(config_path)
    return str(config_path)


@pytest.fixture
def tw(taskwarrior_config: str, taskwarrior_data: str) -> TaskWarrior:
    """Create a TaskWarrior instance with a temporary config."""
    # Ensure Taskwarrior is installed
    try:
        subprocess.run(["task", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Taskwarrior is not installed or not found in PATH.")
    return TaskWarrior(taskrc_file=taskwarrior_config, data_location=taskwarrior_data)


@pytest.fixture
def sample_task() -> TaskInputDTO:
    """Create a sample Task object."""
    return TaskInputDTO(
        description="Test Task",
        priority=Priority.HIGH,
        project="Test",
        tags=["test", "urgent"]
    )
