# Stroke / Repetition Segmentation

**Status:** not started — stub
**Phase:** B.5 / M3 — Measure stage expansion
**Effort:** M
**Depends on:** nothing; enables per-rep metrics, consistency scoring, per-stroke feedback

## Goal

Detect individual strokes and repetitions from motion peaks and wrist velocity,
producing a `segments[]` array with start/end times and per-rep metrics.

## Acceptance

- N segments returned with start/end timestamps.
- Per-rep metrics and variance computed.
- Degrades gracefully on clips where segmentation is uncertain.

---
*Full spec to be written. See [00_priorities.md](00_priorities.md) §6 item M3.*
