# Line Calls / Scoring / Match Stats

**Status:** not started
**Phase:** C6 — Analysis depth
**Effort:** L
**Depends on:** C1 (ball contacts + trajectory) and court/table detection
**Competitor ref:** SwingVision (their headline feature)

## Goal

Automatic scorekeeping, advisory in/out calls, rally stats, and a match
summary. All calls are clearly labelled advisory — never presented as official.

## Where it lives

- Court/table detection (build on or extend table-heatmap work — C13).
- `domain/` — match model: score state machine, in/out geometry.
- Report gains `match{}` block: score, call log, rally stats, match summary.

## Acceptance

- Score tracked with reviewable calls.
- Match summary in the report.
- All calls labelled "advisory" with a review affordance.
- Never presented as official calls.

## Risks

Accuracy / liability: in/out calls depend on ball-landing precision. Do not
ship without clear advisory labelling and a "review this call" affordance.
SwingVision has been doing this for years — accuracy bar is high.

---
*See [00_priorities.md](00_priorities.md) §7 item C6 for sequencing context.*
