"""Unit tests for ConfigStore.set_sync_config."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from src.taskwarrior.config.config_store import ConfigStore
from src.taskwarrior.exceptions import TaskConfigurationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: Path, initial_content: str = "") -> ConfigStore:
    """Create a ConfigStore backed by a tmp taskrc file."""
    rc = tmp_path / ".taskrc"
    rc.write_text(initial_content, encoding="utf-8")
    return ConfigStore(str(rc))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSetSyncConfigRemote:
    def test_writes_remote_keys(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.set_sync_config(
            {
                "sync.server.origin": "https://sync.example.com",
                "sync.server.client_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "sync.encryption.secret": "s3cr3t",
            }
        )
        result = store.get_sync_config()
        assert result["sync.server.origin"] == "https://sync.example.com"
        assert result["sync.server.client_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert result["sync.encryption.secret"] == "s3cr3t"

    def test_keys_persisted_to_taskrc_file(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.set_sync_config({"sync.server.origin": "https://sync.example.com"})
        rc_text = (tmp_path / ".taskrc").read_text(encoding="utf-8")
        assert "sync.server.origin=https://sync.example.com" in rc_text


class TestSetSyncConfigLocal:
    def test_writes_local_server_dir(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        local_dir = str(tmp_path / "server")
        store.set_sync_config({"sync.local.server_dir": local_dir})
        result = store.get_sync_config()
        assert result["sync.local.server_dir"] == local_dir


class TestSetSyncConfigReplacement:
    def test_removes_keys_not_in_new_config(self, tmp_path: Path) -> None:
        """Keys currently in the file but absent from config must be deleted."""
        initial = (
            "sync.server.origin=https://old.example.com\n"
            "sync.server.client_id=old-id\n"
            "sync.encryption.secret=old-secret\n"
        )
        store = _make_store(tmp_path, initial_content=initial)
        # Switch to local sync only — all previous remote keys should disappear.
        store.set_sync_config({"sync.local.server_dir": "/tmp/server"})
        result = store.get_sync_config()
        assert "sync.server.origin" not in result
        assert "sync.server.client_id" not in result
        assert "sync.encryption.secret" not in result
        assert result["sync.local.server_dir"] == "/tmp/server"

    def test_empty_config_wipes_all_sync_keys(self, tmp_path: Path) -> None:
        initial = (
            "sync.server.origin=https://sync.example.com\n"
            "rc.confirmation=off\n"
        )
        store = _make_store(tmp_path, initial_content=initial)
        store.set_sync_config({})
        assert store.get_sync_config() == {}
        # Non-sync keys must survive.
        assert store.config.get("rc.confirmation") == "off"

    def test_non_sync_keys_untouched(self, tmp_path: Path) -> None:
        initial = (
            "rc.confirmation=off\n"
            "sync.server.origin=https://sync.example.com\n"
        )
        store = _make_store(tmp_path, initial_content=initial)
        store.set_sync_config({"sync.server.origin": "https://new.example.com"})
        assert store.config.get("rc.confirmation") == "off"


class TestSetSyncConfigNoneDeletesKey:
    def test_none_value_removes_key(self, tmp_path: Path) -> None:
        initial = "sync.encryption.secret=s3cr3t\n"
        store = _make_store(tmp_path, initial_content=initial)
        store.set_sync_config({"sync.encryption.secret": None})
        assert "sync.encryption.secret" not in store.get_sync_config()

    def test_none_for_absent_key_is_noop(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        # Should not raise.
        store.set_sync_config({"sync.encryption.secret": None})
        assert store.get_sync_config() == {}


class TestSetSyncConfigKeyNormalisation:
    def test_prefix_added_automatically(self, tmp_path: Path) -> None:
        """Keys without the 'sync.' prefix are accepted and prefixed internally."""
        store = _make_store(tmp_path)
        store.set_sync_config({"server.origin": "https://sync.example.com"})
        result = store.get_sync_config()
        assert "sync.server.origin" in result
        assert result["sync.server.origin"] == "https://sync.example.com"


class TestSetSyncConfigCacheConsistency:
    def test_get_sync_config_reflects_new_values(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.set_sync_config({"sync.server.origin": "https://sync.example.com"})
        # get_sync_config reads from the in-memory cache — must be up-to-date.
        assert store.get_sync_config()["sync.server.origin"] == "https://sync.example.com"

    def test_overwrite_existing_value(self, tmp_path: Path) -> None:
        initial = "sync.server.origin=https://old.example.com\n"
        store = _make_store(tmp_path, initial_content=initial)
        store.set_sync_config({"sync.server.origin": "https://new.example.com"})
        assert store.get_sync_config()["sync.server.origin"] == "https://new.example.com"


@pytest.mark.skipif(sys.platform == "win32", reason="chmod not applicable on Windows")
class TestSetSyncConfigErrorHandling:
    def test_raises_task_configuration_error_on_write_failure(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rc_file = tmp_path / ".taskrc"
        rc_file.chmod(stat.S_IRUSR)  # read-only
        try:
            with pytest.raises(TaskConfigurationError):
                store.set_sync_config({"sync.server.origin": "https://sync.example.com"})
        finally:
            rc_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # restore
