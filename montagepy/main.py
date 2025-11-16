"""Main CLI entry point for MontagePy."""

from montagepy.cli import cli

# Export cli as main for entry point compatibility
main = cli

if __name__ == "__main__":
    cli()
