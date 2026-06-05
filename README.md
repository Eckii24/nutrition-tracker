# Nutrition Tracker

Lokales, dateibasiertes Nutrition-Tracking mit **Zwei-Repository-Setup**:
- **Repository 1: dieses CLI-Tool** — generisches, deterministisches Backend für Speicherung, Validierung und Summaries.
- **Repository 2: private Anwendungs-/Daten-Repo** — enthält die eigentlichen Nutzdaten, individuelle Settings und den Hermes-/Skill-Layer für Ingest, Rückfragen, Schätzungen und Bestätigung.

## Status

MVP-Backend implementiert: deterministic Python CLI, JSON-first, file-based source of truth.

## Produktgrenze

Diese CLI ist **absichtlich kein Freitext-Parser**.

Sie erwartet strukturierte Payloads mit geschätzten Nährwerten und ist dafür zuständig:
- Eingaben gegen Schemas zu validieren
- append-only Events zu speichern
- Daily/Weekly Summaries deterministisch neu aufzubauen

Wichtig: Im privaten App-Repo dürfen strukturierte Dateien auch **direkt geschrieben oder editiert** werden, wenn das für den Skill-/Git-Workflow einfacher ist. Die CLI ist vor allem dann wertvoll, wenn sie danach deterministisch prüft, aggregiert und reproduzierbare Auswertungen baut.

Freitext, Bilder, Unsicherheit, Rückfragen und Bestätigung gehören in den vorgeschalteten Hermes-/Skill-Layer im **separaten privaten App-Repo**.

## Architektur: Zwei Repositories

### Repository 1: CLI-Tool

Zweck:
- generische Nutrition-Engine
- installierbares `nutrition`-Tool
- keine personenbezogenen Daten
- keine Skill-spezifische Ingest-Logik

Verantwortlich für:
- `nutrition init`
- `nutrition goals derive`
- `nutrition meal add`
- `nutrition meal list`
- `nutrition day show`
- `nutrition week show`
- `nutrition doctor`

### Repository 2: privates App-/Daten-Repo

Zweck:
- individuelle Nutzdaten
- persönliche `settings.json`
- Skill-/Prompt-Logik für Intake, Rückfragen, Schätzung und Bestätigung
- optional Git-Versionierung der tatsächlichen Tracking-Daten

Typische Inhalte:

```text
my-nutrition-app/
  data/
  schemas/
  prompts/
  scripts/
  README.md
```

Die Verzeichnisse `data/` und `schemas/` werden initial vom CLI-Tool angelegt bzw. befüllt.

## Installation

### Empfohlener Standard für Entwicklung im CLI-Repo: uv

```bash
uv sync --all-extras
uv run nutrition --help
```

### Installation als eigenständiges Tool

Lokal aus dem Repo:

```bash
uv tool install --from /path/to/nutrition-tracker nutrition-tracker
```

Später typischerweise aus Git:

```bash
uv tool install --from git+https://<git-host>/<org>/nutrition-tracker.git nutrition-tracker
```

Danach steht das Kommando `nutrition` direkt zur Verfügung.

### Alternativ: klassisches venv/pip

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## CLI

Im CLI-Repo während der Entwicklung:

```bash
uv run nutrition --help
```

Direkt als Modul:

```bash
uv run python -m nutrition_tracker.cli --help
```

Als installiertes Tool:

```bash
nutrition --help
```

## Commands

```bash
nutrition init --path . --json
nutrition goals derive --path . --json
nutrition meal add --path . --file meal.json --json
nutrition meal list 2026-05-31 --path . --json
nutrition day show 2026-05-31 --path . --json
nutrition week show 2026-W22 --path . --json
nutrition doctor --path . --json
```

## Initialer Workflow im privaten App-Repo

### 1. Leeres Daten-/App-Repo anlegen

```bash
mkdir my-nutrition-app
cd my-nutrition-app
git init
```

### 2. CLI-Struktur initialisieren

```bash
nutrition init --path . --json
```

Das legt an:
- `data/settings.json`
- `data/meals/...`
- `data/daily/...`
- `data/weekly/...`
- `schemas/*.json`

### 3. Persönliche Settings erfassen

Das CLI erzeugt zunächst eine generische `data/settings.json`.

Der **Skill-Layer im privaten Repo** sollte danach prüfen:
- sind noch Default-/Platzhalterwerte enthalten?
- fehlen personenbezogene Profildaten?
- fehlen Zielparameter oder Override-Entscheidungen?

Erst danach sollten die individuellen Werte in `data/settings.json` geschrieben werden. Das darf bewusst **direkt per File-Write/Edit** passieren; dafür ist kein eigener CLI-Command zwingend nötig.

### 3b. Mahlzeiten erfassen

Es gibt zwei legitime Wege:

1. **CLI-append** über `nutrition meal add`
2. **direkter File-Write** ins private Repo, wenn der vorgelagerte Skill ohnehin schon strukturierte JSON/JSONL-Daten erzeugt

Pragmatische Empfehlung:
- **Settings** direkt schreiben
- **Meals** direkt schreiben oder per CLI anhängen — je nachdem, was im Skill-Flow einfacher und robuster ist
- **Auswertungen/Checks** immer über CLI laufen lassen (`goals derive`, `day show`, `week show`, `doctor`)

### 4. Ziele aus Settings ableiten

```bash
nutrition goals derive --path . --json
```

### 5. Konsistenz prüfen

```bash
nutrition doctor --path . --json
```

## Prompt-Templates für das private App-Repo

Dieses CLI-Repo liefert generische Prompt-Vorlagen mit, damit das **zweite Repo** einen sauberen Skill-Workflow aufbauen kann:
- `docs/prompts/init-settings-prompt.md`
- `docs/prompts/derive-goals-prompt.md`

Die Templates gehören **konzeptionell zum Workflow**, aber die eigentliche Skill-Implementierung und der Bestätigungs-/Ingest-Flow gehören **nicht** in dieses CLI-Repo.

## Storage

Source of truth:

```text
data/settings.json
data/meals/YYYY/YYYY-MM-DD.jsonl
```

Derived, rebuildable read models:

```text
data/daily/YYYY/YYYY-MM-DD.summary.json
data/weekly/YYYY/YYYY-Www.summary.json
```

Schemas live in `schemas/` and are copied by `nutrition init`.

## Sample meal payload

```json
{
  "timestamp": "2026-05-31T12:34:56+02:00",
  "source": "manual",
  "foods": [
    {
      "label": "Hähnchenbrust",
      "amount": 180,
      "unit": "g",
      "estimated": false,
      "confidence": "high"
    }
  ],
  "nutrition": {
    "kcal": 620,
    "protein_g": 48,
    "fat_g": 14,
    "carbs_g": 71,
    "fiber_g": 4
  },
  "quality_signals": {
    "fruit_servings": 0,
    "vegetable_servings": 1,
    "highly_processed": false
  },
  "assumptions": ["Kein zusätzliches Öl sichtbar"],
  "notes": "Mittagessen"
}
```

## Verify

```bash
uv run ruff check src tests
uv run pytest -v
```

## Docs

- `docs/PRD.md`
- `docs/spec.md`
- `docs/implementation-plan.md`
- `docs/prompts/init-settings-prompt.md`
- `docs/prompts/derive-goals-prompt.md`
