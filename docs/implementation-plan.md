# Nutrition Tracker MVP Implementation Plan

> **Historical note:** This plan documents the original implementation path. The current repo no longer uses a separate correction-event model; direct structured file edits in the private app repo replaced it.

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a deterministic local CLI for the nutrition tracker MVP that persists file-based nutrition events, derives goals from `settings.json`, computes daily and weekly summaries, and exposes JSON-first commands for the Hermes skill layer.

**Architecture:** Use a small Python package with a thin CLI layer over pure domain services. Keep append-only event files as source of truth, validate all payloads against JSON Schema, and rebuild derived daily/weekly summaries deterministically from events plus corrections.

**Tech Stack:** Python 3.12+, `typer`, `pydantic`, `jsonschema`, `pytest`, `ruff`

---

## 0. Decisions locked before implementation

### Chosen language: Python

**Recommendation:** Python for the CLI.

**Why this is the right call here:**
- strongest leverage for JSON/data processing with low ceremony
- good fit for schema validation, file I/O, date math, and tests
- easy subprocess integration from Hermes
- lower friction than TypeScript for a local deterministic backend with no frontend
- better path if later we want optional nutrition lookup helpers, quick scripts, or notebook-style debugging

**Why not TypeScript for MVP:**
- worse payoff without a web UI
- more build/runtime packaging friction for a local CLI
- no clear product advantage for this specific phase

### Packaging stance
Keep it simple:
- one installable Python package
- one console script: `nutrition`
- no database
- no network dependency in MVP core

---

## 1. Target repository layout

```text
nutrition-tracker/
  docs/
    PRD.md
    spec.md
    implementation-plan.md
  data/
    .gitkeep
  schemas/
    settings.schema.json
    meal-entry.schema.json
    correction-entry.schema.json
    daily-summary.schema.json
    weekly-summary.schema.json
  src/
    nutrition_tracker/
      __init__.py
      cli.py
      paths.py
      constants.py
      errors.py
      jsonio.py
      clock.py
      schema_registry.py
      models/
        __init__.py
        enums.py
        settings.py
        meal.py
        correction.py
        summary.py
      services/
        __init__.py
        init_service.py
        goal_service.py
        meal_service.py
        correction_service.py
        daily_service.py
        weekly_service.py
        rebuild_service.py
        doctor_service.py
      repositories/
        __init__.py
        settings_repo.py
        meal_repo.py
        correction_repo.py
        summary_repo.py
      utils/
        __init__.py
        dates.py
        ids.py
        nutrition_math.py
  tests/
    conftest.py
    fixtures/
      settings.valid.json
      meal.valid.json
      correction.valid.json
    test_cli_init.py
    test_goal_service.py
    test_meal_service.py
    test_correction_service.py
    test_daily_service.py
    test_weekly_service.py
    test_doctor_service.py
    test_end_to_end_logging_flow.py
  pyproject.toml
  README.md
```

---

## 2. Build order

Implement in this order:
1. package scaffold and toolchain
2. path/bootstrap/init flow
3. schema files and validation layer
4. settings model + goal derivation
5. meal append flow
6. correction append flow
7. daily rebuild
8. weekly rebuild
9. CLI commands
10. doctor/integrity checks
11. end-to-end tests

Do not start with image parsing or Hermes skill glue. The CLI must stand on its own first.

---

## 3. Core domain rules that implementation must preserve

1. `data/settings.json` is required after init.
2. Meals are append-only JSONL events.
3. Corrections are append-only JSONL events.
4. Effective meal state is materialized from base meal + later corrections.
5. Daily summaries are deterministic rebuilds.
6. Weekly summaries are derived from daily summaries.
7. CLI returns JSON on all read/write commands when `--json` is set.
8. CLI does not produce coaching prose.
9. Images are never stored by the CLI.
10. Missing optional nutrition fields stay missing; do not invent values.

---

## 4. Task-by-task implementation plan

### Task 1: Create Python package scaffold

**Objective:** Create the minimal installable Python CLI package and test tooling.

**Files:**
- Create: `pyproject.toml`
- Create: `src/nutrition_tracker/__init__.py`
- Create: `src/nutrition_tracker/cli.py`
- Create: `tests/conftest.py`
- Modify: `README.md`

**Step 1: Write failing test**

Create `tests/test_cli_init.py` with:

```python
from typer.testing import CliRunner
from nutrition_tracker.cli import app

runner = CliRunner()


def test_cli_shows_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "nutrition" in result.output.lower()
```

**Step 2: Run test to verify failure**

