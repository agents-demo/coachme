# Service Detection

**Status:** not started
**Phase:** C11 — Table-tennis specific
**Effort:** M
**Depends on:** pose + ball segments from measure stage; stroke segmentation (M3) helps

## Goal

Flag likely serves (toss, no prior ball contact, player positioned at own end)
so serve technique, placement, and variety get dedicated coaching instead of
being treated as ordinary rally strokes.

## Where it lives

- `core/stages/measure/` — detect serve signature from pose (arm raised for
  toss) + ball (no incoming contact before this one) + player position.
- Report schema: `strokes[].type = "serve"`.

## Acceptance

- Serves flagged with a confidence level.
- Degrades gracefully when the toss is out of frame (marks as uncertain, does
  not crash or misclassify).

## Risks

False positives: a high backswing can look like a toss. Toss is often cropped
in phone footage. Keep confidence thresholds conservative.

## Short vs long classification (B5 from feasibility research)

Short/long serve classification and second-bounce projection depend on table
detection (31_table-heatmap.md B2). Without a calibrated table-plane:
- "short/long" is a guess based on ball trajectory angle — label it speculative.
- Do not ship short/long classification until table calibration is solid.

**Build order:** serve flag (this file) first; short/long after B2 passes.

---
*See [00_priorities.md](00_priorities.md) §8 item C11 for sequencing context.*
*Full feasibility detail: [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §3 B5.*
