from __future__ import annotations

from src.taskwarrior import TaskInputDTO, TaskWarrior
from src.taskwarrior.dto.uda_dto import UdaConfig, UdaType


class TestTaskWarriorUtils:
    """Test cases for TaskWarrior utility functions."""

    def test_task_output_to_input_conversion(self, tw: TaskWarrior):
        """Test task_output_to_input conversion function."""
        from src.taskwarrior.utils.dto_converter import task_output_to_input

        # Add a task
        task = TaskInputDTO(description="Test task")
        added_task = tw.add_task(task)

        # Convert to input DTO
        input_task = task_output_to_input(added_task)

        assert input_task.description == "Test task"
        # UUID should not be present in the input DTO
        assert not hasattr(input_task, "uuid")

    def test_get_info_success(self, tw: TaskWarrior):
        """Test get_info method."""
        result = tw.get_info()

        assert "version" in result
        assert "task_cmd" in result


class TestTaskWarriorUdaMethods:
    """Test cases for TaskWarrior UDA-related methods."""

    def test_reload_udas(self, tw: TaskWarrior):
        """Test reload_udas method."""
        # Should not raise
        tw.reload_udas()

    def test_get_uda_names_empty(self, tw: TaskWarrior):
        """Test get_uda_names returns empty set when no UDAs defined."""
        names = tw.get_uda_names()
        assert isinstance(names, set)

    def test_get_uda_config_not_found(self, tw: TaskWarrior):
        """Test get_uda_config returns None for undefined UDA."""
        config = tw.get_uda_config("nonexistent_uda")
        assert config is None

    def test_define_and_get_uda(self, tw: TaskWarrior):
        """Test defining a UDA and retrieving its config."""
        # Define a UDA
        uda = UdaConfig(
            name="test_severity",
            type=UdaType.STRING,
            label="Severity Level",
            values=["low", "medium", "high"],
        )
        tw.uda_service.define_uda(uda)

        # Reload and verify
        tw.reload_udas()
        names = tw.get_uda_names()
        assert "test_severity" in names

        config = tw.get_uda_config("test_severity")
        assert config is not None
        assert config.type == UdaType.STRING
        assert config.label == "Severity Level"

        # Cleanup
        tw.uda_service.delete_uda(uda)

    def test_uda_auto_loaded_on_init(self, taskwarrior_config: str):
        """Test that UDAs are auto-loaded when TaskWarrior is initialized."""
        # Create a taskrc with UDA definitions
        with open(taskwarrior_config, "a") as f:
            f.write("\nuda.auto_test.type=string\n")
            f.write("uda.auto_test.label=Auto Test\n")

        # Create new TaskWarrior instance - should auto-load
        tw = TaskWarrior(taskrc_file=taskwarrior_config)

        names = tw.get_uda_names()
        assert "auto_test" in names

        config = tw.get_uda_config("auto_test")
        assert config is not None
        assert config.type == UdaType.STRING
        assert config.label == "Auto Test"
