import json
import logging
import subprocess
import shlex
from typing import List, Optional, Union
from uuid import UUID

from .exceptions import TaskNotFound, TaskValidationError
from .task import Task
from .services.task_service import TaskService
from .services.recurring_service import RecurringService
from .services.context_service import ContextService
from .services.filter_service import FilterService
from .adapters.taskwarrior_adapter import TaskWarriorAdapter

logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__author__ = "TaskWarrior Python Team"

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


class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    
    def __init__(
        self,
        taskrc_path: Optional[str] = None,
        task_cmd: Optional[str] = None
    ):
        self.taskrc_path = taskrc_path or DEFAULT_TASKRC_PATH
        self.task_cmd = task_cmd or "task"
        
        # Create default config if it doesn't exist
        try:
            with open(self.taskrc_path, 'r') as f:
                pass
        except FileNotFoundError:
            with open(self.taskrc_path, 'w') as f:
                f.write(DEFAULT_TASKRC_CONTENT)
        
        self._validate_taskwarrior()
        
        # Initialize adapters and services
        self.adapter = TaskWarriorAdapter(self.task_cmd, self.taskrc_path)
        self.task_service = TaskService(self.adapter)
        self.recurring_service = RecurringService(self.adapter)
        self.context_service = ContextService(self.adapter)
        self.filter_service = FilterService(self.adapter)
    
    def _validate_taskwarrior(self) -> None:
        """Validate that taskwarrior is installed and working."""
        try:
            result = self._run_task_command(["version"])
            if result.returncode != 0:
                logger.error(f"TaskWarrior validation failed: {result.stderr}")
                raise RuntimeError("TaskWarrior is not properly configured")
        except FileNotFoundError:
            logger.error("TaskWarrior command not found in PATH")
            raise RuntimeError("TaskWarrior command not found. Please install taskwarrior.")
    
    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a taskwarrior command."""
        # Prepend the taskrc path to all commands
        cmd = [self.task_cmd, f"rc:{self.taskrc_path}"] + args
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # We'll handle the error checking ourselves
            )
            
            if result.returncode != 0:
                logger.warning(f"Task command failed with return code {result.returncode}: {result.stderr}")
            
            logger.debug(f"Command result - stdout: {result.stdout[:100]}... stderr: {result.stderr[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Exception while running task command: {e}")
            raise
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        return self.task_service.add_task(task)
    
    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        return self.task_service.modify_task(task)
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID."""
        return self.task_service.get_task(task_id_or_uuid)
    
    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        return self.task_service.get_tasks(filter_args)
    
    def get_recurring_task(self, uuid: UUID) -> Task:
        """Get the recurring task (parent) by its UUID."""
        return self.recurring_service.get_recurring_task(uuid)
    
    def get_recurring_instances(self, uuid: UUID) -> List[Task]:
        """Get all instances of a recurring task."""
        return self.recurring_service.get_recurring_instances(uuid)
    
    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        self.task_service.delete_task(uuid)
    
    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        self.task_service.purge_task(uuid)
    
    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        self.task_service.done_task(uuid)
    
    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        self.task_service.start_task(uuid)
    
    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        self.task_service.stop_task(uuid)
    
    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        self.task_service.annotate_task(uuid, annotation)
    
    def set_context(self, context: str, filter_str: str) -> None:
        """Set a context."""
        self.context_service.set_context(context, filter_str)
    
    def apply_context(self, context: str) -> None:
        """Apply a context."""
        self.context_service.apply_context(context)
    
    def remove_context(self) -> None:
        """Remove the current context."""
        self.context_service.remove_context()
