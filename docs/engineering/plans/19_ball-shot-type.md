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

---
*See [00_priorities.md](00_priorities.md) §7 item C1 for sequencing context.*
