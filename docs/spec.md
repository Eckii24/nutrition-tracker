# Technical Specification: Nutrition Tracker MVP

## 1. Purpose

This document defines the concrete MVP behavior for a local, file-based nutrition tracker with:
- Hermes-first interaction model
- local CLI as deterministic backend tool
- structured file storage as source of truth
- LLM-based extraction and coaching layered on top of raw nutrition data

The CLI itself must remain non-agentic: no direct LLM calls, no coaching prose, no implicit reasoning beyond deterministic calculations and schema validation.

---

## 2. Product Boundary

## In scope
- local file-based storage
- profile-based goal derivation from `settings.json`
- manual overrides for derived goals
- meal logging from structured input
- daily summaries
- weekly averages
- deterministic CLI JSON output
- Hermes skill layer that can:
  - interpret images/text
  - call CLI with structured payloads
  - read JSON results
  - produce coaching feedback

## Out of scope for MVP
- persistent image storage
- native web UI
- barcode scanning
- broad external food database integrations
- sophisticated micronutrient goal tracking
- training/rest-day goal variants
- multi-user support

---

## 3. Architecture

## 3.1 Layers

### Layer A: Storage
File-based source of truth.

### Layer B: CLI
Deterministic commands for:
- init
- profile management
- meal entry
- day summary
- week summary
- export/debug

### Layer C: Hermes skill / LLM
Responsible for:
- image interpretation
- free-text parsing
- uncertainty handling
- asking follow-up questions when needed
- coaching and qualitative evaluation

## 3.2 Strict separation
The CLI must not:
- call LLMs
- invent missing meal attributes
- generate coaching prose
- silently mutate historical records without revision trail

The skill layer must not:
- bypass schemas
- write ad-hoc files outside the CLI contract

---

## 4. Storage Model

## 4.1 Directory layout

```text
nutrition-tracker/
  docs/
    PRD.md
    spec.md
  data/
    settings.json
    meals/
      2026/
        2026-05-31.jsonl
    daily/
      2026/
        2026-05-31.summary.json
    weekly/
      2026/
        2026-W22.summary.json
  schemas/
    settings.schema.json
    meal-entry.schema.json
    daily-summary.schema.json
    weekly-summary.schema.json
```

## 4.2 Source of truth
Source of truth is:
- `data/settings.json`
- append-only meal events in `data/meals/**/*.jsonl`

Derived artifacts:
- `data/daily/**/*.summary.json`
- `data/weekly/**/*.summary.json`

Derived artifacts may be rebuilt at any time.

---

## 5. Settings Model

## 5.1 File
`data/settings.json`

## 5.2 Structure

```json
{
  "profile": {
    "sex": "male",
    "date_of_birth": "1990-01-01",
    "height_cm": 183,
    "weight_kg": 86,
    "activity_level": "moderate",
    "goal_mode": "maintain",
    "body_fat_percent": null
  },
  "goal_inputs": {
    "weekly_weight_change_kg": 0,
    "protein_g_per_kg": 1.8,
    "fat_g_per_kg": 0.8,
    "fiber_g_per_1000kcal": 14
  },
  "goals": {
    "mode": "derived_with_overrides",
    "daily": {
      "kcal": { "target": 2600, "source": "derived" },
      "protein_g": { "target": 155, "source": "derived" },
      "fat_g": { "target": 69, "source": "derived" },
      "carbs_g": { "target": 310, "source": "derived" },
      "fiber_g": { "target": 36, "source": "derived" }
    },
    "overrides": {}
  },
  "defaults": {
    "timezone": "Europe/Berlin",
    "currency": "EUR"
  }
}
```

## 5.3 Derived goal rules
MVP should derive goals deterministically from profile values.

Recommended baseline approach:
- estimate BMR via Mifflin-St Jeor
- multiply by activity factor to get maintenance calories
- apply goal adjustment if gain/loss configured
- protein target from `protein_g_per_kg`
- fat target from `fat_g_per_kg`
- carbs = remaining calories after protein/fat allocation
- fiber target from `fiber_g_per_1000kcal`

This is pragmatic, not medically authoritative.

## 5.4 Overrides
Every derived goal must be manually overridable.
The system must preserve both:
- computed value
- effective overridden value

---

## 6. Meal Event Model

## 6.1 Event semantics
Each meal entry is append-only.
If a value changes later, the private app repo may update the structured meal file directly and rely on Git history for auditability.

