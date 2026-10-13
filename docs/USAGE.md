# Using Topspin Review

Record a session — table tennis, tennis, badminton, squash, padel — and get back **form and
footwork insights**, the main things to fix, and drills. A local video file goes in; a local
report comes out. Two models are used: a **vision** model to read sampled frames and a **text**
model to write the coaching report.

This guide covers everything a user needs: setup, the surfaces, the workflow, the dev scripts, the
settings, and troubleshooting.

> Just want to run a demo? See the step-by-step guide: [RUN_DEMO.md](RUN_DEMO.md).

---

## 1. What it does

1. **Measure** — probes the clip and samples frames **where motion happens** (motion-weighted,
   time-ordered). It isolates the subject, then computes objective metrics: per-step movement
   energy, global image shift, subject box/track, upper/lower-body region motion (a footwork/step
   proxy), a crouch trend, and a heuristic ball/rally signal. It also builds a **motion map**
   (red = where the image moved).
2. **Observe** — two vision passes. Pass 1 gets a compact contact sheet + the metrics and proposes
   the time windows worth a closer look. Pass 2 zooms into those windows and returns structured
   findings, each with **evidence timestamps** and a **confidence**.
3. **Coach** — a text agent turns that into a **coaching report**: strengths, issues (with evidence
   + confidence), drills, a focus, a **progress** line vs the previous report, and limitations.
   History is kept per video.

It is honest about limits: it reasons from sampled frames plus measured motion, so it does **not**
claim to measure spin or exact ball speed, and it says so in the report's `limitations`.

### How the video becomes frames (plain English)

Most tools grab frames on a fixed clock — one every ⅓ second, say — and hope they catch the action.
This one does not. Instead it:

1. reads a few dozen **cheap, low-resolution** stills spread across the clip;
2. compares each still to the one before it to see **where the picture is moving** and where it is still;
3. spends its frame budget on the **busy parts** (a step, a swing) — but gives every part at least a little,
   so nothing is skipped entirely;
4. always keeps the **first and last** frame; and
5. later **zooms in** — samples more frames — inside the moments the vision model asks to look at again.

