from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from nutrition_tracker.domain.constants import GOAL_METRICS
from nutrition_tracker.domain.entities import Settings
from nutrition_tracker.domain.nutrition_math import derive_daily_targets
from nutrition_tracker.infrastructure.settings_repository import load_settings, save_settings


def _override_target(value: Any) -> float:
    if isinstance(value, dict):
        return value.get("target")
    return value


def derive_goals(settings: Settings, on_date: date | None = None) -> dict[str, int]:
    return derive_daily_targets(settings, on_date=on_date)


def derive_goal_entries(
    settings: Settings, on_date: date | None = None
) -> dict[str, dict[str, Any]]:
    computed = derive_goals(settings, on_date=on_date)
    overrides = settings.setdefault("goals", {}).setdefault("overrides", {})
    daily: dict[str, dict[str, Any]] = {}
    for metric in GOAL_METRICS:
        computed_value = computed[metric]
        if metric in overrides:
            target = _override_target(overrides[metric])
            daily[metric] = {
                "target": target,
                "source": "override",
                "computed": computed_value,
            }
        else:
            daily[metric] = {
                "target": computed_value,
                "source": "derived",
                "computed": computed_value,
            }
    return daily


def derive_and_save_goals(root: Path) -> dict[str, Any]:
    settings = load_settings(root)
    settings.setdefault("goals", {})["daily"] = derive_goal_entries(settings)
    save_settings(root, settings)
    return {"status": "ok", "daily": settings["goals"]["daily"]}


def effective_goals(settings: Settings) -> dict[str, float]:
    daily = settings.get("goals", {}).get("daily", {})
    if not all(metric in daily for metric in GOAL_METRICS):
        daily = derive_goal_entries(settings)
    goals: dict[str, float] = {}
    for metric in GOAL_METRICS:
        entry = daily.get(metric, {})
        if isinstance(entry, dict):
            goals[metric] = entry.get("target", 0)
        else:
            goals[metric] = entry
    return goals
