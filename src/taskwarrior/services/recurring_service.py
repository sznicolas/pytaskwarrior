from typing import List
from uuid import UUID

from ..task import Task
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter

class RecurringService:
    """Handles recurring task business logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def get_recurring_task(self, uuid: UUID) -> Task:
        """Get the recurring task (parent) by its UUID."""
        return self.adapter.get_recurring_task(uuid)
    
    def get_recurring_instances(self, uuid: UUID) -> List[Task]:
        """Get all instances of a recurring task."""
        return self.adapter.get_recurring_instances(uuid)
