# Deployment & Ops

**Status:** not started
**Phase:** 0.8 — Foundations
**Effort:** M
**Depends on:** nothing (auth should be kept minimal at first — behind a flag)

## Goal

Make gui2 safely hostable beyond a developer laptop: optional auth + HTTPS,
a Dockerfile, CORS tightening, structured logs with run IDs, error tracking,
and a health/ready endpoint for orchestration.

## Where it lives

- `Dockerfile` at the repo root.
- `surfaces/gui2/server/app.py` — CORS headers, health endpoint (`/health`,
  `/ready`).
- Auth: optional middleware (keep behind a feature flag; do not make it
  mandatory for local use).
- Structured logs: replace `print` / bare `logging` with structured log calls
  that include `run_id`.
- Error tracking: integrate Sentry or equivalent, gated by `SENTRY_DSN`.

## Acceptance

- `docker build && docker run` starts the app on a clean machine.
- The app is auth-gated when `AUTH_ENABLED=true`.
- All errors surface with a run ID.

## Risks

Auth scope creep — keep the implementation minimal (HTTP Basic or a single
bearer token) and do not build a full user-management system here. Full auth
is part of the coach/team layer (D2).

---
*See [00_priorities.md](00_priorities.md) §3 item 0.8 for sequencing context.*
