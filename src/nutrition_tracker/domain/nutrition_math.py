from __future__ import annotations

from datetime import date

from nutrition_tracker.domain.constants import ACTIVITY_FACTORS


def _round_target(value: float) -> int:
    return int(round(value))


def _age_on(date_of_birth: date, on_date: date) -> int:
    return (
        on_date.year
        - date_of_birth.year
        - ((on_date.month, on_date.day) < (date_of_birth.month, date_of_birth.day))
    )


def _bmr_mifflin_st_jeor(settings: dict, on_date: date) -> float:
    profile = settings["profile"]
    age = _age_on(date.fromisoformat(profile["date_of_birth"]), on_date)
    weight_kg = float(profile["weight_kg"])
    height_cm = float(profile["height_cm"])
    sex = profile["sex"].lower()
    sex_adjustment = 5 if sex == "male" else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + sex_adjustment


def derive_daily_targets(settings: dict, on_date: date | None = None) -> dict[str, int]:
    on_date = on_date or date.today()
    profile = settings["profile"]
    goal_inputs = settings.get("goal_inputs", {})
    weight_kg = float(profile["weight_kg"])
    activity_factor = ACTIVITY_FACTORS[profile["activity_level"]]

    bmr = _bmr_mifflin_st_jeor(settings, on_date)
    tdee = bmr * activity_factor
    weekly_weight_change_kg = float(goal_inputs.get("weekly_weight_change_kg", 0))
    kcal_adjustment = (weekly_weight_change_kg * 7700) / 7
    kcal_target = max(0.0, tdee + kcal_adjustment)

    protein_per_kg = float(goal_inputs.get("protein_g_per_kg", 1.8))
    fat_per_kg = float(goal_inputs.get("fat_g_per_kg", 0.8))
    fiber_per_1000kcal = float(goal_inputs.get("fiber_g_per_1000kcal", 14))

    protein_g = weight_kg * protein_per_kg
    fat_g = weight_kg * fat_per_kg
    fiber_g = kcal_target / 1000 * fiber_per_1000kcal
    remaining_kcal = max(0.0, kcal_target - (protein_g * 4 + fat_g * 9))
    carbs_g = remaining_kcal / 4

    return {
        "kcal": _round_target(kcal_target),
        "protein_g": _round_target(protein_g),
        "fat_g": _round_target(fat_g),
        "carbs_g": _round_target(carbs_g),
        "fiber_g": _round_target(fiber_g),
    }
