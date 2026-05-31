from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from nutrition_tracker.constants import ALL_NUTRITION_METRICS, REQUIRED_NUTRITION_METRICS
from nutrition_tracker.errors import ValidationError

NUTRITION_PROPERTIES = {metric: {"type": "number", "minimum": 0} for metric in ALL_NUTRITION_METRICS}

FOOD_SCHEMA = {
    "type": "object",
    "required": ["label", "amount", "unit"],
    "properties": {
        "label": {"type": "string", "minLength": 1},
        "amount": {"type": "number", "minimum": 0},
        "unit": {"type": "string", "minLength": 1},
        "estimated": {"type": "boolean"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "additionalProperties": True,
}

QUALITY_SIGNALS_SCHEMA = {
    "type": "object",
    "properties": {
        "fruit_servings": {"type": "number", "minimum": 0},
        "vegetable_servings": {"type": "number", "minimum": 0},
        "highly_processed": {"type": "boolean"},
    },
    "additionalProperties": True,
}

MEAL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["id", "timestamp", "source", "foods", "nutrition"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "timestamp": {"type": "string", "format": "date-time"},
        "source": {"type": "string", "enum": ["manual", "text", "image", "image+text", "import"]},
        "source_context": {"type": "object", "additionalProperties": True},
        "foods": {"type": "array", "minItems": 1, "items": FOOD_SCHEMA},
        "nutrition": {
            "type": "object",
            "required": list(REQUIRED_NUTRITION_METRICS),
            "properties": NUTRITION_PROPERTIES,
            "additionalProperties": True,
        },
        "micros": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}},
        "quality_signals": QUALITY_SIGNALS_SCHEMA,
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
        "revision": {"type": "integer", "minimum": 1},
    },
    "additionalProperties": True,
}

CORRECTION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["id", "timestamp", "meal_id", "operation", "changes", "reason", "revision"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "timestamp": {"type": "string", "format": "date-time"},
        "meal_id": {"type": "string", "minLength": 1},
        "operation": {"type": "string", "enum": ["replace", "cancel", "annotate"]},
        "changes": {"type": "object", "additionalProperties": True},
        "reason": {"type": "string", "minLength": 1},
        "revision": {"type": "integer", "minimum": 1},
    },
    "additionalProperties": True,
}

SETTINGS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["profile", "goal_inputs", "goals", "defaults"],
    "properties": {
        "profile": {
            "type": "object",
            "required": [
                "sex",
                "date_of_birth",
                "height_cm",
                "weight_kg",
                "activity_level",
                "goal_mode",
            ],
            "properties": {
                "sex": {"type": "string"},
                "date_of_birth": {"type": "string", "format": "date"},
                "height_cm": {"type": "number", "exclusiveMinimum": 0},
                "weight_kg": {"type": "number", "exclusiveMinimum": 0},
                "activity_level": {"type": "string"},
                "goal_mode": {"type": "string"},
                "body_fat_percent": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
            },
            "additionalProperties": True,
        },
        "goal_inputs": {"type": "object", "additionalProperties": True},
        "goals": {
            "type": "object",
            "required": ["mode", "daily", "overrides"],
            "properties": {
                "mode": {"type": "string"},
                "daily": {"type": "object", "additionalProperties": True},
                "overrides": {"type": "object", "additionalProperties": True},
            },
            "additionalProperties": True,
        },
        "defaults": {"type": "object", "additionalProperties": True},
    },
    "additionalProperties": True,
}

SUMMARY_NUTRITION_SCHEMA = {
    "type": "object",
    "additionalProperties": {"type": ["number", "null"]},
}

DAILY_SUMMARY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["date", "meals", "totals", "goals", "delta", "progress_pct", "signals"],
    "properties": {
        "date": {"type": "string", "format": "date"},
        "meals": {"type": "array", "items": {"type": "object"}},
        "totals": SUMMARY_NUTRITION_SCHEMA,
        "goals": SUMMARY_NUTRITION_SCHEMA,
        "delta": SUMMARY_NUTRITION_SCHEMA,
        "progress_pct": SUMMARY_NUTRITION_SCHEMA,
        "signals": {"type": "object", "additionalProperties": True},
    },
    "additionalProperties": True,
}

WEEKLY_SUMMARY_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["week", "included_dates", "days_tracked", "days_total", "coverage_pct", "averages"],
    "properties": {
        "week": {"type": "string", "pattern": r"^\d{4}-W\d{2}$"},
        "included_dates": {"type": "array", "items": {"type": "string", "format": "date"}},
        "days_tracked": {"type": "integer", "minimum": 0},
        "days_total": {"type": "integer", "minimum": 1},
        "coverage_pct": {"type": "number", "minimum": 0},
        "averages": SUMMARY_NUTRITION_SCHEMA,
    },
    "additionalProperties": True,
}

SCHEMAS: dict[str, dict[str, Any]] = {
    "settings.schema.json": SETTINGS_SCHEMA,
    "meal-entry.schema.json": MEAL_SCHEMA,
    "correction-entry.schema.json": CORRECTION_SCHEMA,
    "daily-summary.schema.json": DAILY_SUMMARY_SCHEMA,
    "weekly-summary.schema.json": WEEKLY_SUMMARY_SCHEMA,
}


def package_schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas"


def load_schema(root: Path, name: str) -> dict[str, Any]:
    candidate = root / "schemas" / name
    if candidate.exists():
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid schema JSON in {candidate}: {exc.msg}") from exc

    repo_candidate = package_schema_dir() / name
    if repo_candidate.exists():
        try:
            return json.loads(repo_candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid schema JSON in {repo_candidate}: {exc.msg}") from exc

    if name in SCHEMAS:
        return deepcopy(SCHEMAS[name])
    raise ValidationError(f"Unknown schema: {name}")


def validate_payload(root: Path, schema_name: str, payload: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ModuleNotFoundError as exc:
        raise ValidationError("jsonschema dependency is not installed") from exc

    schema = load_schema(root, schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.path) or "payload"
        raise ValidationError(f"{schema_name} validation failed at {path}: {first.message}")


def write_default_schemas(root: Path) -> list[str]:
    written: list[str] = []
    schema_root = root / "schemas"
    schema_root.mkdir(parents=True, exist_ok=True)
    for name, schema in SCHEMAS.items():
        target = schema_root / name
        if not target.exists():
            target.write_text(
                json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            written.append(str(target.relative_to(root)))
    return written
