# Hip → Shoulder Sequencing

**Status:** not started
**Phase:** B.5 / A3 — Pipeline analytics
**Effort:** S
**Depends on:** dense stroke window; Python pose entries already contain per-frame hip/shoulder twist

## Goal

Per-stroke relative timing of hip and shoulder twist peaks. Hips should lead
the shoulder — the kinetic chain for power transfer. Reports lead/lag in
seconds with a confidence label.

## Where it lives

- Server: per-frame `hip_twist` and `shoulder_twist` already in pose entries;
  use them directly on the dense stroke window.
- Android: compute the same angles from stored world landmarks.
- Output: `hip_leads` / `simultaneous` / `shoulder_leads` per stroke.

## Acceptance

- Classification with evidence frames cited.
- Requires the side view — note as limitation otherwise.

## Risks

Twist angles are noisy at monocular depth. Require the side view and state
confidence clearly.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A3.*
