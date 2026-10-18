# Model-as-Orchestrator: Free Investigation Analysis

**Status:** MVP spec; implementation in progress (revision 1.2)
**Scope:** a new opt-in analysis mode for Topspin Review
**Goal:** make the model own the investigation, not just write the report

*Revision 1.1 incorporates an independent architecture review: run-scoped storage,
single `save_report`, per-run token budget, deferred `compare_windows`, explicit
cancellation limits, corrected partial-report validation and a re-baselined
schedule.*

---

## 1. The problem

The current demo is a **precisely known pipeline**:

```
sample frames -> measure motion/pose/ball -> two vision passes -> write report
```

That is the right default. It is fast, predictable and demo-safe. But it is not the
agentic behaviour we describe in the pitch:

- The programmer decides what gets measured.
- Pose and ball always run, even when they are irrelevant to the hypothesis.
- The model receives a fixed measurement dump and writes prose from it.
- The model cannot say “I need to look at the racket face at contact” and then call
  a tool that was not part of the planned pipeline.
- The report is limited by what the pipeline measured before any finding existed.

The mode proposed here is different:

> **The model is the orchestrator. It receives a small set of investigation tools and
> decides, step by step, what to examine. Measurement is a tool, not a stage.**

This is the “free investigation” behaviour described in
[WHY_AGENTIC_PLATFORM.md](../pitch/WHY_AGENTIC_PLATFORM.md): the agent may ignore
ball placement entirely, or may spend most of its budget on racket angle and wrist
mechanics because that is where its hypothesis leads.

---

## 2. What exists today

### 2.1 Deterministic strategy

`topspin_review/core/strategies/deterministic.py` is the default. It runs:

1. `base.Strategy._prepare()` -> `measure.measure()`
2. deterministic artifact generation
3. coarse vision pass
4. zoom/detail vision pass
5. report agent
6. verification/export

`base.py:_prepare()` always calls `measure()` (`base.py:80`). That function is
monolithic: sampling, activity, ball, pose, strokes and metrics all run before any
agent can reason (`core/stages/measure/measure.py`).

### 2.2 Existing “agentic” strategy

`core/strategies/agentic.py` is an important prototype, but it is **not** the mode
described above:

- `_prepare()` still runs the full fixed `measure()` first.
- The agent gets only two investigation tools:
  - `get_measurements()`
  - `inspect_window(start, end, frame_count)`
- It can choose a few windows and then calls `save_report`.
- `inspect_window()` uses the vision agent and returns text, but does not expose
  pose, ball, stroke segmentation, tracking, racket analysis or an evidence ledger.
- It uses a module-global `_STATE`, which is unsafe for concurrent jobs.
- It does not generate the normal artifacts, so the report/UI is thinner.
- It is exposed as an “Advanced” checkbox and via `--agentic` / `AGENTIC_MODE`.

So we already have **agentic reporting with a fixed measurement layer**. The new
mode is **agentic analysis**: the model owns the investigation.

### 2.3 What openjiuwen already gives us

The installed `openjiuwen` (`C:\Workspace\openjiuwen\agent-core`) provides the
runtime we need:

- `create_deep_agent()` supports tools, `max_iterations`, `parallel_tool_calls`,
  subagents, task loop, rails, workspace, and multimodal `read_file`
  (`openjiuwen/harness/factory.py:460`).
- The inner `ReActAgent` implements the thought -> tool call -> observation loop
  (`openjiuwen/core/single_agent/agents/react_agent.py`).
- `DeepAgent.stream()` and `Runner.run_agent_streaming()` exist, yielding
  `OutputSchema` chunks (`openjiuwen/harness/deep_agent.py:3325`,
  `core/runner/runner.py:849`).
- Rails can hook before/after model and tool calls, including
  `TokenBudgetRail` (`integrations/agents/agent/rails.py`).
- `ContextEngine` supports windowing and compression for long tool traces.
- Tool metadata is auto-derived from the callable name, docstring and signature
  (`integrations/agents/agent/tools.py`).
- `TextBuilder` currently creates a text DeepAgent with application tools
  (`integrations/agents/agent/builder/text.py`); `VisionBuilder` currently creates
  a vision agent with no application tools.

What is missing is not a new framework. It is a **tool surface, a run context, an
evidence model, and a policy**.

---

## 3. Target behaviour

The new mode is called **Investigator** (working name). It is explicitly
experimental and opt-in.

The agent receives:

- video metadata and a cheap overview;
- the player profile and recent sessions;
- a toolbox of measurement, perception and evidence tools;
- a report schema and a hard budget.

It is not told “call the pose stage, then the ball stage, then the report stage.”
It is told:

> “Investigate this session like a coach. Use only the tools you need. Every claim
> must point to evidence. If you do not examine something, say so.”

A possible trace:

```
overview()
  -> motion peaks at 1.2s, 2.8s, 4.1s
look(2.5, 3.1, "Where is contact and what does the wrist do?")
  -> contact appears late; wrist looks stiff; medium confidence
estimate_pose(2.6, 3.0)
  -> wrist speed peak at 2.88s; elbow angle 122 deg
look(4.0, 4.4, "Does the second stroke show the same pattern?")
  -> same late contact; medium confidence
save_report(...)
```

It might never call `track_ball()`. That is allowed. The report must then say
“ball placement was not assessed,” rather than pretending it was.

---

## 4. Architecture

### 4.1 High-level shape

```
InvestigatorStrategy
  ├─ prepare: cheap overview only (no full pose/ball)
  ├─ InvestigationContext
  │    ├─ video/meta/profile
  │    ├─ EvidenceLedger
  │    ├─ Budget (tools, seconds, tokens, frames)
  │    ├─ artifact/cache directories
  │    ├─ progress/event sink
  │    └─ vision helper (for visual questions)
  ├─ build_tools(context)
  ├─ build investigator agent (text orchestrator)
  ├─ run ReAct loop
  └─ finalize: report + evidence + coverage + artifacts
```

The **text agent is the orchestrator**. Visual questions are delegated to a
`look()` tool that internally uses the existing vision agent. This keeps report
reasoning in the stronger text model and avoids requiring a single multimodal model
to do everything. A future variant can use a multimodal orchestrator directly if
the model supports reliable tool calling plus image input.

### 4.2 What is *not* precomputed

Only a cheap overview is precomputed:

- duration, fps, resolution;
- 16–32 motion-sampled thumbnails or one contact sheet;
- motion-energy timeline and peaks;
- optional scene cuts / long static periods.

No pose, no ball, no stroke segmentation, no full metrics. Those become tools.

### 4.3 Why this is not “just another prompt”

The difference is structural:

- The next model prompt contains the result of the tool the model chose, not a
  fixed metric dump.
- The model can stop early or probe a contradiction.
- The tool set is general; new tools extend capability without changing the
  pipeline.
- The report is generated from a trace of evidence, not from a pre-measured schema.

---

## 5. Run lifecycle

### Step 0 — request

Input: video path, profile, language, optional region box, mode.

The mode is `investigator`. The default remains `deterministic`.

### Step 1 — prepare

- validate file;
- set current video;
- load profile;
- create `RunSession` (recorder + vision agent + media dir);
- read video metadata;
- build cheap overview;
- initialize `InvestigationContext`, budget, ledger and progress.

Failure here falls back to the deterministic strategy if
`INVESTIGATOR_FALLBACK=true`.

### Step 2 — orient

The initial user prompt contains:

- profile and history summary;
- overview timeline;
- a short instruction to form a hypothesis;
- tool catalogue descriptions;
- budget and stopping rules.

The model is *not* required to call every tool.

### Step 3 — investigate loop

Each iteration:

1. Model reasons about the current evidence.
2. Model calls one or more tools (serial by default).
3. Tool executes against the video, writes artifacts/cache, records an evidence
   item, and returns a compact JSON observation.
4. Observation is appended to the model context.
5. Model revises, probes, or stops.

### Step 4 — synthesize

The model must produce a report with:

- findings/issues, each with evidence IDs and timestamps;
- strengths;
- drills/focus;
- progress vs previous session;
- limitations, including what was *not* investigated;
- confidence.

`save_report` validates the evidence references before accepting the report. If the
model tries to cite an unknown evidence ID, the tool returns an error and the model
must correct it.

### Step 5 — finalize

- merge the report with run metadata;
- attach artifacts generated on demand;
- add investigation trace/coverage;
- run optional verification;
- export and persist;
- record usage/timings.

If the model exhausts budget or iterations, force a “best current answer” with
explicit limitations; do not silently fail.

---

## 6. Tool catalogue

All tools are plain callables with clear docstrings and simple type hints. Results
are compact JSON strings, not raw arrays. Large payloads are written to files and
referenced by path/evidence ID.

### 6.1 Orientation

| Tool | Purpose | Returns |
|---|---|---|
| `get_video_info()` | duration, fps, size, still/video | compact metadata |
| `get_overview()` | motion timeline, peaks, contact sheet path | timestamps + energy + path |
| `get_profile()` | player profile | JSON |
| `recent_reports(n)` | previous reports | compact JSON |

`get_video_info` and `recent_reports` are **not exposed in the MVP**; duration is
returned by `get_overview`, and history is injected into the initial prompt.

### 6.2 Visual inspection

| Tool | Purpose | Returns |
|---|---|---|
| `look(start, end, question, frames=4)` | ask the vision agent a focused question about a window | observations, signals, confidence, artifact paths |
| `zoom(start, end, focus, frames=6)` | crop/zoom on a region (racket, wrist, feet, table) and inspect | image path + observations |
| `frame_at(t)` | single frame for a precise moment | path + timestamp |

`look()` is the main “eyes” tool. It reuses the existing vision agent and the
`observe` prompts, but accepts a caller-supplied question rather than a fixed
coarse/fine prompt.

### 6.3 Measurement

| Tool | Purpose | Returns |
|---|---|---|
| `measure_motion(start, end, frames=8)` | activity, subject track, mechanics | compact metrics |
| `estimate_pose(start, end, frames=8)` | pose landmarks, angles, summaries | compact pose summary + overlay path |
| `detect_strokes(start, end, frames=8)` | wrist-speed peaks and hand | stroke events |
| `track_ball(start, end, frames=12)` | ball path/stats/overlay | compact stats + path |
| `estimate_racket_angle(start, end)` | racket-face angle/proxy at contact | value/proxy + confidence + method |
| `compare_windows(a_start, a_end, b_start, b_end)` | compare two windows | deferred; not MVP |

These are **post-MVP** capabilities. The MVP list is section 19.1.

`estimate_racket_angle` must be honest. Current code tracks pose wrists but not the
racket. The first implementation can return a **pose/vision proxy** with low/medium
confidence and an explicit method string. A dedicated racket detector is a later
project, not a blocker.

### 6.4 Evidence and reporting

| Tool | Purpose |
|---|---|
| `get_evidence(id)` | retrieve a compact evidence record |
| `list_evidence()` | list IDs and summaries (not MVP) |
| `save_report(report_json)` | validate and save final report |

