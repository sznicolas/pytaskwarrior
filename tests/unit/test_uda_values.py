from unittest.mock import MagicMock

from taskwarrior.dto.uda_dto import UdaConfig, UdaType
from taskwarrior.services.uda_service import UdaService


def test_define_uda_with_list_values():
    mock_config_store = MagicMock()
    uda = UdaConfig(name="complexity", uda_type=UdaType.STRING, values=["low", "medium", "high"], label="Complexity level")
    svc = UdaService(config_store=mock_config_store)
    svc.define_uda(uda)

    mock_config_store.set_value.assert_any_call("uda.complexity.type", uda.uda_type.value)
    mock_config_store.set_value.assert_any_call("uda.complexity.values", "low,medium,high")


def test_define_uda_with_int_values():
    mock_config_store = MagicMock()
    uda = UdaConfig.model_construct(name="score", uda_type=UdaType.NUMERIC, values=[1, 2, 3], label="Score levels")
    svc = UdaService(config_store=mock_config_store)
    svc.define_uda(uda)

    mock_config_store.set_value.assert_any_call("uda.score.type", uda.uda_type.value)
    mock_config_store.set_value.assert_any_call("uda.score.values", "1,2,3")

def test_uda_config_accepts_type_alias():
    # Should accept 'type' as an alias for 'uda_type'
    uda = UdaConfig(name="alias_test", type="string", label="Alias Test")
    assert uda.uda_type == UdaType.STRING
    assert uda.name == "alias_test"
    assert uda.label == "Alias Test"

    # If both 'uda_type' and 'type' are present, 'uda_type' wins
    uda2 = UdaConfig(name="alias_test2", uda_type=UdaType.NUMERIC, type="string")
    assert uda2.uda_type == UdaType.NUMERIC
