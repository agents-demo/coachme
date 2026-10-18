# Benchmark Review UI - Implementation Plan

**Status:** implementation spec. The CLI harness is Phase 1; this UI is Phase 2
and is required for normal benchmark operation.
**Related:** [Benchmark plan](benchmark.md), [Investigator plan](investigator.md).
**Owner:** engineering; benchmark labels and ratings remain coach-owned.

This is not a dashboard added after the fact. It is the operating surface for the
benchmark: launch runs, inspect clips, label findings, collect blind ratings,
adjudicate disagreements and export reproducible results.

---

## 1. Goals

1. Run a benchmark without hand-editing JSON or remembering CLI flags.
2. Review Standard and Investigator side by side, with timestamps that seek the
   clip.
3. Let a coach label findings without seeing AI reports.
4. Collect blind A/B ratings and hide the mode mapping until both raters submit.
5. Show gate status and per-clip failures without hiding bad results.
6. Export the same files the CLI scorer produces, so UI and CLI cannot drift.

## 2. Non-goals

- No production multi-tenant service, cloud database, billing or organisation
  administration.
- No video editor, clip capture, model configuration or API-key entry.
- No replacement for the product UI in `surfaces/gui2`.
- No automatic coach labels and no LLM-as-judge for the primary labels.
- No mobile-first workflow; phones may read a run, but labelling and rating are
  desktop/tablet tasks.
- No remote access in v1. If remote access is needed, stop and add authentication
  and HTTPS as a separate security milestone.

## 3. Design decisions

| Decision | Choice | Reason |
|---|---|---|
| Deployment | Local FastAPI server + SvelteKit SPA | Same stack and packaging pattern as `surfaces/gui2` |
| Source of truth | Files under the benchmark data root | CLI, UI and exports share one contract |
| Database | None | Runs are directories; labels/ratings are versioned JSON |
| Default bind | `127.0.0.1` only | Personal video and labels are sensitive |
| Run execution | Spawn `topspin-benchmark run` as a subprocess | UI cannot corrupt a long analysis |
| Concurrency | One active run per UI process | Avoids model/cost races in v1 |
| Writes | Atomic replace plus ETag/If-Match | Prevents silent overwrites |
| Blind enforcement | Server omits mapping; separate rater packets for true isolation | UI hiding alone is not a security boundary |
| Code location | `topspin_review/benchmark/ui/` | Benchmark is a real subsystem, not a test fixture |
| Data location | `benchmark/` or `TOPSPIN_BENCHMARK_DATA` | Large clips and runs stay out of the package |

## 4. Users and roles

| Role | Can do | Cannot do |
|---|---|---|
| Operator | Launch/cancel runs, browse results, export, manage run selection | Change submitted blind ratings silently |
| Labeler | Edit labels, mark clips labelled | See AI reports while labelling |
| Rater | Rate blind A/B packets, save and submit | See mode mapping, evidence IDs or the other rater's scores |
| Adjudicator | See mapping, both ratings, decide disagreements | Overwrite original rater scores |

The local v1 has no login. These are workflow modes, not security roles. A person
with filesystem access can read the mapping. For genuine blind ratings, either:

- run the UI in rater mode on a machine that cannot read `mapping.json`; or
- export separate rater packets and import the resulting CSV; or
- use the future authenticated rater server.

The UI must say this plainly on the rating screen. Do not claim that a local
single-user UI enforces blindness.

## 5. Information architecture

Routes:

| Route | Screen |
|---|---|
| `/` | Run list |
| `/runs/{run_id}` | Run dashboard |
| `/runs/{run_id}/clips` | Clip review |
| `/runs/{run_id}/clips/{clip_id}` | One clip, selected mode |
| `/runs/{run_id}/labels` | Label workspace |
| `/runs/{run_id}/labels/{clip_id}` | One clip label form |
| `/runs/{run_id}/rate` | Blind rating queue |
| `/runs/{run_id}/rate/{clip_id}` | Blind A/B form |
| `/runs/{run_id}/adjudicate` | Adjudication queue |
| `/runs/{run_id}/adjudicate/{clip_id}` | One adjudication |
| `/help` | Keyboard shortcuts, data-root path, blindness limits |

