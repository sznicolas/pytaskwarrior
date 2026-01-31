"""Data Transfer Objects for User Defined Attributes (UDAs).

UDAs allow extending TaskWarrior with custom fields beyond the
built-in attributes.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class UdaType(str, Enum):
    """Data types for User Defined Attributes.

    TaskWarrior supports several data types for custom attributes.
    The type determines how values are validated and displayed.

    Attributes:
        STRING: Free-form text value.
        NUMERIC: Numeric value (integer or float).
        DATE: Date/time value in TaskWarrior format.
        DURATION: Duration value (e.g., "2hours", "1day").
        UUID: UUID reference to another task.

    Example:
        >>> from taskwarrior.dto.uda_dto import UdaConfig, UdaType
        >>> uda = UdaConfig(name="severity", type=UdaType.STRING)
    """

    STRING = "string"
    NUMERIC = "numeric"
    DATE = "date"
    DURATION = "duration"
    UUID = "uuid"


class UdaConfig(BaseModel):
    """Data Transfer Object for User Defined Attributes (UDAs).

    UDAs extend TaskWarrior with custom fields. Each UDA has a name,
    type, and optional configuration like allowed values or defaults.

    Attributes:
        name: Unique name for the UDA (used as the field name).
        type: Data type of the UDA value.
        label: Human-readable label for display in reports.
        values: List of allowed values (for string type with enumeration).
        default: Default value when not specified.
        coefficient: Urgency coefficient. Positive values increase urgency,
            negative values decrease it.

    Example:
        Define a severity UDA with allowed values::

            uda = UdaConfig(
                name="severity",
                type=UdaType.STRING,
                label="Severity",
                values=["low", "medium", "high", "critical"],
                default="medium",
                coefficient=1.5
            )
            tw.uda_service.define_uda(uda)
    """

    name: str = Field(..., description="Name of the UDA")
    type: UdaType = Field(..., description="Data type of the UDA")
    label: str | None = Field(default=None, description="Display label for the UDA")
    values: list[str] | None = Field(
        default=None, description="Allowed values for the UDA (for string types)"
    )
    default: str | None = Field(default=None, description="Default value")
    coefficient: float | None = Field(
        default=None,
        description="Urgency coefficient applied, influencing task priority",
    )

    model_config = {"populate_by_name": True, "extra": "forbid"}
