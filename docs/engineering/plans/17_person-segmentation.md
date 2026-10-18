# Person Detection + Subject Segmentation

**Status:** not started
**Phase:** B.5 / I1 + I2 — Integrations
**Effort:** M + M
**Depends on:** nothing; I1 is a prerequisite for multi-player attribution (C4 / 22_multi-player.md)
**Build order:** third within Phase B.5

## Goal

**I1 — Person detection:** real person detection and tracking (`person.py`) to
identify and select the correct subject in multi-person clips. Prerequisite
for multi-player (C4).

**I2 — Subject segmentation:** isolate the player from the background using
MediaPipe SelfieSegmentation or a small dedicated model. Improves pose landmark
accuracy on cluttered backgrounds.

## Where it lives

- I1: new `integrations/person.py`; wired into `core/stages/measure/` for
  subject selection.
- I2: `integrations/pose.py` or a new `integrations/segmentation.py`;
  pre-processing step before pose estimation.

## Acceptance

- I1: primary subject is auto-selected in a two-person clip; user can override.
- I2: segmented foreground improves pose landmark accuracy on cluttered
  backgrounds (measure on a test set).

## Risks

- I1: occlusion and player crossings; use a tracking algorithm (e.g. ByteTrack)
  not frame-by-frame detection.
- I2: model size vs. on-device performance. Keep it small; test on Android.

---
*See [00_priorities.md](00_priorities.md) §6 items I1, I2 for sequencing context.*
