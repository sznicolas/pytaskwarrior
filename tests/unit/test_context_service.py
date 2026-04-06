import pytest

from taskwarrior.exceptions import TaskValidationError, TaskWarriorError
from taskwarrior.services.context_service import ContextService
from src.taskwarrior.dto.context_dto import ContextDTO


class DummyResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class DummyAdapter:
    def __init__(self):
        self.commands = []

    def run_task_command(self, args):
        self.commands.append(list(args))
        if args[0] == "_get":
            return DummyResult(returncode=0, stdout="work\n")
        return DummyResult(returncode=0)


class DummyConfig:
    def __init__(self):
        self.refreshed = False

    def refresh(self):
        self.refreshed = True

    def get_contexts(self, current_context=None):
        return []


def test_define_context_valid_calls_adapter_and_refresh():
    adapter = DummyAdapter()
    cfg = DummyConfig()
    svc = ContextService(adapter, cfg)

    svc.define_context(ContextDTO(name="work", read_filter="project:work", write_filter="project:work"))

    assert ["context", "define", "work", "project:work"] in adapter.commands
    assert ["config", "context.work.write", "project:work"] in adapter.commands
    assert cfg.refreshed is True


def test_define_context_invalid_name_raises():
    adapter = DummyAdapter()
    cfg = DummyConfig()
    svc = ContextService(adapter, cfg)

    with pytest.raises(TaskValidationError):
        svc.define_context(ContextDTO(name=" ", read_filter="a", write_filter="b"))


def test_apply_context_failure_raises_taskwarriorerror():
    class FailingAdapter(DummyAdapter):
        def run_task_command(self, args):
            return DummyResult(returncode=1, stderr="fail")

    adapter = FailingAdapter()
    cfg = DummyConfig()
    svc = ContextService(adapter, cfg)

    with pytest.raises(TaskWarriorError):
        svc.apply_context("work")


def test_unset_context_failure_raises():
    class FailingAdapter(DummyAdapter):
        def run_task_command(self, args):
            if args[0] == "context" and args[1] == "none":
                return DummyResult(returncode=1, stderr="fail")
            return DummyResult(returncode=0)

    adapter = FailingAdapter()
    cfg = DummyConfig()
    svc = ContextService(adapter, cfg)

    with pytest.raises(TaskWarriorError):
        svc.unset_context()


def test_get_current_context_returns_name_or_none():
    adapter = DummyAdapter()
    cfg = DummyConfig()
    svc = ContextService(adapter, cfg)

    assert svc.get_current_context() == "work"

    # simulate non-zero returncode
    class AdapterNoContext(DummyAdapter):
        def run_task_command(self, args):
            return DummyResult(returncode=1)

    svc_no = ContextService(AdapterNoContext(), cfg)
    assert svc_no.get_current_context() is None
