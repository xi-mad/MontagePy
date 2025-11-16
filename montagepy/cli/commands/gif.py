"""GIF command for generating animated GIF montages."""

import sys
from pathlib import Path

import click

from montagepy.cli.options.appearance import add_appearance_options
from montagepy.cli.options.common import add_common_options
from montagepy.core.config import Config
from montagepy.core.handlers import process_directory, process_single_file
from montagepy.core.logger import Logger


@click.command(name="gif")
@click.argument("input_path", type=click.Path(exists=True))
@add_common_options
@add_appearance_options
@click.option(
    "--clip-duration",
    "gif_clip_duration",
    type=float,
    default=2.0,
    help="Duration of each clip in seconds.",
)
@click.option(
    "--fps",
    "gif_fps",
    type=int,
    default=10,
    help="GIF frame rate (recommended 8-15).",
)
@click.option(
    "--colors",
    "gif_colors",
    type=int,
    default=256,
    help="Number of colors in GIF (max 256, recommended 128-256).",
)
@click.option(
    "--loop",
    "gif_loop",
    type=int,
    default=0,
    help="Number of loops (0 = infinite).",
)
@click.pass_context
def gif(
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
    gif_clip_duration: float,
    gif_fps: int,
    gif_colors: int,
    gif_loop: int,
) -> None:
    """Generate animated GIF montage from video file(s).

    INPUT_PATH can be a video file or a directory containing video files.
    """
    # Get global options from context
    config = ctx.obj.get("config")
    quiet = ctx.obj.get("quiet", False)
    verbose = ctx.obj.get("verbose", False)

    # Set output format
    cfg = Config()
    cfg.output_format = "gif"

    # Load config from file if provided
    if config:
        try:
            cfg = Config.from_yaml(config)
            cfg.output_format = "gif"  # Force GIF format
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
    if gif_clip_duration != 2.0:
        cfg.gif_clip_duration = gif_clip_duration
    if gif_fps != 10:
        cfg.gif_fps = gif_fps
    if gif_colors != 256:
        cfg.gif_colors = gif_colors
    if gif_loop != 0:
        cfg.gif_loop = gif_loop
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

