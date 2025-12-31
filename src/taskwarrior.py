"""
PyTaskWarrior: A Python wrapper for TaskWarrior CLI

This module provides a Python interface to interact with TaskWarrior,
a command-line task management tool.
"""

from __future__ import annotations
import json
import logging
import shutil
import subprocess
from datetime import datetime, timedelta
from enum import Enum
from os import environ, getenv, path
from typing import List, Optional, Union, get_args, get_origin
from uuid import UUID

import isodate
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

# Configure logging
logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__author__ = "TaskWarrior Python Team"

# Default configuration values
DEFAULT_TASKRC_PATH = 'pytaskrc'
DEFAULT_TASKRC_CONTENT = """
# Default configuration set by pytaskwarrior
confirmation=0
news.version=99.99.99 # disable news output
"""
DEFAULT_CONFIG_OVERRIDES = {
    "confirmation": "off",
    "json.array": "TRUE",
    "verbose": "nothing"
}

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

def parse_datetime_or_timedelta(val) -> str:
    """Convert datetime or timedelta to ISO format string."""
    if isinstance(val, timedelta):
        return isodate.duration_isoformat(val)
    else:
        return str(val)

# Pydantic Models
class Task(BaseModel):
    """Represents a TaskWarrior task."""
    
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

    @field_validator('*', mode='before')
    @classmethod
    def modify_date_format(cls, v, info) -> Union[datetime, timedelta, str]:
        """Convert date strings to datetime objects."""
        field_type = cls.model_fields[info.field_name].annotation

        def contains_datetime_or_timedelta(t):
            origin = get_origin(t)
            if origin in (Union, Optional):
                return any(contains_datetime_or_timedelta(arg) for arg in get_args(t))
            return t in (datetime, timedelta)

        if contains_datetime_or_timedelta(field_type) and isinstance(v, str):
            # Try parsing as datetime
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Try parsing as duration
                try:
                    isodate.parse_duration(v)
                except isodate.ISO8601Error:
                    raise ValueError("Could not parse as datetime or timedelta")
        return v
    
    @field_serializer('uuid')
    def serialize_uuid(self, uuid: UUID) -> str:
        """Serialize UUID to string."""
        return str(uuid)

