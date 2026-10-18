# Gamification — Challenges & Leaderboards

**Status:** not started
**Phase:** D10 — Platform
**Effort:** M
**Depends on:** accounts (coach/team layer, D2); everything opt-in
**Competitor ref:** HomeCourt

## Goal

Drills as challenges with streaks; an opt-in leaderboard to make practice
sticky.

## Where it lives

- gui2 + a small store — challenge state, streak tracking.
- Leaderboard: opt-in only; private by default.

## Acceptance

- Users can join and complete a challenge.
- Streak tracked and shown.
- Opt-in leaderboard ranks users; private by default.

## Risks

Privacy / social moderation: leaderboards expose user data. Keep everything
opt-in. Do not build global leaderboards without a moderation plan.

---
*See [00_priorities.md](00_priorities.md) §8 item D10 for sequencing context.*
