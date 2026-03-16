import pytest

from taskwarrior.sync_backends.factory import create_sync_backend
import taskwarrior.sync_backends.sync_local as sync_local_module
from taskwarrior.sync_backends.sync_local import SyncLocal


def test_create_sync_backend_none_when_missing_key():
    assert create_sync_backend({}) is None


def test_create_sync_backend_none_when_empty_value():
    assert create_sync_backend({"sync.local.server_dir": ""}) is None
    assert create_sync_backend({"sync.local.server_dir": "   "}) is None


def test_create_sync_backend_returns_synclocal(monkeypatch, tmp_path):
    """When a valid server_dir is provided, create_sync_backend should return a SyncLocal instance.

    Patch the Replica.new_on_disk factory to avoid touching the real filesystem.
    """
    class DummyReplica:
        def sync_to_local(self, *args, **kwargs):
            pass

    class DummyReplicaFactory:
        @staticmethod
        def new_on_disk(path, flag):
            return DummyReplica()

    # Replace Replica in the sync_local module with our dummy factory
    monkeypatch.setattr(sync_local_module, "Replica", DummyReplicaFactory, raising=False)

    server_dir = str(tmp_path)
    result = create_sync_backend({"sync.local.server_dir": server_dir})
    assert isinstance(result, SyncLocal)
    assert getattr(result, "sync_dir") == server_dir


def test_create_sync_backend_coerces_non_string(monkeypatch):
    # Ensure non-string values are coerced to str and work
    class DummyReplica:
        def sync_to_local(self, *args, **kwargs):
            pass

    class DummyReplicaFactory:
        @staticmethod
        def new_on_disk(path, flag):
            return DummyReplica()

    monkeypatch.setattr(sync_local_module, "Replica", DummyReplicaFactory, raising=False)

    result = create_sync_backend({"sync.local.server_dir": 12345})
    assert isinstance(result, SyncLocal)
    assert getattr(result, "sync_dir") == "12345"
