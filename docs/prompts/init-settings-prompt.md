# Prompt Template: Initialize Personal Settings

Use this prompt in the **private application repository**, not in the generic CLI repository.

## Purpose

Guide a Hermes skill through the first-run setup after `nutrition init` created a generic `data/settings.json`.

The goal is to detect whether the settings still contain placeholder/default values and, if so, ask the user the right questions before writing personalized settings.

## Suggested prompt

```text
You are setting up a private nutrition-tracker data repository that already contains a generic `data/settings.json` created by the `nutrition` CLI.

Your job:
1. Read `data/settings.json`.
2. Decide whether the profile/settings still look generic or incomplete.
3. If values are missing, generic, placeholder-like, or clearly not user-specific, ask only the necessary follow-up questions.
4. Collect enough information to produce a personalized settings file for nutrition goal derivation.
5. Do not estimate personal profile values silently.
6. Before writing anything, show the proposed settings changes clearly and wait for confirmation.
7. After confirmation, write `data/settings.json`.
8. Then run `nutrition goals derive --path . --json`.
9. Finally run `nutrition doctor --path . --json` and report the result.

Required profile fields to verify:
- sex
- date_of_birth
- height_cm
- weight_kg
- activity_level
- goal_mode
- optional: body_fat_percent

Useful goal inputs to verify:
- weekly_weight_change_kg
- protein_g_per_kg
- fat_g_per_kg
- fiber_g_per_1000kcal

Rules:
- Keep the CLI deterministic; all user-facing interpretation lives in the skill layer.
- Do not store free-text meal descriptions here.
- Do not write ad-hoc files outside the CLI contract.
- Ask compact questions.
- If the user already gave some values, reuse them instead of asking again.
```

## Expected workflow

1. `nutrition init --path . --json`
2. skill inspects `data/settings.json`
3. skill asks only missing/high-leverage questions
4. skill presents proposed personalized settings
5. user confirms
6. skill writes `data/settings.json`
7. skill runs `nutrition goals derive --path . --json`
8. skill runs `nutrition doctor --path . --json`

## Why this belongs outside the CLI

This flow mixes:
- human questioning
- ambiguity handling
- confirmation
- personal-data collection

That is skill-layer behavior, not deterministic CLI behavior.
