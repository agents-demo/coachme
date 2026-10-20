# Architecture

CoachMe is layered (hexagonal). Dependencies point **inward** only.

```
surfaces  ──▶  core  ──▶  integrations  ──▶  domain
```

## Layers

| Layer | Package | Responsibility | May depend on |
|---|---|---|---|
| Domain | `domain/` | Pure rules: report and evidence schemas, game reading (CV→table-tennis translation), progress, comparison, scoring, drills, annotations, text rendering. No I/O, no third-party libs. | stdlib only |
| Integrations | `integrations/` | Outbound adapters: the openjiuwen agentic machinery (`agents/`: settings, models, agent builder, rails, tools, runner, logs, telemetry), `storage/`, `reporting`, `media`. | stdlib, openjiuwen |
| Core | `core/` | The pipeline: stages (`measure`, `observe`, `coach`, `investigate`), the strategies that run them, the shared video primitives (`video/`), the run machinery, jobs, config and the service facade. | integrations, domain |
| Surfaces | `surfaces/` | Inbound adapters: CLI, Streamlit UI, web app (gui2), HTTP API, MCP, readiness checks. | anything |

The rules are enforced by `tests/unit/test_architecture.py` (import direction,
"domain is pure", "openjiuwen only in `integrations/agents`", and the `STAGES`
constant matching the stage packages), so a violation fails CI.

## Package map

```
coachme/
├── __init__.py            # version only (no side effects)
├── domain/                # report, evidence, game_reading, progress, compare, evaluate, drills, annotations, render
├── integrations/          # outbound adapters
│   ├── agents/            # provider access (see below)
│   ├── storage/           # runtime, cache, json_store, store
│   ├── reporting.py       # Markdown / HTML / PDF export
│   ├── media.py           # highlight clips (ffmpeg)
│   ├── pose.py            # pose estimation (mediapipe PoseLandmarker + model download)
│   ├── ballmodel.py       # ONNX ball detector (optional; heuristic fallback)
│   └── cards.py           # share-card PNG rendering
├── core/                  # the pipeline (this package is the orchestrator)
│   ├── bootstrap.py       # runtime dirs + logging; called by entry points
│   ├── config.py          # application settings only (sampling, feature toggles)
│   ├── params.py          # Params: analyze() input + run state
│   ├── progress.py        # run progress reporting
│   ├── run_session.py     # run machinery: Runner, recorder, vision agent
│   ├── service.py         # embedding surface (analyze_video, ask, describe)
│   ├── jobs/worker.py     # standalone out-of-process analysis worker
│   ├── stages/            # measure -> observe -> coach, plus investigate (experimental)
│   ├── investigate/   #   investigator tools, context, evidence ledger
│   ├── strategies/        # deterministic / agentic / investigator
│   └── video/             # shared video primitives: metrics, imaging, cvutil
└── surfaces/              # inbound adapters
    ├── cli/               # command-line interface
    ├── gui/               # the Streamlit UI
    ├── gui2/              # the web app: server/ (FastAPI) + client/ (SvelteKit SPA)
    ├── api.py             # minimal HTTP API
    ├── mcp/               # MCP server + tools
    └── readiness.py       # environment readiness checks
```

### The agents integration

`integrations/agents/` is the **single home for everything under-the-hood of the
agentic system**: every openjiuwen import (no `from openjiuwen...` exists anywhere
else), model/agent access, rails, and telemetry. `core/config.py` holds only
*application* settings. Both text and vision go through agents built by the agent
builder — there is no separate provider transport. The package exposes a small
façade (`build`, `TextParams`/`VisionParams`, `run_agent`, `run_text`, `ConfigError`,
`configure_logging`); everything else is internal. Internally it's grouped by
concern:

