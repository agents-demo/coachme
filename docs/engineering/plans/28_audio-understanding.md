# Audio Understanding (Listen)

**Status:** not started
**Phase:** C10 — Analysis depth
**Effort:** M
**Depends on:** nothing; opt-in, must be privacy-safe

## Goal

Add audio to the multimodal layer — a coach's spoken notes or racket/ball
impact sounds as additional evidence. The pipeline adds *listening* to its
existing watch + read + write + speak senses.

## Where it lives

- `integrations/` — new audio → text step (speech model, e.g. Whisper).
- `core/stages/observe/` — feed the audio transcript into the reasoning
  context alongside the video.
- Report gains an `audio{}` block with the transcript excerpt and findings
  that cite it.

## Acceptance

- A clip with a coach's spoken notes produces findings that cite the audio.
- Audio processing is opt-in and labelled in the report.
- No audio leaves the machine unless sharing is on.

## Risks

- Transcription quality on noisy court environments.
- Privacy: audio of a coaching session may capture third-party voices — require
  explicit consent for audio processing, separate from video consent.

---
*See [00_priorities.md](00_priorities.md) §7 item C10 for sequencing context.*
