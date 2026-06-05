from pathlib import Path
from typing import Any

from nutrition_tracker.errors import NutritionTrackerError
from nutrition_tracker.jsonio import iter_jsonl_with_line_numbers
from nutrition_tracker.paths import daily_dir, data_dir, meals_dir, settings_path, weekly_dir
from nutrition_tracker.repositories.meal_repo import iter_meal_files
from nutrition_tracker.schema_registry import SCHEMAS, load_schema, validate_payload
from nutrition_tracker.services.daily_service import build_daily_summary
from nutrition_tracker.utils.dates import date_from_timestamp


def run_doctor(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    for directory in [data_dir(root), meals_dir(root), daily_dir(root), weekly_dir(root)]:
        if not directory.exists():
            errors.append(f"Missing directory: {directory.relative_to(root)}")

    for schema_name in SCHEMAS:
        try:
            load_schema(root, schema_name)
        except NutritionTrackerError as exc:
            errors.append(str(exc))

    if not settings_path(root).exists():
        errors.append("Missing settings file: data/settings.json")
    else:
        try:
            from nutrition_tracker.repositories.settings_repo import load_settings

            load_settings(root)
        except NutritionTrackerError as exc:
            errors.append(str(exc))

    meal_ids: set[str] = set()
    meal_dates: set[str] = set()
    for path in iter_meal_files(root):
        try:
            for line_number, meal in iter_jsonl_with_line_numbers(path):
                try:
                    validate_payload(root, "meal-entry.schema.json", meal)
                    meal_id = meal["id"]
                    if meal_id in meal_ids:
                        errors.append(f"Duplicate meal id {meal_id} at {path}:{line_number}")
                    meal_ids.add(meal_id)
                    meal_dates.add(date_from_timestamp(meal["timestamp"]))
                except NutritionTrackerError as exc:
                    errors.append(f"{path}:{line_number}: {exc}")
        except NutritionTrackerError as exc:
            errors.append(str(exc))

    if not errors:
        for date_str in sorted(meal_dates):
            try:
                build_daily_summary(root, date_str)
            except NutritionTrackerError as exc:
                errors.append(f"Cannot rebuild day {date_str}: {exc}")

    return {
        "status": "error" if errors else "ok",
        "errors": errors,
        "warnings": warnings,
        "checked": {
            "meal_count": len(meal_ids),
            "day_count": len(meal_dates),
            "schema_count": len(SCHEMAS),
        },
    }
