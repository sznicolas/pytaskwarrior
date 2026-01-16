from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.context_dto import ContextDTO
from ..exceptions import TaskWarriorError


class ContextService:
    """Service for managing task contexts."""

    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter: TaskWarriorAdapter = adapter

    def define_context(self, name: str, filter_str: str) -> None:
        """Create a new context with the given name and filter."""
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

        self.adapter.run_task_command(["context", "define", name, filter_str])

    def apply_context(self, name: str) -> None:
        """Apply a context (set it as current)."""
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

        result = self.adapter.run_task_command(["context", name])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to apply context '{name}': {result.stderr}")

    def unset_context(self) -> None:
        """Deactivate the context (set to none)."""
        result = self.adapter.run_task_command(["context", "none"])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to unset context: {result.stderr}")

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts."""
        try:
            result = self.adapter.run_task_command(["context", "list"])

            if result.returncode != 0:
                raise TaskWarriorError(f"Failed to list contexts: {result.stderr}")

            contexts = []
            # Parse the output to extract context names and filters
            lines = result.stdout.strip().split("\n")
            if len(lines) > 2:  # Skip header lines
                for line in lines[2:]:  # Skip "Context Filter" and empty line
                    if line.strip():
                        parts = line.split(None, 1)  # Split on first whitespace
                        if len(parts) == 2:
                            context_name, filter_str = parts
                            contexts.append(
                                ContextDTO(name=context_name, filter=filter_str)
                            )
            return contexts
        except Exception as e:
            raise TaskWarriorError(f"Error retrieving contexts: {str(e)}")

    def get_current_context(self) -> str | None:
        """Get the name of the current context."""
        try:
            result = self.adapter.run_task_command(["_get", "rc.context"])

            if result.returncode != 0:
                return None

            context_name = result.stdout.strip()
            return context_name if context_name else None
        except Exception as e:
            raise TaskWarriorError(f"Error retrieving current context: {str(e)}")

    def delete_context(self, name: str) -> None:
        """Delete a defined context."""
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

        result = self.adapter.run_task_command(["context", "delete", name])
        if result.returncode != 0:
            raise TaskWarriorError(
                f"Failed to delete context '{name}': {result.stderr}"
            )

    def has_context(self, name: str) -> bool:
        """Check if a context exists."""
        try:
            contexts = self.get_contexts()
            return any(ctx.name == name for ctx in contexts)
        except Exception:
            # If we can't retrieve contexts, assume context doesn't exist
            return False
