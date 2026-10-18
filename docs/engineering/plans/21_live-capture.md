# Real-Time / Live Capture with Instant Feedback

**Status:** not started
**Phase:** C3 — Analysis depth
**Effort:** XL
**Depends on:** C1, C2, reliable 3D pose
**Competitor ref:** HomeCourt, SwingVision, Onform

## Goal

Stream from the device camera; run on-device ball and pose detection; deliver
an instant audio or text cue (e.g. "split-step early", "too upright") within
1 second.

## Where it lives

- New mobile/desktop capture surface (separate from the existing upload flow).
- A low-latency loop: per-frame pose + ball, no full LLM pass per frame.
- Cue generation: rule-based or a small on-device model, not a full pipeline.

## Acceptance

- < 1s latency for a pose-based cue on a mid-range device.
- Graceful degradation when the device cannot maintain framerate (drops cues,
  not crashes).

## Risks

- Latency, battery, and platform permissions — all three are hard on mobile.
- This is the most complex item in the roadmap. Do not start until C1 and C2
  are stable.

---
*See [00_priorities.md](00_priorities.md) §7 item C3 for sequencing context.*
