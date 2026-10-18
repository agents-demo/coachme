# Multi-Player / Court-Role Attribution

**Status:** not started
**Phase:** C4 — Analysis depth
**Effort:** L
**Depends on:** person detection (I1 / 17_person-segmentation.md)
**Competitor ref:** Hudl/Veo, SwingVision

## Goal

Detect and separate multiple people in the frame (near player / far player);
attribute metrics per player; address only the selected player in the coaching
report.

## Where it lives

- `core/video/` — player tracking + role attribution (near/far, left/right).
- Report gains `players[]` with per-player metrics.
- UI: player selector before or after analysis.

## Acceptance

- Two players tracked; metrics correctly attributed per player.
- Report addresses the selected player only.
- Occlusion and player crossings handled without crashing.

## Risks

- Occlusion: players crossing in front of each other is the hard case.
- CPU cost of tracking two players simultaneously on device.

---
*See [00_priorities.md](00_priorities.md) §7 item C4 for sequencing context.*
