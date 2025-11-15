"""Utility functions for MontagePy."""

import re
from pathlib import Path
from typing import List

# Common video file extensions
VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".mts",
    ".m2ts", ".vob", ".asf", ".rm", ".rmvb", ".divx", ".xvid"
}


def scan_video_files(directory: str) -> List[str]:
    """Recursively scan directory for video files.
    
    Args:
        directory: Directory path to scan
        
    Returns:
        List of video file paths
    """
    video_files = []
    dir_path = Path(directory)

    if not dir_path.is_dir():
        return video_files

    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(str(file_path))

    return sorted(video_files)


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
            f"Invalid color format: {original_color_str}. Expected hex color (#RRGGBB or RRGGBB) or color name.")

    # Convert to RGB
    r = int(color_str[0:2], 16)
    g = int(color_str[2:4], 16)
    b = int(color_str[4:6], 16)

    return (r, g, b)


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


def generate_unique_filename(video_file: str, input_root: str) -> str:
    """Generate a unique filename based on the video file's absolute path.
    
    This function creates a unique filename to avoid conflicts when processing
    multiple files with the same name. It uses the input root directory as the
    base for calculating relative paths.
    
    Args:
        video_file: Path to the video file
        input_root: Root directory path used as base for relative path calculation
        
    Returns:
        Unique filename string (e.g., "subdir1_subdir2_filename_montage.jpg")
    """
    # Get absolute paths
    # On Windows, resolve() may fail if the file doesn't exist or path is invalid
    # Use absolute() as fallback, which works even if file doesn't exist
    video_path = Path(video_file)
    try:
        # Try resolve() first (handles symlinks and normalizes path)
        if video_path.exists():
            abs_video_file = video_path.resolve()
        else:
            # If file doesn't exist, use absolute() which doesn't require file to exist
            abs_video_file = video_path.absolute()
    except (OSError, RuntimeError, ValueError):
        # Fallback if resolve() fails
        abs_video_file = video_path.absolute()

    input_root_path = Path(input_root)
    try:
        # Try resolve() first
        if input_root_path.exists():
            abs_input_root = input_root_path.resolve()
        else:
            abs_input_root = input_root_path.absolute()
    except (OSError, RuntimeError, ValueError):
        # Fallback if resolve() fails
        abs_input_root = input_root_path.absolute()

    # Normalize paths (convert to same case on Windows, normalize separators)
    abs_video_file = Path(str(abs_video_file))
    abs_input_root = Path(str(abs_input_root))

    # Get base filename without extension
    base_name = abs_video_file.stem
    suffix = "_montage.jpg"

    # Calculate relative path from input root
    try:
        # On Windows, ensure both paths are on the same drive
        # relative_to() will raise ValueError if paths are on different drives
        rel_path = abs_video_file.relative_to(abs_input_root)
        rel_path_str = str(rel_path)
    except ValueError:
        # If relative path calculation fails (different roots or drives on Windows), use base name only
        # This can happen on Windows if paths are on different drives (e.g., D:\ and C:\)
        return base_name + suffix

    # Check if file is at root or directly in root
    # rel_path_str could be just the filename (e.g., "video.mp4") or "." for root
    if rel_path_str == "." or rel_path_str == abs_video_file.name or rel_path_str == abs_video_file.stem + abs_video_file.suffix:
        return base_name + suffix

    # Get directory part of relative path
    rel_dir = rel_path.parent
    # Check if rel_dir is empty or just "."
    # Path(".").parts is () (empty tuple), so we check for that
    if not rel_dir.parts or rel_dir == Path(".") or str(rel_dir) == ".":
        # File is directly in root, use base name only
        return base_name + suffix

    # Replace path separators with underscores and sanitize
    # Use parts to handle cross-platform path separators properly
    path_parts = [str(part) for part in rel_dir.parts if part != "."]
    path_part = "_".join(path_parts) if path_parts else ""

    # Build filename: pathPart_baseName_montage.jpg
    if path_part:
        filename = f"{path_part}_{base_name}{suffix}"
    else:
        filename = f"{base_name}{suffix}"

    # Get maximum filename length for the current OS
    # Most modern filesystems support 255 characters, but we'll be conservative
    max_filename_len = 255

    # If filename is too long, remove top-level directories from path part
    if len(filename) > max_filename_len:
        parts = path_part.split("_") if path_part else []

        # Remove top-level directories one by one until filename fits
        while parts and len(filename) > max_filename_len:
            # Remove the first (top-level) directory
            parts = parts[1:]

            if parts:
                # Rebuild path part without top-level directory
                path_part = "_".join(parts)
                filename = f"{path_part}_{base_name}{suffix}"
            else:
                # No more path parts, use base name only
                filename = base_name + suffix
                break

        # Final check: if still too long, truncate base name (shouldn't happen often)
        if len(filename) > max_filename_len:
            if path_part:
                available_len = max_filename_len - len(path_part) - len("_") - len(suffix)
                if available_len > 0 and len(base_name) > available_len:
                    base_name = base_name[:available_len]
                    filename = f"{path_part}_{base_name}{suffix}"
                else:
                    # Last resort: use base name only
                    filename = base_name + suffix
            else:
                # Truncate base name if no path part
                if len(base_name) > max_filename_len - len(suffix):
                    base_name = base_name[:max_filename_len - len(suffix)]
                    filename = base_name + suffix

    return filename
