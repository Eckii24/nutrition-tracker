import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from nutrition_tracker.presentation.cli import app


def sample_meal() -> dict[str, Any]:
    return {
        "timestamp": "2026-05-31T08:00:00+02:00",
        "source": "manual",
        "foods": [
            {
                "label": "Skyr",
                "amount": 250,
                "unit": "g",
                "estimated": False,
                "confidence": "high",
            }
        ],
        "nutrition": {
            "kcal": 160,
            "protein_g": 27,
            "fat_g": 0.2,
            "carbs_g": 11,
            "fiber_g": 0,
        },
        "quality_signals": {
            "fruit_servings": 0,
            "vegetable_servings": 0,
            "highly_processed": False,
        },
    }


def test_meal_add_appends_jsonl(initialized_root: Path, runner: CliRunner):
    meal_file = initialized_root / "meal.json"
    meal_file.write_text(json.dumps(sample_meal()), encoding="utf-8")

    result = runner.invoke(
        app,
        ["meal", "add", "--path", str(initialized_root), "--file", str(meal_file), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert (initialized_root / "data" / "meals" / "2026" / "2026-05-31.jsonl").exists()

    payload = json.loads(result.stdout)
    assert payload["meal"]["id"] == "meal-20260531T080000plus0200-001"


def test_meal_add_rejects_negative_nutrition(initialized_root: Path, runner: CliRunner):
    meal = sample_meal()
    meal["nutrition"]["kcal"] = -1
    meal_file = initialized_root / "bad-meal.json"
    meal_file.write_text(json.dumps(meal), encoding="utf-8")

    result = runner.invoke(
        app,
        ["meal", "add", "--path", str(initialized_root), "--file", str(meal_file), "--json"],
    )
    assert result.exit_code != 0
    assert json.loads(result.stdout)["status"] == "error"
