"""Main CLI group for MontagePy."""

import click

from montagepy.cli.commands import gif, jpg


@click.group(invoke_without_command=True)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True),
    help="Path to YAML config file.",
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
@click.pass_context
def cli(ctx: click.Context, config: str = None, quiet: bool = False, verbose: bool = False) -> None:
    """MontagePy - Generate thumbnail sheets for video files.

    Use 'montagepy jpg <input>' to generate static image montages.
    Use 'montagepy gif <input>' to generate animated GIF montages.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["quiet"] = quiet
    ctx.obj["verbose"] = verbose

    # If no subcommand was invoked, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register subcommands
cli.add_command(jpg)
cli.add_command(gif)

