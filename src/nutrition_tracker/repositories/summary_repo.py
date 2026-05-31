from pathlib import Path
from typing import Any

from nutrition_tracker.jsonio import load_json_file, write_json_file
from nutrition_tracker.paths import daily_summary_file, weekly_summary_file


def save_daily_summary(root: Path, summary: dict[str, Any]) -> Path:
    target = daily_summary_file(root, summary["date"])
    write_json_file(target, summary)
    return target


def load_daily_summary(root: Path, date_str: str) -> dict[str, Any] | None:
    target = daily_summary_file(root, date_str)
    if not target.exists():
        return None
    return load_json_file(target)


def save_weekly_summary(root: Path, summary: dict[str, Any]) -> Path:
    target = weekly_summary_file(root, summary["week"])
    write_json_file(target, summary)
    return target
