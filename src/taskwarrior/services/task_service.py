from typing import List, Optional, Union
from uuid import UUID

from ..task import Task, TaskStatus
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter

class TaskService:
    """Handles task-related business logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        return self.adapter.add_task(task)
    
    def modify_task(self, task: Task) -> Task:
        """Modify an existing task."""
        return self.adapter.modify_task(task)
    
    def get_task(self, task_id_or_uuid: Union[str, int]) -> Task:
        """Retrieve a task by ID or UUID."""
        return self.adapter.get_task(task_id_or_uuid)
    
    def get_tasks(self, filter_args: List[str]) -> List[Task]:
        """Get multiple tasks based on filters."""
        return self.adapter.get_tasks(filter_args)
    
    def delete_task(self, uuid: UUID) -> None:
        """Delete a task."""
        self.adapter.delete_task(uuid)
    
    def purge_task(self, uuid: UUID) -> None:
        """Purge a task permanently."""
        self.adapter.purge_task(uuid)
    
    def done_task(self, uuid: UUID) -> None:
        """Mark a task as done."""
        self.adapter.done_task(uuid)
    
    def start_task(self, uuid: UUID) -> None:
        """Start a task."""
        self.adapter.start_task(uuid)
    
    def stop_task(self, uuid: UUID) -> None:
        """Stop a task."""
        self.adapter.stop_task(uuid)
    
    def annotate_task(self, uuid: UUID, annotation: str) -> None:
        """Add an annotation to a task."""
        self.adapter.annotate_task(uuid, annotation)