The MVP tool list in section 19.1 is authoritative. `record_finding` and
`finish` are **not** MVP tools: measurement/inspection tools register evidence
automatically, and `save_report` is the only successful finish path. The report
can be saved if every issue includes valid evidence IDs.

### 6.5 Optional later tools

- `query_coaching_kb(issue)` — coach-validated drills/root causes.
- `compare_to_pro(player)` — reference motion.
- `table_calibration()` — court/table geometry for placement metrics.
- `audio_notes()` — coach voice notes or racket sound.
- `history_trend(metric)` — longitudinal query.

---

## 7. Evidence ledger and report schema

### 7.1 Evidence item

Every tool call creates one:

```json
{
  "id": "ev_0007",
  "tool": "estimate_pose",
  "args": {"start": 2.6, "end": 3.0, "frames": 8},
  "times": [2.61, 2.78, 2.88],
  "summary": "wrist speed peak 2.88s; elbow 122 deg; shoulder rotation 14 deg",
  "data_path": "runtime/data/artifacts/<stem>_investigation/<run_id>/pose_2.6_3.0.json",
  "artifact_paths": [".../pose_overlay.png"],
  "confidence": "high",
  "seconds": 1.8,
  "created_at": "..."
}
```

The full data stays on disk. The model sees the summary and can request
`get_evidence(id)` if it needs detail. This prevents context blow-up.

### 7.2 Report additions

Backward-compatible fields added to the saved report:

```json
{
  "mode": "investigator",
  "evidence": ["ev_0002", "ev_0003", "ev_0004"],
  "investigation": {
    "tool_calls": 12,
    "windows": [[2.6, 3.0], [4.0, 4.4]],
    "coverage": {"pose": true, "ball": false, "vision": true, "motion": true},
    "untested": ["ball placement", "serve type"],
    "hypotheses": [ ... ],
    "budget": {"tool_calls": 12, "seconds": 84, "tokens": 18200}
  }
}
```

`issues` gain optional `evidence_ids` and keep `evidence_times`. Existing readers
continue to work.

### 7.3 Validation

- Every issue must cite at least one valid evidence ID. Every issue timestamp must
  lie inside the union of the cited, non-overview evidence windows (tolerance
  ±0.15s). A timestamp that falls only in an uncited window is rejected.
- Overview evidence cannot be the only support for a finding.
- If a tool was never called, the corresponding coverage flag is false and
  `untested` must mention it.
- **Provenance is not truth.** The validator proves that a claim points to the
  tool output; it cannot prove the claim is correct. Metric-text matching is an
  advisory warning, not a semantic guarantee. Truth is measured in the benchmark
  and by human review.
- Confidence is capped by footage-quality checks and by the weakest supporting
  evidence.
- Unknown evidence IDs are rejected by `save_report`; the model gets a correction
  message.

---

## 8. Agent policy

The system prompt is the product contract. It should encourage investigation, not
checklist execution.

Draft:

```
You are Topspin Review's investigator. You are a coach with tools, not a report
writer following a fixed pipeline.

Your job is to produce a short, evidence-grounded coaching report. You decide what
to examine. Use only the tools that test a real hypothesis. You may ignore a
capability entirely if it is not relevant to this clip.

Start with get_overview. Form one or two hypotheses. Inspect a window, measure it,
or ask a focused visual question. When evidence conflicts, investigate or lower
confidence. Do not invent measurements.

Before saving:
- every issue must cite evidence IDs and timestamps;
- say what you did not examine;
- prefer three specific findings over ten generic ones;
- if the clip does not support coaching, say so and explain why.

Stop when the evidence is sufficient or the budget is nearly exhausted.
```

Important constraints:

- No fixed “call get_measurements first” instruction. The old agentic prompt does
  this; it biases the path.
- No requirement to call ball or pose.
- Explicit permission to return few findings, or a non-coaching observation.
- Explicit requirement to state coverage limitations.
- Low temperature for reproducibility, but not zero (tool-choice diversity).
- The model must not treat tool output as optional context; evidence IDs are
  mandatory.

---

## 9. openjiuwen integration

### 9.1 Builder changes

Current `TextParams` has `tools`, `rails`, `max_iterations`. Add:

```python
parallel_tool_calls: bool = False
enable_task_loop: bool = False
extra_rails: list[Any] = []
```

and pass them through `TextBuilder` to `create_deep_agent()`.

`create_deep_agent()` already supports `parallel_tool_calls` and
`enable_task_loop` (`openjiuwen/harness/factory.py:460-491`). This is a wrapper
change, not new factory work.

For Investigator:

- `max_iterations`: 30–40
- `parallel_tool_calls`: `False` (serial evidence, deterministic ordering)
- `enable_task_loop`: `False` (one investigation, not an outer task loop)
- rails: `memory` plus a **per-run** `TokenBudgetRail` in `extra_rails`. Do not
  include the global `token_budget` name; it would silently apply the wrong budget.
- workspace: a run-specific investigation directory
- recorder: the shared run recorder

### 9.2 Why text orchestrator plus vision tool

- The text model is better at long coaching reasoning and report language.
- The existing vision agent reads images through `read_file` and is instrumented,
  but its general shell/list tools caused wandering in the Phase 0 spike.
- `look()` must use a restricted visual inspector (only `read_file`, or a
  permission policy that denies shell/list tools), so the orchestrator does not
  need direct image access.
- A future single multimodal orchestrator can be added behind the same tool
  interface.

### 9.3 Streaming and progress

Two layers:

1. **Tool events** (must-have): each tool wrapper appends an event to
   `Progress`/a job event sink. The web SSE feed can show:
   `look(2.6–3.0)`, `pose`, `ball`, `finding`, `report`.
2. **Model tokens** (nice-to-have): use `Runner.run_agent_streaming()` or
   `DeepAgent.stream()` with `BaseStreamMode.OUTPUT` to show the model’s reasoning
   or answer tokens. This is not required for the first version.

The current `Runner.run_agent()` is non-streaming; the streaming API exists and
should be wrapped in `integrations/agents/agent/runner.py`, not called outside it.

### 9.4 Context management

- Tool results are summaries, not raw arrays.
- Full data goes to `runtime/data/artifacts/<stem>_investigation/<run_id>/`.
- Use `ContextEngine` compression/recall if a run exceeds context budget.
- Keep a deterministic ordering of tool calls; serial execution avoids race
  conditions in the ledger and makes traces reproducible.
- Do not use a module-global `_STATE`; every run gets its own
  `InvestigationContext`.

### 9.5 Budgets

Three independent limits:

- **Tool calls**: e.g. 24.
- **Wall clock**: e.g. 360s.
- **Tokens**: per-run `INVESTIGATOR_MAX_TOKENS` via a dedicated
  `TokenBudgetRail` in `extra_rails`.

Tool wrappers check the first two; the token rail checks the third. When a limit is
near, the tool returns a “budget remaining” note; when exceeded, the agent is told
to finish immediately. Because pose and frame decoding are blocking, the wall
limit is checked **between tools**, not preemptively. The strategy then uses the
partial-report path with limitations.

---

## 10. Topspin code changes

### 10.1 New files

| File | Responsibility |
|---|---|
| `core/stages/investigate/__init__.py` | stage package |
| `core/stages/investigate/context.py` | run-scoped context, paths, caches, budget |
| `core/stages/investigate/ledger.py` | evidence records, validation, summaries |
| `core/stages/investigate/tools.py` | tool factory (closures over context) |
| `core/stages/investigate/prompts.py` | investigator system prompt and tool guidance |
| `core/stages/investigate/render.py` | contact sheets, overlays, investigation artifacts |
| `core/stages/measure/toolbox.py` | interval-level sampling/measurement helpers |
| `core/strategies/investigator.py` | the new strategy |
| `domain/evidence.py` | pure evidence/finding schema and validation |

### 10.2 Existing files to modify

| File | Change |
|---|---|
| `core/params.py` | add `mode`, `investigation`, `evidence`, `budget` |
| `core/strategies/base.py` | make preparation overridable; use `ReportTarget` for finalize; disable demo-cache fallback for investigator |
| `core/strategies/resolve_strategy.py` | register `investigator`; keep `deterministic` default |
| `core/stages/measure/measure.py` | refactor to use `toolbox` without changing behaviour |
| `core/stages/coach/report_tools.py` | one shared `save_report`; validate before save; preserve evidence fields |
| `domain/report.py` | extend normalize/validate for evidence and investigation; allow investigator partial reports |
| `integrations/agents/agent/builder/params.py` | `parallel_tool_calls`, `enable_task_loop`, `extra_rails` |
| `integrations/agents/agent/builder/text.py` | pass new params to `create_deep_agent` |
| `integrations/agents/agent/runner.py` | add `run_agent_streaming` wrapper |
| `integrations/agents/agent/rails.py` | per-run token rail helper; do not use global name |
| `integrations/storage/store.py` | **run-scoped report target**: `add_report_at(path, report)`; `investigator_enabled` UI setting; stop relying on `_current_video` for investigator |
| `core/progress.py` | investigation events |
| `surfaces/gui2/server/models.py` | `mode` field |
| `surfaces/gui2/server/routes/analyze.py` | pass mode through both sync and async |
| `surfaces/gui2/server/jobs.py` | job mode, event sink, cancel event passed into run |
| `surfaces/gui2/server/routes/jobs.py` | include events in SSE payload |
| `surfaces/gui2/client/src/routes/settings/+page.svelte` | experimental Investigator availability toggle |
| `surfaces/gui2/client/src/lib/components/NewAnalysis.svelte` | mode selector |
| `surfaces/gui2/client/src/lib/components/LiveJob.svelte` | investigation feed |
| `surfaces/gui2/client/src/routes/result/+page.svelte` | investigation/coverage panel |
| `surfaces/cli/main.py` | `--mode` (keep `--agentic` alias) |
| `topspin_review/surfaces/api.py` / MCP | optional mode parameter |
| `docs/guides/USAGE.md` | document the mode and budgets |

### 10.3 Strategy interface

`base.Strategy` should gain an overridable preparation hook:

```python
def _prepare(self, params):
    ...
    self._prepare_measurement(params)   # deterministic default

def _prepare_measurement(self, params):
    measured = measure(...)
    ...
```

`InvestigatorStrategy` overrides `_prepare_measurement` to run only the cheap
overview and create the context. It must still populate enough `Params` fields for
`_finalize` (source, profile, session, timeline) without pretending pose/ball were
measured.

---

## 11. API and UI

### 11.1 Request

`AnalyzeRequest` gets `mode: "deterministic" | "agentic" | "investigator"`.
`agentic: bool` remains as a backward-compatible alias for `mode="agentic"`.

### 11.2 Job events

Extend `Progress` with an event list:

