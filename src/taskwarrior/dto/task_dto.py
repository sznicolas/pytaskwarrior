from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Enums for TaskWarrior-specific fields
class TaskStatus(str, Enum):
    """Task status as defined by TaskWarrior."""
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    WAITING = "waiting"
    RECURRING = "recurring"

class Priority(str, Enum):
    """Task priority levels in TaskWarrior."""
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""

class RecurrencePeriod(str, Enum):
    """Supported recurrence periods for tasks."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"

class TaskInputDTO(BaseModel):
    """Data Transfer Object for task input (creation/update)."""
    description: str = Field(..., description="Task description (required).")
    priority: Optional[Priority] = Field(default=None, description="Priority of the task (H, M, L, or empty)")
    due: Optional[str] = Field(default=None, description="Due date and time for the task (ISO format)")
    project: Optional[str] = Field(default=None, description="Project the task belongs to")
    tags: List[str] = Field(default_factory=list, description="List of tags associated with the task")
    depends: List[UUID] = Field(default_factory=list, description="List of UUIDs of tasks this task depends on")
    parent: Optional[UUID] = Field(default=None, description="UUID of the template task")
    recur: Optional[RecurrencePeriod] = Field(default=None, description="Recurrence period for recurring tasks")
    scheduled: Optional[str] = Field(default=None, description="Schedule the earlier time the task can be done (ISO format)")
    wait: Optional[str] = Field(default=None, description="The task is hidden until the date (ISO format)")
    until: Optional[str] = Field(default=None, description="Expiration date for recurring tasks (ISO format)")
    context: Optional[str] = Field(default=None, description="Context filter for the task")

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_schema_extra={
            'examples': [
                {
                    'description': 'a task'
                },
                {
                    'description': 'a due task in two weeks for lambda project',
                    'due': 'P2W',
                    'project': 'lambda'
                },
            ]
        }
    )

class TaskOutputDTO(BaseModel):
    """Data Transfer Object for task output (retrieval)."""
    
    description: str = Field(..., description="Task description (required).")
    index: Optional[int] = Field(default=None, alias='id', description="READONLY Task index of a task in the working set")
    uuid: Optional[UUID] = Field(default=None, description="READONLY Unique identifier for the task")
    status: Optional[TaskStatus] = Field(default=None, description="Current status of the task")
    priority: Optional[Priority] = Field(default=None, description="Priority of the task (H, M, L, or empty)")
    due: Optional[datetime] = Field(default=None, description="Due date and time for the task (ISO format)")
    entry: Optional[datetime] = Field(default=None, description="READONLY Task creation date and time (ISO format)")
    start: Optional[datetime] = Field(default=None, description="READONLY Task started date and time (ISO format)")
    end: Optional[datetime] = Field(default=None, description="READONLY Task done date and time (ISO format)")
    modified: Optional[datetime] = Field(default=None, description="READONLY Last modification date and time (ISO format)")
    tags: List[str] = Field(default_factory=list, description="List of tags associated with the task")
    project: Optional[str] = Field(default=None, description="Project the task belongs to")
    depends: List[UUID] = Field(default_factory=list, description="List of UUIDs of tasks this task depends on")
    parent: Optional[UUID] = Field(default=None, description="UUID of the template task")
    recur: Optional[RecurrencePeriod] = Field(default=None, description="Recurrence period for recurring tasks")
    scheduled: Optional[datetime] = Field(default=None, description="Schedule the earlier time the task can be done (ISO format)")
    wait: Optional[datetime] = Field(default=None, description="The task is hidden until the date (ISO format)")
    until: Optional[datetime] = Field(default=None, description="Expiration date for recurring tasks (ISO format)")
    context: Optional[str] = Field(default=None, description="Context filter for the task")

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        json_schema_extra={
            'examples': [
                {
                    'description': 'a task'
                },
                {
                    'description': 'a due task in two weeks for lambda project',
                    'due': 'P2W',
                    'project': 'lambda'
                },
            ]
        }
    )

    @field_validator('entry', 'start', 'end', 'modified', 'due', 'scheduled', 'wait', 'until', mode='before')
    @classmethod
    def parse_datetime_field(cls, value):
        if not isinstance(value, str) or value is None:
            return value

        # Handle TaskWarrior's date format (20260101T193139Z)
        try:
            # Try to parse the compact format directly
            if len(value) == 16 and 'T' in value and value.endswith('Z'):
                # Convert compact format to standard: 20260101T193139Z -> 2026-01-01T19:31:39Z
                date_part = value[:8]
                time_part = value[9:-1]  # Remove 'T' and 'Z'
                formatted = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
                return datetime.fromisoformat(formatted.replace('Z', '+00:00'))
            else:
                # Try standard parsing
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except Exception:
            # If parsing fails, return the original value
            return value
