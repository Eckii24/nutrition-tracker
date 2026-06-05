from __future__ import annotations

from pathlib import Path
from typing import Any

from nutrition_tracker.application.goals import effective_goals
from nutrition_tracker.domain.constants import (
    ALL_NUTRITION_METRICS,
    GOAL_METRICS,
    REQUIRED_NUTRITION_METRICS,
)
from nutrition_tracker.domain.dates import parse_date, parse_timestamp
from nutrition_tracker.domain.entities import DailySummary, Meal
from nutrition_tracker.infrastructure.meal_repository import read_meals_for_date
from nutrition_tracker.infrastructure.schema_store import validate_payload
from nutrition_tracker.infrastructure.settings_repository import load_settings
from nutrition_tracker.infrastructure.summary_repository import save_daily_summary


def _round_number(value: float) -> float | int:
    rounded = round(value, 1)
    if rounded == int(rounded):
        return int(rounded)
    return rounded


def calculate_totals(meals: list[Meal]) -> dict[str, float | int]:
    totals: dict[str, float] = {metric: 0.0 for metric in REQUIRED_NUTRITION_METRICS}
    for meal in meals:
        nutrition = meal.get("nutrition", {})
        for metric, value in nutrition.items():
            if metric in ALL_NUTRITION_METRICS and isinstance(value, int | float):
                totals[metric] = totals.get(metric, 0.0) + float(value)
    return {metric: _round_number(value) for metric, value in totals.items()}


def _goal_values(root: Path) -> dict[str, float]:
    return effective_goals(load_settings(root))


def _deltas(totals: dict[str, float | int], goals: dict[str, float]) -> dict[str, float | int]:
    delta: dict[str, float | int] = {}
    for metric in GOAL_METRICS:
        goal = goals.get(metric)
        if goal is None:
            continue
        delta[metric] = _round_number(float(totals.get(metric, 0)) - float(goal))
    return delta


def _progress(totals: dict[str, float | int], goals: dict[str, float]) -> dict[str, float | None]:
    progress: dict[str, float | None] = {}
    for metric in GOAL_METRICS:
        goal = goals.get(metric)
        if not goal:
            progress[metric] = None
        else:
            progress[metric] = round(float(totals.get(metric, 0)) / float(goal) * 100, 1)
    return progress


def _data_confidence(meals: list[Meal]) -> str:
    if not meals:
        return "unknown"
    confidence_values: list[str] = []
    estimated_seen = False
    for meal in meals:
        for food in meal.get("foods", []):
            if food.get("estimated"):
                estimated_seen = True
            confidence = food.get("confidence")
            if confidence:
                confidence_values.append(confidence)
    if "low" in confidence_values:
        return "low"
    if estimated_seen or "medium" in confidence_values or not confidence_values:
        return "medium"
    return "high"


def _signals(meals: list[Meal]) -> dict[str, Any]:
    fruit = 0.0
    vegetables = 0.0
    processed = 0
    for meal in meals:
        signals = meal.get("quality_signals", {}) or {}
        fruit += float(signals.get("fruit_servings", 0) or 0)
        vegetables += float(signals.get("vegetable_servings", 0) or 0)
        if signals.get("highly_processed"):
            processed += 1
    return {
        "meal_count": len(meals),
        "fruit_servings": _round_number(fruit),
        "vegetable_servings": _round_number(vegetables),
        "highly_processed_meal_count": processed,
        "data_confidence": _data_confidence(meals),
    }


def build_daily_summary(root: Path, date_str: str) -> DailySummary:
    parse_date(date_str)
    meals = read_meals_for_date(root, date_str)
    for meal in meals:
        validate_payload(root, "meal-entry.schema.json", meal)
        parse_timestamp(meal["timestamp"])

    totals = calculate_totals(meals)
    goals = _goal_values(root)
    summary: DailySummary = {
        "date": date_str,
        "meals": meals,
        "totals": totals,
        "goals": goals,
        "delta": _deltas(totals, goals),
        "progress_pct": _progress(totals, goals),
        "signals": _signals(meals),
    }
    validate_payload(root, "daily-summary.schema.json", summary)
    save_daily_summary(root, summary)
    return summary


def list_meals(root: Path, date_str: str) -> dict[str, Any]:
    parse_date(date_str)
    meals = read_meals_for_date(root, date_str)
    return {"date": date_str, "meals": meals}
