# Topspin Review

Record a session — table tennis, tennis, badminton, squash, padel — and get back **form and footwork insights**, the main things to fix, and drills. Built on [openjiuwen](https://github.com/openJiuwen-ai/agent-core).

**No third-party integrations.** A local video file goes in; a local report comes out. Two models are used: a **vision** model (`deepseek-v4-flash-vision-exp`) to read sampled frames, and a text model to write the coaching report.

## Quick start

New here? See **[QUICKSTART.md](QUICKSTART.md)** for copy-paste commands to install and run the
Web UI / CLI.

- **Run a demo step by step:** [docs/guides/RUN_DEMO.md](docs/guides/RUN_DEMO.md).
- **Full guide:** [docs/guides/USAGE.md](docs/guides/USAGE.md) — setup, surfaces, workflow, API, scripts, settings, troubleshooting.
- **Design:** [docs/engineering/architecture.md](docs/engineering/architecture.md).
- **Roadmap:** [docs/engineering/ROADMAP.md](docs/engineering/ROADMAP.md) — competitor feature plan for later implementation.
- **Management pitch:** [docs/pitch/](docs/pitch/) — executive roadmap, Huawei pitch and talking points.

The rest of this file covers what it does, the architecture, and the knobs.

## What it does

1. You point it at a video of a session.
2. **Measure, don't eyeball.** It probes the clip and samples frames **where motion happens**
   (motion-weighted, time-ordered). It isolates the **subject** (background subtraction) and
   computes objective metrics: per-step movement energy, global image shift, subject box/track,
   **upper/lower-body region motion** (a footwork/step proxy), a crouch trend, and a heuristic
   **ball/rally** signal. It also builds a **motion map** (red = where the image moved).
3. **Two vision passes.** Pass 1 gets a compact contact sheet + the metrics and proposes the time
   windows worth a closer look. Pass 2 zooms into those windows and returns structured findings,
   each with **evidence timestamps** and a **confidence**.
4. A text agent turns that into a **coaching report** saved as JSON: strengths, issues (with
   evidence + confidence), drills, a focus, a **progress** line vs the previous report, and
   limitations. History is kept per video.

It is honest about limits: it reasons from sampled frames plus measured motion, so it does **not**
claim to measure spin or exact ball speed, and it says so in the report's `limitations`.

## Setup

This machine already has a working openjiuwen environment. Point at one of the repo venvs — `pip`/`python` are not on PATH here.

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"

# everything the demo uses: analysis, pose, PDF, API, MCP, tests
& $PY -m pip install -r requirements.txt
```

Note: `mediapipe` (pose) and the other extras come from this one file. If you only
want the core CLI, `python-dotenv numpy Pillow imageio imageio-ffmpeg streamlit`
are enough; everything else degrades gracefully when missing.

`.env` is already filled in. If you reuse this elsewhere, copy `.env.example`.

## Use

Run from the `topspin-review` folder.

```powershell
# set your profile (sport, level, hand, goal)
& $PY -m topspin_review.surfaces.cli profile

# analyze a video (defaults to runtime/data/sample.mp4)
& $PY -m topspin_review.surfaces.cli analyze runtime/data/sample.mp4

# see past reports
& $PY -m topspin_review.surfaces.cli history
```

Web UI (Streamlit):

```powershell
& $PY -m streamlit run topspin_review/surfaces/gui/ui.py
```

Web app (gui2 — FastAPI + SvelteKit SPA). Build once, then run:

```powershell
cd topspin_review\surfaces\gui2\client; npm install; npm run build; cd ..\..\..\..
& $PY -m uvicorn topspin_review.surfaces.gui2:app --port 8000
# then open http://127.0.0.1:8000/gui2/
```

Make a synthetic sample video (no recording needed):

```powershell
& $PY tests\integration\make_sample.py
```

Offline checks (no model calls):

```powershell
& $PY -m pytest -q                 # unit + architecture tests
& $PY -m ruff check .              # lint
```

## Architecture

Layered (hexagonal) — dependencies point inward only, enforced by
`tests/unit/test_architecture.py`:

```
surfaces → core → integrations → domain
```

```
topspin-review/
├── pyproject.toml            # packaging, extras (pose/pdf/api/mcp/web/dev), ruff/pytest config
├── runtime/                  # generated state, gitignored (created on first run)
│   ├── workspace/  logs/     # DeepAgent workspace scaffold + openjiuwen logs
│   └── data/                 # profile, <video>_report.json, cache/, artifacts/, exports/
├── topspin_review/
│   ├── __init__.py           # version only (no side effects)
│   ├── domain/               # pure: report, game reading, progress, compare, evaluate, drills, render
│   ├── integrations/         # outbound adapters (see below)
│   │   ├── agents/           #   all agentic under-the-hood: settings, logs,
│   │   │                     #     agent/ (builder, models, rails, tools, runner), telemetry/
│   │   ├── storage/          #   runtime, cache, json_store, store
│   │   ├── reporting.py      #   Markdown / HTML / PDF export
│   │   ├── media.py          #   highlight clips (ffmpeg)
│   │   └── pose.py           #   pose estimation (mediapipe + model download)
│   ├── core/                 # the pipeline (this package is the orchestrator)
│   │   ├── bootstrap.py      #   runtime dirs + logging; called by entry points
│   │   ├── config.py         #   application settings (sampling, feature toggles)
│   │   ├── params.py         #   Params: analyze() input + run state
│   │   ├── progress.py       #   run progress reporting
│   │   ├── run_session.py    #   run machinery: Runner, recorder, vision agent
│   │   ├── service.py        #   embedding surface (programmatic use)
│   │   ├── jobs/worker.py    #   standalone out-of-process analysis worker
│   │   ├── stages/           #   measure → observe → coach
│   │   ├── strategies/       #   deterministic / agentic
│   │   └── video/            #   shared video primitives (metrics, imaging, cvutil)
│   └── surfaces/             # inbound adapters: cli/, gui/ (Streamlit), gui2/ (web app), api.py, mcp/, readiness.py
├── tests/
│   ├── unit/                 # pipeline + architecture tests
│   ├── integration/          # full-pipeline checks (need a model endpoint)
│   │                         #   + dev tools: make_sample, evaluate_reports
│   └── eval/expected.json    # labeled expectations for quality checks
├── docs/
│   ├── engineering/             # architecture, pipeline research, roadmap
│   ├── guides/                  # usage and run-a-demo guides
│   └── pitch/                   # management pitch, talking points, executive roadmap
├── .github/workflows/ci.yml
├── .env
└── requirements.txt          # everything: analysis, pose, PDF, API, MCP, tests
```

This project is **self-contained**: it carries its own runtime layout
(`integrations/storage/runtime.py`) and JSON helpers (`integrations/storage/json_store.py`) —
no shared package is required.

## How it uses openjiuwen

All openjiuwen access is funnelled through `topspin_review.integrations.agents/` (the app never
imports `openjiuwen` directly). Its façade is small: `build`, `TextParams`/`VisionParams`,
`run_agent`, `run_text`, `ConfigError`, `configure_logging`. Internally:

- `integrations/agents/agent/builder/` — model + agent construction (`build`), with `text` and `vision` variants.
- `integrations/agents/agent/models/` — the underlying model-client construction.
- `integrations/agents/agent/tools.py` — the generic openjiuwen `@tool` wrapper (`make_tool` / `make_tools`).
- `integrations/agents/agent/rails.py` — optional openjiuwen rails (token-budget guard; memory).
- `integrations/agents/agent/runner.py` — starts the openjiuwen `Runner`; `run_agent` / `run_text`.
- `integrations/agents/telemetry/` — usage/trace recording (tokens, latency, callbacks).

Application tools (`get_profile`, `recent_reports`, `save_report`) live with the stage that uses
them: `core/stages/coach/report_tools.py`.

## Install

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
& $PY -m pip install -r requirements.txt
& $PY -m pip install -e .            # console script: topspin-review
# & $PY -m pip install -e .[all]      # + every optional extra
```

Installing is optional: running `-m topspin_review...` from the project folder
also works — the project is self-contained.

## Development

```powershell
# deterministic checks (no model calls)
& $PY -m pytest -q                 # unit + architecture tests
& $PY -m ruff check .
& $PY tests\integration\evaluate_reports.py  # quality gate against tests/eval/expected.json
```

Compare two analyzed sessions, export, and serve:

```powershell
& $PY -m topspin_review.surfaces.cli compare video11.mp4 video12.mp4
& $PY -m topspin_review.surfaces.cli export video12.mp4
& $PY -m uvicorn topspin_review.surfaces.api:app
& $PY -m topspin_review.surfaces.mcp.server
```

CI (`.github/workflows/ci.yml`) runs all three. Analysis requires a model endpoint
(text + vision); the unit tests are offline (no model calls).

Programmatic use:

```python
from topspin_review.core.service import analyze_video_sync
result = analyze_video_sync("runtime/data/session.mp4")
```

`surfaces/mcp/server.py` exposes the analysis as an MCP tool (`analyze_sport_video`).

## Knobs (`.env`)

- `VISION_MAX_FRAMES` (default 12) — frames sampled across the clip (motion-weighted).
- `VISION_ZOOM_FRAMES` (default 6) — extra frames inside the windows the first pass picks.
- `VISION_MAX_WINDOWS` (default 3) — how many zoom windows are allowed.
- `VISION_CACHE` (default true) — cache sampled frames per video (keyed by path+mtime+size).
- `VISION_MAX_SECONDS` (default 0 = whole clip) — cap analysis for long videos.
- `VISION_PROBE_BUDGET` (default 64) — frames read while locating motion-heavy windows.
- `LLM_RETRIES` (default 2) — retries per vision call (timeout uses `LLM_TIMEOUT`).
- `AGENTIC_MODE` (default false) — let the model drive analysis (`analyze --agentic`).
- `RETRIEVAL` (default true) — add lexically-retrieved past sessions to the report context.
- `RAILS` (default true) — enable openjiuwen rails (token-budget guard; `MemoryRail` when `EMBED_*` set).
- `TRACE_CALLBACKS` (default false) — capture usage for all calls via `Runner.callback_framework`.
- `TOKEN_BUDGET` (default 0 = unlimited) — abort a run past this many tokens.

## Notes

- Each analyzed video is saved as its own report file named after the video:
  `video11.mp4` -> `runtime/data/video11_report.json`. Re-analyzing the same video
  overwrites that video's report; other videos keep their own.
- Every issue in the report cites the timestamps it is based on and a confidence, and the
  report lists its limitations, so hallucinated claims are easy to spot.
- **Primary subject:** the foreground union is reduced to its largest connected blob, so other
  people in the hall are excluded from the motion map and metrics.
- The report `progress` field is computed from all saved reports (`domain/progress.py`):
  recurring themes, issue counts per session, focus history, and whether last session's focus was
  **achieved**. In the web UI, comparing two sessions lives on the **Sessions** page.
- **Export** a report to Markdown + self-contained HTML: `analyze` does it automatically, or run
  `python -m topspin_review.surfaces.cli export [video]`. Open the HTML and print to PDF if needed.
- **Player region:** if the auto primary-subject pick is wrong, pass
  `--box left,top,right,bottom` (0..1) or use the UI sliders to restrict analysis.
- Real joint pose: `pip install -r requirements.txt` (installs `mediapipe`), then `motion.pose_estimate` returns
  knee/elbow angles and stance width (fed into the prompt and saved as a skeleton overlay);
  without it the demo uses the region/box proxy.
- Each run records vision **token/latency usage** in the report (`usage`) and the UI.
- Ball/rally detection is heuristic (blob + nearest-neighbour tracker, not a trained model) and is
  always labelled low confidence.
- Every report is scored by `evaluate.py` (evidence coverage, confidence mix, hallucination flags
  for spin/speed/angle claims); the score feeds the benchmark / quality gate. It is no longer shown
  in the player-facing UI, where it read like a performance rating.
- Coaching quality depends on video quality and camera angle (side view of the player works best).
- Not medical or professional coaching advice.
