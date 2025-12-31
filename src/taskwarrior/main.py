import logging
from typing import List, Optional, Union
from uuid import UUID

from .task import Task
from .services.task_service import TaskService
from .services.recurring_service import RecurringService
from .services.context_service import ContextService
from .services.filter_service import FilterService
from .adapters.taskwarrior_adapter import TaskWarriorAdapter

logger = logging.getLogger(__name__)

class TaskWarrior:
    """A Python API wrapper for TaskWarrior, interacting via CLI commands."""
    
    def __init__(
        self,
        taskrc_path: Optional[str] = None,
        task_cmd: Optional[str] = None
    ):
        self.taskrc_path = taskrc_path
        self.task_cmd = task_cmd or "task"
        
        # Initialize adapters and services
        self.adapter = TaskWarriorAdapter(self.task_cmd, self.taskrc_path)
        self.task_service = TaskService(self.adapter)
        self.recurring_service = RecurringService(self.adapter)
        self.context_service = ContextService(self.adapter)
        self.filter_service = FilterService(self.adapter)
    
    def _run_task_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a task command and return the result."""
        return self.adapter._run_task_command(args)
    
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
