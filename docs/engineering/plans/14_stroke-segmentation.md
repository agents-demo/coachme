# Stroke / Repetition Segmentation

**Status:** not started
**Phase:** B.5 / M3 — Measure stage expansion
**Effort:** M
**Depends on:** nothing; this is the key enabler for per-rep metrics and per-stroke feedback
**Build order:** first within Phase B.5

## Goal

Detect individual strokes and repetitions from motion peaks and wrist velocity,
producing a `segments[]` array with start/end times. This enables per-rep
metrics, consistency scoring, and per-stroke coaching.

## Where it lives

New `core/stages/measure/segment.py`. Wired into `core/strategies/base.py`.
Strokes derived from motion peaks + wrist velocity from pose landmarks.
`segments[]` added to the report schema.

## Acceptance

- N segments returned with start/end timestamps.
- Per-rep metrics and variance computed.
- Degrades gracefully on clips where segmentation is uncertain (returns empty
  or partial with a note).

## Risks

- Motion peak detection may be noisy on clips with camera movement.
- Wrist velocity requires reliable pose tracking — degrades if pose is poor.

---
*See [00_priorities.md](00_priorities.md) §6 item M3 for sequencing context.*
