"""JPG command for generating static image montages."""

import sys
from pathlib import Path

import click

from montagepy.cli.options.appearance import add_appearance_options
from montagepy.cli.options.common import add_common_options
from montagepy.core.config import Config
from montagepy.core.handlers import process_directory, process_single_file
from montagepy.core.logger import Logger


@click.command(name="jpg")
@click.argument("input_path", type=click.Path(exists=True))
@add_common_options
@add_appearance_options
@click.option(
    "--quality",
    "jpeg_quality",
    type=int,
    default=85,
    help="JPEG quality (1-100, higher is better).",
)
@click.pass_context
def jpg(
    ctx: click.Context,
    input_path: str,
    output_path: str,
    columns: int,
    rows: int,
    auto_grid: bool,
    thumb_width: int,
    thumb_height: int,
    padding: int,
    margin: int,
    header_height: int,
    skip_start_percent: float,
    skip_end_percent: float,
    max_workers: int,
    overwrite: bool,
    font_file: str,
    font_color: str,
    shadow_color: str,
    background_color: str,
    show_full_path: bool,
    jpeg_quality: int,
) -> None:
    """Generate static image montage from video file(s).

    INPUT_PATH can be a video file or a directory containing video files.
    """
    # Get global options from context
    config = ctx.obj.get("config")
    quiet = ctx.obj.get("quiet", False)
    verbose = ctx.obj.get("verbose", False)

    # Set output format
    cfg = Config()
    cfg.output_format = "jpg"

    # Load config from file if provided
    if config:
        try:
            cfg = Config.from_yaml(config)
            cfg.output_format = "jpg"  # Force JPG format
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

    # Apply CLI arguments
    cfg.input_path = input_path
    if output_path:
        cfg.output_path = output_path
    if columns != 4:
        cfg.columns = columns
    if rows != 5:
        cfg.rows = rows
    if auto_grid:
        cfg.auto_grid = True
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
    if max_workers != 8:
        cfg.max_workers = max_workers
    if overwrite:
        cfg.overwrite = True
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

