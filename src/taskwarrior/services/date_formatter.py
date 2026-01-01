from __future__ import annotations
import subprocess
import logging
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)

class DateFormatter:
    """Utility class for date formatting and parsing."""
    
    def __init__(self, taskwarrior_binary: str = "task"):
        """
        Initialize the date formatter.
        
        Args:
            taskwarrior_binary: Path to the taskwarrior binary (default: "task")
        """
        self.taskwarrior_binary = taskwarrior_binary
    
    def format_datetime(self, dt: datetime) -> str:
        """
        Format a datetime object to ISO string.
        
        Args:
            dt: Datetime object to format
            
        Returns:
            ISO formatted string
        """
        return dt.isoformat()
