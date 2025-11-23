"""Business logic handlers for processing video files."""

import sys
from pathlib import Path

from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.converters.gif_converter import GifConverter
from montagepy.extractors.clip_extractor import ClipExtractor
from montagepy.extractors.frame_extractor import FrameExtractor
from montagepy.renderers.gif_montage_renderer import GifMontageRenderer
from montagepy.renderers.montage_renderer import MontageRenderer
from montagepy.utils.file_utils import generate_unique_filename, scan_video_files
from montagepy.utils.grid_utils import get_grid_size_by_duration
from montagepy.video_info import get_video_info


def process_single_file(cfg: Config, logger: Logger) -> None:
    """Process a single video file.

    Args:
        cfg: Configuration object
        logger: Logger instance
    """
    # Set output path if not specified
    if not cfg.output_path:
        input_dir = Path(cfg.input_path).parent
        base_name = Path(cfg.input_path).stem
        extension = "gif" if cfg.output_format.lower() == "gif" else "jpg"
        cfg.output_path = str(input_dir / f"{base_name}_montage.{extension}")

    # Check if output file exists or is a directory
    if cfg.output_path and cfg.output_path != "-":
        output_path_obj = Path(cfg.output_path)
        
        # If output path is a directory (or looks like one without extension), generate filename
        is_directory = (output_path_obj.exists() and output_path_obj.is_dir()) or (
            not output_path_obj.exists() and not output_path_obj.suffix
        )
        
        if is_directory:
            output_path_obj.mkdir(parents=True, exist_ok=True)
            base_name = Path(cfg.input_path).stem
            extension = "gif" if cfg.output_format.lower() == "gif" else "jpg"
            cfg.output_path = str(output_path_obj / f"{base_name}_montage.{extension}")
            output_path_obj = Path(cfg.output_path)

        if output_path_obj.exists() and not cfg.overwrite:
            logger.error(f"File already exists (use --overwrite to force): {cfg.output_path}")
            raise FileExistsError(f"File already exists: {cfg.output_path}")

        # Ensure output directory exists (in case it was a file path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Get video info
    logger.info("Analyzing video file: %s", cfg.input_path)
    try:
        video_info = get_video_info(cfg.input_path)
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        raise RuntimeError(f"Failed to get video info: {e}")

    # Auto-adjust grid size based on duration if enabled
    if cfg.auto_grid:
        original_columns, original_rows = cfg.columns, cfg.rows
        cfg.columns, cfg.rows = get_grid_size_by_duration(cfg, video_info.duration)
        if cfg.columns != original_columns or cfg.rows != original_rows:
            duration_minutes = video_info.duration / 60.0
            logger.info(
                "Auto-adjusted grid size: %dx%d -> %dx%d (duration: %.1f minutes)",
                original_columns,
                original_rows,
                cfg.columns,
                cfg.rows,
                duration_minutes,
            )

    # Process video
    logger.info("Video analysis complete. Starting montage generation...")
    try:
        if cfg.output_format.lower() == "gif":
            # GIF mode: extract clips and convert to GIF
            logger.info("GIF mode: Extracting video clips...")
            
            # First, calculate timestamps (same logic as frame extraction)
            num_clips = cfg.columns * cfg.rows
            skip_start = cfg.skip_start_percent / 100.0
            skip_end = cfg.skip_end_percent / 100.0
            
            start_offset = video_info.duration * skip_start
            end_offset = video_info.duration * (1.0 - skip_end)
            duration = end_offset - start_offset
            interval = duration / num_clips
            
            timestamps = [start_offset + (i * interval) for i in range(num_clips)]
            
            # Extract clips
            clip_extractor = ClipExtractor(cfg, video_info, logger)
            clips = clip_extractor.extract_clips(timestamps)
            
            # Convert clips to GIFs
            logger.info("Converting clips to GIFs...")
            gif_converter = GifConverter(cfg, logger)
            gif_images = []
            clip_timestamps = []
            
            for clip in clips:
                thumb_width = cfg.thumb_width
                thumb_height = cfg.thumb_height
                if thumb_height <= 0:
                    thumb_height = int(thumb_width / (video_info.width / video_info.height))
                
                gif_img = gif_converter.convert_clip_to_gif(clip, thumb_width, thumb_height)
                gif_images.append(gif_img)
                clip_timestamps.append(clip.timestamp)
            
            # Render GIF montage
            logger.info("Composing GIF montage...")
            renderer = GifMontageRenderer(cfg, video_info, logger)
            renderer.render(gif_images, clip_timestamps)
        else:
            # JPG mode: extract frames and render static montage
            extractor = FrameExtractor(cfg, video_info, logger)
            frames, timestamps = extractor.extract_frames()

            renderer = MontageRenderer(cfg, video_info, logger)
            renderer.render(frames, timestamps)
    except Exception as e:
        logger.error(f"Failed to generate montage: {e}")
        # print trace
        import traceback

        traceback.print_exc()
        traceback.print_exc()
        raise RuntimeError(f"Failed to generate montage: {e}")

    if cfg.output_path != "-":
        logger.info("✅ Montage generated successfully at: %s", cfg.output_path)
    else:
        logger.info("✅ Montage generated successfully to stdout.")


