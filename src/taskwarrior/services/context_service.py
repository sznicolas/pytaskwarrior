from ..adapters.taskwarrior_adapter import TaskWarriorAdapter

class ContextService:
    """Handles context management business logic."""
    
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
    
    def set_context(self, context: str, filter_str: str) -> None:
        """Set a context."""
        self.adapter.set_context(context, filter_str)
    
    def apply_context(self, context: str) -> None:
        """Apply a context."""
        self.adapter.apply_context(context)
    
    def remove_context(self) -> None:
        """Remove the current context."""
        self.adapter.remove_context()
