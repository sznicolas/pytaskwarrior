from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..utils.conversions import parse_taskwarrior_date


class AnnotationDTO(BaseModel):
    """Data Transfer Object for task annotations."""

    entry: datetime = Field(
        description="Annotation creation date and time (ISO format)"
    )
    description: str = Field(description="Annotation description")

    model_config = {"populate_by_name": True, "extra": "forbid"}

    @field_validator("entry", mode="before")
    @classmethod
    def parse_entry_date(cls, value):
        return parse_taskwarrior_date(value)
