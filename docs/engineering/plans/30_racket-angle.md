# Racket-Angle Proxy (Wrist / Forearm Orientation)

**Status:** not started
**Phase:** C12 — Table-tennis specific
**Effort:** M
**Depends on:** pose landmarks + ball direction + contact timing

## Goal

Estimate wrist/forearm orientation at contact as a coaching hint. This is a
proxy, not the racket face — pose models do not track the racket directly. The
"approximate" label must always be shown.

## Where it lives

- `core/video/` — derive forearm orientation from pose landmarks at the
  contact frame; combine with incoming/outgoing ball direction.
- Report: `strokes[].racket_angle_proxy` with an explicit "approximate" tag.

## Acceptance

- Proxy shown with a caveat that it is not a measured racket angle.
- Never presented as ground truth or precise measurement.

## Risks

Misleading if overclaimed. This must always show as "approximate" — if the UI
ever removes that label, the feature should be disabled.

---
*See [00_priorities.md](00_priorities.md) §8 item C12 for sequencing context.*
