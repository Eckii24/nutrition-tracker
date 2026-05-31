import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app
from tests.test_meal_service import sample_meal


def add_sample_meal(root: Path, runner: CliRunner) -> str:
    meal_file = root / "meal.json"
    meal_file.write_text(json.dumps(sample_meal()), encoding="utf-8")
    result = runner.invoke(app, ["meal", "add", "--path", str(root), "--file", str(meal_file), "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)["meal"]["id"]


def test_correction_against_existing_meal_succeeds(initialized_root: Path, runner: CliRunner):
    meal_id = add_sample_meal(initialized_root, runner)
    correction = {
        "timestamp": "2026-05-31T09:00:00+02:00",
        "meal_id": meal_id,
        "operation": "replace",
        "changes": {
            "nutrition": {"kcal": 180, "protein_g": 30, "fat_g": 0.3, "carbs_g": 12, "fiber_g": 0}
        },
        "reason": "User corrected serving",
    }
    correction_file = initialized_root / "correction.json"
    correction_file.write_text(json.dumps(correction), encoding="utf-8")

    result = runner.invoke(
        app,
        ["meal", "correct", "--path", str(initialized_root), "--file", str(correction_file), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert (initialized_root / "data" / "corrections" / "2026" / "2026-05-31.jsonl").exists()


def test_correction_against_unknown_meal_fails(initialized_root: Path, runner: CliRunner):
    correction = {
        "timestamp": "2026-05-31T09:00:00+02:00",
        "meal_id": "meal_missing",
        "operation": "cancel",
        "changes": {},
        "reason": "Wrong entry",
    }
    correction_file = initialized_root / "bad-correction.json"
    correction_file.write_text(json.dumps(correction), encoding="utf-8")

    result = runner.invoke(
        app,
        ["meal", "correct", "--path", str(initialized_root), "--file", str(correction_file), "--json"],
    )
    assert result.exit_code != 0
    assert json.loads(result.stdout)["status"] == "error"
