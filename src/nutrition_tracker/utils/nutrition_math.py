from datetime import date
from typing import Any

from nutrition_tracker.constants import ACTIVITY_FACTORS


def calculate_age(date_of_birth: str, on_date: date | None = None) -> int:
    today = on_date or date.today()
    year, month, day = map(int, date_of_birth.split("-"))
    born = date(year, month, day)
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def mifflin_st_jeor(profile: dict[str, Any], on_date: date | None = None) -> float:
    weight = float(profile["weight_kg"])
    height = float(profile["height_cm"])
    age = calculate_age(profile["date_of_birth"], on_date=on_date)
    sex = str(profile.get("sex", "")).lower()
    sex_adjustment = 5 if sex == "male" else -161 if sex == "female" else -78
    return 10 * weight + 6.25 * height - 5 * age + sex_adjustment


def derive_daily_targets(settings: dict[str, Any], on_date: date | None = None) -> dict[str, int]:
    profile = settings["profile"]
    inputs = settings["goal_inputs"]
    bmr = mifflin_st_jeor(profile, on_date=on_date)
    factor = ACTIVITY_FACTORS.get(str(profile.get("activity_level", "moderate")), 1.55)
    weekly_change = float(inputs.get("weekly_weight_change_kg", 0))
    kcal = round(bmr * factor + (weekly_change * 7700 / 7))

    weight = float(profile["weight_kg"])
    protein_g = round(weight * float(inputs.get("protein_g_per_kg", 1.8)))
    fat_g = round(weight * float(inputs.get("fat_g_per_kg", 0.8)))
    remaining_kcal = max(0, kcal - protein_g * 4 - fat_g * 9)
    carbs_g = round(remaining_kcal / 4)
    fiber_g = round(kcal / 1000 * float(inputs.get("fiber_g_per_1000kcal", 14)))

    return {
        "kcal": max(0, kcal),
        "protein_g": max(0, protein_g),
        "fat_g": max(0, fat_g),
        "carbs_g": max(0, carbs_g),
        "fiber_g": max(0, fiber_g),
    }
