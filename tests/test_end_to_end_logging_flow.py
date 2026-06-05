import json
from pathlib import Path

from nutrition_tracker.presentation.cli import app
from tests.test_meal_service import sample_meal


def test_end_to_end_append_day_week_flow(tmp_path: Path, runner):
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output

    meal_file = tmp_path / "meal.json"
    meal_file.write_text(json.dumps(sample_meal()), encoding="utf-8")
    result = runner.invoke(
        app,
        ["meal", "add", "--path", str(tmp_path), "--file", str(meal_file), "--json"],
    )
    assert result.exit_code == 0, result.output
    meal_id = json.loads(result.stdout)["meal"]["id"]

    result = runner.invoke(
        app,
        ["meal", "list", "2026-05-31", "--path", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0, result.output
    listed = json.loads(result.stdout)
    assert listed["meals"][0]["id"] == meal_id
    assert listed["meals"][0]["nutrition"]["kcal"] == 160

    result = runner.invoke(
        app,
        ["day", "show", "2026-05-31", "--path", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["totals"]["kcal"] == 160

    result = runner.invoke(
        app,
        ["week", "show", "2026-W22", "--path", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["averages"]["kcal"] == 160
