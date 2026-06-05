from __future__ import annotations

from pathlib import Path

from nutrition_tracker.application import daily as daily_use_cases
from nutrition_tracker.application import goals as goal_use_cases
from nutrition_tracker.infrastructure.schema_store import load_schema
from nutrition_tracker.presentation.cli import app as cli_app


def test_root_package_only_exposes_the_four_top_level_layers() -> None:
    package_root = Path(__file__).resolve().parents[1] / "src" / "nutrition_tracker"
    top_level_dirs = sorted(
        path.name
        for path in package_root.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    )

    assert top_level_dirs == ["application", "domain", "infrastructure", "presentation"]
    assert not (package_root / "cli.py").exists()
    assert not (package_root / "constants.py").exists()
    assert not (package_root / "errors.py").exists()
    assert not (package_root / "jsonio.py").exists()
    assert not (package_root / "paths.py").exists()
    assert not (package_root / "schema_registry.py").exists()
    assert not (package_root / "models").exists()
    assert not (package_root / "repositories").exists()
    assert not (package_root / "services").exists()
    assert not (package_root / "utils").exists()


def test_cli_entrypoint_lives_in_presentation_layer() -> None:
    assert cli_app.info.name == "nutrition"


def test_application_use_cases_are_cli_agnostic() -> None:
    package_root = Path(__file__).resolve().parents[1]
    schema = load_schema(package_root, "meal-entry.schema.json")
    assert schema["type"] == "object"

    settings = {
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
    goals = goal_use_cases.derive_goals(settings)
    totals = daily_use_cases.calculate_totals(
        [{"nutrition": {"kcal": 620, "protein_g": 48, "fat_g": 14, "carbs_g": 71, "fiber_g": 4}}]
    )

    assert goals["kcal"] > 0
    assert totals == {"kcal": 620, "protein_g": 48, "fat_g": 14, "carbs_g": 71, "fiber_g": 4}