Run:
```bash
pytest tests/test_cli_init.py -v
```

Expected: FAIL because package/app does not exist yet.

**Step 3: Write minimal implementation**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "nutrition-tracker"
version = "0.1.0"
description = "Deterministic local CLI backend for a file-based nutrition tracker"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "typer>=0.12",
  "pydantic>=2.7",
  "jsonschema>=4.22",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "ruff>=0.5",
]

[project.scripts]
nutrition = "nutrition_tracker.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
```

Create `src/nutrition_tracker/cli.py`:

```python
import typer

app = typer.Typer(help="Nutrition tracker CLI")


@app.callback()
def main() -> None:
    return None
```

Create empty `__init__.py`.

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_cli_init.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml src/nutrition_tracker tests README.md
git commit -m "build: scaffold python cli package"
```

---

### Task 2: Add `nutrition init` and path bootstrap

**Objective:** Create the repository data skeleton and default `settings.json` template.

**Files:**
- Create: `src/nutrition_tracker/paths.py`
- Create: `src/nutrition_tracker/services/init_service.py`
- Modify: `src/nutrition_tracker/cli.py`
- Test: `tests/test_cli_init.py`

**Step 1: Write failing test**

Add to `tests/test_cli_init.py`:

```python
import json
from pathlib import Path
from typer.testing import CliRunner
from nutrition_tracker.cli import app

runner = CliRunner()


def test_init_creates_required_structure(tmp_path: Path):
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0

    assert (tmp_path / "data" / "settings.json").exists()
    assert (tmp_path / "schemas").exists()

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
```
```

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_cli_init.py::test_init_creates_required_structure -v
```

Expected: FAIL because command does not exist.

**Step 3: Write minimal implementation**

Implement:
- `paths.py` with helper functions for root/data/schema paths
- `init_service.py` creating:
  - `data/`
  - `data/meals/`
  - `data/corrections/`
  - `data/daily/`
  - `data/weekly/`
  - `schemas/`
  - default `data/settings.json`
- `cli.py` command:

```python
@app.command("init")
def init_command(path: Path = typer.Option(Path("."), exists=True, file_okay=False), json_output: bool = typer.Option(False, "--json")) -> None:
    ...
```

Return JSON shape:

```json
{
  "status": "ok",
  "root": "/abs/path",
  "created": ["data/settings.json", "schemas"]
}
```

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_cli_init.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_cli_init.py
git commit -m "feat: add project init command"
```

---

### Task 3: Add JSON schema files and validator registry

**Objective:** Define all persisted payload schemas and central validation entry points.

**Files:**
- Create: `schemas/settings.schema.json`
- Create: `schemas/meal-entry.schema.json`
- Create: `schemas/correction-entry.schema.json`
- Create: `schemas/daily-summary.schema.json`
- Create: `schemas/weekly-summary.schema.json`
- Create: `src/nutrition_tracker/schema_registry.py`
- Create: `src/nutrition_tracker/errors.py`
- Test: `tests/test_doctor_service.py`

**Step 1: Write failing test**

Create `tests/test_doctor_service.py` with:

```python
from pathlib import Path
from nutrition_tracker.schema_registry import load_schema


def test_load_meal_schema(tmp_path: Path):
    schema = load_schema(tmp_path, "meal-entry.schema.json")
    assert schema["type"] == "object"
```

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_doctor_service.py::test_load_meal_schema -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Define schemas with explicit required fields and optional extended metrics.
Meal schema must support:
- required: `id`, `timestamp`, `source`, `foods`, `nutrition`
- nutrition required core fields: `kcal`, `protein_g`, `fat_g`, `carbs_g`
- optional extended fields:
  - `fiber_g`
  - `saturated_fat_g`
  - `sugar_g`
  - `added_sugar_g`
  - `sodium_mg`
  - `cholesterol_mg`
  - `trans_fat_g`
  - `polyunsaturated_fat_g`
  - `monounsaturated_fat_g`
  - `caffeine_mg`
  - `alcohol_g`
  - `vitamin_d_ug`
  - `calcium_mg`

Implement `load_schema(root, name)` and `validate_payload(root, schema_name, payload)`.

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_doctor_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add schemas src/nutrition_tracker/schema_registry.py src/nutrition_tracker/errors.py tests/test_doctor_service.py
git commit -m "feat: add storage schemas and validation registry"
```

---

### Task 4: Implement settings model and goal derivation

**Objective:** Load `settings.json`, derive default targets, and preserve overrides.

