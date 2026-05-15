# Synchronization

pytaskwarrior supports two synchronization modes via the default
`TaskChampionAdapter` — no `task` binary required.

| Mode | Config key | When to use |
|------|-----------|-------------|
| **Remote** | `sync.server.origin` | Sync across machines via a taskchampion HTTP server |
| **Local** | `sync.local.server_dir` | Sync via a shared directory (NFS, SMB, Dropbox, …) |

Both modes expose the same Python API: `tw.synchronize()` and `tw.is_sync_configured()`.

---

## Prerequisites

- `taskchampion-py >= 3.0.1.1` built from the fork in `tmp/taskchampion-py-fork/`
  (installed automatically with `uv sync`)
- Local sync requires the fork to be built with the `server-local` feature
  (enabled by default in this repository's `pyproject.toml`)

---

## Remote sync

Remote sync uses the
[taskchampion sync protocol](https://gothenburgbitfactory.org/taskchampion/sync-protocol.html)
over HTTPS to a compatible server such as
[taskchampion-sync-server](https://github.com/GothenburgBitFactory/taskchampion-sync-server).

### `.taskrc` configuration

```ini
sync.server.origin=https://taskchampion.example.com
sync.server.client_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
sync.encryption.secret=my-passphrase
```

| Key | Required | Description |
|-----|----------|-------------|
| `sync.server.origin` | **yes** | Full URL of the sync server |
| `sync.server.client_id` | no | UUID identifying this client. **Auto-generated and persisted if absent.** |
| `sync.encryption.secret` | recommended | Passphrase used to encrypt tasks at rest on the server |

!!! tip "Automatic client ID"
    If `sync.server.origin` is set but `sync.server.client_id` is absent, pytaskwarrior
    generates a stable UUID on first use and writes it to `.taskrc` automatically.
    The same client ID is then reused in subsequent sessions.

### Python usage

```python
from taskwarrior import TaskWarrior

tw = TaskWarrior()            # sync config is read from ~/.taskrc automatically
tw.synchronize()              # push local changes, pull remote changes
print(tw.is_sync_configured())  # True
```

### Direct `TaskChampionAdapter` usage

```python
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

adapter = TaskChampionAdapter(
    data_location="~/.task",
    sync_server_url="https://taskchampion.example.com",
    sync_client_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    sync_encryption_secret="my-passphrase",
)
adapter.synchronize()
```

---

## Local directory sync

Local sync stores operations in a plain directory that acts as the server.
Both clients must have access to the same directory (e.g. via a network share).

### `.taskrc` configuration

```ini
sync.local.server_dir=/path/to/shared/taskserver
```

| Key | Required | Description |
|-----|----------|-------------|
| `sync.local.server_dir` | **yes** | Path to the shared server directory. Created if absent. |

### Python usage

```python
from taskwarrior import TaskWarrior

tw = TaskWarrior()
# sync.local.server_dir is read from ~/.taskrc automatically
tw.synchronize()
```

### Direct `TaskChampionAdapter` usage

```python
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

adapter = TaskChampionAdapter(
    data_location="~/.task",
    sync_local_server_dir="/path/to/shared/taskserver",
)
adapter.synchronize()
```

!!! note "Local vs remote precedence"
    When both `sync_local_server_dir` and `sync_server_url` are supplied,
    local sync takes precedence.

---

## Python API reference

### `TaskWarrior.synchronize()`

```python
tw.synchronize() -> None
```

Runs a full sync cycle (push local operations, pull remote operations).

Raises `TaskSyncError` if:
- No sync backend is configured (neither remote nor local)
- The sync operation fails (network error, invalid credentials, server unavailable)

### `TaskWarrior.is_sync_configured()`

```python
tw.is_sync_configured() -> bool
```

Returns `True` if at least one sync backend is configured in the active adapter.

---

## `.taskrc` key reference

| Key | Mode | Description |
|-----|------|-------------|
| `sync.server.origin` | Remote | URL of the taskchampion HTTP sync server |
| `sync.server.client_id` | Remote | Client UUID (auto-generated if absent) |
| `sync.encryption.secret` | Remote | Encryption passphrase for at-rest data |
| `sync.local.server_dir` | Local | Path to the shared server directory |

---

## Differences vs `task sync` CLI

When using the `TaskWarriorAdapter` (CLI mode via `TaskWarrior(task_cmd="task")`),
`tw.synchronize()` delegates to `task sync`, which uses TaskWarrior's built-in sync
configuration.

| Aspect | `TaskChampionAdapter` (default) | `TaskWarriorAdapter` (CLI) |
|--------|--------------------------------|---------------------------|
| Binary required | ❌ | ✅ |
| Remote sync server | ✅ `sync_to_remote` | ✅ via `task sync` |
| Local directory sync | ✅ `sync_to_local` | ✅ via `task sync` |
| GCP sync | ✅ `sync_to_gcp` (direct) | ✅ via `task sync` |
| Config key names | TW 3.x standard | TW 3.x standard |
| `is_sync_configured()` | Reads `.taskrc` | Reads `.taskrc` |

!!! warning "Config key names changed in pytaskwarrior 3.0"
    Earlier pre-releases of pytaskwarrior 3.0 read `sync.server.url` and
    `sync.client.id`. These were incorrect. The standard TaskWarrior 3.x keys
    `sync.server.origin` and `sync.server.client_id` are now used.

---

## Troubleshooting

### `TaskSyncError: No sync server configured`

No sync keys were found in `.taskrc` (or the resolved taskrc file).

- Check that `TASKRC` environment variable points to the correct file.
- Verify at least one of `sync.server.origin` or `sync.local.server_dir` is set.
- Run `tw.config_store.get_sync_config()` to inspect what keys are detected:

  ```python
  print(tw.config_store.get_sync_config())
  # {} → no sync keys found
  ```

### `TaskSyncError: Sync failed: …`

The underlying `sync_to_remote` or `sync_to_local` call raised an error.

Common causes:

| Symptom | Likely cause |
|---------|--------------|
| `connection refused` / `unable to connect` | Wrong URL or server down |
| `401 Unauthorized` | Wrong `client_id` or `encryption_secret` |
| `invalid UUID` | `sync.server.client_id` is not a valid UUID v4 |
| `No such file or directory` | `sync.local.server_dir` path does not exist |
| `permission denied` | No write access to `sync.local.server_dir` |

### Sync works from CLI (`task sync`) but not from Python

If `task sync` works but `tw.synchronize()` raises:

1. The CLI adapter uses the TaskWarrior binary's sync (different code path).
2. pytaskwarrior reads config from `.taskrc` directly — verify the keys match
   the TW 3.x names (`sync.server.origin`, not `sync.server.url`).
3. Check that `TASKRC` and `TASKDATA` env vars, if set, point to the same files
   used by the CLI.

### `sync_to_local` not available

The `server-local` feature may not be compiled into your `taskchampion-py` build.
Rebuild the fork with the feature enabled:

```bash
cd tmp/taskchampion-py-fork
maturin develop
```

The repository's `pyproject.toml` already includes `server-local` in the maturin
features list.