Navigation is a left rail on desktop and a top tab bar below 900px. The active
run is always visible in the header.

## 6. Screen specifications

### 6.1 Run list

Content:

- table of runs: `run_id`, created time, environment, modes, clip progress,
  gate result, eligibility badge, status, duration;
- filters: status, environment, pass/fail, date;
- empty state with the benchmark data-root path and a "New run" action;
- "New run" disabled with a reason when the manifest is missing or invalid.

Actions:

- open a run;
- start a new run;
- import an existing run directory;
- open the data-root folder in the OS file manager (local only).

States: loading skeleton, no runs, invalid data root, run currently active,
failed to read a run.

Acceptance: 50 runs load in under 300ms on a local SSD; a corrupt run directory
shows an error row and does not break the list.

### 6.2 New run

A modal or full page with:

- manifest path picker restricted to the benchmark data root;
- mode checkboxes: Standard and Investigator checked, Guided optional;
- environment selector: local, staging, production;
- a read-only summary: clip count, missing files, consent problems, label
  completeness, estimated model calls;
- confirmation that the run will write to `runs/<new_run_id>/`.

The server validates the manifest before creating the run. It never accepts an
arbitrary shell command. The run starts only after validation passes. Labels are
not required to run analysis, but scoring reports missing labels and the release
gates remain blocked until labels are complete.

If a run is already active, show the active run and refuse with a clear message.

### 6.3 Run dashboard

Content:

- status banner: queued, running, complete, failed, cancelled, plus a separate
  score status (`missing`, `scoring`, `current`, `stale`, `failed`);
- eligibility banner: “Pilot / incomplete” or “Release eligible” with the exact
  `blocked_reasons`;
- progress: clips complete / total, current clip and mode;
- gate table from `score.json`, with the metric value, threshold and result;
  blocked or missing gates render as `blocked`, not as zero or pass;
- metric cards: precision, recall, evidence integrity, coverage honesty,
  hallucination flags, cost, latency, path diversity, partial and failure rates;
- per-clip table: clip ID, source availability, Standard status, Investigator
  status, score status, failure reason;
- links to clip review, labels, rating and adjudication;
- export menu: `score.json`, `report.md`, `rating_sheet.csv`, labels, run archive.

Actions:

- cancel a running run;
- resume an incomplete run;
- recompute score if `score.json` is missing or older than reports;
- open a clip at a specific timestamp;
- delete the run after typing its `run_id` to confirm.

Do not render missing metrics as zero. Use `not available` with the reason
(for example, "score not generated" or "no labels").

### 6.4 Clip review

Three regions:

1. Clip list with status dots for Standard, Investigator and labels.
2. Video player and timeline:
   - play/pause, frame step, 0.25x/0.5x/1x speed;
   - current timecode and duration;
   - evidence markers on the timeline;
   - `[` and `]` set the current time as an evidence timestamp in the label form;
   - clicking a timestamp in either report seeks the video.
3. Report panel:
   - tabs Standard / Investigator / Side by side;
   - summary, findings, evidence, limitations and provenance;
   - each finding shows severity, theme, confidence and timestamps;
   - Investigator evidence chips show tool, window and evidence ID;
   - a warning when a report is `partial` or `failed`.

The operator may see mode names and evidence IDs. Rater mode must not.

### 6.5 Label workspace

Purpose: coach ground truth before seeing AI reports.

Layout: clip list on the left; video and label form on the right. The label
endpoints return clip metadata and labels only; they never return report text or
evidence. Report review is a separate route so a labeler does not accidentally
see the candidate output.

