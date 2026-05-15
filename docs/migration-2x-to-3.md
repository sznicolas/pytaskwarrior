# Migration Guide: 2.x → 3.0

pytaskwarrior 3.0 replaces the default backend with
[`TaskChampionAdapter`](taskchampion-adapter.md) — direct SQLite access via
Rust bindings. The `task` binary is no longer required.

This guide covers every breaking change and all new features.

---

## Quick summary

| What changed | Before (2.x) | After (3.0) |
|---|---|---|
| Default backend | `TaskWarriorAdapter` (CLI) | `TaskChampionAdapter` (SQLite) |
| `task` binary required | **yes** | no (only for CLI mode) |
| `TaskWarrior()` | spawns `task` | reads/writes SQLite directly |
| `task_cmd` default | `"task"` | `None` |
| `task_cmd` positional | `TaskWarrior("task")` | `TaskWarrior(task_cmd="task")` |
| `get_info()["task_cmd"]` | always `str` | `None` when TC adapter |
| `get_info()["backend_type"]` | key didn't exist | `"taskchampion"` or `"taskwarrior-cli"` |
| `ContextService(adapter, cfg)` | positional order | `ContextService(cfg, adapter=None)` |
| `UdaService(adapter, cfg)` | positional order | `UdaService(cfg, adapter=None)` |
| `task sync` (CLI) | default sync path | only when `task_cmd="task"` |
| `sync.server.url` key | accepted | **removed** → use `sync.server.origin` |
| `sync.client.id` key | accepted | **removed** → use `sync.server.client_id` |
| Urgency score | returned by CLI | `None` (not computed) |
| OR / AND filters | supported by CLI | **not supported** by TC adapter |

---

## Breaking changes

### 1. Default backend is now `TaskChampionAdapter`

`TaskWarrior()` with no arguments now creates a `TaskChampionAdapter`.
No `task` binary is spawned.

```python
# 2.x
tw = TaskWarrior()           # spawned `task` subprocess, required task binary

# 3.0
tw = TaskWarrior()           # reads/writes SQLite directly, no binary needed
tw = TaskWarrior(task_cmd="task")  # explicit CLI mode (unchanged behaviour)
```

**Action required if you relied on the CLI adapter being the default:** add
`task_cmd="task"` to your `TaskWarrior()` call.

### 2. `task_cmd` was the first positional argument

`task_cmd` changed from `str = "task"` to `str | None = None`.
If you passed the binary path positionally, add the keyword:

```python
# 2.x — positional, worked because str default
TaskWarrior("/usr/bin/task")

# 3.0 — must be explicit keyword
TaskWarrior(task_cmd="/usr/bin/task")
```

These forms are unchanged:
```python
TaskWarrior(task_cmd="task")      # ✅ still works
TaskWarrior(taskrc_file="...")    # ✅ still works
TaskWarrior(data_location="...")  # ✅ still works
TaskWarrior(adapter=my_adapter)   # ✅ still works
```

### 3. `get_info()` shape change

`info["task_cmd"]`, `info["options"]`, and `info["version"]` are `None` when
the TC adapter is active (the default). A new `"backend_type"` key identifies
the active backend.

```python
# 2.x — always had values
info = tw.get_info()
print(info["task_cmd"])   # "/usr/bin/task"
print(info["version"])    # "3.4.0"

# 3.0 — may be None
info = tw.get_info()
print(info["backend_type"])   # "taskchampion"  or  "taskwarrior-cli"
print(info["backend_version"])  # "taskchampion-py/3.0.1"  or  "3.4.0"
print(info["task_cmd"])       # None  (TC)  or  "/usr/bin/task"  (CLI)
print(info["version"])        # None  (TC)  or  "3.4.0"  (CLI)
```

**Action required:** guard any access to `info["task_cmd"]` or `info["version"]`
with `if info["task_cmd"]: ...`, or switch to `info["backend_type"]`.

### 4. `ContextService.__init__` argument order

The `adapter` parameter moved to second position and is now optional.
This affects code that instantiates `ContextService` directly (rare — most
code uses `tw.context_service`).

