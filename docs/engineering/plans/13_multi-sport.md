# Multi-Sport Generalization

**Status:** not started
**Phase:** B6 — Core review experience
**Effort:** L
**Depends on:** solid table-tennis quality first — do not expand early

## Goal

Take the pipeline beyond table tennis to tennis, badminton, squash, and padel:
sport-aware prompts, coaching terms, and calibration references.

## Where it lives

- `domain/` — sport profiles with sport-specific terms and prompt snippets.
- `core/config.py` — sport selector.
- Prompts updated to switch on sport.

## Acceptance

- A tennis clip yields a sensible, sport-correct report through the same
  pipeline.
- Per-sport tuning does not degrade quality for the beachhead sport (table
  tennis).

## Risks

Per-sport prompt tuning is significant work. Resist going broad before one
sport is great — table tennis first.

---
*See [00_priorities.md](00_priorities.md) §5 item B6 for sequencing context.*
