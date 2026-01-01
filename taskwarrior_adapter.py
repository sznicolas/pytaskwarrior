import json
import logging
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

import shlex
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class TaskInputDTO(BaseModel):
    """Task DTO for input - accepts string dates"""
    description: str
    project: Optional[str] = None
    priority: Optional[str] = None
    due: Optional[str] = None  # String format like "tomorrow", "2026-12-31"
    entry: Optional[str] = None
    modified: Optional[str] = None
    end: Optional[str] = None
    
    @validator('due', 'entry', 'modified', 'end', pre=True)
    def parse_dates(cls, v):
        if v is None:
            return v
        # Convert string dates to datetime objects for internal processing
        # This allows the adapter to handle natural language dates like "tomorrow"
        return v

class TaskOutputDTO(BaseModel):
    """Task DTO for output - returns dates as datetime objects"""
    uuid: str
    description: str
    project: Optional[str] = None
    priority: Optional[str] = None
    due: Optional[datetime] = None  # Datetime objects for internal consistency
    entry: datetime
    modified: Optional[datetime] = None
    end: Optional[datetime] = None
    status: str
    
    class Config:
        # Allow datetime objects to be serialized properly
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TaskWarriorError(Exception):
    """Custom exception for Taskwarrior errors"""
    pass

class TaskNotFound(TaskWarriorError):
    """Exception raised when a task is not found"""
    pass

