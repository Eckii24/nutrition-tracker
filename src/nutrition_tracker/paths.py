from pathlib import Path


def resolve_root(path: Path | str = ".") -> Path:
    return Path(path).expanduser().resolve()


def data_dir(root: Path) -> Path:
    return root / "data"


def schemas_dir(root: Path) -> Path:
    return root / "schemas"


def settings_path(root: Path) -> Path:
    return data_dir(root) / "settings.json"


def meals_dir(root: Path) -> Path:
    return data_dir(root) / "meals"


def corrections_dir(root: Path) -> Path:
    return data_dir(root) / "corrections"


def daily_dir(root: Path) -> Path:
    return data_dir(root) / "daily"


def weekly_dir(root: Path) -> Path:
    return data_dir(root) / "weekly"


def meal_file(root: Path, date_str: str) -> Path:
    year = date_str[:4]
    return meals_dir(root) / year / f"{date_str}.jsonl"


def correction_file(root: Path, date_str: str) -> Path:
    year = date_str[:4]
    return corrections_dir(root) / year / f"{date_str}.jsonl"


def daily_summary_file(root: Path, date_str: str) -> Path:
    year = date_str[:4]
    return daily_dir(root) / year / f"{date_str}.summary.json"


def weekly_summary_file(root: Path, iso_week: str) -> Path:
    year = iso_week[:4]
    return weekly_dir(root) / year / f"{iso_week}.summary.json"
