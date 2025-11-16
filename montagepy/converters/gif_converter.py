"""GIF conversion logic for MontagePy."""

from typing import List

from PIL import Image

from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.core.models import VideoClip


class GifConverter:
    """Converts video clips to GIF format."""

    def __init__(self, config: Config, logger: Logger):
        """Initialize GIF converter.

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

    def convert_clip_to_gif(self, clip: VideoClip, width: int, height: int) -> Image.Image:
        """Convert a video clip to GIF format.

        Args:
            clip: VideoClip object
            width: Target width
            height: Target height

        Returns:
            PIL.Image: GIF image object
        """
        if not clip.frames:
            raise ValueError("Clip has no frames")

        # Resample frames to match target FPS
        frames = self._resample_frames(clip.frames, clip.duration)

        # Resize frames if necessary
        resized_frames = []
        for frame in frames:
            if frame.size[0] != width or frame.size[1] != height:
                resized_frame = frame.resize((width, height), Image.Resampling.LANCZOS)
            else:
                resized_frame = frame
            resized_frames.append(resized_frame)

        # Quantize colors if needed
        if self.config.gif_colors < 256:
            resized_frames = self._quantize_colors(resized_frames, self.config.gif_colors)

        # Create GIF from frames
        if not resized_frames:
            raise ValueError("No frames to convert to GIF")

        # Calculate frame duration in milliseconds
        frame_duration = int(1000 / self.config.gif_fps)

        # Store frames in a custom attribute for later use in montage composition
        # We'll create a temporary GIF to get the proper format, but store frames separately
        first_frame = resized_frames[0].copy()
        first_frame._frames = resized_frames  # type: ignore
        first_frame._duration = frame_duration  # type: ignore
        first_frame._loop = self.config.gif_loop  # type: ignore

        return first_frame

    def _resample_frames(self, frames: List[Image.Image], duration: float) -> List[Image.Image]:
        """Resample frames to match target FPS.

        Args:
            frames: Original frames
            duration: Clip duration in seconds

        Returns:
            Resampled frames
        """
        if not frames:
            return frames

        # Calculate target frame count
        target_frame_count = int(duration * self.config.gif_fps)

        # If we have fewer frames than target, return all frames
        if len(frames) <= target_frame_count:
            return frames

        # If we have more frames, sample them
        if target_frame_count <= 0:
            target_frame_count = 1

        step = len(frames) / target_frame_count
        sampled_frames = []

        for i in range(target_frame_count):
            index = int(i * step)
            if index >= len(frames):
                index = len(frames) - 1
            sampled_frames.append(frames[index])

        return sampled_frames

    def _quantize_colors(self, frames: List[Image.Image], colors: int) -> List[Image.Image]:
        """Quantize colors to specified number.

        Args:
            frames: Frames to quantize
            colors: Target number of colors

        Returns:
            Quantized frames
        """
        quantized_frames = []

        for frame in frames:
            # Convert to RGB if needed
            if frame.mode not in ("RGB", "RGBA"):
                frame = frame.convert("RGB")

            # Quantize colors
            if frame.mode == "RGBA":
                # For RGBA, we need to handle transparency
                # Convert to RGB with white background
                rgb_frame = Image.new("RGB", frame.size, (255, 255, 255))
                rgb_frame.paste(frame, mask=frame.split()[3] if len(frame.split()) > 3 else None)
                frame = rgb_frame

            # Quantize
            quantized = frame.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG if self.config.gif_dither else Image.Dither.NONE)
            # Convert back to RGB for consistency
            quantized = quantized.convert("RGB")
            quantized_frames.append(quantized)

        return quantized_frames

