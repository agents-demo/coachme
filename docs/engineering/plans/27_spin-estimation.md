# Spin Estimation

**Status:** stretch goal — likely non-goal
**Phase:** C9 — Analysis depth
**Effort:** XL
**Depends on:** ball track + possibly a dedicated model
**Competitor ref:** SwingVision

## Goal

Estimate spin type and rough amount from a single camera — only if it can be
done honestly.

## Where it lives

`core/video/` — ball trajectory cues (curve, deceleration); possibly a small
dedicated model trained on labelled spin data.

## Acceptance

**This item ships only if reliable on a labelled test set.**

If not reliable: permanently descoped. The app notes spin estimation as a
stated limitation rather than shipping a guess. Single-camera spin is
unreliable by physics — do not ship a guess.

## Risks

Single-camera spin estimation is fundamentally limited — the ball rotation is
not directly visible at normal framerates. This is likely a non-goal. A
feasibility assessment should be done before any implementation work.

---
*See [00_priorities.md](00_priorities.md) §7 item C9 for sequencing context.*
