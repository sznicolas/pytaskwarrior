from __future__ import annotations
import subprocess
import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)

class DateCalculationService:
    """Handles date calculations and parsing using TaskWarrior's built-in capabilities."""
    
    def __init__(self, taskwarrior_binary: str = "task"):
        """
        Initialize the date calculation service.
        
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
    
    def calculate_date(self, expression: str) -> datetime:
        """
        Calculate a date using TaskWarrior's calc command.
        
        Args:
            expression: Date calculation expression
            
        Returns:
            Calculated datetime object
        """
        try:
            result = subprocess.run(
                [self.taskwarrior_binary, "calc", expression],
                capture_output=True,
                text=True,
                check=True
            )
            
            date_output = result.stdout.strip()
            return datetime.fromisoformat(date_output.replace('Z', '+00:00'))
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to calculate date '{expression}': {e}")
            raise ValueError(f"Could not calculate date: {expression}")
        except Exception as e:
            logger.error(f"Error calculating date '{expression}': {e}")
            raise ValueError(f"Could not calculate date: {expression}")
    
    def validate_date(self, date_string: str) -> bool:
        """
        Validate if a date string is valid according to TaskWarrior.
        
        Args:
            date_string: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.parse_date(date_string)
            return True
        except ValueError:
            return False
    
    def get_current_time(self) -> datetime:
        """
        Get current time using TaskWarrior's internal clock.
        
        Returns:
            Current datetime
        """
        return self.parse_date("now")
    
    def get_today(self) -> datetime:
        """
        Get today's date at 00:00:00.
        
        Returns:
            Today's date at start of day
        """
        return self.parse_date("today")
    
    def get_tomorrow(self) -> datetime:
        """
        Get tomorrow's date at 00:00:00.
        
        Returns:
            Tomorrow's date at start of day
        """
        return self.parse_date("tomorrow")
    
    def get_yesterday(self) -> datetime:
        """
        Get yesterday's date at 00:00:00.
        
        Returns:
            Yesterday's date at start of day
        """
        return self.parse_date("yesterday")
    
    def get_end_of_month(self) -> datetime:
        """
        Get end of current month date.
        
        Returns:
            End of current month at 23:59:59
        """
        return self.parse_date("eom")
    
    def get_start_of_month(self) -> datetime:
        """
        Get start of current month date.
        
        Returns:
            Start of current month at 00:00:00
        """
        return self.parse_date("som")
    
    def get_start_of_week(self) -> datetime:
        """
        Get start of current week (Monday).
        
        Returns:
            Start of current week at 00:00:00
        """
        return self.parse_date("sow")
    
    def get_end_of_week(self) -> datetime:
        """
        Get end of current week (Sunday).
        
        Returns:
            End of current week at 23:59:59
        """
        return self.parse_date("eow")
