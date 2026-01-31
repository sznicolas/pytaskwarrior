"""Registry for User Defined Attributes (UDAs).

This module provides the UdaRegistry singleton class for tracking
and managing UDA definitions.
"""

from __future__ import annotations

from pathlib import Path

from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.uda_dto import UdaConfig, UdaType
from ..exceptions import TaskWarriorError


class UdaRegistry:
    """Singleton registry for User Defined Attributes (UDAs).

    This class maintains a registry of UDA definitions, loaded from
    the taskrc file or defined programmatically. It uses the singleton
    pattern to ensure consistent state across the application.

    Attributes:
        _udas: Dictionary mapping UDA names to their definitions.

    Example:
        >>> registry = UdaRegistry()
        >>> registry.load_from_taskrc("~/.taskrc")
        >>> names = registry.get_uda_names()
    """

    _instance = None
    _udas: dict[str, UdaConfig] = {}

    def __new__(cls) -> UdaRegistry:
        """Create or return the singleton instance.

        Returns:
            The singleton UdaRegistry instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_from_taskrc(self, taskrc_file: str | Path) -> None:
        """Load UDA definitions from a taskrc file.

        Parses the taskrc file to find all `uda.*` configuration lines
        and creates UdaConfig objects for each discovered UDA.

        Args:
            taskrc_file: Path to the taskrc configuration file.

        Raises:
            TaskWarriorError: If the file doesn't exist or parsing fails.

        Example:
            >>> registry.load_from_taskrc("/path/to/.taskrc")
        """
        self._udas = {}
        try:
            with open(taskrc_file) as f:
                content = f.read()
            # Find all uda.* lines
            uda_lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip().startswith("uda.")
            ]
            # Group by UDA name
            uda_groups: dict[str, dict[str, str]] = {}
            for line in uda_lines:
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                parts = key.split(".")
                if len(parts) < 3:
                    continue
                name, attr = parts[1], parts[2]
                if name not in uda_groups:
                    uda_groups[name] = {}
                uda_groups[name][attr] = value.strip()

            # Convert to UdaConfig objects
            for name, attrs in uda_groups.items():
                try:
                    # Convert type string to UdaType enum
                    converted_attrs: dict[str, object] = {}
                    for key, value in attrs.items():
                        if key == "type":
                            converted_attrs[key] = UdaType(value)
                        elif key == "values":
                            converted_attrs[key] = value.split(",") if value else []
                        elif key == "default":
                            converted_attrs[key] = value
                        else:
                            converted_attrs[key] = value

                    self._udas[name] = UdaConfig(name=name, **converted_attrs)  # type: ignore[arg-type]
                except Exception as e:
                    raise TaskWarriorError(f"Error while parsing {name}: {str(e)}") from e

        except FileNotFoundError as e:
            raise TaskWarriorError(f"Taskrc file not found: {taskrc_file}") from e
        except Exception as e:
            raise TaskWarriorError(f"Error reading taskrc: {str(e)}") from e

    def define_update_uda(self, uda: UdaConfig, adapter: TaskWarriorAdapter) -> None:
        """Define or update a UDA in TaskWarrior configuration.

        Uses `task config` commands to set UDA properties and
        updates the local registry.

        Args:
            uda: The UDA definition to create or update.
            adapter: The TaskWarriorAdapter for executing commands.
        """
        # Get all field names from UdaConfig
        field_names = uda.__class__.model_fields.keys() - {"name"}
        # Process the type
        field_names -= {"type"}
        adapter.run_task_command(
            ["config", f"uda.{uda.name}.type", uda.type.value]
        )

        # Process each field that has a value
        for field_name in field_names:
            value = getattr(uda, field_name)
            if value is not None and value != "":
                config_key = f"uda.{uda.name}.{field_name}"
                adapter.run_task_command(["config", config_key, str(value)])
        self._udas.update({uda.name: uda})

    def delete_uda(self, uda: UdaConfig, adapter: TaskWarriorAdapter) -> None:
        """Delete a UDA from TaskWarrior configuration.

        Clears all UDA configuration entries and removes it from the registry.

        Args:
            uda: The UDA to delete.
            adapter: The TaskWarriorAdapter for executing commands.
        """
        # Clear all UDA configuration entries by setting them to empty strings
        field_names = uda.__class__.model_fields.keys()
        for key in field_names:
            adapter.run_task_command(["config", f"uda.{uda.name}.{key}"])
        self._udas.pop(uda.name)

    def get_uda(self, name: str) -> UdaConfig | None:
        """Get a UDA definition by name.

        Args:
            name: The name of the UDA to retrieve.

        Returns:
            The UdaConfig if found, None otherwise.
        """
        return self._udas.get(name)

    def get_uda_names(self) -> set[str]:
        """Get all registered UDA names.

        Returns:
            Set of UDA names currently in the registry.
        """
        return set(self._udas.keys())

    def is_uda_field(self, field_name: str) -> bool:
        """Check if a field name corresponds to a registered UDA.

        Args:
            field_name: The field name to check.

        Returns:
            True if the field is a registered UDA, False otherwise.
        """
        return field_name in self._udas
