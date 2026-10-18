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

At least **two** clips must be **adversarial / zero-finding** cases (for example a
still with no correctable issue, a clip where the honest answer is "nothing
supported", or a clip with clearly poor quality where findings cannot be supported).
One zero-finding clip is not enough to detect a mode that invents findings; two
gives a small false-positive rate to track. Assign zero-finding slots to clips 7
and 8, or make one of the existing slots a zero-finding case.

A **false-positive rate on zero-finding clips** is reported separately: FP_zero = Investigator
issues reported on zero-finding clips / total zero-finding clips. This is not a hard gate in v1
but must be reported alongside precision and recall.

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
- record the labeler and adjudication;
- for slots 5 and 6 (tennis or badminton clips), the labeler must have coaching or playing
  experience in the relevant sport. A table-tennis coach is not qualified to label tennis
  mechanics; use a separate domain expert for those clips.

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
only rater. For transfer clips (slots 5, 6: tennis or badminton), at least one rater
must have domain-specific expertise in that sport. A table-tennis coach rating
tennis reports cannot assess mechanics accurately. Before computing the preference gate, verify that inter-rater agreement
on preference (A vs B vs tie) is at least 60% across non-tie clips, or that Cohen's κ > 0.4.
If agreement is below this threshold, add an adjudicator to resolve disagreements before
the gate is computed.

## 6. Metrics

- **Evidence integrity (Investigator only):** issues with (a) a valid evidence ID,
  (b) a cited non-overview window, (c) a timestamp, **and (d) a window that semantically
  encompasses the described finding** — verified by manual spot-check of at least 20% of
  matched Investigator findings. Purely structural validity (ID present, window non-empty)
  is necessary but not sufficient; a finding that cites a valid window for the wrong moment
  fails integrity.
- **Finding precision / recall:** matched against coach labels using §17. For still clips, theme matching is used and the timestamp rule is waived.
- **Coverage honesty:** false coverage flags and missing “not assessed” statements.
- **Hallucination flags:** a **hallucination** is a specific factual claim (angle, timestamp,
  observation about a body part, ball trajectory, or player behaviour) that is not supported
  by any cited evidence record or by coach-labelled ground truth. Limitations, confidence
  caveats, and correctly labelled measured values are **not** hallucinations. Scan with
  `domain/evaluate.py`, then manually review every flagged item against the clip and evidence
  records. Compare Standard and Investigator on the same reviewed definition and the same
  reviewer.
- **Cost:** median and p95 tokens, tool seconds and frame decodes.
- **Latency:** median and p95 per clip, recorded with the environment name.
- **Path diversity:** unique normalized Investigator tool sequences. Path diversity is a
  proxy, not a quality gate by itself — three diverse but inappropriate sequences are not
  better than one appropriate one. Pair path diversity with a 20% spot-check of
  tool-appropriateness: did the tools called match what the cited evidence required?
- **Partial report rate:** partial reports / Investigator runs.
- **Failure rate:** crashed or invalid runs / all runs; an invalid run has no parsable report.
- **FP rate on zero-finding clips:** Investigator issues reported on zero-finding clips /
  total zero-finding clips (also computed for Standard). Not a hard gate in v1; reported
  for diagnostic purposes. A mode that invents findings on zero-finding clips warrants
  immediate investigation regardless of overall precision.

## 7. Release gates

Investigator stays opt-in until all gates pass.

A gate can pass only when the evidence set is complete:

- the released set has all 8 clips;
- every clip has a valid coach label, including an explicit zero-finding reason
  where applicable;
- the required number of raters has submitted every rating;
- `score.json` exists and matches the current run configuration.

A pilot or incomplete run may report metrics, but its gates are `null` (blocked),
`pass` is `false`, and `release_eligible` is `false`. Do not present a partial run
as a release decision.

| Gate | Threshold |
|---|---|
| Evidence integrity | 100% |
| Precision | >= Standard - 5 percentage points |
| Recall | >= Standard on labelled findings |
| Median cost | <= 2.5x Standard |
| p95 latency | <= 2x Standard in the same environment; release requires production (see note) |
| Coverage honesty | >= 90% of Investigator reports |
| Hallucination flags | No increase over Standard |
| Coach preference | >= 60% of non-tie clip votes prefer Investigator |
| Inter-rater agreement | >= 60% preference agreement, or Cohen's κ > 0.4, before preference gate runs |
| Path diversity | >= 3 distinct tool sequences |
| Partial report rate | <= 10% of Investigator runs |
| Failure rate | 0 crashes on the benchmark |

> **Statistical limits — coach preference gate:** With 8 clips and 2 raters there are at most
> 16 preference votes. The 60% threshold requires only 10 votes. This is an early-stage
> indicator, not a statistically powered study. Treat it as a directional signal: a clear
> preference (≥ 75%) is meaningful; a marginal pass (60–65%) is not a strong endorsement.
> If the benchmark is expanded to 16+ clips, re-evaluate the threshold.

> **Gate rationale — precision vs recall:** Investigator is designed to surface issues Standard misses, so its recall must not drop below Standard's (no grace). The 5 percentage-point grace on precision accommodates the extra false positives that may come from a deeper investigation. If precision falls more than 5pp below Standard, the extra findings are noise, not signal.

> **Latency gate — production definition:** "Production" means: (1) the same model provider,
> model version and configuration used in the consumer-facing app; (2) run on a dedicated
> machine or cloud instance, not a developer laptop or shared CI runner; (3) no debug logging
> or profiling overhead active. A staging run may report latency for diagnosis, but the
> latency gate can only pass for a run whose `run.json` records `environment: "production"`.
> If production access is not yet available, the latency gate must remain `null` (blocked),
> not estimated from staging.

Gate values are `true`, `false` or `null`. `null` means blocked or not measurable;
it is never treated as a pass. If a gate fails, keep the mode opt-in, narrow it,
or stop. Do not tune the benchmark to make the mode look finished.

## 7.1 Benchmark validity check (negative control)

Before treating any benchmark result as a release decision, verify that the benchmark can
detect a bad system. Run the benchmark once against a **known-bad baseline** — for example,
Standard with its coaching prompt stripped (returning only a header and no findings, or only
generic advice with no timestamps). A valid benchmark must fail at least three release gates
on the known-bad run. If the known-bad run passes more than two gates, the benchmark has a
validity problem (the gates are too loose or the clips are too easy) and cannot be trusted
as a release signal.

Record the known-bad baseline run in `run.json` with `label: "negative-control"`. It does
not count toward release eligibility and is not included in preference scoring. It exists
solely to verify benchmark sensitivity.

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

### Stability check

For a production release gate, run the same clip set twice within 48 hours under identical
conditions (same model, budget settings and environment). Precision, recall and evidence
integrity must not differ by more than ±5 percentage points between the two runs. If the
variance exceeds this, the gate result is not reproducible and `release_eligible` must remain
`false`. Alternatively, fix temperature = 0 in the model configuration to reduce run-to-run
variance, and document this in `run.json`.

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
| `rating_sheet.csv` | Combined blind ratings export; each rater gets only a blank per-rater template |
| `runs/<run_id>/` | Reports, traces, ratings, score, summary |
| Benchmark UI | Local review, labelling, blind rating and adjudication surface |

This is a real benchmark subsystem, not a test fixture. Unit tests live under
`tests/benchmark/`; benchmark data and generated runs live outside the package.

The GUI is required for normal operation and is specified in
[Benchmark Review UI](02_benchmark-ui.md). It is a local-only FastAPI + SvelteKit
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
  README.md                 # tracked
  manifest.example.json     # tracked, no real people or paths
  labels.example.json       # tracked, schema only
  manifest.json            # local, ignored
  labels.json              # local, ignored
  clips/                    # local, ignored; external fixture paths allowed
  runs/                     # local, ignored
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
  .gitignore

tests/benchmark/            # unit and API tests only
```

`TOPSPIN_BENCHMARK_DATA` overrides the default data root. Set it to a path
outside the repository for real clips. Commit only `README.md`, example schemas
and the inner `.gitignore`.

The inner `.gitignore` must cover:

```gitignore
manifest.json
labels.json
clips/
runs/
```

Never commit real manifests, labels, clips, ratings or run artifacts. The example
files exist only to document the schema.

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
- `consent.expires` is checked at run time; a run must not start if any clip's consent has
  expired. The runner must validate expiry dates before creating the run, not only at manifest
  import. Expired consent produces a hard validation error, not a warning;
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
- write `run.json` with versions, models, budgets, environment, `config_hash`,
  `required_clips`, `required_raters` and status;
- validate consent expiry for every clip before starting the run; a clip with expired consent
  must be skipped with `status: consent_expired` and a clear log message, not silently analysed;
- fail the clip, not the whole run, on analysis errors; record `status: failed`;
- `--fail-fast` is optional;
- `--resume` skips clips with a valid JSON output and a matching `config_hash`
  covering manifest, labels, prompts, models, budgets and code revision.

**Scoring is a separate step.** `run` performs analysis only; it does not compute
gates. After runs, labels and ratings exist, compute the score explicitly:

```text
topspin-benchmark score --run benchmark/runs/<run_id>
```

The UI exposes this as `POST /api/runs/{run_id}/score` and shows “Score not
generated” with a “Recompute score” action. A completed run does not imply a
score, and a stale `score.json` is never treated as current.

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
- Raters see only the blind packet and their own blank rating-sheet template;
  never the combined sheet, labels or mapping.

Rating CSV columns:

```text
clip_id,rater,A_specific,A_supported,A_complete,A_honest,A_use,B_specific,B_supported,B_complete,B_honest,B_use,preferred,adjudicated_preference,rationale,notes
```

This is the combined export. A rater packet uses the same header without
`adjudicated_preference`; adjudication is added only after both rater sheets are
submitted.

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
  "required_clips": 8,
  "clips": 8,
  "required_raters": 2,
  "raters_submitted": 2,
  "labels_complete": true,
  "set_complete": true,
  "environment": "production",
  "config_hash": "...",
  "release_eligible": false,
  "blocked_reasons": ["gate_failed:precision"],
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
    "failure_rate": 0.0,
    "fp_zero_clip_rate": 0.0
  },
  "coach": {"investigator": 0, "standard": 0, "ties": 0, "agreement": 0.0},
  "hallucination_rate": 0.0,
  "gates": {
    "evidence_integrity": true,
    "coverage_honesty": true,
    "precision": false,
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

Field rules:

- `set_complete` is true only when all `required_clips` (default 8) are present.
- `labels_complete` is true only when every clip in the required set has a valid
  label, including an explicit zero-finding reason where needed.
- `release_eligible` is true only when the set, labels and ratings are complete,
  a current `score.json` exists, and every release gate is `true`.
- `blocked_reasons` uses stable IDs: `clips_incomplete`, `labels_incomplete`,
  `ratings_incomplete`, `score_missing`, `latency_environment_not_production`,
  and `gate_failed:<gate>`.
- A gate value is `true`, `false` or `null`; `null` is blocked, never a pass.
- `pass` has the same value as `release_eligible`; it is kept for compatibility.

`report.md` is the human summary: gates, eligibility, blocked reasons, per-clip
results and failures.

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
| 9 | Gate report | complete `score.json` + `report.md` with eligibility and blocked reasons |
| 10 | Tests | matching, ties, missing evidence, empty labels, failures |
| 11 | Benchmark UI | run list/dashboard, clip review, labels, blind rating, adjudication and export; see [Benchmark Review UI](02_benchmark-ui.md) |

## 21. Definition of done

- 8 clips and labels exist;
- one command runs Standard and Investigator into an isolated run directory;
- the local UI can launch/cancel runs, review clips, label findings, collect
  blind ratings, adjudicate and export results;
- two coaches rate blind packets;
- scoring produces all gates, eligibility, blocked reasons and a human report;
- UI and CLI produce the same score, report and rating-sheet files;
- real data is ignored by git and no PII enters tracked examples;
- results are reproducible from manifest, labels and run metadata.