**Files:**
- Create: `src/nutrition_tracker/models/settings.py`
- Create: `src/nutrition_tracker/repositories/settings_repo.py`
- Create: `src/nutrition_tracker/services/goal_service.py`
- Create: `src/nutrition_tracker/utils/nutrition_math.py`
- Test: `tests/test_goal_service.py`

**Step 1: Write failing test**

Create `tests/test_goal_service.py`:

```python
from nutrition_tracker.services.goal_service import derive_goals


def test_derive_goals_returns_core_targets():
    settings = {
        "profile": {
            "sex": "male",
            "date_of_birth": "1990-01-01",
            "height_cm": 183,
            "weight_kg": 86,
            "activity_level": "moderate",
            "goal_mode": "maintain",
            "body_fat_percent": None,
        },
        "goal_inputs": {
            "weekly_weight_change_kg": 0,
            "protein_g_per_kg": 1.8,
            "fat_g_per_kg": 0.8,
            "fiber_g_per_1000kcal": 14,
        },
        "goals": {"mode": "derived_with_overrides", "daily": {}, "overrides": {}},
        "defaults": {"timezone": "Europe/Berlin", "currency": "EUR"},
    }

    goals = derive_goals(settings)

    assert set(goals.keys()) >= {"kcal", "protein_g", "fat_g", "carbs_g", "fiber_g"}
    assert goals["protein_g"] > 0
```

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_goal_service.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Implement deterministic derivation using:
- age from DOB
- Mifflin-St Jeor for BMR
- simple activity factor mapping
- calorie adjustment from `weekly_weight_change_kg`
- protein/fat from body weight multipliers
- carbs as remainder
- fiber by kcal ratio

Expose `nutrition goals derive --json` returning:

```json
{
  "status": "ok",
  "daily": {
    "kcal": {"target": 2600, "source": "derived"},
    "protein_g": {"target": 155, "source": "derived"}
  }
}
```

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_goal_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_goal_service.py
git commit -m "feat: derive nutrition goals from settings"
```

---

### Task 5: Implement meal append flow

**Objective:** Accept a structured meal payload, validate it, append it to the correct JSONL file, and return the stored object.

**Files:**
- Create: `src/nutrition_tracker/models/meal.py`
- Create: `src/nutrition_tracker/repositories/meal_repo.py`
- Create: `src/nutrition_tracker/services/meal_service.py`
- Create: `src/nutrition_tracker/jsonio.py`
- Create: `src/nutrition_tracker/utils/ids.py`
- Test: `tests/test_meal_service.py`

**Step 1: Write failing test**

Create `tests/test_meal_service.py`:

```python
import json
from pathlib import Path
from typer.testing import CliRunner
from nutrition_tracker.cli import app

runner = CliRunner()


def test_meal_add_appends_jsonl(tmp_path: Path):
    runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])

    payload = {
        "timestamp": "2026-05-31T08:00:00+02:00",
        "source": "manual",
        "foods": [{"label": "Skyr", "amount": 250, "unit": "g", "estimated": False, "confidence": "high"}],
        "nutrition": {"kcal": 160, "protein_g": 27, "fat_g": 0.2, "carbs_g": 11, "fiber_g": 0},
    }
    meal_file = tmp_path / "meal.json"
    meal_file.write_text(json.dumps(payload), encoding="utf-8")

    result = runner.invoke(app, ["meal", "add", "--path", str(tmp_path), "--file", str(meal_file), "--json"])
    assert result.exit_code == 0
    assert (tmp_path / "data" / "meals" / "2026" / "2026-05-31.jsonl").exists()
```

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_meal_service.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Implement:
- payload file loading
- ID generation if missing
- schema validation
- append JSONL line to `data/meals/YYYY/YYYY-MM-DD.jsonl`
- JSON result including stored record

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_meal_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_meal_service.py
git commit -m "feat: add meal append command"
```

---

### Task 6: Implement correction append flow

**Objective:** Append correction events against known meal IDs and reject unknown targets.

**Files:**
- Create: `src/nutrition_tracker/models/correction.py`
- Create: `src/nutrition_tracker/repositories/correction_repo.py`
- Create: `src/nutrition_tracker/services/correction_service.py`
- Test: `tests/test_correction_service.py`

**Step 1: Write failing test**

Create `tests/test_correction_service.py` with two tests:
- correction against existing meal ID succeeds
- correction against unknown meal ID fails with non-zero exit code

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_correction_service.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Implement correction operations:
- `replace`
- `cancel`
- `annotate`

