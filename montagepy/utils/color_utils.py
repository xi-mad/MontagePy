"""Color utility functions for MontagePy."""

import re


def parse_color(color_str: str) -> tuple[int, int, int]:
    """Parse color string to RGB tuple.

    Supports:
    - Hex colors: #RRGGBB or RRGGBB (with or without #)
    - Color names: black, white, red, etc.

    Args:
        color_str: Color string

    Returns:
        RGB tuple (R, G, B) with values 0-255

    Raises:
        ValueError: If color string is invalid
    """
    if not color_str:
        raise ValueError("Color string cannot be empty")

    original_color_str = color_str  # Keep original for error message
    color_str = color_str.strip()

    # Color name to hex mapping
    color_map = {
        "black": "#000000",
        "white": "#FFFFFF",
        "red": "#FF0000",
        "lime": "#00FF00",
        "green": "#008000",
        "blue": "#0000FF",
        "yellow": "#FFFF00",
        "cyan": "#00FFFF",
        "magenta": "#FF00FF",
        "silver": "#C0C0C0",
        "gray": "#808080",
        "grey": "#808080",
        "maroon": "#800000",
        "olive": "#808000",
        "purple": "#800080",
        "teal": "#008080",
        "navy": "#000080",
        "darkgray": "#A9A9A9",
        "darkgrey": "#A9A9A9",
        "lightgray": "#D3D3D3",
        "lightgrey": "#D3D3D3",
    }

    # Check if it's a color name (case-insensitive)
    color_lower = color_str.lower()
    if color_lower in color_map:
        color_str = color_map[color_lower]

    # Remove # if present
    color_str = color_str.lstrip("#")

    # Convert to lowercase for validation
    color_str = color_str.lower()

    # Validate hex format (must be exactly 6 hex digits)
    if not re.match(r"^[0-9a-f]{6}$", color_str):
        raise ValueError(
            f"Invalid color format: {original_color_str}. Expected hex color (#RRGGBB or RRGGBB) or color name."
        )

    # Convert to RGB
    r = int(color_str[0:2], 16)
    g = int(color_str[2:4], 16)
    b = int(color_str[4:6], 16)

    return (r, g, b)

