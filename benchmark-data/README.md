# CoachMe benchmark data root

This directory holds the benchmark harness inputs and generated runs. Real
clips, manifests, labels, ratings and runs are **local only** and ignored by git.

```text
benchmark-data/
  README.md
  manifest.example.json
  labels.example.json
  .gitignore
  manifest.json       # local, ignored
  labels.json         # local, ignored
  clips/              # local, ignored
  runs/               # local, ignored
  .auth/              # local accounts/session secret, ignored
  tenants/            # tenant-scoped data roots, ignored
```

`COACHME_BENCHMARK_DATA` overrides this root. Keep real clips outside the
repository when possible.

## Commands

```text
coachme-benchmark run --manifest benchmark-data/manifest.json --modes standard,investigator
coachme-benchmark run --manifest benchmark-data/manifest.json --modes standard --negative-control --out benchmark-data/runs/negative
coachme-benchmark score --run benchmark-data/runs/<run_id>
coachme-benchmark import --run benchmark-data/runs/<run_id> --rater coach-a --file coach-a.csv
coachme-benchmark packets --run benchmark-data/runs/<run_id> --raters coach-a,coach-b --out packets.zip
coachme-benchmark evidence-review --run benchmark-data/runs/<run_id> --out evidence.csv
coachme-benchmark evidence-import --run benchmark-data/runs/<run_id> --file evidence.csv --reviewer coach-a
coachme-benchmark tool-review --run benchmark-data/runs/<run_id> --out tools.csv
coachme-benchmark tool-import --run benchmark-data/runs/<run_id> --file tools.csv --reviewer coach-a
coachme-benchmark hallucination-review --run benchmark-data/runs/<run_id> --out hallucinations.csv
coachme-benchmark hallucination-import --run benchmark-data/runs/<run_id> --file hallucinations.csv --reviewer coach-a
coachme-benchmark negative-control --run benchmark-data/runs/<run_id> --out benchmark-data/runs/negative
coachme-benchmark stability --run benchmark-data/runs/<run_id> --against benchmark-data/runs/<other_run>
coachme-benchmark withdraw --manifest benchmark-data/manifest.json --clip tt-clean-01 --reason "consent withdrawn"
coachme-benchmark prune --manifest benchmark-data/manifest.json
coachme-benchmark ui --data benchmark --port 8765
```

The runner executes each clip in a subprocess with its own `COACHME_DATA_DIR`
under the run directory, disables demo fallback and uses a fresh cache. It never
writes analysis output into `runtime/data`.

## Current status

The CLI and full local review UI are implemented, including run control, labels,
blind rating, adjudication, rater packets, exports, negative control, manual
evidence/tool/hallucination review, stability, consent withdrawal and retention
pruning. The UI streams live progress over SSE; Playwright covers the real local
backend and serious/critical accessibility scans on every review screen. A
stripped-prompt negative-control analysis mode is also available. The real 3?8
clip labelled set remains.

A run with fewer than `--required-clips` (default 8), missing labels or missing
ratings is a pilot/diagnostic run: metrics are reported, but release gates are
blocked and `release_eligible` stays false.

## Privacy

- Do not commit personal clips, labels, ratings or run artifacts.
- Consent is person-level and must not be expired at run time.
- The local CLI can read `mapping.json`; true blind rating requires separate rater
  packets or a restricted machine. The UI states this limitation.

## Remote / multi-user

See [deploy/benchmark/README.md](../../deploy/benchmark/README.md) for accounts,
roles, tenant isolation, remote binding and Docker deployment.