Validation rules:
- target meal ID must exist
- `replace` may replace `foods`, `nutrition`, `notes`
- write to `data/corrections/YYYY/YYYY-MM-DD.jsonl`

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_correction_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_correction_service.py
git commit -m "feat: add correction append command"
```

---

### Task 7: Implement effective-meal projection and daily rebuild

**Objective:** Compute the effective state for a day after applying corrections and persist a daily summary.

**Files:**
- Create: `src/nutrition_tracker/models/summary.py`
- Create: `src/nutrition_tracker/repositories/summary_repo.py`
- Create: `src/nutrition_tracker/services/daily_service.py`
- Create: `src/nutrition_tracker/utils/dates.py`
- Test: `tests/test_daily_service.py`

**Step 1: Write failing test**

Create `tests/test_daily_service.py` asserting:
- meals are aggregated
- corrections alter totals
- cancelled meals disappear from effective totals
- summary file is written under `data/daily/YYYY/YYYY-MM-DD.summary.json`

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_daily_service.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Implement daily summary fields:
- `date`
- `meals`
- `totals`
- `goals`
- `delta`
- `progress_pct`
- `signals`

Signals should include only deterministic facts such as:
- meal_count
- fruit_servings
- vegetable_servings
- highly_processed_meal_count
- data_confidence

Add CLI command:
```bash
nutrition day show YYYY-MM-DD --json
```

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_daily_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_daily_service.py
git commit -m "feat: add daily summary rebuild"
```

---

### Task 8: Implement weekly summary rebuild

**Objective:** Build weekly averages from daily summaries with coverage reporting.

**Files:**
- Create: `src/nutrition_tracker/services/weekly_service.py`
- Test: `tests/test_weekly_service.py`

**Step 1: Write failing test**

Create `tests/test_weekly_service.py` asserting:
- averages are computed from tracked days only
- `days_tracked`, `days_total`, and `coverage_pct` are returned
- summary file is written under `data/weekly/YYYY/YYYY-Www.summary.json`

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_weekly_service.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Add command:
```bash
nutrition week show 2026-W22 --json
```

Compute:
- tracked day count
- 7-day denominator
- averages for core metrics
- averages for extended metrics only when present

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_weekly_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_weekly_service.py
git commit -m "feat: add weekly summary rebuild"
```

---

### Task 9: Implement `meal list` and JSON read-model commands

**Objective:** Expose stable read commands the Hermes skill can rely on for day-level meal lookup and correction targeting.

**Files:**
- Modify: `src/nutrition_tracker/cli.py`
- Modify: `src/nutrition_tracker/services/daily_service.py`
- Test: `tests/test_end_to_end_logging_flow.py`

**Step 1: Write failing test**

Create `tests/test_end_to_end_logging_flow.py` asserting this sequence:
1. init
2. add meal
3. list meals for day
4. correct meal by ID
5. show day summary
6. show week summary

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_end_to_end_logging_flow.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

Add command:
```bash
nutrition meal list 2026-05-31 --path . --json
```

Return:

```json
{
  "date": "2026-05-31",
  "meals": [
    {
      "id": "meal_...",
      "effective": true,
      "cancelled": false,
      "nutrition": {"kcal": 160, "protein_g": 27, "fat_g": 0.2, "carbs_g": 11}
    }
  ]
}
```

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_end_to_end_logging_flow.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_end_to_end_logging_flow.py
git commit -m "feat: add read model commands for meal listing"
```

---

### Task 10: Implement `doctor` integrity checks

**Objective:** Add an explicit consistency checker for schema, file layout, and summary rebuildability.

**Files:**
- Create: `src/nutrition_tracker/services/doctor_service.py`
- Modify: `src/nutrition_tracker/cli.py`
- Modify: `tests/test_doctor_service.py`

**Step 1: Write failing test**

Add test cases for:
- valid repo returns `status=ok`
- malformed meal line returns `status=error`
- unknown correction target returns `status=error`

**Step 2: Run test to verify failure**

Run:
```bash
PYTHONPATH=src pytest tests/test_doctor_service.py -v
```

Expected: FAIL.

**Step 3: Write minimal implementation**

`nutrition doctor --json` must verify:
- required directories exist
- settings file exists and validates
- meal/correction JSON lines parse
- schemas load
- all correction targets exist
- daily rebuild can complete without exception

**Step 4: Run test to verify pass**

Run:
```bash
PYTHONPATH=src pytest tests/test_doctor_service.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/nutrition_tracker tests/test_doctor_service.py
git commit -m "feat: add storage integrity doctor"
```

