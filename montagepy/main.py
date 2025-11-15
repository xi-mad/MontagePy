"""Main CLI entry point for MontagePy."""

import sys
from pathlib import Path

import click

from montagepy.config import Config
from montagepy.logger import Logger
from montagepy.processor import Processor
from montagepy.utils import generate_unique_filename, scan_video_files
from montagepy.video_info import get_video_info


class FontFilePath(click.ParamType):
    """Custom path type that allows empty string but validates non-empty paths."""
    name = "font_file_path"

    def convert(self, value, param, ctx):
        if not value or value == "":
            return ""
        # Validate path exists if non-empty
        path = Path(value)
        if not path.exists():
            self.fail(f"Path '{value}' does not exist", param, ctx)
        return str(path)


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=str,
    default="",
    help="Output path. Use '-' to stream image data to stdout.",
)
@click.option(
    "-c",
    "--columns",
    type=int,
    default=4,
    help="Number of columns in the grid.",
)
@click.option(
    "-r",
    "--rows",
    type=int,
    default=5,
    help="Number of rows in the grid.",
)
@click.option(
    "--thumb-width",
    type=int,
    default=640,
    help="Width of each thumbnail.",
)
@click.option(
    "--thumb-height",
    type=int,
    default=-1,
    help="Height of each thumbnail. Defaults to -1 (auto-scale based on aspect ratio).",
)
@click.option(
    "--padding",
    type=int,
    default=5,
    help="Padding between thumbnails.",
)
@click.option(
    "--margin",
    type=int,
    default=20,
    help="Margin around the grid.",
)
@click.option(
    "--header",
    "header_height",
    type=int,
    default=120,
    help="Height of the header section.",
)
@click.option(
    "--skip-start",
    "skip_start_percent",
    type=float,
    default=5.0,
    help="Percentage of video duration to skip at the start (0-100).",
)
@click.option(
    "--skip-end",
    "skip_end_percent",
    type=float,
    default=5.0,
    help="Percentage of video duration to skip at the end (0-100).",
)
@click.option(
    "--font-file",
    type=FontFilePath(),
    default="",
    help="Path to a .ttf font file for text rendering. Leave empty to disable text rendering.",
)
@click.option(
    "--font-color",
    type=str,
    default="white",
    help="Color of the main font.",
)
@click.option(
    "--shadow-color",
    type=str,
    default="black",
    help="Color of the text shadow.",
)
@click.option(
    "--bg-color",
    "background_color",
    type=str,
    default="#222222",
    help="Background color of the montage.",
)
@click.option(
    "--show-full-path",
    is_flag=True,
    default=False,
    help="Show full file path instead of just filename in the montage header.",
)
@click.option(
    "--jpeg-quality",
    type=int,
    default=2,
    help="JPEG quality for the output image (1-31, lower is better).",
)
@click.option(
    "--max-workers",
    type=int,
    default=8,
    help="Maximum number of threads for parallel frame extraction.",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to YAML config file.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing output files.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress all log output.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output.",
)
@click.version_option(version="0.1.0")
def main(
        input_path: str,
        output_path: str,
        columns: int,
        rows: int,
        thumb_width: int,
        thumb_height: int,
        padding: int,
        margin: int,
        header_height: int,
        skip_start_percent: float,
        skip_end_percent: float,
        font_file: str,
        font_color: str,
        shadow_color: str,
        background_color: str,
        show_full_path: bool,
        jpeg_quality: int,
        max_workers: int,
        config: str,
        overwrite: bool,
        quiet: bool,
        verbose: bool,
) -> None:
    """MontagePy - Generate thumbnail sheets for video files.
    
    INPUT_PATH can be a video file or a directory containing video files.
    """
    # Load config from file if provided
    cfg = Config()
    if config:
        try:
            cfg = Config.from_yaml(config)
            # Validate font_file from config if provided
            if cfg.font_file and cfg.font_file != "":
                font_path = Path(cfg.font_file)
                if not font_path.exists():
                    click.echo(f"Warning: Font file from config does not exist: {cfg.font_file}", err=True)
                    click.echo("Text rendering will be disabled.", err=True)
                    cfg.font_file = ""
        except Exception as e:
            click.echo(f"Error loading config file: {e}", err=True)
            sys.exit(1)

    # Override with CLI arguments (CLI takes precedence)
    cfg.input_path = input_path
    if output_path:
        cfg.output_path = output_path
    if columns != 4:
        cfg.columns = columns
    if rows != 5:
        cfg.rows = rows
    if thumb_width != 640:
        cfg.thumb_width = thumb_width
    if thumb_height != -1:
        cfg.thumb_height = thumb_height
    if padding != 5:
        cfg.padding = padding
    if margin != 20:
        cfg.margin = margin
    if header_height != 120:
        cfg.header_height = header_height
    if skip_start_percent != 5.0:
        cfg.skip_start_percent = skip_start_percent
    if skip_end_percent != 5.0:
        cfg.skip_end_percent = skip_end_percent
    if font_file:
        cfg.font_file = font_file
    if font_color != "white":
        cfg.font_color = font_color
    if shadow_color != "black":
        cfg.shadow_color = shadow_color
    if background_color != "#222222":
        cfg.background_color = background_color
    if show_full_path:
        cfg.show_full_path = True
    if jpeg_quality != 2:
        cfg.jpeg_quality = jpeg_quality
    if max_workers != 8:
        cfg.max_workers = max_workers
    if overwrite:
        cfg.overwrite = True
    if quiet:
        cfg.quiet = True
    if verbose:
        cfg.verbose = True

    # Create logger
    logger = Logger(quiet=cfg.quiet, verbose=cfg.verbose)

    # Check if input is directory or file
    input_path_obj = Path(input_path)
    if input_path_obj.is_dir():
        process_directory(cfg, logger)
    else:
        process_single_file(cfg, logger)


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
        cfg.output_path = str(input_dir / f"{base_name}_montage.jpg")

    # Check if output file exists
    if cfg.output_path != "-":
        output_path_obj = Path(cfg.output_path)
        if output_path_obj.exists() and not cfg.overwrite:
            logger.error(f"File already exists (use --overwrite to force): {cfg.output_path}")
            sys.exit(1)

        # Ensure output directory exists
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Get video info
    logger.info("Analyzing video file: %s", cfg.input_path)
    try:
        video_info = get_video_info(cfg.input_path)
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        sys.exit(1)

    # Process video
    logger.info("Video analysis complete. Starting montage generation...")
    processor = Processor(cfg, video_info, logger)
    try:
        processor.run()
    except Exception as e:
        logger.error(f"Failed to generate montage: {e}")
        # print trace
        import traceback
        traceback.print_exc()
        sys.exit(1)

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
        sys.exit(1)

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
            is_directory = (
                                   output_path_obj.exists() and output_path_obj.is_dir()
                           ) or (
                                   not output_path_obj.exists() and not output_path_obj.suffix
                           )

            if is_directory:
                # Output is a directory - use unique filename based on relative path
                output_path_obj.mkdir(parents=True, exist_ok=True)
                unique_filename = generate_unique_filename(video_file, cfg.input_path)
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


if __name__ == "__main__":
    main()
