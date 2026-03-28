# Changelog

All notable changes to pytaskwarrior will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-28

### Added

- **`TaskConfigurationError`** — new exception for environment and configuration errors:
  binary not found in PATH, taskrc file missing or unreadable.
  Replaces `TaskValidationError` in these cases, which was semantically incorrect.
- **`TaskOperationError`** — new exception for write-operation failures on existing tasks
  (delete, purge, done, start, stop, annotate).
  Replaces `TaskNotFound` in these cases; a failed operation is not the same as a missing task.
- All six exceptions are now **exported from the top-level package** (`from taskwarrior import …`):
  `TaskWarriorError`, `TaskNotFound`, `TaskValidationError`, `TaskSyncError`,
  `TaskConfigurationError`, `TaskOperationError`.
- `TaskWarrior.is_sync_configured()` and `TaskWarrior.synchronize()` — the façade now exposes
  the sync backend; `synchronize()` propagates `TaskSyncError` when no backend is configured.

### Changed

- `OSError` / `subprocess.SubprocessError` are now caught in `run_task_command` and wrapped
  in `TaskWarriorError` instead of being re-raised as stdlib exceptions, preserving the
  library's exception contract.
- `ConfigStore._extract_taskrc_config` now raises `TaskConfigurationError` on
  `FileNotFoundError`, `PermissionError`, or any OS-level I/O failure when reading the taskrc.
- `get_task` with a non-zero return code now raises `TaskNotFound` (was `TaskWarriorError`
  with a misleading "not found" message).
- `modify_task` failure now raises `TaskWarriorError` (was `TaskValidationError` — a CLI
  command failure is not a data-validation issue).
- `ContextService._validate_name` now raises `TaskValidationError` for an empty context name
  (was `TaskWarriorError`).
- `UdaRegistry.load_from_taskrc` now raises `TaskConfigurationError` when the taskrc file
  does not exist (was `TaskWarriorError`).
- `get_recurring_instances` and `get_recurring_task` JSON decode errors now raise
  `TaskWarriorError` (was `TaskNotFound` — parsing failure ≠ task not found).
- `add_task` fallback path now raises `TaskWarriorError` (was `RuntimeError`, which broke
  the library exception contract).
- Synchronization via the `TaskWarrior` façade is temporarily disabled due to compatibility
  concerns with py-taskchampion. The original call is preserved as a code comment for easy
  reactivation. `SyncLocal` replica creation is now lazy to avoid side effects at init time.
- `parse_taskwarrior_date` fallback `fromisoformat` call is now wrapped in a proper try/except;
  invalid dates raise `ValueError` with a descriptive message instead of a bare traceback.
- `get_recurring_task` now protects the `json.loads` call with try/except (only method that
  was missing this guard).

### Tests

- `uv run pytest -q` (164 passed, 0 failed)
- Updated all mocked and integration tests to reflect the new exception semantics.
- `test_task_warrior_error_inheritance` extended to verify `TaskConfigurationError` and
  `TaskOperationError` are subclasses of `TaskWarriorError`.

## [1.1.2rc1] - 2026-03-10
### Added
- Added TaskWarrior.is_sync_configured() and TaskWarrior.synchronize() so the façade exposes the existing sync backend; `synchronize()` propagates `TaskSyncError` when no backend is configured or synchronization fails.

### Changed
- Temporarily disabled synchronization via the TaskWarrior façade (TaskWarrior.synchronize()). The original call is preserved as a code comment to allow quick reactivation; this avoids invoking py-taskchampion flows while compatibility is evaluated.
- Made SyncLocal Replica creation lazy (instantiated on first use) to avoid side-effects at instantiation time.

### Fixed
- Updated adapter, UDA, context, and registry tests to the new `ConfigStore`-backed initialization so they no longer rely on removed constructor parameters and private helpers.
- Emulated TaskWarrior CLI interactions in registry/UDA tests, eliminating the need to invoke the real `task` binary while preserving realistic config updates.
### Tests
- `uv run pytest -q` (159 passed, 0 failed)
- Added tests to ensure facade synchronization is a no-op and to support lazy SyncLocal behavior.

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
  tw.define_context("work", "project:work")

  # After
  tw.define_context("work", read_filter="project:work", write_filter="project:work")
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
