# Changelog

All notable changes to pytaskwarrior will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
