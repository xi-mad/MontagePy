"""Appearance-related CLI options."""

import click

from montagepy.cli.types import FontFilePath


def add_appearance_options(func):
    """Add appearance options to a command."""
    func = click.option(
        "--font-file",
        type=FontFilePath(),
        default="",
        help="Path to a .ttf font file for text rendering. Leave empty to disable text rendering.",
    )(func)
    func = click.option(
        "--font-color",
        type=str,
        default="white",
        help="Color of the main font.",
    )(func)
    func = click.option(
        "--shadow-color",
        type=str,
        default="black",
        help="Color of the text shadow.",
    )(func)
    func = click.option(
        "--bg-color",
        "background_color",
        type=str,
        default="#222222",
        help="Background color of the montage.",
    )(func)
    func = click.option(
        "--show-full-path",
        is_flag=True,
        default=False,
        help="Show full file path instead of just filename in the montage header.",
    )(func)
    return func

