# PyTaskWarrior 1.2.0 Release Notes

## Overview

**PyTaskWarrior 1.2.0** delivers a fully consistent exception hierarchy, new public exception
classes, and better error coverage throughout the library.

### Key Highlights

- **Coherent exceptions**: two new exception classes, all six exceptions now publicly exported
- **No more stdlib exceptions leaking**: `OSError`/`SubprocessError` are now wrapped
- **164 tests** passing (was 132 in 1.1.1), 0 failures
- Sync backend infrastructure in place (temporarily disabled at façade level)

---

## What's New in 1.2.0

### New Exceptions

Two new exception classes complete the hierarchy:

| Class | Inherits from | Use case |
|-------|--------------|----------|
| `TaskConfigurationError` | `TaskWarriorError` | Binary not found in PATH, taskrc missing or unreadable |
| `TaskOperationError` | `TaskWarriorError` | Write operation failure on an existing task (delete, done, start, stop, annotate, purge) |

All six exceptions are now importable from the top-level package:

```python
from taskwarrior import (
    TaskWarriorError,
    TaskNotFound,
    TaskValidationError,
    TaskOperationError,
    TaskConfigurationError,
    TaskSyncError,
)
```

### Exception Semantic Fixes

| Before | After | Location |
|--------|-------|----------|
| `TaskValidationError` | `TaskConfigurationError` | Binary not found in PATH |
| `TaskValidationError` | `TaskWarriorError` | JSON parse errors on CLI responses |
| `TaskNotFound` | `TaskOperationError` | delete / purge / done / start / stop / annotate failures |
| `TaskNotFound` | `TaskWarriorError` | JSON errors in `get_recurring_instances` |
| `TaskWarriorError` | `TaskNotFound` | `get_task` with non-zero return code |
| `TaskValidationError` | `TaskWarriorError` | `modify_task` generic CLI failure |
| `TaskWarriorError` | `TaskValidationError` | Empty context name in `ContextService` |
| `TaskWarriorError` | `TaskConfigurationError` | Missing taskrc in `UdaRegistry` |
| `RuntimeError` | `TaskWarriorError` | `add_task` fallback path |

### Error Coverage Improvements

- `OSError` / `SubprocessError` in `run_task_command` now wrapped in `TaskWarriorError`
- `get_recurring_task` now protects `json.loads` (was the only method missing this guard)
- `ConfigStore._extract_taskrc_config` now raises `TaskConfigurationError` on file I/O errors
- `parse_taskwarrior_date` fallback now raises `ValueError` with a descriptive message

### Sync Infrastructure (1.2.0)

- `TaskWarrior.is_sync_configured()` and `TaskWarrior.synchronize()` exposed on the façade
- `SyncLocal` replica creation is now lazy (no side effects at init time)
- Synchronization is temporarily disabled at the façade level pending py-taskchampion
  compatibility review; the original call is preserved as a comment for easy reactivation

---

## Installation

```bash
pip install pytaskwarrior==1.2.0
```

## Links

- **[CHANGELOG.md](CHANGELOG.md)** – Full release history and migration guides
- **[README.md](README.md)** – Quick start, API reference, examples
- **[GitHub Issues](https://github.com/sznicolas/pytaskwarrior/issues)** – Bug reports

## Contributors

- Nicolas Schmeltz ([@sznicolas](https://github.com/sznicolas))
- GitHub Copilot (exception audit, refactoring, test updates)

---

**v1.2.0** | March 28, 2026