```
integrations/agents/
├── __init__.py            # the façade
├── settings.py            # backend env: keys, model names, timeouts, embeddings, budget/tracing
├── logs.py                # route openjiuwen logging to a directory
├── agent/                 # build & run an agent
│   ├── builder/           #   the agent builder
│   │   ├── build.py       #     build(params): the single entry point
│   │   ├── params.py      #     Params / TextParams / VisionParams
│   │   ├── base.py        #     AgentBuilder (owns recorder + instrumentation)
│   │   ├── text.py        #     TextBuilder
│   │   ├── vision.py      #     VisionBuilder
│   │   └── result.py      #     BuildResult
│   ├── models/            #   generic model construction
│   │   ├── builder.py     #     build_model(params) (constructs an openjiuwen Model)
│   │   └── params.py      #     ModelParams
│   ├── rails.py           #   AgentRail base + TokenBudgetRail + memory_rail() + resolve(names)
│   ├── tools.py           #   make_tool()/make_tools() (openjiuwen tool decoration)
│   └── runner.py          #   Runner lifecycle, run_agent(), callback-event bridge
└── telemetry/             # run telemetry
    ├── usage.py           #   token/latency extraction + UsageCollector
    ├── traces.py          #   CallTrace / ToolTrace / CallbackTrace
    └── recorder.py        #   Recorder + attach (the builder-owned run recorder)
```

### The core package

`core/` is a **pipeline** of three stages (measure → observe → coach), run by two
interchangeable **strategies**. The strategies share a base class (`base.py`,
template method): `analyze` prepares the clip (sample + measure), calls the
mode-specific `_run`, then finalizes (usage, report patch, export) — so the
deterministic and agentic modules only implement their real difference. Callers
obtain a strategy from the `core` package (registry: `core.resolve(...)` /
`core.get_strategy(name)`) and run `strategy.analyze(core.Params(...))` — they never
import a concrete module.

```
core/
├── bootstrap.py             # runtime dirs + logging
├── config.py                # application settings
├── params.py                # Params: analyze() input + run state
├── progress.py              # run progress reporting
├── run_session.py           # run machinery: Runner, recorder, vision agent
├── service.py               # embedding surface used by the API / MCP / GUI
├── jobs/worker.py           # standalone out-of-process worker (progress JSON)
├── video/                   # shared video measurement/rendering primitives:
│                            #   metrics, imaging, cvutil
├── stages/                  # the pipeline stages (STAGES constant lives here)
│   ├── measure/             #   stage 1: video → frames + measurements
│   │   ├── measure.py         # measure(): sample frames + compute metrics
│   │   ├── sampling.py        # motion-weighted frame sampling
│   │   ├── ball.py            # ball detection/tracking (ONNX or heuristic)
│   │   ├── strokes.py         # fast-hand events from pose wrists
│   │   └── quality.py         # footage-quality gate
│   ├── observe/             #   stage 2: frames → observations
│   │   ├── build_agent.py     # build the vision DeepAgent
│   │   ├── render_images.py   # render/save the images the model reads
│   │   ├── ask_agent.py       # ask the vision agent + parse JSON
│   │   ├── run_passes.py      # the overview / detail / still passes
│   │   └── prompts.py         # vision prompt text
│   └── coach/               #   stage 3: observations → coaching report
│       ├── build_agent.py     # build the report DeepAgent
│       ├── report_tools.py    # get_profile / recent_reports / save_report
│       ├── retrieve_reports.py# lexical retrieval over past reports
│       ├── verify_issues.py   # prune issues the evidence doesn't support
│       └── prompts.py         # report / verify prompts + rubrics
└── strategies/              #   the interchangeable modes
    ├── base.py              #     Strategy base class (template) + shared steps
    ├── resolve_strategy.py  #     STRATEGIES registry + get_strategy()/resolve()
    ├── deterministic.py     #     default mode: fixed measure → observe → coach
    └── agentic.py           #     opt-in mode: the agent inspects the clip itself
```

## openjiuwen integration

All framework access is funnelled through `integrations/agents/`; the rest of the
app imports only `coachme.integrations.agents`.

- **Model clients** — `integrations.agents.agent.models` is **internal**
  (`make_text_model` / `make_vision_model`, lazy `openjiuwen...Model`, reading
  `integrations.agents.settings`). External code never imports it.
