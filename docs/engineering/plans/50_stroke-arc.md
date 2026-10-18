# Backswing & Follow-Through Arc

**Status:** not started
**Phase:** B.5 / A5 — Pipeline analytics
**Effort:** S–M
**Depends on:** dense stroke window at 15–20 fps (without this, it is noise)

## Goal

Wrist path length and direction in the 0.3 s before and after each stroke.
Short backswing → weak stroke. Abbreviated follow-through → arm-stop.

## Where it lives

`core/video/` — numeric integration over dense wrist landmarks per stroke
window.

## Acceptance

- Arc length + direction per stroke.
- Omit if fewer than 3 frames captured in the window — no invented values.

## Risks

Wrist-speed peak is a proxy for contact, not the true contact instant. Arc
direction is approximate at 30 fps.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A5.*
