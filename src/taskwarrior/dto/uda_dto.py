from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field

class UdaType(str, Enum):
    """Types of User Defined Attributes in TaskWarrior."""
    STRING = "string"
    NUMERIC = "numeric"
    DATE = "date"
    BOOLEAN = "boolean"
    TAG = "tag"

class UdaDTO(BaseModel):
    """Data Transfer Object for User Defined Attributes (UDAs)."""

    name: str = Field(..., description="Name of the UDA")
    type: UdaType = Field(..., description="Data type of the UDA")
    label: str | None = Field(default=None, description="Display label for the UDA")
    values: list[str] | None = Field(default=None, description="Allowed values for the UDA (for string types)")
    coefficient: float = Field(default=1.0, description="Urgency coefficient applied, influencing task priority")
    orphaned: bool = Field(default=False, description="Whether the UDA is orphaned (not used by any task)")

    model_config = {
        "populate_by_name": True,
        "extra": "forbid"
    }
