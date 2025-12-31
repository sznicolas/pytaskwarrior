import json
import logging
import subprocess
from typing import List, Optional, Union
from uuid import UUID

from .exceptions import TaskNotFound
from .task import Task

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
    
    def _validate_taskwarrior(self) -> None:
        """Validate that taskwarrior is installed and working."""
        try:
            result = self._run_task_command(["version"])
            if result.returncode != 0:
                raise RuntimeError("TaskWarrior is not properly configured")
        except FileNotFoundError:
            raise RuntimeError("TaskWarrior command not found. Please install taskwarrior.")
    
    def _build_args(self, task: Task) -> List[str]:
        """Build command arguments for a task."""
        args = []
        
        # Add all fields that are not None
        for field_name, value in task.model_dump(exclude_unset=True).items():
            if field_name == "uuid":
                continue
            elif field_name == "tags" and value:
                # Handle tags correctly - they should be added as tag values, not "tags+=tag"
                args.extend([f"+{tag}" for tag in value])
            elif field_name == "depends" and value:
                args.extend([f"depends+={dep}" for dep in value])
            else:
                if isinstance(value, (list, tuple)):
                    args.append(f"{field_name}={','.join(str(v) for v in value)}")
                elif isinstance(value, UUID):
                    args.append(f"{field_name}={str(value)}")
                elif hasattr(value, 'total_seconds'):
                    # Handle timedelta objects by converting to days
                    total_days = value.total_seconds() / (24 * 3600)
                    args.append(f"{field_name}={int(total_days)}d")
                else:
                    # Convert to string for other types
                    args.append(f"{field_name}={value}")
        
        return args
    
    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a taskwarrior command."""
        # Prepend the taskrc path to all commands
        cmd = [self.task_cmd, f"rc:{self.taskrc_path}"] + args
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Task command failed: {result.stderr}")
        
        return result
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        args = self._build_args(task)
        result = self._run_task_command(["add"] + args)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to add task: {result.stderr}")
        
        # Get the latest added task
        tasks = self.get_tasks(filter_args=["+LATEST"])
        if not tasks:
            raise RuntimeError("Failed to retrieve added task")
        
        return tasks[0]
    
    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        if not task.uuid:
            raise ValueError("Task must have a UUID to modify")
        
        args = self._build_args(task)
        result = self._run_task_command([str(task.uuid), "modify"] + args)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to modify task: {result.stderr}")
        
        # Get the updated task details
        return self.get_task(task.uuid)
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID.
        
        Args:
            task_id_or_uuid: Task ID or UUID
            
        Returns:
            Task: Task object
            
        Raises:
            RuntimeError: If task is not found
        """
        # First try to get the task normally
        result = self._run_task_command([str(task_id_or_uuid), "export"])
        
        if result.returncode == 0:
            tasks_data = json.loads(result.stdout)
            if tasks_data:
                return Task.model_validate(tasks_data[0])
        
        # If that fails, check if it's a deleted task
        try:
            # Try to get the task with status:deleted filter
            result = self._run_task_command([str(task_id_or_uuid), "export", "status:deleted"])
            if result.returncode == 0:
                tasks_data = json.loads(result.stdout)
                if tasks_data:
                    return Task.model_validate(tasks_data[0])
        except Exception:
            pass
        
        # If we still haven't found it, raise the exception
        raise TaskNotFound(f"Task {task_id_or_uuid} not found.")
    
    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        # Convert any UUID objects to strings in filter_args
        str_filter_args = [str(arg) if isinstance(arg, UUID) else arg for arg in filter_args]
        # Ensure we properly handle regex patterns by wrapping them appropriately
        args = str_filter_args + ["export"]
        result = self._run_task_command(args)
        
        if result.returncode != 0:
            # Check if it's a "no matches" error that we should handle gracefully
            if "No matches" in result.stderr or "Unable to find report that matches" in result.stderr:
                return []
            raise RuntimeError(f"Failed to get tasks: {result.stderr}")
        
        if not result.stdout.strip():
            return []
            
        tasks_data = json.loads(result.stdout)
        return [Task.model_validate(task_data) for task_data in tasks_data]
    
    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        result = self._run_task_command([str(uuid), "delete"])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to delete task: {result.stderr}")
    
    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        result = self._run_task_command([str(uuid), "purge"])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to purge task: {result.stderr}")
    
    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        result = self._run_task_command([str(uuid), "done"])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to mark task as done: {result.stderr}")
    
    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        result = self._run_task_command([str(uuid), "start"])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start task: {result.stderr}")
    
    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        result = self._run_task_command([str(uuid), "stop"])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to stop task: {result.stderr}")
    
    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        result = self._run_task_command([str(uuid), "annotate", annotation])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to annotate task: {result.stderr}")
    
    def set_context(self, context: str, filter_str: str) -> None:
        """Set a context."""
        result = self._run_task_command(["context", "add", context, filter_str])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to set context: {result.stderr}")
    
    def apply_context(self, context: str) -> None:
        """Apply a context."""
        result = self._run_task_command(["context", "apply", context])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to apply context: {result.stderr}")
    
    def remove_context(self) -> None:
        """Remove the current context."""
        result = self._run_task_command(["context", "remove"])
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to remove context: {result.stderr}")
