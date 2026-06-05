import json

from typer.testing import CliRunner

from nutrition_tracker.application.goals import derive_goals
from nutrition_tracker.presentation.cli import app


def test_derive_goals_returns_core_targets():
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

    goals = derive_goals(settings)

    assert set(goals.keys()) >= {"kcal", "protein_g", "fat_g", "carbs_g", "fiber_g"}
    assert goals["protein_g"] > 0


def test_goals_derive_command_updates_settings(initialized_root, runner: CliRunner):
    result = runner.invoke(
        app,
        ["goals", "derive", "--path", str(initialized_root), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["daily"]["kcal"]["target"] > 0
