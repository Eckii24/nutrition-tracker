# Prompt Template: Derive and Review Goals

Use this prompt in the **private application repository**, after personalized settings have been written.

## Purpose

Guide a Hermes skill through a deterministic goal-derivation pass:
- trigger goal derivation
- inspect returned values
- explain them compactly to the user
- ask for overrides only when useful

## Suggested prompt

```text
You are working inside a private nutrition-tracker data repository.

Your job:
1. Read `data/settings.json`.
2. Run `nutrition goals derive --path . --json`.
3. Inspect the derived daily goals.
4. Present the derived targets compactly to the user.
5. Explain that these are deterministic derived values based on the stored profile and goal inputs.
6. Ask whether the user wants any manual overrides.
7. If the user requests overrides, update `data/settings.json` accordingly, preserving both computed and effective values where the schema expects them.
8. Re-run `nutrition goals derive --path . --json` after any settings change.
9. Run `nutrition doctor --path . --json` and report the final state.

Important rules:
- Do not treat derived values as medical advice.
- Do not silently invent override values.
- Keep explanations short and factual.
- If values look implausible, point out the likely input drivers (weight, activity level, weekly change target, protein/fat factors) instead of guessing a fix.
```

## Expected workflow

1. personalized `data/settings.json` already exists
2. skill runs `nutrition goals derive --path . --json`
3. skill shows result to user
4. user optionally requests overrides or input corrections
5. skill updates settings if confirmed
6. skill re-derives goals
7. skill runs `nutrition doctor --path . --json`

## Why this belongs outside the CLI

The derivation itself is deterministic CLI behavior.

The decision whether a target is:
- acceptable
- surprising
- too aggressive
- worth overriding

is conversational skill-layer behavior.
