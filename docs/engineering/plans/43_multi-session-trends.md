# Multi-Session Trend View

**Status:** not started
**Phase:** D12 — Platform
**Effort:** M
**Depends on:** ≥ 3 sessions of data; calibration (05_calibration.md) for trustworthy trend lines
**Competitor ref:** Onform

## Goal

Aggregate issue recurrence, drill completion, and key metrics across all
sessions — not just pairwise compare. Shows whether the player is actually
improving on flagged issues over time.

## Where it lives

- A new trends endpoint over existing reports (`surfaces/gui2/server/routes/`).
- gui2 — trend chart page (line charts per metric, issue-recurrence timeline).
- Android — same view.

## Acceptance

- Trend lines shown when ≥ 3 sessions exist.
- Chart warns when metrics are uncalibrated (comparison unreliable).
- Pairwise compare remains the fallback for < 3 sessions.

## Risks

Sparse data: most users will have < 3 sessions early. Do not show trend lines
with fewer than 3 data points.

---
*See [00_priorities.md](00_priorities.md) §8 item D12 for sequencing context.*
