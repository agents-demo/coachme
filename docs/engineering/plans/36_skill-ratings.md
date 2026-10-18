# Assessments / Skill Ratings

**Status:** not started
**Phase:** D5 — Platform
**Effort:** M
**Depends on:** calibration (05_calibration.md) for trustworthy scores across sessions
**Competitor ref:** Sportsbox AI, HomeCourt

## Goal

A per-skill rubric (footwork, preparation, transfer, recovery) with a score
1–5 and a level estimate; reassessed each session and shown as a trend.

## Where it lives

- `domain/` — rubric definition + scoring logic; a coach prompt that derives
  skill scores from the report findings.
- gui2 — radar chart and line chart per skill over time.

## Acceptance

- 4 skill scores per session.
- Radar/line chart visible in the report and the trend view.
- Scores are explainable — every score links to the evidence that drove it.

## Risks

Subjectivity: skill scores are only trustworthy when tied to measured evidence.
If the prompt cannot ground the score in evidence, do not ship it.

---
*See [00_priorities.md](00_priorities.md) §8 item D5 for sequencing context.*
