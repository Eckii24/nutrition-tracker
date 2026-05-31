import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app
from tests.test_correction_service import add_sample_meal


def write_correction(root: Path, runner: CliRunner, correction: dict) -> None:
    correction_file = root / f"correction-{correction['operation']}.json"
    correction_file.write_text(json.dumps(correction), encoding="utf-8")
    result = runner.invoke(
        app, ["meal", "correct", "--path", str(root), "--file", str(correction_file), "--json"]
    )
    assert result.exit_code == 0, result.output


def test_daily_summary_aggregates_meals_and_writes_file(initialized_root: Path, runner: CliRunner):
    add_sample_meal(initialized_root, runner)

    result = runner.invoke(app, ["day", "show", "2026-05-31", "--path", str(initialized_root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["totals"]["kcal"] == 160
    assert payload["signals"]["meal_count"] == 1
    assert (initialized_root / "data" / "daily" / "2026" / "2026-05-31.summary.json").exists()


def test_daily_summary_applies_replace_and_cancel(initialized_root: Path, runner: CliRunner):
    meal_id = add_sample_meal(initialized_root, runner)
    write_correction(
        initialized_root,
        runner,
        {
            "timestamp": "2026-05-31T09:00:00+02:00",
            "meal_id": meal_id,
            "operation": "replace",
            "changes": {
                "nutrition": {"kcal": 180, "protein_g": 30, "fat_g": 0.3, "carbs_g": 12, "fiber_g": 0}
            },
            "reason": "Corrected nutrition",
        },
    )
    result = runner.invoke(app, ["day", "show", "2026-05-31", "--path", str(initialized_root), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["totals"]["kcal"] == 180

    write_correction(
        initialized_root,
        runner,
        {
            "timestamp": "2026-05-31T10:00:00+02:00",
            "meal_id": meal_id,
            "operation": "cancel",
            "changes": {},
            "reason": "Wrong meal",
        },
    )
    result = runner.invoke(app, ["day", "show", "2026-05-31", "--path", str(initialized_root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["totals"]["kcal"] == 0
    assert payload["signals"]["meal_count"] == 0
