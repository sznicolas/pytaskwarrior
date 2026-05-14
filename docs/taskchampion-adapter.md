# TaskChampion Adapter

Direct-SQLite access for pytaskwarrior via
[taskchampion-py](https://github.com/GothenburgBitFactory/taskchampion-py)
(PyO3 bindings to the Rust
[taskchampion](https://github.com/GothenburgBitFactory/taskchampion) library).

## Motivation

The default `TaskWarriorAdapter` spawns a `task` subprocess for every
operation.  `TaskChampionAdapter` reads and writes the task database
directly, removing process-spawn overhead and the CLI dependency while
keeping the same `AdapterProtocol` surface.

## Quick start

```python
from taskwarrior.adapters.taskchampion_adapter import TaskChampionAdapter
from taskwarrior.dto.task_dto import TaskInputDTO

adapter = TaskChampionAdapter(data_location="~/.local/share/task")

task = adapter.add_task(TaskInputDTO(description="Buy milk", tags=["errand"]))
print(task.index, task.uuid, task.description)

tasks = adapter.get_tasks(filter="project:home +errand")
adapter.done_task(task.uuid)
```

Use `data_location=None` for an **in-memory** database (useful in tests):

```python
adapter = TaskChampionAdapter()  # in-memory, no file I/O
```

## Constructor parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `data_location` | `str \| Path \| None` | `None` | Path to the taskchampion data directory. `None` = in-memory. |
| `create_if_missing` | `bool` | `True` | Create the DB if the path doesn't exist. |
| `sync_server_url` | `str \| None` | `None` | taskchampion sync server URL. |
| `sync_client_id` | `str \| None` | `None` | Client UUID sent to the sync server. |
| `sync_encryption_secret` | `str \| None` | `None` | Encryption secret for sync. |

## Supported filter syntax

`get_tasks(filter=...)` accepts a **subset** of the TaskWarrior filter language.
Tokens are combined with **AND** logic.

| Token | Example | Meaning |
|---|---|---|
| `+tag` | `+work` | Task must have the tag |
| `-tag` | `-personal` | Task must NOT have the tag |
| `status:X` | `status:pending` | Exact status match |
| `status.not:X` | `status.not:deleted` | Negate status |
| `project:X` | `project:work` | Exact or hierarchical prefix (`work` matches `work.reports`) |
| `uuid:X` | `uuid:abc123…` | Exact UUID match |
| `priority:X` | `priority:H` | Exact priority (H / M / L / "") |
| `parent:X` | `parent:uuid…` | Match recurring-instance parent UUID |
| `+LATEST` | `+LATEST` | Return only the most recently created task |

## Feature parity

### ✅ Fully supported

| Feature | Notes |
|---|---|
| add / modify / get / get_tasks | Full CRUD |
| delete / purge / done / start / stop | All status transitions |
| annotate | Unique timestamps guaranteed |
| tags | User tags: add, remove, diff |
| UDAs | Legacy (`key`) and namespaced (`ns.key`) |
| dependencies | add, remove, diff |
| project | Hierarchical project names |
| recur | Standard `RecurrencePeriod` values |
| scheduled / until | Via raw `set_value` |
| wait (hiding) | `TaskStatus.WAITING` via `is_waiting()` |
| annotations | With collision-safe timestamps |
| get_projects | Scan all tasks |
| get_tags | User and virtual (opt-in) |
| get_recurring_instances | By `parent` UUID |
| `AdapterProtocol` compliance | `isinstance(adapter, AdapterProtocol)` → `True` |

### ⚠️ Partially supported

| Feature | Limitation |
|---|---|
| `recur` output | Non-standard recurrence strings (e.g. `"2weeks"`) are mapped to `None` in `TaskOutputDTO.recur` (the raw value is preserved in the DB) |
| `urgency` | Always `None` — not computed (requires TW urgency formula) |
| Filter expressions | Only the tokens listed above; `due.before:tomorrow`, virtual-tag filters (`+OVERDUE`, `+DUE`), urgency sort, etc. are not supported |

### ❌ Not supported

| Feature | Reason |
|---|---|
| `task_calc("tomorrow")` | Now supported via `DateResolver` — returns ISO 8601 UTC string for common TW expressions |
| `task_date_validator("eom")` | Now returns `True` for all expressions supported by `DateResolver` |
| TW date expressions in input DTOs | Fields like `due="tomorrow"` are resolved by `DateResolver`; compound expressions with spaces (e.g. `"today + 2weeks"`) are still skipped with a warning — use compact form (`"now+2w"`) |
| Hooks (`pre-add`, `on-modify`, …) | Specific to the `task` executable |
| Context / `~/.taskrc` reading | taskchampion doesn't read taskrc; UDA config must be supplied separately |
| Recurrence expansion | taskchampion stores the recur field but doesn't expand instances |
| Thread safety | taskchampion-py Replica is not `Send`/thread-safe |
| Sync (v2) | Requires explicit `sync_server_url`; HTTP taskchampion sync servers supported |

## Hybrid model — facade with `TaskChampionAdapter`

When `TaskWarrior` is initialised with a `TaskChampionAdapter`, the façade
operates in **hybrid mode**: task CRUD goes through SQLite while
configuration services fall back to the CLI.

```
TaskWarrior(adapter=TaskChampionAdapter(...))
│
├─ task CRUD (add/modify/get/done/…)  → TaskChampionAdapter → SQLite
│
├─ context_service                     → TaskWarriorAdapter (CLI) if available
│                                        raises TaskConfigurationError otherwise
│
└─ uda_service                         → TaskWarriorAdapter (CLI) if available
                                         raises TaskConfigurationError otherwise
```

### Which methods require the CLI?

| Category | Requires CLI (`task` binary) |
|---|---|
| Task CRUD (`add_task`, `get_tasks`, …) | ❌ No |
| `task_calc` / `task_date_validator` | ❌ No (handled by `DateResolver`) |
| `context_service.*` | ✅ Yes — raises `TaskConfigurationError` when CLI unavailable |
| `uda_service.*` | ✅ Yes — raises `TaskConfigurationError` when CLI unavailable |
| `synchronize()` | ❌ No (requires sync server config, not CLI) |
| `get_info()` — `task_cmd`, `version` | ⚠️ Present only when CLI adapter available |

### Using the `tw_tc` test fixture

```python
# In tests — no task binary required
def test_something(tw_tc: TaskWarrior):
    task = tw_tc.add_task(TaskInputDTO(description="Buy milk"))
    assert task.description == "Buy milk"
```

The `tw_tc` fixture (defined in `tests/conftest.py`) creates a `TaskWarrior`
backed by an in-memory `TaskChampionAdapter`.  It is safe to use in any CI
environment without installing TaskWarrior.

## Date expression support (`DateResolver`)

`TaskChampionAdapter` resolves TaskWarrior date expressions via
`taskwarrior.utils.date_resolver.resolve_date()` — no `task` binary needed.

| Expression | Example | Supported |
|---|---|---|
| ISO 8601 | `"2026-01-15T14:30:00Z"` | ✅ |
| Named | `"now"`, `"today"`, `"tomorrow"`, `"yesterday"` | ✅ |
| End-of-period | `"eod"`, `"eow"`, `"eom"`, `"eoy"` | ✅ |
| Compact relative | `"now+2d"`, `"now-1w"`, `"now+1m"` | ✅ |
| ISO 8601 duration | `"P2W"`, `"P3D"`, `"P1M"`, `"P1Y"` | ✅ |
| Weekday names | `"monday"` … `"sunday"` (next occurrence) | ✅ |
| Compound arithmetic | `"today + 2weeks"`, `"due.before:tomorrow"` | ❌ (use compact form) |

## Evaluation 2 — taskchampion 3.x fork

A second evaluation (`P2`) targets a fork of `taskchampion-py` updated to
the `taskchampion` 3.0.2-pre Rust crate.  Key differences vs 2.0.2:

| Change | Impact |
|---|---|
| Entire `Replica` API becomes `async` | Requires `tokio::runtime::Runtime::block_on()` bridge in PyO3 |
| `Replica<S: Storage>` becomes generic | Requires `Box<dyn Storage + Send + Sync>` type-erasure |
| New `pending_tasks()` method | `get_tasks(include_completed=False, include_deleted=False)` becomes O(pending) instead of O(all) |
| Flat UDA API: `get_user_defined_attribute(key)` | Replaces `get_uda(ns, key)` namespace pattern |
| New sync backends: AWS S3, Git | Exposed via new `sync_to_aws` / `sync_to_git` methods |
| `Status::Unknown(String)` payload | Better handling of unknown status values |
| MSRV bump: 1.83 → 1.91.1 | Requires Rust toolchain upgrade |

See `tmp/taskchampion-py-fork/` (Phase 2) for the fork implementation.
