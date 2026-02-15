"""User Defined Attributes (UDA) service for TaskWarrior.

This module provides the UdaService class for managing custom task attributes.
"""

from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.uda_dto import UdaConfig
from ..registry.uda_registry import UdaRegistry


class UdaService:
    """Service for managing User Defined Attributes (UDAs).

    UDAs allow extending TaskWarrior with custom fields. This service
    provides methods to define, update, and delete UDAs, delegating
    the actual work to UdaRegistry.

    Attributes:
        adapter: The TaskWarriorAdapter instance for CLI communication.
        registry: The UdaRegistry for tracking defined UDAs.

    Example:
        This service is typically accessed via TaskWarrior::

            tw = TaskWarrior()
            uda = UdaConfig(name="severity", type=UdaType.STRING)
            tw.uda_service.define_uda(uda)
    """

    def __init__(self, adapter: TaskWarriorAdapter):
        """Initialize the UDA service.

        Args:
            adapter: The TaskWarriorAdapter to use for CLI commands.
        """
        self.adapter = adapter
        self.registry = UdaRegistry()

    def load_udas_from_taskrc(self) -> None:
        """Load existing UDA definitions from the taskrc file.

        Parses the taskrc file to discover and register any UDAs
        that have been previously defined.
        """
        self.registry.load_from_taskrc(self.adapter.taskrc_file)

    def define_uda(self, uda: UdaConfig) -> None:
        """Define a new UDA in TaskWarrior.

        Creates the UDA configuration in TaskWarrior and registers
        it in the local registry.

        Args:
            uda: The UDA definition to create.

        Example:
            >>> uda = UdaConfig(
            ...     name="severity",
            ...     type=UdaType.STRING,
            ...     values=["low", "medium", "high"]
            ... )
            >>> service.define_uda(uda)
        """
        self.registry.define_update_uda(uda, self.adapter)

    def update_uda(self, uda: UdaConfig) -> None:
        """Update an existing UDA definition.

        Modifies the UDA configuration in TaskWarrior.

        Args:
            uda: The updated UDA definition.
        """
        self.registry.define_update_uda(uda, self.adapter)

    def delete_uda(self, uda: UdaConfig) -> None:
        """Delete a UDA from TaskWarrior.

        Removes the UDA configuration and unregisters it.

        Args:
            uda: The UDA to delete.
        """
        self.registry.delete_uda(uda, self.adapter)
