from src.taskwarrior.dto.uda_dto import UdaConfig, UdaType
from src.taskwarrior.registry.uda_registry import UdaRegistry


def _config_from_string(s: str) -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in s.splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        cfg[key.strip()] = val.strip()
    return cfg


def test_uda_registry_independent_instances():
    """Test that each UdaRegistry instance has its own independent state."""
    registry1 = UdaRegistry()
    registry2 = UdaRegistry()
    assert registry1 is not registry2
    assert registry1._udas is not registry2._udas


def test_load_from_config_success(tmp_path):
    """Test loading UDAs from a valid taskrc-like content via load_from_config."""
    taskrc_content = """
uda.test_string.type=string
uda.test_string.label=Test String
uda.priority.type=numeric
uda.priority.coefficient=2.0
"""

    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text(taskrc_content)

    registry = UdaRegistry()
    cfg = _config_from_string(taskrc_file.read_text(encoding="utf-8"))
    registry.load_from_config(cfg)

    assert "test_string" in registry.get_uda_names()
    assert "priority" in registry.get_uda_names()

    test_uda = registry.get_uda("test_string")
    assert test_uda.uda_type == UdaType.STRING
    assert test_uda.label == "Test String"

    priority_uda = registry.get_uda("priority")
    assert priority_uda.uda_type == UdaType.NUMERIC
    assert priority_uda.coefficient == 2.0


def test_load_from_config_with_empty_mapping():
    """Loading with an empty mapping yields no UDAs (no file I/O)."""
    registry = UdaRegistry()
    registry.load_from_config({})
    assert registry.get_uda_names() == set()


def test_is_uda_field():
    """Test checking if a field name is a defined UDA."""
    registry = UdaRegistry()

    # Initially empty
    assert not registry.is_uda_field("test")

    taskrc_content = "uda.test.type=string\n"
    cfg = _config_from_string(taskrc_content)
    registry.load_from_config(cfg)

    assert registry.is_uda_field("test")
    assert not registry.is_uda_field("nonexistent")


def test_get_uda_type():
    """Test getting UDA type by name."""
    registry = UdaRegistry()

    taskrc_content = "uda.test.type=string\n"
    cfg = _config_from_string(taskrc_content)
    registry.load_from_config(cfg)

    assert registry.get_uda("test").uda_type == UdaType.STRING
    assert registry.get_uda("nonexistent") is None


def test_get_uda_names():
    """Test getting all UDA names."""
    registry = UdaRegistry()

    taskrc_content = """
uda.first_str.type=string
uda.second_date.type=date
"""
    cfg = _config_from_string(taskrc_content)
    registry.load_from_config(cfg)

    expected_names = {"first_str", "second_date"}
    assert registry.get_uda_names() == expected_names


def test_load_from_config_invalid_uda():
    """Test handling of invalid UDA definitions."""
    taskrc_content = """
uda.testtype=invalid_type
uda.valid.type=string
"""

    registry = UdaRegistry()
    cfg = _config_from_string(taskrc_content)
    registry.load_from_config(cfg)

    assert "valid" in registry.get_uda_names()
    assert "test" not in registry.get_uda_names()


def test_define_update_uda_with_empty_fields(tmp_path):
    """Test adding a UDA to registry with some empty fields."""
    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text("")

    registry = UdaRegistry()

    uda = UdaConfig(name="test_uda", uda_type=UdaType.STRING, label="", default="default_value")
    # Registry is pure: add_uda is non-side-effecting
    registry.add_uda(uda)

    assert "test_uda" in registry.get_uda_names()
    loaded_uda = registry.get_uda("test_uda")
    assert loaded_uda.uda_type == UdaType.STRING
    assert loaded_uda.default == "default_value"


def test_delete_uda(tmp_path):
    """Test removing a UDA from the registry (in-memory)."""
    taskrc_file = tmp_path / ".taskrc"
    taskrc_file.write_text("uda.test_uda.type=string\nuda.test_uda.label=Test UDA\n")

    registry = UdaRegistry()
    cfg = _config_from_string(taskrc_file.read_text(encoding="utf-8"))
    registry.load_from_config(cfg)

    assert "test_uda" in registry.get_uda_names()

    # Remove from registry in-memory
    registry.remove_uda("test_uda")
    assert "test_uda" not in registry.get_uda_names()