- **Agent builder** — `integrations.agents.build(params)` is the single entry point:
  it builds (and instruments) the model, decorates tools, resolves rails and
  constructs the DeepAgent. The `agent.builder.params` dataclasses (`TextParams`,
  `VisionParams`) describe the agent. `core/stages/coach/build_agent.build_agent` is
  the report policy over `TextParams`; the deterministic and agentic strategies both
  use it (the agentic one overrides the prompt, tools and iterations).
- **Tools** — application code passes plain callables
  (`core/stages/coach/report_tools.py`, the agentic strategy's `inspect_window`); the
  builder decorates them internally (auto-extracting name/description/schema from the
  function/docstring/signature). Nothing about tooling decoration is known outside
  `integrations/agents`. (External exposure is over MCP —
  `surfaces/mcp/server.py` + `surfaces/mcp/tools.py`, FastMCP.)
- **Rails** — application code only names rails (`core.config.rails()`, e.g.
  `["token_budget", "memory"]`); `integrations.agents.build` resolves the names via
  `agent.rails.resolve()` and builds/attaches the rails. The implementations
  (`AgentRail`, `TokenBudgetRail`, `memory_rail()`) never leave `integrations/agents`.
- **Runner** — `integrations.agents.run_agent`, and its callback-event bridge
  (`on_tool_calls` / `on_llm_output`) used by `agents.telemetry` traces.
- **Vision** — `core/stages/observe/build_agent.build_agent` builds (via the agents
  builder) a DeepAgent whose model is the vision model, reading rendered images
  through the `read_file` tool (`SysOperationRail` + `enable_read_image_multimodal`).
  `core/stages/observe/run_passes.py` persists contact sheets / motion maps / frames
  and asks the agent to read them.
- **Telemetry** — the builder creates a run **Recorder**
  (`integrations.agents.telemetry.recorder`, internal) that captures usage/traces;
  callers never touch it directly. The UI shapes it for display in
  `surfaces/gui/timeline.py` (presentation, not the integration).
- **Agents only.** Application code never calls `Model.invoke` directly; every model
  interaction — text, verification, Q&A, and vision — goes through an openjiuwen
  agent + `Runner` built by the agents integration.
- **Logging** — `integrations.agents.logs.configure` routes openjiuwen logging into
  `runtime/logs/`.

Everything above is optional at import time (lazy imports), so the deterministic
parts (`core.video` / `domain` / `integrations.storage`) run without openjiuwen
installed.

## Data flow

```
video ─▶ core.stages.measure.sampling (motion-weighted, cached in integrations.storage.cache)
      ─▶ core.video.metrics.analyze (energy, shift, subject, mechanics, ball, pose)
      ─▶ core.stages.observe.coarse (contact sheet + core.video.metrics.text) ─▶ windows
      ─▶ core.stages.measure.sampling.sample_window (zoom)
      ─▶ core.stages.observe.fine (frames + motion map + pose) ─▶ observations/signals
      ─▶ core.stages.coach.build_agent (DeepAgent + tools) ─▶ report.json
      ─▶ integrations.reporting + domain.game_reading / domain.progress / domain.compare
```

## Boundaries & conventions

- **No import side effects.** `__init__.py` only sets `__version__`. Logging is
  configured by `core.bootstrap.setup()`, called by every surface entry point (and by
  `conftest.py` in tests) so openjiuwen logs always land in `runtime/logs/`.
- **Agents, not providers.** Text and vision both go through the agents builder;
  there is no separate provider transport to swap.
- **Single source of paths.** All generated state lives under `runtime/` via
  `integrations.storage.runtime` (`runtime.DATA_DIR`, `ARTIFACTS_DIR`, `CACHE_DIR`, ...).
- **Schema at the boundary.** `domain.report.normalize/validate` runs inside the
  `save_report` tool, so stored reports always match the schema.
- **One implementation each** of: report rendering (`domain.render`), report lookup
  (`integrations.storage.store.find_report`), and the tool contract
  (`core.service.describe`).

## Extending

- New surface (e.g. gRPC) → add a module under `surfaces/`; reuse `core.service`.
- New video signal → add to `core/stages/measure/` (detection/sampling) or
  `core/video/` (rendering), surface it through `core.video.metrics.analyze` and
  `core.video.metrics.text`.
