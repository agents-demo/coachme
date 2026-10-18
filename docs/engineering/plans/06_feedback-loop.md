# Feedback Loop (Thumbs / Corrections)

**Status:** not started
**Phase:** 0.3 — Foundations
**Effort:** S
**Depends on:** nothing

## Goal

Capture per-issue 👍/👎 and "this is wrong" corrections; store them; use them
to guide prompt improvements over time.

## Where it lives

- Report schema gains a `feedback[]` array.
- New route: `POST /reports/{stem}/feedback`.
- Small thumbs UI on each issue card in gui2.
- A `tools/` developer view lists disagreements grouped by prompt version.

## Acceptance

- Feedback persists across app restarts.
- The `tools/` view shows disagreements per prompt version.
- Prompt changes reference the feedback that motivated them.

## Risks

Building the loop is easy. Acting on it — actually reviewing disagreements and
updating prompts — is the real work. Plan for a regular review cadence, not a
one-time build.

---
*See [00_priorities.md](00_priorities.md) §3 item 0.3 for sequencing context.*
