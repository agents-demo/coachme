# Rally Length Distribution

**Status:** not started
**Phase:** B.5 / A8 — Pipeline analytics
**Effort:** S
**Depends on:** reliable ball hits/bounces (already in ball tracking); rally segments (already exist)

## Goal

Group consecutive ball contacts into bins (1, 2–3, 4–7, 8+ shots) and report
percentages. Short rallies imply serve-and-attack; long rallies imply
consistency.

## Where it lives

`core/stages/measure/` — use existing `ball.hits[]` / `bounces[]` timestamps
and rally segments. Exclude segments with implausible contact spacing.

## Acceptance

- Distribution shown with the number of rallies used.
- Low-confidence tag when hit detection is weak.

## Risks

Missed or false ball contacts change the distribution. No point-end detection,
so "rally" here means continuous ball exchange, not a scored point.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A8.*
