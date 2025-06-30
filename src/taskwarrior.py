from __future__ import annotations
from datetime import datetime, timedelta
from uuid import UUID
import json
from os import environ, getenv, path
import subprocess
from enum import Enum
import shutil
from typing import Annotated, Optional, List, Union, get_origin, get_args

import isodate
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

"""
A taskrc must exist for `task`, by default ~/.taskrc.
As we are in a non interactive mode, we better use a custom taskrc file to set our conf
especially `confirmation=off`
This is the default, overridable by TASKRC env, and next by taskrc_path in TaskWarrior.__init()"""
DEFAULT_TASKRCPATH = 'pytaskrc'
DEFAULT_TASKRC_CONTENT = """
# Default configuration set by pytaskwarrior
confirmation=0
news.version=99.99.99 # disable news output
"""
DEFAULT_CONFIG_OVERRIDES = { # we must at least have confirmation off. !!! Not implemented yet. To be improved and simplified.
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

def parse_datetime_or_timedelta(val):
    """Returns a string, date time or iso 8601 duration"""
    if isinstance(val, timedelta):
        return isodate.duration_isoformat(val)
    else:
        return str(val)

# Pydantic Models
class Task(BaseModel):
    """Represents a TaskWarrior task.
    timedelta looks like `[±]P[DD]DT[HH]H[MM]M[SS]S` (ISO 8601 format for timedelta)"""

    description: Annotated[str, Field(..., description="Task description (required).")]
    index: Annotated[
        Optional[int],
        Field(default=None, alias='id', description="READONLY Task index of a task in the working set, which can change when tasks are completed or deleted.")
    ]
    uuid: Annotated[
        Optional[UUID],
        Field(default=None, description="READONLY Unique identifier for the task. Cannot be set when adding task")
    ]
    status: Annotated[
        Optional[TaskStatus],
        Field(default=None, description="Current status of the task.")
    ]
    priority: Annotated[
        Optional[Priority],
        Field(default=None, description="Priority of the task (H, M, L, or empty).")
    ]
    due: Annotated[
        Optional[Union[datetime, timedelta]],
        Field(default=None, description="Due date and time for the task.")
    ]
    entry: Annotated[
        Optional[datetime],
        Field(default=None, description="READONLY Task creation date and time.")
    ]
    start: Annotated[
        Optional[datetime],
        Field(default=None, description="READONLY Task started date and time.")
    ]
    end: Annotated[
        Optional[datetime],
        Field(default=None, description="READONLY Task done date and time.")
    ]
    modified: Annotated[
        Optional[datetime],
        Field(default=None, description="READONLY Last modification date and time.")
    ]
    tags: Annotated[
        Optional[List[str]],
        Field(default_factory=list, description="List of tags associated with the task.")
    ]
    project: Annotated[
        Optional[str],
        Field(default=None, description="Project the task belongs to.")
    ]
    depends: Annotated[
        Optional[List[UUID]],
        Field(default_factory=list, description="List of UUIDs of tasks this task depends on.")
    ]
    parent: Annotated[
        Optional[UUID],
        Field(default=None, description="UUID of the template task")
    ]
    recur: Annotated[
        Optional[RecurrencePeriod],
        Field(default=None, description="Recurrence period for recurring tasks.")
    ]
    scheduled: Annotated[
        Optional[Union[datetime, timedelta]],
        Field(default=None, description="Schedule the earlier time the task can be done. Masked when using the `ready` filter")
    ]
    wait: Annotated[
        Optional[Union[datetime, timedelta]],
        Field(default=None, description="The task is hidden until the date.")
    ]
    until: Annotated[
        Optional[Union[datetime, timedelta]],
        Field(default=None, description="Expiration date for recurring tasks.")
    ]
    #annotations: List[Annotation ({'entry': datetime, 'description': str}] = Field(default_factory=list, description="List of annotations for the task.")
    context: Annotated[
        Optional[str],
        Field(default=None, description="Context filter for the task.")
    ]
    # Urgency should be readonly
    # urgency: Optional[float] = Field(default=None, description="Computed urgency score by TaskWarrior.")
#    udas: Dict[str, Any] = Field(default_factory=dict) #TODO: Review UDA usage

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
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        return [tag.strip() for tag in v if tag.strip()]

    @field_validator('*', mode='before')
    @classmethod
    def modify_date_format(cls, v, info):
        """Date converter"""
        # Get the field's type annotation
        field_type = cls.model_fields[info.field_name].annotation

        # Helper function to check if datetime is in the type (handles Union, Optional)
        def contains_datetime_or_timedelta(t):
            origin = get_origin(t)
            if origin in (Union, Optional):
                return any(contains_datetime_or_timedelta(arg) for arg in get_args(t))
            return t in (datetime, timedelta)

        # Check if the field involves datetime and the input is a string
        if contains_datetime_or_timedelta(field_type):# and isinstance(v, str):
            #        if (field_type == datetime or field_type == Union[datetime, timedelta]) and isinstance(v, str):
            if isinstance(v, (datetime, timedelta)):
                return v
            # Try parsing as datetime (format: yyyymmddThhmmssZ)
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                # Try parsing as duration (example format: P21DT1H10M49S)
                try:
                    isodate.parse_duration(v)
                except isodate.ISO8601Error:
                    raise ValueError("Could not parse until as datetime or timedelta")
        return v
    
    @field_serializer('uuid')
    def serialize_uuid(self, uuid: UUID, _info):
        return str(uuid)

#    class Config:
#        use_enum_values = True  # Store enum values as strings
#        json_encoders = {
#            datetime: lambda v: v.isoformat(),
#            UUID: str,
#        }


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    def __init__(
            self,
            taskrc_path: str = None,
            #            config_overrides: dict[str, str] = None,
            task_cmd: str = None
            ):
        """
        Initialize the TaskWarrior API.

        Args:
            taskrc_path: Optional path to the .taskrc file. If None, uses default.
            TODO: implement this: config_overrides: Optional dict passed to `task`. As it overrides the defauts, should have at least `confirmation: off
            task_cmd: Optional path to the command.
        """
        if taskrc_path:
            self.taskrc_path = taskrc_path
        else:
            self.taskrc_path = getenv('TASKRC', path.join(path.dirname(__file__), DEFAULT_TASKRCPATH))
        environ['TASKRC'] = self.taskrc_path
        try:
            with open(self.taskrc_path, 'x') as file:
                print(f'Warning; taskrc file "{self.taskrc_path}" not found. Create it')
                file.write(DEFAULT_TASKRC_CONTENT)
        except FileExistsError:
            ...
#        self.config_overrides = config_overrides or DEFAULT_CONFIG_OVERRIDES
        if not task_cmd:
            self.task_cmd = shutil.which('task')
            if self.task_cmd is None:
                raise RuntimeError("Taskwarrior is not found in PATH.")
        else:
            self.task_cmd = task_cmd
        self._validate_taskwarrior()

    def _validate_taskwarrior(self) -> None:
        """Ensure Taskwarrior is installed and accessible."""
        try:
            subprocess.run([self.task_cmd, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Taskwarrior is not installed or not found in PATH.")

    def _build_args(self, task: Task) -> dict:
        args = []
        if task.description:
            args.extend(task.description.split())
        if task.priority:
            args.extend(["priority:" + task.priority])
        if task.due:
            args.extend(["due:" + parse_datetime_or_timedelta(task.due)])
        if task.until:
            args.extend(["until:" + parse_datetime_or_timedelta(task.until)])
        if task.scheduled:
            args.extend(["scheduled:" + parse_datetime_or_timedelta(task.scheduled)])
        if task.wait:
            args.extend(["wait:" + parse_datetime_or_timedelta(task.wait)])
        if task.project:
            args.extend(["project:" + task.project])
        if task.tags:
            args.extend([f"+{tag}" for tag in task.tags])
        if task.recur:
            args.extend(["recur:" + task.recur])
        if task.depends:
            args.extend(["depends:" + ",".join(str(uuid) for uuid in task.depends)])
        if task.context:
            args.extend(["context:" + task.context])
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
#        ' '.join([ f'rc.{k}={v}' for k, v in self.config_overrides.items()])

        command = [self.task_cmd] + args
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                env={**environ}
            )
            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"TaskWarrior command failed: {e.stderr}")


    def add_task(self, task: Task) -> Task:
        # TODO: if exists annotaion, must be set after the task creation.
        args = ['add']
        args += self._build_args(task)
        result = self._run_task_command(args)
        task_id = None
        for line in result.stdout.splitlines():
            if 'Created task' in line:
                task_id = int(line.removeprefix('Created task ').split()[0].strip("."))
        return self.get_task(task_id)

    def modify_task(self, task: Task) -> Task:
        """
        Modify an existing task in TaskWarrior.

        Args:
            task: Task object with updated fields.

        Returns:
            Task: Updated task object.

        Raises:
            ValueError: If task ID or UUID is missing.
        """
        try:
            self.get_task(task.uuid)
        except RuntimeError:
            raise ValueError("Task UUID required to modify a task")
        args = [str(task.uuid), 'modify']
        args += self._build_args(task)
        self._run_task_command(args)
        return self.get_task(task.uuid)

    def get_task(self, task_id_or_uuid: str) -> Task:
        """
        Retrieve a task by ID or UUID.

        Args:
            task_id_or_uuid: Task ID or UUID.

        Returns:
            Task: Task object.

        Raises:
            RuntimeError: If task is not found.
        """
        result = self._run_task_command([str(task_id_or_uuid), "export"])
        tasks_data = json.loads(result.stdout)
        if not tasks_data:
            raise RuntimeError(f"Task {task_id_or_uuid} not found.")
        return Task(**tasks_data[0])

    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """
        Retrieves all tasks matching.

        Args:
            filter_args: filter list as accepted by task

        Returns:
            List[Task]: matching tasks
        """
        # sanitize
        args = []
        for arg in filter_args:
            args.append(str(arg))
        result = self._run_task_command(args + ["export"])
        tasks = json.loads(result.stdout)
        return [Task(**task) for task in tasks]

    def delete_task(self, uuid: UUID) -> None:
        """Delete a task by UUID."""
        self._run_task_command([str(uuid), "delete"])

    def purge_task(self, uuid: UUID) -> None:
        """Delete a task by UUID."""
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

#    def define_context(self, context: str, filter_str: str) -> None:
#        """Define a context with a filter."""
#        self._run_task_command(["context", "define", context, filter_str])
#
#    def apply_context(self, context: str) -> None:
#        """Apply a context to filter tasks."""
#        self._run_task_command(["context", context])
#
#    def remove_context(self) -> None:
#        """Remove the current context."""
#        self._run_task_command(["context", "none"])
