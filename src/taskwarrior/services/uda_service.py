"""User Defined Attributes (UDA) service for TaskWarrior.

This module provides the UdaService class for managing custom task attributes.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.config_store import ConfigStore

from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.uda_dto import UdaConfig
from ..exceptions import TaskOperationError
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
            uda = UdaConfig(name="severity", uda_type=UdaType.STRING)
            tw.uda_service.define_uda(uda)
    """

    def __init__(self, adapter: TaskWarriorAdapter, config_store: "ConfigStore") -> None:
        """Initialize the UDA service.

        Args:
            adapter: The TaskWarriorAdapter to use for CLI commands.
            config_store: The configuration store instance (required).
        """

        self.adapter = adapter
        self.config_store = config_store
        self.registry = UdaRegistry()

    def load_udas_from_store(self) -> None:
        """Load existing UDA definitions from the configured ConfigStore.

        This method delegates parsing to ConfigStore.get_udas() and registers
        the resulting UdaConfig objects in the registry (in-memory only).
        """
        udas = self.config_store.get_udas()
        self.registry.register_udas(udas)

    def define_uda(self, uda: UdaConfig) -> None:
        """Define a new UDA in TaskWarrior and register it locally.

        The service executes the required `task config` commands via the adapter
        and only updates the registry if all commands succeed.

        Args:
            uda: The UdaConfig describing the UDA to create.

        Raises:
            TaskOperationError: If any underlying TaskWarrior config command fails.

        Example:
            >>> uda = UdaConfig(name="sev", uda_type=UdaType.STRING, label="Severity")
            >>> service.define_uda(uda)
        """
        # Build commands to define the UDA
        field_names = uda.__class__.model_fields.keys() - {"name"}
        # uda_type is handled first
        commands: list[list[str]] = [["config", f"uda.{uda.name}.type", uda.uda_type.value]]
        field_names -= {"uda_type"}

        for field_name in field_names:
            value = getattr(uda, field_name)
            if value is not None and value != "":
                value_str = ",".join(map(str, value)) if field_name == "values" else str(value)
                commands.append(["config", f"uda.{uda.name}.{field_name}", value_str])

        # Execute commands via adapter; if any fail, raise and do not modify registry
        for cmd in commands:
            result = self.adapter.run_task_command(cmd)
            if getattr(result, "returncode", 0) != 0:
                stderr = str(getattr(result, "stderr", ""))
                raise TaskOperationError(f"Failed to run task command: {cmd} -> {stderr}")

        # On success, update registry
        self.registry.add_uda(uda)

    def update_uda(self, uda: UdaConfig) -> None:
        """Update an existing UDA in TaskWarrior and in the registry.

        Executes commands via adapter and updates the registry on success.

        Args:
            uda: The UdaConfig with updated settings to apply.

        Raises:
            TaskOperationError: If applying the updated configuration fails.
        """
        # For now, same as define_uda
        self.define_uda(uda)

    def delete_uda(self, uda: UdaConfig) -> None:
        """Delete a UDA from TaskWarrior and remove it from the registry.

        Executes `task config <key>` without a value to remove each UDA key.

        Args:
            uda: The UdaConfig identifying the UDA to remove.

        Raises:
            TaskOperationError: If an unexpected TaskWarrior error occurs while
                attempting to remove configuration keys (missing keys are tolerated).
        """
        # Mirror define_uda: skip 'name' and map internal 'uda_type' -> TaskWarrior 'type'
        field_names = set(uda.__class__.model_fields.keys()) - {"name"}
        keys_to_delete: list[str] = []

        if "uda_type" in field_names:
            keys_to_delete.append("type")
            field_names.remove("uda_type")

        # delete remaining fields deterministically
        keys_to_delete.extend(sorted(field_names))

        for key in keys_to_delete:
            cmd = ["config", f"uda.{uda.name}.{key}"]
            result = self.adapter.run_task_command(cmd)
            if getattr(result, "returncode", 0) != 0:
                stderr = str(getattr(result, "stderr", ""))
                # tolerate missing keys (idempotent deletion)
                if "no entry named" in stderr.lower():
                    continue
                raise TaskOperationError(f"Failed to run task command: {cmd} -> {stderr}")

        # On success, remove from registry
        self.registry.remove_uda(uda.name)
