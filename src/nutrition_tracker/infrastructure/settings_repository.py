from __future__ import annotations

from pathlib import Path

from nutrition_tracker.domain.entities import Settings
from nutrition_tracker.infrastructure.json_store import load_json_file, write_json_file
from nutrition_tracker.infrastructure.project_paths import settings_path
from nutrition_tracker.infrastructure.schema_store import validate_payload


def default_settings() -> Settings:
    return {
        "profile": {
            "sex": "male",
            "date_of_birth": "1990-01-01",
            "height_cm": 183,
            "weight_kg": 86,
            "activity_level": "moderate",
            "goal_mode": "maintain",
            "body_fat_percent": None,
        },
        "goal_inputs": {
            "weekly_weight_change_kg": 0,
            "protein_g_per_kg": 1.8,
            "fat_g_per_kg": 0.8,
            "fiber_g_per_1000kcal": 14,
        },
        "goals": {"mode": "derived_with_overrides", "daily": {}, "overrides": {}},
        "defaults": {"timezone": "Europe/Berlin", "currency": "EUR"},
    }


def load_settings(root: Path) -> Settings:
    settings = load_json_file(settings_path(root))
    validate_payload(root, "settings.schema.json", settings)
    return settings


def save_settings(root: Path, settings: Settings) -> None:
    validate_payload(root, "settings.schema.json", settings)
    write_json_file(settings_path(root), settings)