class TaskwarriorAdapter:
    def __init__(self, task_command: str = "task"):
        self.task_command = task_command

    def _run_task_command(self, args: List[str]) -> 'subprocess.CompletedProcess':
        """Execute a taskwarrior command and return the result."""
        import subprocess
        cmd = [self.task_command] + args
        logger.debug(f"Executing command: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

    def create_task(self, task_data: TaskInputDTO) -> TaskOutputDTO:
        """Create a new task."""
        logger.info(f"Creating task: {task_data.description}")
        
        # Convert TaskInputDTO to command arguments
        cmd_args = ["add", task_data.description]
        
        if task_data.project:
            cmd_args.extend(["project:" + task_data.project])
        if task_data.priority:
            cmd_args.extend(["priority:" + task_data.priority])
        if task_data.due:
            cmd_args.extend(["due:" + task_data.due])
        
        result = self._run_task_command(cmd_args)
        
        if result.returncode != 0:
            error_msg = f"Failed to create task: {result.stderr}"
            logger.error(error_msg)
            raise TaskWarriorError(error_msg)
        
        # Parse the UUID from the response
        uuid_line = result.stdout.strip()
        if not uuid_line:
            raise TaskWarriorError("Failed to get UUID from task creation")
        
        # Extract UUID (usually the first word in the response)
        uuid = uuid_line.split()[0]
        
        # Get the created task details
        return self.get_task(uuid)

    def get_task(self, uuid: UUID) -> TaskOutputDTO:
        """Get a task by UUID."""
        logger.debug(f"Getting task with UUID: {uuid}")
        
        result = self._run_task_command([str(uuid), "export"])
        
        if result.returncode != 0:
            error_msg = f"Failed to get task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)
        
        try:
            task_data = json.loads(result.stdout)[0]
            # Convert string dates to datetime objects for output
            if task_data.get('due'):
                task_data['due'] = datetime.fromisoformat(task_data['due'].replace('Z', '+00:00'))
            if task_data.get('entry'):
                task_data['entry'] = datetime.fromisoformat(task_data['entry'].replace('Z', '+00:00'))
            if task_data.get('modified'):
                task_data['modified'] = datetime.fromisoformat(task_data['modified'].replace('Z', '+00:00'))
            if task_data.get('end'):
                task_data['end'] = datetime.fromisoformat(task_data['end'].replace('Z', '+00:00'))
            
            return TaskOutputDTO(**task_data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse task data: {e}")
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}")

    def get_task_by_description(self, description: str) -> TaskOutputDTO:
        """Get a task by its description."""
        logger.debug(f"Getting task with description: {description}")
        
        result = self._run_task_command(["description:" + description, "export"])
        
        if result.returncode != 0:
            error_msg = f"Failed to get task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)
        
        try:
            task_data = json.loads(result.stdout)[0]
            # Convert string dates to datetime objects for output
            if task_data.get('due'):
                task_data['due'] = datetime.fromisoformat(task_data['due'].replace('Z', '+00:00'))
            if task_data.get('entry'):
                task_data['entry'] = datetime.fromisoformat(task_data['entry'].replace('Z', '+00:00'))
            if task_data.get('modified'):
                task_data['modified'] = datetime.fromisoformat(task_data['modified'].replace('Z', '+00:00'))
            if task_data.get('end'):
                task_data['end'] = datetime.fromisoformat(task_data['end'].replace('Z', '+00:00'))
            
            return TaskOutputDTO(**task_data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse task data: {e}")
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}")

    def get_tasks(self, filter_str: str = "") -> List[TaskOutputDTO]:
        """Get all tasks matching a filter."""
        logger.debug(f"Getting tasks with filter: {filter_str}")
        
        cmd = ["export"]
        if filter_str:
            cmd.insert(0, filter_str)
        
        result = self._run_task_command(cmd)
        
        if result.returncode != 0:
            error_msg = f"Failed to get tasks: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)
        
        if not result.stdout.strip():
            return []
        
        try:
            tasks_data = json.loads(result.stdout)
            tasks = []
            
            for task_data in tasks_data:
                # Convert string dates to datetime objects for output
                if task_data.get('due'):
                    task_data['due'] = datetime.fromisoformat(task_data['due'].replace('Z', '+00:00'))
                if task_data.get('entry'):
                    task_data['entry'] = datetime.fromisoformat(task_data['entry'].replace('Z', '+00:00'))
                if task_data.get('modified'):
                    task_data['modified'] = datetime.fromisoformat(task_data['modified'].replace('Z', '+00:00'))
                if task_data.get('end'):
                    task_data['end'] = datetime.fromisoformat(task_data['end'].replace('Z', '+00:00'))
                
                tasks.append(TaskOutputDTO(**task_data))
            
            return tasks
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse tasks data: {e}")
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}")

    def get_recurring_instances(self, uuid: UUID) -> List[TaskOutputDTO]:
        """Get all instances of a recurring task."""
        logger.debug(f"Getting recurring instances for parent UUID: {uuid}")

        # Get child tasks that are instances of the recurring parent
        result = self._run_task_command([f"parent:{str(uuid)}", "export"])

        if result.returncode != 0:
            # Check if it's a "no matches" error that we should handle gracefully
            if (
                "No matches" in result.stderr
                or "Unable to find report that matches" in result.stderr
            ):
                logger.debug("No recurring instances found")
                return []
            error_msg = f"Failed to get recurring instances: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        if not result.stdout.strip():
            logger.debug("No recurring instances returned (empty response)")
            return []

        try:
            tasks_data = json.loads(result.stdout)
            tasks = []
            
            for task_data in tasks_data:
                # Convert string dates to datetime objects for output
                if task_data.get('due'):
                    task_data['due'] = datetime.fromisoformat(task_data['due'].replace('Z', '+00:00'))
                if task_data.get('entry'):
                    task_data['entry'] = datetime.fromisoformat(task_data['entry'].replace('Z', '+00:00'))
                if task_data.get('modified'):
                    task_data['modified'] = datetime.fromisoformat(task_data['modified'].replace('Z', '+00:00'))
                if task_data.get('end'):
                    task_data['end'] = datetime.fromisoformat(task_data['end'].replace('Z', '+00:00'))
                
                tasks.append(TaskOutputDTO(**task_data))
            
            logger.debug(f"Retrieved {len(tasks)} recurring instances")
            return tasks
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise TaskNotFound(f"Invalid response from TaskWarrior: {result.stdout}")

    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        logger.info(f"Deleting task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "delete"])

        if result.returncode != 0:
            error_msg = f"Failed to delete task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully deleted task with UUID: {uuid}")

    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        logger.info(f"Purging task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "purge"])

        if result.returncode != 0:
            error_msg = f"Failed to purge task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully purged task with UUID: {uuid}")

    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        logger.info(f"Completing task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "done"])

        if result.returncode != 0:
            error_msg = f"Failed to mark task as done: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully completed task with UUID: {uuid}")

    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        logger.info(f"Starting task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "start"])

        if result.returncode != 0:
            error_msg = f"Failed to start task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully started task with UUID: {uuid}")

    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        logger.info(f"Stopping task with UUID: {uuid}")

        result = self._run_task_command([str(uuid), "stop"])

        if result.returncode != 0:
            error_msg = f"Failed to stop task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully stopped task with UUID: {uuid}")

    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        logger.info(f"Annotating task {uuid} with: {annotation}")

        # Sanitize the annotation to prevent command injection
        sanitized_annotation = shlex.quote(annotation)
        result = self._run_task_command([str(uuid), "annotate", sanitized_annotation])

        if result.returncode != 0:
            error_msg = f"Failed to annotate task: {result.stderr}"
            logger.error(error_msg)
            raise TaskNotFound(error_msg)

        logger.info(f"Successfully annotated task with UUID: {uuid}")

    def set_context(self, context: str, filter_str: str) -> None:
        """Set a context."""
        result = self._run_task_command(["context", "add", context, filter_str])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to set context: {result.stderr}")

    def apply_context(self, context: str) -> None:
        """Apply a context."""
        result = self._run_task_command(["context", "apply", context])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to apply context: {result.stderr}")

    def remove_context(self) -> None:
        """Remove the current context."""
        result = self._run_task_command(["context", "remove"])
        if result.returncode != 0:
            raise TaskWarriorError(f"Failed to remove context: {result.stderr}")