---

### Task 11: Add polish, docs, and full test pass

**Objective:** Make the repository runnable by another engineer without tribal knowledge.

**Files:**
- Modify: `README.md`
- Modify: `docs/spec.md`
- Modify: `docs/implementation-plan.md`
- Modify: `tests/*`

**Step 1: Write final verification checklist into README**

Document:
- installation
- local dev setup
- init flow
- sample meal payload
- sample correction payload
- available commands

**Step 2: Run code quality checks**

Run:
```bash
ruff check src tests
```

Expected: no errors.

**Step 3: Run full test suite**

Run:
```bash
PYTHONPATH=src pytest -v
```

Expected: all tests pass.

**Step 4: Manual smoke test**

Run:
```bash
python -m nutrition_tracker.cli --help
nutrition init --path /tmp/nutrition-smoke --json
nutrition goals derive --path /tmp/nutrition-smoke --json
```

Expected: JSON outputs, no tracebacks.

**Step 5: Commit**

```bash
git add README.md docs tests src
git commit -m "docs: finalize mvp cli implementation plan and verification"
```

---

## 5. Sample payloads for implementation

### Sample meal input file

`meal.json`

```json
{
  "timestamp": "2026-05-31T12:34:56+02:00",
  "source": "manual",
  "source_context": {
    "channel": "telegram",
    "message_id": "12345",
    "image_present": false
  },
  "foods": [
    {
      "label": "Hähnchenbrust",
      "amount": 180,
      "unit": "g",
      "estimated": false,
      "confidence": "high"
    },
    {
      "label": "Reis gekocht",
      "amount": 220,
      "unit": "g",
      "estimated": true,
      "confidence": "medium"
    }
  ],
  "nutrition": {
    "kcal": 620,
    "protein_g": 48,
    "fat_g": 14,
    "carbs_g": 71,
    "fiber_g": 4,
    "saturated_fat_g": 2.5,
    "sugar_g": 1.1,
    "sodium_mg": 220
  },
  "quality_signals": {
    "fruit_servings": 0,
    "vegetable_servings": 1,
    "highly_processed": false
  },
  "assumptions": [
    "Kein zusätzliches Öl sichtbar"
  ],
  "notes": "Mittagessen"
}
```

### Sample correction input file

`correction.json`

```json
{
  "timestamp": "2026-05-31T13:10:00+02:00",
  "meal_id": "meal_2026-05-31T12-34-56+02-00_001",
  "operation": "replace",
  "changes": {
    "foods": [
      {
        "label": "Hähnchenbrust",
        "amount": 180,
        "unit": "g",
        "estimated": false,
        "confidence": "high"
      },
      {
        "label": "Reis gekocht",
        "amount": 250,
        "unit": "g",
        "estimated": false,
        "confidence": "high"
      }
    ],
    "nutrition": {
      "kcal": 670,
      "protein_g": 49,
      "fat_g": 14,
      "carbs_g": 82,
      "fiber_g": 4
    }
  },
  "reason": "User corrected rice amount"
}
```

---

## 6. Key risks during implementation

### Risk 1: Overengineering the nutrition model
Do not build a giant nutrient ontology now.
MVP needs a stable core and optional extended fields.

### Risk 2: Smuggling LLM behavior into the CLI
Do not add fuzzy text parsing to the CLI.
That belongs in Hermes.

### Risk 3: Treating summaries as source of truth
They are caches/read models. Rebuild must stay possible.

### Risk 4: Weak correction semantics
If corrections are vague, history becomes untrustworthy.
Internal stable meal IDs are mandatory even if user-facing UX is natural language.

### Risk 5: Test coverage too shallow
End-to-end append → correct → rebuild → summarize must be covered before calling MVP real.

---

## 7. Definition of done for MVP backend

MVP backend is done when all of the following are true:
- `nutrition init` creates a valid working tree
- `nutrition goals derive --json` computes stable core goals
- `nutrition meal add --file ... --json` appends a valid meal
- `nutrition meal correct --file ... --json` appends a valid correction
- `nutrition meal list DATE --json` returns stable IDs and effective meals
- `nutrition day show DATE --json` returns totals, goals, delta, progress
- `nutrition week show YYYY-Www --json` returns tracked-day averages and coverage
- `nutrition doctor --json` catches broken state
- full pytest suite passes
- no command depends on network or LLM availability

---

## 8. Execution handoff

Plan complete and saved. Ready to execute using subagent-driven-development — one task at a time, with verification after each task.