```json
{"t": 12.4, "kind": "tool", "name": "estimate_pose", "args": {"start": 2.6, "end": 3.0}, "status": "done", "summary": "elbow 122 deg"}
```

SSE sends events with the normal status. The UI groups them under
“Investigation” rather than the fixed pipeline stages.

### 11.3 Result page

Add a collapsible **Investigation** panel:

- tool calls and windows visited;
- coverage: pose/ball/motion/vision;
- evidence list with timestamps;
- “not assessed” list;
- cost/time.

This is not only observability; it is how the user learns to trust the report.

### 11.4 Mode selector

**Per-run choice** in `NewAnalysis` advanced section:

- Standard (recommended)
- Guided (existing agentic)
- Investigator (experimental, only when enabled below)

Show a short warning: slower, higher cost, variable path, cites evidence.

**Global availability** in `Settings ? Analysis`:

- ?Enable experimental Investigator mode? (off by default)
- backed by `ui_settings.investigator_enabled`, not by hiding a default mode
- the deployment flag `INVESTIGATOR_ENABLED` must also be true; if false, the
  setting is hidden and the API rejects the mode

The mode choice itself stays with the run; Settings only decides whether the
experimental option is offered.

---

## 12. Safety and guardrails

| Risk | Guardrail |
|---|---|
| Model invents a measurement | Tools are the only source; evidence IDs mandatory; validation rejects unknown references, not semantic error |
| Model wanders / never stops | Tool/wall/token budgets; max iterations; “finish now” instruction; timeout checked between tools |
| Context overflow | Compact tool summaries; data on disk; compression/recall; cap evidence in prompt |
| A tool crashes | Tool returns a structured error and the run continues; repeated failures stop with limitation |
| Bad video | Quality checks; lower confidence; report limitations |
| Concurrent runs | Per-run context + run-scoped storage and artifact paths; serial tool calls |
| Privacy | Local-first default; artifacts under run dir; no extra uploads beyond model calls |
| Non-determinism | Trace every tool call; store investigation metadata; evaluation uses evidence support, not exact text |
| Cost | Tool budget, model selection, cached windows, no full pose/ball unless asked |

Important product rule: **a free agent must be allowed to produce less coverage, but
not allowed to pretend it has more.** “I did not assess ball placement” is a valid
and valuable report.

---

## 13. Evaluation

### 13.1 Unit tests

- toolbox interval sampling and measurement parity with `measure()` on the same
  frames;
- evidence ledger IDs, ordering, validation, unknown-ID rejection;
- budget enforcement;
- report normalization with evidence fields;
- tool schema/docstrings;
- no openjiuwen imports outside `integrations/agents`.

### 13.2 Integration tests

- a scripted/stub investigator model that calls a fixed tool sequence, proving the
  loop and evidence flow without a live LLM;
- a real-model smoke test on 2–3 clips (nightly, not CI-blocking);
- failure/fallback test when a tool raises;
- concurrency test with two parallel investigator jobs.

### 13.3 Quality benchmark

Use `tests/eval/expected.json` and add investigator traces for the same clips.

Metrics:

- **Evidence integrity:** percentage of issues with valid evidence IDs and
  timestamps (target 100%).
- **Issue precision/recall:** compare with deterministic and coach labels.
- **Coverage:** which capabilities were used; is the limitation honest?
- **Cost:** model tokens and tool seconds per clip.
- **Latency:** median/p95.
- **Path diversity:** different clips should produce different tool sequences;
  otherwise the “free” mode is not actually free.
- **Failure rate:** crashes/timeouts.

Proposed gates before making it visible by default:

- 100% evidence integrity;
- precision not more than 5 points below deterministic on the benchmark;
- recall at least equal to deterministic;
- median cost ≤ 2.5× deterministic;
- p95 latency ≤ 2× deterministic;
- no increase in hallucination flags.

If these fail, keep Investigator as an experimental demo mode.

---

## 14. Rollout plan

### Phase 0 — foundations (1–2 days)

- **exit-gate spike:** real text-model tool calls + focused `look()` answers;
- `measure/toolbox.py` and parity tests;
- `InvestigationContext`, ledger, budget;
- refactor `base._prepare` hook;
- report schema extension.

### Phase 1 — CLI prototype (3–5 days)

- `InvestigatorStrategy`;
- 5 tools: `get_overview`, `look`, `estimate_pose`, `measure_motion`,
  `save_report`;
- no UI, no streaming;
- run on 3 clips, inspect traces by hand.

### Phase 2 — useful mode (1–2 weeks)

- `get_evidence` and the six-tool MVP surface;
- artifact generation;
- run-scoped storage, run-keyed artifacts, cancellation and queue;
- budget enforcement and fallback;
- API/job mode support;
- UI selector and investigation feed;
- evaluation runner (labels in parallel).

### Phase 3 ? product hardening (2?4 weeks)

- context compression/recall;
- streaming model output (optional);
- quality benchmark and regression suite;
- docs, cost telemetry, privacy review;
- hardening from real-model traces.

### Phase 4 — progressive/live (separate project)

- chunked video ingestion;
- event detector (stroke/point);
- persistent session memory;
- live feedback policy;
- latency and safety.

The first three phases are post-hoc investigation. Phase 4 is the “as the video
progresses” architecture.

Cumulative MVP estimate, including label acquisition and hardening: **6–10 weeks**
(not 2.5–4). The shorter estimate covers Phase 0–1 and a CLI only.

---

## 15. Risks and trade-offs

- **Non-determinism:** two runs may investigate different things. This is the
  feature, but it complicates support and evaluation. Mitigation: traces, seeds,
  evidence coverage, benchmark.
- **Cost:** a free agent can burn tokens on irrelevant windows. Mitigation: compact
  overview, budgets, cached results, cheap motion prefilter.
- **Model tool reliability:** small models may call tools poorly or loop. Mitigation:
  strong schema, few well-named tools, max iterations, validation errors fed back.
- **Context growth:** many tool results can overwhelm the context. Mitigation:
  summaries, evidence IDs, disk-backed details.
- **Racket angle:** the camera may not resolve the racket face. Do not promise
  exact degrees; use a proxy and confidence, or defer.
- **Evaluation:** no single “correct” investigation path. Judge evidence and
  outcomes, not sequence similarity.
- **Product clarity:** users may not understand why one run inspected ball and
  another did not. The coverage panel turns this into trust rather than confusion.

---

## 16. Acceptance criteria

The mode is ready for an experimental release when:

1. It can be selected from CLI, API and gui2.
2. The model can call tools in a different order on different clips.
3. It can omit ball or pose and still produce a valid report with explicit
   limitations.
4. Every issue cites a valid evidence ID and timestamp.
5. `save_report` rejects unsupported evidence and the model corrects it.
6. Tool, time and token budgets are enforced; a partial report is produced on
   exhaustion.
7. Deterministic mode is unchanged and remains the default.
8. The report page shows investigation, coverage and “not assessed.”
9. The benchmark meets the evidence/precision/cost gates or the mode stays hidden.
10. Two concurrent investigator jobs do not share state.

---

## 17. Example trace (target)

```
overview()
  evidence ev_0001: peaks 1.2, 2.8, 4.1; 14 frames; duration 6.4s
look(2.6, 3.1, "Where is contact and what does the racket face do?")
  evidence ev_0002: contact ~2.88s; racket face appears closed; confidence medium
estimate_pose(2.6, 3.0)
  evidence ev_0003: wrist peak 2.88s; elbow 122 deg; shoulder rotation 14 deg
look(4.0, 4.4, "Does the second stroke show the same contact pattern?")
  evidence ev_0004: same late contact on second stroke
save_report({
  issues: [
    {issue: "...", evidence_ids: ["ev_0002","ev_0003","ev_0004"], ...}
  ],
  limitations: ["Ball placement was not assessed", "Racket angle is a visual proxy"]
})
```

This is the product behaviour: the model investigated a hypothesis, ignored
irrelevant capabilities, cited evidence, and told the truth about what it did not
do.

---

## 18. Decisions for MVP

These are resolved for the first implementation:

1. **Orchestrator model:** text orchestrator + `look()` vision tool. A single
   multimodal orchestrator is a later experiment, not the MVP.
2. **Racket angle:** deferred. Do not ship a numeric racket-angle claim in MVP.
   The `look()` tool may return a visual observation with low/medium confidence.
3. **Tool count:** six MVP tools. The larger catalogue is post-MVP.
4. **Default mode:** deterministic stays default. Investigator is behind a feature
   flag and never selected automatically.
5. **Evidence UI:** advanced/collapsible panel in MVP; no change to the normal
   coaching view.
6. **Budgets:** defaults in section 21; all configurable.
7. **Coach knowledge base:** post-MVP. It is a tool, not a prerequisite.
8. **Streaming:** tool/progress events in MVP; model-token streaming is phase 3.
9. **Report compatibility:** evidence fields are additive; old reports remain
   readable.

### 18.1 Phase 0 spike results (2026-10-18)

The model/tool-calling spike passed with the current text model:

- one tool call, correct result (`TOOL_RESULT:42`);
- 3 model calls, **1,326 tokens**, **4.6s**.

The focused vision spike passed **only after restricting the agent**:

- 8-frame contact sheet, 2.5?3.2s window;
- 2 model calls, **12,143 tokens**, **7.9s**;
- returned valid JSON with signals and explicitly said racket/wrist detail was
  not visible;
- without the restriction, the agent called `bash`/`list_files` and hit
  `max_iterations`. The inspector must not expose a general shell.

Two implementation constraints came out of the spike:

1. The rendered image must live **inside the vision agent workspace**, or
   `read_file` is denied by the sandbox.
2. `look()` needs a restricted visual inspector (only `read_file`, or a permission
   policy that denies shell/list tools), not the general vision agent with bash.

The shared runtime workspace also produced a multi-minute file-lock wait in a
separate process. Investigator must use a run-specific workspace/media directory,
which is already required by the run-scoped plan.

### 18.2 Feasibility evidence and test status

This section exists so an external reviewer can distinguish what has been tested
from what is still assumed.

**Already tested**

| Check | Result |
|---|---|
| Text model can call an openjiuwen tool | **Pass**: correct tool result; 3 model calls, 1,326 tokens, 4.6s |
| Vision model can inspect a focused window | **Pass with restriction**: 2 calls, 12,143 tokens, 7.9s; valid JSON; correctly said racket/wrist detail was not visible |
| Image sandbox path | **Fail then fixed in design**: image must be inside the inspector workspace |
| Inspector tool restriction | **Fail then fixed in design**: general vision agent wandered into `bash`/`list_files`; prompt restriction works, permission restriction still to implement |
| Toolbox parity with `measure()` | **Pass**: unit test compares canonical fields |
| Run context/ledger isolation | **Pass**: two contexts do not share IDs or artifact paths |
| Evidence validation | **Pass**: unknown IDs, overview-only evidence, and out-of-window timestamps rejected |
| Transactional `save_report` | **Pass**: invalid report is not written; partial investigator report validated |
| Unit suite | **45 passed** at the time of writing |
| Ruff on changed files | **Clean** |
| End-to-end Investigator run on a copied 10.6s clip | **Prototype pass**: 3 issues, 9 evidence records, coverage motion/pose/vision, ball untested, 9 tool calls, 155.7s, 88 frames |

