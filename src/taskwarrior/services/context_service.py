from ..dto.context_dto import ContextDTO
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..exceptions import TaskWarriorError


class ContextService:
    """Service for managing task contexts."""

    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter

    def create_context(self, name: str, filter_str: str) -> None:
        """Create a new context with the given name and filter."""
        self.adapter.define_context(name, filter_str)

    def apply_context(self, name: str) -> None:
        """Apply a context (set it as current)."""
        self.adapter.apply_context(name)

    def remove_context(self) -> None:
        """Remove the current context (set to none)."""
        self.adapter.remove_context()

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts."""
        return self.adapter.get_contexts()

    def get_current_context(self) -> str | None:
        """Get the name of the current context."""
        return self.adapter.get_current_context()

    def delete_context(self, name: str) -> None:
        """Delete a defined context."""
        self.adapter.delete_context(name)

    def has_context(self, name: str) -> bool:
        """Check if a context exists."""
        contexts = self.get_contexts()
        return any(ctx.name == name for ctx in contexts)
