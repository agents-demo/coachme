# Whole-Session Auto-Segmentation

**Status:** not started
**Phase:** C2 — Analysis depth
**Effort:** L
**Depends on:** C1 (ball shot-type + contacts) — 19_ball-shot-type.md
**Competitor ref:** SwingVision, Hudl/Veo

## Goal

Feed a whole session file; auto-detect rallies using ball signal and motion
gaps; analyze each rally, producing per-rally reports and an aggregate summary.

## Where it lives

- New `core/stages/measure/segment.py` (or extend from M3 segmentation).
- Strategy orchestrates per-rally analysis runs.
- Report gains `rallies[]` with per-rally summaries and an aggregate.

## Acceptance

- A long clip (5–10 min) yields N per-rally reports plus an aggregate.
- User can drill into one rally from the aggregate.
- LLM cost per clip managed by token budget controls (one pass per rally).

## Risks

- Segmentation errors (merged or split rallies) compound report quality.
- Cost: one LLM pass per rally on a 30-rally session is significant — gate
  behind a cost toggle and show cost in Diagnostics.

---
*See [00_priorities.md](00_priorities.md) §7 item C2 for sequencing context.*
