import json
from pathlib import Path

from typer.testing import CliRunner

from nutrition_tracker.cli import app


def test_cli_shows_help(runner: CliRunner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "nutrition" in result.output.lower()


def test_init_creates_required_structure(tmp_path: Path, runner: CliRunner):
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output

    assert (tmp_path / "data" / "settings.json").exists()
    assert (tmp_path / "data" / "meals").exists()
    assert (tmp_path / "data" / "corrections").exists()
    assert (tmp_path / "data" / "daily").exists()
    assert (tmp_path / "data" / "weekly").exists()
    assert (tmp_path / "schemas" / "meal-entry.schema.json").exists()

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
