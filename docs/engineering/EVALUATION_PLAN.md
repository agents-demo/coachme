# Evaluation Plan: Standard vs Investigator

**Role:** shared benchmark and release gates. Use this to decide whether Investigator is ready.

**Status:** template — clips, labels and scoring harness still to be built
**Scope:** shared evaluation for Standard, Guided and Investigator
**Owner:** engineering owns the harness; a coach/analyst owns ground-truth labels

This is deliberately separate from the Investigator implementation plan. The
benchmark evaluates the product against the reliable baseline, not just whether
the agent code runs.

---

## 1. What the benchmark must answer

1. Does Investigator find real coaching issues that Standard misses?
2. Are its findings supported by the evidence it cites?
3. Does it admit what it did not examine?
4. Is the quality gain worth the extra cost and latency?
5. Does it produce different investigation paths across different clips?

It does **not** score whether the agent followed the “correct” path. There is no
single correct path; there is only evidence support and coaching value.

---

## 2. Dataset

Target: **8 clips** for the first benchmark.

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

Rules:

- keep clips short (ideally 6–20 seconds);
- use real footage, not synthetic clips, for the benchmark;
- store large clips outside git or use a downloadable fixture with checksums;
- record consent and retention rules before uploading personal video;
- do not train on benchmark clips without explicit opt-in.

Artifact layout:

```text
tests/eval/investigation/
  README.md
  manifest.json
  labels.json
  clips/                 # or external fixture paths
  runs/<date>/           # generated reports and traces
```

---

## 3. Manifest

Each clip entry:

```json
{
  "id": "tt-clean-01",
  "path": "clips/tt-clean-01.mp4",
  "sport": "table tennis",
  "duration_s": 10.4,
  "capture": "side-on, phone, tripod",
  "notes": "one player, forehand drill",
  "split": "benchmark"
}
```

---

## 4. Coach labels

A coach/analyst watches each clip and records the **ground truth**, not a review
of the AI report.

Each finding:

```json
{
  "clip_id": "tt-clean-01",
  "finding": "Contact point is late and the elbow drops on the backswing",
  "evidence_times": [2.8, 4.1],
  "severity": "high",
  "confidence": "high",
  "theme": "contact point",
  "expected_coverage": ["pose", "vision"],
  "acceptable_limitations": ["ball placement not assessed"]
}
```

Rules:

- label the top 3–5 findings only;
- include at least one timestamp per finding;
- mark whether the finding needs pose, ball, motion or visual evidence;
- write what a good report may legitimately leave unassessed;
- do not read the AI reports before labeling.

---

## 5. Blind A/B protocol

For each clip, generate:

- **A:** Standard report
- **B:** Investigator report

Randomize A/B order; hide the mode name. A coach rates each report:

| Question | Scale |
|---|---|
| Are the findings specific and actionable? | 1–5 |
| Are they supported by the clip? | 1–5 |
| Is anything important missing? | 1–5 |
| Is the report honest about what it did not assess? | 1–5 |
| Would you use this before a lesson? | yes/no |
| Which report is better? | A / B / tie |

Two coaches per clip is the minimum. Do not let the builder of the system be the
only rater.

---

## 6. Metrics

### Evidence integrity

Percentage of investigator issues with:

- at least one valid evidence ID;
- at least one timestamp inside a cited, non-overview evidence window;
- a confidence value.

Target: **100%**.

### Finding precision / recall

Match findings by theme + timestamp tolerance (±1.5s) against coach labels.

- **Precision:** how many reported findings are real.
- **Recall:** how many labelled findings were found.

### Coverage honesty

- false coverage flags;
- missing “not assessed” statements;
- claims that require evidence that was never collected.

### Hallucination flags

Reuse `domain/evaluate.py` plus investigator evidence rules. No increase over
Standard is acceptable.

### Cost

Tokens, tool seconds, frame decodes. Compare median and p95 against Standard.

### Latency

Median and p95, measured on the production server, not a laptop.

### Path diversity

Count distinct tool sequences across the 8 clips. If every run uses the same
path, Investigator is not actually adaptive.

### Failure rate

Crashes, validation failures, timeouts, partial reports.

---

## 7. Release gates

Investigator stays opt-in until all gates pass:

| Gate | Threshold |
|---|---|
| Evidence integrity | 100% |
| Precision | ≥ Standard − 5 percentage points |
| Recall | ≥ Standard on labelled themes |
| Median cost | ≤ 2.5× Standard |
| p95 latency | ≤ 2× Standard |
| Hallucination flags | No increase over Standard |
| Coach preference | Investigator preferred in a clear majority of clips |
| Path diversity | At least 3 distinct tool sequences across 8 clips |
| Partial report rate | ≤ 10% of runs |

If a gate fails, keep the mode experimental or narrow it. Do not remove the
warning to make the mode look finished.

---

## 8. Reproducibility

For every benchmark run, store:

- clip manifest version and checksums;
- label version;
- prompt version and toolset version;
- model names and provider;
- budget settings;
- per-clip report JSON and investigation trace;
- scoring output.

The benchmark must be rerunnable after a prompt or tool change.

---

## 9. Ownership and sequence

1. Engineering creates the manifest, label schema and scoring sheet.
2. Coach/analyst labels the clips without seeing AI reports.
3. Engineering runs Standard and Investigator, randomizes A/B.
4. Coaches rate blindly.
5. Engineering computes metrics and writes the gate report.
6. Product decides: keep experimental, narrow, or graduate.

Label acquisition is a **1–2 week dependency**, not a coding task inside the
Investigator milestone.
