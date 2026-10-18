# Stroke Consistency Score

**Status:** not started
**Phase:** C / analysis-ideas C1 — Pipeline analytics
**Effort:** M
**Depends on:** stroke-type classification (19_ball-shot-type.md); dense stroke windows

## Goal

Per-stroke-type standard deviation of elbow angle, knee flexion, and wrist arc
across attempts in a session; output 0–100 with attempt count. Distinguishes
technique inconsistency from technique error.

## Where it lives

`core/video/` + `domain/` — compute per-type stddev across the stroke windows;
report as `consistency{}` per stroke type.

## Acceptance

- Score per stroke type with attempt count shown.
- Small samples (2–3 strokes) labelled low-confidence.

## Risks

Only meaningful with enough attempts per type (≥4 recommended). Report "too
few attempts" rather than a misleading number.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §4 C1.*
