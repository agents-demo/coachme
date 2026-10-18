# Pro / Reference Comparison

**Status:** not started
**Phase:** B5 — Core review experience
**Effort:** M
**Depends on:** overlay compare (B4 / 11_overlay-compare.md); phase model in domain/
**Competitor ref:** Onform, V1 Sports

## Goal

Compare your motion to a reference — a pro template or your own best session
— as an overlay or side-by-side, aligned by stroke phase (backswing / contact /
follow-through).

## Where it lives

- `surfaces/gui2/client/` — phase-aligned playback (build on B4).
- `domain/` — a phase model that identifies stroke phases so two clips can be
  aligned at the equivalent moment.

## Acceptance

- User picks a reference session or template.
- Comparison shown phase-aligned at the contact point.

## Risks

- Reference licensing: any bundled pro template needs explicit rights clearance.
- Phase alignment robustness — depends on stroke segmentation (M3) being
  reliable enough for reliable phase detection.

---
*See [00_priorities.md](00_priorities.md) §5 item B5 for sequencing context.*