So the frames follow the **action**, not the clock. (ffmpeg's only job is to hand over the frames it asks for.)

**Vocabulary**

- **Session / report** — one analyzed video. Identified by the video file name; saved as
  `runtime/data/<stem>_report.json`.
- **Metrics** — the measured numbers (`energy`, `shift`, `track`, `mechanics`, `footwork_series`, `ball`, `pose`).
- **Issue** — a finding with `evidence_times` (where it was seen) and a `confidence`.
- **Artifacts** — the contact sheet, motion map, pose overlay, metrics JSON, observability JSON.
- **Usage** — the tokens/latency each model call used.

---

## 2. Setup

On this machine `python`/`pip` are **not on PATH** — use the repo venv. From the `topspin-review`
folder:

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"

& $PY -m pip install -r requirements.txt
```

`requirements.txt` installs everything the demo can use (analysis, `mediapipe` for pose, `reportlab`
for PDF, FastAPI, MCP, Streamlit, tests). `.env` holds the model endpoint; copy `.env.example` if
you need a fresh one. The required keys are `API_KEY`, `API_BASE`, `MODEL_NAME` (the vision model
defaults to `deepseek-v4-flash-vision-exp`).

Everything degrades gracefully: with only `python-dotenv numpy Pillow imageio imageio-ffmpeg
streamlit` the core CLI + UI still run; the extras (pose, PDF, API, MCP) activate when installed.

---

## 3. The surfaces

One engine, several inbound adapters. All expose the same analysis.

**Web UI (Streamlit)** → http://localhost:8501:

```powershell
& $PY -m streamlit run topspin_review/surfaces/gui/ui.py
```

- **Sessions** — history; open or delete a session.
- **Analyze** — upload a video/photo or use the built-in sample; **Advanced** (frames, seconds cap,
  agentic mode, region box).
- **Result** — Report / Movement / Details / Technical tabs, plus an **Ask** box.
- **Practice** — the drills as a checklist.
- **Progress** — the trend across sessions and a compare tool.
- **You** — your profile (sport, level, dominant hand, goal).

**Web app (gui2)** → http://127.0.0.1:8000/gui2/:

```powershell
cd topspin_review\surfaces\gui2\client; npm install; npm run build; cd ..\..\..\..
& $PY -m uvicorn topspin_review.surfaces.gui2:app --port 8000
```

A FastAPI server (`server/`) serving a SvelteKit SPA (`client/`). Same engine, built for the
**video** experience: scrub the source clip; **Video / Analysis / Observations / Coaching /
Diagnostics** tabs — Video is the plain clip (+ frames), Analysis is the measurements (Heat maps,
Movement, Pose, Tracked object), Observations is the table-tennis reading (findings + notable
moments + clips), Coaching is the plan; an **Ask** box; a live stage feed with **Cancel/Retry**.
Sessions are browsed — and compared pairwise — from the **Sessions** page, and a new analysis is
started from the header's **＋ New analysis**. The server also exposes the JSON API (§6).

**CLI** — see §5.

**HTTP API** — a minimal API over the same service (`uvicorn topspin_review.surfaces.api:app`), §6.

**MCP** — exposes `analyze_sport_video` to MCP clients (`python -m topspin_review.surfaces.mcp.server`).

**Programmatic** — `from topspin_review.core.service import analyze_video_sync`.

---

## 4. End-to-end workflow

1. Set your **profile** (sport, level, hand, goal) in **You** (or `cli profile`).
2. **Analyze** a clip (upload or sample).
3. Watch the stages: measure → observe → coach (→ verify / export).
4. Read the **Result**: focus, strengths, issues with timestamps, drills.
5. **Practice** the drills; next session, compare the two on the **Sessions** page.

---

## 5. Command line

```powershell
& $PY -m topspin_review.surfaces.cli profile                                  # set your profile
& $PY -m topspin_review.surfaces.cli analyze runtime/data/sample.mp4          # analyze (default path)
& $PY -m topspin_review.surfaces.cli analyze clip.mp4 --box 0.2,0.1,0.8,0.9   # restrict to a region
& $PY -m topspin_review.surfaces.cli analyze clip.mp4 --agentic               # let the model drive
& $PY -m topspin_review.surfaces.cli history                                  # recent reports
& $PY -m topspin_review.surfaces.cli export clip.mp4                          # Markdown/HTML/PDF
& $PY -m topspin_review.surfaces.cli compare a.mp4 b.mp4                      # diff two sessions
& $PY -m topspin_review.surfaces.cli reset                                    # clear saved reports
```

Run the analysis in its own process (used by the UI, useful in scripts):

```powershell
& $PY -m topspin_review.core.jobs.worker runtime/data/sample.mp4 --progress progress.json --agentic
```

---

## 6. HTTP API

Start with `uvicorn topspin_review.surfaces.api:app`. Routes:

| Method | Path | Purpose |
|---|---|---|
| GET | `/reports` | list saved reports (`source`, `date`, `focus`) |
| GET | `/reports/{stem}` | one full report |
| POST | `/analyze` | analyze a `{video_path, region_box?}` and return the report |

The gui2 server (`uvicorn topspin_review.surfaces.gui2:app`) is a richer API and also serves the SPA:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health`, `/ready` | liveness · readiness checks |
| GET | `/reports`, `/reports/{stem}` | list · one report (with `calls`/`tools`/`timeline`/`score`) |
| GET | `/reports/{stem}/ask?q=…` | ask about a report |
| GET | `/compare?a=&b=` | diff two sessions |
| POST | `/analyze` | synchronous analysis |
| POST | `/analyze/async` | enqueue → `{job_id}` (poll `/jobs/{id}`) |
| GET | `/jobs`, `/jobs/{id}` | jobs · status+progress |
| POST | `/jobs/{id}/cancel`, `/jobs/{id}/retry` | cancel · retry |
| POST | `/upload` | upload a clip/photo → `{path}` |
| GET | `/samples` | local clips (sample + uploads) |
| GET | `/source/{stem}`, `/artifact/{stem}/{kind}`, `/clip/{stem}/{key}` | media (video, artifacts, clips) |
| GET | `/export/{stem}/{md|html}` | downloadable report |
| — | `/gui2/` | the SvelteKit SPA |

---

## 7. Dev scripts

```powershell
& $PY tests\integration\make_sample.py        # synthetic table-tennis clip → runtime/data/sample.mp4
& $PY tests\integration\evaluate_reports.py   # quality gate against tests/eval/expected.json (CI-safe)
```

Rebuild the gui2 web app after editing its client:

```powershell
cd topspin_review\surfaces\gui2\client
npm run build          # writes client/build/ which the server serves at /gui2/
```

The full-pipeline integration tests (`tests/integration/`) need a configured model endpoint and
cost tokens; see `tests/integration/README.md`.

Typical first run:

```powershell
& $PY tests\integration\make_sample.py
& $PY -m topspin_review.surfaces.cli analyze runtime/data/sample.mp4
& $PY -m topspin_review.surfaces.cli export runtime/data/sample.mp4
```

---

## 8. Settings (`.env`)

**Model endpoint** — `MODEL_PROVIDER`, `API_KEY`, `API_BASE`, `MODEL_NAME`, `VISION_MODEL_NAME`,
`LLM_TEMPERATURE`, `VISION_TEMPERATURE`, `LLM_TIMEOUT`, `LLM_RETRIES`, `LLM_SSL_VERIFY`.

**Vision sampling** — `VISION_MAX_FRAMES` (12), `VISION_ZOOM_FRAMES` (6), `VISION_MAX_WINDOWS` (3),
`VISION_ZOOM_FPS` (8), `VISION_CACHE` (true), `VISION_MAX_SECONDS` (0 = whole clip),
`VISION_PROBE_BUDGET` (64).

**Analysis behaviour** — `AGENTIC_MODE` (false), `VERIFY_REPORTS` (true), `HIGHLIGHT_CLIPS` (true),
`RETRIEVAL` (true), `RAILS` (true).

**Ball detector** — `BALL_MODEL` (`auto` uses the ONNX model when installed, `off` forces the
heuristic), `BALL_MODEL_PATH` (default `runtime/data/models/ball.onnx`), `BALL_MODEL_IMGSZ` (640),
`BALL_MODEL_CONF` (0.25), `BALL_MODEL_FAMILY` (`auto`/`yolov5`/`yolov8`),
`BALL_SAMPLE_FPS` (10), `BALL_MAX_FRAMES` (400) — the last two control the dedicated dense
ball-tracking pass. Provision the MIT table-tennis
model with `scripts/fetch_ball_model.py`, or train your own via `scripts/train_ball.py` (needs
`pip install ultralytics`); without a model the heuristic tracker runs unchanged.

**Run constraints** — `TOKEN_BUDGET` (0 = unlimited), `TRACE_CALLBACKS` (false), `SAVE_CALL_IO` (true).

Full list with defaults: `.env.example`.

---

## 9. Where things live

All generated state is under `runtime/` (gitignored):

```
runtime/
├── logs/                                    # openjiuwen logs
└── data/
    ├── profile.json                         # your profile
    ├── <stem>_report.json                   # the coaching report (one per video)
    ├── cache/<stem>/                        # cached sampled frames
    ├── artifacts/                           # <stem>_frames/_motion/_pose.png, _metrics.json, _observability.json
    └── exports/                             # <stem>_report.md/.html/.pdf
```

---

## 10. Troubleshooting

- **`python`/`pip` not found** → use `$PY` (the repo venv) as above.
- **`Missing required environment variables`** → fill `API_KEY` / `API_BASE` / `MODEL_NAME` in `.env`.
- **No movement data** → single-image inputs have none; use a video for form/footwork.
- **Pose overlay missing** → install `mediapipe` (`pip install -r requirements.txt`); without it the
  analysis uses the region/box proxy.
- **Wrong subject picked** → pass `--box left,top,right,bottom` (0..1) or use the UI region sliders.
- **Port 8501 busy** → `--server.port 8502`; the API uses the port you pass to `uvicorn`.
- **PDF not produced** → install `reportlab`; otherwise the HTML report prints to PDF from a browser.

---

## 11. Going further

- **Architecture & rules**: [`architecture.md`](architecture.md).
- **Contributing** (setup, layers, where to add things): [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
- **Quick reference**: [`../QUICKSTART.md`](../QUICKSTART.md).