Labels are dataset-level and keyed by `clip_id`, shared across runs. The
run-scoped route supplies context only. The label ETag is global for
`labels.json`, not per run.

Form fields per finding:

- text (required, 1-500 characters);
- themes (multi-select from the fixed set in the benchmark plan);
- evidence times (one or more; `0` allowed for stills);
- severity (low, medium, high);
- required evidence (motion, pose, vision; `ball` disabled);
- acceptable limitations (clip-level);
- zero-finding reason when there are no findings.

Actions:

- add/remove/reorder findings, maximum five;
- mark clip labelled;
- save draft and save final;
- copy limitations from the previous clip;
- next/previous clip;
- keyboard save with `Ctrl/Cmd+S`.

Validation is server-side and mirrored in the UI:

- finding text non-empty;
- allowed theme and severity;
- times within clip duration;
- video findings need at least one time;
- zero findings requires a reason;
- `ball` evidence is rejected;
- labels cannot be marked complete while invalid.

Autosave a local draft every 5 seconds. A server save requires the current ETag.
On `409`, do not overwrite; show a diff summary and ask the user to reload or
merge. The UI must not silently discard edits.

### 6.6 Blind rating

Queue view: clip list with rater progress (`not started`, `draft`, `submitted`).
Only clips with a complete blind packet are enabled.

One clip view:

- shared video player at the top;
- A and B report panels side by side, with identical normalized fields;
- no mode names, evidence IDs, trace paths or file names;
- A/B order randomized per clip by the server and recorded in `mapping.json`;
- rating form:
  - specific, supported, complete, honest: 1-5;
  - would use: yes/no;
  - preference: A / B / tie;
  - rationale (required when preference is not tie);
- save draft, submit, next clip;
- submitted ratings lock; editing requires an explicit "reopen" that records an
  audit event.

The server must strip mode-specific data before serializing the response. A
client-side hide is not sufficient. Test the network response for forbidden keys.

The rating screen displays: "This is a local single-user view. True blindness
requires separate rater packets or a restricted machine."

### 6.7 Adjudication

Only after both raters have submitted a clip:

- show mapping and both rating forms;
- show the two reports with mode labels and evidence;
- choose the final preference;
- require a rationale;
- write `adjudicated_preference` and `rationale`;
- keep the original votes unchanged;
- show agreement before and after adjudication.

If a rater is missing, the clip is not adjudicable; show the missing rater.

### 6.8 Help

- keyboard shortcuts;
- current benchmark data root;
- how to start a run;
- how to export/import rater packets;
- explicit blindness and local-access warning;
- link to the benchmark plan and schema versions.

## 7. Key flows

### Start a run

1. Operator opens "New run".
2. UI calls `GET /api/manifest/validate` with the selected path.
3. Server validates manifest, clips, consent, labels and output root.
4. Operator confirms modes and environment.
5. `POST /api/runs` returns `202` and a `run_id`.
6. UI opens the dashboard and subscribes to `GET /api/runs/{run_id}/events`.
7. Server spawns `topspin-benchmark run` with an argument list, no shell.
8. On completion the server updates `run.json`; scoring is **not** automatic.
9. Dashboard switches to complete, failed or cancelled and shows `score_status`
   as `missing` until the operator clicks “Recompute score”.
10. “Recompute score” calls `POST /api/runs/{run_id}/score`; the dashboard polls
    `score_status` until it is `current` or `failed`.

### Label a clip

1. Labeler opens the label workspace.
2. UI loads clip metadata and labels with an ETag.
3. Labeler edits findings and uses `[` / `]` to capture times.
4. Autosave sends `PUT /api/labels/{clip_id}` with `If-Match`.
5. On success, the ETag updates; on `409`, show the conflict.
6. "Mark labelled" is enabled only when server validation passes.
7. Progress updates on the dashboard.

### Rate a clip

