# Annotated Coaching Clips

**Status:** not started
**Phase:** D13 — Platform
**Effort:** M
**Depends on:** existing trim/reel pipeline
**Competitor ref:** Coach's Eye, Onform

## Goal

Burn issue text and timestamps into a trimmed clip (e.g. "right elbow too
high — 0:04") for sharing with a coach or posting on social media.

## Where it lives

- Extends the existing trim/reel export pipeline.
- ffmpeg/Media3 — text-overlay pass at each finding's timestamp.
- gui2 / Android — export action from the report.

## Acceptance

- Exported clip shows issue labels at their evidence timestamps.
- Clip is playable and shareable without the app.
- Text layout is clean (no overflow, readable on mobile screens).

## Risks

Render cost and text layout on varied clip lengths. Test on 30-second and
5-minute clips.

---
*See [00_priorities.md](00_priorities.md) §8 item D13 for sequencing context.*
