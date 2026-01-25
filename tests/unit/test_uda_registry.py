from unittest.mock import mock_open, patch

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.uda_dto import UdaDTO, UdaType
from src.taskwarrior.exceptions import TaskWarriorError
from src.taskwarrior.registry.uda_registry import UdaRegistry


def test_uda_registry_singleton():
    """Test that UdaRegistry is a singleton."""
    registry1 = UdaRegistry()
    registry2 = UdaRegistry()
    assert registry1 is registry2


def test_load_from_taskrc_success(tmp_path):
    """Test loading UDAs from a valid taskrc file."""
    # Create a mock taskrc file
    taskrc_content = """
uda.test_string.type=string
uda.test_string.label=Test String
uda.priority.type=numeric
uda.priority.coefficient=2.0
"""

    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text(taskrc_content)

    # Load registry
    registry = UdaRegistry()
    registry.load_from_taskrc(str(taskrc_file))

    # Verify loaded UDAs
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

    # After loading, check valid and invalid fields
    taskrc_content = "uda.test.type=string\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc()

    assert registry.is_uda_field("test")
    assert not registry.is_uda_field("nonexistent")


def test_get_uda_type():
    """Test getting UDA type by name."""
    registry = UdaRegistry()

    taskrc_content = "uda.test.type=string\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc()

    assert registry.get_uda("test").type == UdaType.STRING
    assert registry.get_uda("nonexistent") is None


def test_get_uda_names():
    """Test getting all UDA names."""
    UdaRegistry._instance = None
    registry = UdaRegistry()

    taskrc_content = """
uda.first_str.type=string
uda.second_date.type=date
"""
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc()

    expected_names = {"first_str", "second_date"}
    assert registry.get_uda_names() == expected_names


def test_load_from_taskrc_invalid_uda():
    """Test handling of invalid UDA definitions."""
    taskrc_content = """
uda.testtype=invalid_type
uda.valid.type=string
"""

    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        UdaRegistry._instance = None
        registry = UdaRegistry()
        registry.load_from_taskrc()

    # Should load valid UDA but skip invalid one
    assert "valid" in registry.get_uda_names()
    assert "test" not in registry.get_uda_names()


def test_define_update_uda_with_empty_fields(tmp_path):
    """Test defining a UDA with some empty fields."""
    # Create a temporary taskrc file
    taskrc_content = ""
    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text(taskrc_content)

    # Create registry with real adapter
    registry = UdaRegistry()
    registry.adapter = TaskWarriorAdapter(taskrc_file=str(taskrc_file))

    # Create a test UDA with some empty fields
    uda = UdaDTO(
        name="test_uda", type=UdaType.STRING, label="", default="default_value"
    )
    registry.define_update_uda(uda)

    # Verify the UDA was defined by reloading the registry
    registry2 = UdaRegistry()
    registry2.load_from_taskrc(str(taskrc_file))

    # Check that the UDA was loaded
    assert "test_uda" in registry2.get_uda_names()

    # Get the UDA and verify its properties
    loaded_uda = registry2.get_uda("test_uda")
    assert loaded_uda.type == UdaType.STRING
    # Note: Empty label should not be set, but default should be


def test_delete_uda(tmp_path):
    """Test deleting a UDA through the registry with real adapter."""
    # Create a temporary taskrc file
    taskrc_content = "uda.test_uda.type=string\nuda.test_uda.label=Test UDA\n"
    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text(taskrc_content)

    # Create registry with real adapter
    adapter = TaskWarriorAdapter(taskrc_file=str(taskrc_file))
    registry = UdaRegistry(adapter)

    # Verify UDA exists before deletion
    print(" **** ", registry.get_uda_names())
    assert "test_uda" in registry.get_uda_names()

    # Call delete_uda
    print("*** 1: ", registry.get_uda_names())
    registry.delete_uda(registry.get_uda("test_uda"))
    print("*** 2: ", registry.get_uda_names())

    # Verify the UDA was deleted by reloading the registry
    registry3 = UdaRegistry()
    registry3.load_from_taskrc(str(taskrc_file))
    print("*** 3: ", registry3.get_uda_names())
    # Check that the UDA was removed
    assert "test_uda" not in registry3.get_uda_names()
