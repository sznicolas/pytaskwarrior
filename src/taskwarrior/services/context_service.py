"""Context management service for TaskWarrior.

This module provides the ContextService class for managing TaskWarrior
contexts (named filters).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..dto.context_dto import ContextDTO
from ..exceptions import TaskValidationError, TaskWarriorError

if TYPE_CHECKING:
    from ..config.config_store import ConfigStore


class ContextService:
    """Service for managing TaskWarrior contexts.

    Reads and writes context definitions directly in ``.taskrc`` via
    :class:`~taskwarrior.config.config_store.ConfigStore` — no ``task``
    binary is required.
    """

    def __init__(self, config_store: ConfigStore) -> None:
        self.config_store = config_store

    def _validate_name(self, name: str) -> None:
        if not name or not name.strip():
            raise TaskValidationError("Context name cannot be empty")

    def define_context(self, ctx: ContextDTO) -> None:
        """Create or update a context by writing keys directly to ``.taskrc``."""
        self._validate_name(ctx.name)
        try:
            self.config_store.set_value(f"context.{ctx.name}.read", ctx.read_filter)
            self.config_store.set_value(f"context.{ctx.name}.write", ctx.write_filter)
        except Exception as e:
            raise TaskWarriorError(f"Failed to define context '{ctx.name}': {e}") from e

    def apply_context(self, name: str) -> None:
        """Apply a context, making it the active filter."""
        self._validate_name(name)
        if not self.has_context(name):
            raise TaskWarriorError(
                f"Failed to apply context '{name}': context is not defined. "
                "Define it with define_context() before applying."
            )
        try:
            self.config_store.set_value("context", name)
        except Exception as e:
            raise TaskWarriorError(f"Failed to apply context '{name}': {e}") from e

    def unset_context(self) -> None:
        """Deactivate the current context."""
        try:
            self.config_store.delete_value("context")
        except Exception as e:
            raise TaskWarriorError(f"Failed to unset context: {e}") from e

    def get_contexts(self) -> list[ContextDTO]:
        """List all defined contexts with their read and write filters."""
        try:
            current = self.get_current_context()
            return self.config_store.get_contexts(current_context=current)
        except Exception as e:
            raise TaskWarriorError(f"Error retrieving contexts: {str(e)}") from e

    def get_current_context(self) -> str | None:
        """Get the name of the currently active context, or ``None``."""
        return self.config_store.config.get("context") or None

    def delete_context(self, name: str) -> None:
        """Delete a defined context from ``.taskrc``."""
        self._validate_name(name)
        if not self.has_context(name):
            raise TaskWarriorError(f"Context '{name}' is not defined.")
        try:
            self.config_store.delete_value(f"context.{name}.read")
            self.config_store.delete_value(f"context.{name}.write")
            if self.get_current_context() == name:
                self.config_store.delete_value("context")
        except Exception as e:
            raise TaskWarriorError(f"Failed to delete context '{name}': {e}") from e

    def has_context(self, name: str) -> bool:
        """Return ``True`` if a context with *name* is defined."""
        return f"context.{name}.read" in self.config_store.config
