"""Date and time conversion utilities for TaskWarrior.

This module provides functions for parsing TaskWarrior's date formats
into Python datetime objects.
"""

from datetime import datetime


def parse_taskwarrior_date(value: str) -> datetime:
    """Parse a TaskWarrior date string into a datetime object.

    TaskWarrior uses a compact date format (20260101T193139Z) that differs
    from standard ISO 8601. This function handles both formats.

    Args:
        value: The date string to parse. Can be in TaskWarrior's compact
            format (20260101T193139Z) or standard ISO format.

    Returns:
        A timezone-aware datetime object.

    Raises:
        ValueError: If the date string cannot be parsed.

    Example:
        >>> dt = parse_taskwarrior_date("20260115T143000Z")
        >>> print(dt)
        2026-01-15 14:30:00+00:00
    """
    # Handle TaskWarrior's date format (20260101T193139Z)
    try:
        # Check if it's the compact format used by TaskWarrior
        if len(value) == 16 and "T" in value and value.endswith("Z"):
            # Convert compact format to standard: 20260101T193139Z -> 2026-01-01T19:31:39Z
            date_part = value[:8]
            time_part = value[9:-1]  # Remove 'T' and 'Z'
            formatted = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
            return datetime.fromisoformat(formatted.replace("Z", "+00:00"))
        else:
            # Try standard parsing
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        # If parsing fails, try to parse as ISO format
        return datetime.fromisoformat(value)

