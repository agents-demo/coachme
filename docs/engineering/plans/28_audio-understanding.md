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

## Contact sound classification (B7 — experimental)

Beyond speech transcription, audio can classify racket/ball contact sounds:
crisp topspin, soft push/block, or smash. Timestamps come from stroke
segmentation; the classifier labels each contact.

**Reality check (from [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §3 B7):**
phone mic distance, compression artifacts, crowd noise, and rubber/blade
variation make classification unreliable in real sessions. A labelled training
set is required. Adds `scipy` or `librosa` as a new dependency.

**Acceptance for B7:** ship only as an optional, confidence-labelled evidence
channel in the `audio{}` block. Do not gate any other metric on it. Mark
findings as "audio hint — not measured." High false-positive rate is expected;
the user must see that caveat before enabling it.

## Risks

- Transcription quality on noisy court environments.
- Privacy: audio of a coaching session may capture third-party voices — require
  explicit consent for audio processing, separate from video consent.
- Contact classification (B7): high false-positive rate; do not enable by
  default. Gating behind a user opt-in and a clear label is non-negotiable.

---
*See [00_priorities.md](00_priorities.md) §7 item C10 for sequencing context.*
*Full pipeline feasibility: [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §3 B7.*
