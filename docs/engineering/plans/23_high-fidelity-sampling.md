# Higher-Fidelity Analysis Inputs (Thorough Mode)

**Status:** not started
**Phase:** C5 — Analysis depth
**Effort:** M
**Depends on:** nothing; gated by config toggle

## Goal

Configurable higher frame sampling, multi-scale contact sheets, and a 60fps
burst around motion peaks for footwork analysis — opt-in, not the default.

## Where it lives

- `core/config.py` — `VISION_MAX_FRAMES`, `MAX_WIDTH`, thorough-mode toggle.
- `core/stages/measure/sampling.py` — extra burst logic.
- `core/stages/observe/` — multi-scale contact sheet generation.

## Acceptance

- Thorough mode doubles frames around motion peaks.
- Report notes that extra sampling was used.
- Token and latency cost increase is shown in Diagnostics.
- Default mode is unchanged.

## Risks

Token and latency cost roughly doubles. Must be clearly opt-in and must not
increase cost for users who did not enable it.

---
*See [00_priorities.md](00_priorities.md) §7 item C5 for sequencing context.*
