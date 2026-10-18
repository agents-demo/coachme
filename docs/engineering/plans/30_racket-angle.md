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

## Upgrade path: MediaPipe Hands (B8 from feasibility research)

MediaPipe Hands provides hand landmarks at stroke frames, constraining palm
orientation better than the forearm alone. Even so, grip and wrist
pronation/supination are not fully observable — it remains a proxy.

- Show as "estimated face tendency (open/closed)" with confidence, never an
  exact angle.
- Extra per-stroke compute: hands are often small or motion-blurred at 30 fps.
  Measure inference time before committing.

**Reliable alternative:** a visible marker on the blade or a racket IMU gives
true racket-face angle. Consider offering this as a premium calibration option.

---
*See [00_priorities.md](00_priorities.md) §8 item C12 for sequencing context.*
*Full feasibility detail: [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §3 B8.*
