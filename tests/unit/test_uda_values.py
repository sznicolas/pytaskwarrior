import types

from taskwarrior.dto.uda_dto import UdaConfig, UdaType
from taskwarrior.services.uda_service import UdaService


def test_define_uda_with_list_values():
    calls = []

    class DummyAdapter:
        def run_task_command(self, cmd):
            # record the command and simulate success
            calls.append(cmd)
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    class DummyConfigStore:
        pass

    uda = UdaConfig(name="complexity", uda_type=UdaType.STRING, values=["low", "medium", "high"], label="Complexity level")
    svc = UdaService(DummyAdapter(), DummyConfigStore())
    svc.define_uda(uda)

    # Type command must be present
    assert ["config", "uda.complexity.type", uda.uda_type.value] in calls

    # Values list should be converted to comma-separated string
    assert ["config", "uda.complexity.values", "low,medium,high"] in calls


def test_define_uda_with_int_values():
    calls = []

    class DummyAdapter:
        def run_task_command(self, cmd):
            calls.append(cmd)
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    class DummyConfigStore:
        pass

    # values provided as ints should be stringified and joined
    # construct without validation to simulate non-str inputs
    uda = UdaConfig.model_construct(name="score", uda_type=UdaType.NUMERIC, values=[1, 2, 3], label="Score levels")
    svc = UdaService(DummyAdapter(), DummyConfigStore())
    svc.define_uda(uda)

    assert ["config", "uda.score.type", uda.uda_type.value] in calls
    assert ["config", "uda.score.values", "1,2,3"] in calls
