"""Logging utilities for MontagePy."""

import sys


class Logger:
    """Simple logger for MontagePy."""

    def __init__(self, quiet: bool = False, verbose: bool = False):
        """Initialize logger.
        
        Args:
            quiet: If True, suppress all output
            verbose: If True, enable verbose output
        """
        self.quiet = quiet
        self.verbose = verbose

    def info(self, message: str, *args) -> None:
        """Log an info message."""
        if not self.quiet:
            if args:
                print(message % args, file=sys.stderr)
            else:
                print(message, file=sys.stderr)

    def verbose(self, message: str, *args) -> None:
        """Log a verbose message."""
        if self.verbose and not self.quiet:
            if args:
                print(message % args, file=sys.stderr)
            else:
                print(message, file=sys.stderr)

    def error(self, message: str, *args) -> None:
        """Log an error message."""
        if not self.quiet:
            if args:
                print(f"Error: {message % args}", file=sys.stderr)
            else:
                print(f"Error: {message}", file=sys.stderr)
