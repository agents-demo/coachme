# iOS App

**Status:** not started
**Phase:** D1 — Platform
**Effort:** XL
**Depends on:** core/service.py + gui2 API (reused); Android app already shipped
**Competitor ref:** all competitors

## Goal

iOS capture + on-device pose (MediaPipe mobile) + upload-to-analyze + report
review on iPhone.

## Where it lives

- New iOS surface (separate from Android).
- Reuse `core/service.py` and the gui2 API — the analysis pipeline is the same.
- App Store build, distribution, and permissions.

## Acceptance

- Record → analyze → view a full report on iPhone.
- On-device pose runs without network.

## Risks

- App Store builds, native MediaPipe on iOS, and TestFlight/distribution are
  all non-trivial.
- iOS camera API differences vs Android.

---
*See [00_priorities.md](00_priorities.md) §8 item D1 for sequencing context.*
