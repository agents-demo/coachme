# Late-Feet Timing Gap

**Status:** not started
**Phase:** B.5 / A2 — Pipeline analytics
**Effort:** S
**Depends on:** stroke-window dense sampling (14_stroke-segmentation.md); footwork_series already exists

## Goal

Time between the last large lateral footwork reversal before a stroke and the
wrist-speed peak. Negative = feet arrived after the arm started. "Late feet"
is the most common correction at intermediate level.

## Where it lives

`core/stages/measure/` — find the last direction reversal in `footwork_series`
before each stroke; delta = stroke_t − reversal_t. Report per stroke and
session median.

## Acceptance

- Flags late feet only when |delta| exceeds a stated threshold.
- Degrades to "unknown" with sparse footwork data — no fabricated values.

## Risks

The footwork proxy is lower-body centroid, not feet. Label accordingly.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A2.*
