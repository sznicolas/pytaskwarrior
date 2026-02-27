from unittest.mock import mock_open, patch

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.uda_dto import UdaConfig, UdaType
from src.taskwarrior.exceptions import TaskWarriorError
from src.taskwarrior.registry.uda_registry import UdaRegistry


def test_uda_registry_independent_instances():
    """Test that each UdaRegistry instance has its own independent state."""
    registry1 = UdaRegistry()
    registry2 = UdaRegistry()
    assert registry1 is not registry2
    assert registry1._udas is not registry2._udas


def test_load_from_taskrc_success(tmp_path):
    """Test loading UDAs from a valid taskrc file."""
    taskrc_content = """
uda.test_string.type=string
uda.test_string.label=Test String
uda.priority.type=numeric
uda.priority.coefficient=2.0
"""

    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text(taskrc_content)

    registry = UdaRegistry()
    registry.load_from_taskrc(str(taskrc_file))

    assert "test_string" in registry.get_uda_names()
    assert "priority" in registry.get_uda_names()

    test_uda = registry.get_uda("test_string")
    assert test_uda.type == UdaType.STRING
    assert test_uda.label == "Test String"

    priority_uda = registry.get_uda("priority")
    assert priority_uda.type == UdaType.NUMERIC
    assert priority_uda.coefficient == 2.0


def test_load_from_taskrc_file_not_found():
    """Test handling of missing taskrc file."""
    registry = UdaRegistry()
    with pytest.raises(TaskWarriorError) as exc_info:
        registry.load_from_taskrc("/non/existent/file")
    assert "Taskrc file not found" in str(exc_info.value)


def test_is_uda_field():
    """Test checking if a field name is a defined UDA."""
    registry = UdaRegistry()

    # Initially empty
    assert not registry.is_uda_field("test")

    taskrc_content = "uda.test.type=string\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc("/fake/path")

    assert registry.is_uda_field("test")
    assert not registry.is_uda_field("nonexistent")


def test_get_uda_type():
    """Test getting UDA type by name."""
    registry = UdaRegistry()

    taskrc_content = "uda.test.type=string\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc("/fake/path")

    assert registry.get_uda("test").type == UdaType.STRING
    assert registry.get_uda("nonexistent") is None


def test_get_uda_names():
    """Test getting all UDA names."""
    registry = UdaRegistry()

    taskrc_content = """
uda.first_str.type=string
uda.second_date.type=date
"""
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc("/fake/path")

    expected_names = {"first_str", "second_date"}
    assert registry.get_uda_names() == expected_names


def test_load_from_taskrc_invalid_uda():
    """Test handling of invalid UDA definitions."""
    taskrc_content = """
uda.testtype=invalid_type
uda.valid.type=string
"""

    registry = UdaRegistry()
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc("/fake/path")

    assert "valid" in registry.get_uda_names()
    assert "test" not in registry.get_uda_names()


def test_define_update_uda_with_empty_fields(tmp_path):
    """Test defining a UDA with some empty fields."""
    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text("")

    registry = UdaRegistry()
    adapter = TaskWarriorAdapter(taskrc_file=str(taskrc_file))

    uda = UdaConfig(
        name="test_uda", type=UdaType.STRING, label="", default="default_value"
    )
    registry.define_update_uda(uda, adapter)

    registry2 = UdaRegistry()
    registry2.load_from_taskrc(str(taskrc_file))

    assert "test_uda" in registry2.get_uda_names()
    loaded_uda = registry2.get_uda("test_uda")
    assert loaded_uda.type == UdaType.STRING


def test_delete_uda(tmp_path):
    """Test deleting a UDA through the registry with real adapter."""
    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text("uda.test_uda.type=string\nuda.test_uda.label=Test UDA\n")

    adapter = TaskWarriorAdapter(taskrc_file=str(taskrc_file))
    registry = UdaRegistry()
    registry.load_from_taskrc(str(taskrc_file))

    assert "test_uda" in registry.get_uda_names()

    registry.delete_uda(registry.get_uda("test_uda"), adapter)

    registry2 = UdaRegistry()
    registry2.load_from_taskrc(str(taskrc_file))
    assert "test_uda" not in registry2.get_uda_names()
