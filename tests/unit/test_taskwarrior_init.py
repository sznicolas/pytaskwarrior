from __future__ import annotations

import os
from pathlib import Path

from src.taskwarrior import TaskWarrior


class TestTaskWarriorInit:
    """Test cases for TaskWarrior and TaskWarriorAdapter initialization."""

    def test_taskwarrior_init_with_params(self, taskwarrior_config: str):
        """Test TaskWarrior initialization with custom parameters."""
        tw = TaskWarrior(task_cmd="task", taskrc_file=taskwarrior_config)

        assert "task" in str(tw.adapter.task_cmd)
        assert str(tw.config_store._taskrc_path) == taskwarrior_config
        # No data_location anymore
        # Also verify adapter options are set correctly
        assert isinstance(tw.adapter.cli_options, list)
        # get_info returns correct types
        info = tw.get_info()
        assert isinstance(info["task_cmd"], str)
        assert isinstance(info["taskrc_file"], str)
        assert isinstance(info["options"], list)
        assert isinstance(info["backend_version"], str)
        assert info["taskrc_file"] == str(taskwarrior_config)

    def test_get_info_comprehensive(self, taskwarrior_config: str):
        """Test get_info with comprehensive information retrieval."""
        tw = TaskWarrior(taskrc_file=taskwarrior_config)
        info = tw.get_info()

        assert "task_cmd" in info
        assert "taskrc_file" in info
        assert "options" in info
        assert "backend_version" in info
        assert "backend_type" in info

        # With default TC adapter: task_cmd and options are None
        assert info["task_cmd"] is None
        assert info["options"] is None
        assert isinstance(info["taskrc_file"], str)
        assert info["backend_type"] == "taskchampion"

    def test_get_info_with_custom_params(self, taskwarrior_config: str):
        """Test get_info with custom parameters."""
        tw = TaskWarrior(task_cmd="task", taskrc_file=taskwarrior_config)

        info = tw.get_info()

        assert "task" in info["task_cmd"]
        assert info["taskrc_file"] == str(taskwarrior_config)
        assert isinstance(tw.adapter._cli_options, list)
        assert isinstance(info["task_cmd"], str)
        assert isinstance(info["taskrc_file"], str)
        assert isinstance(info["options"], list)
        assert isinstance(info["backend_version"], str)

    def test_taskwarrior_init_defaults(self):
        """Test TaskWarrior and Adapter initialization with defaults (TaskChampion)."""
        if "TASKRC" in os.environ:
            del os.environ["TASKRC"]
        if "TASKDATA" in os.environ:
            del os.environ["TASKDATA"]

        tw = TaskWarrior()
        from src.taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
        assert isinstance(tw.adapter, TaskChampionAdapter)
        info = tw.get_info()
        assert info["taskrc_file"] is not None and info["taskrc_file"] != ""
        assert info["backend_type"] == "taskchampion"
        # Default should expand to real home directory
        expected_taskrc = Path.home() / ".taskrc"
        assert Path(os.path.expandvars(info["taskrc_file"])).expanduser() == expected_taskrc
        # No CLI: task_cmd and options are None
        assert info["task_cmd"] is None
        assert info["options"] is None

    def test_get_projects(self, taskwarrior_config: str):
        """Test getting projects from TaskWarrior."""
        tw = TaskWarrior(taskrc_file=taskwarrior_config)

        # This test verifies the method exists and returns a list
        projects = tw.get_projects()
        assert isinstance(projects, list)

        # Verify all items are strings
        for project in projects:
            assert isinstance(project, str)
            assert project.strip() != ""

    def test_get_tags(self, taskwarrior_config: str):
        """Test getting tags from TaskWarrior."""
        tw = TaskWarrior(taskrc_file=taskwarrior_config)

        tags = tw.get_tags()
        assert isinstance(tags, list)
        assert "TODAY" not in tags
        assert "READY" not in tags

        tags_with_virtual = tw.get_tags(include_virtual_tags=True)
        assert "TODAY" in tags_with_virtual
        assert "READY" in tags_with_virtual
        assert tw.get_context_tags() == []
