# Privacy & Compliance

**Status:** not started
**Phase:** 0.7 — Foundations
**Effort:** S–M
**Depends on:** nothing

## Goal

Be explicit that video of a person is sensitive. Consent on the Analyze screen,
configurable data retention with auto-prune, and local-first as the enforced
default (sharing is opt-in).

## Where it lives

- `core/config.py` — add `RETENTION_DAYS`; auto-prune on `runtime.setup()`.
- `surfaces/gui2/client/` — consent line on the Analyze screen.
- A short data-handling doc (internal, for the team + future compliance audits).

## Acceptance

- Retention prunes clips and reports older than `RETENTION_DAYS` automatically.
- Consent is recorded before any analysis starts.
- No frames leave the machine unless sharing is explicitly on.

## Risks

No technical risks. Policy: ensure the consent text names external model
providers/subprocessors and the region. Check with legal before any
public launch.

---
*See [00_priorities.md](00_priorities.md) §3 item 0.7 for sequencing context.*
