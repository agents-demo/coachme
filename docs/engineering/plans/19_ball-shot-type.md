# Ball: Shot-Type Classification & Pace

**Status:** not started
**Phase:** C1 — Analysis depth
**Effort:** L
**Depends on:** existing ball tracker
**Competitor ref:** SwingVision (their core product)
**Go/no-go gate:** accuracy must clear stated threshold on a labelled set; else descope C1 and C6, keep heuristic with a "low confidence" label

## Goal

On top of the working ball tracker, classify shot type (forehand / backhand /
serve) and estimate pace per contact; drive rally segmentation from ball
contacts.

## Where it lives

- `core/video/` — feature extraction from ball track + pose (contact point,
  arm swing direction, ball incoming/outgoing angle).
- `integrations/ballmodel.py` or a new `integrations/shottype.py` for the
  classifier.
- `domain/report.py` — prompts updated to use shot-type labels.
- Report schema gains `strokes[].type` and `strokes[].pace`.

## Acceptance

- Shot labels (forehand / backhand / serve) on a labelled test set with a
  stated accuracy threshold (define the threshold before building).
- Graceful fallback when classification is uncertain.

## Risks

- Dataset and licensing: training a classifier needs labelled data; public
  datasets may be research-only.
- Generalization across sports and camera angles.
- C2 and C6 depend on this — if this does not reach the accuracy threshold,
  both are descoped.

## Implementation path (from feasibility research)

**Start heuristic, then ML (B1 from 45_analysis-pipeline-research.md):**

A rule-based classifier over relative signals (hand, wrist speed, ball
height/exit direction, contact side) can reach ~60–70% on clean single-player
clips. That is not 90%+. Do not present uncertain labels as fact.

1. Build a small labelled set from your own clips (export timestamps + stroke
   type).
2. Heuristic rules + confidence; abstain when uncertain.
3. Only then consider an ML model (TTNet-style) — that is a separate training
   effort with its own data/licence requirements.

Serve classification is unreliable without table detection (31_table-heatmap.md
B2). Do not classify serves until that is solid.

**Ball speed (B3):**

A table-plane homography alone cannot give ball speed — it maps only points on
the table plane, not the ball's flight path. Feasible options:

1. Ball-size scale: the known 40 mm diameter gives a monocular size cue per
   frame (blob area already tracked). Gives approximate 3D → approximate speed.
   Label it "estimated" with an error band.
2. Calibrated camera + table model: needs camera intrinsics and a stable camera.
3. High-framerate capture during the stroke window reduces motion blur.

Only show speed with a stated error band. Keep "relative speed" as the default
until calibration is solid.

---
*See [00_priorities.md](00_priorities.md) §7 item C1 for sequencing context.*
*Full feasibility detail: [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §3 B1, B3.*
