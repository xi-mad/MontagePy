"""Formatting utility functions for MontagePy."""


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "01:23:45"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

