import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app
from tests.test_meal_service import sample_meal


def add_meal_on(root: Path, runner: CliRunner, timestamp: str, kcal: int) -> None:
    meal = sample_meal()
    meal["timestamp"] = timestamp
    meal["nutrition"]["kcal"] = kcal
    meal_file = root / f"meal-{timestamp[:10]}.json"
    meal_file.write_text(json.dumps(meal), encoding="utf-8")
    result = runner.invoke(app, ["meal", "add", "--path", str(root), "--file", str(meal_file), "--json"])
    assert result.exit_code == 0, result.output


def test_weekly_summary_averages_tracked_days(initialized_root: Path, runner: CliRunner):
    add_meal_on(initialized_root, runner, "2026-05-25T08:00:00+02:00", 100)
    add_meal_on(initialized_root, runner, "2026-05-26T08:00:00+02:00", 300)

    result = runner.invoke(app, ["week", "show", "2026-W22", "--path", str(initialized_root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["days_tracked"] == 2
    assert payload["days_total"] == 7
    assert payload["coverage_pct"] == 28.6
    assert payload["averages"]["kcal"] == 200
    assert (initialized_root / "data" / "weekly" / "2026" / "2026-W22.summary.json").exists()
