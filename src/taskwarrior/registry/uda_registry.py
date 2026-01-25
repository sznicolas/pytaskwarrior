from src.taskwarrior.adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.uda_dto import UdaDTO, UdaType
from ..exceptions import TaskWarriorError


class UdaRegistry:
    """Registry for User Defined Attributes (UDAs) read from taskrc file."""

    _instance = None
    _udas: dict[str, UdaDTO] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_from_taskrc(self, taskrc_file) -> None:
        """Load UDAs from taskrc file."""
        self._udas = {}
        try:
            with open(taskrc_file, "r") as f:
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
                    raise TaskWarriorError(f"Error while parsing {name}: {str(e)}")

        except FileNotFoundError:
            raise TaskWarriorError(f"Taskrc file not found: {taskrc_file}")
        except Exception as e:
            raise TaskWarriorError(f"Error reading taskrc: {str(e)}")

    def define_update_uda(self, uda: UdaDTO, adapter: TaskWarriorAdapter) -> None:
        """Define or modify a User Defined Attribute (UDA) using task config commands."""
        # Get all field names from UdaDTO
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

    def delete_uda(self, uda: UdaDTO, adapter: TaskWarriorAdapter) -> None:
        """Delete a User Defined Attribute (UDA) by clearing its configuration."""
        # Clear all UDA configuration entries by setting them to empty strings
        field_names = uda.__class__.model_fields.keys()
        for key in field_names:
            adapter.run_task_command(["config", key, ""])
        self._udas.pop(uda.name)

    def get_uda(self, name: str) -> UdaDTO | None:
        """Get UDA definition by name."""
        return self._udas.get(name)

    def get_uda_names(self) -> set[str]:
        """Get all defined UDA names."""
        return set(self._udas.keys())

    def is_uda_field(self, field_name: str) -> bool:
        """Check if a field name corresponds to a defined UDA."""
        return field_name in self._udas
