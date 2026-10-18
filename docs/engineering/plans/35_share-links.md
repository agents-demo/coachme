# Share Links & Socials

**Status:** not started
**Phase:** D4 — Platform
**Effort:** M
**Depends on:** nothing; share is opt-in (privacy default)
**Competitor ref:** Onform, Hudl/Veo

## Goal

Public read-only report links (no auth required) and export to
Instagram/TikTok-friendly vertical clips.

## Where it lives

- `surfaces/gui2/server/routes/` — tokenized read-only report route.
- `surfaces/gui2/client/` — share action; read-only report view.
- ffmpeg/Pillow — vertical highlight clip renderer (builds on existing reel
  export).

## Acceptance

- A share URL renders the report read-only with no login required.
- A vertical highlight clip exports from the report.
- Share is always opt-in; default is private.

## Risks

Privacy: ensure the tokenized link cannot be guessed and expires reasonably.
Default must be private.

---
*See [00_priorities.md](00_priorities.md) §8 item D4 for sequencing context.*
