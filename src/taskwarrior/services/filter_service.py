from typing import List

from ..task import Task
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter

class FilterService:
    """Handles task filtering logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def filter_tasks(self, filter_args: List[str]) -> List[Task]:
        """Filter tasks based on criteria."""
        return self.adapter.get_tasks(filter_args)
