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

## Table detection (B2 from feasibility research) — spike, not guaranteed

Auto-detecting the table (colour + contour) is the upgrade path over manual
corner taps. But:

- OpenCV is not currently a dependency. Adding `opencv-python-headless` is fine
  server-side; Android needs a native CV port or falls back to manual corners.
- Colour detection fails on non-green/blue tables, under glare, occlusion, and
  when the near edge is cropped.
- **Ship manual 4-corner calibration first.** Auto-detection is a time-boxed
  spike with a no-go gate: if it is unreliable on your test set, keep manual
  calibration and still get the heatmap.

**Build order:** manual corners (this spec) → auto-detection spike (B2).

## Player distance from table (B6 from feasibility research)

Projecting a foot landmark through the table homography is wrong — feet are on
the floor plane, not the table plane. Two feasible options:

1. **Floor-plane homography:** calibrate with floor points / table base.
2. **Player-height scale:** known height + pose shoulder→ankle to estimate
   scale.

Report a range (near / mid / far) with an error band, not a centimetre value.
Hide when uncalibrated.

---
*See [00_priorities.md](00_priorities.md) §8 item C13 for sequencing context.*
*Full feasibility detail: [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §3 B2, B4, B6.*
