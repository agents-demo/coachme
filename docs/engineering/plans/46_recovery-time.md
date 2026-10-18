# Recovery Time Per Stroke

**Status:** not started
**Phase:** B.5 / A1 — Pipeline analytics
**Effort:** S
**Depends on:** stroke-window dense sampling (14_stroke-segmentation.md + M8 from 16_handedness-sampling.md)

## Goal

Measure seconds from each wrist-speed peak until the player returns to a ready
configuration (ankle separation near shoulder width, knee near baseline, hands
near hip height). The most actionable intermediate-player metric — they are
still finishing the follow-through when the next ball arrives.

## Where it lives

`core/stages/measure/` — scan the dense stroke window forward until ready
criteria hold for 2 consecutive frames. Add to the `strokes[]` block in the
report.

## Acceptance

- Median recovery time + count recovered/total per session.
- Manual spot-check on 10 strokes against video.
- Omits strokes with no recovery inside the window (no invented values).

## Risks

Thresholds are individual — store a configurable baseline, not hard-coded
degree values. Expose in settings.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A1.*
