"""Data models for MontagePy."""

from dataclasses import dataclass
from typing import List

from PIL import Image


@dataclass
class VideoClip:
    """Represents a video clip segment."""

    start_time: float  # Start time in seconds
    end_time: float  # End time in seconds
    frames: List[Image.Image]  # List of frames
    timestamp: float  # Center timestamp (for display)

    @property
    def duration(self) -> float:
        """Clip duration in seconds."""
        return self.end_time - self.start_time

    @property
    def frame_count(self) -> int:
        """Number of frames in the clip."""
        return len(self.frames)

