from __future__ import annotations

import pytest
from uuid import uuid4

from src.taskwarrior import TaskWarrior, TaskInputDTO, TaskOutputDTO
from src.taskwarrior.enums import Priority, TaskStatus, RecurrencePeriod
from src.taskwarrior.exceptions import TaskNotFound, TaskValidationError, TaskWarriorError


class TestTaskWarriorInit:
    """Test cases for TaskWarrior initialization."""

    def test_taskwarrior_init_with_params(self, taskwarrior_config: str):
        """Test TaskWarrior initialization with parameters."""
        tw = TaskWarrior(
            task_cmd="task",
            taskrc_path=taskwarrior_config,
            data_location="/tmp/test"
        )
        
        assert tw.adapter.task_cmd == "task"
        assert tw.adapter.taskrc_path == taskwarrior_config
        assert tw.adapter.data_location == "/tmp/test"

    def test_taskwarrior_init_defaults(self):
        """Test TaskWarrior initialization with defaults."""
        tw = TaskWarrior()
        
        assert tw.adapter.task_cmd == "task"
        assert tw.adapter.taskrc_path is None
        assert tw.adapter.data_location is None

    def test_taskwarrior_adapter_init_with_params(self, taskwarrior_config: str):
        """Test TaskWarriorAdapter initialization with parameters."""
        adapter = TaskWarriorAdapter(
            task_cmd="task",
            taskrc_path=taskwarrior_config,
            data_location="/tmp/test"
        )
        
        assert adapter.task_cmd == "task"
        assert adapter.taskrc_path == taskwarrior_config
        assert adapter.data_location == "/tmp/test"
        assert "rc.data.location=/tmp/test" in adapter._options

    def test_taskwarrior_adapter_init_defaults(self):
        """Test TaskWarriorAdapter initialization with defaults."""
        adapter = TaskWarriorAdapter()
        
        assert adapter.task_cmd == "task"
        assert adapter.taskrc_path is None
        assert adapter.data_location is None
        assert "rc.confirmation=off" in adapter._options
