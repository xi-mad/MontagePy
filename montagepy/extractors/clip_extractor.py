"""Video clip extraction logic for MontagePy."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import av
from PIL import Image

from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.core.models import VideoClip
from montagepy.video_info import VideoInfo


class ClipExtractor:
    """Extracts video clips from video files."""

    def __init__(self, config: Config, video_info: VideoInfo, logger: Logger):
        """Initialize clip extractor.

        Args:
            config: Configuration object
            video_info: Video information
            logger: Logger instance
        """
        self.config = config
        self.video_info = video_info
        self.logger = logger
        
        # Use NEAREST for fastest resize (acceptable quality for thumbnails)
        # For better quality, use Image.Resampling.BILINEAR or LANCZOS
        self._resample_method = Image.Resampling.BILINEAR

    def extract_clips(self, timestamps: List[float]) -> List[VideoClip]:
        """Extract video clips at specified timestamps.

        Args:
            timestamps: List of center timestamps for each clip

        Returns:
            List of VideoClip objects
        """
        # Calculate clip duration and offsets
        clip_duration = self.config.gif_clip_duration
        start_offset = self.config.gif_clip_start_offset
        end_offset = self.config.gif_clip_end_offset

        # Calculate thumbnail dimensions
        thumb_width = self.config.thumb_width
        thumb_height = self.config.thumb_height
        if thumb_height <= 0:
            if self.video_info.height == 0:
                raise ValueError("Video height is 0, cannot auto-calculate thumbnail height")
            thumb_height = int(thumb_width / (self.video_info.width / self.video_info.height))

        # Extract clips in parallel
        clips: List[VideoClip] = []
        max_workers = min(len(timestamps), self.config.max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(
                    self._extract_single_clip, ts, start_offset, end_offset, thumb_width, thumb_height
                ): i
                for i, ts in enumerate(timestamps)
            }

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    clip = future.result()
                    clips.append(clip)
                except Exception as e:
                    self.logger.error(f"Failed to extract clip {index}: {e}")
                    raise

        # Sort clips by timestamp to maintain order
        clips.sort(key=lambda c: c.timestamp)
        return clips

    def _extract_single_clip(
        self,
        center_time: float,
        start_offset: float,
        end_offset: float,
        thumb_width: int,
        thumb_height: int,
    ) -> VideoClip:
        """Extract a single video clip.

        Args:
            center_time: Center timestamp for the clip
            start_offset: Start offset from center (negative = before)
            end_offset: End offset from center (positive = after)
            thumb_width: Target thumbnail width
            thumb_height: Target thumbnail height

        Returns:
            VideoClip object
        """
        # Calculate clip time range
        start_time = max(0, center_time + start_offset)
        end_time = min(self.video_info.duration, center_time + end_offset)

        # Ensure valid time range
        if start_time >= end_time:
            start_time = max(0, center_time - 1.0)
            end_time = min(self.video_info.duration, center_time + 1.0)

        container = av.open(self.video_info.path)

        try:
            # Get video stream
            video_stream = None
            for stream in container.streams:
                if stream.type == "video":
                    video_stream = stream
                    break

            if video_stream is None:
                raise ValueError("No video stream found")

            # Get the time base for converting frame PTS to seconds
            time_base = video_stream.time_base

            # Seek to start time
            seek_pts = int(start_time / time_base)
            container.seek(seek_pts, stream=video_stream, backward=True, any_frame=False)

            # Extract frames
            frames: List[Image.Image] = []
            end_pts = int(end_time / time_base)

            for packet in container.demux(video_stream):
                if packet.pts is None:
                    continue

                # Stop if we've passed the end time
                if packet.pts > end_pts:
                    break

                # Decode frames
                for decoded_frame in packet.decode():
                    if decoded_frame.pts is None:
                        continue

                    frame_time = float(decoded_frame.pts * time_base)

                    # Only include frames within the clip range
                    if start_time <= frame_time <= end_time:
                        # Convert to PIL Image
                        pil_image = decoded_frame.to_image()

                        # Resize if necessary (using fast NEAREST method)
                        if pil_image.size[0] != thumb_width or pil_image.size[1] != thumb_height:
                            pil_image = pil_image.resize(
                                (thumb_width, thumb_height), self._resample_method
                            )

                        frames.append(pil_image)

            # If no frames extracted, try to get at least one frame
            if not frames:
                # Seek to center time and get one frame
                seek_pts = int(center_time / time_base)
                container.seek(seek_pts, stream=video_stream, backward=True, any_frame=False)
                for packet in container.demux(video_stream):
                    for decoded_frame in packet.decode():
                        if decoded_frame.key_frame:
                            pil_image = decoded_frame.to_image()
                            if pil_image.size[0] != thumb_width or pil_image.size[1] != thumb_height:
                                pil_image = pil_image.resize(
                                    (thumb_width, thumb_height), self._resample_method
                                )
                            frames.append(pil_image)
                            break
                    if frames:
                        break

            if not frames:
                raise ValueError(f"Could not extract any frames from clip at {center_time:.2f}s")

            return VideoClip(
                start_time=start_time,
                end_time=end_time,
                frames=frames,
                timestamp=center_time,
            )

        finally:
            container.close()

