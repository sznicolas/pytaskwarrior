from __future__ import annotations

import json
import subprocess
from uuid import uuid4

import pytest

from src.taskwarrior.services.context_service import ContextService
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
    def context_service(self, taskwarrior_config: str):
        """Create a TaskWarriorAdapter instance for testing."""
        task_warrior_adapter = TaskWarriorAdapter(task_cmd="task", taskrc_path=taskwarrior_config)
        return ContextService(task_warrior_adapter)


    def test_context_management_errors(self, context_service: ContextService):
        """Test context management error conditions."""
        # Test apply_context with non-existent context
        with pytest.raises(TaskWarriorError):
            context_service.apply_context("nonexistent_context")

        # Test delete_context with non-existent context
        with pytest.raises(TaskWarriorError):
            context_service.delete_context("nonexistent_context")

    def test_context_management_sequence(self, context_service: ContextService):
        """Test sequence of context management operations."""
        # Set a context
        context_service.define_context("test_context", "status:pending")

        # Apply it
        context_service.apply_context("test_context")

        # Remove it
        context_service.remove_context()

        # Verify no context is set
        context = context_service.current_context()
        assert context is None

    def test_context_management_comprehensive(self, context_service: ContextService):
        """Test comprehensive context management."""
        # Test setting multiple contexts
        context_service.define_context("context1", "status:pending")
        context_service.define_context("context2", "status:completed")

        # List contexts
        contexts = context_service.get_contexts()
        assert isinstance(contexts, dict)
        assert "context1" in contexts
        assert "context2" in contexts

        # Apply one context
        context_service.apply_context("context1")
        context = context_service.current_context()
        assert context == "context1"

        # Remove context
        context_service.remove_context()
        context = context_service.current_context()
        assert context is None

        # Delete a context
        context_service.delete_context("context1")
        contexts = context_service.get_contexts()
        assert "context1" not in contexts

    def test_context_management(self, context_service: ContextService):
        """Test context management functionality."""
        # Test set and apply context
        context_service.define_context("test_context", "status:pending")
        context_service.apply_context("test_context")

        # Test remove context
        context_service.remove_context()

        # Test list contexts
        contexts = context_service.get_contexts()
        assert isinstance(contexts, dict)

        # Test show context
        context = context_service.current_context()
        assert context is None or isinstance(context, str)

