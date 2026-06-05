from __future__ import annotations

from pathlib import Path

from nutrition_tracker.domain.entities import DailySummary, WeeklySummary
from nutrition_tracker.infrastructure.json_store import load_json_file, write_json_file
from nutrition_tracker.infrastructure.project_paths import daily_summary_file, weekly_summary_file


def save_daily_summary(root: Path, summary: DailySummary) -> Path:
    target = daily_summary_file(root, summary["date"])
    write_json_file(target, summary)
    return target


def load_daily_summary(root: Path, date_str: str) -> DailySummary:
    return load_json_file(daily_summary_file(root, date_str))


def save_weekly_summary(root: Path, summary: WeeklySummary) -> Path:
    target = weekly_summary_file(root, summary["week"])
    write_json_file(target, summary)
    return target
