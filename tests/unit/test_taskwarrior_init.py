from __future__ import annotations
import os
from pathlib import Path

import pytest
from uuid import uuid4

from src.taskwarrior import TaskWarrior, TaskInputDTO, TaskOutputDTO
from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.enums import Priority, TaskStatus, RecurrencePeriod
from src.taskwarrior.exceptions import TaskNotFound, TaskValidationError, TaskWarriorError


class TestTaskWarriorInit:
    """Test cases for TaskWarrior initialization."""

    def test_taskwarrior_init_with_params(self, taskwarrior_config: str):
        """Test TaskWarrior initialization with parameters."""
        tw = TaskWarrior(
            task_cmd="task",
            taskrc_file=taskwarrior_config,
            data_location="/tmp/test"
        )

        assert "task" in str(tw.adapter.task_cmd)
        assert str(tw.adapter.taskrc_file) == taskwarrior_config
        assert str(tw.adapter.data_location) == "/tmp/test"

    def test_taskwarrior_init_defaults(self):
        """Test TaskWarrior initialization with defaults."""
        if "TASKRC" in os.environ:
            del os.environ["TASKRC"]
        if "TASKDATA" in os.environ:
            del os.environ["TASKDATA"]
        tw = TaskWarrior()
        assert "task" in str(tw.adapter.task_cmd)
        assert tw.adapter.taskrc_file is not None
        assert isinstance(tw.adapter.taskrc_file, Path)
        assert  str(tw.adapter.taskrc_file) == "$HOME/.taskrc"
        assert tw.adapter.data_location is None

    def test_taskwarrior_adapter_init_with_params(self, taskwarrior_config: str):
        """Test TaskWarriorAdapter initialization with parameters."""
        adapter = TaskWarriorAdapter(
            task_cmd="task",
            taskrc_file=taskwarrior_config,
            data_location="/tmp/test"
        )

        assert "task" in str(adapter.task_cmd)
        assert str(adapter.taskrc_file) == taskwarrior_config
        assert str(adapter.data_location) == "/tmp/test"
        assert "rc.data.location=/tmp/test" in adapter._options

    def test_taskwarrior_adapter_init_defaults(self):
        """Test TaskWarriorAdapter initialization with defaults."""
        adapter = TaskWarriorAdapter()

        assert "task" in str(adapter.task_cmd)
        assert  str(adapter.taskrc_file) == "$HOME/.taskrc"
        assert adapter.data_location is None
        assert "rc.confirmation=off" in adapter._options
