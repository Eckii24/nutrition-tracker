from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from nutrition_tracker.constants import ALL_NUTRITION_METRICS, GOAL_METRICS, REQUIRED_NUTRITION_METRICS
from nutrition_tracker.repositories.correction_repo import iter_all_corrections
from nutrition_tracker.repositories.meal_repo import read_meals_for_date
from nutrition_tracker.repositories.settings_repo import load_settings
from nutrition_tracker.repositories.summary_repo import save_daily_summary
from nutrition_tracker.schema_registry import validate_payload
from nutrition_tracker.services.goal_service import effective_goals
from nutrition_tracker.utils.dates import parse_date, parse_timestamp


def _sorted_corrections(corrections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(corrections, key=lambda item: item.get("timestamp", ""))


def _apply_replace(meal: dict[str, Any], changes: dict[str, Any], revision: int) -> dict[str, Any]:
    updated = deepcopy(meal)
    for key, value in changes.items():
        if key in {
            "foods",
            "nutrition",
            "notes",
            "assumptions",
            "quality_signals",
            "micros",
            "source_context",
        }:
            updated[key] = value
    updated["revision"] = revision
    return updated


def project_meals_for_date(root: Path, date_str: str) -> list[dict[str, Any]]:
    parse_date(date_str)
    base_meals = [deepcopy(meal) for meal in read_meals_for_date(root, date_str)]
    by_id = {meal["id"]: meal for meal in base_meals}
    cancelled: set[str] = set()

    relevant = [corr for corr in iter_all_corrections(root) if corr.get("meal_id") in by_id]
    for correction in _sorted_corrections(relevant):
        meal_id = correction["meal_id"]
        operation = correction["operation"]
        revision = int(correction.get("revision", by_id[meal_id].get("revision", 1) + 1))
        if operation == "cancel":
            cancelled.add(meal_id)
            by_id[meal_id]["revision"] = revision
        elif operation == "replace":
            by_id[meal_id] = _apply_replace(by_id[meal_id], correction.get("changes", {}), revision)
            cancelled.discard(meal_id)
        elif operation == "annotate":
            changes = correction.get("changes", {})
            if "notes" in changes:
                existing = by_id[meal_id].get("notes", "")
                by_id[meal_id]["notes"] = "\n".join(part for part in [existing, changes["notes"]] if part)
            by_id[meal_id]["revision"] = revision

    projected: list[dict[str, Any]] = []
    for meal in base_meals:
        effective = deepcopy(by_id[meal["id"]])
        is_cancelled = meal["id"] in cancelled
        effective["cancelled"] = is_cancelled
        effective["effective"] = not is_cancelled
        projected.append(effective)
    return projected


def effective_meals_for_date(root: Path, date_str: str) -> list[dict[str, Any]]:
    return [meal for meal in project_meals_for_date(root, date_str) if meal.get("effective", True)]


def _round_number(value: float) -> float | int:
    rounded = round(value, 1)
    if rounded == int(rounded):
        return int(rounded)
    return rounded


def calculate_totals(meals: list[dict[str, Any]]) -> dict[str, float | int]:
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


def _data_confidence(meals: list[dict[str, Any]]) -> str:
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


def _signals(meals: list[dict[str, Any]]) -> dict[str, Any]:
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


def build_daily_summary(root: Path, date_str: str) -> dict[str, Any]:
    parse_date(date_str)
    for meal in read_meals_for_date(root, date_str):
        validate_payload(root, "meal-entry.schema.json", meal)
        parse_timestamp(meal["timestamp"])

    meals = effective_meals_for_date(root, date_str)
    totals = calculate_totals(meals)
    goals = _goal_values(root)
    summary = {
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
    meals = project_meals_for_date(root, date_str)
    return {"date": date_str, "meals": meals}
