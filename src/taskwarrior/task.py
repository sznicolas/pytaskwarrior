from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Union, get_args, get_origin
from uuid import UUID

import isodate
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

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

# Pydantic Models
class TaskInternal(BaseModel):
    """Represents a TaskWarrior task with full internal validation and logic."""
    
    description: str = Field(..., description="Task description (required).")
    index: Optional[int] = Field(default=None, alias='id', description="READONLY Task index of a task in the working set")
    uuid: Optional[UUID] = Field(default=None, description="READONLY Unique identifier for the task")
    status: Optional[TaskStatus] = Field(default=None, description="Current status of the task")
    priority: Optional[Priority] = Field(default=None, description="Priority of the task (H, M, L, or empty)")
    due: Optional[Union[datetime, timedelta]] = Field(default=None, description="Due date and time for the task")
    entry: Optional[datetime] = Field(default=None, description="READONLY Task creation date and time")
    start: Optional[datetime] = Field(default=None, description="READONLY Task started date and time")
    end: Optional[datetime] = Field(default=None, description="READONLY Task done date and time")
    modified: Optional[datetime] = Field(default=None, description="READONLY Last modification date and time")
    tags: List[str] = Field(default_factory=list, description="List of tags associated with the task")
    project: Optional[str] = Field(default=None, description="Project the task belongs to")
    depends: List[UUID] = Field(default_factory=list, description="List of UUIDs of tasks this task depends on")
    parent: Optional[UUID] = Field(default=None, description="UUID of the template task")
    recur: Optional[RecurrencePeriod] = Field(default=None, description="Recurrence period for recurring tasks")
    scheduled: Optional[Union[datetime, timedelta]] = Field(default=None, description="Schedule the earlier time the task can be done")
    wait: Optional[Union[datetime, timedelta]] = Field(default=None, description="The task is hidden until the date")
    until: Optional[Union[datetime, timedelta]] = Field(default=None, description="Expiration date for recurring tasks")
    context: Optional[str] = Field(default=None, description="Context filter for the task")

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        """Validate that task description is not empty."""
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags."""
        return [tag.strip() for tag in v if tag.strip()]

    @field_serializer('uuid')
    def serialize_uuid(self, uuid: UUID) -> str:
        """Serialize UUID to string."""
        return str(uuid)
    
    @field_serializer('due', 'scheduled', 'wait', 'until')
    def serialize_datetime_or_timedelta(self, value: Union[datetime, timedelta]) -> str:
        """Serialize datetime or timedelta fields to appropriate format."""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, timedelta):
            # Convert timedelta to ISO duration format
            return isodate.duration_isoformat(value)
        else:
            # For other types, convert to string
            return str(value)
    
    @field_serializer('tags')
    def serialize_tags(self, tags: List[str]) -> str:
        """Serialize tags to comma-separated string."""
        return ','.join(tags)
    
    @field_serializer('depends')
    def serialize_depends(self, depends: List[UUID]) -> str:
        """Serialize dependencies to comma-separated string of UUIDs."""
        return ','.join(str(dep) for dep in depends)
