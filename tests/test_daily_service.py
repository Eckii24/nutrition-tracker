import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.presentation.cli import app
from tests.test_meal_service import sample_meal


def add_sample_meal(root: Path, runner: CliRunner) -> str:
    meal_file = root / "meal.json"
    meal_file.write_text(json.dumps(sample_meal()), encoding="utf-8")
    result = runner.invoke(
        app,
        ["meal", "add", "--path", str(root), "--file", str(meal_file), "--json"],
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)["meal"]["id"]


def test_daily_summary_aggregates_meals_and_writes_file(initialized_root: Path, runner: CliRunner):
    add_sample_meal(initialized_root, runner)

    result = runner.invoke(
        app,
        [
            "day",
            "show",
            "2026-05-31",
            "--path",
            str(initialized_root),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["totals"]["kcal"] == 160
    assert payload["signals"]["meal_count"] == 1
    assert (initialized_root / "data" / "daily" / "2026" / "2026-05-31.summary.json").exists()


def test_daily_summary_uses_stored_meals_without_projection(
    initialized_root: Path, runner: CliRunner
):
    meal_id = add_sample_meal(initialized_root, runner)

    result = runner.invoke(
        app,
        [
            "meal",
            "list",
            "2026-05-31",
            "--path",
            str(initialized_root),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    listed = json.loads(result.stdout)
    assert listed["meals"][0]["id"] == meal_id
    assert listed["meals"][0]["nutrition"]["kcal"] == 160

    result = runner.invoke(
        app,
        [
            "day",
            "show",
            "2026-05-31",
            "--path",
            str(initialized_root),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["totals"]["kcal"] == 160
    assert payload["signals"]["meal_count"] == 1
