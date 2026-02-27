# Changelog

All notable changes to pytaskwarrior will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-26

### Added
- **Type-safe DTOs** - `TaskInputDTO` and `TaskOutputDTO` with Pydantic validation
- **Context management** - Define, apply, switch, and delete contexts
- **UDA support** - User Defined Attributes with `UdaRegistry`
- **Recurring tasks** - Full recurrence support with `RecurrencePeriod` enum
- **Task annotations** - Add and retrieve annotations
- **Date calculations** - `task_calc()` and `date_validator()` methods
- **Priority enum** - Type-safe `Priority.HIGH`, `MEDIUM`, `LOW`
- **Task status enum** - `TaskStatus.PENDING`, `COMPLETED`, `DELETED`, etc.
- **Code quality** - ruff linting, mypy strict mode, 87% test coverage

### Changed
- **Complete API refactoring** - New clean architecture with adapters/services/DTOs
- **Python 3.12+ required** - Modern Python features
- **TaskWarrior 3.4+ required** - Latest TaskWarrior compatibility
- Path expansion now supports both `~` and `$HOME` environment variables

### Fixed
- Circular import issues resolved
- `has_context()` now correctly returns boolean value
- Exception chaining with `from e` for better tracebacks

## [0.2.0] - 2025-06-29

### Added
- Basic task operations (add, get, modify, delete, done)
- Initial TaskWarrior wrapper

## [0.1.0] - 2025-06-14

### Added
- Initial release
- Basic proof of concept
