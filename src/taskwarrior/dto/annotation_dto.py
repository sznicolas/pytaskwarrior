"""Data Transfer Object for task annotations.

Annotations are timestamped notes that can be attached to tasks.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..utils.conversions import parse_taskwarrior_date


class AnnotationDTO(BaseModel):
    """Data Transfer Object for task annotations.

    Annotations are timestamped notes attached to tasks. Each annotation
    records when it was added and its content.

    Attributes:
        entry: Timestamp when the annotation was created.
        description: The annotation text content.

    Example:
        Annotations are typically retrieved as part of a task::

            task = tw.get_task(uuid)
            for annotation in task.annotations:
                print(f"{annotation.entry}: {annotation.description}")
    """

    entry: datetime = Field(
        description="Annotation creation date and time (ISO format)"
    )
    description: str = Field(description="Annotation description")

    model_config = {"populate_by_name": True, "extra": "forbid"}

    @field_validator("entry", mode="before")
    @classmethod
    def parse_entry_date(cls, value: str | datetime | None) -> datetime:
        """Parse the entry date from TaskWarrior format.

        Args:
            value: The date value, either as string or datetime.

        Returns:
            A datetime object with timezone info.
        """
        if isinstance(value, datetime):
            return value
        return parse_taskwarrior_date(value or "")