## 6.2 Meal entry schema

```json
{
  "id": "meal_2026-05-31T12-34-56+02-00_001",
  "timestamp": "2026-05-31T12:34:56+02:00",
  "source": "manual",
  "source_context": {
    "channel": "telegram",
    "message_id": "12345",
    "image_present": false
  },
  "foods": [
    {
      "label": "Skyr natur",
      "amount": 250,
      "unit": "g",
      "estimated": false,
      "confidence": "high"
    },
    {
      "label": "Banane",
      "amount": 1,
      "unit": "piece",
      "estimated": true,
      "confidence": "medium"
    }
  ],
  "nutrition": {
    "kcal": 290,
    "protein_g": 29,
    "fat_g": 0.8,
    "carbs_g": 38,
    "fiber_g": 3.2
  },
  "micros": {},
  "quality_signals": {
    "fruit_servings": 1,
    "vegetable_servings": 0,
    "highly_processed": false
  },
  "assumptions": [
    "Banane als mittelgroß angenommen"
  ],
  "notes": "Frühstück",
  "revision": 1
}
```

## 6.3 Required fields
Required for MVP:
- `id`
- `timestamp`
- `source`
- `foods[]`
- `nutrition.kcal`
- `nutrition.protein_g`
- `nutrition.fat_g`
- `nutrition.carbs_g`

Optional but recommended:
- `nutrition.fiber_g`
- `assumptions[]`
- `quality_signals`
- `source_context`

## 6.4 Source enum
Allowed values:
- `manual`
- `text`
- `image`
- `image+text`
- `import`

---

## 7. Editing Model

The CLI no longer exposes a separate correction event stream.
Corrections happen by directly editing structured meal files in the private app repo.
The CLI then validates and rebuilds summaries deterministically from the current stored meals.

---

## 8. Aggregation Rules

## 8.1 Daily summary
A daily summary must include:
- date
- all stored meals for that day
- totals
- goals
- deltas
- percent progress
- basic factual signals for coaching layer

Example:

```json
{
  "date": "2026-05-31",
  "totals": {
    "kcal": 2140,
    "protein_g": 148,
    "fat_g": 71,
    "carbs_g": 201,
    "fiber_g": 24
  },
  "goals": {
    "kcal": 2600,
    "protein_g": 155,
    "fat_g": 69,
    "carbs_g": 310,
    "fiber_g": 36
  },
  "delta": {
    "kcal": -460,
    "protein_g": -7,
    "fat_g": 2,
    "carbs_g": -109,
    "fiber_g": -12
  },
  "progress_pct": {
    "kcal": 82.3,
    "protein_g": 95.5,
    "fat_g": 102.9,
    "carbs_g": 64.8,
    "fiber_g": 66.7
  },
  "signals": {
    "meal_count": 3,
    "fruit_servings": 1,
    "vegetable_servings": 2,
    "highly_processed_meal_count": 0,
    "data_confidence": "medium"
  }
}
```

## 8.2 Weekly summary
Weekly summary is built from daily summaries.

Must include:
- ISO week
- included dates
- average kcal/macros/fiber
- count of tracked days
- completion coverage

Example:

```json
{
  "week": "2026-W22",
  "days_tracked": 6,
  "days_total": 7,
  "coverage_pct": 85.7,
  "averages": {
    "kcal": 2480,
    "protein_g": 162,
    "fat_g": 73,
    "carbs_g": 280,
    "fiber_g": 29
  }
}
```

---

## 9. CLI Contract

Binary name assumption for MVP:
- `nutrition`

Language is not fixed yet, but JSON-first behavior is mandatory.

## 9.1 Command principles
All read commands must support machine-readable JSON.
All write commands must return created/updated objects as JSON.
Non-zero exit code on validation failure.

## 9.2 Commands

### `nutrition init`
Creates initial directory structure and `settings.json` template.

Example:
```bash
nutrition init --path .
```

### `nutrition goals derive`
Recomputes derived goals from `settings.json`.

Example:
```bash
nutrition goals derive --json
```

### `nutrition meal add`
Adds a structured meal event.

Example:
```bash
nutrition meal add --file meal.json --json
```

### `nutrition day show`
Returns daily view from stored meals.

Example:
```bash
nutrition day show 2026-05-31 --json
```

### `nutrition week show`
Returns weekly averages.

Example:
```bash
nutrition week show 2026-W22 --json
```

