"""Configuration management for MontagePy."""

from dataclasses import dataclass, field
from typing import List

import yaml


@dataclass
class DurationGridRule:
    """Rule for grid size based on video duration."""

    max_duration: float  # Maximum duration in seconds (-1 means unlimited)
    columns: int
    rows: int


@dataclass
class Config:
    """Configuration for MontagePy."""

    # Input/Output paths
    input_path: str = ""
    output_path: str = ""

    # Grid layout
    columns: int = 4
    rows: int = 5
    thumb_width: int = 640
    thumb_height: int = -1  # -1 means auto-calculate based on aspect ratio
    padding: int = 5
    margin: int = 20
    header_height: int = 120

    # Auto grid based on duration
    auto_grid: bool = False  # Enable automatic grid sizing based on video duration
    duration_grid_rules: List[DurationGridRule] = field(
        default_factory=lambda: [
            DurationGridRule(max_duration=120, columns=2, rows=2),  # 0-2 minutes
            DurationGridRule(max_duration=600, columns=3, rows=3),  # 2-10 minutes
            DurationGridRule(max_duration=1800, columns=4, rows=4),  # 10-30 minutes
            DurationGridRule(max_duration=-1, columns=5, rows=5),  # 30+ minutes
        ]
    )

    # Frame extraction
    skip_start_percent: float = 5.0  # Percentage of video duration to skip at the start (0-100)
    skip_end_percent: float = 5.0  # Percentage of video duration to skip at the end (0-100)
    max_workers: int = 8  # Maximum number of threads for parallel frame extraction

    # Appearance
    font_file: str = ""
    font_color: str = "white"
    shadow_color: str = "black"
    background_color: str = "#222222"
    show_full_path: bool = False
    jpeg_quality: int = 85  # 1-100, higher is better (standard JPEG quality scale)

    # File handling
    overwrite: bool = False

    # Logging
    quiet: bool = False
    verbose: bool = False

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Convert dict to Config, only including fields that exist in Config
        config_dict = {}
        for key, value in data.items():
            # Convert snake_case keys from YAML to the dataclass field names
            if hasattr(cls, key):
                # Special handling for duration_grid_rules
                if key == "duration_grid_rules" and isinstance(value, list):
                    rules = []
                    for rule_dict in value:
                        rules.append(
                            DurationGridRule(
                                max_duration=rule_dict.get("max_duration", -1),
                                columns=rule_dict.get("columns", 4),
                                rows=rule_dict.get("rows", 5),
                            )
                        )
                    config_dict[key] = rules
                else:
                    config_dict[key] = value

        return cls(**config_dict)

    def merge(self, other: "Config") -> None:
        """Merge another config into this one, only overwriting non-default values."""
        for field_name, field_value in other.__dict__.items():
            if field_value is not None and field_value != "":
                setattr(self, field_name, field_value)

