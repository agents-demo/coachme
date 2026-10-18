# Eval Harness & Prompt Regression

**Status:** not started — stub
**Phase:** 0.1 — Foundations
**Effort:** M
**Depends on:** nothing (do first)

## Goal

A labelled clip benchmark and regression tests so issue quality and token cost
do not silently drift between releases.

## Acceptance

- `pytest -m eval` prints per-clip precision/recall vs labelled ground truth.
- CI fails when results drop below stored thresholds.
- A golden-report snapshot test locks the prompt output.

## Notes

This is a simpler, in-repo evaluation harness — not the full multi-coach blind
benchmark in [01_benchmark.md](01_benchmark.md). It lives in `tests/eval/` and
`tests/integration/evaluate_reports.py`.

---
*Full spec to be written. See [00_priorities.md](00_priorities.md) §3 item 0.1.*
