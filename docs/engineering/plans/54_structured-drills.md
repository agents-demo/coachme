# Structured Drill Schema

**Status:** not started
**Phase:** B.5 / A10 — Pipeline analytics
**Effort:** M
**Depends on:** nothing (prompt + schema change only)

## Goal

Drills become structured objects `{drill, stroke_type, cue, reps, success_condition}`
instead of plain strings. Enables checkable drill assignments, progress
tracking, and training plans.

## Where it lives

- `domain/report.py` — schema change for `drills[]`.
- Prompt update — instruct the model to emit structured drills.
- Report migration — old reports with string drills still load (backward-compatible).

## Acceptance

- New reports render structured drills with reps and a success condition.
- Old reports still load without error.
- Model-suggested reps/success conditions labelled as "suggested, not measured."

## Risks

The model can invent reps or unrealistic success conditions. Mark them as
"suggested" and let the user edit them. This is the prerequisite for training
plans (34_training-plans.md) to be useful.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A10.*
