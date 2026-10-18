# Calibration & Normalization

**Status:** not started — stub
**Phase:** 0.2 — Foundations
**Effort:** L
**Depends on:** nothing; unblocks compare/progress accuracy

## Goal

Make metrics comparable across sessions when camera distance, angle, or zoom
changes — so "progress" is real, not an artifact.

## Acceptance

- Two clips of the same player at different distances produce comparable metric
  ranges within a stated tolerance.
- Report notes the calibration basis used.
- `compare` warns when clips are uncalibrated.

---
*Full spec to be written. See [00_priorities.md](00_priorities.md) §3 item 0.2.*
