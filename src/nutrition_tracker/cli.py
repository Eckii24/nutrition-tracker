import json
from pathlib import Path
from typing import Any

import typer

from nutrition_tracker.errors import NutritionTrackerError
from nutrition_tracker.paths import resolve_root
from nutrition_tracker.services.daily_service import build_daily_summary, list_meals
from nutrition_tracker.services.doctor_service import run_doctor
from nutrition_tracker.services.goal_service import derive_and_save_goals
from nutrition_tracker.services.init_service import init_project
from nutrition_tracker.services.meal_service import add_meal
from nutrition_tracker.services.weekly_service import build_weekly_summary

app = typer.Typer(help="Deterministic local backend for file-based nutrition tracking.")
goals_app = typer.Typer(help="Derive and inspect daily nutrition goals.")
meal_app = typer.Typer(help="Write and inspect meal events.")
day_app = typer.Typer(help="Build deterministic daily summaries from stored events.")
week_app = typer.Typer(help="Build deterministic weekly summaries from stored events.")

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


@app.command("init", help="Create the directory layout, schemas, and default settings for a nutrition project.")
def init_command(
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root where data/ and schemas/ should be created.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(init_project(resolve_root(path)), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@goals_app.command("derive", help="Derive daily macro targets from data/settings.json and write goal snapshots.")
def goals_derive_command(
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root containing data/settings.json.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(derive_and_save_goals(resolve_root(path)), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@meal_app.command("add", help="Validate one structured meal payload and append it to the meal event log.")
def meal_add_command(
    file: Path = typer.Option(
        ...,
        "--file",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="Structured meal payload JSON file.",
    ),
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root containing data/ and schemas/.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(add_meal(resolve_root(path), file), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@meal_app.command("list", help="List stored meals for one day.")
def meal_list_command(
    date: str = typer.Argument(..., help="Date as YYYY-MM-DD"),
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root containing meal logs.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(list_meals(resolve_root(path), date), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@day_app.command("show", help="Build and emit one daily summary from stored meals.")
def day_show_command(
    date: str = typer.Argument(..., help="Date as YYYY-MM-DD"),
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root containing meal and settings data.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(build_daily_summary(resolve_root(path), date), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@week_app.command("show", help="Build and emit one weekly summary from stored daily data.")
def week_show_command(
    week: str = typer.Argument(..., help="ISO week as YYYY-Www"),
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root containing meal, daily, and settings data.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON"),
) -> None:
    try:
        _emit(build_weekly_summary(resolve_root(path), week), json_output)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        _handle_error(exc, json_output)


@app.command("doctor", help="Validate the repo structure and check stored data against the JSON schemas.")
def doctor_command(
    path: Path = typer.Option(
        Path("."),
        "--path",
        file_okay=False,
        resolve_path=True,
        help="Project root to validate.",
    ),
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
