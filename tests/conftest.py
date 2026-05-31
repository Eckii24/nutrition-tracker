from pathlib import Path

import pytest
from typer.testing import CliRunner

from nutrition_tracker.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def initialized_root(tmp_path: Path, runner: CliRunner) -> Path:
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    return tmp_path
