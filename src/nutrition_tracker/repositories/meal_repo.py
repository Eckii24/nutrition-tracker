from pathlib import Path
from typing import Any

from nutrition_tracker.jsonio import append_jsonl, read_jsonl
from nutrition_tracker.paths import meal_file, meals_dir
from nutrition_tracker.utils.dates import date_from_timestamp


def append_meal(root: Path, meal: dict[str, Any]) -> Path:
    date_str = date_from_timestamp(meal["timestamp"])
    target = meal_file(root, date_str)
    append_jsonl(target, meal)
    return target


def read_meals_for_date(root: Path, date_str: str) -> list[dict[str, Any]]:
    return read_jsonl(meal_file(root, date_str))


def iter_meal_files(root: Path) -> list[Path]:
    base = meals_dir(root)
    if not base.exists():
        return []
    return sorted(base.glob("*/*.jsonl"))


def iter_all_meals(root: Path) -> list[dict[str, Any]]:
    meals: list[dict[str, Any]] = []
    for path in iter_meal_files(root):
        meals.extend(read_jsonl(path))
    return meals


def meal_ids(root: Path) -> list[str]:
    return [meal["id"] for meal in iter_all_meals(root) if "id" in meal]


def meal_exists(root: Path, meal_id: str) -> bool:
    return meal_id in set(meal_ids(root))
