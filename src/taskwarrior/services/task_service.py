from typing import List, Optional, Union
from uuid import UUID

from ..task import Task, TaskStatus
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..exceptions import TaskNotFound, TaskValidationError, TaskWarriorError

class TaskService:
    """Handles task-related business logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        try:
            return self.adapter.add_task(task)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except TaskValidationError as e:
            # Re-raise TaskValidationError as-is  
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to add task: {str(e)}") from e
    
    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        try:
            return self.adapter.modify_task(task)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except TaskValidationError as e:
            # Re-raise TaskValidationError as-is  
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to modify task: {str(e)}") from e
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID."""
        return self.adapter.get_task(task_id_or_uuid)
    
    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        return self.adapter.get_tasks(filter_args)
    
    def get_recurring_task(self, uuid: UUID) -> Task:
        """Get a recurring task by UUID."""
        return self.adapter.get_recurring_task(uuid)
    
    def get_recurring_instances(self, uuid: UUID) -> List[Task]:
        """Get instances of a recurring task."""
        return self.adapter.get_recurring_instances(uuid)
    
    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        try:
            self.adapter.delete_task(uuid)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to delete task: {str(e)}") from e
    
    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        try:
            self.adapter.purge_task(uuid)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to purge task: {str(e)}") from e
    
    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        try:
            self.adapter.done_task(uuid)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to mark task as done: {str(e)}") from e
    
    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        try:
            self.adapter.start_task(uuid)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to start task: {str(e)}") from e
    
    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        try:
            self.adapter.stop_task(uuid)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to stop task: {str(e)}") from e
    
    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        try:
            self.adapter.annotate_task(uuid, annotation)
        except TaskNotFound as e:
            # Re-raise TaskNotFound as-is
            raise
        except Exception as e:
            # Convert other exceptions to TaskWarriorError for consistency
            raise TaskWarriorError(f"Failed to annotate task: {str(e)}") from e
