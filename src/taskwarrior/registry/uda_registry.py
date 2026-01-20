from pathlib import Path
from ..dto.uda_dto import UdaDTO, UdaType
from ..exceptions import TaskWarriorError, TaskValidationError


class UdaRegistry:
    """Registry for User Defined Attributes (UDAs) read from taskrc file."""

    _instance = None
    _udas: dict[str, UdaDTO] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_from_taskrc(self, taskrc_path: str = "~/.taskrc") -> None:
        """Load UDAs from taskrc file."""
        self._udas = {}
        try:
            with open(Path(taskrc_path).expanduser(), "r") as f:
                content = f.read()
            # Find all uda.* lines
            uda_lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip().startswith("uda.")
            ]
            # Group by UDA name
            uda_groups = {}
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

            # Convert to UdaDTO objects
            for name, attrs in uda_groups.items():
                try:
                    # Convert type string to UdaType enum
                    if "type" in attrs:
                        attrs["type"] = UdaType(attrs["type"])

                    self._udas[name] = UdaDTO(name=name, **attrs)
                except Exception as e:
                    raise TaskWarriorError(f"Error while parsong {name}: {str(e)}")

        except FileNotFoundError:
            raise TaskWarriorError(f"Taskrc file not found: {taskrc_path}")
        except Exception as e:
            raise TaskWarriorError(f"Error reading taskrc: {str(e)}")

    def define_uda(self, uda: UdaDTO) -> None:
        """Define or modify a User Defined Attribute (UDA) using task config commands."""
        # Set the UDA type
        self.adapter.run_task_command(["config", f"uda.{name}.type", type_])
    
        # Set other attributes if provided
        if label:
            self.adapter.run_task_command(["config", f"uda.{name}.label", label])
        if default:
            self.adapter.run_task_command(["config", f"uda.{name}.default", default])
        if values:
            self.adapter.run_task_command(["config", f"uda.{name}.values", values])
    
    def delete_uda(self, name: str) -> None:
        """Delete a User Defined Attribute (UDA) by clearing its configuration."""
        # Clear all UDA configuration entries by setting them to empty strings
        config_keys = [
            f"uda.{name}.type",
            f"uda.{name}.label",
            f"uda.{name}.default",
            f"uda.{name}.values",
            f"uda.{name}.readonly"
        ]

    for key in config_keys:
        self.adapter.run_task_command(["config", key, ""])

    def get_uda(self, name: str) -> UdaDTO | None:
        """Get UDA definition by name."""
        return self._udas.get(name)

    def get_uda_names(self) -> set[str]:
        """Get all defined UDA names."""
        return set(self._udas.keys())

    def is_uda_field(self, field_name: str) -> bool:
        """Check if a field name corresponds to a defined UDA."""
        return field_name in self._udas
