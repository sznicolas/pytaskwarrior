from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..enums import TaskStatus


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
