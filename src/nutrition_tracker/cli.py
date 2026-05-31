import json
from pathlib import Path
from typing import Any

import typer

from nutrition_tracker.errors import NutritionTrackerError
from nutrition_tracker.paths import resolve_root
from nutrition_tracker.services.correction_service import add_correction
from nutrition_tracker.services.daily_service import build_daily_summary, list_meals
from nutrition_tracker.services.doctor_service import run_doctor
from nutrition_tracker.services.goal_service import derive_and_save_goals
from nutrition_tracker.services.init_service import init_project
from nutrition_tracker.services.meal_service import add_meal
from nutrition_tracker.services.weekly_service import build_weekly_summary

app = typer.Typer(help="Nutrition tracker CLI")
goals_app = typer.Typer(help="Goal commands")
meal_app = typer.Typer(help="Meal commands")
day_app = typer.Typer(help="Daily summary commands")
week_app = typer.Typer(help="Weekly summary commands")

app.add_typer(goals_app, name="goals")
app.add_typer(meal_app, name="meal")
app.add_typer(day_app, name="day")
app.add_typer(week_app, name="week")


def _json_default(value: Any) -> str:
    return str(value)


def _emit(payload: dict[str, Any], json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, default=_json_default))
    else:
        typer.echo(payload.get("status", "ok"))


def _handle_error(exc: Exception, json_output: bool) -> None:
    payload = {"status": "error", "error": str(exc)}
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        typer.echo(str(exc), err=True)
    raise typer.Exit(1)


@app.callback()
def main() -> None:
    """Deterministic local backend for file-based nutrition tracking."""


@app.command("init")
def init_command(
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(init_project(resolve_root(path)), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@goals_app.command("derive")
def goals_derive_command(
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(derive_and_save_goals(resolve_root(path)), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@meal_app.command("add")
def meal_add_command(
    file: Path = typer.Option(..., "--file", exists=True, dir_okay=False, resolve_path=True),
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(add_meal(resolve_root(path), file), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@meal_app.command("correct")
def meal_correct_command(
    file: Path = typer.Option(..., "--file", exists=True, dir_okay=False, resolve_path=True),
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(add_correction(resolve_root(path), file), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@meal_app.command("list")
def meal_list_command(
    date: str = typer.Argument(..., help="Date as YYYY-MM-DD"),
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(list_meals(resolve_root(path), date), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@day_app.command("show")
def day_show_command(
    date: str = typer.Argument(..., help="Date as YYYY-MM-DD"),
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(build_daily_summary(resolve_root(path), date), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@week_app.command("show")
def week_show_command(
    week: str = typer.Argument(..., help="ISO week as YYYY-Www"),
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(build_weekly_summary(resolve_root(path), week), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@app.command("doctor")
def doctor_command(
    path: Path = typer.Option(Path("."), "--path", file_okay=False, resolve_path=True),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        payload = run_doctor(resolve_root(path))
        _emit(payload, json_output)
        if payload["status"] != "ok":
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except NutritionTrackerError as exc:
        _handle_error(exc, json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


if __name__ == "__main__":
    app()
