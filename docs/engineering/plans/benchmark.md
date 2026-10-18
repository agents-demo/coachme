# Benchmark Plan: Standard vs Investigator

**Role:** shared benchmark and release gates. Use this to decide whether Investigator is ready.

**Status:** implementation spec — clips, coach labels and harness still to be built
**Scope:** shared evaluation for Standard, Guided and Investigator
**Owner:** engineering owns the harness; a coach/analyst owns ground-truth labels

This is separate from the Investigator implementation plan because it evaluates
the product against the reliable baseline, not just whether the agent code runs.

---

# Part I — Protocol

## 1. What the benchmark must answer

1. Does Investigator find real coaching issues that Standard misses?
2. Are its findings supported by the evidence it cites?
3. Does it admit what it did not examine?
4. Is the quality gain worth the extra cost and latency?
5. Does it produce different investigation paths across different clips?

It does **not** score whether the agent followed a “correct” path. There is no
single correct path; there is evidence support and coaching value.

## 1.1 Benchmark modes

| Benchmark name | Code strategy | Role |
|---|---|---|
| **Standard** | `deterministic` | Baseline; always scored |
| **Guided** | `agentic` | Optional diagnostic; not part of the release gate |
| **Investigator** | `investigator` | Candidate; scored against Standard |

The runner uses the benchmark names; the adapter maps them to code names. Do not
invent a fourth name.

## 2. Dataset

The first released benchmark uses **8 clips**. The schema supports any number;
more clips do not require a code change.

Do not wait for all 8 clips before building the harness. Use **3 pilot clips**
to implement and test the runner, scorer and UI; mark that run `pilot` and do not
apply release gates. Expand to the full 8 before a release decision.

### 2.1 How to acquire the clips

The fastest reliable path is one recording session:

- record a player or coach with a phone on a tripod, side-on, 1080p, 6-20 seconds
  per clip;
- capture the eight slot types in one 30-45 minute session;
- get written consent before recording, including external model processing;
- keep the original files outside git and record checksums in the manifest.

Public footage is a fallback, not the default. Candidate sources include UCF101
(`TableTennisShot`), Roboflow Universe table-tennis datasets and Kaggle
table-tennis datasets. Check each licence: many are research-only, and a public
video is not the same as consent for model processing. Record `source` and
licence in the manifest; manually label every selected clip.

`demo/Michael-Osher.mp4` may be used for a smoke test only when its rights allow
it. It is not a benchmark clip and cannot support a release gate.

| Slot | Clip type | Purpose |
|---|---|---|
| 1 | Table tennis, clean side-on | Baseline quality |
| 2 | Table tennis, two players | Subject-selection / distraction |
| 3 | Table tennis, overhead | Geometry and tracking |
| 4 | Table tennis, poor lighting | Robustness |
| 5 | Tennis or badminton, clean | Transfer check |
| 6 | Tennis or badminton, difficult | Transfer robustness |
| 7 | Stroke-type switch mid-clip | Adaptive investigation |
| 8 | Still photo | Static posture path |

