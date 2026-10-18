# Table Contact-Point Heatmap

**Status:** not started
**Phase:** C13 — Table-tennis specific
**Effort:** L
**Depends on:** manual 4-corner table calibration + ball trajectory + table-plane intersection

## Goal

A top-down heatmap of where the ball lands per session, revealing cross-court
bias and short/long patterns — visible in the report and on Android.

## Where it lives

- Calibration: user taps the four table corners on a freeze-frame (one-time
  per clip or per camera setup).
- `core/video/` — project ball trajectory to the table plane using the corner
  calibration.
- Report / Android overlay: render a top-down table with landing-point density.

## Acceptance

- Calibrated sessions show a landing heatmap.
- Uncalibrated sessions hide the heatmap with a clear reason.

## Risks

- Calibration UX: tapping four corners on a phone is fiddly; needs a good UI.
- Camera angle and monocular depth limit accuracy on low-angle shots.

---
*See [00_priorities.md](00_priorities.md) §8 item C13 for sequencing context.*
