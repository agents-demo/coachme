# Elbow Position at Contact

**Status:** not started
**Phase:** B.5 / A4 — Pipeline analytics
**Effort:** S
**Depends on:** 3D landmarks at the stroke frame (dense window)

## Goal

Elbow coordinates in a body frame (mid-shoulder/mid-hip origin) at the stroke
frame. A flared elbow is a common forehand inconsistency and a potential injury
risk.

## Where it lives

`core/video/` — rotate/translate existing 3D landmarks to a body frame; compare
elbow X against shoulder width at contact.

## Acceptance

- Flags only when outside a stated margin, with the contact frame shown.
- Never presented as a clinical measurement.

## Risks

World-landmark drift. Do not present as a precise angle — report as a relative
position (e.g. "elbow wider than shoulder by ~15%").

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A4.*
