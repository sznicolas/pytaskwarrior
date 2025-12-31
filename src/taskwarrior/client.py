from __future__ import annotations
import json
import logging
import shutil
import subprocess
from os import environ, getenv, path
from typing import List, Optional, Union

from .task import Task, parse_datetime_or_timedelta
from .exceptions import TaskNotFound, TaskValidationError

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
            raise TaskValidationError("Task UUID required to modify a task")
            
        try:
            self.get_task(task.uuid)
        except RuntimeError:
            raise TaskNotFound("Task not found for modification")
            
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
            raise TaskNotFound(f"Task {task_id_or_uuid} not found.")
            
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
