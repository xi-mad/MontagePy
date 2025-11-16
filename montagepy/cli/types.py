"""Custom Click parameter types for MontagePy."""

from pathlib import Path

import click


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

