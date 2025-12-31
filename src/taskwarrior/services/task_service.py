from typing import List, Optional, Union
from uuid import UUID

from ..task import Task, TaskStatus
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..exceptions import TaskNotFound, TaskValidationError

class TaskService:
    """Handles task-related business logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        try:
            return self.adapter.add_task(task)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        try:
            return self.adapter.modify_task(task)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID."""
        try:
            return self.adapter.get_task(task_id_or_uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        try:
            return self.adapter.get_tasks(filter_args)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def get_recurring_task(self, uuid: UUID) -> Task:
        """Get a recurring task by UUID."""
        try:
            return self.adapter.get_recurring_task(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def get_recurring_instances(self, uuid: UUID) -> List[Task]:
        """Get instances of a recurring task."""
        try:
            return self.adapter.get_recurring_instances(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        try:
            self.adapter.delete_task(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        try:
            self.adapter.purge_task(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        try:
            self.adapter.done_task(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        try:
            self.adapter.start_task(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        try:
            self.adapter.stop_task(uuid)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
    
    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        try:
            self.adapter.annotate_task(uuid, annotation)
        except Exception as e:
            # Re-raise with more specific context if needed
            raise
