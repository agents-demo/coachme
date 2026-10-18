# Real-Time Audio Coaching (Playback Mode)

**Status:** not started
**Phase:** D7 — Platform
**Effort:** M
**Depends on:** voice-over + issue timeline (already shipped)
**Competitor ref:** HomeCourt, Onform

## Goal

During report review, an audio cue track aligned to the timeline — the app
speaks the coaching finding at the relevant timestamp (e.g. "here — split-step
early").

## Where it lives

- gui2 — TTS call per finding, triggered at the finding's evidence timestamp
  during playback.
- Android — same via the existing TTS integration.
- Toggle on/off; does not auto-play.

## Acceptance

- Toggle plays coaching cues at evidence timestamps during clip review.
- Works on both web and Android.
- Does not auto-play; user controls it.

## Risks

None serious. TTS latency on web may introduce a small delay relative to the
video — pre-generate audio on report creation if needed.

---
*See [00_priorities.md](00_priorities.md) §8 item D7 for sequencing context.*
