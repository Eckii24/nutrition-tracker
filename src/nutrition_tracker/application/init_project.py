from __future__ import annotations

from pathlib import Path
from typing import Any

from nutrition_tracker.application.goals import derive_goal_entries
from nutrition_tracker.infrastructure.project_paths import (
    daily_dir,
    data_dir,
    meals_dir,
    settings_path,
    weekly_dir,
)
from nutrition_tracker.infrastructure.schema_store import write_default_schemas
from nutrition_tracker.infrastructure.settings_repository import default_settings, save_settings


def init_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    created: list[str] = []
    for directory in [data_dir(root), meals_dir(root), daily_dir(root), weekly_dir(root)]:
        existed = directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        if not existed:
            created.append(str(directory.relative_to(root)))

    settings_file = settings_path(root)
    if not settings_file.exists():
        settings = default_settings()
        settings["goals"]["daily"] = derive_goal_entries(settings)
        save_settings(root, settings)
        created.append(str(settings_file.relative_to(root)))

    created.extend(write_default_schemas(root))
    return {"status": "ok", "root": str(root), "created": created}
