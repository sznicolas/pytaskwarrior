# PyTaskWarrior 1.0.0 Release Notes

## Overview

**PyTaskWarrior 1.0.0** is the first production-ready release featuring a complete API rewrite with professional-grade code quality.

### Key Highlights

- **Production-ready**: 132 comprehensive tests (96% coverage), strict type checking (mypy), zero linting errors (ruff)
- **Type-safe API**: Pydantic v2 DTOs with full IDE/type-checker support (PEP 561)
- **Hardened subprocess handling**: 30s timeout, atomic operations, regex-based date validation
- **Clean architecture**: Adapters, services, and domain objects — no singletons, no hidden state
- **Full TaskWarrior feature parity**: Contexts, UDAs, recurring tasks, annotations, date calculations

### Breaking Changes

⚠️ **Python 3.12+** and **TaskWarrior 3.4+** required.  
⚠️ Complete API rewrite — see migration guide in [CHANGELOG.md](CHANGELOG.md).

### What's New

#### Core Features
- **Type-safe operations** via `TaskInputDTO` / `TaskOutputDTO` (Pydantic v2)
- **Context management** with active context tracking
- **UDA support** with registry and validation
- **Recurring tasks** enum + custom recurrence strings ("2weeks", "10days")
- **Task annotations** with ISO timestamps
- **Date utilities**: arithmetic and validation

#### Reliability & Safety
- Subprocess timeout (30s) prevents hangs
- Atomic `add_task()` — parses task ID from stdout (no race conditions)
- Atomic date validation via ISO regex (not exit code)
- Proper exception hierarchy with exception chaining
- Thread-safe `UdaRegistry` (no global state)

#### Code Quality
- 132 unit tests (35 mocked, 97 integration)
- 96% code coverage (was 87%)
- `ruff` — zero linting errors (6 rules + SIM117 ignore for tests)
- `mypy` strict mode enabled
- GitHub Actions CI/CD (pytest matrix 3.12–3.13)

### Migration from 0.3.0

```python
# Use Pydantic DTOs instead of dicts
from taskwarrior import TaskInputDTO, Priority

task = TaskInputDTO(description="New task", priority=Priority.HIGH)
tw.add_task(task)

# TaskOutputDTO replaces dict responses
for task in tw.get_tasks():
    print(task.description, task.status)
```

Full migration guide in [CHANGELOG.md](CHANGELOG.md#migration-guide).

### Installation

```bash
pip install pytaskwarrior==1.0.0
```

### Documentation

- **[README.md](README.md)** – Quick start, examples, API reference
- **[CHANGELOG.md](CHANGELOG.md)** – Full release notes, breaking changes, migration guide
- **[GitHub Discussions](https://github.com/sznicolas/pytaskwarrior/discussions)** – Questions & feedback

### Contributors

- Nicolas Schmeltz ([@sznicolas](https://github.com/sznicolas))
- GitHub Copilot (code review, quality audit, refactoring)

### Support

Report issues: [GitHub Issues](https://github.com/sznicolas/pytaskwarrior/issues)

---

**v1.0.0** | February 26, 2026
