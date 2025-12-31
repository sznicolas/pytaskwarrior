import subprocess
from typing import List, Optional, Union

from .adapters.taskwarrior_adapter import TaskWarriorAdapter
from .exceptions import TaskNotFound, TaskValidationError
from .services.date_calculation_service import DateCalculationService

class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    
    def __init__(self, taskrc_path: Optional[str] = None):
        """
        Initialize the TaskWarrior API wrapper.
        
        Args:
            taskrc_path: Path to the taskrc configuration file
        """
        self.taskrc_path = taskrc_path
        self.adapter = TaskWarriorAdapter(taskrc_path)
        self.date_service = DateCalculationService()
    
    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run a task command and return the result.
        
        Args:
            args: List of arguments to pass to task command
            
        Returns:
            CompletedProcess object with the result
            
        Raises:
            FileNotFoundError: If task binary is not found
            subprocess.CalledProcessError: If the command fails with non-zero exit code
        """
        try:
            # Build the command with taskrc if provided
            cmd = ["task"]
            if self.taskrc_path:
                cmd.extend(["-f", self.taskrc_path])
            
            # Add the arguments
            cmd.extend(args)
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise on non-zero exit codes
            )
            
            # If the command failed, check if it's a FileNotFoundError (binary not found)
            if result.returncode != 0:
                # Check if the error is due to command not found
                if "command not found" in result.stderr.lower() or \
                   "no such file or directory" in result.stderr.lower():
                    raise FileNotFoundError(f"Task binary not found: {cmd[0]}")
            
            return result
            
        except FileNotFoundError:
            # Re-raise FileNotFoundError if it was already raised
            raise
        except Exception as e:
            # For any other exception, re-raise it
            raise
    
    def add_task(self, task) -> "Task":
        """Add a new task."""
        return self.adapter.add_task(task)
    
    def modify_task(self, task) -> "Task":
        """Modify an existing task."""
        return self.adapter.modify_task(task)
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> "Task":
        """Get a specific task by ID or UUID."""
        return self.adapter.get_task(task_id_or_uuid)
    
    def get_tasks(self, filter_args: List[str]) -> List["Task"]:
        """Get tasks matching the given filters."""
        return self.adapter.get_tasks(filter_args)
    
    def get_recurring_task(self, uuid) -> "Task":
        """Get a recurring task by UUID."""
        return self.adapter.get_recurring_task(uuid)
    
    def get_recurring_instances(self, uuid) -> List["Task"]:
        """Get instances of a recurring task."""
        return self.adapter.get_recurring_instances(uuid)
    
    def delete_task(self, uuid) -> None:
        """Delete a task."""
        self.adapter.delete_task(uuid)
    
    def purge_task(self, uuid) -> None:
        """Purge a task."""
        self.adapter.purge_task(uuid)
    
    def done_task(self, uuid) -> None:
        """Mark a task as done."""
        self.adapter.done_task(uuid)
    
    def start_task(self, uuid) -> None:
        """Start a task."""
        self.adapter.start_task(uuid)
    
    def stop_task(self, uuid) -> None:
        """Stop a task."""
        self.adapter.stop_task(uuid)
    
    def annotate_task(self, uuid, annotation: str) -> None:
        """Add an annotation to a task."""
        self.adapter.annotate_task(uuid, annotation)
