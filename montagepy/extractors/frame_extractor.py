"""Frame extraction logic for MontagePy."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

import av
from PIL import Image

from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.video_info import VideoInfo


class FrameExtractor:
    """Extracts frames from video files."""

    def __init__(self, config: Config, video_info: VideoInfo, logger: Logger):
        """Initialize frame extractor.

        Args:
            config: Configuration object
            video_info: Video information
            logger: Logger instance
        """
        self.config = config
        self.video_info = video_info
        self.logger = logger

    def extract_frames(self) -> Tuple[List[Image.Image], List[float]]:
        """Extract frames from video at calculated timestamps.

        Returns:
            Tuple of (frames list, timestamps list)
        """
        num_frames = self.config.columns * self.config.rows
        if num_frames <= 0:
            raise ValueError("Number of frames must be positive")

        # Calculate thumbnail dimensions
        thumb_width = self.config.thumb_width
        thumb_height = self.config.thumb_height
        if thumb_height <= 0:
            if self.video_info.height == 0:
                raise ValueError("Video height is 0, cannot auto-calculate thumbnail height")
            thumb_height = int(thumb_width / (self.video_info.width / self.video_info.height))

        # Calculate timestamps based on configured skip percentages
        skip_start = self.config.skip_start_percent / 100.0
        skip_end = self.config.skip_end_percent / 100.0

        # Validate skip percentages
        if skip_start < 0 or skip_start >= 1:
            raise ValueError(
                f"skip_start_percent must be between 0 and 100, got {self.config.skip_start_percent}"
            )
        if skip_end < 0 or skip_end >= 1:
            raise ValueError(
                f"skip_end_percent must be between 0 and 100, got {self.config.skip_end_percent}"
            )
        if skip_start + skip_end >= 1:
            raise ValueError(
                f"skip_start_percent + skip_end_percent must be less than 100, "
                f"got {self.config.skip_start_percent} + {self.config.skip_end_percent}"
            )

        start_offset = self.video_info.duration * skip_start
        end_offset = self.video_info.duration * (1.0 - skip_end)
        duration = end_offset - start_offset
        interval = duration / num_frames

        timestamps = [start_offset + (i * interval) for i in range(num_frames)]

        # Log timestamps in verbose mode
        if self.logger and self.logger.verbose:
            self.logger.verbose(f"Video duration: {self.video_info.duration:.2f}s")
            self.logger.verbose(f"Extracting {num_frames} frames from {start_offset:.2f}s to {end_offset:.2f}s")
            self.logger.verbose(f"First 5 timestamps: {[f'{ts:.2f}' for ts in timestamps[:5]]}")

        # Extract frames in parallel
        frames: List[Optional[Image.Image]] = [None] * num_frames
        actual_timestamps: List[float] = [0.0] * num_frames  # Store actual keyframe timestamps

        max_workers = min(num_frames, self.config.max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self._extract_single_frame, ts, thumb_width, thumb_height): i
                for i, ts in enumerate(timestamps)
            }

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    frame, actual_timestamp = future.result()
                    frames[index] = frame
                    actual_timestamps[index] = actual_timestamp
                except Exception as e:
                    self.logger.error(f"Failed to extract frame {index}: {e}")
                    raise

        # Verify all frames were extracted
        if any(f is None for f in frames):
            raise ValueError("Some frames failed to extract")

        # Return frames with actual keyframe timestamps (not the target timestamps)
        return frames, actual_timestamps  # type: ignore

    def _extract_single_frame(
        self, timestamp: float, thumb_width: int, thumb_height: int
    ) -> Tuple[Image.Image, float]:
        """Extract the next keyframe starting from the given timestamp.

        Seeks to the timestamp (or keyframe before it), then finds and uses the next keyframe.
        This is faster than finding the closest keyframe as we stop at the first one found.

        Args:
            timestamp: Starting timestamp in seconds
            thumb_width: Target thumbnail width
            thumb_height: Target thumbnail height

        Returns:
            Tuple of (PIL Image object, actual keyframe timestamp)
        """
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

            # Seek to timestamp (or keyframe before it)
            # Use backward=True to seek to keyframe before timestamp, then decode forward
            seek_pts = int(timestamp / time_base)
            container.seek(seek_pts, stream=video_stream, backward=True, any_frame=False)

            # Find the next keyframe after seeking
            keyframe = None
            keyframe_time = None
            packet_count = 0
            max_packets = 15  # Usually only need a few packets to find next keyframe

            # Also track the seek position keyframe as fallback
            seek_position_keyframe = None
            seek_position_time = None

            for packet in container.demux(video_stream):
                # Safety check: prevent infinite loops
                packet_count += 1
                if packet_count > max_packets:
                    break

                # Decode frames from packet, find first keyframe
                for decoded_frame in packet.decode():
                    # Only process keyframes (I-frames)
                    if not decoded_frame.key_frame:
                        continue  # Skip non-keyframes

                    # Keep the first keyframe we find (at seek position) as fallback
                    if seek_position_keyframe is None:
                        seek_position_keyframe = decoded_frame
                        if decoded_frame.pts is not None:
                            seek_position_time = float(decoded_frame.pts * time_base)
                        else:
                            seek_position_time = timestamp

                    # Found a keyframe after seek position - use it immediately
                    keyframe = decoded_frame

                    # Get keyframe timestamp
                    if decoded_frame.pts is not None:
                        keyframe_time = float(decoded_frame.pts * time_base)
                    else:
                        # Fallback: use target timestamp if keyframe has no PTS
                        keyframe_time = timestamp

                    # Found keyframe, exit immediately
                    break

                # Exit if we found a keyframe
                if keyframe is not None:
                    break

            # Fallback: if no keyframe found after seek position, use the seek position keyframe
            if keyframe is None:
                if seek_position_keyframe is not None:
                    # Use the keyframe at seek position (backward seek found a keyframe)
                    keyframe = seek_position_keyframe
                    keyframe_time = seek_position_time if seek_position_time is not None else timestamp
                else:
                    # Last resort: try seeking backward to find any keyframe
                    container.seek(0, stream=video_stream, backward=False, any_frame=False)
                    for packet in container.demux(video_stream):
                        for decoded_frame in packet.decode():
                            if decoded_frame.key_frame:
                                keyframe = decoded_frame
                                if decoded_frame.pts is not None:
                                    keyframe_time = float(decoded_frame.pts * time_base)
                                else:
                                    keyframe_time = timestamp
                                break
                        if keyframe is not None:
                            break

                    # If still no keyframe found, raise error
                    if keyframe is None:
                        raise ValueError(f"Could not find any keyframe starting from timestamp {timestamp:.2f}s")

            # Ensure we have a valid timestamp
            if keyframe_time is None:
                if keyframe.pts is not None:
                    keyframe_time = float(keyframe.pts * time_base)
                else:
                    keyframe_time = timestamp  # Last resort fallback

            # Convert keyframe to PIL Image
            pil_image = keyframe.to_image()

            # Optimized resize: use BILINEAR instead of LANCZOS for 2-3x speed improvement
            # BILINEAR is sufficient for thumbnails and much faster than LANCZOS
            # Only resize if necessary (check size first to avoid unnecessary operation)
            if pil_image.size[0] != thumb_width or pil_image.size[1] != thumb_height:
                pil_image = pil_image.resize((thumb_width, thumb_height), Image.Resampling.BILINEAR)

            # Return both the image and the actual keyframe timestamp
            return pil_image, keyframe_time

        finally:
            container.close()

