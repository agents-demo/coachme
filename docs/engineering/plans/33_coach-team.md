# Coach / Team Layer

**Status:** not started
**Phase:** D2 — Platform
**Effort:** XL
**Depends on:** deployment/auth (10_deployment-ops.md); treat as a separate product line
**Competitor ref:** Hudl/Veo, Onform
**Go/no-go gate:** coach/team pilot with ≥N coaches retained 4 weeks; else park

## Goal

Accounts, roster management, session assignment to athletes, coach annotations
and comments, shared library, playlists.

## Where it lives

- New auth system (extend from 10_deployment-ops.md minimal auth).
- Multi-tenant store in `integrations/storage/`.
- New gui2 routes and pages: roster, session assignment, comments.
- Notification system (push or email).

## Acceptance

- A coach can see an athlete's sessions.
- Comments persist and appear in the session.
- Share links work and are scoped to the team.
- Auth and data model are secure and team-scoped.

## Risks

Auth/security scope — do not build a full user-management system in one go.
Treat as a separate product line with its own planning cycle. Start with a
pilot of 2–3 coaches before full build.

---
*See [00_priorities.md](00_priorities.md) §8 item D2 for sequencing context.*