The E2E run used a copied demo clip and a temporary budget
(`INVESTIGATOR_MAX_SECONDS=240`, `INVESTIGATOR_MAX_TOKENS=60000`). Temporary video,
report, evidence and exports were removed.

**Not yet tested**

- CLI/API mode plumbing
- gui2 mode selector and investigation feed
- cancellation and the submission queue
- two concurrent Investigator jobs
- partial-report path under real budget/time exhaustion
- token-rail accounting (the prototype report showed `tokens: 0`, so this is not
  validated)
- multi-clip quality, coach labels and final budget calibration
- deterministic end-to-end regression after the refactor (unit parity is tested;
  a fresh deterministic run on a real clip is still useful)
- Android behavior (unchanged)
- inspector permission restriction (prompt restriction is tested; shell denial via
  permissions is not)

**Conclusion for a reviewer:** the core technical assumptions are demonstrated at
prototype level. The remaining work is integration, hardening, UI and evaluation,
not proof that the model/tools can work at all.

Reproduce the current checks with:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit -q
.venv\Scripts\python.exe -m ruff check topspin_review tests/unit
```

### 18.3 Implementation status after the prototype

This is deliberately separate from the target design. As of 2026-10-18:

**Implemented**

- `measure/toolbox.py`; deterministic `measure()` uses it
- `domain/evidence.py`, evidence ledger, run context, budget, cancellation event
- report schema extension and shared transactional `save_report`
- six MVP tools, focused visual inspector, `InvestigatorStrategy`
- run-scoped working report/artifact paths and final publish
- `Progress` investigation events
- one end-to-end Investigator report on a copied clip

**Partially implemented**

| Area | Status |
|---|---|
| Run-scoped storage | working + final writes exist; **atomic publish and per-stem lock are not implemented** |
| Token/usage accounting | rail is passed, but `Budget.tokens` is not connected to it and the inspector has a separate recorder; the prototype report showed `tokens: 0` and can undercount vision cost |
| Cancellation | context event exists; `JobManager` does not pass it yet |
| Progress events | `Progress` + context events exist; SSE/UI do not consume them |
| Inspector restriction | prompt restriction works; **permission-level denial of bash/list tools is pending** |
| Partial report | code path exists; not yet exercised under a real timeout/budget hit |
| Report finalize | working report and final report are written; exports are basic |

**Not started**

- CLI/API mode plumbing
- gui2 mode selector and investigation feed
- cancellation/queue wiring in jobs
- concurrent-run test
- evaluation runner and coach labels
- multi-clip benchmark and final budget calibration
- Android integration
- deterministic end-to-end regression after the refactor

**Deviations from the earlier design**

- `InvestigatorStrategy` overrides `_prepare` directly instead of using a
  `_prepare_measurement` hook. The hook remains a later refactor; it is not needed
  for the prototype.
- The inspector currently relies on a strict prompt; the permission-level
  restriction is still the target.
- The E2E run used a copied clip and a temporary 240s/60k budget; 155.7s and 9 tool
  calls were observed, so the default 360s is sensible but still needs calibration.

**Next order**

1. Fix and verify usage accounting: connect `Budget.tokens` to the rail and merge the inspector recorder into the run usage.
2. Add permission-level inspector restriction.
3. Wire CLI/API `mode` (sync and async).
4. Add cancellation/queue and atomic publish + per-stem lock.
5. Wire SSE/UI selector, investigation feed and coverage panel.
6. Build evaluation runner and coach labels.
7. Run deterministic vs Investigator benchmark and set final budgets.

---

# Part II — Implementation-ready specification

## 19. MVP scope

### 19.1 Included

The MVP proves the architecture on table tennis and one or two clean clips from
another racket sport.

- opt-in Investigator mode from CLI and gui2;
- cheap overview, no mandatory full measurement;
- six tools:
  1. `get_overview()`
  2. `look(start, end, question, frames)`
  3. `measure_motion(start, end, frames)`
  4. `estimate_pose(start, end, frames)`
  5. `get_evidence(evidence_id)`
  6. `save_report(report_json)`
- profile and previous-session summary are injected into the initial prompt; the
  investigator agent does **not** expose `get_profile` or `recent_reports`
- evidence ledger with IDs, times, summaries and disk-backed details;
- report validation that rejects unsupported evidence;
- tool/wall/token budgets and partial-report fallback;
- CLI/API mode plumbing and a basic UI selector;
- investigation trace stored on the report;
- deterministic mode unchanged.

### 19.2 Explicitly deferred

- ball tracking;
- stroke segmentation;
- racket-angle measurement;
- coach knowledge-base retrieval;
- pro comparison;
- table/court calibration;
- `compare_windows` (let the model compare existing evidence records instead);
- live/streaming video;
- multi-agent teams or openjiuwen subagents;
- model-token streaming in the UI;
- automatic default selection.

These are not forgotten; they are deliberately outside the MVP so the
orchestration loop can be evaluated first.

### 19.3 MVP success statement

> Given a short clip, the model can choose a non-predetermined investigation path,
> ignore irrelevant capabilities, and produce a report whose claims are fully
> traceable to tool evidence — within budget and without changing standard mode.

---

## 20. Tool contracts

All tools are plain callables inside `core/stages/investigate/tools.py`, built as
closures over one `InvestigationContext`. They are serialized by the agent
(`parallel_tool_calls=False`).

### 20.1 Common result envelope

Every tool returns a compact JSON string:

```json
{
  "ok": true,
  "evidence_id": "ev_0003",
  "summary": "wrist peak 2.88s; elbow 122 deg",
  "times": [2.61, 2.78, 2.88],
  "confidence": "high",
  "data_path": "runtime/data/artifacts/<stem>_investigation/<run_id>/ev_0003.json",
  "artifacts": [".../ev_0003_pose.png"],
  "truncated": false
}
```

Error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "WINDOW_OUT_OF_RANGE",
    "message": "end 8.2s exceeds duration 6.4s",
    "retryable": false
  }
}
```

Rules:

- Never return full landmark arrays, raw frames or base64 in the tool result.
- Put large data in `ev_<id>.json` and return the path.
- `summary` is at most 1,000 characters.
- `times` are seconds, rounded to two decimals.
- Every successful **measurement or inspection** tool call registers exactly one
  evidence record. `get_evidence`, `save_report`, `get_profile` and
  `recent_reports` are exempt. `get_overview` registers orientation evidence.
- Tool errors do not crash the run; the agent sees the error and can correct.

### 20.2 `get_overview()`

Input: none.

Returns:

```json
{
  "ok": true,
  "evidence_id": "ev_0001",
  "duration": 6.4,
  "fps": 30,
  "size": [1920, 1080],
  "is_still": false,
  "peak_times": [1.2, 2.8, 4.1],
  "activity": [{"t": 0.0, "energy": 1.2}, ...],
  "contact_sheet": ".../overview.png",
  "summary": "6.4s clip; motion peaks at 1.2, 2.8 and 4.1s"
}
```

Limits:

- reserves and samples at most 32 probe frames;
- activity series downsampled to at most 40 points;
- no pose or ball.

### 20.3 `look(start, end, question, frames=4)`

Input:

- `start`, `end`: seconds, `0 <= start < end <= duration`;
- window length at most 10s;
- `frames`: 1–12;
- `question`: 1–400 characters.

Behavior:

- sample frames in the window;
- render a focused contact sheet/zoom image;
- call the existing vision agent with the question, the player profile and the
  measured window context;
- return structured observations and signals.

Returns:

```json
{
  "ok": true,
  "evidence_id": "ev_0002",
  "summary": "contact ~2.88s; racket face appears closed; medium confidence",
  "times": [2.88],
  "observations": "...",
  "signals": [
    {"signal": "...", "evidence_times": [2.88], "confidence": "medium"}
  ],
  "artifacts": [".../look_2.6_3.1.png"],
  "confidence": "medium"
}
```

The vision agent must be instructed not to invent spin, ball speed or exact
angles. Any numeric claim must come from a measurement tool, not from `look()`.

### 20.4 `measure_motion(start, end, frames=8)`

Returns compact activity, subject box/track summary, mechanics and peak time.
No pose, no ball. The detailed series goes to disk.

Input limits: valid window, `1 <= frames <= 8`, frame budget available. Errors:
`WINDOW_OUT_OF_RANGE`, `BUDGET_EXHAUSTED`, `NO_FRAMES`.

### 20.5 `estimate_pose(start, end, frames=8)`

Returns pose summaries, joint angles, wrist-speed peaks and an overlay path.
Detailed landmarks go to disk. The summary must include the number of frames with
usable pose and a confidence note.

Input limits: valid window, `1 <= frames <= 8`, pose available, frame budget
available. Errors: `WINDOW_OUT_OF_RANGE`, `POSE_UNAVAILABLE`,
`BUDGET_EXHAUSTED`, `NO_FRAMES`. A failed pose estimate creates no evidence and
must be reported as a limitation if it affects the conclusion.

### 20.6 `compare_windows` — deferred

`compare_windows` is not part of the MVP. It duplicates measurement and creates
composite evidence. The MVP model can call `get_evidence()` on two records and
compare them in its own reasoning. The later design is kept in section 31 for
reference only.

### 20.7 `get_evidence(evidence_id)`

Returns the compact evidence record, a bounded `details` field (max 2,000
characters or a small structured series) and the data path. Used when the model
needs detail without keeping everything in context. The full payload remains on
disk.

### 20.8 `save_report(report_json)`

The only way to finish successfully.

Validation:

- required fields per `domain/report.py`;
- every issue must have at least one `evidence_ids` entry;
- every ID must exist and be owned by this run;
- every timestamp must fall within the union of the cited, non-overview evidence
  windows (tolerance ±0.15s);
- confidence must be one of high/medium/low;
- if `mode == "investigator"`, `investigation.coverage` and `untested` are required.

