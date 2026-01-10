from __future__ import annotations

import json
import subprocess
from uuid import uuid4

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.task_dto import TaskInputDTO
from src.taskwarrior.enums import Priority, RecurrencePeriod
from src.taskwarrior.exceptions import (
    TaskNotFound,
    TaskValidationError,
    TaskWarriorError,
)


class TestTaskWarriorAdapterContext:
    """Test cases for TaskWarriorAdapter context management functionality."""

    @pytest.fixture
    def adapter(self, taskwarrior_config: str):
        """Create a TaskWarriorAdapter instance for testing."""
        return TaskWarriorAdapter(task_cmd="task", taskrc_path=taskwarrior_config)

    def test_context_management_errors(self, adapter: TaskWarriorAdapter):
        """Test context management error conditions."""
        # Test apply_context with non-existent context
        with pytest.raises(TaskWarriorError):
            adapter.apply_context("nonexistent_context")

        # Test delete_context with non-existent context
        with pytest.raises(TaskWarriorError):
            adapter.delete_context("nonexistent_context")

    def test_context_management_sequence(self, adapter: TaskWarriorAdapter):
        """Test sequence of context management operations."""
        # Set a context
        adapter.define_context("test_context", "status:pending")

        # Apply it
        adapter.apply_context("test_context")

        # Remove it
        adapter.remove_context()

        # Verify no context is set
        context = adapter.current_context()
        assert context is None

    def test_context_management_comprehensive(self, adapter: TaskWarriorAdapter):
        """Test comprehensive context management."""
        # Test setting multiple contexts
        adapter.define_context("context1", "status:pending")
        adapter.define_context("context2", "status:completed")

        # List contexts
        contexts = adapter.get_contexts()
        assert isinstance(contexts, dict)
        assert "context1" in contexts
        assert "context2" in contexts

        # Apply one context
        adapter.apply_context("context1")
        context = adapter.current_context()
        assert context == "context1"

        # Remove context
        adapter.remove_context()
        context = adapter.current_context()
        assert context is None

        # Delete a context
        adapter.delete_context("context1")
        contexts = adapter.get_contexts()
        assert "context1" not in contexts
