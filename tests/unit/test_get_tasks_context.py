

from taskwarrior import TaskWarrior
from taskwarrior.dto.context_dto import ContextDTO


def _make_tw(monkeypatch):
    # Ensure adapter binary check passes in test environment
    monkeypatch.setattr(
        "taskwarrior.adapters.taskwarrior_adapter.shutil.which",
        lambda cmd: "/usr/bin/task",
    )
    return TaskWarrior()


def test_get_tasks_applies_context_read_filter(monkeypatch):
    tw = _make_tw(monkeypatch)

    # Simulate an active context with a read_filter
    monkeypatch.setattr(tw, "get_current_context", lambda: "work")
    ctx = ContextDTO(name="work", read_filter="project:work", write_filter="project:work", active=True)
    monkeypatch.setattr(tw.context_service, "get_contexts", lambda: [ctx])

    captured = {}

    def fake_get_tasks(filter: str = "", include_completed: bool = False, include_deleted: bool = False):
        captured["filter"] = filter
        captured["include_completed"] = include_completed
        captured["include_deleted"] = include_deleted
        return []

    monkeypatch.setattr(tw.adapter, "get_tasks", fake_get_tasks)

    tw.get_tasks(filter="priority:H")

    assert captured["filter"] == "project:work and (priority:H)"


def test_get_tasks_with_only_context_read_filter(monkeypatch):
    tw = _make_tw(monkeypatch)

    monkeypatch.setattr(tw, "get_current_context", lambda: "work")
    ctx = ContextDTO(name="work", read_filter="project:work", write_filter="project:work", active=True)
    monkeypatch.setattr(tw.context_service, "get_contexts", lambda: [ctx])

    captured = {}

    def fake_get_tasks(filter: str = "", include_completed: bool = False, include_deleted: bool = False):
        captured["filter"] = filter
        return []

    monkeypatch.setattr(tw.adapter, "get_tasks", fake_get_tasks)

    tw.get_tasks()

    assert captured["filter"] == "project:work"