```python
# 2.x
from taskwarrior.services.context_service import ContextService
svc = ContextService(adapter, config_store)

# 3.0
svc = ContextService(config_store)              # adapter optional
svc = ContextService(config_store, adapter)     # explicit adapter
svc = ContextService(config_store, adapter=adapter)  # keyword form
```

### 5. `UdaService.__init__` argument order

Same change as `ContextService`:

```python
# 2.x
from taskwarrior.services.uda_service import UdaService
svc = UdaService(adapter, config_store)

# 3.0
svc = UdaService(config_store)
svc = UdaService(config_store, adapter=adapter)
```

### 6. Sync `.taskrc` key names

pytaskwarrior 3.0 aligns with the TaskWarrior 3.x standard key names.
Update your `.taskrc` if needed:

| Old key | New key |
|---------|---------|
| `sync.server.url` | `sync.server.origin` |
| `sync.client.id` | `sync.server.client_id` |
| `sync.encryption.secret` | **unchanged** |
| `sync.local.server_dir` | **new** (local sync) |

```ini
# .taskrc — 3.0 format
sync.server.origin=https://taskchampion.example.com
sync.server.client_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
sync.encryption.secret=my-passphrase
```

### 7. Urgency is `None`

`TaskOutputDTO.urgency` is always `None` when using the default TC adapter.
TaskChampion does not compute urgency scores.

```python
# 2.x — urgency computed by `task`
task = tw.get_task(1)
print(task.urgency)   # 8.2

# 3.0 — urgency not computed
task = tw.get_task(1)
print(task.urgency)   # None
```

**Action required:** if you sort or filter by urgency, switch to CLI mode or
implement urgency computation in your application layer.

### 8. `get_tags(include_virtual_tags=True)` return value

In 2.x with the CLI adapter, `get_tags(include_virtual_tags=True)` returned
TaskChampion's internal synthetic tag strings (e.g. `"Synthetic(Pending)"`).
In 3.0 it returns the standard TaskWarrior virtual tag names:

```python
# 2.x (TC adapter, pre-3.0)
tw.get_tags(include_virtual_tags=True)
# ["work", "Synthetic(Pending)", "Synthetic(Unblocked)", ...]

# 3.0
tw.get_tags(include_virtual_tags=True)
# ["work", "PENDING", "UNBLOCKED", "OVERDUE", "DUE", ...]
```

---

## New features

### Filters: date-range expressions

The TC filter engine now understands date-range tokens — no CLI required:

```python
tw.get_tasks("due.before:tomorrow")
tw.get_tasks("due.after:eom")
tw.get_tasks("due.by:friday")          # inclusive (≤)
tw.get_tasks("scheduled.after:today")
tw.get_tasks("wait.before:now")
tw.get_tasks("due.before:now + P7D")   # compound expression
```

Supported fields: `due`, `wait`, `scheduled`, `until`, `entry`, `modified`

Supported operators:

| Operator | Meaning |
|----------|---------|
| `before` | strict `<` |
| `after` | strict `>` |
| `by` | `≤` (inclusive) |
| `not` | `≠` — tasks with no date set also match |

### Filters: virtual tags in pure Python

All 30 TaskWarrior virtual tags work as filter tokens without calling the CLI.
28 are computed in Python; `LATEST` is a post-filter selector; `ORPHAN` is
recognized but always returns `False`:

```python
tw.get_tasks("+OVERDUE")
tw.get_tasks("+READY -BLOCKED")
tw.get_tasks("+DUE +PRIORITY project:work")
tw.get_tasks("+WEEK")
tw.get_tasks("+LATEST")   # keeps only the most recently created task
```

