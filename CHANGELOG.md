# Changelog

All notable changes to pytaskwarrior will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
