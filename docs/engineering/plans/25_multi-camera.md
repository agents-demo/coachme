# Multi-Camera / Dual-Angle

**Status:** not started
**Phase:** C7 — Analysis depth
**Effort:** L
**Depends on:** benefits from C1 and depth; sync needs audio or pose alignment
**Competitor ref:** Onform, V1 Sports (pro tools)

## Goal

Analyze two synced captures (front + side) together for better depth cues and
a more complete mechanical read than a single camera allows.

## Where it lives

- Multi-file submission flow in gui2.
- Sync by audio waveform correlation or pose-peak alignment.
- `core/video/` — fusion of two-angle features.
- Report notes which angle each finding came from.

## Acceptance

- Two clips submitted and synced automatically.
- Combined report uses both angles; depth-dependent findings improve.

## Risks

Sync robustness — audio sync fails for clips without distinct impact sounds;
pose sync may be unreliable on very short clips. Plan a manual offset fallback.

---
*See [00_priorities.md](00_priorities.md) §7 item C7 for sequencing context.*
