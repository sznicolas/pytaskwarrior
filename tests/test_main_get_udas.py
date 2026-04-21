
from taskwarrior import TaskWarrior


def test_get_udas_empty(monkeypatch):
    tw = TaskWarrior(task_cmd="task", taskrc_file="/tmp/nonexistent", data_location=None)
    monkeypatch.setattr(tw.uda_service.registry, "get_udas", lambda: [])
    assert tw.get_udas() == []


def test_get_udas_multiple(monkeypatch):
    tw = TaskWarrior(task_cmd="task", taskrc_file="/tmp/nonexistent", data_location=None)

    class DummyUda:
        def __init__(self, name):
            self.name = name

    names = {"sev", "est"}
    monkeypatch.setattr(tw.uda_service.registry, "get_udas", lambda: [DummyUda("sev"), DummyUda("est")])

    udas = tw.get_udas()
    assert {u.name for u in udas} == names
