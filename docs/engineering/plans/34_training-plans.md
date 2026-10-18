# Personalized Training Plan + Memory

**Status:** not started
**Phase:** D3 — Platform
**Effort:** L
**Depends on:** report history; feedback loop (06_feedback-loop.md)
**Competitor ref:** Onform

## Goal

A weekly plan generated from report history: targeted drills, load targets,
and a progress review. The agent remembers past focuses and adapts the next
plan based on what was completed.

## Where it lives

- New `core/stages/plan/` — agentic strategy that reads session history and
  produces a plan.
- Store plans in `runtime/data/plans/`.
- gui2 — "Plan my week" action; checkable drill list; next week adapts.

## Acceptance

- "Plan my week" produces a plan referencing past issues and foci.
- Drills are checkable; completion is recorded.
- Next week's plan adapts based on check-off history.
- Every plan item cites evidence from the session history (no hallucinated
  recommendations).

## Risks

Grounding: the plan must cite real session evidence — not invent drills that
were never suggested in any report. Hallucination in plan generation is a
trust-breaking failure.

---
*See [00_priorities.md](00_priorities.md) §8 item D3 for sequencing context.*
