from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..enums import TaskStatus



def parse_taskwarrior_date(value):
    """Parse TaskWarrior date format (20260101T193139Z) to datetime."""
    if not isinstance(value, str) or value is None:
        return value

    try:
        # Handle TaskWarrior's compact format (20260101T193139Z)
        if len(value) == 16 and "T" in value and value.endswith("Z"):
            # Convert compact format to standard: 20260101T193139Z -> 2026-01-01T19:31:39Z
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        else:
            # Try standard parsing
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        # If parsing fails, return the original value
        return value

class AnnotationDTO(BaseModel):
    """Data Transfer Object for task annotations."""

    entry: datetime = Field(
        description="Annotation creation date and time (ISO format)"
    )
    description: str = Field(
        description="Annotation description"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "forbid"
    }

    @field_validator("entry", mode="before")
    @classmethod
    def parse_entry_date(cls, value):
        return parse_taskwarrior_date(value)
