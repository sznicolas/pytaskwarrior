from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID

import isodate
from pydantic import BaseModel, ConfigDict, Field

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

class TaskDTO(BaseModel):
    """Data Transfer Object for task representation with clean JSON schema."""
    
    description: str = Field(..., description="Task description (required).")
    index: Optional[int] = Field(default=None, alias='id', description="READONLY Task index of a task in the working set")
    uuid: Optional[UUID] = Field(default=None, description="READONLY Unique identifier for the task")
    status: Optional[TaskStatus] = Field(default=None, description="Current status of the task")
    priority: Optional[Priority] = Field(default=None, description="Priority of the task (H, M, L, or empty)")
    due: Optional[str] = Field(default=None, description="Due date and time for the task (ISO format)")
    entry: Optional[str] = Field(default=None, description="READONLY Task creation date and time (ISO format)")
    start: Optional[str] = Field(default=None, description="READONLY Task started date and time (ISO format)")
    end: Optional[str] = Field(default=None, description="READONLY Task done date and time (ISO format)")
    modified: Optional[str] = Field(default=None, description="READONLY Last modification date and time (ISO format)")
    tags: List[str] = Field(default_factory=list, description="List of tags associated with the task")
    project: Optional[str] = Field(default=None, description="Project the task belongs to")
    depends: List[str] = Field(default_factory=list, description="List of UUIDs of tasks this task depends on")
    parent: Optional[str] = Field(default=None, description="UUID of the template task")
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
