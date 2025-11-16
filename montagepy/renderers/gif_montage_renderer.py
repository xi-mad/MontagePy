"""GIF montage rendering logic for MontagePy."""

import sys
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.utils.color_utils import parse_color
from montagepy.utils.format_utils import format_duration
from montagepy.video_info import VideoInfo


class GifMontageRenderer:
    """Renders GIF montages from multiple GIF clips."""

    def __init__(self, config: Config, video_info: VideoInfo, logger: Logger):
        """Initialize GIF montage renderer.

        Args:
            config: Configuration object
            video_info: Video information
            logger: Logger instance
        """
        self.config = config
        self.video_info = video_info
        self.logger = logger
        
        # Load fonts once during initialization
        self.header_font = None
        self.meta_font = None
        self.timestamp_font = None
        self._font_cache = {}  # Cache for dynamically sized fonts
        
        if self.config.font_file:
            try:
                self.header_font = ImageFont.truetype(self.config.font_file, 40)
                self.meta_font = ImageFont.truetype(self.config.font_file, 20)
                self.timestamp_font = ImageFont.truetype(self.config.font_file, 18)
            except Exception as e:
                self.logger.verbose(f"Could not load font: {e}")

    def render(self, gif_images: List[Image.Image], timestamps: List[float]) -> None:
        """Render the GIF montage.

        Args:
            gif_images: List of GIF image objects (each with _frames attribute)
            timestamps: List of timestamps corresponding to GIFs
        """
        # Calculate thumbnail dimensions
        thumb_width = self.config.thumb_width
        thumb_height = self.config.thumb_height
        if thumb_height <= 0:
            if self.video_info.height == 0:
                raise ValueError("Video height is 0, cannot auto-calculate thumbnail height")
            thumb_height = int(thumb_width / (self.video_info.width / self.video_info.height))

        # Extract frames from all GIFs
        all_frames_lists = []
        frame_duration = int(1000 / self.config.gif_fps)
        loop_count = self.config.gif_loop
        
        for gif_img in gif_images:
            if hasattr(gif_img, "_frames"):
                all_frames_lists.append(gif_img._frames)  # type: ignore
                # Get duration and loop from first GIF if available
                if hasattr(gif_img, "_duration"):
                    frame_duration = gif_img._duration  # type: ignore
                if hasattr(gif_img, "_loop"):
                    loop_count = gif_img._loop  # type: ignore
            else:
                # Fallback: treat as single frame
                all_frames_lists.append([gif_img])

        # Synchronize frames (use minimum frame count)
        min_frames = min(len(frames) for frames in all_frames_lists if frames)
        if min_frames == 0:
            raise ValueError("No frames to render")

        # Limit frames to minimum
        synchronized_frames = [frames[:min_frames] for frames in all_frames_lists]

        # Calculate canvas dimensions
        grid_width = self.config.columns * thumb_width + (self.config.columns - 1) * self.config.padding
        grid_height = self.config.rows * thumb_height + (self.config.rows - 1) * self.config.padding

        total_width = grid_width + 2 * self.config.margin
        total_height = grid_height + 2 * self.config.margin + self.config.header_height

        # Create header image (static)
        header_image = self._create_header_image(total_width, thumb_width, thumb_height)

        # Pre-create timestamp overlay (static, reused for all frames)
        timestamp_overlay = self._create_timestamp_overlay(
            thumb_width, thumb_height, timestamps, grid_width, grid_height
        )

        # Compose all frames
        montage_frames = []

        for frame_idx in range(min_frames):
            # Get frame from each GIF
            frame_images = []
            for i, frames in enumerate(synchronized_frames):
                if frame_idx < len(frames):
                    frame_images.append(frames[frame_idx])
                else:
                    # Use last frame if not enough frames
                    frame_images.append(frames[-1] if frames else Image.new("RGB", (thumb_width, thumb_height)))

            # Compose grid frame (without timestamps)
            grid_frame = self._compose_grid_frame(frame_images, thumb_width, thumb_height)
            
            # Paste timestamp overlay if available (use alpha channel as mask)
            if timestamp_overlay:
                grid_frame.paste(timestamp_overlay, (0, 0), timestamp_overlay.split()[3] if timestamp_overlay.mode == "RGBA" else timestamp_overlay)

            # Combine with header
            montage_frame = Image.new("RGB", (total_width, total_height), parse_color(self.config.background_color))
            montage_frame.paste(header_image, (0, 0))
            montage_frame.paste(grid_frame, (0, self.config.header_height))

            montage_frames.append(montage_frame)

        # Save as GIF
        if not montage_frames:
            raise ValueError("No frames to save")

        save_kwargs = {
            "format": "GIF",
            "save_all": True,
            "append_images": montage_frames[1:],
            "duration": frame_duration,
            "loop": loop_count,
            "optimize": self.config.gif_optimize,
        }

        if self.config.output_path == "-":
            montage_frames[0].save(sys.stdout.buffer, **save_kwargs)
        else:
            montage_frames[0].save(self.config.output_path, **save_kwargs)

    def _create_header_image(self, total_width: int, thumb_width: int, thumb_height: int) -> Image.Image:
        """Create static header image.

        Args:
            total_width: Total canvas width
            thumb_width: Thumbnail width
            thumb_height: Thumbnail height

        Returns:
            Header image
        """
        header_image = Image.new("RGB", (total_width, self.config.header_height), parse_color(self.config.background_color))
        draw = ImageDraw.Draw(header_image)

        # Use preloaded fonts
        if self.header_font:
            self._draw_header_text(draw, total_width, self.header_font, self.meta_font)

        return header_image

    def _draw_header_text(
        self,
        draw: ImageDraw.Draw,
        total_width: int,
        header_font: ImageFont.FreeTypeFont,
        meta_font: Optional[ImageFont.FreeTypeFont],
    ) -> None:
        """Draw header text.

        Args:
            draw: ImageDraw object
            total_width: Total canvas width
            header_font: Font for header text
            meta_font: Font for metadata text
        """
        # Prepare text
        if self.config.show_full_path:
            video_path = Path(self.video_info.path)
            try:
                if video_path.exists():
                    display_text = str(video_path.resolve())
                else:
                    display_text = str(video_path.absolute())
            except (OSError, RuntimeError, ValueError) as e:
                if self.logger:
                    self.logger.verbose(f"Could not resolve path {self.video_info.path}: {e}")
                display_text = str(video_path.absolute())
        else:
            display_text = Path(self.video_info.path).name

        # Adjust font size to fit (use cached fonts if available)
        font_size = 40
        while font_size > 10:
            try:
                # Check cache first
                if font_size in self._font_cache:
                    test_font = self._font_cache[font_size]
                else:
                    test_font = ImageFont.truetype(self.config.font_file, font_size)
                    self._font_cache[font_size] = test_font
                
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

        # Calculate text position
        bbox = draw.textbbox((0, 0), display_text, font=header_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = center_x - text_width // 2
        text_y = 30 - text_height // 2

        # Draw shadow
        draw.text((text_x + 2, text_y + 2), display_text, fill=shadow_color, font=header_font)
        # Draw text
        draw.text((text_x, text_y), display_text, fill=font_color, font=header_font)

        # Draw metadata if available
        if meta_font:
            meta1 = self._format_metadata_line1()
            meta2 = self._format_metadata_line2()

            # Line 1
            bbox1 = draw.textbbox((0, 0), meta1, font=meta_font)
            meta1_width = bbox1[2] - bbox1[0]
            meta1_x = center_x - meta1_width // 2
            draw.text((meta1_x + 1, 80), meta1, fill=shadow_color, font=meta_font)
            draw.text((meta1_x, 79), meta1, fill=(255, 255, 255), font=meta_font)

            # Line 2
            bbox2 = draw.textbbox((0, 0), meta2, font=meta_font)
            meta2_width = bbox2[2] - bbox2[0]
            meta2_x = center_x - meta2_width // 2
            draw.text((meta2_x + 1, 105), meta2, fill=shadow_color, font=meta_font)
            draw.text((meta2_x, 104), meta2, fill=(255, 255, 255), font=meta_font)

    def _create_timestamp_overlay(
        self, thumb_width: int, thumb_height: int, timestamps: List[float], grid_width: int, grid_height: int
    ) -> Optional[Image.Image]:
        """Create a static timestamp overlay image (RGBA with transparency).

        Args:
            thumb_width: Thumbnail width
            thumb_height: Thumbnail height
            timestamps: List of timestamps
            grid_width: Grid width
            grid_height: Grid height

        Returns:
            Timestamp overlay image with alpha channel, or None if no font
        """
        if not self.timestamp_font:
            return None

        # Calculate grid dimensions
        total_width = grid_width + 2 * self.config.margin
        total_height = grid_height + 2 * self.config.margin

        # Create transparent overlay
        overlay = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Pre-parse colors
        shadow_color = parse_color(self.config.shadow_color)
        white_color = (255, 255, 255)

        # Pre-format all timestamps
        formatted_timestamps = [format_duration(ts) for ts in timestamps]

        # Draw all timestamps once
        num_positions = self.config.columns * self.config.rows
        for i in range(min(num_positions, len(formatted_timestamps))):
            row = i // self.config.columns
            col = i % self.config.columns

            x = self.config.margin + col * (thumb_width + self.config.padding)
            y = self.config.margin + row * (thumb_height + self.config.padding)

            text_x = x + 10
            text_y = y + thumb_height - 15
            timestamp_str = formatted_timestamps[i]

            # Draw shadow (with alpha)
            draw.text(
                (text_x + 1, text_y + 1),
                timestamp_str,
                fill=(*shadow_color, 255),  # Add alpha channel
                font=self.timestamp_font,
            )
            # Draw text (with alpha)
            draw.text((text_x, text_y), timestamp_str, fill=(*white_color, 255), font=self.timestamp_font)

        return overlay

    def _compose_grid_frame(
        self, frame_images: List[Image.Image], thumb_width: int, thumb_height: int
    ) -> Image.Image:
        """Compose a single grid frame (without timestamps).

        Args:
            frame_images: List of frame images for each position
            thumb_width: Thumbnail width
            thumb_height: Thumbnail height

        Returns:
            Composed grid frame
        """
        # Calculate grid dimensions
        grid_width = self.config.columns * thumb_width + (self.config.columns - 1) * self.config.padding
        grid_height = self.config.rows * thumb_height + (self.config.rows - 1) * self.config.padding

        total_width = grid_width + 2 * self.config.margin
        total_height = grid_height + 2 * self.config.margin

        # Create canvas
        bg_color = parse_color(self.config.background_color)
        canvas = Image.new("RGB", (total_width, total_height), bg_color)

        # Draw frames (no timestamps here, they're added via overlay)
        for i, img in enumerate(frame_images):
            row = i // self.config.columns
            col = i % self.config.columns

            x = self.config.margin + col * (thumb_width + self.config.padding)
            y = self.config.margin + row * (thumb_height + self.config.padding)

            canvas.paste(img, (x, y))

        return canvas

    def _format_metadata_line1(self) -> str:
        """Format first metadata line: Resolution | FPS | Bitrate."""
        dims = f"{self.video_info.width}x{self.video_info.height}"

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

