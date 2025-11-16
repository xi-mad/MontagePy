"""Logging utilities for MontagePy."""

import sys
from datetime import datetime


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

    def _now(self) -> str:
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    def info(self, message: str, *args) -> None:
        """Log an info message."""
        if not self.quiet:
            prefix = self._now()
            if args:
                print(f"{prefix} {message % args}", file=sys.stderr)
            else:
                print(f"{prefix} {message}", file=sys.stderr)

    def verbose(self, message: str, *args) -> None:
        """Log a verbose message."""
        if self.verbose and not self.quiet:
            prefix = self._now()
            if args:
                print(f"{prefix} {message % args}", file=sys.stderr)
            else:
                print(f"{prefix} {message}", file=sys.stderr)

    def error(self, message: str, *args) -> None:
        """Log an error message."""
        if not self.quiet:
            prefix = self._now()
            if args:
                print(f"{prefix} Error: {message % args}", file=sys.stderr)
            else:
                print(f"{prefix} Error: {message}", file=sys.stderr)