On failure, return:

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_REPORT",
    "message": "issue 1 has no evidence_ids",
    "problems": ["issue 1 has no evidence_ids", "issue 1 confidence is invalid"],
    "retryable": true
  }
}
```

The report is not saved. The model gets one or more correction attempts; after
`INVESTIGATOR_MAX_REPORT_FIXES` the strategy fails over to a partial report with a
clear error.

### 20.9 Tool versioning

Each tool has a stable name and a `toolset_version` in the report. Renaming or
changing the meaning of a tool is a version bump. Old traces must remain readable.

---

## 21. Evidence and report schema v1

### 21.1 Evidence record v1

```json
{
  "id": "ev_0007",
  "run_id": "20261018T090000Z-abc12345",
  "tool": "estimate_pose",
  "tool_version": "1",
  "args": {"start": 2.6, "end": 3.0, "frames": 8},
  "window": [2.6, 3.0],
  "times": [2.61, 2.78, 2.88],
  "summary": "wrist speed peak 2.88s; elbow 122 deg; 7/8 usable frames",
  "confidence": "high",
  "data_path": "..._investigation/<run_id>/ev_0007.json",
  "artifacts": ["..._investigation/<run_id>/ev_0007_pose.png"],
  "seconds": 1.8,
  "created_at": "2026-10-18T09:00:04Z"
}
```

Evidence is immutable. Corrections create a new ID.

### 21.2 Report additions

```json
{
  "mode": "investigator",
  "evidence": ["ev_0002", "ev_0003", "ev_0004"],
  "issues": [
    {
      "issue": "...",
      "evidence_times": [2.88, 4.12],
      "evidence_ids": ["ev_0002", "ev_0003", "ev_0004"],
      "confidence": "medium"
    }
  ],
  "investigation": {
    "schema_version": 1,
    "prompt_version": "inv-v1",
    "toolset_version": "tools-v1",
    "model": "...",
    "tool_calls": 12,
    "windows": [[2.6, 3.0], [4.0, 4.4]],
    "coverage": {"motion": true, "pose": true, "vision": true, "ball": false},
    "untested": ["ball placement", "serve type"],
    "budget": {
      "tool_calls": 12,
      "seconds": 84,
      "tokens": 18200,
      "frames": 46
    },
    "stop_reason": "evidence_sufficient"
  }
}
```

### 21.3 Migration and compatibility

- Old reports have no `mode`/`evidence`/`investigation`; UI treats them as
  `deterministic`.
- Existing `issues` without `evidence_ids` remain valid for deterministic mode.
- Investigator reports are rejected without evidence IDs.
- Export/report renderers ignore unknown fields; add evidence sections only when
  `mode == "investigator"`.
- The evidence details file is the source of truth if summaries and report differ.

### 21.4 Coverage rules

- `coverage.pose` is true only if `estimate_pose` succeeded at least once.
- `coverage.ball` is false unless a ball tool exists and was called.
- `untested` is generated from false coverage flags plus any explicit model notes.
- If no visual tool was called, `vision` is false and the report must say so.
- A report with only motion evidence is valid, but cannot claim technical findings
  that require pose or vision.

---

## 22. Budgets and cost defaults

All values are environment-configurable and stored in the report.

| Limit | Default | Meaning |
|---|---:|---|
| `INVESTIGATOR_MAX_TOOL_CALLS` | 24 | successful and failed tool calls both count |
| `INVESTIGATOR_MAX_SECONDS` | 360 | wall clock for the investigation loop |
| `INVESTIGATOR_MAX_TOKENS` | 80000 | model tokens for the run |
| `INVESTIGATOR_MAX_FRAMES` | 160 | total decoded frames across all tools |
| `INVESTIGATOR_MAX_WINDOW_SECONDS` | 10 | max length of one window |
| `INVESTIGATOR_MAX_WINDOW_FRAMES` | 12 | max frames per tool call |
| `INVESTIGATOR_MAX_REPORT_FIXES` | 2 | validation correction attempts |
| `INVESTIGATOR_MAX_CONCURRENT` | 1 | concurrent investigator runs per process |

Frame accounting (enforced by the tool wrapper, not by the model):

| Tool | Frames per call |
|---|---:|
| `get_overview` | 32 |
| `look` | 12 max |
| `measure_motion` | 8 max |
| `estimate_pose` | 8 max |
| `get_evidence` / `save_report` | 0 |

`INVESTIGATOR_MAX_FRAMES=160` is a hard total. A run cannot spend 24 × 12 frames;
the wrapper rejects a call when the next request would exceed the total. The model
sees `BUDGET_EXHAUSTED` and must finish with current evidence.

Phase 0 measured one 8-frame `look()` at **12,143 tokens / 7.9s** and a trivial
text tool call at **1,326 tokens / 4.6s**. The 80,000 default therefore supports
roughly 5?6 visual inspections plus reasoning. If the benchmark needs more
coverage, raise `INVESTIGATOR_MAX_TOKENS` to 120,000 rather than increasing frame
counts blindly.

Budget behavior:

- at 80% of any limit, tool results include `budget_warning`;
- at 100%, tools return `BUDGET_EXHAUSTED` and instruct the model to save a partial
  report;
- wall-clock time is checked **between tools**. Pose and frame decoding are
  blocking and cannot be preempted mid-call; the strategy may overshoot by one
  tool call;
- a partial report is saved only if it passes the evidence rules; otherwise the
  run uses the fallback rules in section 34.

Cost target: median Investigator cost **≤ 2.5×** deterministic on the benchmark.
If exceeded, reduce windows/frames or switch to a cheaper orchestrator model.

---

## 23. Execution, cancellation, concurrency and resume

### 23.1 Mode plumbing

- `AnalyzeRequest.mode`: `"deterministic" | "agentic" | "investigator"`.
- `agentic: true` maps to `"agentic"` only when `mode` is absent.
- both `/analyze` and `/analyze/async` honor the mode (the current sync route does
  not pass the agentic flag; fix this while adding the mode).
- CLI: `--mode investigator`; keep `--agentic` as a deprecated alias.
- `INVESTIGATOR_ENABLED` deployment flag defaults to `false`; the UI hides the
  setting and NewAnalysis option when false.
- `ui_settings.investigator_enabled` defaults to `false`; when the deployment flag
  is true, Settings exposes the toggle and NewAnalysis shows the option only when
  the user has enabled it.
- `/settings` GET/PATCH carries `investigator_enabled` next to `show_demo`.
- The API rejects `mode="investigator"` when either flag is off.

### 23.2 Cancellation

- `JobManager` creates a per-job `threading.Event`; `Job.snapshot()` exposes no
  internals, but the run receives the event through `InvestigationContext`.
- The job manager currently only flips a status flag (`jobs.py:102-109`). Add an
  explicit `cancel_event` to the job and pass it into the strategy.
- Every tool checks the event before doing expensive work and returns
  `CANCELLED`.
- The strategy checks before/after each model call; openjiuwen runs cannot always
  be interrupted mid-call, so cancellation is best-effort.
- A cancelled run is discarded, not saved as a report.
- `JobManager._run` must catch `InvestigationCancelled` and mark the job
  `cancelled`, not `failed`, and must not send an error traceback.

### 23.3 Concurrency and storage

- No module-global state. `InvestigationContext` is per run.
- **Current storage is not concurrency-safe.** `store.set_current_video()` and
  `_current_video` are module globals (`store.py:38`); `add_report` and
  `patch_last_report` write through them. Two investigator jobs would overwrite
  each other regardless of per-run context.
- Add `store.add_report_at(path, report)` and `store.patch_report_at(path, patch)`.
  Investigator uses an explicit `ReportTarget` path from the run context. The
  deterministic path keeps the old API.
- Artifact paths must be run-keyed:
  `<stem>_investigation/<run_id>/`, not `<stem>_investigation/`. This prevents
  same-video or concurrent runs from overwriting evidence and overlays.
- Tools are serial by default.
- The ledger, cache and progress event sink are thread-safe.
- `INVESTIGATOR_MAX_CONCURRENT` gates submissions; extra jobs stay queued. The
  queue itself does not exist today and must be added to `JobManager`.
- A per-stem lock serializes same-video runs. Different videos may run
  concurrently when the global limit allows it.

### 23.4 Resume

Not in MVP. The trace and evidence are stored, so a future version can resume by
replaying tool calls and asking the model to continue. Do not promise resume until
the loop is stable.

### 23.5 Partial reports

Use the full algorithm in section 34. Key rules:

1. Ask the model for one tool-free final answer using existing evidence.
2. Validate it; save if valid.
3. If validation fails, build a minimal report with populated `date`, `sport`,
   `focus`, evidence list, `limitations` including the stop reason, and
   `stop_reason`.
4. Allow empty `issues` only for investigator partial reports.
5. Never save unsupported issues just to have a report.
6. Never let the inherited `Strategy.analyze()` demo-cache fallback return a
   stale report. Investigator must bypass or disable that fallback explicitly.

### 23.6 Run-scoped report target and readers

The report must remain discoverable by the existing readers. Use a two-stage path:

1. **Working copy:** `runtime/data/.runs/<run_id>/<stem>_report.json`, plus
   `runtime/data/artifacts/<stem>_investigation/<run_id>/`.
2. **Publish:** on successful finalize, atomically replace the standard
   `runtime/data/<stem>_report.json` from the working copy.

`ReportTarget`:

```python
@dataclass
class ReportTarget:
    stem: str
    run_id: str          # filesystem-safe: YYYYMMDDTHHMMSSZ-<8 hex>
    working_report: Path
    final_report: Path
    artifact_dir: Path
