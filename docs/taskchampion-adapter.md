# TaskChampion Adapter

The `TaskChampionAdapter` is the **default backend** for pytaskwarrior.
It provides direct access to TaskWarrior's SQLite database via
[taskchampion-py](https://github.com/GothenburgBitFactory/taskchampion-py) —
Rust bindings to the taskchampion storage engine.

No `task` binary is required.

## Architecture

```
TaskWarrior (facade)
├── TaskChampionAdapter        ← default CRUD backend
│   ├── taskchampion-py        ← Rust PyO3 bindings (taskchampion 3.0.1)
│   │   └── Replica            ← reads/writes ~/.task/taskchampion.sqlite
│   ├── tc_filter.py           ← Python filter engine
│   │   ├── Date-range tokens  ← due.before:X, scheduled.after:X, …
│   │   └── Virtual tags       ← +OVERDUE, +DUE, +TODAY, +BLOCKED, …
│   └── tc_converter.py        ← TaskOutputDTO ↔ TC Task conversion
├── ConfigStore                ← reads/writes ~/.taskrc
│   ├── ContextService         ← define/apply/delete contexts (no CLI)
│   └── UdaService             ← define/delete UDAs (no CLI)
└── TaskWarriorAdapter         ← optional CLI fallback (task_cmd="task")
```

## Usage

```python
from taskwarrior import TaskWarrior

# Default: TaskChampionAdapter on ~/.task
tw = TaskWarrior()

# Custom data directory
tw = TaskWarrior(data_location="/path/to/mydata")

# In-memory (for tests)
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
tw = TaskWarrior(adapter=TaskChampionAdapter(data_location=None))

# Read-only access (safe for concurrent readers)
from taskwarrior.adapters import AccessMode
tw = TaskWarrior(adapter=TaskChampionAdapter(access_mode=AccessMode.ReadOnly))

# Explicit CLI mode (requires task binary)
tw = TaskWarrior(task_cmd="task")
```

## Thread Safety

`TaskChampionAdapter` is **bound to the thread that created it**.  The underlying
`Replica` object (a PyO3 `#[pyclass(unsendable)]`) must be accessed exclusively
from its owner thread.

Starting with pytaskwarrior 3.1, the adapter enforces this at the Python level:
every method that touches the `Replica` calls an internal `_check_thread_affinity()`
guard on entry.  If called from the wrong thread, it raises `RuntimeError`
immediately — **a clear Python error instead of an opaque Rust panic**.

A `threading.Lock` is also held for the duration of each operation, providing
internal consistency for callers sharing one adapter across coroutines on the
same asyncio event loop.

**Rule: one `TaskChampionAdapter` (and its `Replica`) per thread.**

```python
import threading
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter

adapter = TaskChampionAdapter()

def worker():
    adapter.get_tasks()  # ❌ raises RuntimeError — wrong thread

t = threading.Thread(target=worker)
t.start()
t.join()
# RuntimeError: TaskChampionAdapter instance was created on thread 1
# but is being accessed from thread 3. Create a separate
# TaskChampionAdapter instance per thread…
```

### FastAPI patterns

```python
# ✅ async def — runs on the event-loop thread; one shared adapter is safe
adapter = TaskChampionAdapter()

@app.get("/tasks")
async def list_tasks():
    return adapter.get_tasks()

# ✅ sync def — each request runs in a worker thread; use thread-local storage
import threading
_local = threading.local()

def get_adapter():
    if not hasattr(_local, "adapter"):
        _local.adapter = TaskChampionAdapter()
    return _local.adapter

@app.get("/tasks")
def list_tasks():
    return get_adapter().get_tasks()

# ✅ Read-only concurrent access — one ReadOnly adapter per thread
@app.get("/tasks")
def list_tasks():
    # short-lived per-request adapter is fine for reads
    adapter = TaskChampionAdapter(access_mode=AccessMode.ReadOnly)
    return adapter.get_tasks()
```

### SQLite concurrency

The underlying SQLite database uses `journal_mode=WAL`, which allows multiple
concurrent readers alongside a single writer. A `busy_timeout` of 5 seconds
means a second writer will wait rather than fail immediately.

`AccessMode.ReadOnly` opens the database read-only — no write lock is ever
acquired, making it safe for many concurrent connections.

## Metrics

Each `TaskChampionAdapter` instance records cumulative operation metrics.
Retrieve a snapshot with `get_metrics()`:

```python
adapter = TaskChampionAdapter()
adapter.add_task(TaskInputDTO(description="Buy milk"))
adapter.get_tasks()

print(adapter.get_metrics())
# {
#   'calls_total': 2,
#   'errors_total': 0,
#   'avg_wait_seconds': 0.0,
# }
```

| Key | Description |
|-----|-------------|
| `calls_total` | Total number of operations that went through `_locked_call` |
| `errors_total` | Number of those that raised an exception |
| `avg_wait_seconds` | Average time (seconds) spent waiting to acquire the internal lock |

Metrics are useful for diagnosing lock contention in high-concurrency
same-thread scenarios (e.g., many asyncio coroutines on one event loop).
The lock is non-reentrant and held only briefly, so contention should
normally be negligible.

## Supported Filter Syntax

The filter engine (`tc_filter.py`) supports a subset of TaskWarrior's filter syntax,
applied as a Python post-query pass over all tasks.

| Token | Example | Notes |
|-------|---------|-------|
| `+tag` / `-tag` | `+urgent -someday` | User tags |
| `+VIRTUAL` | `+OVERDUE`, `-BLOCKED` | 28 virtual tags supported |
| `status:X` | `status:pending` | pending / completed / deleted / waiting |
| `status.not:X` | `status.not:completed` | Negated status |
| `project:X` | `project:work` | Hierarchical: matches `work.reports` too |
| `uuid:X` | `uuid:abc-123` | Exact UUID |
| `priority:X` | `priority:H` | H / M / L |
| `parent:X` | `parent:uuid` | Recurring task parent |
| `field.before:X` | `due.before:tomorrow` | Strict less-than |
| `field.after:X` | `scheduled.after:eom` | Strict greater-than |
| `field.by:X` | `due.by:friday` | Less-than-or-equal |
| `field.not:X` | `due.not:today` | Not equal (tasks with no date also match) |
| `+LATEST` | | Keep only the most recent task |

**Date fields** for range tokens: `due`, `wait`, `scheduled`, `until`, `entry`, `modified`

**Not supported** (requires CLI adapter): `or`, `and`, parenthesised expressions.

## Virtual Tags

All 30 virtual tags are recognized. 28 are computed in pure Python; 2 have special behaviour:

| Tag | Computation |
|-----|-------------|
| `OVERDUE` | `due < now` and task is pending/waiting |
| `DUE` | `due ≤ now + 7 days` |
| `DUETODAY` | due date is today |
| `TODAY` | due today or scheduled today |
| `TOMORROW` | due tomorrow |
| `YESTERDAY` | due yesterday |
| `WEEK` | `due ≤ now + 7 days` |
| `MONTH` | `due < start of next month` |
| `QUARTER` | `due < start of next quarter` |
| `YEAR` | `due < start of next year` |
| `SCHEDULED` | `scheduled` field is set |
| `UNTIL` | `until` field is set |
| `BLOCKED` | depends on at least one pending task |
| `UNBLOCKED` | not blocked |
| `BLOCKING` | other tasks depend on this one |
| `ACTIVE` | task has been started |
| `WAITING` | wait date is in the future |
| `PENDING` | status is pending (not waiting) |
| `COMPLETED` | status is completed |
| `DELETED` | status is deleted |
| `READY` | pending, not blocked, not scheduled in future |
| `TAGGED` | has at least one user tag |
| `ANNOTATED` | has at least one annotation |
| `PRIORITY` | has a priority set |
| `PROJECT` | belongs to a project |
| `PARENT` | is a recurrence template |
| `CHILD` | is a recurrence instance |
| `UDA` | has at least one UDA field set |
| `ORPHAN` | ⚠ not computed — always `False` (requires CLI for full support) |
| `LATEST` | **special** — `+LATEST` keeps only the most recently created task from the result set |

## Date Expression Support

Date expressions are resolved by `DateResolver` — no CLI needed:

| Expression | Meaning |
|------------|---------|
| `today`, `tomorrow`, `yesterday` | Calendar days |
| `now` | Current moment |
| `eod`, `eow`, `eom`, `eoy` | End of day/week/month/year |
| `monday` … `sunday` | Next occurrence of weekday |
| `2026-01-15`, `2026-01-15T12:00:00Z` | ISO 8601 |
| `P2W`, `P3D`, `PT4H` | ISO duration (added to now) |
| `now+3d`, `eom-1w`, `today+2h` | Compact relative |
| `now + P1D`, `today + 3d` | Compound with spaces |

## Context and UDA Management

Contexts and UDAs are managed entirely through `.taskrc` — no CLI needed:

```python
from taskwarrior.dto.context_dto import ContextDTO
from taskwarrior.dto.uda_dto import UdaConfig, UdaType

# Contexts — written directly to .taskrc
tw.define_context(ContextDTO(name="work", read_filter="project:work", write_filter="project:work"))
tw.apply_context("work")
tw.unset_context()
tw.delete_context("work")

# UDAs — written directly to .taskrc
tw.define_uda(UdaConfig(name="complexity", uda_type=UdaType.STRING, label="Complexity"))
tw.delete_uda(UdaConfig(name="complexity", uda_type=UdaType.STRING))
```

## Sync Support

Both remote (taskchampion HTTP server) and local directory sync are supported.
Sync configuration is read automatically from `.taskrc`:

```ini
# Remote sync
sync.server.origin=https://taskchampion.example.com
sync.server.client_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
sync.encryption.secret=my-passphrase

# Local sync (alternative)
sync.local.server_dir=/path/to/shared/server
```

```python
tw = TaskWarrior()        # sync config picked up automatically
tw.synchronize()          # runs sync_to_remote or sync_to_local
tw.is_sync_configured()   # True if any sync key is present
```

See **[Synchronization](sync.md)** for the full guide, including direct
`TaskChampionAdapter` usage, troubleshooting, and differences from `task sync`.

## Limitations vs CLI Adapter

| Feature | TC Adapter | CLI Adapter |
|---------|-----------|-------------|
| CRUD operations | ✅ | ✅ |
| Virtual tags | ✅ (Python) | ✅ (native) |
| Date expressions | ✅ (Python) | ✅ (native) |
| OR / AND filters | ❌ | ✅ |
| `task sync` CLI | ❌ | ✅ |
| TC sync protocol | ✅ | ❌ |
| Binary required | ❌ | ✅ |

## Compatibility with taskchampion-py

This library depends on `taskchampion3-py-fork` (version `>= 3.0.1.1`) that
tracks taskchampion `3.0.1`. The package is located at
`tmp/taskchampion-py-dev/` and must be built locally until published upstream:

```bash
uv sync  # builds and installs the package automatically
```

The Python import name is unchanged: `import taskchampion`.
