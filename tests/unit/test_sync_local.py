import os
import pytest
from unittest.mock import MagicMock, patch
from src.taskwarrior.sync_backends.sync_local import SyncLocal

class DummyReplica:
    def __init__(self):
        self.synced = False
        self.fail = False
    def sync_to_local(self, sync_dir, avoid_snapshots=False):
        if self.fail:
            raise RuntimeError("Sync failed!")
        self.synced = True

@patch("src.taskwarrior.sync_backends.sync_local.Replica")
def test_sync_local_success(mock_replica):
    dummy = DummyReplica()
    mock_replica.new_on_disk.return_value = dummy
    sync_dir = "/tmp/syncdir"
    sync = SyncLocal(sync_dir)
    sync.synchronize()
    assert dummy.synced is True

@patch("src.taskwarrior.sync_backends.sync_local.Replica")
def test_sync_local_failure(mock_replica):
    dummy = DummyReplica()
    dummy.fail = True
    mock_replica.new_on_disk.return_value = dummy
    sync_dir = "/tmp/syncdir"
    sync = SyncLocal(sync_dir)
    with pytest.raises(RuntimeError, match="Sync failed!"):
        sync.synchronize()

@patch("src.taskwarrior.sync_backends.sync_local.Replica")
def test_sync_local_config_absent(mock_replica, tmp_path):
    # Simulate missing directory
    dummy = DummyReplica()
    mock_replica.new_on_disk.return_value = dummy
    sync_dir = tmp_path / "not_created"
    sync = SyncLocal(str(sync_dir))
    # Should not raise on instantiation
    sync.synchronize()
    assert dummy.synced is True
