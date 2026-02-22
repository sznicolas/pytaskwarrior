"""Data Transfer Objects for task data.

This module defines the Pydantic models used for creating, updating,
and retrieving tasks from TaskWarrior.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import Priority, RecurrencePeriod, TaskStatus
from ..exceptions import TaskValidationError
from ..utils.conversions import parse_taskwarrior_date
from .annotation_dto import AnnotationDTO


class TaskInputDTO(BaseModel):
    """Data Transfer Object for creating and updating tasks.

    This model is used when adding new tasks or modifying existing ones.
    All fields except `description` are optional.

    Attributes:
        description: Task description.
        priority: Task priority level (H, M, L, or None).
        due: Due date/time. Accepts ISO format or TaskWarrior expressions
            like "tomorrow", "friday", "eom" (end of month).
        project: Project name. Supports hierarchical projects like "work.reports".
        tags: List of tags to assign to the task.
        depends: List of UUIDs of tasks this task depends on.
        parent: UUID of the parent recurring task template.
        recur: Recurrence period for recurring tasks.
        scheduled: Earliest date/time the task can be started.
        wait: Date until which the task is hidden from pending list.
        until: Expiration date for recurring task instances.
        annotations: List of annotation strings to add to the task.
        udas: Dictionary of User Defined Attribute values (e.g., {"severity": "high"}).

    Example:
        Create a simple task::

            task = TaskInputDTO(description="Buy milk")

        Create a task with full details::

            task = TaskInputDTO(
                description="Finish project report",
                priority=Priority.HIGH,
                project="work.reports",
                tags=["urgent", "q1"],
                due="friday",
                scheduled="tomorrow",
            )

        Create a task with UDAs::

            task = TaskInputDTO(
                description="Fix critical bug",
                udas={"severity": "critical", "estimate": 2.5}
            )
    """

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
    udas: dict[str, Any] = Field(
        default_factory=dict,
        description="User Defined Attribute values (e.g., {'severity': 'high'})",
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
        """Validate that task description is not empty.

        Args:
            v: The description value to validate.

        Returns:
            The stripped description string.

        Raises:
            TaskValidationError: If the description is empty or whitespace-only.
        """
        if not v.strip():
            raise TaskValidationError("Task description cannot be empty")
        return v.strip()


class TaskOutputDTO(BaseModel):
    """Data Transfer Object for task retrieval results.

    This model represents a task as returned by TaskWarrior. It includes
    all input fields plus read-only fields set by TaskWarrior.

    Attributes:
        description: Task description.
        index: Task ID number in the working set (alias: "id").
        uuid: Unique identifier for the task.
        status: Current task status (pending, completed, deleted, etc.).
        priority: Task priority level.
        due: Due date/time as datetime object.
        entry: Task creation timestamp (read-only).
        start: Timestamp when task was started (read-only).
        end: Timestamp when task was completed (read-only).
        modified: Last modification timestamp (read-only).
        tags: List of tags assigned to the task.
        project: Project the task belongs to.
        depends: List of UUIDs of dependency tasks.
        parent: UUID of parent recurring task template.
        recur: Recurrence period if recurring.
        scheduled: Scheduled start date/time.
        wait: Date until which task is hidden.
        until: Expiration date for recurring instances.
        urgency: Calculated urgency score (read-only).
        annotations: List of annotation objects with timestamps.
        udas: Dictionary of User Defined Attribute values.
        imask: Mask for recurring tasks or instance number.
        rtype: Type of recurring task.

    Example:
        Retrieve and inspect a task::

            task = tw.get_task(uuid)
            print(f"Task #{task.index}: {task.description}")
            print(f"Status: {task.status}")
            print(f"Urgency: {task.urgency}")

        Access UDA values::

            severity = task.get_uda("severity")
            estimate = task.get_uda("estimate", default=0)
    """

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
    udas: dict[str, Any] = Field(
        default_factory=dict,
        description="User Defined Attribute values",
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
        extra="ignore",
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

    @model_validator(mode="before")
    @classmethod
    def extract_udas_from_extra_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Extract unknown fields from TaskWarrior JSON into the udas dict.

        TaskWarrior returns UDA values as top-level fields in the JSON.
        This validator captures any field not defined in the model and
        moves it to the 'udas' dictionary.

        Args:
            data: The raw input data dictionary.

        Returns:
            The data dictionary with extra fields moved to 'udas'.
        """
        if not isinstance(data, dict):
            return data

        known_fields = set(cls.model_fields.keys()) | {"id"}  # 'id' is alias for 'index'
        udas = data.get("udas", {})
        udas = dict(udas) if isinstance(udas, dict) else {}

        extra_fields = []
        for key, value in data.items():
            if key not in known_fields and not key.startswith("_"):
                udas[key] = value
                extra_fields.append(key)

        for key in extra_fields:
            del data[key]

        data["udas"] = udas
        return data

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
    def parse_datetime_field(cls, value: str | datetime | None) -> datetime:
        """Parse datetime fields from TaskWarrior format.

        Handles both TaskWarrior's compact format (20260101T193139Z)
        and standard ISO format.

        Args:
            value: The datetime value to parse, either as string or datetime.

        Returns:
            A datetime object with timezone info.
        """
        if isinstance(value, datetime):
            return value
        return parse_taskwarrior_date(value or "")

    def get_uda(self, name: str, default: Any = None) -> Any:
        """Get a User Defined Attribute value by name.

        Args:
            name: The name of the UDA to retrieve.
            default: Value to return if the UDA is not set. Defaults to None.

        Returns:
            The UDA value if set, otherwise the default value.

        Example:
            >>> task = tw.get_task(uuid)
            >>> severity = task.get_uda("severity")
            >>> estimate = task.get_uda("estimate", default=0)
        """
        return self.udas.get(name, default)
