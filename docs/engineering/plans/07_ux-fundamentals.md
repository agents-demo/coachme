# UX Fundamentals

**Status:** not started
**Phase:** 0.4 — Foundations
**Effort:** M (session library) + M (token streaming)
**Depends on:** nothing

## Goal

First-run onboarding, empty states, a session library with search/filter/tags/
rename/notes/bulk-delete, and token streaming so the report appears as it is
written rather than all at once.

## Where it lives

- `surfaces/gui2/server/routes/` — new tags field, bulk-delete endpoint.
- `surfaces/gui2/server/read.py` — session library query with filter support.
- `surfaces/gui2/client/` — session list page, onboarding screen, empty states.
- Streaming: SSE on the analyze path (`surfaces/gui2/server/routes/analyze.py`).

## Acceptance

- Tag, rename, and search/filter sessions.
- Report streams progressively (tokens appear as the model writes them).
- Clear loading, empty, and error states everywhere in the app.

## Risks

SSE plumbing with the existing job manager needs care — the job manager must
flush tokens to the SSE stream without buffering the whole response. Test on
slow model runs.

---
*See [00_priorities.md](00_priorities.md) §3 item 0.4 for sequencing context.*
