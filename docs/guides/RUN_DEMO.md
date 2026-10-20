# Run a demo — step by step

This page shows how to run CoachMe and get a result. It uses a real model
(a **text** model for the report and a **vision** model to read the frames) on a
short racket-sport clip.

You can run it from the **Web UI** or the **command line**. Pick one; the Standard
pipeline is the same. Investigator is an experimental alternative that chooses its
own investigation path.

---

## Before you start

Open a PowerShell window and set the Python path once:

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
cd C:\Workspace\openjiuwendemos\coachme
```

Check that `.env` has a model (a real model, not a fake):

```powershell
Get-Content .env | Select-String "API_KEY|API_BASE|MODEL_NAME|VISION_MODEL_NAME"
```

The required keys are `API_KEY`, `API_BASE`, `MODEL_NAME`. The vision model defaults
to `deepseek-v4-flash-vision-exp`.

---

## The demo clip

No recording handy? Make a synthetic side-view table-tennis clip (a player silhouette
with visible stance, footwork and a forehand swing, plus a table, net and ball):

```powershell
& $PY tests\integration\make_sample.py
```

That writes `runtime/data/sample.mp4`. You can also use your own clip — side-on,
full-body works best. A single photo works too (you get posture feedback only).

---

## Option A — Web UI

### 1. Start the UI

```powershell
& $PY -m streamlit run coachme/surfaces/gui/ui.py
```

Leave this window open.

### 2. Open the UI

In your browser, open:

```
http://localhost:8501
```

### 3. Analyze

On the **Analyze** page: choose a video (or a single photo), or tick **use the built-in
sample clip**. Under **Advanced** you can set how many frames to study, cap the first
N seconds, choose agentic or (when enabled) Investigator mode, and restrict analysis to just you
(a region box).

Click **Analyze**. A progress bar shows each stage (`preparing`, `vision: overview`,
`vision: detail`, `agent writing report`, …). You can **Stop** a run.

### 4. Read the result

The **Result** page has four tabs:

- **Report** — focus, summary, strengths, issues (tap a timestamp to jump the video),
  key-moment clips, drills.
- **Movement** — the movement over time, the motion map (red = where you moved most),
  the frames the model read, and a pose overlay.
- **Details** — limitations and a confidence score, plus download buttons (Markdown / HTML).
- **Technical** — token/latency usage and the full execution timeline (every model and
  tool call).

A floating **Ask** box (bottom-right) answers questions grounded in the report.

### 5. Track progress

**Practice** turns the drills into a checklist. **Progress** shows the trend across
sessions and compares any two. **Sessions** is the history; **You** holds your profile.

---

## Option B — Web app (gui2)

The web app is a FastAPI server that serves a SvelteKit single-page app. It gives a smoother
video experience: scrub the video, tap a moment to jump to it, sync the movement chart, compare
sessions. Build it once (needs Node), then run the server:

```powershell
cd coachme\surfaces\gui2\client; npm install; npm run build; cd ..\..\..\..
& $PY -m uvicorn coachme.surfaces.gui2:app --port 8000
```

Then open:

```
http://127.0.0.1:8000/gui2/
```

Pick **＋ New analysis** in the header: use a sample clip, upload a video/photo, or paste a path;
then click **Analyze**. A live feed shows each stage; when it finishes it opens the **Result** with
**Video / Analysis / Observations / Coaching / Diagnostics** tabs. Video is the clip (+ the frames
read); Analysis holds the measurements (Heat maps, Movement, Pose, Tracked object); Observations is
the table-tennis reading (findings + notable moments + clips); Coaching is the plan. Browse — and
compare pairwise — sessions from the **Sessions** page.

---

## Option C — command line

Start the app in one window:

```powershell
& $PY -m coachme.surfaces.cli analyze runtime/data/sample.mp4
```

Other commands:

```powershell
& $PY -m coachme.surfaces.cli profile   # set your profile
& $PY -m coachme.surfaces.cli history   # past reports
& $PY -m coachme.surfaces.cli export runtime/data/sample.mp4
& $PY -m coachme.surfaces.cli compare a.mp4 b.mp4
```

---

## Option D — programmatic / HTTP / MCP

```python
from coachme.core.service import analyze_video_sync
result = analyze_video_sync("runtime/data/sample.mp4")
```

```powershell
& $PY -m uvicorn coachme.surfaces.api:app     # HTTP API
& $PY -m coachme.surfaces.mcp.server          # MCP tool: analyze_sport_video
```

---

## What the run does

CoachMe runs three stages (plus verification, retrieval and clip-cutting):

| Stage | What it does |
|---|---|
| measure | samples frames **where motion happens**, isolates the subject, computes objective metrics (energy, shift, region motion, crouch trend, ball/rally) |
| observe | two vision passes — an overview that picks the windows worth a closer look, then a zoom into those windows → structured findings with evidence timestamps |
| coach | a text agent writes the coaching report (strengths, issues with evidence + confidence, drills, focus, progress vs last time) |

Add `--agentic` (or the **Advanced** switch) for guided window selection, or
`--mode investigator` for the experimental model-directed mode.

---

## Where the results are

```
runtime/data/<stem>_report.json            # the coaching report (one file per video)
runtime/data/artifacts/<stem>_frames.png   # the contact sheet the model read
runtime/data/artifacts/<stem>_motion.png   # the motion map
runtime/data/artifacts/<stem>_pose.png     # the pose overlay (when mediapipe is installed)
runtime/data/artifacts/<stem>_metrics.json # the measured numbers
runtime/data/artifacts/<stem>_observability.json  # model + tool calls
runtime/data/exports/<stem>_report.md/.html/.pdf  # the exported report
```

`<stem>` is the video file name, e.g. `sample`.

---

## One important thing — it is honest about limits

It reasons from **sampled frames plus measured motion**, so it does **not** claim to
measure spin or exact ball speed, and it says so in the report's `limitations`. Each
issue cites the timestamps it is based on and a confidence, so unsupported claims are
easy to spot. Coaching quality depends on video quality and camera angle.

---

## Problems

- **`python`/`pip` not found** → use `$PY` (the repo venv) as above.
- **`Missing required environment variables`** → fill `API_KEY` / `API_BASE` / `MODEL_NAME` in `.env`.
- **No movement data** → single-image inputs have none; use a video for form/footwork.
- **Pose overlay missing** → `pip install -r requirements.txt` (installs `mediapipe`); without it
  the analysis uses the region/box proxy.
- **Port 8501 busy** → pick another: `--server.port 8502`.
- **Clip not found** → run `tests\integration\make_sample.py`, or pass a real path.

See [USAGE.md](USAGE.md) for the full guide.
