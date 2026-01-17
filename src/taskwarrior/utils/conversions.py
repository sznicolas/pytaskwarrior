from datetime import datetime


def parse_taskwarrior_date(value: str) -> str:
    """Parse TaskWarrior date format (20260101T193139Z) to datetime."""
    # Handle TaskWarrior's date format (20260101T193139Z)
    try:
        # Check if it's the compact format used by TaskWarrior
        if len(value) == 16 and "T" in value and value.endswith("Z"):
            # Convert compact format to standard: 20260101T193139Z -> 2026-01-01T19:31:39Z
            date_part = value[:8]
            time_part = value[9:-1]  # Remove 'T' and 'Z'
            formatted = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
            return datetime.fromisoformat(formatted.replace("Z", "+00:00")).isoformat()
        else:
            # Try standard parsing
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except Exception:
        # If parsing fails, return the original value
        return value

