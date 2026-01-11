from ..dto.context_dto import ContextDTO
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..exceptions import TaskWarriorError


class ContextService:
    """Service for managing task contexts."""

    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter

    def create_context(self, name: str, filter_str: str) -> None:
        """Create a new context with the given name and filter."""
        self.adapter.run_task_command(["context", "define", name, filter_str])

    def apply_context(self, name: str) -> None:
        """Apply a context (set it as current)."""
        self.adapter.run_task_command(["context", name])

    def remove_context(self) -> None:
        """Remove the current context (set to none)."""
        self.adapter.run_task_command(["context", "none"])

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts."""
        result = self.adapter.run_task_command(["context", "list"])
        contexts = []
        # Parse the output to extract context names and filters
        lines = result.stdout.strip().split("\n")
        if len(lines) > 2:  # Skip header lines
            for line in lines[2:]:  # Skip "Context Filter" and empty line
                if line.strip():
                    parts = line.split(None, 1)  # Split on first whitespace
                    if len(parts) == 2:
                        context_name, filter_str = parts
                        contexts.append(ContextDTO(name=context_name, filter=filter_str))
        return contexts

    def get_current_context(self) -> str | None:
        """Get the name of the current context."""
        result = self.adapter.run_task_command(["_get", "rc.context"])
        if result.returncode != 0:
            # Check if it's because no context is set (command returns non-zero but that's expected)
            # We should return None when no context is set
            return None
        context_name = result.stdout.strip()
        return context_name if context_name else None

    def delete_context(self, name: str) -> None:
        """Delete a defined context."""
        self.adapter.run_task_command(["context", "delete", name])

    def has_context(self, name: str) -> bool:
        """Check if a context exists."""
        contexts = self.get_contexts()
        return any(ctx.name == name for ctx in contexts)
