# Calibration & Normalization

**Status:** not started
**Phase:** 0.2 — Foundations
**Effort:** L
**Depends on:** nothing; unblocks trustworthy compare/progress/skill-ratings

## Goal

Make metrics comparable across sessions when camera distance, angle, or zoom
changes — so reported "progress" is real, not an artifact of the recording
setup.

## Where it lives

`core/video/metrics.py` — add a normalization step. Three options (implement
in priority order):

1. **Table/court detection** as a known-size scale reference (best for table
   tennis).
2. **Subject-height normalization** — pose shoulder→ankle as a reference
   length.
3. **Explicit user input** — "distance/height" stored in the profile
   (`core/config.py` + profile store) as a manual fallback.

Store `calibration` block in the report; re-state metrics in calibrated units
where the method allows it.

## Acceptance

- Two clips of the same player at different distances produce comparable metric
  ranges within a stated tolerance.
- Report notes the calibration basis used (or "uncalibrated").
- `compare` warns when clips are uncalibrated.

## Risks

- Detection robustness — court/table detection fails on poor-angle clips.
- May need a calibration UI step later (user taps table corners).

---
*See [00_priorities.md](00_priorities.md) §3 item 0.2 for sequencing context.*
