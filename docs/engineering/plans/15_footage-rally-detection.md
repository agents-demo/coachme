# Footage Quality Expansion + Rally / Scene Detection

**Status:** not started
**Phase:** B.5 / M5 + M6 — Measure stage expansion
**Effort:** S + S
**Depends on:** nothing
**Build order:** second within Phase B.5 (after M3)

## Goal

**M5 — Footage quality expansion:** extend the existing quality check to cover
full-body framing, pose completeness, lighting, camera shake, distance, and fps
— with specific actionable tips for each issue found.

**M6 — Scene / cut detection:** detect hard cuts in multi-rally recordings so
each segment is analyzed cleanly, not spliced together.

## Where it lives

- M5: grow `core/stages/measure/quality.py`.
- M6: new `core/stages/measure/scene.py`; rally segments already exist, this
  adds hard-cut detection.

## Acceptance

- M5: quality check returns `usable/limits` with a specific tip for each issue
  (e.g. "camera too far — move within 4m", "lighting too dark for pose").
- M6: cuts detected; each segment analyzed as a separate clip.

## Risks

Camera-shake detection on low-framerate clips may produce false positives.
Keep thresholds configurable.

---
*See [00_priorities.md](00_priorities.md) §6 items M5, M6 for sequencing context.*
