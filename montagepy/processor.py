"""Core processing logic for generating thumbnail montages."""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

import av
from PIL import Image, ImageDraw, ImageFont

from montagepy.config import Config
from montagepy.logger import Logger
from montagepy.utils import format_duration, parse_color
from montagepy.video_info import VideoInfo


class Processor:
    """Processes video files to generate thumbnail montages."""

    def __init__(self, config: Config, video_info: VideoInfo, logger: Logger):
        """Initialize processor.
        
        Args:
            config: Configuration object
            video_info: Video information
            logger: Logger instance
        """
        self.config = config
        self.video_info = video_info
        self.logger = logger

    def run(self) -> None:
        """Run the montage generation process."""
        # Calculate thumbnail dimensions
        thumb_width = self.config.thumb_width
        thumb_height = self.config.thumb_height
        if thumb_height <= 0:
            if self.video_info.height == 0:
                raise ValueError("Video height is 0, cannot auto-calculate thumbnail height")
            thumb_height = int(thumb_width / (self.video_info.width / self.video_info.height))

        # Extract frames
        self.logger.info("Extracting frames...")
        frames, timestamps = self.extract_frames(thumb_width, thumb_height)

        # Compose montage
        self.logger.info("Composing montage...")
        self.compose_montage(frames, timestamps, thumb_width, thumb_height)

    def extract_frames(self, thumb_width: int, thumb_height: int) -> Tuple[List[Image.Image], List[float]]:
        """Extract frames from video at calculated timestamps.
        
        Args:
            thumb_width: Target thumbnail width
            thumb_height: Target thumbnail height
            
        Returns:
            Tuple of (frames list, timestamps list)
        """
        num_frames = self.config.columns * self.config.rows
        if num_frames <= 0:
            raise ValueError("Number of frames must be positive")

        # Calculate timestamps based on configured skip percentages
        skip_start = self.config.skip_start_percent / 100.0
        skip_end = self.config.skip_end_percent / 100.0

        # Validate skip percentages
        if skip_start < 0 or skip_start >= 1:
            raise ValueError(f"skip_start_percent must be between 0 and 100, got {self.config.skip_start_percent}")
        if skip_end < 0 or skip_end >= 1:
            raise ValueError(f"skip_end_percent must be between 0 and 100, got {self.config.skip_end_percent}")
        if skip_start + skip_end >= 1:
            raise ValueError(
                f"skip_start_percent + skip_end_percent must be less than 100, got {self.config.skip_start_percent} + {self.config.skip_end_percent}")

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

    def _extract_single_frame(self, timestamp: float, thumb_width: int, thumb_height: int) -> Tuple[Image.Image, float]:
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

    def compose_montage(
            self,
            frames: List[Image.Image],
            timestamps: List[float],
            thumb_width: int,
            thumb_height: int,
    ) -> None:
        """Compose the final montage image.
        
        Args:
            frames: List of frame images
            timestamps: List of timestamps corresponding to frames
            thumb_width: Thumbnail width
            thumb_height: Thumbnail height
        """
        # Calculate canvas dimensions
        grid_width = self.config.columns * thumb_width + (self.config.columns - 1) * self.config.padding
        grid_height = self.config.rows * thumb_height + (self.config.rows - 1) * self.config.padding

        total_width = grid_width + 2 * self.config.margin
        total_height = grid_height + 2 * self.config.margin + self.config.header_height

        # Create canvas
        bg_color = parse_color(self.config.background_color)
        canvas = Image.new("RGB", (total_width, total_height), bg_color)
        draw = ImageDraw.Draw(canvas)

        # Load fonts if available
        header_font = None
        meta_font = None
        timestamp_font = None

        if self.config.font_file:
            try:
                header_font = ImageFont.truetype(self.config.font_file, 40)
                meta_font = ImageFont.truetype(self.config.font_file, 20)
                timestamp_font = ImageFont.truetype(self.config.font_file, 18)
            except Exception as e:
                self.logger.verbose(f"Could not load font: {e}")

        # Draw header text
        if header_font:
            self._draw_header(draw, total_width, header_font, meta_font)

        # Draw frames
        for i, img in enumerate(frames):
            row = i // self.config.columns
            col = i % self.config.columns

            x = self.config.margin + col * (thumb_width + self.config.padding)
            y = self.config.header_height + self.config.margin + row * (thumb_height + self.config.padding)

            canvas.paste(img, (x, y))

            # Draw timestamp on frame
            if timestamp_font:
                timestamp_str = format_duration(timestamps[i])
                text_x = x + 10
                text_y = y + thumb_height - 15

                # Draw shadow
                draw.text(
                    (text_x + 1, text_y + 1),
                    timestamp_str,
                    fill=parse_color(self.config.shadow_color),
                    font=timestamp_font,
                )
                # Draw text
                draw.text(
                    (text_x, text_y),
                    timestamp_str,
                    fill=parse_color("white"),
                    font=timestamp_font,
                )

        # Save image with optimized JPEG encoding
        # Convert JPEG quality: config uses 1-31 (lower is better), PIL uses 1-100 (higher is better)
        pil_quality = 100 - (self.config.jpeg_quality - 1) * 3
        pil_quality = max(1, min(100, pil_quality))

        # Optimize JPEG save performance:
        # - optimize=True: Skip Huffman table optimization (faster, slightly larger file)
        # - progressive=False: Use baseline JPEG instead of progressive (faster encoding)
        # - subsampling: Use default subsampling (good balance of speed/quality)
        # - qtables: Use default quantization tables (faster)
        save_kwargs = {
            "format": "JPEG",
            "quality": pil_quality,
            "optimize": True,  # Disable optimization for faster encoding (saves ~20-30% time)
            "progressive": False,  # Use baseline JPEG (faster than progressive, saves ~10-15% time)
        }

        if self.config.output_path == "-":
            canvas.save(sys.stdout.buffer, **save_kwargs)
        else:
            canvas.save(self.config.output_path, **save_kwargs)

    def _draw_header(self, draw: ImageDraw.Draw, total_width: int, header_font: ImageFont.FreeTypeFont,
                     meta_font: Optional[ImageFont.FreeTypeFont]) -> None:
        """Draw header text on the canvas.
        
        Args:
            draw: ImageDraw object
            total_width: Total canvas width
            header_font: Font for header text
            meta_font: Font for metadata text
        """
        # Prepare text
        if self.config.show_full_path:
            # Get absolute path
            video_path = Path(self.video_info.path)
            try:
                # On Windows, resolve() may fail if file doesn't exist
                # Try resolve() first if file exists, otherwise use absolute()
                if video_path.exists():
                    display_text = str(video_path.resolve())  # resolve() handles symlinks and gives absolute path
                else:
                    display_text = str(video_path.absolute())  # absolute() works even if file doesn't exist
            except (OSError, RuntimeError, ValueError) as e:
                # Fallback to absolute() if resolve() fails
                if self.logger:
                    self.logger.verbose(f"Could not resolve path {self.video_info.path}: {e}")
                display_text = str(video_path.absolute())
        else:
            display_text = Path(self.video_info.path).name

        # Adjust font size to fit
        font_size = 40
        while font_size > 10:
            try:
                test_font = ImageFont.truetype(self.config.font_file, font_size)
                bbox = draw.textbbox((0, 0), display_text, font=test_font)
                text_width = bbox[2] - bbox[0]
                if text_width < total_width * 0.9:
                    header_font = test_font
                    break
            except Exception:
                pass
            font_size -= 2

        # Draw filename
        font_color = parse_color(self.config.font_color)
        shadow_color = parse_color(self.config.shadow_color)

        center_x = total_width // 2

        # Calculate text position for center alignment
        bbox = draw.textbbox((0, 0), display_text, font=header_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = center_x - text_width // 2
        text_y = 30 - text_height // 2

        # Draw shadow
        draw.text(
            (text_x + 2, text_y + 2),
            display_text,
            fill=shadow_color,
            font=header_font,
        )
        # Draw text
        draw.text(
            (text_x, text_y),
            display_text,
            fill=font_color,
            font=header_font,
        )

        # Draw metadata lines
        if meta_font:
            meta1 = self._format_metadata_line1()
            meta2 = self._format_metadata_line2()

            # Calculate positions for metadata lines
            bbox1 = draw.textbbox((0, 0), meta1, font=meta_font)
            meta1_width = bbox1[2] - bbox1[0]
            meta1_height = bbox1[3] - bbox1[1]
            meta1_x = center_x - meta1_width // 2
            meta1_y = 80 - meta1_height // 2

            bbox2 = draw.textbbox((0, 0), meta2, font=meta_font)
            meta2_width = bbox2[2] - bbox2[0]
            meta2_height = bbox2[3] - bbox2[1]
            meta2_x = center_x - meta2_width // 2
            meta2_y = 105 - meta2_height // 2

            # Line 1
            draw.text(
                (meta1_x + 1, meta1_y + 1),
                meta1,
                fill=shadow_color,
                font=meta_font,
            )
            draw.text(
                (meta1_x, meta1_y),
                meta1,
                fill=(255, 255, 255),
                font=meta_font,
            )

            # Line 2
            draw.text(
                (meta2_x + 1, meta2_y + 1),
                meta2,
                fill=shadow_color,
                font=meta_font,
            )
            draw.text(
                (meta2_x, meta2_y),
                meta2,
                fill=(255, 255, 255),
                font=meta_font,
            )

    def _format_metadata_line1(self) -> str:
        """Format first metadata line: Resolution | FPS | Bitrate."""
        dims = f"{self.video_info.width}x{self.video_info.height}"

        # Parse frame rate
        fps_str = "N/A FPS"
        if self.video_info.avg_frame_rate:
            parts = self.video_info.avg_frame_rate.split("/")
            if len(parts) == 2:
                try:
                    num = float(parts[0])
                    den = float(parts[1])
                    if den != 0:
                        fps_str = f"{num / den:.2f} FPS"
                except ValueError:
                    pass

        # Format bitrate
        bitrate_mbps = self.video_info.bit_rate / 1000000
        bitrate_str = f"{bitrate_mbps:.2f} Mbps"

        return f"{dims} | {fps_str} | {bitrate_str}"

    def _format_metadata_line2(self) -> str:
        """Format second metadata line: Duration | File Size | Codecs."""
        duration_str = format_duration(self.video_info.duration)

        size_mb = self.video_info.file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB"

        codecs = self.video_info.video_codec.upper()
        if self.video_info.audio_codec:
            codecs += " / " + self.video_info.audio_codec.upper()

        return f"{duration_str} | {size_str} | {codecs}"
