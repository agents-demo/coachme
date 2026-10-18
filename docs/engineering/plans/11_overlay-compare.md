# Overlay Compare (Blend / Side-by-Side)

**Status:** not started
**Phase:** B4 — Core review experience
**Effort:** M
**Depends on:** existing compare slider
**Competitor ref:** Coach's Eye (CE), V1 Sports, Onform

## Goal

Beyond the basic slider: a 50% blend/onion-skin mode and a "ghost" overlay of
an earlier session, plus a synchronized dual scrubber.

## Where it lives

`surfaces/gui2/client/` — canvas compositing on top of the existing compare
slider component. No backend changes needed.

## Acceptance

- Slider ⇄ blend ⇄ side-by-side mode toggle.
- Synced playhead: both sessions play at the same normalized progress point.

## Risks

Performance of dual `<video>` + canvas compositing on low-end Android devices.
Test on the lowest-spec target device before shipping.

---
*See [00_priorities.md](00_priorities.md) §5 item B4 for sequencing context.*
