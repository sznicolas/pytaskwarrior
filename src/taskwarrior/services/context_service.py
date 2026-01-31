"""Context management service for TaskWarrior.

This module provides the ContextService class for managing TaskWarrior
contexts (named filters).
"""

from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.context_dto import ContextDTO
from ..exceptions import TaskWarriorError


class ContextService:
    """Service for managing TaskWarrior contexts.

    Contexts are named filters that can be applied globally to focus
    on specific subsets of tasks. This service handles creating,
    applying, and managing contexts.

    Attributes:
        adapter: The TaskWarriorAdapter instance for CLI communication.

    Example:
        This service is typically accessed via TaskWarrior::

            tw = TaskWarrior()
            tw.define_context("work", "project:work")
            tw.apply_context("work")
    """

    def __init__(self, adapter: TaskWarriorAdapter):
        """Initialize the context service.

        Args:
            adapter: The TaskWarriorAdapter to use for CLI commands.
        """
        self.adapter: TaskWarriorAdapter = adapter

    def define_context(self, name: str, filter_str: str) -> None:
        """Create a new context with the given name and filter.

        Args:
            name: Unique name for the context.
            filter_str: TaskWarrior filter expression.

        Raises:
            TaskWarriorError: If the name is empty or creation fails.

        Example:
            >>> service.define_context("urgent", "+urgent or priority:H")
        """
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

        self.adapter.run_task_command(["context", "define", name, filter_str])

    def apply_context(self, name: str) -> None:
        """Apply a context, making it the active filter.

        Args:
            name: Name of the context to apply.

        Raises:
            TaskWarriorError: If the name is empty or the context doesn't exist.
        """
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

        result = self.adapter.run_task_command(["context", name])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to apply context '{name}': {result.stderr}")

    def unset_context(self) -> None:
        """Deactivate the current context.

        Removes any active context filter, returning to showing all tasks.

        Raises:
            TaskWarriorError: If unsetting the context fails.
        """
        result = self.adapter.run_task_command(["context", "none"])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to unset context: {result.stderr}")

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts.

        Returns:
            List of ContextDTO objects with name and filter for each context.

        Raises:
            TaskWarriorError: If retrieval fails.
        """
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
            raise TaskWarriorError(f"Error retrieving contexts: {str(e)}") from e

    def get_current_context(self) -> str | None:
        """Get the name of the currently active context.

        Returns:
            The context name if one is active, None otherwise.

        Raises:
            TaskWarriorError: If retrieval fails.
        """
        try:
            result = self.adapter.run_task_command(["_get", "rc.context"])

            if result.returncode != 0:
                return None

            context_name = result.stdout.strip()
            return context_name if context_name else None
        except Exception as e:
            raise TaskWarriorError(f"Error retrieving current context: {str(e)}") from e

    def delete_context(self, name: str) -> None:
        """Delete a defined context.

        Args:
            name: Name of the context to delete.

        Raises:
            TaskWarriorError: If the name is empty or deletion fails.
        """
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

        result = self.adapter.run_task_command(["context", "delete", name])
        if result.returncode != 0:
            raise TaskWarriorError(
                f"Failed to delete context '{name}': {result.stderr}"
            )

    def has_context(self, name: str) -> bool:
        """Check if a context with the given name exists.

        Args:
            name: Name of the context to check.

        Returns:
            True if the context exists, False otherwise.
        """
        try:
            contexts = self.get_contexts()
            return any(ctx.name == name for ctx in contexts)
        except TaskWarriorError:
            # If we can't retrieve contexts, assume context doesn't exist
            return False
