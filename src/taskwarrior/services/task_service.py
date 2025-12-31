from typing import List, Optional, Union
from uuid import UUID

from ..task import Task, TaskStatus
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..exceptions import TaskNotFound, TaskValidationError, TaskWarriorError

class TaskService:
    """Handles task-related business logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def _execute_task_operation(self, operation_func, *args, **kwargs):
        """Execute a task operation with consistent error handling."""
        try:
            return operation_func(*args, **kwargs)
        except TaskNotFound:
            # Re-raise TaskNotFound as-is
            raise
        except TaskValidationError:
            # Re-raise TaskValidationError as-is  
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to {operation_func.__name__}: {str(e)}") from e
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        return self.adapter.add_task(task)
    
    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        return self.adapter.modify_task(task)
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID."""
        return self._execute_task_operation(self.adapter.get_task, task_id_or_uuid)
    
    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        return self._execute_task_operation(self.adapter.get_tasks, filter_args)
    
    def get_recurring_task(self, uuid: UUID) -> Task:
        """Get a recurring task by UUID."""
        return self.adapter.get_recurring_task(uuid)
    
    def get_recurring_instances(self, uuid: UUID) -> List[Task]:
        """Get instances of a recurring task."""
        return self.adapter.get_recurring_instances(uuid)
    
    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        self._execute_task_operation(self.adapter.delete_task, uuid)
    
    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        self._execute_task_operation(self.adapter.purge_task, uuid)
    
    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        self._execute_task_operation(self.adapter.done_task, uuid)
    
    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        self._execute_task_operation(self.adapter.start_task, uuid)
    
    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        self._execute_task_operation(self.adapter.stop_task, uuid)
    
    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        self._execute_task_operation(self.adapter.annotate_task, uuid, annotation)
