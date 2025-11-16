"""CLI command definitions for MontagePy."""

import sys
from pathlib import Path

import click

from montagepy.cli.types import FontFilePath
from montagepy.core.config import Config
from montagepy.core.handlers import process_directory, process_single_file
from montagepy.core.logger import Logger


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
    "--auto-grid",
    is_flag=True,
    default=False,
    help="Automatically adjust grid size based on video duration.",
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
    "--output-format",
    type=click.Choice(["jpg", "gif"], case_sensitive=False),
    default="jpg",
    help="Output format: 'jpg' for static images, 'gif' for animated montage.",
)
@click.option(
    "--jpeg-quality",
    type=int,
    default=85,
    help="JPEG quality for the output image (1-100, higher is better).",
)
@click.option(
    "--gif-clip-duration",
    type=float,
    default=2.0,
    help="Duration of each clip in seconds (for GIF mode).",
)
@click.option(
    "--gif-fps",
    type=int,
    default=10,
    help="GIF frame rate (recommended 8-15).",
)
@click.option(
    "--gif-colors",
    type=int,
    default=256,
    help="Number of colors in GIF (max 256, recommended 128-256).",
)
@click.option(
    "--gif-loop",
    type=int,
    default=0,
    help="Number of loops for GIF (0 = infinite).",
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
    output_format: str,
    jpeg_quality: int,
    gif_clip_duration: float,
    gif_fps: int,
    gif_colors: int,
    gif_loop: int,
    max_workers: int,
    config: str,
    overwrite: bool,
    quiet: bool,
    verbose: bool,
    auto_grid: bool,
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
    # Always set output_format from CLI (even if it's the default "jpg")
    cfg.output_format = output_format.lower()
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
    if jpeg_quality != 85:
        cfg.jpeg_quality = jpeg_quality
    if gif_clip_duration != 2.0:
        cfg.gif_clip_duration = gif_clip_duration
    if gif_fps != 10:
        cfg.gif_fps = gif_fps
    if gif_colors != 256:
        cfg.gif_colors = gif_colors
    if gif_loop != 0:
        cfg.gif_loop = gif_loop
    if max_workers != 8:
        cfg.max_workers = max_workers
    if overwrite:
        cfg.overwrite = True
    if quiet:
        cfg.quiet = True
    if verbose:
        cfg.verbose = True
    if auto_grid:
        cfg.auto_grid = True

    # Create logger
    logger = Logger(quiet=cfg.quiet, verbose=cfg.verbose)

    # Check if input is directory or file
    input_path_obj = Path(input_path)
    if input_path_obj.is_dir():
        process_directory(cfg, logger)
    else:
        process_single_file(cfg, logger)

