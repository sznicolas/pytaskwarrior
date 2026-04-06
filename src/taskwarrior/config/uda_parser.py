"""Parser utilities to convert TaskWarrior config mappings into UdaConfig DTOs.

This module centralizes the logic that converts a mapping of configuration
keys (as produced by ConfigStore.config) into UdaConfig DTOs.
"""

from __future__ import annotations

from ..dto.uda_dto import UdaConfig, UdaType
from ..exceptions import TaskWarriorError


def parse_udas_from_mapping(config: dict[str, str]) -> list[UdaConfig]:
    """Parse UDA definitions from a config mapping.

    Accepts keys like 'uda.<name>.<attr>' or 'taskrc.uda.<name>.<attr>'.
    Returns a list of UdaConfig objects.

    Raises TaskWarriorError on parsing errors.
    """
    uda_groups: dict[str, dict[str, str]] = {}
    for key, value in config.items():
        if not key:
            continue
        k = key.strip()
        # normalize 'taskrc.' prefix if present
        if k.startswith("taskrc."):
            k = k[len("taskrc.") :]
        if not k.startswith("uda."):
            continue
        parts = k.split(".")
        if len(parts) < 3:
            continue
        name, attr = parts[1], parts[2]
        uda_groups.setdefault(name, {})[attr] = value

    udas: list[UdaConfig] = []
    for name, attrs in uda_groups.items():
        try:
            converted_attrs: dict[str, object] = {}
            for attr, val in attrs.items():
                if attr == "type":
                    try:
                        converted_attrs["uda_type"] = UdaType(val)
                    except ValueError:
                        converted_attrs["uda_type"] = UdaType(val.lower())
                elif attr == "values":
                    converted_attrs["values"] = [v.strip() for v in val.split(",")] if val else []
                elif attr == "coefficient":
                    try:
                        converted_attrs["coefficient"] = float(val)
                    except (TypeError, ValueError):
                        converted_attrs["coefficient"] = None
                elif attr == "label":
                    converted_attrs["label"] = val
                elif attr == "default":
                    converted_attrs["default"] = val
                else:
                    converted_attrs[attr] = val

            uda = UdaConfig(name=name, **converted_attrs)  # type: ignore[arg-type]
            udas.append(uda)
        except Exception as e:
            raise TaskWarriorError(f"Error while parsing UDA '{name}': {e}") from e
    return udas
