import pytest


def test_facade_synchronize_no_op(monkeypatch):
    """Calling TaskWarrior.synchronize() via the façade must not trigger adapter synchronization.

    We monkeypatch the TaskWarriorAdapter, ConfigStore, ContextService and UdaService
    to avoid filesystem or binary lookups and to detect whether adapter.synchronize()
    is invoked.
    """
    import taskwarrior.main as main_mod

    called = {"adapter_sync_called": False}

    class DummyAdapter:
        def __init__(self, *a, **kw):
            # minimal adapter stub
            self.cli_options = []

        def synchronize(self):
            called["adapter_sync_called"] = True

        def is_sync_configured(self):
            return True

        def get_version(self):
            return "0.0"

    class DummyConfigStore:
        def __init__(self, taskrc_file, data_location):
            self.cli_options = []
            self.taskrc_file = taskrc_file
            self.data_location = data_location

    class DummyContextService:
        def __init__(self, adapter, config_store):
            pass

    class DummyUdaService:
        def __init__(self, adapter, config_store):
            self.registry = type("R", (), {"get_uda_names": lambda self: set(), "get_uda": lambda self, name: None})()

        def load_udas_from_taskrc(self):
            pass

    monkeypatch.setattr(main_mod, "TaskWarriorAdapter", DummyAdapter)
    # ConfigStore is imported inside TaskWarrior.__init__ (local import). Patch the module path used by that import.
    monkeypatch.setattr("taskwarrior.config.config_store.ConfigStore", DummyConfigStore, raising=True)
    monkeypatch.setattr(main_mod, "ContextService", DummyContextService)
    monkeypatch.setattr(main_mod, "UdaService", DummyUdaService)

    tw = main_mod.TaskWarrior(task_cmd="task", taskrc_file=":memory:")
    # Should be a no-op and not call DummyAdapter.synchronize()
    tw.synchronize()

    assert called["adapter_sync_called"] is False
