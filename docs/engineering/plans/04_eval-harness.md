# Eval Harness & Prompt Regression

**Status:** not started
**Phase:** 0.1 — Foundations
**Effort:** M
**Depends on:** nothing — do first; unblocks every quality gate

## Goal

A labelled clip benchmark and regression tests so issue quality and token cost
do not silently drift between releases.

## Where it lives

- Extend `tests/eval/expected.json` with per-clip expected issues and metrics.
- Add a graded suite to `tests/integration/evaluate_reports.py`.
- Add a `pytest` marker (`-m eval`) that runs it offline on shipped reports.

## Acceptance

- `pytest -m eval` prints per-clip precision/recall vs labelled ground truth.
- CI fails when results drop below stored thresholds.
- A golden-report snapshot test locks the prompt output.

## Risks

Label authoring needs a coach or very careful manual build. Plan for 1–2 days
of labelling before the harness is useful.

## Notes

This is a simpler, in-repo evaluation harness — not the full multi-coach blind
benchmark in [01_benchmark.md](01_benchmark.md). It lives in `tests/eval/` and
runs offline with no model calls (uses shipped reports as fixtures).

---
*See [00_priorities.md](00_priorities.md) §3 item 0.1 for sequencing context.*
