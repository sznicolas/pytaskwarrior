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

# Explicit CLI mode (requires task binary)
tw = TaskWarrior(task_cmd="task")
```

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

All 28 virtual tags are computed in pure Python:

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

The default `TaskWarrior()` constructor reads sync credentials from `.taskrc`
and passes them to `TaskChampionAdapter`:

```ini
# .taskrc
sync.server.url=https://taskchampion.example.com
sync.client.id=my-client-id
sync.encryption.secret=my-secret
```

```python
tw = TaskWarrior()        # sync config picked up automatically
tw.synchronize()          # syncs via taskchampion sync protocol
tw.is_sync_configured()   # True if sync.server.url is set
```

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

## Compatibility with taskchampion-py Fork

This library depends on a fork of `taskchampion-py` (version `3.0.1.1`) that
tracks taskchampion `3.0.1`. The fork is located at
`tmp/taskchampion-py-fork/` and must be built locally until merged upstream:

```bash
uv sync  # builds and installs the fork automatically
```
