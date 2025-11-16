"""Grid utility functions for MontagePy."""

from montagepy.core.config import Config


def get_grid_size_by_duration(config: Config, duration_seconds: float) -> tuple[int, int]:
    """Get grid size (columns, rows) based on video duration.

    Args:
        config: Configuration object
        duration_seconds: Video duration in seconds

    Returns:
        Tuple of (columns, rows)
    """
    if not config.auto_grid or not config.duration_grid_rules:
        return config.columns, config.rows

    # Separate rules with limits and default rule (max_duration: -1)
    limited_rules = [r for r in config.duration_grid_rules if r.max_duration > 0]
    default_rule = next((r for r in config.duration_grid_rules if r.max_duration < 0), None)

    # Check limited rules first (sorted by max_duration ascending)
    for rule in sorted(limited_rules, key=lambda r: r.max_duration):
        if duration_seconds <= rule.max_duration:
            return rule.columns, rule.rows

    # If no limited rule matches, use default rule (max_duration: -1)
    if default_rule:
        return default_rule.columns, default_rule.rows

    # Fallback to config defaults
    return config.columns, config.rows