class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    
    def __init__(
        self,
        taskrc_path: Optional[str] = None,
        task_cmd: Optional[str] = None
    ):
        """
        Initialize the TaskWarrior API.
        
        Args:
            taskrc_path: Optional path to the .taskrc file. If None, uses default.
            task_cmd: Optional path to the task command. If None, searches PATH.
            
        Raises:
            RuntimeError: If TaskWarrior is not installed or accessible.
        """
        self.taskrc_path = taskrc_path or getenv('TASKRC', path.join(path.dirname(__file__), DEFAULT_TASKRC_PATH))
        environ['TASKRC'] = self.taskrc_path
        
        # Create taskrc file if it doesn't exist
        try:
            with open(self.taskrc_path, 'x') as file:
                logger.info(f'Creating taskrc file "{self.taskrc_path}"')
                file.write(DEFAULT_TASKRC_CONTENT)
        except FileExistsError:
            pass  # File already exists, that's fine
        
        self.task_cmd = task_cmd or shutil.which('task')
        if not self.task_cmd:
            raise RuntimeError("Taskwarrior is not found in PATH.")
        
        self._validate_taskwarrior()

    def _validate_taskwarrior(self) -> None:
        """Ensure Taskwarrior is installed and accessible."""
        try:
            subprocess.run(
                [self.task_cmd, "--version"], 
                capture_output=True, 
                check=True,
                text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Taskwarrior is not installed or not found in PATH.")

    def _build_args(self, task: Task) -> List[str]:
        """Build command arguments from a Task object."""
        args = []
        
        # Add description as separate words
        if task.description:
            args.extend(task.description.split())
        
        # Add other fields
        if task.priority:
            args.append(f"priority:{task.priority}")
        
        if task.due:
            args.append(f"due:{parse_datetime_or_timedelta(task.due)}")
        
        if task.until:
            args.append(f"until:{parse_datetime_or_timedelta(task.until)}")
        
        if task.scheduled:
            args.append(f"scheduled:{parse_datetime_or_timedelta(task.scheduled)}")
        
        if task.wait:
            args.append(f"wait:{parse_datetime_or_timedelta(task.wait)}")
        
        if task.project:
            args.append(f"project:{task.project}")
        
        # Add tags
        if task.tags:
            args.extend([f"+{tag}" for tag in task.tags])
        
        if task.recur:
            args.append(f"recur:{task.recur}")
        
        if task.depends:
            args.append(f"depends:{','.join(str(uuid) for uuid in task.depends)}")
        
        if task.context:
            args.append(f"context:{task.context}")
            
        return args

    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Execute a TaskWarrior command via subprocess.
        
        Args:
            args: List of command arguments to append to the base task command.
            
        Returns:
            subprocess.CompletedProcess: Result of the command execution.
            
        Raises:
            RuntimeError: If the command fails.
        """
        command = [self.task_cmd] + args
        logger.debug(f"Executing command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                env={**environ}
            )
            logger.debug(f"Command output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"TaskWarrior command failed: {e.stderr}")
            raise RuntimeError(f"TaskWarrior command failed: {e.stderr}")

    def add_task(self, task: Task) -> Task:
        """
        Add a new task to TaskWarrior.
        
        Args:
            task: Task object to add
            
        Returns:
            Task: The created task with UUID and other metadata
        """
        args = ['add']
        args += self._build_args(task)
        
        result = self._run_task_command(args)
        
        # Extract task ID from output
        task_id = None
        for line in result.stdout.splitlines():
            if 'Created task' in line:
                # Extract the number after "Created task"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'Created' and i + 1 < len(parts) and parts[i+1] == 'task':
                        task_id = int(parts[i+2].strip("."))
                        break
        
        if not task_id:
            raise RuntimeError("Failed to create task - no ID returned")
            
        return self.get_task(task_id)

    def modify_task(self, task: Task) -> Task:
        """
        Modify an existing task in TaskWarrior.
        
        Args:
            task: Task object with updated fields
            
        Returns:
            Task: Updated task object
            
        Raises:
            ValueError: If task ID or UUID is missing
        """
        if not task.uuid:
            raise ValueError("Task UUID required to modify a task")
            
        try:
            self.get_task(task.uuid)
        except RuntimeError:
            raise ValueError("Task not found for modification")
            
        args = [str(task.uuid), 'modify']
        args += self._build_args(task)
        
        self._run_task_command(args)
        return self.get_task(task.uuid)

    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """
        Retrieve a task by ID or UUID.
        
        Args:
            task_id_or_uuid: Task ID or UUID
            
        Returns:
            Task: Task object
            
        Raises:
            RuntimeError: If task is not found
        """
        result = self._run_task_command([str(task_id_or_uuid), "export"])
        tasks_data = json.loads(result.stdout)
        
        if not tasks_data:
            raise RuntimeError(f"Task {task_id_or_uuid} not found.")
            
        return Task(**tasks_data[0])

    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """
        Retrieve all tasks matching the given filters.
        
        Args:
            filter_args: List of filter arguments as accepted by task
            
        Returns:
            List[Task]: Matching tasks
        """
        # Sanitize filter arguments
        args = [str(arg) for arg in filter_args]
        result = self._run_task_command(args + ["export"])
        
        tasks_data = json.loads(result.stdout)
        return [Task(**task) for task in tasks_data]

    def delete_task(self, uuid: UUID) -> None:
        """Delete a task by UUID."""
        self._run_task_command([str(uuid), "delete"])

    def purge_task(self, uuid: UUID) -> None:
        """Permanently delete a task by UUID."""
        self._run_task_command([str(uuid), "purge"])

    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done by UUID."""
        self._run_task_command([str(uuid), "done"])

    def start_task(self, uuid: UUID) -> None:
        """Start a task by UUID."""
        self._run_task_command([str(uuid), "start"])

    def stop_task(self, uuid: UUID) -> None:
        """Stop a task by UUID."""
        self._run_task_command([str(uuid), "stop"])

    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        self._run_task_command([str(uuid), "annotate", annotation])

    def set_context(self, context: str, filter_str: str) -> None:
        """Define a context with a filter."""
        self._run_task_command(["context", "define", context, filter_str])

    def apply_context(self, context: str) -> None:
        """Apply a context to filter tasks."""
        self._run_task_command(["context", context])

    def remove_context(self) -> None:
        """Remove the current context."""
        self._run_task_command(["context", "none"])
