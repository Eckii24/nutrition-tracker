from pathlib import Path
from typing import Any

from nutrition_tracker.jsonio import append_jsonl, read_jsonl
from nutrition_tracker.paths import correction_file, corrections_dir
from nutrition_tracker.utils.dates import date_from_timestamp


def append_correction(root: Path, correction: dict[str, Any]) -> Path:
    date_str = date_from_timestamp(correction["timestamp"])
    target = correction_file(root, date_str)
    append_jsonl(target, correction)
    return target


def read_corrections_for_date(root: Path, date_str: str) -> list[dict[str, Any]]:
    return read_jsonl(correction_file(root, date_str))


def iter_correction_files(root: Path) -> list[Path]:
    base = corrections_dir(root)
    if not base.exists():
        return []
    return sorted(base.glob("*/*.jsonl"))


def iter_all_corrections(root: Path) -> list[dict[str, Any]]:
    corrections: list[dict[str, Any]] = []
    for path in iter_correction_files(root):
        corrections.extend(read_jsonl(path))
    return corrections
