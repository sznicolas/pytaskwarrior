from __future__ import annotations

import pytest

from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from src.taskwarrior.dto.context_dto import ContextDTO
from src.taskwarrior.exceptions import TaskWarriorError
from src.taskwarrior.services.context_service import ContextService


class TestTaskWarriorAdapterContext:
    """Test cases for ContextService."""

    @pytest.fixture
    def context_service(self, taskwarrior_config: str):
        adapter = TaskWarriorAdapter(task_cmd="task", taskrc_file=taskwarrior_config)
        return ContextService(adapter)

    # ------------------------------------------------------------------
    # define_context
    # ------------------------------------------------------------------

    def test_define_context_sets_read_and_write(self, context_service: ContextService):
        """Both read and write filters are stored and retrievable."""
        context_service.define_context("work", "project:work", "project:work")
        contexts = context_service.get_contexts()
        ctx = next((c for c in contexts if c.name == "work"), None)
        assert ctx is not None
        assert ctx.read_filter == "project:work"
        assert ctx.write_filter == "project:work"

    def test_define_context_distinct_filters(self, context_service: ContextService):
        """Read and write filters can differ."""
        context_service.define_context("review", "+urgent", "")
        contexts = context_service.get_contexts()
        ctx = next((c for c in contexts if c.name == "review"), None)
        assert ctx is not None
        assert ctx.read_filter == "+urgent"
        assert ctx.write_filter == ""

    def test_define_context_empty_name_raises(self, context_service: ContextService):
        with pytest.raises(TaskWarriorError):
            context_service.define_context("", "project:work", "project:work")

    def test_define_context_whitespace_name_raises(self, context_service: ContextService):
        with pytest.raises(TaskWarriorError):
            context_service.define_context("   ", "project:work", "project:work")

    def test_define_context_is_idempotent(self, context_service: ContextService):
        """Redefining an existing context updates it without error."""
        context_service.define_context("work", "project:work", "project:work")
        context_service.define_context("work", "project:work or +urgent", "project:work")
        contexts = context_service.get_contexts()
        ctx = next((c for c in contexts if c.name == "work"), None)
        assert ctx is not None
        assert "urgent" in ctx.read_filter

    # ------------------------------------------------------------------
    # get_contexts / ContextDTO shape
    # ------------------------------------------------------------------

    def test_get_contexts_returns_context_dto_instances(self, context_service: ContextService):
        context_service.define_context("ctx1", "status:pending", "status:pending")
        contexts = context_service.get_contexts()
        assert all(isinstance(c, ContextDTO) for c in contexts)

    def test_get_contexts_returns_both_defined(self, context_service: ContextService):
        context_service.define_context("ctx1", "status:pending", "status:pending")
        context_service.define_context("ctx2", "project:perso", "project:perso")
        names = [c.name for c in context_service.get_contexts()]
        assert "ctx1" in names
        assert "ctx2" in names

    def test_get_contexts_dto_has_no_filter_attribute(self, context_service: ContextService):
        """Legacy 'filter' field must not exist — breaking change confirmed."""
        context_service.define_context("work", "project:work", "project:work")
        ctx = context_service.get_contexts()[0]
        assert not hasattr(ctx, "filter")

    # ------------------------------------------------------------------
    # apply / unset / get_current_context
    # ------------------------------------------------------------------

    def test_apply_context(self, context_service: ContextService):
        context_service.define_context("work", "project:work", "project:work")
        context_service.apply_context("work")
        assert context_service.get_current_context() == "work"

    def test_unset_context(self, context_service: ContextService):
        context_service.define_context("work", "project:work", "project:work")
        context_service.apply_context("work")
        context_service.unset_context()
        assert context_service.get_current_context() is None

    def test_get_current_context_none_by_default(self, context_service: ContextService):
        assert context_service.get_current_context() is None

    def test_active_flag_reflects_current_context(self, context_service: ContextService):
        context_service.define_context("work", "project:work", "project:work")
        context_service.apply_context("work")
        contexts = context_service.get_contexts()
        active = [c for c in contexts if c.active]
        assert len(active) == 1
        assert active[0].name == "work"

    # ------------------------------------------------------------------
    # delete / has_context
    # ------------------------------------------------------------------

    def test_delete_context(self, context_service: ContextService):
        context_service.define_context("work", "project:work", "project:work")
        context_service.delete_context("work")
        names = [c.name for c in context_service.get_contexts()]
        assert "work" not in names

    def test_delete_nonexistent_context_raises(self, context_service: ContextService):
        with pytest.raises(TaskWarriorError):
            context_service.delete_context("nonexistent")

    def test_delete_empty_name_raises(self, context_service: ContextService):
        with pytest.raises(TaskWarriorError):
            context_service.delete_context("")

    def test_has_context_true(self, context_service: ContextService):
        context_service.define_context("work", "project:work", "project:work")
        assert context_service.has_context("work") is True

    def test_has_context_false(self, context_service: ContextService):
        assert context_service.has_context("nonexistent") is False

    # ------------------------------------------------------------------
    # apply_context error conditions
    # ------------------------------------------------------------------

    def test_apply_nonexistent_context_raises(self, context_service: ContextService):
        with pytest.raises(TaskWarriorError):
            context_service.apply_context("nonexistent_context")
