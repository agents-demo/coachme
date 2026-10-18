# Technique Drift / Fatigue Detection

**Status:** not started
**Phase:** B.5 / A7 — Pipeline analytics
**Effort:** S
**Depends on:** ≥6 strokes in the clip; stroke segmentation (14_stroke-segmentation.md)

## Goal

Compare first vs last 30% of strokes (knee flex, lateral range, stroke
strength) to distinguish skill from conditioning. Flags when a player's
mechanics deteriorate over a session.

## Where it lives

`core/stages/measure/` — per-stroke medians across time windows; compare
first-third vs last-third.

## Acceptance

- Flags drift only when the effect exceeds a stated minimum.
- Returns "no clear drift" when the clip is too short or variance is within
  noise — never invents a trend.

## Risks

Short highlight clips are not fatigue tests. Label the finding as a "hint"
with the clip length and stroke count shown.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A7.*
