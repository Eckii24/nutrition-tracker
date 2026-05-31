import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app
from tests.test_meal_service import sample_meal


def test_end_to_end_append_correct_day_week_flow(tmp_path: Path, runner: CliRunner):
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output

    meal_file = tmp_path / "meal.json"
    meal_file.write_text(json.dumps(sample_meal()), encoding="utf-8")
    result = runner.invoke(app, ["meal", "add", "--path", str(tmp_path), "--file", str(meal_file), "--json"])
    assert result.exit_code == 0, result.output
    meal_id = json.loads(result.stdout)["meal"]["id"]

    result = runner.invoke(app, ["meal", "list", "2026-05-31", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    listed = json.loads(result.stdout)
    assert listed["meals"][0]["id"] == meal_id

    correction = {
        "timestamp": "2026-05-31T09:00:00+02:00",
        "meal_id": meal_id,
        "operation": "replace",
        "changes": {
            "nutrition": {"kcal": 180, "protein_g": 30, "fat_g": 0.3, "carbs_g": 12, "fiber_g": 0}
        },
        "reason": "Corrected serving",
    }
    correction_file = tmp_path / "correction.json"
    correction_file.write_text(json.dumps(correction), encoding="utf-8")
    result = runner.invoke(
        app, ["meal", "correct", "--path", str(tmp_path), "--file", str(correction_file), "--json"]
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["day", "show", "2026-05-31", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["totals"]["kcal"] == 180

    result = runner.invoke(app, ["week", "show", "2026-W22", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["averages"]["kcal"] == 180