At least one clip must be an **adversarial / zero-finding** case (for example a
still with no correctable issue, or a clip where the honest answer is "nothing
supported"). This protects against a mode that always invents findings.

Rules:

- keep clips short (ideally 6–20 seconds);
- use real footage, not synthetic clips;
- store large clips outside git or use a downloadable fixture with checksums;
- record consent and retention rules before uploading personal video;
- do not train on benchmark clips without explicit opt-in.

## 3. Manifest

See §12 for the exact schema. Each clip has an ID, path, sport, duration, capture
notes, consent record and checksum.

## 4. Coach labels

A coach/analyst watches each clip and records the **ground truth**, not a review
of an AI report.

Rules:

- label the reportable coaching findings, up to five per clip;
- every video finding needs at least one timestamp; a still may use `0`;
- use the fixed theme set in §13;
- mark which evidence type is required to support the finding;
- write what a good report may legitimately leave unassessed;
- do not read AI reports before labeling;
- record the labeler and adjudication.

The exact schema is §13.

## 5. Blind A/B protocol

For each clip, generate Standard and Investigator reports. Redact mode names and
evidence IDs, then present them as A and B.

A coach rates each report:

| Question | Scale |
|---|---|
| Are the findings specific and actionable? | 1-5 (5 = excellent) |
| Are they supported by the clip? | 1-5 (5 = fully supported) |
| Is anything important missing? | 1-5 (5 = nothing important missing) |
| Is the report clear about what it did not assess? | 1-5 (5 = very clear) |
| Would you use this before a lesson? | yes/no |
| Which report is better? | A / B / tie |

Two coaches per clip is the minimum. The builder of the system must not be the
only rater.

## 6. Metrics

- **Evidence integrity (Investigator only):** issues with a valid evidence ID,
  cited non-overview window and timestamp / all Investigator issues.
- **Finding precision / recall:** matched against coach labels using §17. For still clips, theme matching is used and the timestamp rule is waived.
- **Coverage honesty:** false coverage flags and missing “not assessed” statements.
- **Hallucination flags:** scan with `domain/evaluate.py`, then review. Do not count a
  limitation or a correctly labelled measured value as a hallucination. Compare
  Standard and Investigator on the same reviewed definition.
- **Cost:** median and p95 tokens, tool seconds and frame decodes.
- **Latency:** median and p95 per clip, recorded with the environment name.
- **Path diversity:** unique normalized Investigator tool sequences.
- **Partial report rate:** partial reports / Investigator runs.
- **Failure rate:** crashed or invalid runs / all runs; an invalid run has no parsable report.

## 7. Release gates

Investigator stays opt-in until all gates pass:

| Gate | Threshold |
|---|---|
| Evidence integrity | 100% |
| Precision | >= Standard - 5 percentage points |
| Recall | >= Standard on labelled findings |
| Median cost | <= 2.5x Standard |
| p95 latency | <= 2x Standard in the same environment; release requires production |
| Coverage honesty | >= 90% of Investigator reports |
| Hallucination flags | No increase over Standard |
| Coach preference | >= 60% of non-tie clip votes prefer Investigator |
| Path diversity | >= 3 distinct tool sequences |
| Partial report rate | <= 10% of Investigator runs |
| Failure rate | 0 crashes on the benchmark |

If a gate fails, keep the mode opt-in, narrow it, or stop. Do not tune the
benchmark to make the mode look finished.

## 8. Reproducibility

For every run, store:

- manifest and label versions + checksums;
- prompt and toolset versions;
- model names and provider;
- budget settings;
- environment name (local / staging / production);
- per-clip reports and traces;
- blind mapping and ratings;
- score output.

## 9. Ownership and sequence

1. Engineering creates the manifest, label schema and harness.
2. Coach/analyst labels the clips without seeing AI reports.
3. Engineering runs Standard and Investigator.
4. Coaches rate blinded A/B packets.
5. Engineering computes metrics and writes the gate report.
6. Product decides: keep opt-in, narrow, or graduate.

Label acquisition is a 1–2 week dependency, not an Investigator coding task.

---

# Part II — Implementation specification

## 10. Deliverables

| Deliverable | Purpose |
|---|---|
| `topspin_review/benchmark/` | Installable runner, scorer, schemas and CLI |
| `topspin-benchmark` | `run`, `score`, `ui` and `import` commands |
| `manifest.json` | Clips, metadata, consent, checksums |
| `labels.json` | Coach ground truth |
| `rating_sheet.csv` | Blind coach ratings |
| `runs/<run_id>/` | Reports, traces, ratings, score, summary |
| Benchmark UI | Local review, labelling, blind rating and adjudication surface |

This is a real benchmark subsystem, not a test fixture. Unit tests live under
`tests/benchmark/`; benchmark data and generated runs live outside the package.

The GUI is required for normal operation and is specified in
[Benchmark Review UI](benchmark-ui.md). It is a local-only FastAPI + SvelteKit
application. There is no production multi-tenant service, database or auth in
v1; do not confuse the benchmark UI with `surfaces/gui2`.

## 11. File layout

```text
topspin_review/benchmark/
  __init__.py
  cli.py                    # run, score, ui, import
  runner.py
  scorer.py
  schemas.py
  matching.py
  paths.py
  ui/
    server/
    client/

benchmark/                  # default TOPSPIN_BENCHMARK_DATA
  README.md
  manifest.json
  labels.json
  clips/                    # external fixture paths are allowed
  runs/
    <run_id>/
      run.json
      runner.log
      mapping.json          # hidden from raters
      ratings/<rater>.json
      blind/<clip_id>/{A.json,B.json}
      raw/<mode>/<clip_id>.json
      traces/<mode>/<clip_id>.json
      score.json
      report.md

tests/benchmark/            # unit and API tests only
```

## 12. Manifest schema v1

```json
{
  "version": 1,
  "fixture_root": "clips",
  "clips": [
    {
      "id": "tt-clean-01",
      "path": "tt-clean-01.mp4",
      "media_type": "video",
      "sport": "table tennis",
      "duration_s": 10.4,
      "capture": "side-on, phone, tripod",
      "notes": "one player, forehand drill",
      "split": "benchmark",
      "fps": 30,
      "resolution": [1920, 1080],
      "people": ["participant-1"],
      "source": "recorded-for-benchmark",
      "license": "internal-benchmark",
      "consent": {
        "granted": true,
        "scope": "internal benchmark + model API processing",
        "by": "participant-or-guardian",
        "date": "2026-10-18",
        "expires": "2027-10-18",
        "retention_days": 365
      },
      "sha256": "..."
    }
  ]
}
```

Validation:

- unique `id`; safe ID (letters, digits, `-`, `_`);
- `path` resolves under `fixture_root`;
- `consent.granted` must be true and not expired;
- `people` must list every identifiable person; each person needs consent;
- `source` and `license` are required; public footage must identify its dataset;
- for more than one person, use a `consents` array with one record per person;
- `media_type` is `video` or `still`; `split` is `benchmark` or `holdout`;
- `duration_s > 0` for video; stills use `0`;
- `sha256` is required for benchmark clips;
- adding clips does not require a schema change.

## 13. Labels schema v1

```json
{
  "version": 1,
  "labelers": [{"name": "coach-a", "labeled_at": "2026-10-18"}],
  "adjudication": {"by": "coach-b", "date": "2026-10-18", "notes": ""},
  "clips": {
    "tt-clean-01": {
      "acceptable_limitations": ["ball placement not assessed"],
      "zero_finding_reason": "",
      "findings": [
        {
          "id": "f1",
          "text": "Contact point is late and the elbow drops on the backswing",
          "themes": ["stroke", "preparation"],
          "evidence_times": [2.8, 4.1],
          "severity": "high",
          "required_evidence": ["pose", "vision"]
        }
      ]
    }
  }
}
```

Rules:

- allowed themes: `footwork`, `stroke`, `preparation`, `recovery`, `serve`, `other`;
- a finding may have more than one theme;
- `required_evidence` is a subset of `motion`, `pose`, `ball`, `vision`; `ball`
  is invalid in the MVP because no ball tool exists;
- label all findings a coach would put in a report, up to five;
- `severity` is `low`, `medium` or `high`;
- a clip may have zero findings only with a non-empty `zero_finding_reason`;
- record the labeler and adjudication; two labelers are preferred for the first set.

## 14. Report normalization contract

The scorer cannot read raw report shapes directly. It must normalize them.

For each report issue:

```python
{
    "clip_id": clip_id,
    "text": str(issue.get("issue", "")).strip(),
    "themes": sorted(progress.classify(str(issue.get("issue", "")))) or ["other"],
    "times": issue.get("evidence_times") or [],
    "evidence_ids": issue.get("evidence_ids") or [],
    "confidence": issue.get("confidence", "low"),
}
```

Rules:

- `theme` is derived with `domain.progress.classify`; if it returns none, use `["other"]`;
- a report issue with `other` can match only a label explicitly marked `other`; `other` is a fallback, not a normal coaching theme;
- Standard and Investigator use the same normalizer;
- evidence-type support is checked only for Investigator, because Standard does
  not emit evidence IDs.

## 15. Runner contract

**Prerequisite:** the runner must use an isolated data root. It must not write into
the user’s `runtime/data` or use the demo-cache fallback. Before implementing the
runner, add a `TOPSPIN_DATA_DIR` override (used by `runtime.py` and `store.py`) or
run inside a disposable container. Until that exists, cost, latency and report
paths are not trustworthy. Use a fresh cache per run and `DEMO_FALLBACK=false`.

CLI:

```text
topspin-benchmark run \
  --manifest benchmark/manifest.json \
  --out benchmark/runs/<run_id> \
  --modes standard,guided,investigator
```

The local review UI is launched with:

```text
topspin-benchmark ui --data benchmark --port 8765
```

Behavior:

- create a filesystem-safe `run_id`;
- map `standard -> deterministic`, `guided -> agentic`, `investigator -> investigator`;
- run each clip sequentially in a subprocess:
  `python -m topspin_review.surfaces.cli analyze <clip> --mode <strategy>`;
- write raw reports under `raw/<mode>/<clip_id>.json`;
- write `traces/<mode>/<clip_id>.json` with evidence records, tool sequence, budget
  and timings; Standard trace may be report-only;
- write `run.json` with versions, models, budgets, environment, `config_hash` and status;
- fail the clip, not the whole run, on analysis errors; record `status: failed`;
- `--fail-fast` is optional;
- `--resume` skips clips with a valid JSON output and a matching `config_hash`
  covering manifest, labels, prompts, models, budgets and code revision.

Trace schema (`traces/<mode>/<clip_id>.json`):

```json
{
  "mode": "investigator",
  "clip_id": "tt-clean-01",
  "tool_sequence": ["get_overview", "look", "estimate_pose"],
  "evidence": [{"id": "ev_0001", "tool": "look", "window": [2.0, 3.0]}],
  "budget": {"tool_calls": 3, "frames": 22, "tokens": 12000, "seconds": 18.2},
  "status": "complete"
}
```

Standard may store `tool_sequence: []` and no evidence records, but must still
store cost/latency from usage. A partial report is `status: "partial"`; a run with
no parsable report is `status: "failed"`.

Exit codes:

- `0` all requested clips completed;
- `2` input/validation error;
- `3` one or more analysis failures.

## 16. Blind packet and ratings

- For each clip, write `blind/<clip_id>/A.json` and `B.json`.
- Remove `mode`, `evidence`, `investigation`, `evidence_ids`, trace paths and
  file names from the packet; both A and B must have identical normalized keys.
- Keep timestamps, findings, confidence and limitations only.
- Store the A/B mapping separately in `mapping.json`.
- Shuffle A/B per clip with a recorded seed; randomize presentation order and
  counterbalance across raters.
- Store blind packets in a separate directory from `mapping.json` and raw reports.
- Raters see only the blind packet and `rating_sheet.csv`; label and mapping access
  is separate.

Rating CSV columns:

```text
clip_id,rater,A_specific,A_supported,A_complete,A_honest,A_use,B_specific,B_supported,B_complete,B_honest,B_use,preferred,adjudicated_preference,rationale,notes
```

- `A_use` / `B_use`: `yes` or `no`.
- `preferred`: `A`, `B` or `tie`.
- Two raters minimum; record each separately.
- Record agreement rate and adjudication; missing votes do not count toward the
  preference denominator.
- If raters disagree on preference, use `tie` unless an adjudicator decides.
- Clip vote: both raters agree -> that vote; disagreement -> `tie` unless adjudicated.
- Train raters on 1–2 anchor clips before the real set.

## 17. Matching and scoring

Matching is clip-local and one-to-one.

For still clips, match on theme only; timestamps may be `[0]` or absent.

1. Normalize all report issues (§14).
2. For each label finding and report finding, candidates need:
   - at least one shared theme;
   - at least one timestamp pair within ±1.5s;
   - for Investigator, at least one cited evidence record whose tool covers a
     required evidence type: `estimate_pose` → pose, `look` → vision,
     `measure_motion` → motion. `get_overview` is orientation evidence and never
     satisfies a required evidence type.
3. Score candidate pairs by absolute time distance, then lexicographic issue text
   (do not use self-reported confidence as a tie-break).
4. Use deterministic maximum-cardinality one-to-one matching (brute force is fine
   for <=5 labels and <=5 reported issues per clip); ties are resolved by the same
   score order.
5. Unmatched label = false negative; unmatched report issue = false positive.
6. Freeze the theme-classifier version in `run.json`; manually audit a 20% sample
   of matched pairs for theme correctness.

Metrics:

- **Precision** = TP / (TP + FP); if there are no reported issues, precision is
  `0` when labels exist and `1` when the clip has no labels.
- **Recall** = TP / (TP + FN); if there are no labels, recall is `1` when there
  are no reported issues and `0` otherwise.
- Do not exclude zero-denominator clips from the pooled values. Every clip is
  included so a mode cannot hide a silent failure by reporting nothing.
- **Evidence integrity** = valid Investigator issues / all Investigator issues
- **Coverage honesty** = Investigator reports with no false coverage and required
  untested statements / all Investigator reports; gate >=90%
- **Hallucination flags** = reviewed count and rate from `domain/evaluate.py`;
  exclude legitimate limitations and measured values
- **Cost** = median/p95 tokens, tool seconds, frames
- **Latency** = median/p95 seconds; record environment
- **Path diversity** = unique normalized Investigator tool-name sequences from
  the final successful attempt per clip; normalize by dropping consecutive
  duplicates
- **Partial report rate** = partial / Investigator runs; a run is partial when
  `investigation.stop_reason` is anything other than `evidence_sufficient`
- **Failure rate** = crashed/invalid / all runs

Report pooled and per-clip precision/recall. Pooled values are micro-averaged
over all clips; Standard and Investigator are evaluated on the same clip set.
Pooled values drive the gates.

## 18. Score output

`score.json`:

```json
{
  "version": 1,
  "run_id": "...",
  "clips": 8,
  "environment": "local",
  "config_hash": "...",
  "standard": {"precision": 0.0, "recall": 0.0, "cost_median": 0, "latency_p95": 0, "hallucination_rate": 0.0},
  "investigator": {
    "precision": 0.0,
    "recall": 0.0,
    "evidence_integrity": 0.0,
    "coverage_honesty": 0.0,
    "hallucination_rate": 0.0,
    "cost_median": 0,
    "latency_p95": 0,
    "path_diversity": 0,
    "partial_rate": 0.0,
    "failure_rate": 0.0
  },
  "coach": {"investigator": 0, "standard": 0, "ties": 0, "agreement": 0.0},
  "hallucination_rate": 0.0,
  "gates": {
    "evidence_integrity": true,
    "coverage_honesty": true,
    "precision": true,
    "recall": true,
    "cost": true,
    "latency": true,
    "hallucination": true,
    "coach_preference": true,
    "path_diversity": true,
    "partial_rate": true,
    "failure_rate": true
  },
  "pass": false
}
```

`report.md` is the human summary: gates, per-clip results and failures.

Guided is diagnostic only and may be omitted from `score.json`. A local or staging
run records `environment` and may compute latency, but the latency gate can pass
only for a production run.

## 19. Privacy and data handling

- consent must be person-level, including every identifiable player; a parent or
  guardian consents for a minor;
- no PII in labels or run metadata;
- consent must name external model providers/subprocessors, region and training
  policy; provider-side retention/deletion must be confirmed;
- clips stay outside git unless explicitly shareable;
- retention covers clips, frames, reports, traces, blind packets, ratings and
  backups; delete derived artifacts with the clip;
- consent withdrawal removes the clip and its derived artifacts, with a deletion
  manifest recording what was removed;
- raters see only blind packets; labels and mapping are access-controlled;
- redact names/PII from file paths, labels and rater notes;
- no training on benchmark clips without explicit opt-in;
- delete local copies when the benchmark is retired.

## 20. Implementation backlog

| # | Task | Acceptance |
|---|---|---|
| 1 | Isolated data root (`TOPSPIN_DATA_DIR` or container) | benchmark never writes to user runtime |
| 2 | Manifest schema + validator | invalid manifest fails clearly |
| 3 | Label schema + validator | invalid theme/time/consent fails |
| 4 | Report normalizer | Standard and Investigator share one finding shape |
| 5 | Runner | 8 clips × requested modes; failures isolated; resume works |
| 6 | Blind packet + mapping | mode/evidence IDs removed; mapping hidden |
| 7 | Rating import | two raters; ties; per-clip votes |
| 8 | Scoring | precision/recall/evidence/cost/latency/path/partial |
| 9 | Gate report | complete `score.json` + `report.md` |
| 10 | Tests | matching, ties, missing evidence, empty labels, failures |
| 11 | Benchmark UI | run list/dashboard, clip review, labels, blind rating, adjudication and export; see [Benchmark Review UI](benchmark-ui.md) |

## 21. Definition of done

- 8 clips and labels exist;
- one command runs Standard and Investigator into an isolated run directory;
- the local UI can launch/cancel runs, review clips, label findings, collect
  blind ratings, adjudicate and export results;
- two coaches rate blind packets;
- scoring produces all gates and a human report;
- UI and CLI produce the same score and report files;
- results are reproducible from manifest, labels and run metadata.
