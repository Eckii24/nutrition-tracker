import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app
from nutrition_tracker.schema_registry import load_schema
from tests.test_correction_service import add_sample_meal


def test_load_meal_schema(tmp_path: Path):
    schema = load_schema(tmp_path, "meal-entry.schema.json")
    assert schema["type"] == "object"


def test_doctor_valid_repo_returns_ok(initialized_root: Path, runner: CliRunner):
    add_sample_meal(initialized_root, runner)
    result = runner.invoke(app, ["doctor", "--path", str(initialized_root), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["status"] == "ok"


def test_doctor_malformed_meal_line_returns_error(initialized_root: Path, runner: CliRunner):
    meal_path = initialized_root / "data" / "meals" / "2026" / "2026-05-31.jsonl"
    meal_path.parent.mkdir(parents=True, exist_ok=True)
    meal_path.write_text("not-json\n", encoding="utf-8")

    result = runner.invoke(app, ["doctor", "--path", str(initialized_root), "--json"])
    assert result.exit_code != 0
    assert json.loads(result.stdout)["status"] == "error"


def test_doctor_unknown_correction_target_returns_error(initialized_root: Path, runner: CliRunner):
    correction_path = initialized_root / "data" / "corrections" / "2026" / "2026-05-31.jsonl"
    correction_path.parent.mkdir(parents=True, exist_ok=True)
    correction_path.write_text(
        json.dumps(
            {
                "id": "corr_1",
                "timestamp": "2026-05-31T09:00:00+02:00",
                "meal_id": "meal_missing",
                "operation": "cancel",
                "changes": {},
                "reason": "Bad target",
                "revision": 2,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", "--path", str(initialized_root), "--json"])
    assert result.exit_code != 0
    assert json.loads(result.stdout)["status"] == "error"
