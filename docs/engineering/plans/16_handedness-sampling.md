# Handedness Auto-Detect + Thorough Sampling Mode

**Status:** not started
**Phase:** B.5 / M7 + M8 — Measure stage expansion
**Effort:** S + S
**Depends on:** pose landmarks
**Build order:** fourth within Phase B.5 (small; can be done in parallel with I1/I2)

## Goal

**M7 — Handedness auto-detect:** infer whether the player is left- or
right-handed from which arm swings more; suggest a profile correction if it
differs from the stored setting.

**M8 — Thorough sampling mode:** a config-gated extra frame burst around
motion peaks for a more detailed per-stroke read.

## Where it lives

- M7: `core/stages/measure/` — derived from pose arm-swing magnitude.
  Profile suggestion written to `core/config.py` / profile store.
- M8: `core/config.py` toggle + `core/stages/measure/sampling.py` extra burst
  (uses existing `sample_burst`).

## Acceptance

- M7: handedness inferred with confidence; profile suggestion shown if it
  differs from stored setting.
- M8: thorough mode doubles frames around peaks; report notes the extra
  sampling; token/latency increase visible in Diagnostics.

## Risks

- M7: ambiguous on drill clips with only one shot type.
- M8: cost increase must be clearly surfaced and opt-in.

---
*See [00_priorities.md](00_priorities.md) §6 items M7, M8 for sequencing context.*
