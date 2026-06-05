from __future__ import annotations

from pathlib import Path
from typing import Any

from nutrition_tracker.application.daily import build_daily_summary
from nutrition_tracker.domain.dates import iso_week_dates, parse_iso_week
from nutrition_tracker.domain.entities import WeeklySummary
from nutrition_tracker.infrastructure.meal_repository import read_meals_for_date
from nutrition_tracker.infrastructure.schema_store import validate_payload
from nutrition_tracker.infrastructure.summary_repository import save_weekly_summary


def _round_number(value: float) -> float | int:
    rounded = round(value, 1)
    if rounded == int(rounded):
        return int(rounded)
    return rounded


def build_weekly_summary(root: Path, iso_week: str) -> WeeklySummary:
    parse_iso_week(iso_week)
    included_dates: list[str] = []
    day_totals: list[dict[str, Any]] = []
    for date_str in iso_week_dates(iso_week):
        if not read_meals_for_date(root, date_str):
            continue
        summary = build_daily_summary(root, date_str)
        if summary["signals"].get("meal_count", 0) == 0:
            continue
        included_dates.append(date_str)
        day_totals.append(summary["totals"])

    averages: dict[str, float | int] = {}
    metric_values: dict[str, list[float]] = {}
    for totals in day_totals:
        for metric, value in totals.items():
            if isinstance(value, int | float):
                metric_values.setdefault(metric, []).append(float(value))
    for metric, values in metric_values.items():
        if values:
            averages[metric] = _round_number(sum(values) / len(values))

    days_tracked = len(included_dates)
    summary: WeeklySummary = {
        "week": iso_week,
        "included_dates": included_dates,
        "days_tracked": days_tracked,
        "days_total": 7,
        "coverage_pct": round(days_tracked / 7 * 100, 1),
        "averages": averages,
    }
    validate_payload(root, "weekly-summary.schema.json", summary)
    save_weekly_summary(root, summary)
    return summary
