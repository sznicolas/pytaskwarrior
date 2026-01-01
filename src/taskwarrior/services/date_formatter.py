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
    
    def parse_date(self, date_string: str) -> datetime:
        """
        Parse a date string using TaskWarrior's built-in parser.
        
        Args:
            date_string: Date string to parse (can include synonyms, formats, etc.)
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If the date string cannot be parsed
        """
        try:
            # Use task calc command to parse dates
            result = subprocess.run(
                [self.taskwarrior_binary, "calc", date_string],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output (should be in ISO format)
            date_output = result.stdout.strip()
            return datetime.fromisoformat(date_output.replace('Z', '+00:00'))
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to parse date '{date_string}': {e}")
            raise ValueError(f"Invalid date format: {date_string}")
        except Exception as e:
            logger.error(f"Error parsing date '{date_string}': {e}")
            raise ValueError(f"Could not parse date: {date_string}")
    
    def format_datetime(self, dt: datetime) -> str:
        """
        Format a datetime object to ISO string.
        
        Args:
            dt: Datetime object to format
            
        Returns:
            ISO formatted string
        """
        return dt.isoformat()
    
    def format_timedelta(self, td: Union[datetime, timedelta]) -> str:
        """
        Format a timedelta object to ISO duration string.
        
        Args:
            td: Timedelta object to format
            
        Returns:
            ISO duration formatted string
        """
        import isodate
        return isodate.duration_isoformat(td)
