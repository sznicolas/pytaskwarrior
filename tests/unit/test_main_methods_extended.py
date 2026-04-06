from types import SimpleNamespace

from src.taskwarrior.dto.context_dto import ContextDTO
from taskwarrior.main import TaskWarrior


def test_context_delegation_methods_invoked():
    tw = TaskWarrior.__new__(TaskWarrior)

    class DummyContextService:
        def __init__(self):
            self.calls = []

        def define_context(self, ctx):
            self.calls.append(("define", ctx.name, ctx.read_filter, ctx.write_filter))

        def apply_context(self, name):
            self.calls.append(("apply", name))

        def unset_context(self):
            self.calls.append(("unset",))

        def delete_context(self, name):
            self.calls.append(("delete", name))

        def get_contexts(self):
            self.calls.append(("get_contexts",))
            return [
                SimpleNamespace(
                    name="work",
                    read_filter="project:work",
                    write_filter="project:work",
                    active=True,
                )
            ]

        def has_context(self, name):
            self.calls.append(("has", name))
            return name == "exists"

    svc = DummyContextService()
    tw.context_service = svc

    tw.define_context(ContextDTO(name="work", read_filter="project:work", write_filter="project:work"))
    assert ("define", "work", "project:work", "project:work") in svc.calls

    tw.apply_context("work")
    assert ("apply", "work") in svc.calls

    tw.unset_context()
    assert ("unset",) in svc.calls

    tw.delete_context("work")
    assert ("delete", "work") in svc.calls

    # get_contexts should delegate and return the same list
    assert tw.get_contexts()[0].name == "work"

    assert tw.has_context("exists") is True
    assert tw.has_context("no") is False


def test_is_sync_configured_and_synchronize():
    tw = TaskWarrior.__new__(TaskWarrior)

    class DummyAdapter:
        def __init__(self):
            self.sync_called = False

        def is_sync_configured(self):
            return True

        def synchronize(self):
            self.sync_called = True

    adapter = DummyAdapter()
    tw.adapter = adapter

    assert tw.is_sync_configured() is True
    tw.synchronize()
    assert adapter.sync_called is True


def test_get_info_with_active_context():
    tw = TaskWarrior.__new__(TaskWarrior)

    class DummyAdapter:
        task_cmd = "/usr/bin/task"
        cli_options = {"rc.test": "1"}

        def get_version(self):
            return "3.5.0"

    class DummyConfig:
        taskrc_path = "/tmp/.taskrc"

    tw.adapter = DummyAdapter()
    tw.config_store = DummyConfig()
    tw.get_current_context = lambda: "work"
    tw.context_service = SimpleNamespace(
        get_contexts=lambda: [
            SimpleNamespace(
                name="work",
                read_filter="project:work",
                write_filter="project:work",
                active=True,
            )
        ]
    )

    info = tw.get_info()
    assert info["task_cmd"] == "/usr/bin/task"
    assert info["taskrc_file"] == "/tmp/.taskrc"
    assert info["version"] == "3.5.0"
    assert info["current_context"] == "work"
    assert info["current_context_details"] == {
        "name": "work",
        "read_filter": "project:work",
        "write_filter": "project:work",
        "active": True,
    }


def test_get_tasks_combines_filter_with_active_context():
    tw = TaskWarrior.__new__(TaskWarrior)

    class DummyAdapter:
        def __init__(self):
            self.last_filter = None

        def get_tasks(self, filter="", include_completed=False, include_deleted=False):
            self.last_filter = filter
            return []

    adapter = DummyAdapter()
    tw.adapter = adapter

    tw.get_current_context = lambda: "work"
    tw.context_service = SimpleNamespace(
        get_contexts=lambda: [
            SimpleNamespace(name="work", read_filter="project:work", write_filter="", active=False)
        ]
    )

    tw.get_tasks(filter="priority:H")
    assert adapter.last_filter == "project:work and (priority:H)"

    # When no filter provided, should use just the context read_filter
    tw.get_tasks()
    assert adapter.last_filter == "project:work"
