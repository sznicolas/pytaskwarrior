# Runtime Configuration Guide

This guide shows how to modify TaskWarrior configuration at runtime in your
application — without restarting or recreating the `TaskWarrior` instance.

---

## What changed

Prior to this feature, sync parameters and other taskrc settings were read
**once** at construction time.  Any change required recreating the adapter.

Now both adapters read configuration **lazily** from `config_store` on every
call.  A single `set_value()` is enough — no restart needed.

---

## Step 1 — Nothing changes at construction

Your existing initialization code stays exactly the same:

```python
# Before — still valid, nothing to change
self._tw = TaskWarrior(taskrc_file="/path/to/.taskrc")

# Or with explicit data directory
self._tw = TaskWarrior(
    taskrc_file="/path/to/.taskrc",
    data_location="/path/to/task/data",
)
```

---

## Step 2 — Modify config at runtime via `config_store`

`TaskWarrior` exposes a `config_store` attribute.  Use it to read or write any
taskrc key at any point after construction.

### Set a single key

```python
self._tw.config_store.set_value("sync.server.origin", "https://sync.example.com")
```

The change is written to disk **and** the in-memory cache is refreshed
immediately.  The next adapter call picks it up automatically.

### Delete a key

```python
self._tw.config_store.delete_value("sync.encryption.secret")
```

### Read the current value

```python
origin = self._tw.config_store.config.get("sync.server.origin")
```

---

## Step 3 — Replace sync configuration

Use `set_sync_config()` to **replace** all `sync.*` keys in one atomic
operation (existing keys not in the new dict are removed):

```python
# Switch to remote sync
self._tw.config_store.set_sync_config({
    "sync.server.origin": "https://taskchampion.example.com",
    "sync.server.client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "sync.encryption.secret": "my-passphrase",
})

# Switch to local sync (previous remote keys are removed automatically)
self._tw.config_store.set_sync_config({
    "sync.local.server_dir": "/mnt/shared/taskserver",
})

# Disable sync entirely
self._tw.config_store.set_sync_config({})
```

After any of the above, just call:

```python
self._tw.synchronize()  # uses the new config immediately
```

---

## Step 4 — Real-world patterns

### Pattern A — Configure sync from user input

```python
class MyApp:
    def __init__(self, taskrc: str):
        self._tw = TaskWarrior(taskrc_file=taskrc)

    def configure_sync(self, server_url: str, secret: str) -> None:
        self._tw.config_store.set_sync_config({
            "sync.server.origin": server_url,
            "sync.encryption.secret": secret,
        })

    def sync(self) -> None:
        if self._tw.is_sync_configured():
            self._tw.synchronize()
```

### Pattern B — Toggle sync on / off

```python
def enable_sync(self, server_dir: str) -> None:
    self._tw.config_store.set_value("sync.local.server_dir", server_dir)

def disable_sync(self) -> None:
    self._tw.config_store.set_sync_config({})  # removes all sync.* keys
```

### Pattern C — Read then modify

```python
def rotate_secret(self, new_secret: str) -> None:
    cfg = self._tw.config_store.get_sync_config()
    if not cfg.get("sync.server.origin"):
        raise RuntimeError("Remote sync is not configured")
    self._tw.config_store.set_value("sync.encryption.secret", new_secret)
```

---

## What you must NOT change at runtime

| Setting | Why |
|---------|-----|
| `rc.data.location` | The SQLite database (`Replica`) is opened once at construction; changing the path has no effect on the running adapter. |

If you need a different data directory, create a new `TaskWarrior` instance:

```python
# Correct way to switch data directory
self._tw = TaskWarrior(
    taskrc_file=self._taskrc,
    data_location="/new/path",
)
```

---

## Quick reference

| Goal | Method |
|------|--------|
| Write a single key | `tw.config_store.set_value(key, value)` |
| Delete a single key | `tw.config_store.delete_value(key)` |
| Replace all `sync.*` keys | `tw.config_store.set_sync_config({…})` |
| Read a value | `tw.config_store.config.get(key)` |
| Read all sync keys | `tw.config_store.get_sync_config()` |
| Reload from disk | `tw.config_store.refresh()` |
| Check sync active | `tw.is_sync_configured()` |
