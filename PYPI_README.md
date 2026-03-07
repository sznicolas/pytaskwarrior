# pytaskwarrior

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests](https://github.com/sznicolas/pytaskwarrior/workflows/CI/badge.svg)](https://github.com/sznicolas/pytaskwarrior/actions)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)](https://github.com/sznicolas/pytaskwarrior)
[![PyPI version](https://img.shields.io/pypi/v/pytaskwarrior.svg)](https://pypi.org/project/pytaskwarrior/)

A modern Python wrapper for [TaskWarrior](https://taskwarrior.org/), the command-line task management tool.

Production-ready with 132 tests (96% coverage), strict type checking, and professional-grade code quality. Zero linting errors, full async-safe subprocess handling, and PEP 561 type hints for IDE support.

## Features

- ✅ Full CRUD operations for tasks
- ✅ Type-safe with Pydantic models
- ✅ Context management
- ✅ UDA (User Defined Attributes) support
- ✅ Recurring tasks and annotations

## Requirements

- Python 3.12+
- TaskWarrior 3.4+ installed

## Installation

```bash
pip install pytaskwarrior
```

## Quick Start

```python
from taskwarrior import TaskWarrior, TaskInputDTO, Priority

tw = TaskWarrior()

# Create a task
task = TaskInputDTO(
    description="Important meeting",
    priority=Priority.HIGH,
    project="work",
    due="friday"
)
added = tw.add_task(task)

# Get all pending tasks
for t in tw.get_tasks():
    print(f"[{t.priority or '-'}] {t.description}")

# Complete a task
tw.done_task(added.uuid)
```

## Documentation

Full documentation: [GitHub Repository](https://github.com/sznicolas/pytaskwarrior/)
