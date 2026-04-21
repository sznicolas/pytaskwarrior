"""Registry for User Defined Attributes (UDAs).

This module provides the UdaRegistry class for tracking and managing UDA definitions.

The registry no longer performs direct file I/O. UDA discovery is performed
via ConfigStore (ConfigStore.get_udas()) or by passing an in-memory config
mapping to `load_from_config`.
"""

from __future__ import annotations

from ..dto.uda_dto import UdaConfig


class UdaRegistry:
    """Registry for User Defined Attributes (UDAs).

    This class maintains a registry of UDA definitions loaded from in-memory
    configuration mappings or provided by a ConfigStore instance. It intentionally
    avoids performing direct file I/O to keep concerns separated.

    Example:
        >>> registry = UdaRegistry()
        >>> registry.load_from_config({"uda.example.type": "string"})
        >>> names = registry.get_uda_names()
    """

    def __init__(self) -> None:
        self._udas: dict[str, UdaConfig] = {}

    def register_udas(self, udas: list[UdaConfig]) -> None:
        """Register a list of UdaConfig objects into the registry."""
        for uda in udas:
            self._udas[uda.name] = uda

    def load_from_config(self, config: dict[str, str]) -> None:
        """Load UDA definitions from an in-memory config mapping.

        The config mapping should contain keys like 'uda.<name>.<attr>'.
        This avoids direct file I/O and allows using ConfigStore.config.
        """
        # Local import to avoid module import cycles
        from ..config.uda_parser import parse_udas_from_mapping

        udas = parse_udas_from_mapping(config)
        self.register_udas(udas)

    def add_uda(self, uda: UdaConfig) -> None:
        """Add a UDA definition to the in-memory registry (no side effects)."""
        self._udas[uda.name] = uda

    def update_uda(self, uda: UdaConfig) -> None:
        """Update an existing UDA definition in the registry (no side effects)."""
        self._udas[uda.name] = uda

    def remove_uda(self, name: str) -> None:
        """Remove a UDA definition from the registry by name (no side effects)."""
        self._udas.pop(name, None)

    def get_uda(self, name: str) -> UdaConfig | None:
        """Get a UDA definition by name."""
        return self._udas.get(name)

    def get_uda_names(self) -> set[str]:
        """Get all registered UDA names."""
        return set(self._udas.keys())

    def is_uda_field(self, field_name: str) -> bool:
        """Check if a field name corresponds to a registered UDA."""
        return field_name in self._udas

    def get_udas(self) -> list[UdaConfig]:
        """Return all registered UdaConfig objects as a list.

        This provides a direct way to retrieve the full UdaConfig objects
        currently stored in the registry.
        """
        return list(self._udas.values())
