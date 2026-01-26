from unittest.mock import mock_open, patch, MagicMock

import pytest

from src.taskwarrior.registry.uda_registry import UdaRegistry
from src.taskwarrior.services.uda_service import UdaService
from src.taskwarrior.dto.uda_dto import UdaDTO, UdaType


def test_uda_service_singleton():
    """Test that UdaRegistry is properly integrated with UdaService."""
    # Reset singleton instance
    UdaRegistry._instance = None
    
    # Create service instances
    service1 = UdaService(adapter=MagicMock())
    service2 = UdaService(adapter=MagicMock())
    
    # Both should use the same registry instance
    assert service1.registry is service2.registry


def test_uda_service_load_udas_from_taskrc():
    """Test loading UDAs from taskrc file through UdaService."""
    # Reset singleton instance
    UdaRegistry._instance = None
    
    # Create mock adapter
    mock_adapter = MagicMock()
    
    # Create service
    service = UdaService(adapter=mock_adapter)
    
    # Mock the taskrc file path
    mock_adapter.taskrc_file = "/fake/path"
    
    # Test loading with valid content
    taskrc_content = "uda.test.type=string\nuda.test.label=Test Label\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        service.load_udas_from_taskrc()
    
    # Verify registry was updated
    registry = UdaRegistry()
    assert "test" in registry.get_uda_names()
    uda = registry.get_uda("test")
    assert uda.type == UdaType.STRING
    assert uda.label == "Test Label"


def test_uda_service_define_uda():
    """Test defining a new UDA through UdaService."""
    # Reset singleton instance
    UdaRegistry._instance = None
    
    # Create mock adapter
    mock_adapter = MagicMock()
    
    # Create service
    service = UdaService(adapter=mock_adapter)
    
    # Create test UDA
    uda = UdaDTO(
        name="test_uda", 
        type=UdaType.STRING, 
        label="Test UDA",
        default="default_value"
    )
    
    # Call define_uda
    service.define_uda(uda)
    
    # Verify adapter was called with correct commands
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.type", "string"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.label", "Test UDA"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.default", "default_value"
    ])
    
    # Verify UDA was stored in registry
    registry = UdaRegistry()
    assert "test_uda" in registry.get_uda_names()
    loaded_uda = registry.get_uda("test_uda")
    assert loaded_uda.type == UdaType.STRING
    assert loaded_uda.label == "Test UDA"


def test_uda_service_update_uda():
    """Test updating an existing UDA through UdaService."""
    # Reset singleton instance
    UdaRegistry._instance = None
    
    # Create mock adapter
    mock_adapter = MagicMock()
    
    # Create service
    service = UdaService(adapter=mock_adapter)
    
    # First define a UDA
    initial_uda = UdaDTO(
        name="test_uda", 
        type=UdaType.STRING, 
        label="Original Label"
    )
    service.define_uda(initial_uda)
    
    # Now update it
    updated_uda = UdaDTO(
        name="test_uda", 
        type=UdaType.NUMERIC, 
        label="Updated Label",
        default="new_default"
    )
    
    # Call update_uda
    service.update_uda(updated_uda)
    
    # Verify adapter was called with correct commands for update
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.type", "numeric"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.label", "Updated Label"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.default", "new_default"
    ])
    
    # Verify UDA was updated in registry
    registry = UdaRegistry()
    loaded_uda = registry.get_uda("test_uda")
    assert loaded_uda.type == UdaType.NUMERIC
    assert loaded_uda.label == "Updated Label"
    assert loaded_uda.default == "new_default"


def test_uda_service_delete_uda():
    """Test deleting a UDA through UdaService."""
    # Reset singleton instance
    UdaRegistry._instance = None
    
    # Create mock adapter
    mock_adapter = MagicMock()
    
    # Create service
    service = UdaService(adapter=mock_adapter)
    
    # First define a UDA
    uda = UdaDTO(
        name="test_uda", 
        type=UdaType.STRING, 
        label="Test UDA"
    )
    service.define_uda(uda)
    
    # Verify UDA exists
    registry = UdaRegistry()
    assert "test_uda" in registry.get_uda_names()
    
    # Call delete_uda
    service.delete_uda(uda)
    
    # Verify adapter was called to clear config entries
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.name"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.type"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.label"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.values"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.default"
    ])
    mock_adapter.run_task_command.assert_any_call([
        "config", "uda.test_uda.coefficient"
    ])
    
    # Verify UDA was removed from registry
    assert "test_uda" not in registry.get_uda_names()


def test_uda_service_integration_with_registry():
    """Test that UdaService properly integrates with UdaRegistry."""
    # Reset singleton instance
    UdaRegistry._instance = None
    
    # Create mock adapter
    mock_adapter = MagicMock()
    
    # Create service
    service = UdaService(adapter=mock_adapter)
    
    # Define a UDA through service
    uda = UdaDTO(
        name="integration_test", 
        type=UdaType.DATE, 
        label="Integration Test"
    )
    service.define_uda(uda)
    
    # Verify registry has the UDA
    registry = UdaRegistry()
    assert "integration_test" in registry.get_uda_names()
    
    # Verify we can query it
    retrieved_uda = registry.get_uda("integration_test")
    assert retrieved_uda.type == UdaType.DATE
    assert retrieved_uda.label == "Integration Test"
    
    # Verify it's recognized as a UDA field
    assert registry.is_uda_field("integration_test") is True
    assert registry.is_uda_field("nonexistent") is False
