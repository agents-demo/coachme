# Cross-Device Sync

**Status:** not started
**Phase:** D11 — Platform
**Effort:** M–L
**Depends on:** accounts (33_coach-team.md) + a sync store

## Goal

Sync sessions and the training plan across devices (phone ↔ web) once
accounts exist.

## Where it lives

- Builds on the account + storage model from D2.
- Sync store: likely a cloud-backed key-value or document store.
- Conflict handling: last-write-wins for sessions; merge for plans.

## Acceptance

- A session recorded on the phone shows up on the web within a sync cycle.
- Conflict handling defined, tested, and surfaced to the user when needed.

## Risks

Conflict handling is the hard part — define the rules before building, not
after.

---
*See [00_priorities.md](00_priorities.md) §8 item D11 for sequencing context.*