```

Because the final path is standard, `get_reports`, `find_report`,
`recent_reports`, deletion and exports continue to work **without scanning
`.runs/`**. Add `store.add_report_at(path, report)` and
`store.patch_report_at(path, patch)`; keep the old API for deterministic mode.

`base._prepare()` currently calls `store.set_current_video()` and
`base._finalize()` uses `store.patch_last_report()`, `store.report_path()` and
`demo_cache.save()`. Investigator must override that path:

- `InvestigatorStrategy._prepare()` creates a `ReportTarget` and does **not**
  call `store.set_current_video()`;
- `_finalize()` patches the working report via `ReportTarget`;
- publish atomically at the end;
- disable `demo_cache.save()` for investigator (never return a stale demo-cache
  report).

The working directory `.runs/` is ignored by report discovery and can be pruned
after publish.

---

## 24. Evaluation dataset and gates

### 24.1 Dataset

Create `tests/eval/investigation/` with:

- 8 clips total for MVP:
  - 4 table tennis: clean side-on, two players, overhead, poor lighting;
  - 2 tennis or badminton: clean and one difficult;
  - 1 clip with a stroke-type switch;
  - 1 still photo.
- `manifest.json`: source path, sport, duration, capture notes.
- `labels.json`: coach-labelled top findings, expected themes, key timestamps,
  expected coverage (pose/ball/vision) and acceptable limitations.
- Keep clips out of the repo if large; use a downloadable fixture with checksums.

**Label acquisition is a separate dependency, not a 2–3 day coding task.** It needs
a coach/analyst, a labelling rubric and review time. Plan **1–2 weeks** for the
first 8 clips, and do not schedule the quality gates as if labels already exist.
The engineering runner can be built in parallel, but the gates wait for labels.

### 24.2 Metrics

- **Evidence integrity:** issues with valid evidence IDs and in-window timestamps.
- **Finding precision:** labelled findings matched by theme + timestamp tolerance.
- **Finding recall:** labelled findings found.
- **Coverage honesty:** untested capabilities are declared; no false coverage.
- **Hallucination flags:** reuse `domain/evaluate.py` plus new rules for
  investigator evidence.
- **Cost:** tokens, tool seconds, frame decodes.
- **Latency:** median and p95.
- **Path diversity:** unique tool sequences across clips.
- **Failure rate:** crashes, validation failures, timeouts.

### 24.3 Benchmarks

Run each clip with:

1. deterministic;
2. investigator, text + `look`;
3. (phase 3 experiment) multimodal orchestrator.

Store traces under `tests/eval/investigation/runs/<date>/`.

### 24.4 Gates for experimental release

- Evidence integrity: **100%**.
- Precision: not more than **5 points below** deterministic.
- Recall: **at least equal** to deterministic on labelled themes.
- Median cost: **≤ 2.5×** deterministic.
- p95 latency: **≤ 2×** deterministic.
- No increase in hallucination flags.
- At least **3 distinct tool sequences** across the 8 clips.

If a gate fails, Investigator remains hidden or limited to internal demos.

---

## 25. Prompt, versioning and observability

### 25.1 Versions

- `INVESTIGATOR_PROMPT_VERSION = "inv-v1"`
- `INVESTIGATOR_TOOLSET_VERSION = "tools-v1"`
- `INVESTIGATOR_SCHEMA_VERSION = 1`

Write all three into `investigation`. A prompt change that alters tool policy is a
version bump.

### 25.2 Prompt storage

- System prompt in `core/stages/investigate/prompts.py`.
- No runtime string concatenation of untrusted video metadata into the system
  prompt; pass metadata as a user message/tool result.
- Profile and history are data, not instructions.
- Keep the prompt short enough to leave room for tool observations.

### 25.3 Trace

Persist:

- every tool call (name, args, evidence ID, seconds);
- every model call (via existing recorder/observability);
- validation errors and correction attempts;
- stop reason and budget usage;
- prompt/toolset versions.

The trace is for debugging and evaluation, not for the normal user.

### 25.4 Observability fields

Add to the report usage block:

```json
{
  "mode": "investigator",
  "tool_seconds": 84.2,
  "tool_calls": 12,
  "decoded_frames": 46,
  "investigation_tokens": 18200
}
```

---

## 26. Implementation backlog

Estimates assume one focused engineer. Dependencies are listed.

| # | Task | Depends on | Estimate | Acceptance |
|---|---|---|---|---|
| 1 | Extract `measure/toolbox.py`; parity tests with `measure()` | — | 1–2d | deterministic output unchanged |
| 2 | `InvestigationContext`, budget, event sink | 1 | 1d | two contexts do not share state |
| 3 | `EvidenceLedger` + `domain/evidence.py` | 2 | 1–2d | IDs, immutability, unknown-ID rejection |
| 4 | MVP tools: overview, motion, pose, evidence | 1–3 | 2–3d | tool unit tests pass |
| 5 | `look()` tool using vision agent | 4 | 1–2d | focused question; no invented metrics |
| 6 | `InvestigatorStrategy` + override prepare hook | 2–5 | 2d | CLI run produces a report |
| 7 | Extend `TextParams`/`TextBuilder` for serial tool calls | 6 | 0.5d | tools run in order |
| 8 | Report schema extension + shared `save_report` validation | 3,6 | 1–2d | unsupported issues rejected |
| 9 | Run-scoped storage + run-keyed artifacts | 2,8 | 1–2d | two same-video runs do not overwrite |
| 10 | Budgets, timeout, partial report, fallback | 6,8 | 2d | budget exhaustion produces valid partial report |
| 11 | Cancellation event + submission queue | 2,10 | 1–2d | cancel is checked between tools; queue works |
| 12 | CLI `--mode` and API job mode plumbing | 6 | 1d | sync and async both honor mode |
| 13 | Progress events + SSE investigation feed | 12 | 1–2d | UI shows tool calls live |
| 14 | NewAnalysis mode selector + result Investigation panel | 13 | 2d | hidden when feature flag off |
| 15 | Evaluation runner (labels are separate) | 8 | 2–3d | metrics report generated |
| 16 | Evaluation labels (coach/analyst) | clips selected | **1–2w** | labels reviewed |
| 17 | Benchmark and gate run | 15,16 | 2d | gates pass or mode stays hidden |
| 18 | Documentation + privacy review | 14–17 | 1d | docs updated; no secrets in traces |

Total MVP: roughly **6–10 weeks** for one engineer. The earlier 2.5–4 week
estimate covers only Phase 0–1 and a CLI with five tools. Tasks 4/5 and 13/14 are
parallelizable; label acquisition (task 16) is the critical path for the quality
gates.

### 26.1 Order of work

0. **Phase 0 exit gate:** verify real openjiuwen tool calling with the chosen text
   model, and verify focused `look()` answers with the vision model. If either
   fails, stop and revisit the model/tool design.
1. Toolbox + context + ledger.
2. Run-scoped storage + run-keyed artifacts.
3. Tools and `look`.
4. Strategy + serial tool loop.
5. Report validation.
6. Budgets/fallback + cancellation/queue.
7. API/CLI.
8. UI.
9. Evaluation runner + labels.
10. Benchmark and gates.

Do not start with UI or the full tool catalogue.

### 26.2 Definition of done for MVP

- A developer can run `--mode investigator` on a clip and get a report.
- The trace shows a different tool path on at least two clips.
- The model can omit pose or ball and still produce a valid report with
  limitations.
- Every investigator issue has valid evidence IDs.
- Budget exhaustion produces a valid partial report, never a fabricated one.
- Standard mode is unchanged; existing tests pass.
- The benchmark gates are measured and documented, even if not all pass.
- The feature is hidden unless `INVESTIGATOR_ENABLED=true`.

---

## 27. Post-MVP roadmap

1. **Ball tool** with dense sampling and a clear confidence note.
2. **Stroke segmentation** and per-stroke comparison.
3. **Racket-angle proxy** or dedicated detector, with honest confidence.
4. **Coach knowledge base** as a tool.
5. **Evidence UI** for normal users (simplified coverage).
6. **Model-token streaming** into the job feed.
7. **Multimodal orchestrator** experiment.
8. **Chunked/live** investigation with persistent session state.
9. **Resume** from a stored trace.
10. **Automatic mode selection** only after benchmark evidence.

---

# Part III — v1.1 implementation contracts

This part removes the remaining ambiguities. It is the contract an engineer should
implement against.

## 28. `look()` implementation contract

### 28.1 New inspect helper

Add `core/stages/observe/inspect.py`:

```python
async def inspect(
    agent: Any,
    frames: list[Image.Image],
    timestamps: list[float],
    question: str,
    profile: dict,
    *,
    media_dir: Path,
) -> dict:
    ...
```

It must:

1. Validate `frames` and `timestamps`.
2. Render one `focused_sheet` image using `imaging.contact_sheet` with timestamps
   and 2–12 frames.
3. Build `INSPECT_PROMPT` (below).
4. Call the existing vision agent via `observe.ask_agent.ask(agent, prompt)`.
5. Parse the JSON; validate the shape.
6. On invalid JSON or missing fields, retry once with a short “return only the
   requested JSON” message.
7. Return:

```json
{
  "observations": "...",
  "signals": [
    {"signal": "...", "evidence_times": [2.88], "confidence": "medium"}
  ],
  "limitations": ["..."],
  "artifact_paths": ["..."]
}
```

### 28.2 Prompt

```text
You are looking at {n} frames sampled in order from {start:.2f}s to {end:.2f}s
of a {sport} session. Player: level {level}, {hand}-handed, working on {goal}.

Question: {question}

Read this image once: {sheet_path}
Do NOT call bash, list_files, or any tool other than read_file. Do NOT inspect
the file with Python. After read_file returns the image, answer immediately.

Answer only what the frames show. Do not invent spin, ball speed or exact
angles. If the racket face, wrist or contact point is not visible, say so.
Return ONLY this JSON:
{
  "observations": "short paragraph",
  "signals": [
    {"signal": "short finding", "evidence_times": [seconds], "confidence": "high|medium|low"}
  ],
  "limitations": ["..."]
}
```

### 28.3 `look()` tool wrapper

```python
async def look(start: float, end: float, question: str, frames: int = 4) -> str:
    """Inspect a time window with the vision model and return observations."""
    return await ctx.run_tool(
        "look",
        {"start": start, "end": end, "question": question, "frames": frames},
        window=(start, end),
        impl=lambda: _look_impl(start, end, question, frames),
    )
```

`_look_impl`:

- clamps `frames` to 1–12;
- rejects questions longer than 400 characters;
- rejects windows longer than `INVESTIGATOR_MAX_WINDOW_SECONDS`;
- calls `sampling.sample_window`;
- calls `observe.inspect.inspect`;
- derives `summary` from the first 1–2 signals or observations;
- derives `confidence` as the minimum confidence of returned signals, default
  `"low"`;
- returns the result; `ctx.run_tool` writes evidence and artifacts.

### 28.4 Important boundary

`look()` is visual evidence, not measurement. If it says “racket face looks
closed,” that is an observation with confidence, not a degree value. Numeric
racket-angle claims remain out of MVP.

---

## 29. Tool execution and evidence registration

### 29.1 One wrapper for every tool

No tool writes evidence itself. Every measurement or inspection tool goes through
`InvestigationContext.run_tool()`:

**Evidence-exempt tools:** `get_evidence` and `save_report`. `get_overview` **does**
create `ev_0001` (orientation evidence), but its window is the whole clip and
cannot be the only evidence for a finding. `get_profile` and `recent_reports` are
not exposed to the investigator agent.

The wrapper owns frame accounting. It checks the **requested** frame count before
calling `impl()`; a result's internal `_frames` count is then consumed against
`INVESTIGATOR_MAX_FRAMES`.

All MVP tool wrappers are `async def`, even when the implementation is synchronous.
This gives openjiuwen one tool-call contract.

```python
async def run_tool(self, name, args, *, window=None, impl):
    self.budget.check_tool_call()
    self.budget.check_frames(args.get("frames", 0))
    self.cancel.check()
    started = time.monotonic()
    self.progress.emit("tool_started", name=name, args=args)

    try:
        result = impl()
        if inspect.isawaitable(result):
            result = await result
        evidence = self.ledger.add(
            tool=name,
            args=args,
            window=window,
            result=result,
            seconds=time.monotonic() - started,
        )
        self.budget.consume_tool(
            seconds=time.monotonic() - started,
            frames=result.get("_frames", args.get("frames", 0)),
        )
        self.progress.emit(
            "tool_finished",
            name=name,
            evidence_id=evidence.id,
            summary=evidence.summary,
            seconds=evidence.seconds,
        )
        return evidence.envelope()
    except InvestigationError as exc:
        self.progress.emit("tool_error", name=name, error=exc.code)
        return exc.envelope()
    except Exception as exc:
        self.progress.emit("tool_error", name=name, error="TOOL_FAILED")
        return {
            "ok": False,
            "error": {"code": "TOOL_FAILED", "message": str(exc), "retryable": False},
        }