1. Rater selects their name or enters a rater ID.
2. UI requests `GET /api/runs/{run_id}/blind/{clip_id}?rater=...`.
3. Server verifies the rater has not submitted and returns A/B without mapping.
4. Rater submits; server writes `ratings/<rater>.json` atomically.
5. Mapping stays hidden until all required raters submit.
6. Adjudication becomes available to the adjudicator.

### Cancel a run

1. Operator confirms cancel.
2. Server sends terminate to the child process.
3. After 10 seconds, kill and mark `cancelled`.
4. Partial outputs remain for diagnosis but are not scored as a completed run.

## 8. API contract

All endpoints are under `/api`. JSON errors use:

```json
{"error": {"code": "conflict", "message": "labels changed since load", "details": {}}}
```

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/health` | - | `{ok, version, data_root, active_run}` |
| GET | `/runs` | - | `{runs: [RunSummary]}` |
| POST | `/runs` | `{manifest_path, modes, environment, label?, required_raters?}` | `202 {run_id}` |
| POST | `/runs/import` | `{path, confirm: true}` | `201 {run_id}` |
| GET | `/runs/{run_id}` | - | `RunDetail` |
| DELETE | `/runs/{run_id}` | `confirm=run_id` | `{deleted}` |
| POST | `/runs/{run_id}/cancel` | - | `{status}` |
| POST | `/runs/{run_id}/score` | - | `202 {status}` |
| GET | `/runs/{run_id}/events` | - | SSE progress events |
| GET | `/runs/{run_id}/clips` | - | `{clips: [ClipSummary]}` |
| GET | `/runs/{run_id}/clips/{clip_id}` | - | `ClipDetail` |
| GET | `/runs/{run_id}/blind/{clip_id}` | `rater` | `BlindPacket` |
| GET | `/runs/{run_id}/media/{clip_id}/source` | - | video/image with range support |
| GET | `/runs/{run_id}/media/{clip_id}/artifact/{kind}` | - | image/JSON artifact |
| GET | `/labels` | - | `{version, etag, clips}` |
| GET | `/labels/{clip_id}` | - | `{version, etag, clip}` |
| PUT | `/labels/{clip_id}` | label object + `If-Match` | `{version, etag, clip}` |
| GET | `/runs/{run_id}/ratings/{rater}` | - | `RatingSheet` |
| PUT | `/runs/{run_id}/ratings/{rater}/{clip_id}` | rating + `If-Match` | `{etag, clip_rating}` |
| POST | `/runs/{run_id}/ratings/{rater}/submit` | - | `{submitted, count}` |
| POST | `/runs/{run_id}/ratings/{rater}/{clip_id}/reopen` | `{reason}` | `{etag, clip_rating}` |
| POST | `/runs/{run_id}/rater-packets` | `{raters: ["coach-a","coach-b"]}` | zip download |
| POST | `/runs/{run_id}/ratings/import` | multipart `rater`, `file` | `{rater, submitted, count}` |
| GET | `/runs/{run_id}/adjudication` | - | queue |
| PUT | `/runs/{run_id}/adjudication/{clip_id}` | decision + `If-Match` | `{decision}` |
| GET | `/runs/{run_id}/export/{name}` | - | file download |
| GET | `/manifest/validate` | `path` | validation result |

Rules:

- `If-Match` is required for labels, ratings and adjudication writes.
- Missing `If-Match` is `428`; stale is `409`.
- `GET /blind` never returns mapping, mode names, evidence IDs or trace paths.
- `GET /adjudication` returns mapping only after all required ratings submit.
- Media paths are resolved from the clip ID, never from a client path.
- Downloads set `Content-Disposition` and do not expose absolute paths.
- The export whitelist is `score.json`, `report.md`, `rating_sheet.csv`, `labels.json`,
  `runner.log` and `run.zip`; no arbitrary file names.
- `POST /runs/import` and `DELETE /runs` are restricted to the benchmark data root
  and require an explicit confirmation value.
- `rater-packets` contains one folder per rater with A/B JSON and a CSV template;
  it contains no mapping and no mode names.
- Reopening a submitted clip requires a reason, appends to
  `rating_events.jsonl`, and is rejected after adjudication is recorded.
- `POST /runs/{run_id}/score` is accepted only when analysis status is
  `complete`; runs with partial clip reports may be scored for diagnosis but
  remain ineligible for release. `running`, `failed` and `cancelled` runs return
  `409`.
- Rating import accepts only the documented CSV columns and the run's clip IDs;
  unknown columns are rejected, not ignored.
- SSE events are newline-delimited `event:`/`data:` frames; polling is the
  fallback.
- Run creation uses a filesystem lock at `runs/.active.json` with PID, host and
  heartbeat. The UI and CLI both respect it; a stale lock is recoverable after
  10 minutes. A second live run returns `409`.

## 9. Data contracts

### RunSummary

```json
{
  "run_id": "20261018-142501-a1b2",
  "created_at": "2026-10-18T14:25:01Z",
  "environment": "local",
  "modes": ["standard", "investigator"],
  "status": "complete",
  "clips_total": 8,
  "clips_complete": 8,
  "clips_failed": 0,
  "labels_complete": true,
  "set_complete": true,
  "score_status": "current",
  "score_updated_at": "2026-10-18T14:31:12Z",
  "gates_pass": false,
  "release_eligible": false,
  "blocked_reasons": ["gate_failed:precision"],
  "warning": null
}
```

### RunDetail

```json
{
  "run_id": "20261018-142501-a1b2",
  "label": "release-2026-10",
  "status": "complete",
  "score_status": "current",
  "environment": "production",
  "modes": ["standard", "investigator"],
  "required_clips": 8,
  "required_raters": 2,
  "raters_submitted": 2,
  "config_hash": "...",
  "created_at": "2026-10-18T14:25:01Z",
  "data_root": "benchmark",
  "run_dir": "benchmark/runs/20261018-142501-a1b2",
  "clips_total": 8,
  "clips_complete": 8,
  "clips_failed": 0,
  "labels_complete": true,
  "set_complete": true,
  "score_available": true,
  "release_eligible": false,
  "blocked_reasons": ["gate_failed:precision"],
  "log_url": "/api/runs/20261018-142501-a1b2/export/runner.log",
  "warning": null
}
```

`required_clips` defaults to 8 and `required_raters` to 2; both are stored in
`run.json`. `score_status` is `missing`, `scoring`, `current`, `stale` or `failed`.
`release_eligible` is true only when the set, labels, ratings and score are
complete and every gate passes. Adjudication and mapping reveal use
`required_raters`. `run_dir` is display-only and is never accepted as an API path.

### ClipSummary

```json
{
  "clip_id": "tt-clean-01",
  "media_type": "video",
  "duration_s": 10.4,
  "capture": "side-on, phone, tripod",
  "consent_ok": true,
  "reports": {
    "standard": {"status": "complete", "issue_count": 3},
    "investigator": {"status": "partial", "issue_count": 5}
  },
  "label_status": "complete",
  "ratings_submitted": 2
}
```

### BlindPacket

```json
{
  "clip_id": "tt-clean-01",
  "packet_id": "pkt-7f3a",
  "media_url": "/api/runs/.../media/tt-clean-01/source",
  "reports": {
    "A": {"summary": "...", "issues": [], "limitations": []},
    "B": {"summary": "...", "issues": [], "limitations": []}
  }
}
```

No other keys are allowed. Server tests must assert the serialized response has
no `mode`, `evidence`, `investigation`, `evidence_ids`, `trace_path` or file name.

### RatingSheet

```json
{
  "version": 1,
  "run_id": "20261018-142501-a1b2",
  "rater": "coach-a",
  "updated_at": "2026-10-18T15:00:00Z",
  "clips": {
    "tt-clean-01": {
      "A_specific": 5,
      "A_supported": 4,
      "A_complete": 4,
      "A_honest": 5,
      "A_use": "yes",
      "B_specific": 4,
      "B_supported": 5,
      "B_complete": 5,
      "B_honest": 4,
      "B_use": "yes",
      "preferred": "B",
      "rationale": "B cited the contact point more precisely.",
      "submitted": true,
      "submitted_at": "2026-10-18T15:00:00Z"
    }
  }
}
```

### Rating CSV import

The rater packet template and `ratings/import` use exactly this header:

```text
clip_id,rater,A_specific,A_supported,A_complete,A_honest,A_use,B_specific,B_supported,B_complete,B_honest,B_use,preferred,rationale,notes
```

Rules:

- one row per clip; duplicate or unknown `clip_id` rejects the import;
- `rater` must match the `rater` form field;
- all scores are integers `1-5`; `A_use` and `B_use` are `yes` or `no`;
- `preferred` is `A`, `B` or `tie`;
- `rationale` is required when `preferred` is not `tie`;
- unknown or missing columns reject the whole import;
- `adjudicated_preference` is export-only and is not accepted on rater import.

The exported combined `rating_sheet.csv` adds `adjudicated_preference` after
`preferred`.

### Label and scoring schemas

Labels follow the benchmark plan §13. Scoring, matching, gates and zero-denominator
rules follow benchmark plan §17-18. The UI does not implement its own scoring
logic; it calls the CLI scorer.

## 10. Runtime and packaging

Code:

```text
topspin_review/benchmark/
  __init__.py
  cli.py                 # run, score, ui, import
  runner.py
  scorer.py
  schemas.py
  paths.py
  ui/
    server/
      app.py
      routes/
      read.py
      jobs.py
    client/
      package.json
      src/
        routes/
          +layout.svelte
          +page.svelte                  # runs
          runs/[run_id]/+page.svelte       # dashboard
          runs/[run_id]/clips/[clip_id]/+page.svelte
          runs/[run_id]/labels/[clip_id]/+page.svelte
          runs/[run_id]/rate/[clip_id]/+page.svelte
          runs/[run_id]/adjudicate/[clip_id]/+page.svelte
        lib/
          api.ts
          types.ts
          stores.ts
          components/
            RunTable.svelte
            EligibilityBanner.svelte
            GateTable.svelte
            ClipPlayer.svelte
            ReportPanel.svelte
            LabelForm.svelte
            RatingForm.svelte
            AdjudicationPanel.svelte
      e2e/benchmark.spec.ts
      build/             # bundled static assets for the package
