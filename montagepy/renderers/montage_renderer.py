"""Montage rendering logic for MontagePy."""

import sys
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.utils.color_utils import parse_color
from montagepy.utils.format_utils import format_duration
from montagepy.video_info import VideoInfo


class MontageRenderer:
    """Renders thumbnail montages from extracted frames."""

    def __init__(self, config: Config, video_info: VideoInfo, logger: Logger):
        """Initialize montage renderer.

        Args:
            config: Configuration object
            video_info: Video information
            logger: Logger instance
        """
        self.config = config
        self.video_info = video_info
        self.logger = logger

    def render(self, frames: List[Image.Image], timestamps: List[float], layout: Optional["GridLayout"] = None) -> None:
        """Render the montage image.

        Args:
            frames: List of frame images
            timestamps: List of timestamps corresponding to frames
            layout: Optional custom grid layout
        """
        # Calculate thumbnail dimensions
        thumb_width = self.config.thumb_width
        thumb_height = self.config.thumb_height
        if thumb_height <= 0:
            if self.video_info.height == 0:
                raise ValueError("Video height is 0, cannot auto-calculate thumbnail height")
            thumb_height = int(thumb_width / (self.video_info.width / self.video_info.height))

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
            if layout:
                # Use custom layout
                # Import here to avoid circular imports if necessary, or assume it's passed correctly
                cell = layout.get_cell(i)
                if not cell:
                    self.logger.verbose(f"No layout cell defined for frame {i}, skipping")
                    continue
                
                row = cell.row
                col = cell.col
                row_span = cell.row_span
                col_span = cell.col_span
            else:
                # Default grid logic
                row = i // self.config.columns
                col = i % self.config.columns
                row_span = 1
                col_span = 1

            # Calculate position
            x = self.config.margin + col * (thumb_width + self.config.padding)
            y = self.config.header_height + self.config.margin + row * (thumb_height + self.config.padding)

            # Calculate size for merged cells
            # Width = span * single_width + (span - 1) * padding
            current_thumb_width = col_span * thumb_width + (col_span - 1) * self.config.padding
            current_thumb_height = row_span * thumb_height + (row_span - 1) * self.config.padding

            # Resize image if cell is merged (and thus larger)
            if row_span > 1 or col_span > 1:
                img = img.resize((current_thumb_width, current_thumb_height), Image.Resampling.LANCZOS)

            canvas.paste(img, (x, y))

            # Draw timestamp on frame
            if timestamp_font:
                timestamp_str = format_duration(timestamps[i])
            # Draw timestamp on frame
            if timestamp_font:
                timestamp_str = format_duration(timestamps[i])
                text_x = x + 10
                # Use current_thumb_height if defined (from layout logic), otherwise thumb_height
                cell_height = locals().get('current_thumb_height', thumb_height)
                text_y = y + cell_height - 15

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
        # JPEG quality is 1-100 (higher is better), directly use config value
        pil_quality = max(1, min(100, self.config.jpeg_quality))

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

    def _draw_header(
        self,
        draw: ImageDraw.Draw,
        total_width: int,
        header_font: ImageFont.FreeTypeFont,
        meta_font: Optional[ImageFont.FreeTypeFont],
    ) -> None:
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
                    display_text = str(
                        video_path.resolve()
                    )  # resolve() handles symlinks and gives absolute path
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