```

Do not duplicate evidence logic in individual tools.

### 29.2 Evidence storage

`EvidenceLedger.add()`:

1. allocate `ev_0001` under a lock;
2. write `ev_XXXX.json` with the full result (minus frames/images);
3. copy/write artifact paths under
   `runtime/data/artifacts/<stem>_investigation/<run_id>/`;
4. build a compact summary (max 1,000 chars) and a bounded `details` field
   (max 2,000 chars or a small series);
5. append an immutable `EvidenceRecord` to the in-memory list;
6. update coverage flags;
7. return the record.

Data layout:

```
runtime/data/artifacts/<stem>_investigation/<run_id>/
  overview.png
  ev_0001.json
  ev_0001_look.png
  ev_0002.json
  ev_0002_pose.png
  investigation.json        # full trace, written at finalize
```

The full trace is not put in the model context. `get_evidence(id)` returns the
record summary and path only.

### 29.3 Evidence ID rules

- IDs are run-local and monotonic.
- A failed tool call does not create an evidence ID.
- A retry creates a new ID; never mutate an old record.
- The report may reference only IDs from the same run.
- `get_evidence` with an unknown ID returns `UNKNOWN_EVIDENCE`.

### 29.4 Tool decorator versus explicit wrappers

Use explicit functions for the six MVP tools. `functools.wraps` and auto-schema
extraction can hide the real signature; explicit signatures are safer for
openjiuwen's tool metadata. Each function has a short docstring and simple type
hints.

---

## 30. Per-run token budget

### 30.1 Do not use the global budget silently

`TokenBudgetRail` currently reads `backend_settings.token_budget()` (global
`TOKEN_BUDGET`). Investigator needs a per-run value.

Add to `TextParams`:

```python
extra_rails: list[Any] = field(default_factory=list)
```

`TextBuilder.build()`:

```python
rails = [*backend_rails.resolve(self.params.rails), *self.params.extra_rails]
```

`InvestigatorStrategy` builds:

```python
from topspin_review.integrations.agents.agent.rails import TokenBudgetRail
from topspin_review.integrations.agents.agent.rails import _count_tokens

rail = TokenBudgetRail(config.investigator_max_tokens(), _count_tokens)
```

and passes `extra_rails=[rail]` in `TextParams`.

### 30.2 Precedence

1. `INVESTIGATOR_MAX_TOKENS` if set and > 0.
2. Else `TOKEN_BUDGET` if set and > 0.
3. Else `80000` (the documented default).

`config.rails()` must be filtered for Investigator: remove the `token_budget`
name and add the explicit per-run rail via `extra_rails`. Do not apply both the
global and per-run rails.

### 30.3 Coverage limitation

`TokenBudgetRail` sees orchestrator model calls. The vision agent makes separate
model calls and is not on that rail. For MVP:

- the wall-clock and tool-call budgets bound vision work;
- after each `look()`, `InvestigationContext` compares recorder usage against the
  run limit and returns a `budget_warning` when above 80%;
- a hard post-run check prevents a report from claiming budget compliance when it
  is not.

For MVP, this is accepted as an accounting gap, not a reason to add another rail.
Before budget calibration, connect `Budget.tokens` to the rail and merge the inspector
recorder into the run usage so the report reflects vision cost.

### 30.4 Force-finish behavior

When the rail fires:

- the agent should produce a tool-free final answer;
- if it does not save a report, `InvestigatorStrategy` uses the partial-report
  algorithm in section 34;
- `stop_reason` is `token_budget`.

---

## 31. `compare_windows` contract — deferred

**Do not implement this in the MVP.** It is retained only as a future design.
The MVP model compares existing evidence records through `get_evidence()` and its
own reasoning. If this tool is revived, it must not create composite evidence; it
must reference the two existing window evidence IDs.

### 31.1 Input

```python
def compare_windows(
    a_start: float,
    a_end: float,
    b_start: float,
    b_end: float,
    focus: str = "motion",
) -> str:
    """Compare two inspected windows and report measurable differences."""
```

- `focus` is `"motion"` or `"pose"`; default `"motion"`.
- Both windows must satisfy the normal window limits.
- Windows may overlap.
- No ball comparison in MVP.

### 31.2 Behavior

For each window:

1. sample 8 frames (or `INVESTIGATOR_MAX_WINDOW_FRAMES`);
2. run `metrics.analyze(..., with_pose=(focus == "pose"))`;
3. optionally run `pose.estimate` for `focus="pose"`;
4. find the peak-motion time in each window;
5. align the comparison at those peaks (report the offset explicitly).

### 31.3 Output

```json
{
  "ok": true,
  "evidence_id": "ev_0009",
  "summary": "second window contacts 0.12s later; elbow 9 deg lower",
  "times": [2.88, 4.12],
  "delta": {
    "peak_offset_s": 0.12,
    "mean_energy_delta": -0.4,
    "lower_lateral_range_delta": -0.03,
    "crouch_change_delta": 0.01,
    "elbow_delta_deg": -9.0,
    "knee_delta_deg": 4.0
  },
  "evidence_ids": ["ev_0007", "ev_0008"],
  "confidence": "medium"
}
```

If `focus="motion"`, omit elbow/knee keys. If no usable pose exists, return
`POSE_UNAVAILABLE` rather than inventing a delta.

### 31.4 Evidence

The tool creates one evidence record for the comparison and references the two
window records (`evidence_ids`). It does not duplicate their data.

---

## 32. `save_report` transaction

### 32.0 One implementation only

There must be **one** `save_report` implementation in
`core/stages/coach/report_tools.py`, shared by deterministic and investigator
agents. The investigator tool wrapper calls that function; it does not copy it.
The current function saves before validating (`report_tools.py:66-69`); change the
order to validate first, then save.

Context injection uses a closure so the model still sees only `report_json`:

```python
# shared core function, not exposed directly to the model
def save_report_for(run, report_json: str) -> str:
    ...

# investigator tool factory
def make_save_report_tool(run):
    def save_report(report_json: str) -> str:
        """Save the coaching report. ..."""
        return save_report_for(run, report_json)
    return save_report
```

Do not add `run`, `context` or `target` to the tool signature; openjiuwen would
expose them in the schema.

### 32.1 Sequence

```
parse JSON
  -> report_schema.normalize()
  -> validate schema
  -> validate evidence IDs and timestamps
  -> validate coverage/untested
  -> store.add_report_at(context.report_path, report)
  -> context.mark_saved()
  -> return ok
