from __future__ import annotations

from pathlib import Path

from nutrition_tracker.domain.dates import date_from_timestamp
from nutrition_tracker.domain.entities import Meal
from nutrition_tracker.infrastructure.json_store import append_jsonl, read_jsonl
from nutrition_tracker.infrastructure.project_paths import meal_file, meals_dir


def append_meal(root: Path, meal: Meal) -> Path:
    date_str = date_from_timestamp(meal["timestamp"])
    target = meal_file(root, date_str)
    append_jsonl(target, meal)
    return target


def read_meals_for_date(root: Path, date_str: str) -> list[Meal]:
    return read_jsonl(meal_file(root, date_str))


def iter_meal_files(root: Path) -> list[Path]:
    base = meals_dir(root)
    if not base.exists():
        return []
    return sorted(base.glob("*/*.jsonl"))


def iter_all_meals(root: Path) -> list[Meal]:
    meals: list[Meal] = []
    for path in iter_meal_files(root):
        meals.extend(read_jsonl(path))
    return meals


def meal_ids(root: Path) -> list[str]:
    return [meal["id"] for meal in iter_all_meals(root) if "id" in meal]


def meal_exists(root: Path, meal_id: str) -> bool:
    return meal_id in set(meal_ids(root))
