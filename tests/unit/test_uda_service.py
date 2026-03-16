from unittest.mock import MagicMock, mock_open, patch

from src.taskwarrior.dto.uda_dto import UdaConfig, UdaType
from src.taskwarrior.services.uda_service import UdaService


def test_uda_service_uses_own_registry():
    """Test that each UdaService has its own isolated UdaRegistry instance."""
    import tempfile, os
    from src.taskwarrior.config.config_store import ConfigStore
    tmpdir = tempfile.mkdtemp()
    taskrc = os.path.join(tmpdir, ".taskrc")
    open(taskrc, "w").close()
    mock_config_store = ConfigStore(taskrc)
    service1 = UdaService(adapter=MagicMock(), config_store=mock_config_store)
    service2 = UdaService(adapter=MagicMock(), config_store=mock_config_store)
    assert service1.registry is not service2.registry


def test_uda_service_load_udas_from_taskrc():
    """Test loading UDAs from taskrc file through UdaService."""
    mock_adapter = MagicMock()
    mock_adapter.taskrc_file = "/fake/path"
    # Provide a simple config_store object with _taskrc_path attribute
    class DummyConfig:
        pass
    dummy_config = DummyConfig()
    dummy_config._taskrc_path = "/fake/path"
    service = UdaService(adapter=mock_adapter, config_store=dummy_config)

    taskrc_content = "uda.test.type=string\nuda.test.label=Test Label\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        service.load_udas_from_taskrc()

    assert "test" in service.registry.get_uda_names()
    uda = service.registry.get_uda("test")
    assert uda.type == UdaType.STRING
    assert uda.label == "Test Label"


def test_uda_service_define_uda():
    """Test defining a new UDA through UdaService."""
    mock_adapter = MagicMock()
    service = UdaService(adapter=mock_adapter, config_store=MagicMock())

    uda = UdaConfig(
        name="test_uda",
        type=UdaType.STRING,
        label="Test UDA",
        default="default_value",
    )
    service.define_uda(uda)

    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.type", "string"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.label", "Test UDA"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.default", "default_value"])

    assert "test_uda" in service.registry.get_uda_names()
    loaded_uda = service.registry.get_uda("test_uda")
    assert loaded_uda.type == UdaType.STRING
    assert loaded_uda.label == "Test UDA"


def test_uda_service_update_uda():
    """Test updating an existing UDA through UdaService."""
    mock_adapter = MagicMock()
    service = UdaService(adapter=mock_adapter, config_store=MagicMock())

    service.define_uda(UdaConfig(name="test_uda", type=UdaType.STRING, label="Original Label"))

    updated_uda = UdaConfig(
        name="test_uda", type=UdaType.NUMERIC, label="Updated Label", default="new_default"
    )
    service.update_uda(updated_uda)

    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.type", "numeric"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.label", "Updated Label"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.default", "new_default"])

    loaded_uda = service.registry.get_uda("test_uda")
    assert loaded_uda.type == UdaType.NUMERIC
    assert loaded_uda.label == "Updated Label"
    assert loaded_uda.default == "new_default"


def test_uda_service_delete_uda():
    """Test deleting a UDA through UdaService."""
    mock_adapter = MagicMock()
    service = UdaService(adapter=mock_adapter, config_store=MagicMock())

    uda = UdaConfig(name="test_uda", type=UdaType.STRING, label="Test UDA")
    service.define_uda(uda)
    assert "test_uda" in service.registry.get_uda_names()

    service.delete_uda(uda)

    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.name"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.type"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.label"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.values"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.default"])
    mock_adapter.run_task_command.assert_any_call(["config", "uda.test_uda.coefficient"])

    assert "test_uda" not in service.registry.get_uda_names()


def test_uda_service_integration_with_registry():
    """Test that UdaService properly integrates with UdaRegistry."""
    mock_adapter = MagicMock()
    service = UdaService(adapter=mock_adapter, config_store=MagicMock())

    uda = UdaConfig(name="integration_test", type=UdaType.DATE, label="Integration Test")
    service.define_uda(uda)

    assert "integration_test" in service.registry.get_uda_names()
    retrieved_uda = service.registry.get_uda("integration_test")
    assert retrieved_uda.type == UdaType.DATE
    assert retrieved_uda.label == "Integration Test"
    assert service.registry.is_uda_field("integration_test") is True
    assert service.registry.is_uda_field("nonexistent") is False
