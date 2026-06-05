from __future__ import annotations

from pathlib import Path
from typing import Any

from nutrition_tracker.domain.dates import date_from_timestamp, parse_timestamp
from nutrition_tracker.domain.entities import Meal
from nutrition_tracker.domain.errors import ValidationError
from nutrition_tracker.domain.ids import make_event_id
from nutrition_tracker.infrastructure.json_store import load_json_file
from nutrition_tracker.infrastructure.meal_repository import append_meal, read_meals_for_date
from nutrition_tracker.infrastructure.schema_store import validate_payload


def add_meal(root: Path, payload_file: Path) -> dict[str, Any]:
    payload = load_json_file(payload_file)
    meal = prepare_meal(root, payload)
    target = append_meal(root, meal)
    return {"status": "ok", "meal": meal, "path": str(target.relative_to(root))}


def prepare_meal(root: Path, payload: dict[str, Any]) -> Meal:
    meal = dict(payload)
    timestamp = meal.get("timestamp")
    if not timestamp:
        raise ValidationError("Meal timestamp is required")
    parse_timestamp(timestamp)
    date_str = date_from_timestamp(timestamp)
    meal.setdefault("revision", 1)
    if "id" not in meal:
        existing = read_meals_for_date(root, date_str)
        meal["id"] = make_event_id("meal", timestamp, len(existing) + 1)
    meal.setdefault("assumptions", [])
    meal.setdefault("micros", {})
    validate_payload(root, "meal-entry.schema.json", meal)
    return meal
