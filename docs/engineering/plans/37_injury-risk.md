# Injury-Risk / Load Flags

**Status:** not started
**Phase:** D6 — Platform
**Effort:** L
**Depends on:** pose metrics; non-diagnostic disclaimer is mandatory
**Note:** regulatory / liability risk — never diagnostic

## Goal

Flag risky movement patterns (deep knee valgus, asymmetry, fatigue drift in
the last reps) with a "watch this" notice and the evidence that triggered it.

## Where it lives

- `core/video/` — derived metrics for knee alignment, bilateral asymmetry,
  per-rep velocity trend (fatigue proxy).
- Report: a `risk{}` block per flagged pattern with evidence and a disclaimer.

## Acceptance

- Risk flags shown with evidence and a clear "not medical advice" disclaimer.
- Not diagnostic — never uses clinical language.

## Risks

Regulatory / liability: any injury-risk feature that uses clinical language or
omits the disclaimer is a legal and trust risk. The disclaimer is non-optional.
Get legal review before any public launch of this feature.

---
*See [00_priorities.md](00_priorities.md) §8 item D6 for sequencing context.*
