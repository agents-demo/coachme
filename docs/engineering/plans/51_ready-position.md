# Ready-Position Quality Score

**Status:** not started
**Phase:** B.5 / A6 — Pipeline analytics
**Effort:** S
**Depends on:** dense pose between strokes; player-specific thresholds

## Goal

Fraction of inter-stroke frames meeting ready criteria (stance width, knee
flex, hands near hips). Output 0–100% plus the worst moments as evidence.

## Where it lives

`core/stages/measure/` — dense pose between stroke windows; configurable
thresholds per sport/level.

## Acceptance

- Score moves in the expected direction on a before/after clip.
- Thresholds exposed in settings or learned from a player baseline — not
  hard-coded.

## Risks

Criteria differ by sport and level. Expose thresholds or learn a per-player
baseline. Flag as "sport-default" when using generic values.

---
*Full technical detail in [45_analysis-pipeline-research.md](45_analysis-pipeline-research.md) §2 A6.*
