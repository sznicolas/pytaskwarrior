"""Context management service for TaskWarrior.

This module provides the ContextService class for managing TaskWarrior
contexts (named filters).
"""

import re

from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.context_dto import ContextDTO
from ..exceptions import TaskWarriorError


class ContextService:
    """Service for managing TaskWarrior contexts.

    Contexts are named filters applied globally to focus on specific subsets
    of tasks. Each context has a read_filter (applied when listing tasks) and
    a write_filter (applied when creating or modifying tasks).

    Attributes:
        adapter: The TaskWarriorAdapter instance for CLI communication.

    Example:
        This service is typically accessed via TaskWarrior::

            tw = TaskWarrior()
            tw.define_context("work", read_filter="project:work", write_filter="project:work")
            tw.apply_context("work")
    """

    def __init__(self, adapter: TaskWarriorAdapter):
        """Initialize the context service.

        Args:
            adapter: The TaskWarriorAdapter to use for CLI commands.
        """
        self.adapter: TaskWarriorAdapter = adapter

    def _validate_name(self, name: str) -> None:
        if not name or not name.strip():
            raise TaskWarriorError("Context name cannot be empty")

    def define_context(
        self, name: str, read_filter: str, write_filter: str
    ) -> None:
        """Create or update a context with explicit read and write filters.

        TaskWarrior stores read and write filters separately in .taskrc.
        Both must be provided — there is no implicit default.

        Args:
            name:         Unique context name.
            read_filter:  Filter applied when listing/querying tasks.
            write_filter: Filter applied when creating or modifying tasks.

        Raises:
            TaskWarriorError: If the name is empty or creation fails.

        Example:
            >>> service.define_context("work", "project:work", "project:work")
            >>> service.define_context("urgent", "+urgent", "")  # read-only filter
        """
        self._validate_name(name)
        result = self.adapter.run_task_command(["context", "define", name, read_filter])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to define context '{name}': {result.stderr}")
        result = self.adapter.run_task_command(
            ["config", f"context.{name}.write", write_filter]
        )
        if result.returncode != 0:
            raise TaskWarriorError(
                f"Failed to set write filter for context '{name}': {result.stderr}"
            )

    def apply_context(self, name: str) -> None:
        """Apply a context, making it the active filter.

        Args:
            name: Name of the context to apply.

        Raises:
            TaskWarriorError: If the name is empty or the context doesn't exist.
        """
        self._validate_name(name)
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
        """List all defined contexts with their read and write filters.

        Reads context.*.read and context.*.write entries directly from
        .taskrc to guarantee correctness regardless of CLI output format.

        Returns:
            List of ContextDTO objects (name, read_filter, write_filter, active).

        Raises:
            TaskWarriorError: If retrieval fails.
        """
        try:
            current = self.get_current_context()
            taskrc_path = self.adapter.taskrc_file
            content = taskrc_path.read_text(encoding="utf-8")

            # Collect all context.*.read entries as canonical source of truth
            names: dict[str, dict[str, str]] = {}
            for m in re.finditer(
                r"^\s*context\.([^.\s]+)\.(read|write)\s*=\s*(.*)",
                content,
                re.MULTILINE,
            ):
                ctx_name = m.group(1)
                kind = m.group(2)
                value = m.group(3).strip()
                names.setdefault(ctx_name, {})[kind] = value

            return [
                ContextDTO(
                    name=n,
                    read_filter=filters.get("read", ""),
                    write_filter=filters.get("write", ""),
                    active=(n == current),
                )
                for n, filters in names.items()
            ]
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
        """Delete a defined context (both read and write filters).

        Args:
            name: Name of the context to delete.

        Raises:
            TaskWarriorError: If the name is empty or deletion fails.
        """
        self._validate_name(name)
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
            return any(ctx.name == name for ctx in self.get_contexts())
        except TaskWarriorError:
            return False
