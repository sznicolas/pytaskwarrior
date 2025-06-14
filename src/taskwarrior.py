from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import json
from os import environ, getenv, path
import subprocess
import os
from dataclasses import dataclass, field
from enum import Enum


"""
A taskrc must exist for `task`, by default ~/.taskrc.
As we are in a non interactive mode, we better use a custom taskrc file to set our conf
especially `confirmation=off`
This is the default, overridable by TASKRC env, and next by taskrc_path in TaskWarrior.__init()"""
DEFAULT_TASKRC = 'api_taskrc_path'
DEFAULT_CONFIG_OVERRIDES = { # we must at least have confirmation off. To be improved and simplified.
    "confirmation": "off",
    "json.array": "TRUE",
    "verbose": "nothing"
}

class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"
    WAITING = "waiting"
    RECURRING = "recurring"


class TaskPriority(Enum):
    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""


@dataclass
class Task:
    """Task structure based on Taskwarrior RFC (task.md)."""
    description: str
    status: TaskStatus = TaskStatus.PENDING
    uuid: UUID = field(default_factory=uuid4)
    entry: datetime = field(default_factory=datetime.now)
    modified: Optional[datetime] = None
    due: Optional[datetime] = None
    wait: Optional[datetime] = None
    until: Optional[datetime] = None
    scheduled: Optional[datetime] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.NONE
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    depends: List[UUID] = field(default_factory=list)
    recur: Optional[str] = None
    mask: Optional[str] = None
    imask: Optional[float] = None
    parent: Optional[UUID] = None
    udas: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Task to dictionary for Taskwarrior JSON export/import."""
        task_dict = {
            "description": self.description,
            "status": self.status.value,
            "uuid": str(self.uuid),
            "entry": self.entry.isoformat(),
        }
        if self.modified:
            task_dict["modified"] = self.modified.isoformat()
        if self.due:
            task_dict["due"] = self.due.isoformat()
        if self.wait:
            task_dict["wait"] = self.wait.isoformat()
        if self.until:
            task_dict["until"] = self.until.isoformat()
        if self.scheduled:
            task_dict["scheduled"] = self.scheduled.isoformat()
        if self.start:
            task_dict["start"] = self.start.isoformat()
        if self.end:
            task_dict["end"] = self.end.isoformat()
        if self.priority != TaskPriority.NONE:
            task_dict["priority"] = self.priority.value
        if self.project:
            task_dict["project"] = self.project
        if self.tags:
            task_dict["tags"] = self.tags
        if self.annotations:
            task_dict["annotations"] = self.annotations
        if self.depends:
            task_dict["depends"] = [str(uuid) for uuid in self.depends]
        if self.recur:
            task_dict["recur"] = self.recur
        if self.mask:
            task_dict["mask"] = self.mask
        if self.imask is not None:
            task_dict["imask"] = self.imask
        if self.parent:
            task_dict["parent"] = str(self.parent)
        if self.udas:
            task_dict.update(self.udas)
        return task_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        """Create Task from Taskwarrior JSON dictionary."""
        return cls(
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            uuid=UUID(data.get("uuid", str(uuid4()))),
            entry=datetime.fromisoformat(data.get("entry", datetime.now().isoformat())),
            modified=datetime.fromisoformat(data["modified"]) if data.get("modified") else None,
            due=datetime.fromisoformat(data["due"]) if data.get("due") else None,
            wait=datetime.fromisoformat(data["wait"]) if data.get("wait") else None,
            until=datetime.fromisoformat(data["until"]) if data.get("until") else None,
            scheduled=datetime.fromisoformat(data["scheduled"]) if data.get("scheduled") else None,
            start=datetime.fromisoformat(data["start"]) if data.get("start") else None,
            end=datetime.fromisoformat(data["end"]) if data.get("end") else None,
            priority=TaskPriority(data.get("priority", "")),
            project=data.get("project"),
            tags=data.get("tags", []),
            annotations=data.get("annotations", []),
            depends=[UUID(dep) for dep in data.get("depends", [])],
            recur=data.get("recur"),
            mask=data.get("mask"),
            imask=data.get("imask"),
            parent=UUID(data["parent"]) if data.get("parent") else None,
            udas={k: v for k, v in data.items() if k not in cls.__dataclass_fields__ and k != "id"}
        )


class TaskWarrior:
    """Python API for Taskwarrior using shell commands."""
    def __init__(self, taskrc_path: str = None, config_overrides: Optional[Dict[str, Any]] = None):
        if taskrc_path:
            self.taskrc_path = taskrc_path
        else:
            self.taskrc_path = getenv('TASKRC', path.join(path.dirname(__file__), DEFAULT_TASKRC))
        environ['TASKRC'] = self.taskrc_path
        self.config_overrides = config_overrides or DEFAULT_CONFIG_OVERRIDES

        self._validate_taskwarrior()

    def _validate_taskwarrior(self) -> None:
        """Ensure Taskwarrior is installed and accessible."""
        try:
            subprocess.run(["task", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Taskwarrior is not installed or not found in PATH.")

    def _run_task_command(self, args: List[str], input_data: Optional[bytes] = None) -> subprocess.CompletedProcess:
        """Execute a Taskwarrior command with arguments."""
        cmd = ["task"] + args
        ' '.join([ f'{k}={v}' for k, v in self.config_overrides.items()])

        try:
            return subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ}
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Taskwarrior command failed: {e.stderr}")

    def load_tasks(self, command: str = "all") -> Dict[str, List[Task]]:
        """Load tasks from Taskwarrior database."""
        result = self._run_task_command(["export", command])
        tasks_data = json.loads(result.stdout)
        return {
            "pending": [Task.from_dict(task) for task in tasks_data if task.get("status") == "pending"],
            "completed": [Task.from_dict(task) for task in tasks_data if task.get("status") == "completed"],
            "deleted": [Task.from_dict(task) for task in tasks_data if task.get("status") == "deleted"],
            "waiting": [Task.from_dict(task) for task in tasks_data if task.get("status") == "waiting"],
            "recurring": [Task.from_dict(task) for task in tasks_data if task.get("status") == "recurring"]
        }

    def task_add(self, task: Task) -> Task:
        """Add a new task to Taskwarrior."""
        task_data = task.to_dict()
        input_data = json.dumps(task_data)
        result = self._run_task_command(["import"], input_data=input_data)
        # Fetch the newly added task to get its ID
        tasks = self.load_tasks()
        for status, task_list in tasks.items():
            for t in task_list:
                if t.uuid == task.uuid:
                    return t
        raise RuntimeError("Failed to retrieve added task.")

    def task_update(self, task: Task) -> Task:
        """Update an existing task in Taskwarrior."""
        task_data = task.to_dict()
        task_data["modified"] = datetime.now().isoformat()
        input_data = json.dumps(task_data)
        self._run_task_command(["import"], input_data=input_data)
        return task

    def task_delete(self, uuid: UUID) -> None:
        """Delete a task by UUID."""
        self._run_task_command([str(uuid), "delete"])

    def task_done(self, uuid: UUID) -> None:
        """Mark a task as done by UUID."""
        self._run_task_command([str(uuid), "done"])

    def task_start(self, uuid: UUID) -> None:
        """Start a task by UUID."""
        self._run_task_command([str(uuid), "start"])

    def task_stop(self, uuid: UUID) -> None:
        """Stop a task by UUID."""
        self._run_task_command([str(uuid), "stop"])

    def task_annotate(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        self._run_task_command([str(uuid), "annotate", annotation])

    def filter_tasks(self, **filters: Any) -> List[Task]:
        """Filter tasks using Taskwarrior filter syntax."""
        filter_args = []
        for key, value in filters.items():
            if isinstance(value, list):
                for v in value:
                    filter_args.append(f"{key}:{v}")
            else:
                filter_args.append(f"{key}:{value}")
        result = self._run_task_command(filter_args + ["export"])
        tasks_data = json.loads(result.stdout)
        return [Task.from_dict(task) for task in tasks_data]

    def set_context(self, context: str, filter_str: str) -> None:
        """Define a context with a filter."""
        self._run_task_command(["context", "define", context, filter_str])

    def apply_context(self, context: str) -> None:
        """Apply a context to filter tasks."""
        self._run_task_command(["context", context])

    def remove_context(self) -> None:
        """Remove the current context."""
        self._run_task_command(["context", "none"])

    def add_recurring_task(self, task: Task, recur: str, until: Optional[datetime] = None) -> Task:
        """Add a recurring task with a recurrence period."""
        task.recur = recur
        if until:
            task.until = until
        task.status = TaskStatus.RECURRING
        return self.task_add(task)

    def get_task(self, uuid: UUID) -> Optional[Task]:
        """Retrieve a task by UUID."""
        tasks = self.load_tasks()
        for status, task_list in tasks.items():
            for task in task_list:
                if task.uuid == uuid:
                    return task
        return None
