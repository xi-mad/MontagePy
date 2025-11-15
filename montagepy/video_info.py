"""Video information extraction using PyAV."""

from dataclasses import dataclass
from pathlib import Path

import av


@dataclass
class VideoInfo:
    """Video metadata information."""

    path: str
    duration: float
    width: int
    height: int
    file_size: int
    video_codec: str
    audio_codec: str
    bit_rate: int
    avg_frame_rate: str


def get_video_info(video_path: str) -> VideoInfo:
    """Extract video information using PyAV.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        VideoInfo object containing video metadata
        
    Raises:
        ValueError: If video file cannot be opened or has no video stream
    """
    container = av.open(video_path)

    try:
        # Get file size
        file_size = Path(video_path).stat().st_size

        # Get duration from container
        # container.duration is in time_base units, convert to seconds
        # PyAV uses microseconds as the base unit (1e6)
        if container.duration:
            duration = float(container.duration) / 1000000.0
        else:
            # Fallback: try to get duration from format metadata
            duration_str = container.metadata.get("duration", "0")
            try:
                # Parse duration string (format: HH:MM:SS.microseconds)
                parts = duration_str.split(":")
                if len(parts) == 3:
                    hours, minutes, seconds = map(float, parts)
                    duration = hours * 3600 + minutes * 60 + seconds
                else:
                    duration = float(duration_str)
            except (ValueError, AttributeError):
                duration = 0.0

        # Find video and audio streams
        video_stream = None
        audio_stream = None

        for stream in container.streams:
            if stream.type == "video" and video_stream is None:
                video_stream = stream
            elif stream.type == "audio" and audio_stream is None:
                audio_stream = stream

        if video_stream is None:
            raise ValueError("No video stream found in file")

        # Extract video information
        width = video_stream.width
        height = video_stream.height
        video_codec = video_stream.codec.name if video_stream.codec else "unknown"

        # Calculate average frame rate
        if video_stream.average_rate:
            avg_frame_rate = f"{video_stream.average_rate.numerator}/{video_stream.average_rate.denominator}"
        else:
            avg_frame_rate = "0/1"

        # Extract audio codec
        audio_codec = ""
        if audio_stream and audio_stream.codec:
            audio_codec = audio_stream.codec.name

        # Get bitrate from container metadata
        bit_rate = container.bit_rate if container.bit_rate else 0

        return VideoInfo(
            path=video_path,
            duration=duration,
            width=width,
            height=height,
            file_size=file_size,
            video_codec=video_codec,
            audio_codec=audio_codec,
            bit_rate=bit_rate,
            avg_frame_rate=avg_frame_rate,
        )
    finally:
        container.close()
