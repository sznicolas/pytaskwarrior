"""User Defined Attributes (UDA) service for TaskWarrior.

This module provides the UdaService class for managing custom task attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
    from ..config.config_store import ConfigStore

from ..dto.uda_dto import UdaConfig
from ..exceptions import TaskOperationError
from ..registry.uda_registry import UdaRegistry


class UdaService:
    """Service for managing User Defined Attributes (UDAs).

    UDAs allow extending TaskWarrior with custom fields. This service
    reads and writes UDA definitions directly in ``.taskrc`` via
    :class:`~taskwarrior.config.config_store.ConfigStore` — no ``task``
    binary is required.

    Attributes:
        config_store: The configuration store backed by ``.taskrc``.
        registry: The UdaRegistry for tracking defined UDAs in memory.

    Example:
        This service is typically accessed via TaskWarrior::

            tw = TaskWarrior()
            uda = UdaConfig(name="severity", uda_type=UdaType.STRING)
            tw.uda_service.define_uda(uda)
    """

    def __init__(
        self,
        config_store: "ConfigStore",
        adapter: "TaskWarriorAdapter | None" = None,
    ) -> None:
        """Initialize the UDA service.

        Args:
            config_store: The configuration store instance (required).
            adapter: Legacy parameter kept for backwards compatibility;
                no longer used for write operations.
        """
        self.config_store = config_store
        # Kept for backwards compatibility; write ops no longer use it.
        self.adapter = adapter
        self.registry = UdaRegistry()

    def load_udas_from_store(self) -> None:
        """Load existing UDA definitions from the configured ConfigStore.

        This method delegates parsing to ConfigStore.get_udas() and registers
        the resulting UdaConfig objects in the registry (in-memory only).
        """
        udas = self.config_store.get_udas()
        self.registry.register_udas(udas)

    def define_uda(self, uda: UdaConfig) -> None:
        """Define (or update) a UDA by writing keys directly to ``.taskrc``.

        All non-null fields of *uda* are persisted.  On success the UDA is
        registered in the in-memory registry.

        Args:
            uda: The UdaConfig describing the UDA to create or update.

        Raises:
            TaskOperationError: If the taskrc file cannot be written.

        Example:
            >>> uda = UdaConfig(name="sev", uda_type=UdaType.STRING, label="Severity")
            >>> service.define_uda(uda)
        """
        try:
            self.config_store.set_value(f"uda.{uda.name}.type", uda.uda_type.value)

            field_names = set(uda.__class__.model_fields.keys()) - {"name", "uda_type"}
            for field_name in sorted(field_names):
                value = getattr(uda, field_name)
                if value is not None and value != "":
                    value_str = (
                        ",".join(map(str, value)) if field_name == "values" else str(value)
                    )
                    self.config_store.set_value(f"uda.{uda.name}.{field_name}", value_str)
        except Exception as e:
            raise TaskOperationError(f"Failed to define UDA '{uda.name}': {e}") from e

        self.registry.add_uda(uda)

    def update_uda(self, uda: UdaConfig) -> None:
        """Update an existing UDA in ``.taskrc`` and in the registry.

        Args:
            uda: The UdaConfig with updated settings to apply.

        Raises:
            TaskOperationError: If applying the updated configuration fails.
        """
        self.define_uda(uda)

    def delete_uda(self, uda: UdaConfig) -> None:
        """Delete a UDA by removing its keys from ``.taskrc``.

        Missing keys are silently ignored (idempotent).

        Args:
            uda: The UdaConfig identifying the UDA to remove.

        Raises:
            TaskOperationError: If the taskrc file cannot be written.
        """
        try:
            field_names = set(uda.__class__.model_fields.keys()) - {"name"}
            # Map internal uda_type → taskrc "type"
            if "uda_type" in field_names:
                self.config_store.delete_value(f"uda.{uda.name}.type")
                field_names.remove("uda_type")

            for field_name in sorted(field_names):
                self.config_store.delete_value(f"uda.{uda.name}.{field_name}")
        except Exception as e:
            raise TaskOperationError(f"Failed to delete UDA '{uda.name}': {e}") from e

        self.registry.remove_uda(uda.name)
