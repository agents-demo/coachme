# Coach Comments on Frames + Drill Assignments

**Status:** not started
**Phase:** D9 — Platform
**Effort:** M
**Depends on:** coach/team layer (33_coach-team.md); annotations
**Competitor ref:** Hudl/Veo, Onform

## Goal

A coach pins comments to a specific frame or timestamp; assigns drills; the
athlete sees them in the session view and receives a notification.

## Where it lives

- Builds on the annotations schema.
- gui2 — coach comment panel; drill assignment list.
- Notifications: push (mobile) or in-app.

## Acceptance

- Comments pinned to timestamps persist in the session.
- Drill assignments appear as a checklist for the athlete.
- Completions are trackable by the coach.

## Risks

Scope: keep this to comments + assignment only — not a full LMS. Do not build
curriculum management here.

---
*See [00_priorities.md](00_priorities.md) §8 item D9 for sequencing context.*