### `nutrition meal list`
Lists meals for a day including effective state and IDs.

Example:
```bash
nutrition meal list 2026-05-31 --json
```

### `nutrition doctor`
Checks storage integrity and schema validity.

Example:
```bash
nutrition doctor --json
```

---

## 10. Hermes / Skill Flow

## 10.1 Image-based logging
1. User sends meal photo, optionally with text.
2. Hermes analyzes image.
3. Hermes extracts structured meal candidate.
4. Hermes states uncertainty and assumptions.
5. Hermes writes or updates the structured meal data in the private app repo.
6. CLI validates stored data and returns daily summary JSON.
7. Hermes generates user-facing feedback and coaching.

## 10.2 Text-based logging
1. User sends text description.
2. Hermes extracts foods/amounts.
3. If ambiguity is too high, Hermes asks follow-up.
4. Hermes writes or updates structured meal data in the private app repo.
5. CLI returns updated day state.
6. Hermes responds with summary + coaching.

## 10.3 Update flow
1. User says e.g. "Das waren eher 250g Reis statt 150g."
2. Hermes resolves target meal.
3. Hermes updates the structured meal data in the private app repo.
4. CLI validates current files.
5. CLI rebuilds day summary.
6. Hermes replies with changed totals and interpretation.

---

## 11. Coaching Boundary

## CLI returns only facts
Examples:
- totals
- deltas
- progress percentages
- weak quality signals
- confidence indicators

## Skill returns interpretation
Examples:
- "Dir fehlen heute wahrscheinlich noch etwa 25g Protein."
- "Kalorien liegen noch moderat unter Ziel."
- "Ballaststoffe sind bisher eher schwach abgedeckt."
- "Bisher wirkt der Tag insgesamt proteinseitig solide, gemüseseitig aber dünn."

This split matters. Otherwise the CLI becomes a hidden prompt-engine, which is the wrong abstraction.

---

## 12. Standard Metrics for MVP

A screenshot from an existing tracker app is now available and confirms a sensible baseline metric set.

### Visible tracker fields from the screenshot
- kcal
- fat_g (`Gesamtfett`)
- saturated_fat_g (`Gesättigtes Fett`)
- trans_fat_g (`Transfett`)
- polyunsaturated_fat_g (`Mehrfachfett`)
- monounsaturated_fat_g (`Einfachfett`)
- cholesterol_mg
- sodium_mg
- carbs_g (`Gesamtkohlenhydrate`)
- fiber_g (`Ballaststoffe`)
- sugar_g (`Gesamtzucker`)
- added_sugar_g (`Zuckerzusatz`)
- protein_g
- caffeine_mg
- alcohol_g
- vitamin_d_ug
- calcium_mg

### MVP required goal metrics
These should be first-class in the MVP and supported in daily + weekly summaries:
- kcal
- protein_g
- fat_g
- carbs_g
- fiber_g

### MVP extended informational metrics
These should be modeled already if practical, even if not all are used for goal logic on day 1:
- saturated_fat_g
- sugar_g
- added_sugar_g
- sodium_mg
- cholesterol_mg

### Deferred-but-schema-friendly metrics
Useful to support in the schema early, even if often missing from AI estimates:
- trans_fat_g
- polyunsaturated_fat_g
- monounsaturated_fat_g
- caffeine_mg
- alcohol_g
- vitamin_d_ug
- calcium_mg

### Practical recommendation
Do not make the full micronutrient surface mandatory for every meal event.
AI extraction will frequently be uncertain or incomplete there.
Instead:
- require core macro fields
- allow nullable/optional extended nutrition fields
- aggregate extended fields when present
- use missingness explicitly instead of inventing values

---

## 13. Validation Rules

The CLI must reject:
- invalid JSON
- schema violations
- impossible negative nutrition values
- malformed timestamps

The CLI should warn, but not necessarily reject:
- unusually large calories for one meal
- missing fiber
- low-confidence estimated foods

---

## 14. Open Technical Questions

Still open before implementation:
1. programming language for CLI
2. local nutrition reference source / lookup approach
3. exact schema versioning strategy
4. whether summaries are eagerly written or computed on read with cache refresh
5. exact Hermes edit/write workflow for updating existing meal files

---

## 15. Recommended Next Step

Next artifact should be an implementation plan covering:
- CLI language choice
- exact file paths
- schema files
- command parser
- aggregation engine
- test strategy
- first end-to-end logging flow
