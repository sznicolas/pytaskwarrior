from unittest.mock import mock_open, patch

from src.taskwarrior.registry.uda_registry import UdaRegistry

from src.taskwarrior.dto.uda_dto import UdaType

def test_uda_registry_service_integration():
    """Test integration between registry and adapter for UDA operations."""
    # Test that registry properly handles adapter interactions
    UdaRegistry._instance = None
    registry = UdaRegistry()

    # Test that registry can be initialized without adapter
    assert registry._udas == {}

    # Test singleton behavior
    registry2 = UdaRegistry()
    assert registry is registry2

    # Test empty state
    assert registry.get_uda_names() == set()
    assert registry.is_uda_field("any_field") is False
    assert registry.get_uda("nonexistent") is None


def test_uda_registry_load_and_query():
    """Test loading UDAs and querying them."""
    UdaRegistry._instance = None
    registry = UdaRegistry()

    # Test loading with empty content
    taskrc_content = ""
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc("/fake/path")

    assert registry.get_uda_names() == set()

    # Test loading with valid UDA
    taskrc_content = "uda.test.type=string\nuda.test.label=Test Label\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        registry.load_from_taskrc("/fake/path")

    assert "test" in registry.get_uda_names()
    uda = registry.get_uda("test")
    assert uda is not None
    assert uda.type == UdaType.STRING
    assert uda.label == "Test Label"

    # Test is_uda_field
    assert registry.is_uda_field("test") is True
    assert registry.is_uda_field("nonexistent") is False
