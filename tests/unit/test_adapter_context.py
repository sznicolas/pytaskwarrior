from __future__ import annotations

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.context_dto import ContextDTO
from src.taskwarrior.exceptions import (
    TaskWarriorError,
)
from src.taskwarrior.services.context_service import ContextService


class TestTaskWarriorAdapterContext:
    """Test cases for TaskWarriorAdapter context management functionality."""

    @pytest.fixture
    def context_service(self, taskwarrior_config: str):
        """Create a TaskWarriorAdapter instance for testing."""
        task_warrior_adapter = TaskWarriorAdapter(
            task_cmd="task", taskrc_file=taskwarrior_config
        )
        return ContextService(task_warrior_adapter)

    def test_context_management_comprehensive(self, context_service: ContextService):
        """Test comprehensive context management including all operations."""
        # Test setting multiple contexts
        context_service.define_context("context1", "status:pending")
        context_service.define_context("context2", "status:completed")

        # List contexts
        contexts = context_service.get_contexts()
        assert isinstance(contexts[0], ContextDTO)
        assert "context1" in [c.name for c in contexts]
        assert "context2" in [c.name for c in contexts]

        # Apply one context
        context_service.apply_context("context1")
        context = context_service.get_current_context()
        assert context == "context1"

        # Remove context
        context_service.unset_context()
        context = context_service.get_current_context()
        assert context is None

        # Delete a context
        context_service.delete_context("context1")
        contexts = context_service.get_contexts()
        assert "context1" not in contexts

    def test_context_management_error_conditions(self, context_service: ContextService):
        """Test context management error conditions."""
        # Test apply_context with non-existent context
        with pytest.raises(TaskWarriorError):
            context_service.apply_context("nonexistent_context")

        # Test delete_context with non-existent context
        with pytest.raises(TaskWarriorError):
            context_service.delete_context("nonexistent_context")

        # Test with empty context names
        with pytest.raises(TaskWarriorError):
            context_service.define_context("", "status:pending")

        # Test with whitespace-only names
        with pytest.raises(TaskWarriorError):
            context_service.define_context("   ", "status:pending")