```

Any failure returns an error and does **not** write the report. The deterministic
path still uses `store.add_report()`; investigator uses the explicit target path
from `ReportTarget`.

### 32.2 Normalization changes

`domain/report.normalize()` must preserve:

- `evidence_ids` on issues (list of strings);
- `mode`;
- `evidence` (list of IDs);
- `investigation` (dict).

It must keep old behavior for deterministic reports.

### 32.3 Validation

For `mode == "investigator"`:

- every issue has at least one `evidence_ids`;
- every ID exists in this run;
- every issue timestamp lies inside the union of the cited, non-overview evidence
  ±0.15s);
- `investigation.coverage` exists;
- `investigation.untested` exists and is consistent with false coverage flags;
- `stop_reason` exists;
- `issues` may be empty only if `summary` explains that no supported finding was
  found and `limitations` says why;
- for partial investigator reports, `focus` may be empty when `stop_reason` is
  present; `date` and `sport` are populated from the run context.

For deterministic mode, existing rules remain unchanged.

### 32.4 Duplicate saves

- First valid save wins.
- A later `save_report` returns:

```json
{"ok": false, "error": {"code": "REPORT_ALREADY_SAVED", "message": "...", "retryable": false}}
```

- Corrections must happen before the first successful save.

### 32.5 Finalization merge

`Strategy._finalize()` still patches:

- `metrics` (summary/coverage, not a full fake pipeline dump);
- `source`, `frames`, `frame_times`, `fps`;
- `artifacts`;
- `usage`, `timings`, `exports`.

It must not overwrite the model’s issue text, evidence IDs or investigation trace.

---

## 33. SSE event contract

### 33.1 Job snapshot

Add to the job snapshot:

```json
{
  "mode": "investigator",
  "progress": {
    "stage": "investigator",
    "pct": 41.0,
    "events": [
      {
        "seq": 7,
        "t": 12.4,
        "kind": "tool_finished",
        "tool": "estimate_pose",
        "args": {"start": 2.6, "end": 3.0},
        "evidence_id": "ev_0003",
        "summary": "elbow 122 deg",
        "seconds": 1.8
      }
    ]
  }
}
```

Event kinds:

- `tool_started`
- `tool_finished`
- `tool_error`
- `report_saved`
- `budget_warning`
- `run_stopped`

### 33.2 Ordering and size

- `seq` is monotonic per job.
- The API keeps the last 200 events in memory.
- The full trace is written to `investigation.json` and is not streamed.
- SSE sends the full current event list every 600 ms (the existing polling
  model); no delta protocol in MVP.
- `LiveJob` may render the last 20 events; the result page shows all.

### 33.3 UI behavior

- Group by nothing; show a chronological feed.
- `tool_started` is “looking at …”, `tool_finished` shows summary.
- `tool_error` is amber, not fatal.
- Final status still controls navigation.

---

## 34. Partial-report algorithm

### 34.1 Triggers

- tool-call budget exhausted;
- wall-clock deadline;
- token rail force-finish;
- max ReAct iterations;
- repeated tool errors;
- model returns without calling `save_report`.

### 34.2 Algorithm

1. Set `stop_reason` (e.g. `budget_exhausted`, `timeout`, `token_budget`,
   `max_iterations`, `model_error`).
2. Build a compact evidence summary from valid ledger records.
3. If at least one evidence record exists **and the stop reason is not
   `token_budget`**, make **one** tool-free model call: ?Write the best partial
   report using only these evidence IDs. State what was not assessed.? Use the
   normal report schema. When the token budget is already exhausted, skip this
   call; do not spend more tokens to explain the exhaustion.
4. Validate the result. If valid, save it with `investigation.stop_reason`.
5. If the call fails or validation fails, build a minimal report:

```json
{
  "date": "...",
  "sport": "...",
  "summary": "Analysis stopped early: <reason>. Only the inspected evidence is reported.",
  "strengths": [],
  "issues": [],
  "drills": [],
  "focus": "",
  "progress": "",
  "limitations": [
    "Analysis stopped early: <reason>.",
    "Not assessed: <coverage.untested>."
  ],
  "mode": "investigator",
  "evidence": ["..."],
  "investigation": {...}
}
```

6. If there are **no** evidence records, do not save a report. If
   `INVESTIGATOR_FALLBACK=true`, run the deterministic strategy explicitly and
   disable the demo-cache fallback for that path; otherwise return a failure with
   the stop reason.

`date` comes from today, `sport` from the profile, and `focus` may be empty for
this investigator-only partial report.

### 34.3 Never do this

- Never invent an issue to satisfy “no issues” validation.
- Never claim full coverage in a partial report.
- Never mark a partial report as complete without `stop_reason`.

### 34.4 Validation exception

`domain/report.validate()` must allow `issues: []` and empty `focus` for
investigator partial reports when `summary`, `limitations` and `stop_reason`
explain the early stop. `date` and `sport` are populated. This exception is not
available to deterministic reports.

---

## 35. Contract tests

Add these before UI work:

| Test | Assertion |
|---|---|
| `test_look_contract` | focused sheet path exists; JSON shape; no numeric racket claim |
| `test_tool_envelope` | success/error envelopes match section 20.1 |
| `test_evidence_ids` | IDs monotonic, immutable, run-scoped |
| `test_unknown_evidence_rejected` | `save_report` returns `INVALID_REPORT` |
| `test_timestamp_outside_window_rejected` | issue evidence time outside cited, non-overview union fails |
| `test_evidence_exempt_tools` | get_evidence/save_report create no evidence; get_overview does |
| `test_async_tool_wrapper` | async and sync implementations both return data, not coroutines |
| `test_frame_budget_precheck` | a call that would exceed the total is rejected before decoding |
| `test_coverage_untested` | false coverage must appear in `untested` |
| `test_token_budget_precedence` | investigator uses its own rail; global rail is not also applied |
| `test_run_scoped_storage` | two same-video runs write different working/artifact paths |
| `test_report_publish_readers` | published report is visible to get_reports/find_report/delete |
| `test_cancel_between_tools` | cancel event stops before the next tool, not mid-blocking call |
| `test_sse_events` | seq monotonic, bounded, final event present |
| `test_partial_report` | budget exhaustion produces valid partial report or clean failure |
| `test_partial_focus` | investigator partial report with empty focus validates |
| `test_no_global_state` | two contexts do not share evidence |
| `test_deterministic_unchanged` | golden report test for standard mode |

---

## 36. Final implementation-ready checklist

The spec is implementation-ready when all of these are true:

- [x] MVP tool list and deferred list are frozen.
- [x] Each MVP tool has input limits, output shape and error shape.
- [x] Evidence record and report extension are defined.
- [x] `look()` uses the existing vision agent through a defined prompt.
- [x] Tool calls auto-register evidence through one wrapper, with an explicit exempt list.
- [x] `compare_windows` is deferred.
- [x] Per-run token budget precedence is defined and the global rail is excluded.
- [x] `save_report` is one shared implementation, transactional, and validates evidence.
- [x] Run-scoped report storage and run-keyed artifact paths are specified.
- [x] Settings availability toggle and per-run mode selector are defined separately.
- [x] SSE event schema is defined.
- [x] Partial-report behavior is defined, including empty `focus` and empty `issues`.
- [x] Cancellation is explicitly between-tool only.
- [x] Contract tests are listed.
- [x] Deterministic mode remains unchanged.
- [x] Implementation backlog and acceptance criteria exist.
- [x] Schedule is re-baselined to 6–10 weeks for the full MVP.

Remaining non-spec work before coding starts:

1. Choose and verify a text model that reliably emits tool calls with the
   openjiuwen schema.
2. Create the 8-clip evaluation fixture and coach labels (1?2 weeks).
3. Confirm the vision model can answer focused window questions without
   hallucinating numeric measurements.
4. Set initial `INVESTIGATOR_MAX_*` values after one cost measurement on a real
   clip.

These are experiments, not unresolved design decisions.

---

## Appendix A — Current code map

| Concern | Current location |
|---|---|
| Fixed pipeline | `topspin_review/core/strategies/deterministic.py` |
| Mandatory full measurement | `topspin_review/core/strategies/base.py:69-80` |
| Existing agentic prototype | `topspin_review/core/strategies/agentic.py` |
| Measurement | `topspin_review/core/stages/measure/measure.py` |
| Sampling | `topspin_review/core/stages/measure/sampling.py` |
| Pose | `topspin_review/integrations/pose.py` |
| Ball | `topspin_review/core/stages/measure/ball.py`, `integrations/ballmodel.py` |
| Strokes | `topspin_review/core/stages/measure/strokes.py` |
| Vision passes | `topspin_review/core/stages/observe/` |
| Report tools | `topspin_review/core/stages/coach/report_tools.py` |
| Report schema | `topspin_review/domain/report.py` |
| Agent builder | `topspin_review/integrations/agents/agent/builder/` |
| openjiuwen DeepAgent | `C:\Workspace\openjiuwen\agent-core\openjiuwen\harness\factory.py` |
| ReAct loop | `C:\Workspace\openjiuwen\agent-core\openjiuwen\core\single_agent\agents\react_agent.py` |
| Streaming | `C:\Workspace\openjiuwen\agent-core\openjiuwen\harness\deep_agent.py:3325`, `core/runner/runner.py:849` |
| Rails | `topspin_review/integrations/agents/agent/rails.py` |
| Jobs/progress | `topspin_review/surfaces/gui2/server/jobs.py`, `core/progress.py` |

## Appendix B — What this mode is not

- It is not a replacement for the deterministic demo.
- It is not a guarantee that the agent will find more than the pipeline.
- It is not a live streaming coach; that is a separate architecture.
- It is not a license to invent metrics or to claim full coverage.
- It is not "agentic" as a label; it is a measurable change in who chooses the
  investigation path.

---

## Appendix C — Blocking items before Phase 2

These are implementation gaps that must be closed before any user-facing release.
They were identified in the architectural critique of the prototype (2026-10-18).

**Status as of 2026-10-18 — fixed in this commit:**

| # | Item | File(s) changed | Status |
|---|---|---|---|
| B1 | Token budget rail (`TokenBudgetRail.used`) was never written back to `Budget.tokens`. Every run reported `tokens: 0`. | `investigator.py` | ✅ Fixed: `ctx.budget.tokens = token_rail.used` after `run_agent()`. |
| B2 | Vision inspector had its own recorder; costs were not merged into the run's usage summary. | `observe/build_agent.py`, `investigate/tools.py`, `investigator.py` | ✅ Fixed: `recorder=` passed through to the vision builder. |
| B3 | `InvestigationContext` accepted a `cancel_event` but the job manager never created or passed one. A hung run could not be stopped from the UI. | `params.py`, `jobs.py`, `investigator.py` | ✅ Fixed: `Job.cancel_event` is a `threading.Event`; `JobManager.cancel()` calls `.set()`; the event is threaded into `Params` and then into `InvestigationContext`. |
| B4 | No CLI or API route recognised `--mode investigator`. The strategy was registered but inaccessible. | `cli/main.py`, `cli/commands/analyze.py`, `routes/analyze.py`, `models.py`, `jobs.py` | ✅ Fixed: `--mode {deterministic,agentic,investigator}` added to CLI; `mode` field added to `AnalyzeRequest` and `Job`; `JobManager._run()` calls `get_strategy(job.mode)` when set. |
| B5 | No test proved two concurrent `InvestigationContext` instances share no state. | `tests/unit/test_concurrent_investigator.py` | ✅ Fixed: serial and concurrent isolation tests added. |
| B6 | Strategy resolver had no regression test; deterministic path could silently break. | `tests/unit/test_strategy_resolver.py` | ✅ Fixed: tests for all three strategy names, unknown name, and default-not-investigator invariant. |

**Still open (before experimental release to users):**

| # | Item | Reason not yet done |
|---|---|---|
| B7 | Atomic rename / per-stem lock on final report write. Two simultaneous investigator jobs on the same video stem can clobber the final report. | Race is low-risk until concurrent UI submission exists; defer to hardening. |
| B8 | Permission-level restriction on the vision inspector (currently prompt-only; `bash`/`list_files` not denied at the permission layer). | Requires openjiuwen permission API; deferred to Phase 3 hardening. |
| B9 | `run_agent()` timeout / force-finish is not caught in `_run()`; on budget exhaustion the exception propagates to the base `Strategy.analyze()` fallback rather than triggering `_save_partial()`. | Requires wrapping `run_agent()` in a try/except that calls `_save_partial(reason="budget_exhausted")`. |
| B10 | Budget defaults (24 calls, 360 s, 80 k tokens, 160 frames) are from a single prototype run. Need calibration on ≥5 real clips before experimental release. | Depends on evaluation fixtures (task 16 in backlog). |

---

## Appendix D — Graduation criteria

Investigator mode is hidden behind `INVESTIGATOR_ENABLED=true` and the
`investigator_enabled` UI toggle. It graduates from **experimental** to
**general availability** when ALL of the following hold:

| Gate | Threshold | Rationale |
|---|---|---|
| Issue precision | ≥ deterministic − 2 percentage points on the evaluation set | Users trust investigator because it cites evidence; it must not find fewer real problems |
| p95 latency | ≤ 60 s on clips ≤ 30 s, measured on the production server | A 90-second run after the UI promises "slower" is an acceptable trade; beyond 60 s for short clips is not |
| Evidence integrity | 100% of issues in investigator reports cite valid, non-overview evidence IDs | Already enforced by validation; must remain 100% |
| Partial report rate | ≤ 10% of runs end in budget exhaustion (partial report) | If the budget is tuned correctly, most clips should reach `save_report` with full coverage |
| Coach validation | ≥ 50 investigator reports reviewed and rated by at least 2 coaches | Precision/recall gates are necessary but not sufficient; coaches must confirm the findings are actionable |
| No regression | All existing deterministic tests pass; `test_strategy_resolver.py` passes | Investigator additions must not touch the deterministic path |

Until all gates are met, the mode remains behind the experimental flag and the
UI warning stays visible. Do not remove the warning to make the mode look more
finished.

---

## Appendix E — Explicitly deferred items

The following were requested or discussed but deliberately moved out of scope.
Each has a reason. Revisit only after the graduation criteria above are met.

| Item | Deferred to | Reason |
|---|---|---|
| Investigation steering ("look more at footwork") | Phase 4 / live session | Requires mid-analysis interactive input; fundamentally different product architecture |
| `compare_windows` tool (cross-session evidence) | Phase 2+ | Requires session store integration; significant scope |
| Cost/latency estimate per run before it starts | Phase 2 UI | Backend token usage is not predictable before the run; show rough static ranges in UI settings only (done) |
| Per-run cost shown in the report | Phase 2 | Token accounting now works (B1 fixed); surface it in the UI report view |
| Confidence derived from evidence count (not model-assigned) | Phase 2 | Requires evidence weighting logic; current model-assigned confidence is acceptable for MVP |
| Ball tracking tool | Phase 2 | Not ready; no reliable ball detector in the current toolbox |
| Coach knowledge base as a tool | Phase 3 | Requires a validated KB; does not exist yet |
| Permission-level inspector restriction | Phase 3 hardening | Requires openjiuwen permission API |
| Automatic mode selection (AI chooses standard vs investigator) | Post-GA only | Must not happen before benchmark evidence proves investigator is better |
