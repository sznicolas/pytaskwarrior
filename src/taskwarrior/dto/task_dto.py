from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums import Priority, RecurrencePeriod, TaskStatus
from ..exceptions import TaskValidationError
from ..utils.conversions import parse_taskwarrior_date
from .annotation_dto import AnnotationDTO


class TaskInputDTO(BaseModel):
    """Data Transfer Object for task input (creation/update)."""

    description: str = Field(..., description="Task description (required).")
    priority: Priority | None = Field(
        default=None, description="Priority of the task (H, M, L, or empty)"
    )
    due: str | None = Field(
        default=None, description="Due date and time for the task (ISO format)"
    )
    project: str | None = Field(default=None, description="Project the task belongs to")
    tags: list[str] = Field(
        default_factory=list, description="List of tags associated with the task"
    )
    depends: list[UUID] = Field(
        default_factory=list, description="List of UUIDs of tasks this task depends on"
    )
    parent: UUID | None = Field(default=None, description="UUID of the template task")
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
    annotations: list[str] = Field(
        default_factory=list, description="List of annotations for the task"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
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
    uuid: UUID = Field(description="READONLY Unique identifier for the task")
    status: TaskStatus = Field(description="Current status of the task")
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
    project: str | None = Field(default=None, description="Project the task belongs to")
    depends: list[UUID] = Field(
        default_factory=list, description="List of UUIDs of tasks this task depends on"
    )
    parent: UUID | None = Field(default=None, description="UUID of the template task")
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
    urgency: float | None = Field(default=None, description="Task urgency score")
    annotations: list[AnnotationDTO] = Field(
        default_factory=list, description="List of annotations for the task"
    )
    imask: str | int | None = Field(
        default=None,
        description="Mask for recurring tasks if str, or the instance number if int",
    )
    rtype: str | None = Field(default=None, description="Type of recurring task")

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        populate_by_name=True,
        extra="forbid",
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
        return parse_taskwarrior_date(value)
