from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from nutrition_tracker.domain.errors import ValidationError


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc.msg}") from exc
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing JSON file: {path}") from exc


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for _line_number, payload in iter_jsonl_with_line_numbers(path):
        rows.append(payload)
    return rows


def iter_jsonl_with_line_numbers(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Invalid JSONL in {path}:{line_number}: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValidationError(f"Invalid JSONL in {path}:{line_number}: expected object")
            yield line_number, payload
