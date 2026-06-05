import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app
from nutrition_tracker.schema_registry import load_schema
from tests.test_daily_service import add_sample_meal


def test_load_meal_schema(tmp_path: Path):
    schema = load_schema(tmp_path, "meal-entry.schema.json")
    assert schema["type"] == "object"


def test_doctor_valid_repo_returns_ok(initialized_root: Path, runner: CliRunner):
    add_sample_meal(initialized_root, runner)
    result = runner.invoke(app, ["doctor", "--path", str(initialized_root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["checked"]["schema_count"] == 4


def test_doctor_malformed_meal_line_returns_error(initialized_root: Path, runner: CliRunner):
    meal_path = initialized_root / "data" / "meals" / "2026" / "2026-05-31.jsonl"
    meal_path.parent.mkdir(parents=True, exist_ok=True)
    meal_path.write_text("not-json\n", encoding="utf-8")

    result = runner.invoke(app, ["doctor", "--path", str(initialized_root), "--json"])
    assert result.exit_code != 0
    assert json.loads(result.stdout)["status"] == "error"
