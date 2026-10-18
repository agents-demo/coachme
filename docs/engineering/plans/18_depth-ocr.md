# Monocular Depth + Scoreboard OCR

**Status:** not started
**Phase:** B.5 / I4 + I5 — Integrations
**Effort:** L + S
**Depends on:** nothing (I4 assists calibration; I5 is independent)
**Build order:** fourth within Phase B.5 (lower priority than I1/I2)

## Goal

**I4 — Monocular depth (MiDaS):** rough depth/scale estimate to assist metric
calibration when no court or table anchor is detected.

**I5 — OCR:** read a scoreboard or scoreline from the video for match context
in the report.

## Where it lives

- I4: new `integrations/depth.py` using MiDaS; consumed by
  `core/video/metrics.py` calibration step (05_calibration.md).
- I5: new `integrations/ocr.py`; output fed into `core/stages/observe/`
  as context for the report.

## Acceptance

- I4: calibration can use the depth estimate when no table/court anchor is
  available; confidence noted in the report.
- I5: scoreline extracted and included in report context when legible; ignored
  when not legible (no hallucinated scores).

## Risks

- I4: MiDaS is a large model; test inference time on device before committing.
  Monocular depth is an approximation — label it as such.
- I5: OCR accuracy on scoreboards with motion blur. Never surface an uncertain
  read as confident.

---
*See [00_priorities.md](00_priorities.md) §6 items I4, I5 for sequencing context.*
