from __future__ import annotations

import os
from pathlib import Path

from src.taskwarrior import TaskWarrior


class TestTaskWarriorInit:
    """Test cases for TaskWarrior and TaskWarriorAdapter initialization."""

    def test_taskwarrior_init_with_params(self, taskwarrior_config: str):
        """Test TaskWarrior initialization with custom parameters."""
        tw = TaskWarrior(
            task_cmd="task",
            taskrc_file=taskwarrior_config,
            data_location="/tmp/test"
        )

        assert "task" in str(tw.adapter.task_cmd)
        assert str(tw.adapter.taskrc_file) == taskwarrior_config
        assert str(tw.adapter.data_location) == "/tmp/test"
        # Also verify adapter options are set correctly
        assert "rc.data.location=/tmp/test" in tw.adapter._options

    def test_taskwarrior_init_defaults(self):
        """Test TaskWarrior and Adapter initialization with defaults."""
        if "TASKRC" in os.environ:
            del os.environ["TASKRC"]
        if "TASKDATA" in os.environ:
            del os.environ["TASKDATA"]

        tw = TaskWarrior()
        assert "task" in str(tw.adapter.task_cmd)
        assert tw.adapter.taskrc_file is not None
        assert isinstance(tw.adapter.taskrc_file, Path)
        # Default should expand to real home directory
        expected_taskrc = Path.home() / ".taskrc"
        assert tw.adapter.taskrc_file == expected_taskrc
        assert tw.adapter.data_location is None
        assert "rc.confirmation=off" in tw.adapter._options