```

Data:

```text
benchmark/               # default TOPSPIN_BENCHMARK_DATA
  README.md              # tracked
  manifest.example.json  # tracked, schema only
  labels.example.json    # tracked, schema only
  .gitignore             # ignores real data
  manifest.json          # local, ignored
  labels.json            # local, ignored
  clips/                 # local, ignored
  runs/                  # local, ignored
    <run_id>/
      run.json
      runner.log
      mapping.json       # never served to raters
      ratings/<rater>.json
      rating_events.jsonl # reopen/submit audit, append-only
      blind/<clip_id>/{A.json,B.json}
      raw/<mode>/<clip_id>.json
      traces/<mode>/<clip_id>.json
      score.json
      report.md
      ui_job.json
```

Inner `.gitignore`:

```gitignore
manifest.json
labels.json
clips/
runs/
```

Real manifests, labels, clips, ratings and runs must never be committed. Use
`TOPSPIN_BENCHMARK_DATA` for a data root outside the repository.

Commands:

```text
topspin-benchmark run --manifest benchmark/manifest.json --modes standard,investigator
topspin-benchmark score --run benchmark/runs/<run_id>
topspin-benchmark ui --data benchmark --port 8765
topspin-benchmark import --from <run_dir>
```

Packaging:

- add `topspin-benchmark = "topspin_review.benchmark.cli:main"` to
  `[project.scripts]`;
- reuse the `api` extra (`fastapi`, `uvicorn`); do not add a second web framework;
- bundle the built SvelteKit client as package data, using the same pattern as
  `surfaces/gui2`;
- add `@playwright/test` as a client dev dependency and `npm run test:e2e`;
- do not add new Python dependencies for the GUI;
- the UI server binds to loopback by default and refuses non-loopback unless an
  explicit future `--allow-remote` implementation with auth exists.

The benchmark UI must use `TOPSPIN_BENCHMARK_DATA`, not `runtime/data`. The runner
sets `TOPSPIN_DATA_DIR` to a run-scoped analysis directory and disables the demo
fallback.

## 11. Process and state handling

Run statuses:

```text
queued -> running -> complete
                    \-> failed
