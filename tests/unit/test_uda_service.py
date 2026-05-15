from unittest.mock import MagicMock, mock_open, patch

from src.taskwarrior.dto.uda_dto import UdaConfig, UdaType
from src.taskwarrior.services.uda_service import UdaService


def test_uda_service_uses_own_registry():
    """Test that each UdaService has its own isolated UdaRegistry instance."""
    import os
    import tempfile

    from src.taskwarrior.config.config_store import ConfigStore

    tmpdir = tempfile.mkdtemp()
    taskrc = os.path.join(tmpdir, ".taskrc")
    open(taskrc, "w").close()
    mock_config_store = ConfigStore(taskrc)
    service1 = UdaService(config_store=mock_config_store)
    service2 = UdaService(config_store=mock_config_store)
    assert service1.registry is not service2.registry


def test_uda_service_load_udas_from_taskrc():
    """Test loading UDAs from taskrc file through UdaService (now via ConfigStore.get_udas)."""
    class DummyConfig:
        def __init__(self, path: str):
            self._taskrc_path = path

        def get_udas(self):
            with open(self._taskrc_path, encoding="utf-8") as f:
                content = f.read()
            cfg = {
                line.split("=", 1)[0].strip(): line.split("=", 1)[1].strip()
                for line in content.splitlines()
                if "=" in line
            }
            from src.taskwarrior.config.uda_parser import parse_udas_from_mapping
            return parse_udas_from_mapping(cfg)

    dummy_config = DummyConfig("/fake/path")
    service = UdaService(config_store=dummy_config)

    taskrc_content = "uda.test.type=string\nuda.test.label=Test Label\n"
    with patch("builtins.open", mock_open(read_data=taskrc_content)):
        service.load_udas_from_store()

    assert "test" in service.registry.get_uda_names()
    uda = service.registry.get_uda("test")
    assert uda.uda_type == UdaType.STRING
    assert uda.label == "Test Label"


def test_uda_service_define_uda():
    """Test defining a new UDA writes to ConfigStore."""
    mock_config_store = MagicMock()
    service = UdaService(config_store=mock_config_store)

    uda = UdaConfig(
        name="test_uda",
        uda_type=UdaType.STRING,
        label="Test UDA",
        default="default_value",
    )
    service.define_uda(uda)

    mock_config_store.set_value.assert_any_call("uda.test_uda.type", "string")
    mock_config_store.set_value.assert_any_call("uda.test_uda.label", "Test UDA")
    mock_config_store.set_value.assert_any_call("uda.test_uda.default", "default_value")

    assert "test_uda" in service.registry.get_uda_names()
    loaded_uda = service.registry.get_uda("test_uda")
    assert loaded_uda.uda_type == UdaType.STRING
    assert loaded_uda.label == "Test UDA"


def test_uda_service_update_uda():
    """Test updating an existing UDA through UdaService (via define_uda)."""
    mock_config_store = MagicMock()
    service = UdaService(config_store=mock_config_store)

    service.define_uda(UdaConfig(name="test_uda", uda_type=UdaType.STRING, label="Original Label"))

    updated_uda = UdaConfig(
        name="test_uda", uda_type=UdaType.NUMERIC, label="Updated Label", default="new_default"
    )
    service.define_uda(updated_uda)

    mock_config_store.set_value.assert_any_call("uda.test_uda.type", "numeric")
    mock_config_store.set_value.assert_any_call("uda.test_uda.label", "Updated Label")
    mock_config_store.set_value.assert_any_call("uda.test_uda.default", "new_default")

    loaded_uda = service.registry.get_uda("test_uda")
    assert loaded_uda.uda_type == UdaType.NUMERIC
    assert loaded_uda.label == "Updated Label"
    assert loaded_uda.default == "new_default"


def test_uda_service_delete_uda():
    """Test deleting a UDA calls delete_value on ConfigStore."""
    mock_config_store = MagicMock()
    service = UdaService(config_store=mock_config_store)

    uda = UdaConfig(name="test_uda", uda_type=UdaType.STRING, label="Test UDA")
    service.define_uda(uda)
    assert "test_uda" in service.registry.get_uda_names()

    service.delete_uda(uda)

    mock_config_store.delete_value.assert_any_call("uda.test_uda.type")
    mock_config_store.delete_value.assert_any_call("uda.test_uda.label")

    assert "test_uda" not in service.registry.get_uda_names()


def test_uda_service_integration_with_registry():
    """Test that UdaService properly integrates with UdaRegistry."""
    mock_config_store = MagicMock()
    service = UdaService(config_store=mock_config_store)

    uda = UdaConfig(name="integration_test", uda_type=UdaType.DATE, label="Integration Test")
    service.define_uda(uda)

    assert "integration_test" in service.registry.get_uda_names()
    retrieved_uda = service.registry.get_uda("integration_test")
    assert retrieved_uda.uda_type == UdaType.DATE
    assert retrieved_uda.label == "Integration Test"
    assert service.registry.is_uda_field("integration_test") is True
    assert service.registry.is_uda_field("nonexistent") is False
