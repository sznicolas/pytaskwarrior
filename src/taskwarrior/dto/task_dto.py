from __future__ import annotations
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums import TaskStatus, Priority, RecurrencePeriod
from ..exceptions import TaskValidationError


class TaskInputDTO(BaseModel):
    """Data Transfer Object for task input (creation/update)."""

    description: str = Field(..., description="Task description (required).")
    priority: Priority | None = Field(
        default=None, description="Priority of the task (H, M, L, or empty)"
    )
    due: str | None = Field(
        default=None, description="Due date and time for the task (ISO format)"
    )
    project: str | None = Field(
        default=None, description="Project the task belongs to"
    )
    tags: list[str] = Field(
        default_factory=list, description="List of tags associated with the task"
    )
    depends: list[UUID] = Field(
        default_factory=list, description="List of UUIDs of tasks this task depends on"
    )
    parent: UUID | None = Field(
        default=None, description="UUID of the template task"
    )
    recur: RecurrencePeriod | None = Field(
        default=None, description="Recurrence period for recurring tasks"
    )
    scheduled: str | None = Field(
        default=None,
        description="Schedule the earlier time the task can be done (ISO format)",
    )
    wait: str | None = Field(
        default=None, description="The task is hidden until the date (ISO format)"
    )
    until: str | None = Field(
        default=None, description="Expiration date for recurring tasks (ISO format)"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        extra='forbid',
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {"description": "a task"},
                {
                    "description": "a due task in two weeks for lambda project",
                    "due": "P2W",
                    "project": "lambda",
                },
            ]
        },
    )

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        """Validate that task description is not empty."""
        if not v.strip():
            raise TaskValidationError("Task description cannot be empty")
        return v.strip()


class TaskOutputDTO(BaseModel):
    """Data Transfer Object for task output (retrieval)."""

    description: str = Field(..., description="Task description (required).")
    index: int = Field(
        alias="id",
        description="READONLY Task index of a task in the working set",
    )
    uuid: UUID = Field(
        description="READONLY Unique identifier for the task"
    )
    status: TaskStatus = Field(
        description="Current status of the task"
    )
    priority: Priority | None = Field(
        default=None, description="Priority of the task (H, M, L, or empty)"
    )
    due: datetime | None = Field(
        default=None, description="Due date and time for the task (ISO format)"
    )
    entry: datetime | None = Field(
        default=None, description="READONLY Task creation date and time (ISO format)"
    )
    start: datetime | None = Field(
        default=None, description="READONLY Task started date and time (ISO format)"
    )
    end: datetime | None = Field(
        default=None, description="READONLY Task done date and time (ISO format)"
    )
    modified: datetime | None = Field(
        default=None,
        description="READONLY Last modification date and time (ISO format)",
    )
    tags: list[str] = Field(
        default_factory=list, description="List of tags associated with the task"
    )
    project: str | None = Field(
        default=None, description="Project the task belongs to"
    )
    depends: list[UUID] = Field(
        default_factory=list, description="List of UUIDs of tasks this task depends on"
    )
    parent: UUID | None = Field(
        default=None, description="UUID of the template task"
    )
    recur: RecurrencePeriod | None = Field(
        default=None, description="Recurrence period for recurring tasks"
    )
    scheduled: datetime | None = Field(
        default=None,
        description="Schedule the earlier time the task can be done (ISO format)",
    )
    wait: datetime | None = Field(
        default=None, description="The task is hidden until the date (ISO format)"
    )
    until: datetime | None = Field(
        default=None, description="Expiration date for recurring tasks (ISO format)"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        populate_by_name=True,
        extra='forbid',
        json_schema_extra={
            "examples": [
                {"description": "a task"},
                {
                    "description": "a due task in two weeks for lambda project",
                    "due": "P2W",
                    "project": "lambda",
                },
            ]
        },
    )

    @field_validator(
        "entry",
        "start",
        "end",
        "modified",
        "due",
        "scheduled",
        "wait",
        "until",
        mode="before",
    )
    @classmethod
    def parse_datetime_field(cls, value):
        if not isinstance(value, str) or value is None:
            return value

        # Handle TaskWarrior's date format (20260101T193139Z)
        try:
            # Check if it's the compact format used by TaskWarrior
            if len(value) == 16 and "T" in value and value.endswith("Z"):
                # Convert compact format to standard: 20260101T193139Z -> 2026-01-01T19:31:39Z
                date_part = value[:8]
                time_part = value[9:-1]  # Remove 'T' and 'Z'
                formatted = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
                return datetime.fromisoformat(formatted.replace("Z", "+00:00"))
            else:
                # Try standard parsing
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            # If parsing fails, return the original value
            return value
