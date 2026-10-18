# Similar-Session Retrieval

**Status:** not started
**Phase:** C / analysis-ideas C3 — Platform
**Effort:** M
**Depends on:** calibrated metrics (05_calibration.md); stable metric schema; ≥5 sessions

## Goal

Embed each session's key metrics; retrieve nearest past sessions; explain the
deltas. Surfaces patterns like "your lateral range was 20% lower last week —
here is what changed."

## Where it lives

- Session embeddings stored alongside reports.
- A retrieval endpoint: nearest-K by calibration-aware metric distance.
- Report / gui2 — "Similar past sessions" panel.

## Acceptance

- Nearest sessions retrieved with explained metric deltas.
- Calibration-aware distance — does not compare uncalibrated sessions as if
  they are comparable.

## Risks

Requires calibrated metrics (05_calibration.md) — do not build until
calibration is trusted. Postpone until A9 (43_multi-session-trends.md) is
stable.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §4 C3.*
