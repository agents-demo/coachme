# 3D Biomechanics — Kinematic Sequence

**Status:** not started
**Phase:** C8 — Analysis depth
**Effort:** L
**Depends on:** 3D world landmarks from MediaPipe pose; needs a clean side view for accuracy
**Competitor ref:** Sportsbox AI (their core product)

## Goal

Joint-by-joint kinematic sequence (hips → torso → shoulder → arm) and phase
timing (backswing, contact, follow-through) per stroke.

## Where it lives

- `core/video/` — kinematic sequence computation from 3D pose world landmarks.
- `integrations/pose.py` — enable 3D world landmark output if not already on.
- Report gains `biomechanics{}` block per stroke.

## Acceptance

- Kinematic sequence and phase timing reported per stroke with confidence.
- Degrades gracefully without 3D landmarks (side-view requirement noted to
  the user).

## Risks

Monocular 3D accuracy — MediaPipe world landmarks are estimates, not
ground-truth. Label confidence ranges clearly; do not present them as
measured angles.

---
*See [00_priorities.md](00_priorities.md) §7 item C8 for sequencing context.*
