# Contributing to pytaskwarrior

Thank you for your interest in contributing to pytaskwarrior! 🎉

## Getting Started

### Prerequisites

- Python 3.12+
- TaskWarrior 3.4+ installed
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/sznicolas/pytaskwarrior.git
cd pytaskwarrior

# Install dependencies (with uv)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=src/taskwarrior --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_dto.py -v
```

### Code Quality

We use **ruff** for linting/formatting and **mypy** for type checking:

```bash
# Linting
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Formatting
ruff format src/ tests/

# Type checking (strict mode)
mypy src/taskwarrior
```

All checks must pass before submitting a PR.

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates

### Commit Messages

Use clear, descriptive commit messages:

```
Add context management methods
Fix circular import in uda_service
Update README with API examples
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass and code quality checks succeed
5. Submit a PR with a clear description

## Code Style

- Use type hints for all function signatures
- Follow existing patterns in the codebase
- Add tests for new functionality
- Update documentation if needed

## Project Structure

```
pytaskwarrior/
├── src/taskwarrior/
│   ├── adapters/          # TaskWarrior CLI wrapper
│   ├── dto/               # Pydantic data models
│   ├── registry/          # UDA registry
│   ├── services/          # Business logic (context, UDA)
│   ├── utils/             # Helper functions
│   ├── enums.py           # Priority, Status, Recurrence
│   ├── exceptions.py      # Custom exceptions
│   └── main.py            # TaskWarrior facade class
├── tests/
│   ├── unit/              # Unit tests
│   └── conftest.py        # Pytest fixtures
└── examples/              # Usage examples
```

## Questions?

Feel free to open an issue for questions or discussions.
