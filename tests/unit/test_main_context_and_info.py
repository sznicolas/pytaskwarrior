from taskwarrior.main import TaskWarrior


def test_get_tasks_when_context_lookup_fails():
    # Create an instance without running __init__ to avoid side effects
    tw = TaskWarrior.__new__(TaskWarrior)

    class DummyAdapter:
        def get_tasks(self, filter="", include_completed=False, include_deleted=False):
            assert filter == ""  # combined_filter should remain empty when context lookup fails
            return ["task1"]

    tw.adapter = DummyAdapter()

    def broken_get_current_context():
        raise RuntimeError("context failure")

    tw.get_current_context = broken_get_current_context

    tasks = tw.get_tasks()
    assert tasks == ["task1"]


def test_get_info_handles_context_errors_and_returns_basic_info():
    tw = TaskWarrior.__new__(TaskWarrior)

    class DummyAdapter:
        task_cmd = "/usr/bin/task"
        cli_options = {"rc.test": "1"}

        def get_version(self):
            return "2.6.1"

    tw.adapter = DummyAdapter()

    class DummyConfig:
        taskrc_path = "/tmp/.taskrc"

    tw.config_store = DummyConfig()

    def broken_get_current_context():
        raise RuntimeError("boom")

    tw.get_current_context = broken_get_current_context

    # context_service may be present but will not be used because get_current_context raises
    tw.context_service = object()

    info = tw.get_info()

    assert info["task_cmd"] == "/usr/bin/task"
    assert info["taskrc_file"] == "/tmp/.taskrc"
    assert info["version"] == "2.6.1"
    assert info["current_context"] is None
    assert info["current_context_details"] is None