queued/running -> cancelled
```

Scoring has its own status: `missing -> scoring -> current`, with `stale` when
reports, labels or ratings change, and `failed` when the scorer exits nonzero.
`run` never sets `score_status` to `current` by itself.

Rules:

- the server creates `runs/<run_id>/` before spawning;
- `run.json` is the source of truth for analysis status and `score_status`;
- the child process writes logs to `runner.log` and status to `run.json`;
- the server polls `run.json` every 1 second and emits SSE progress;
- a missing or stale `run.json` for more than 60 seconds marks the job as failed
  with a diagnostic, not as complete;
- scoring runs only after all requested modes finish; partial runs are not scored
  as releases;
- the scorer writes `score.json.tmp`, validates it, then atomically replaces
  `score.json`; readers never see a partial score;
- a failed rescore leaves the previous score in place and marks `score_status`
  `stale` or `failed` with the error, never silently deletes it;
- cancellation is idempotent;
- resume uses the runner's `config_hash`, not a UI flag.

`ui_job.json` stores:

```json
{
  "run_id": "...",
  "pid": 12345,
  "started_at": "...",
  "command": ["python", "-m", "topspin_review.benchmark.cli", "run", "..."],
  "modes": ["standard", "investigator"],
  "environment": "local",
  "required_raters": 2
}
```

`run.json` stores the same `required_raters`, `config_hash`, status and timestamps.
`ui_job.json` is UI-local; the runner does not depend on it.

Do not log API keys, absolute personal paths, labels or report text in server
logs.

## 12. Blindness and access control

- `/api/runs/{run_id}/blind/{clip_id}` is the only rater report endpoint.
- It requires a rater identifier and returns only normalized A/B reports.
- It checks that the clip packet exists and that the rater has not submitted.
- Mapping and mode are never included in the response, even after submission.
- Adjudication routes require both raters' submitted sheets.
- A local operator can still read `mapping.json`; the UI must not claim otherwise.
- For true separation, use separate rater packets on separate machines, or add
  authenticated rater identities in a later milestone.
- Remote binding is outside v1 and must not be exposed on a LAN or public
  interface.

## 13. Privacy and consent

- The UI does not upload clips anywhere.
- Starting a run shows which external model provider will process frames and
  requires the operator to confirm consent coverage.
- Invalid or expired consent blocks run creation; it does not warn and continue.
- The data root and run paths are visible only to the local operator.
- Export archives may contain personal video metadata; show a warning and include
  only requested files.
- Delete run removes the run directory and derived artifacts; labels remain only
  if the operator explicitly keeps them for the dataset.
- Do not put PII in filenames, labels, rater names or logs.

## 14. Accessibility and layout

- All controls reachable by keyboard; visible focus rings.
- Video controls have text labels and shortcuts; no drag-only interaction.
- Status is not conveyed by colour alone; use text plus icon.
- Contrast meets WCAG AA for text and controls.
- Respect `prefers-reduced-motion`; no auto-playing video.
- Desktop target 1280px; tablet 768px; below 768px show a read-only warning for
  labelling and rating.
- Every async view has loading, empty, error and retry states.
- Long reports scroll independently; video remains visible while scrolling findings.

## 15. Performance targets

- Run list: under 300ms for 50 runs on local SSD.
- Run dashboard: under 500ms excluding media.
- Clip switch: under 1s excluding video buffering.
- Label save: under 300ms for a clip.
- Blind rating save: under 300ms.
- Media uses HTTP range requests; do not load entire clips into memory.
- Server memory under 250MB with one run and one video open.
- No more than one active benchmark run.

## 16. Testing and acceptance

Server tests (pytest, temporary data root):

1. empty data root returns an empty run list;
2. invalid manifest returns a field-level error;
3. run creation rejects paths outside the data root;
4. second run while active returns `409`;
5. cancel transitions to `cancelled` and is idempotent;
6. label save without `If-Match` returns `428`;
7. stale label ETag returns `409` and leaves the file unchanged;
8. blind response contains no mode/evidence/trace keys;
9. mapping is unavailable until both ratings submit;
10. adjudication requires two submitted ratings;
11. media route rejects unknown clip IDs and path traversal;
12. atomic writes leave no partial JSON after a simulated failure.

UI acceptance:

1. open with no runs and see the data-root path and disabled New run reason;
2. start a run, watch progress, cancel, see cancelled status;
3. open a clip, click a finding timestamp, verify seek within 0.2s;
4. label a clip, trigger validation, save, reopen and verify persistence;
5. simulate an ETag conflict and verify no silent overwrite;
6. rate a blind packet, refresh, verify draft/submitted state resumes;
7. confirm A/B panels contain no mode names or evidence IDs in the DOM;
8. after two raters, adjudicate and export;
9. export `score.json`, `report.md`, `rating_sheet.csv` and verify filenames/content;
10. keyboard-only pass through run, label and rating screens.

Automated browser smoke test:

- `ui/client/e2e/benchmark.spec.ts`, run with `npm run test:e2e` using
  `@playwright/test`;
- start the UI against a temp data root seeded with one fixture run, two clips,
  labels, one submitted rater sheet and one empty rater sheet;
- no model calls and no network access outside loopback;
- cover: open run → eligibility banner → open clip → label save → rate blind
  packet → verify no mode/evidence text in the DOM → adjudicate → export;
- assert a second browser reload resumes the same state.

## 17. Implementation sequence

1. **Foundation:** package skeleton, CLI entry point, data-root resolution,
   manifest validation, run reader, atomic JSON utility, API health/runs.
2. **Read-only UI:** Svelte shell, run list, run dashboard, clip review, media
   range serving, score/report loading.
3. **Labels:** label read/write API, ETag conflict, form, validation, autosave,
   mark-labelled, progress.
4. **Blind ratings:** packet generation/reader, rater sheet API, blind UI,
   submission lock, mapping guard.
5. **Adjudication:** queue, mapping reveal, decision save, agreement display.
6. **Run control:** new-run validation, subprocess launch, SSE, cancel, rescore,
   import.
7. **Export and hardening:** archives, accessibility, error states, privacy
   checks, performance, pytest coverage and the Playwright smoke test.

Each step must leave the CLI usable and the data files valid by themselves.

## 18. Definition of done

- `topspin-benchmark ui` starts a local server and opens the SPA;
- a run can be launched, cancelled and rescored from the UI;
- every clip can be reviewed with timestamp seeking;
- a coach can label all clips without touching JSON;
- two raters can submit blind ratings without seeing the mapping;
- an adjudicator can resolve disagreements;
- gates and failures are visible, including missing, blocked and failed runs;
- eligibility and `blocked_reasons` are visible on every run;
- all writes are atomic and conflict-safe;
- no clip, label, rating or mapping is written outside the benchmark data root;
- real data is ignored by git and examples contain no PII;
- CLI and UI produce the same `score.json`, `report.md` and `rating_sheet.csv`;
- the Playwright smoke test passes without model calls;
- the privacy and blindness warnings are visible and accurate.
