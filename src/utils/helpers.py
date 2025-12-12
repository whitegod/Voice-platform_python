"""
Helper Utility Functions
"""

import uuid
import re
from datetime import datetime, timedelta
from typing import Optional


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string
    """
    uid = str(uuid.uuid4())
    return f"{prefix}_{uid}" if prefix else uid


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize and clean text input.

    Args:
        text: Input text
        max_length: Maximum length to truncate to

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def format_timestamp(dt: datetime, format: str = "iso") -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        format: Format type (iso, human, short)

    Returns:
        Formatted string
    """
    if format == "iso":
        return dt.isoformat()
    elif format == "human":
        return dt.strftime("%B %d, %Y at %I:%M %p")
    elif format == "short":
        return dt.strftime("%Y-%m-%d %H:%M")
    else:
        return str(dt)


def parse_duration(duration_str: str) -> Optional[timedelta]:
    """
    Parse duration string to timedelta.

    Args:
        duration_str: Duration string (e.g., "30m", "2h", "1d")

    Returns:
        Timedelta object or None
    """
    pattern = r'(\d+)([smhd])'
    match = re.match(pattern, duration_str.lower())

    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)

    return None


def truncate_string(s: str, length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to specified length.

    Args:
        s: String to truncate
        length: Maximum length
        suffix: Suffix to append if truncated

    Returns:
        Truncated string
    """
    if len(s) <= length:
        return s
    return s[:length - len(suffix)] + suffix


def format_file_size(bytes: int) -> str:
    """
    Format bytes to human-readable size.

    Args:
        bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display.

    Args:
        data: Data to mask
        visible_chars: Number of characters to show at end

    Returns:
        Masked string
    """
    if len(data) <= visible_chars:
        return "***"
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]

