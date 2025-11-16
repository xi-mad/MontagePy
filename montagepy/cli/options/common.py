"""Common CLI options shared across commands."""

import click


def add_common_options(func):
    """Add common options to a command."""
    func = click.option(
        "-o",
        "--output",
        "output_path",
        type=str,
        default="",
        help="Output path. Use '-' to stream image data to stdout.",
    )(func)
    func = click.option(
        "-c",
        "--columns",
        type=int,
        default=4,
        help="Number of columns in the grid.",
    )(func)
    func = click.option(
        "-r",
        "--rows",
        type=int,
        default=5,
        help="Number of rows in the grid.",
    )(func)
    func = click.option(
        "--auto-grid",
        is_flag=True,
        default=False,
        help="Automatically adjust grid size based on video duration.",
    )(func)
    func = click.option(
        "--thumb-width",
        type=int,
        default=640,
        help="Width of each thumbnail.",
    )(func)
    func = click.option(
        "--thumb-height",
        type=int,
        default=-1,
        help="Height of each thumbnail. Defaults to -1 (auto-scale based on aspect ratio).",
    )(func)
    func = click.option(
        "--padding",
        type=int,
        default=5,
        help="Padding between thumbnails.",
    )(func)
    func = click.option(
        "--margin",
        type=int,
        default=20,
        help="Margin around the grid.",
    )(func)
    func = click.option(
        "--header",
        "header_height",
        type=int,
        default=120,
        help="Height of the header section.",
    )(func)
    func = click.option(
        "--skip-start",
        "skip_start_percent",
        type=float,
        default=5.0,
        help="Percentage of video duration to skip at the start (0-100).",
    )(func)
    func = click.option(
        "--skip-end",
        "skip_end_percent",
        type=float,
        default=5.0,
        help="Percentage of video duration to skip at the end (0-100).",
    )(func)
    func = click.option(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum number of threads for parallel processing.",
    )(func)
    func = click.option(
        "--overwrite",
        is_flag=True,
        default=False,
        help="Overwrite existing output files.",
    )(func)
    return func