def process_directory(cfg: Config, logger: Logger) -> None:
    """Process a directory of video files.

    Args:
        cfg: Configuration object
        logger: Logger instance
    """
    logger.info("Scanning directory for video files: %s", cfg.input_path)
    try:
        video_files = scan_video_files(cfg.input_path)
    except Exception as e:
        logger.error(f"Failed to scan directory: {e}")
        raise RuntimeError(f"Failed to scan directory: {e}")

    if not video_files:
        logger.info("No video files found in directory.")
        return

    logger.info("Found %d video file(s).", len(video_files))

    if cfg.output_path == "-":
        logger.info("Warning: Output to stdout is not supported for directory processing.")
        logger.info("Each video will generate a montage file next to the video file.")

    # Process each video file
    success_count = 0
    for i, video_file in enumerate(video_files, 1):
        logger.info("[%d/%d] Processing: %s", i, len(video_files), video_file)

        # Create a copy of config for this video
        video_cfg = Config()
        video_cfg.__dict__.update(cfg.__dict__)
        video_cfg.input_path = video_file

        # Set output path
        if cfg.output_path and cfg.output_path != "-":
            output_path_obj = Path(cfg.output_path)
            # Check if output path is a directory (exists and is dir, or doesn't exist and has no extension)
            is_directory = (output_path_obj.exists() and output_path_obj.is_dir()) or (
                not output_path_obj.exists() and not output_path_obj.suffix
            )

            if is_directory:
                # Output is a directory - use unique filename based on relative path
                output_path_obj.mkdir(parents=True, exist_ok=True)
                extension = "gif" if cfg.output_format.lower() == "gif" else "jpg"
                unique_filename = generate_unique_filename(video_file, cfg.input_path, extension)
                video_cfg.output_path = str(output_path_obj / unique_filename)
                if logger:
                    if logger.verbose:
                        logger.verbose(f"Video file: {video_file}")
                        logger.verbose(f"Input root: {cfg.input_path}")
                        logger.verbose(f"Generated unique filename: {unique_filename}")
                        logger.verbose(f"Full output path: {video_cfg.output_path}")
                    else:
                        logger.info(f"Output: {unique_filename}")
            else:
                # Output is a file pattern (only works for single file)
                video_cfg.output_path = cfg.output_path
        else:
            # Default: place next to video file (will be set in process_single_file)
            video_cfg.output_path = ""

        try:
            process_single_file(video_cfg, logger)
            success_count += 1
        except SystemExit:
            # Skip files that already exist
            continue
        except Exception as e:
            logger.error(f"Failed to process {video_file}: {e}")
            continue

    logger.info("✅ Successfully processed %d/%d video file(s).", success_count, len(video_files))

