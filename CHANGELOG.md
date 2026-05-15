# Changelog

All notable changes to pytaskwarrior will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-05-15

**Major release.** The default backend is now `TaskChampionAdapter` — direct SQLite
access via [taskchampion-py](https://github.com/GothenburgBitFactory/taskchampion-py).
The `task` binary is no longer required for any operation.

### Breaking Changes

#### `TaskWarrior()` default backend changed

`TaskWarrior()` now creates a `TaskChampionAdapter` instead of a `TaskWarriorAdapter`.

```python
# Before (2.x): required the task binary
tw = TaskWarrior()              # → TaskWarriorAdapter (CLI)

# After (3.0): no binary needed
tw = TaskWarrior()              # → TaskChampionAdapter (direct SQLite)
tw = TaskWarrior(task_cmd="task")  # → TaskWarriorAdapter (explicit CLI mode)
```

**Migration:** Add `task_cmd="task"` to your `TaskWarrior()` call if you need the CLI adapter.

#### `TaskWarrior.__init__` signature: `task_cmd` default changed

`task_cmd` changed from `str = "task"` to `str | None = None`.

| Before | After |
|--------|-------|
| `TaskWarrior(task_cmd="task")` | unchanged ✅ |
| `TaskWarrior()` | now uses TC adapter (no CLI) |
| `TaskWarrior("/usr/bin/task")` | `TaskWarrior(task_cmd="/usr/bin/task")` |

Note: `task_cmd` was the first positional argument.  
**If you were calling `TaskWarrior("task")` positionally, add the keyword: `TaskWarrior(task_cmd="task")`.**

#### `TaskWarrior.get_info()` shape change

The `"version"` key has been **removed** from the dict. `info["task_cmd"]` and
`info["options"]` are `None` when the TC adapter is active (the default).
Use `"backend_version"` for the version string.

```python
info = tw.get_info()
# Before (2.x / 3.0-pre): info["version"] → "3.4.0"  |  info["task_cmd"] → str
# After (3.0): "version" key no longer exists — KeyError if accessed
#              info["backend_version"] → version string (always present)
#              info["backend_type"]    → "taskchampion" or "taskwarrior-cli"
#              info["task_cmd"]        → None for TC adapter
```

**Migration:** Replace `info["version"]` with `info["backend_version"]`.
Guard `info["task_cmd"]` with `if info["task_cmd"]` before using.

#### `ContextService.__init__` signature simplified

The `adapter` parameter has been removed. Services write directly to `.taskrc`
via `ConfigStore` — no adapter is needed.

```python
# Before (2.x)
ContextService(adapter, config_store)

# After (3.0)
ContextService(config_store)
```

**Migration:** Remove the `adapter` argument. `ContextService` is an internal
class; use the `TaskWarrior` facade methods (`tw.define_context()`,
`tw.get_contexts()`, etc.) for all context operations.

#### `UdaService.__init__` signature simplified

Same change as `ContextService`:

```python
# Before (2.x)
UdaService(adapter, config_store)

# After (3.0)
UdaService(config_store)
```

#### `TaskWarrior.context_service` and `.uda_service` properties removed

The `context_service` and `uda_service` properties no longer exist on
`TaskWarrior`. Use the facade methods directly:

| Before (via property) | After (facade method) |
|---|---|
| `tw.context_service.define_context(ctx)` | `tw.define_context(ctx)` |
| `tw.context_service.get_contexts()` | `tw.get_contexts()` |
| `tw.context_service.apply_context(name)` | `tw.apply_context(name)` |
| `tw.context_service.get_current_context()` | `tw.get_current_context()` |
| `tw.context_service.has_context(name)` | `tw.has_context(name)` |
| `tw.context_service.delete_context(name)` | `tw.delete_context(name)` |
| `tw.context_service.unset_context()` | `tw.unset_context()` |
| `tw.uda_service.define_uda(uda)` | `tw.define_uda(uda)` |
| `tw.uda_service.delete_uda(uda)` | `tw.delete_uda(uda)` |
| `tw.uda_service.update_uda(uda)` | `tw.define_uda(uda)` |
| `tw.uda_service.get_udas()` | `tw.get_udas()` |
| `tw.uda_service.get_uda_names()` | `tw.get_uda_names()` |

**Migration:** Replace all `tw.context_service.*` and `tw.uda_service.*` calls with the
corresponding `tw.*` facade methods shown above.

#### `taskwarrior.version` alias removed

The `version` module-level alias is removed. Use `__version__` instead:

```python
# Before
from taskwarrior import version

# After
from taskwarrior import __version__
```

#### `taskchampion-py` minimum version bumped to `3.0.1.1`

The dependency `taskchampion-py` is now pinned to `>=3.0.1.1` (was `>=2.0.2`).
This version tracks the taskchampion Rust crate `3.0.1` and requires building the
fork from `tmp/taskchampion-py-fork/` until it is published upstream.

The fork is built with the `server-local` feature enabled, adding support for
local directory sync (`sync_to_local`).

#### Sync config key names align with TaskWarrior 3.x

If you were using sync keys from an earlier pytaskwarrior 3.0 pre-release, update
your `.taskrc`:

| Old (incorrect) | New (TW 3.x standard) |
|---|---|
| `sync.server.url` | `sync.server.origin` |
| `sync.client.id` | `sync.server.client_id` |
| `sync.encryption.secret` | unchanged ✅ |

---

### Added

#### Direct `.taskrc` writes — no CLI required

`ConfigStore` now supports writing configuration:

- `ConfigStore.set_value(key, value)` — upsert any key in `.taskrc`
- `ConfigStore.delete_value(key)` — remove a key from `.taskrc`
- `ConfigStore.data_location` — property returning the effective data directory
  (constructor arg → `rc.data.location` in taskrc → `~/.task`)

`ContextService` and `UdaService` use `ConfigStore` directly for all writes.
The `task` binary is no longer called for `define_context`, `apply_context`,
`define_uda`, `delete_uda`, or any configuration change.

#### Date-range filter expressions

New filter tokens in `tc_filter.py`:

```python
tw.get_tasks("due.before:tomorrow")
tw.get_tasks("due.after:eom")
tw.get_tasks("due.by:friday")          # inclusive
tw.get_tasks("scheduled.after:today")
tw.get_tasks("wait.before:now")
```

Supported fields: `due`, `wait`, `scheduled`, `until`, `entry`, `modified`  
Supported operators: `before` (strict `<`), `after` (strict `>`), `by` (`<=`), `not` (`!=`)  
Threshold is resolved via `DateResolver` — all TW date expressions supported.

#### Virtual tags — 30 tags supported in pure Python

`+TAG` / `-TAG` filter tokens for all standard TaskWarrior virtual tags:

| Category | Tags |
|----------|------|
| Date | `+OVERDUE`, `+DUE`, `+DUETODAY`, `+TODAY`, `+TOMORROW`, `+YESTERDAY`, `+WEEK`, `+MONTH`, `+QUARTER`, `+YEAR` |
| Status | `+PENDING`, `+COMPLETED`, `+DELETED`, `+WAITING`, `+ACTIVE` |
| Dependencies | `+BLOCKED`, `+UNBLOCKED`, `+BLOCKING` |
| Task state | `+SCHEDULED`, `+UNTIL`, `+READY`, `+TAGGED`, `+ANNOTATED`, `+PRIORITY`, `+PROJECT`, `+PARENT`, `+CHILD`, `+UDA`, `+ORPHAN` |
| Special | `+LATEST` (keep only the most recently created task) |

```python
tw.get_tasks("+OVERDUE")
tw.get_tasks("+READY -BLOCKED")
tw.get_tasks("+DUE project:work")
tw.get_tasks("+WEEK +PRIORITY")
```

#### Compound date expressions in `DateResolver`

`DateResolver` (and `task_calc`) now supports expressions with spaces:

```python
tw.task_calc("now + P1D")      # ISO duration
tw.task_calc("today + 3d")     # compact
tw.task_calc("eom - P1W")      # subtract
tw.task_calc("now + 2weeks")   # TW shorthand
# Filter expressions
tw.get_tasks("due.before:now + P7D")
```

#### `apply_filter(now=)` parameter

`apply_filter()` accepts an optional `now` parameter for deterministic testing
of date-based filters and virtual tags.

#### Sync config auto-read from `.taskrc`

When using the default `TaskChampionAdapter`, sync configuration is read
automatically from `.taskrc` using the standard TaskWarrior 3.x key names:

```ini
# Remote sync (taskchampion sync server)
sync.server.origin=https://taskchampion.example.com
sync.server.client_id=11111111-2222-3333-4444-555555555555
sync.encryption.secret=my-secret

# Local sync (directory-based)
sync.local.server_dir=/path/to/shared/server_dir
```

Both remote and local sync are supported. If `sync.server.origin` is set but
`sync.server.client_id` is absent, a stable UUID is generated and persisted to
`.taskrc` automatically.

No changes required — `tw.synchronize()` and `tw.is_sync_configured()` work as before.

#### `TaskChampionAdapter` — local directory sync

`TaskChampionAdapter` now accepts a `sync_local_server_dir` parameter for
taskchampion-style local directory sync:

```python
adapter = TaskChampionAdapter(sync_local_server_dir="/path/to/server_dir")
adapter.synchronize()
```

`sync_local_server_dir` takes precedence over `sync_server_url` when both are set.
Requires the `server-local` feature in the `taskchampion-py` fork.

#### Stable `sync.server.client_id` auto-generated and persisted

When remote sync (`sync.server.origin`) is configured but no `sync.server.client_id`
exists in `.taskrc`, a stable UUID is generated and written to `.taskrc` automatically.
This prevents each session from registering as a new client with the sync server.



Now includes `TASKWARRIOR_VIRTUAL_TAGS` (30 names) alongside user tags.

#### Virtual tags extracted to `utils/virtual_tags.py`

`TASKWARRIOR_VIRTUAL_TAGS` and `TASKWARRIOR_VIRTUAL_TAG_SET` are now in
`taskwarrior.utils.virtual_tags` (previously only in `taskwarrior_adapter`).

---

### Changed

- `ContextService` and `UdaService` no longer call the `task` CLI for any write
  operation; they write directly to `.taskrc` via `ConfigStore`.
- `TaskWarrior.__init__`: services are always instantiated regardless of whether
  the CLI adapter is available.
- The `context_service` and `uda_service` properties have been **removed** from
  `TaskWarrior`. Use the facade methods directly (e.g. `tw.define_context()`,
  `tw.get_udas()`). See the **Breaking Changes** section above for the full mapping.
- `task_calc()` docstring updated: compound expressions with spaces are now supported.
- `get_tags(include_virtual_tags=True)`: now returns TW virtual tag names (not TC
  internal synthetic tag strings like `Synthetic(Pending)`).

---

### Migration Guide (2.x → 3.0)

```python
# 1. No-arg constructor now uses TC adapter
tw = TaskWarrior()                    # was CLI, now TC (no binary)
tw = TaskWarrior(task_cmd="task")     # explicit CLI mode

# 2. get_info(): "version" key removed — use backend_version
info = tw.get_info()
print(info["backend_version"])        # always present
if info["task_cmd"]:                  # guard before use
    print(info["task_cmd"])
print(info["backend_type"])           # "taskchampion" or "taskwarrior-cli"
# info["version"]  →  KeyError — key is gone; migrate to info["backend_version"]

# 3. Service constructors (internal use only)
# ContextService(config_store)   # adapter removed
# UdaService(config_store)       # adapter removed

# 4. context_service / uda_service properties removed — use facade methods
# tw.context_service.define_context(ctx)  →  tw.define_context(ctx)
# tw.uda_service.define_uda(uda)          →  tw.define_uda(uda)
# (see breaking changes section for full mapping)

# 5. version alias removed — use __version__
from taskwarrior import __version__   # not: version

# 6. New filter features
tw.get_tasks("+OVERDUE")
tw.get_tasks("due.before:tomorrow")
tw.get_tasks("+READY project:work")
```

### Added

- Added TaskWarrior.get_udas() and UdaRegistry.get_udas(): public API to retrieve full UDA definitions (UdaConfig objects) from the in-memory registry.

## [2.0.5]

### Added

- UdaConfig now accepts `type` as an alias for `uda_type` when instantiated from a dict (e.g., from YAML or user config). This allows `UdaConfig(**uda)` to work seamlessly with user-supplied mappings using the TaskWarrior convention.
- Harmonized UDA deletion and facade methods: UdaService.delete_uda now maps the library's internal `uda_type` field to TaskWarrior's `uda.<name>.type` key and removes the correct configuration keys; public facade methods `tw.define_uda`, `tw.update_uda` and `tw.delete_uda` were added to simplify UDA management.
- Documentation review and improvements: updated examples to use the public TaskWarrior façade, added guidance on UDA `uda_type` vs TaskWarrior `type`, and added tag helper examples (`tw.get_tags`, `tw.get_context_tags`) for clarity and consistency.

## [2.0.4]

### Added

- Added TaskID utility class and TaskRef type alias to unify task references (`int` id, `UUID`, or `TaskID`). Exported `TaskID` from the public API and added unit tests.
- Updated TaskWarrior and adapter method signatures to accept `TaskRef` (int, UUID, or TaskID) for task references.

### Changed

- Documentation: swept and updated examples and how-tos to use the public API and clarified terminology around UDAs and tags.
- API: parameter name changed in several methods from `task_id_or_uuid` to `task_id`/`task_ref`. Positional calls are unaffected; callers using the old keyword name may need to update (see migration notes below).

### Tests

- Added unit tests for `TaskID` (tests/unit/test_task_id.py). Full test suite passes locally.

### Notes / Migration

- Backwards compatibility: `TaskID` constructor accepts `str`, `int`, and `UUID` to remain compatible with existing call-sites. However, some tests and user code that relied on the `task_id_or_uuid` keyword argument may need to update to the new `task_id`/`task_ref` keyword or use positional arguments.


## [2.0.3] - 2026-04-10

### Changed

- add get_tags()
- add tw.get_context_tags(); tags beginning with `@`

## [2.0.2] - 2026-04-06

### Changed

- Bumped package version to 2.0.2 in pyproject.toml.

## [2.0.1] - 2026-04-07

### Fixed

- UDA predefined values fixed

## [2.0.0] - 2026-04-06

### Breaking Changes

- **`UdaConfig.type` renamed to `UdaConfig.uda_type`**: The `type` field in `UdaConfig` has been renamed to avoid conflicts with Python's built-in `type` function. This is a **major breaking change** requiring code updates.
- **`define_context` signature changed**: `define_context` now accepts a single ContextDTO instance (`ContextDTO(name, read_filter, write_filter)`) instead of positional name/read/write parameters. This is a breaking API change in 2.0.0.
  - **Example:** `UdaConfig(name="severity", type=UdaType.STRING)` → `UdaConfig(name="severity", uda_type=UdaType.STRING)`
  - The `.taskrc` configuration format remains unchanged (parser automatically maps config `type` to DTO `uda_type`).
- **Centralize UDA discovery via ConfigStore.get_udas()**: UdaRegistry and UdaService no longer parse the `.taskrc` file directly. Use `ConfigStore.get_udas()` (returns `list[UdaConfig]`) and `registry.register_udas()` to populate the in-memory registry. This is a breaking change that may require updates to registry initialization in consumer code.

### Changed

- All documentation, tests, and examples updated to use `uda_type` instead of `type`.
- `UdaService.define_uda()` and `UdaService.update_uda()` now use the `uda_type` field.
- UDA discovery removed legacy file parsing paths; parsing moved to `src/taskwarrior/config/uda_parser.py`.


## [1.2.0] - 2026-03-28

### Added

- **`Context in get_info`** — TaskWarrior.get_info() now includes `current_context` and `current_context_details` (name, read_filter, write_filter, active).

- **`TaskConfigurationError`** — new exception for environment and configuration errors:
  binary not found in PATH, taskrc file missing or unreadable.
- **`TaskOperationError`** — new exception for write-operation failures on existing tasks
  (delete, purge, done, start, stop, annotate).
- All six exceptions now **exported from the top-level package**:
  `TaskWarriorError`, `TaskNotFound`, `TaskValidationError`, `TaskSyncError`,
  `TaskConfigurationError`, `TaskOperationError`.
- **`TaskWarrior.synchronize()`** now runs `task sync` via the CLI.
  Both local (`sync.local.server_dir`) and remote (`sync.server.origin`) sync backends are
  supported through TaskWarrior's built-in sync command.
- `TaskWarrior.is_sync_configured()` returns `True` when any `sync.*` key is present in taskrc.

### Changed

- Exception hierarchy unified: 13 semantic fixes throughout the codebase ensure the right
  exception is raised in the right context.
  - `TaskValidationError` → `TaskConfigurationError` for binary not found / taskrc errors
  - `TaskNotFound` → `TaskOperationError` for operation failures on existing tasks
  - `OSError` / `subprocess.SubprocessError` → wrapped in `TaskWarriorError` to preserve exception contract
  - All JSON parse errors now use `TaskWarriorError` instead of domain-specific exceptions
- `synchronize()` is **no longer a no-op**: the façade now calls `self.adapter.synchronize()`,
  which in turn runs `task sync`. Raises `TaskSyncError` if sync is not configured or fails.
- `get_tasks()` now respects the active context's `read_filter` — when a context is applied,
  its `read_filter` is combined with the user-provided filter using AND so listings are scoped
  correctly (e.g. `project:work and (priority:H)`).
- Enhanced error coverage: all file I/O, JSON parsing, and subprocess operations now properly
  protected with appropriate exception handling.

### Tests

- `uv run pytest -q` (164 passed, 0 failed)
- New `test_adapter_sync.py` validates sync behavior via `task sync` CLI.
- Updated sync tests to reflect new implementation (CLI-based, no external dependencies).
- `test_task_warrior_error_inheritance` extended to verify exception hierarchy.

## [1.1.1] - 2026‑03‑07
### Added
- Automated publishing to PyPI via GitHub Actions (trusted publishing with OIDC).
- Updated documentation links to reflect the new release.

### Changed
- Bumped package version to 1.1.1 (patch release).

### Fixed
- Minor typo fixes in the README badge URLs.

## [1.1.0] - 2026-03-06
### Breaking Changes

- **`define_context` signature changed**: now requires explicit `read_filter` and `write_filter` named
  parameters. The old single-filter positional form no longer works.

  ```python
  # Before (1.0.0)
  tw.define_context(ContextDTO(name="work", read_filter="project:work", write_filter="project:work"))

  # After
  tw.define_context(ContextDTO(name="work", read_filter="project:work", write_filter="project:work"))
  ```

  **Migration**: set `write_filter` to the same value as the old single filter, or to `""` for a
  read-only context (tasks created while the context is active won't inherit a project).

- **`get_tasks` signature changed**: `filter_args` renamed to `filter`; status exclusion is now
  controlled by dedicated parameters instead of being part of the filter string.

  ```python
  # Before (1.0.0)
  tw.get_tasks()                                       # all non-deleted/completed
  tw.get_tasks("project:work")                         # still works (positional)
  tw.get_tasks(filter_args="status:completed")         # ← broken keyword

  # After
  tw.get_tasks()                                       # same default behaviour
  tw.get_tasks("project:work")                         # unchanged
  tw.get_tasks(include_completed=True)                 # include completed tasks
  tw.get_tasks("project:work", include_deleted=True)   # include deleted
  tw.get_tasks(filter="project:work", include_completed=True)  # explicit keyword
  ```

  **Key improvement**: compound `or`/`and` filters no longer need manual parentheses —
  `get_tasks("project:dmc or project:pro")` now works correctly.

### Added

- **`get_tasks(filter, include_completed, include_deleted)`**: new parameters give fine-grained
  control over status exclusion without requiring raw filter strings.
- **Auto-wrapping of filter expressions**: compound filters passed to `get_tasks` are automatically
  wrapped in parentheses so that `or`/`and` expressions are evaluated correctly by Taskwarrior.
- **`TaskInputDTO.recur` accepts ISO-8601 durations**: in addition to `RecurrencePeriod` enum values
  and Taskwarrior shorthand strings (e.g. `"2weeks"`), you can now pass ISO-8601 duration strings
  such as `"P1D"`, `"P3DT4H"`, or `"PT30M"`.  Note: the week designator `PnW` (e.g. `"P2W"`) is not
  yet validated by the built-in regex; use `"P14D"` or `"2weeks"` instead.

### Fixed

- **`run_task_command` option ordering**: `rc:` and `rc.data.location=` options are now placed
  *before* the command and filter arguments in the subprocess call, which fixes cases where
  TaskWarrior silently ignored the custom taskrc or data location.

## [1.0.0] - 2026-02-26

**PyTaskWarrior 1.0.0** is a complete production-ready rewrite with professional-grade code quality: 132 tests (96% coverage), strict type checking (mypy), zero linting errors (ruff), and clean architecture (adapters/services/DTOs). Full async-ready subprocess handling, comprehensive error recovery, and PEP 561 type hints.

### Breaking Changes

- **Python version**: Now requires Python 3.12+ (modern language features)
- **TaskWarrior version**: Requires TaskWarrior 3.4+ (uses `json.array=TRUE`)
- **Complete API rewrite**: New `TaskWarrior` facade with adapters/services; `TaskInputDTO`/`TaskOutputDTO` replace dict-based responses
- **UdaRegistry removed singleton**: Each instance has its own `_udas` dictionary (thread-safe, no global state)

### Added

- **Type-safe operations**: `TaskInputDTO` and `TaskOutputDTO` with Pydantic v2 validation
- **Context management**: Define, apply, switch, and delete TaskWarrior contexts; `ContextDTO.active` reflects current context
- **UDA support**: Full User Defined Attributes registry with validation and discovery
- **Recurring tasks**: `RecurrencePeriod` enum (DAILY/WEEKLY/MONTHLY/YEARLY/QUARTERLY/SEMIANNUALLY/HOURLY/MINUTELY/SECONDLY) + support for custom strings ("2weeks", "10days", etc.)
- **Task annotations**: Create and retrieve task annotations with ISO timestamps
- **Date utilities**: `task_calc()` for date arithmetic and `date_validator()` for validation
- **Enums**: `TaskStatus`, `Priority`, `RecurrencePeriod` for type-safe task properties
- **Production hardening**:
  - `subprocess.run()` timeout (30s) to prevent hangs
  - Atomic `add_task()`: parses ID from stdout (no race conditions with `+LATEST`)
  - Atomic date validation: regex-based ISO format detection (not exit code)
  - Proper exception hierarchy: `TaskWarriorError`, `TaskNotFound`, `TaskValidationError`
  - Exception chaining (`raise ... from e`) for better debugging
- **Type hints**: PEP 561 `py.typed` marker for full IDE/type-checker support
- **Test coverage**: 132 unit tests (96% coverage) + 35 subprocess-mocked tests (no binary dependency)
- **Code quality**: ruff (zero errors), mypy strict mode, pytest with coverage reporting

### Changed

- **Architecture**: Clean separation (adapters → services → main facade)
- **Error handling**: No bare `except Exception`; specific `OSError`/`subprocess.SubprocessError` catches
- **Config expansion**: Paths support both `~` and `$HOME` environment variables
- **Project metadata**: Author, license, documentation URLs, and full PyPI classifiers
- **CI/CD**: GitHub Actions workflows (pytest matrix 3.12–3.13, ruff, mypy, coverage reports)

### Fixed

- Circular import issues resolved
- `has_context()` returns correct boolean (not exception)
- UdaRegistry no longer shares state across instances
- `task_date_validator()` now correctly distinguishes valid/invalid dates
- Subprocess errors (timeout, OSError) properly caught and re-raised

### Deprecated

- Direct use of plain dicts for tasks; use `TaskInputDTO`/`TaskOutputDTO` instead

### Migration Guide

**From 0.3.0 → 1.0.0:**

```python
# Before (0.3.0)
task_dict = {"description": "Task", "priority": "H"}
tw.add_task(task_dict)

# After (1.0.0)
from taskwarrior import TaskInputDTO, Priority
task = TaskInputDTO(description="Task", priority=Priority.HIGH)
tw.add_task(task)

# Retrieve tasks
tasks = tw.get_tasks()  # Returns TaskOutputDTO[]
for task in tasks:
    print(task.description, task.uuid, task.status)
```

See [README.md](README.md) for full API examples.

## [0.2.0] - 2025-06-29

### Added

- Basic task operations (add, get, modify, delete, done)
- Initial TaskWarrior wrapper

## [0.1.0] - 2025-06-14

### Added

- Initial release
- Basic proof of concept
