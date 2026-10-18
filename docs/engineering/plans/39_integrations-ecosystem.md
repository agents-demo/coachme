# Integrations & Ecosystem

**Status:** not started
**Phase:** D8 — Platform
**Effort:** M–XL (varies per integration)
**Depends on:** varies per integration; most need accounts (D2)
**Competitor ref:** Hudl/Veo

## Goal

Calendar and coach tools, wearables (HR/IMU), Apple Health, Strava-style
activity export. Each is a separate adapter.

## Where it lives

`integrations/` — one adapter file per integration. Each is behind a config
toggle; none are mandatory dependencies.

## Acceptance

Per-integration acceptance criteria to be defined in sub-specs when each
integration is scheduled. High-level: each adapter is config-toggled, has no
impact on users who do not enable it, and handles auth-token expiry gracefully.

## Risks

API churn: third-party APIs change. Build each adapter with a clear contract
so it can be replaced without touching the core pipeline.

---
*See [00_priorities.md](00_priorities.md) §8 item D8 for sequencing context.*
