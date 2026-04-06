from taskwarrior import TaskWarrior
from taskwarrior.dto.context_dto import ContextDTO


def test_get_info_without_context(tmp_path, monkeypatch):
    tw = TaskWarrior(taskrc_file=str(tmp_path / "taskrc"), data_location=str(tmp_path / "data"))
    monkeypatch.setattr(tw.adapter, "get_version", lambda: "1.2.0")
    monkeypatch.setattr(tw, "get_current_context", lambda: None)

    info = tw.get_info()

    assert "current_context" in info
    assert info["current_context"] is None
    assert info["current_context_details"] is None


def test_get_info_with_active_context(tmp_path, monkeypatch):
    tw = TaskWarrior(taskrc_file=str(tmp_path / "taskrc"), data_location=str(tmp_path / "data"))
    monkeypatch.setattr(tw.adapter, "get_version", lambda: "1.2.0")
    monkeypatch.setattr(tw, "get_current_context", lambda: "work")

    ctx = ContextDTO(
        name="work", read_filter="project:work", write_filter="project:work", active=True
    )
    monkeypatch.setattr(tw.context_service, "get_contexts", lambda *a, **k: [ctx])

    info = tw.get_info()

    assert info["current_context"] == "work"
    assert info["current_context_details"] == {
        "name": "work",
        "read_filter": "project:work",
        "write_filter": "project:work",
        "active": True,
    }
