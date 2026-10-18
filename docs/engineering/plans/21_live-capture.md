# Real-Time / Live Capture with Instant Feedback

**Status:** not started — stub
**Phase:** C3 — Analysis depth
**Effort:** XL
**Depends on:** C1, C2, 3D pose
**Competitor ref:** HomeCourt, SwingVision, Onform

## Goal

Stream from the device camera; run on-device ball and pose detection; deliver
an instant audio or text cue (e.g. "split-step", "too upright") within 1 second.

## Acceptance

- < 1s feedback latency for a pose-based cue.
- Graceful degradation when the device cannot maintain framerate.

---
*Full spec to be written. See [00_priorities.md](00_priorities.md) §7 item C3.*
