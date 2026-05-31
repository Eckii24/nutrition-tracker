from pathlib import Path
from typing import Any

from nutrition_tracker.errors import ValidationError
from nutrition_tracker.jsonio import load_json_file
from nutrition_tracker.repositories.correction_repo import append_correction, read_corrections_for_date
from nutrition_tracker.repositories.meal_repo import meal_exists
from nutrition_tracker.schema_registry import validate_payload
from nutrition_tracker.utils.dates import date_from_timestamp, parse_timestamp
from nutrition_tracker.utils.ids import make_event_id


def add_correction(root: Path, payload_file: Path) -> dict[str, Any]:
    payload = load_json_file(payload_file)
    correction = prepare_correction(root, payload)
    target = append_correction(root, correction)
    return {"status": "ok", "correction": correction, "path": str(target.relative_to(root))}


def prepare_correction(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    correction = dict(payload)
    timestamp = correction.get("timestamp")
    if not timestamp:
        raise ValidationError("Correction timestamp is required")
    parse_timestamp(timestamp)
    meal_id = correction.get("meal_id")
    if not meal_id:
        raise ValidationError("Correction meal_id is required")
    if not meal_exists(root, meal_id):
        raise ValidationError(f"Correction targets unknown meal_id: {meal_id}")

    date_str = date_from_timestamp(timestamp)
    correction.setdefault("revision", 2)
    correction.setdefault("changes", {})
    if "id" not in correction:
        existing = read_corrections_for_date(root, date_str)
        correction["id"] = make_event_id("corr", timestamp, len(existing) + 1)
    validate_payload(root, "correction-entry.schema.json", correction)
    return correction