See [TaskChampion Adapter — Virtual Tags](taskchampion-adapter.md#virtual-tags)
for the full table.

### Date expressions: compound forms with spaces

`DateResolver` (used by `task_calc()` and all filter date thresholds) now
resolves compound expressions containing a space-separated operator:

```python
tw.task_calc("now + P1D")      # → tomorrow same time (ISO 8601)
tw.task_calc("today + 3d")     # → 3 days from now at midnight
tw.task_calc("eom - P1W")      # → one week before end of month
tw.task_calc("now + 2weeks")   # → TaskWarrior shorthand form

# Combined with filters
tw.get_tasks("due.before:now + P7D")
tw.get_tasks("scheduled.after:eom - P1W")
```

### `.taskrc` writes without the CLI

`ConfigStore` now supports direct writes. `ContextService` and `UdaService`
use it for all write operations — the `task` binary is never called for
configuration changes:

```python
# These all work without a task binary in 3.0:
tw.define_uda(UdaConfig(name="complexity", uda_type=UdaType.STRING, label="Complexity"))
tw.delete_uda(UdaConfig(name="complexity", uda_type=UdaType.STRING))
tw.define_context(ContextDTO(name="work", read_filter="project:work", write_filter="project:work"))
tw.apply_context("work")
tw.unset_context()
tw.delete_context("work")
```

Low-level access is also available:

```python
tw.config_store.set_value("uda.complexity.type", "string")
tw.config_store.set_value("uda.complexity.label", "Complexity")
tw.config_store.delete_value("uda.complexity.type")
```

### Sync: local directory mode

In addition to remote HTTP sync, the TC adapter now supports local directory
sync — useful for syncing between machines via a network share, or for
testing without a server:

```python
# .taskrc
# sync.local.server_dir=/mnt/share/taskserver

tw = TaskWarrior()   # picks up sync.local.server_dir automatically
tw.synchronize()
```

Or directly:

```python
adapter = TaskChampionAdapter(sync_local_server_dir="/mnt/share/taskserver")
adapter.synchronize()
```

### Sync: stable `client_id` auto-generated

When remote sync is configured but `sync.server.client_id` is absent,
a UUID is generated and written to `.taskrc` automatically. The same ID
is reused in all subsequent sessions, preventing duplicate client registrations.

### In-memory adapter for tests

`TaskChampionAdapter` supports an in-memory database — no filesystem needed:

```python
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
from taskwarrior import TaskWarrior

tw = TaskWarrior(adapter=TaskChampionAdapter(data_location=None))
# Fully isolated, nothing written to disk
```

### `apply_filter(now=)` for deterministic tests

The public filter function accepts a `now` argument for time-sensitive tests:

```python
from datetime import datetime, timezone
from taskwarrior.adapters.tc_filter import apply_filter

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
results = apply_filter(tasks, "+OVERDUE", now=NOW)
```

---

## Limitations of the TC adapter vs CLI adapter

| Feature | TC adapter (default) | CLI adapter (`task_cmd="task"`) |
|---------|----------------------|--------------------------------|
| CRUD (add / modify / done / delete) | ✅ | ✅ |
| Date-range filters | ✅ | ✅ |
| Virtual tags | ✅ (28 computed, 1 selector, 1 stub) | ✅ |
| `task` binary required | ❌ | ✅ |
| Urgency score | ❌ always `None` | ✅ |
| OR / AND filters | ❌ | ✅ |
| Parenthesised filter expressions | ❌ | ✅ |
| Remote sync (TC protocol) | ✅ `sync_to_remote` | ✅ `task sync` |
| Local directory sync | ✅ `sync_to_local` | ✅ `task sync` |
| GCP sync | ✅ `sync_to_gcp` | ✅ `task sync` |
| Context & UDA management | ✅ (`.taskrc` writes) | ✅ |

For features in the ❌ column, use `TaskWarrior(task_cmd="task")`.

---

## Migration checklist

```python
# ✅ 1. Update the constructor call
tw = TaskWarrior(task_cmd="task")    # keep CLI adapter, or:
tw = TaskWarrior()                   # switch to TC adapter (no binary)

# ✅ 2. Fix positional task_cmd usage
# Before: TaskWarrior("/usr/bin/task")
TaskWarrior(task_cmd="/usr/bin/task")

# ✅ 3. Guard get_info() access
info = tw.get_info()
if info["task_cmd"]:
    print(info["task_cmd"])

# ✅ 4. Update sync keys in .taskrc
# sync.server.url   → sync.server.origin
# sync.client.id    → sync.server.client_id

# ✅ 5. Remove urgency-dependent logic (TC adapter) or switch to CLI
task = tw.get_task(1)
if task.urgency is not None:   # guard
    ...

# ✅ 6. Update ContextService / UdaService if used directly
# ContextService(config_store, adapter=adapter)   # new order
# UdaService(config_store, adapter=adapter)       # new order
```
