# Android APK — Self-contained Technical Plan

*A native Android app that does everything the current web app does, **on the phone**, with **no
code reuse** — calling the same DeepSeek API directly. No backend server, no openjiuwen.*

---

## 1. Goal

Ship a **self-contained Android APK** that:

- Lets the user **pick a video (or photo) from the phone**, analyze it, and read the report.
- Reproduces the **same rubrics and screens** as today: **Video / Analysis / Observations / Coaching /
  Diagnostics**, with the same items and the same look, made mobile-friendly.
- Calls the **same DeepSeek API** configured in `.env` (`API_KEY`, `API_BASE`, `MODEL_NAME`,
  `VISION_MODEL_NAME`) **directly from the device** — no server of ours.
- Uses **internet** (models are remote) — that is the only external dependency.

## 2. Non-goals

- No openjiuwen, no Python, no FastAPI, no browser.
- No offline/local model (the models stay remote).
- No shared code with `topspin_review/` — this is a clean native rewrite.

## 3. Principle — rewrite, don't reuse

The existing app is Python + SvelteKit. Android is Kotlin. We **reimplement** the logic natively,
keeping the *behavior* and *data shapes* identical so the report and screens match.

## 4. Where it lives

A new surface, alongside the others:

```
topspin_review/surfaces/android/
├── app/                     # Android app module (Kotlin, Jetpack Compose)
│   └── src/main/
│       ├── java/…/androidapp/
│       │   ├── ui/          # Compose screens + components (see §10)
│       │   ├── pipeline/    # measure → observe → coach (see §7)
│       │   ├── llm/         # DeepSeek client + prompts + tools (see §8)
│       │   ├── media/       # decode, sample, pose, ball, clips (see §7)
│       │   ├── data/        # report model, storage, settings (see §9)
│       │   └── util/
│       └── assets/          # bundled models (pose, ball) + prompts
├── build.gradle.kts
└── README.md
```

Prompts and the report JSON schema live in `assets/` so they match the desktop app's outputs.

## 5. High-level architecture

```
Pick media ─▶ MEASURE (on-device CV) ─▶ OBSERVE (DeepSeek vision) ─▶ COACH (DeepSeek text + tools)
                                                                          │
                                                                          ▼
                                                              report.json + artifacts  ─▶  Compose UI
```

All three stages run in the app; only the two model calls go over the network.

## 6. Tech stack

| Concern | Choice |
|---|---|
| Language / UI | Kotlin + **Jetpack Compose** (Material 3) |
| Async | Coroutines + Flow |
| HTTP | OkHttp (+ kotlinx.serialization) |
| Video decode | **MediaMetadataRetriever / MediaCodec** (avoid ffmpeg licensing) |
| On-device CV | **OpenCV Android** (or pure Kotlin + a numeric lib) |
| Pose | **MediaPipe Tasks — PoseLandmarker** (Android SDK) |
| Ball | **ONNX Runtime Mobile** (bundled `ball.onnx`) *or* **TFLite** export |
| Video playback | **Media3 ExoPlayer** + a Compose overlay for telestration |
| 3D (pose/ball) | **SceneView/Filament** *or* a `WebView` with the existing three.js-like canvas |
| Speech out/in | Android `TextToSpeech` + `SpeechRecognizer` |
| Storage | App-private files (`filesDir`) — no `runtime/` |

## 7. The pipeline to reimplement (parity with today)

### 7.1 Frame extraction & sampling
- Decode with `MediaMetadataRetriever`/`MediaCodec`; downscale.
- Port the **motion-weighted sampling**: probe frames (low-res), per-interval motion = mean abs
  gray diff, split a frame budget by motion weight, always keep first/last; plus the **even** pass for
  the ball. (Mirrors `sampling.sample_frames` / `sample_even`.)

### 7.2 Metrics & maps (pure CV)
- **Activity** (movement energy timeline), **subject region** (background subtraction → largest blob
  → `region_box` override), **track**, **mechanics** (upper/middle/lower body regions → lower-body
  lateral range + direction changes), **posture**.
- **Maps**: motion map (frame diffs → red overlay) and position heatmap (subject-centre histogram),
  drawn on `Bitmap`/Canvas.
- Emit the **same `metrics` keys**, including `footwork_series`.

### 7.3 Pose
- **MediaPipe Tasks PoseLandmarker** (`pose_landmarker_lite.task` is already bundled in the repo).
- Produce per-frame landmarks + **world landmarks** → knee/elbow angles, stance width, crouch, and
  **3D** (torso lean, shoulder/hip twist). Mirror `pose.summarize` / `summarize3d`.
- Render the **skeleton overlay** and the **angles chart**.

### 7.4 Ball tracking (YOLO)
- Bundle `ball.onnx` (already an **ONNX** YOLOv5 single-class, 640×640, output `[1,25200,6]`).
- Run via **ONNX Runtime Mobile** (or export to **TFLite** with Ultralytics for NNAPI/GPU).
- Port pre/post: **letterbox → infer → class-agnostic NMS**, then the **constant-velocity tracker**
  (max jump, tolerate misses, keep tracks ≥3 points, reject static). Produce path, contacts/bounces,
  spans, 3D trajectory.

### 7.5 Observe — vision pass (DeepSeek)
- Build the **contact sheet** (tile sampled frames) and the **zoom frames**.
- Send them to the **vision model** (`VISION_MODEL_NAME`) as multimodal input; two passes: overview
  (propose windows) → detail (per-window findings with **evidence timestamps** + confidence).

### 7.6 Coach — report agent (DeepSeek + tools)
- Call the **text model** (`MODEL_NAME`) with **function/tool calling**, reproducing today's tools:
  `get_profile`, `recent_reports`, `save_report`, and (agentic) `inspect_window`.
- Produce the report with the **same fields**: `summary`, `focus`, `strengths`,
  `issues[{issue, evidence_times, confidence}]`, `drills`, `progress`, `limitations`.
- Deterministic post-steps in-app: **verify issues** (evidence support), **retrieval** from past
  reports, **drill details**, **game reading** (CV→table-tennis translation), **highlight clips**.

### 7.7 Artifacts & exports (keep parity)
- **Highlight reel (mp4)**, **moment clips**, **share card (PNG)**, **trim**, **GIF**, **vertical**.
- **Export** Markdown + HTML (self-contained); PDF optional (Android print).
- Use `MediaExtractor`/`MediaMuxer` or Media3 for cutting (no GPL ffmpeg needed).

## 8. DeepSeek API contract (direct from the device)

- **Config**: `API_BASE`, `API_KEY`, `MODEL_NAME` (text), `VISION_MODEL_NAME` (vision) — same values as
  the desktop `.env`.
- **Vision call**: chat/completions with **image content** (base64 frames) + the overview/detail
  prompts; parse structured JSON.
- **Text call**: chat/completions with **tools** (JSON schemas from the ported tool functions);
  handle the tool-call loop, retries, timeouts.
- **Telemetry**: record per-call tokens/latency + the **stage timeline** for the Diagnostics tab.
- **Cost controls**: the same toggles (`agentic`, frame budget) and a per-run token guard.

## 9. Data model & storage (on device)

- **Report JSON** — same schema as `runtime/data/<stem>_report.json` (`metrics`, `artifacts`, `clips`,
  `annotations`, `issues`, `focus`, `tt_reading`, `usage`, `timeline`, `calls`, `tools`, `quality`).
- **Storage** — app-private `filesDir`:
  - `reports/<stem>.json`
  - `artifacts/<stem>_*.png|jpg` (contact sheet, maps, pose, ball path, cards)
  - `clips/<stem>/*.mp4`
  - `cache/` (decoded frames)
  - `exports/<stem>_report.md|.html`
- **Profile** — sport, level, hand, goal (Settings).
- **Settings** — API base/key/models, region box, agentic toggle, theme.

## 10. GUI — mobile screens (same rubrics, touch-first)

Reimplement each screen of the current app in Compose:

- **Sessions** (home): stats; session cards (thumbnail, name, date, sport, focus, issue count,
  delete); **＋ New analysis**; **Compare two sessions**.
- **New analysis**: pick **video/photo from the phone** (or a bundled sample); advanced (agentic,
  region box); **live stage feed** with cancel/retry; **environment readiness**.
- **Result — header**: session name, sport · date, "recorded run" badge.
- **Result — tabs**: **Video · Analysis · Observations · Coaching · Diagnostics**.
  - **Video**: `Motion | Frames`. Motion = player + controls (play, frame-step, slow-mo, scrub,
    **draw / angle tool**, save annotations) + **Trim & export** + **Movement over time** (synced
    chart, tap to seek) + **Active spans**. Frames = **Frames read**.
  - **Analysis**: `Heat maps | Movement | Pose | Tracked object` (opens on the first).
    - Heat maps: **Movement map**, **Position map**.
    - Movement: **Side-to-side movement** (chart with axes, shaded band %, direction-change dots) + stats.
    - Pose: **Skeleton**, **Body angles**, **Body 3D**, **Fast-hand events**.
    - Tracked object: **Object path**, **Object trajectory (3D)**.
    - Every item keeps **label + plain "how" + "details" (method/engine/source)**.
  - **Observations**: `Findings | Key moments`.
    - Findings: **Play / Player / Ball** groups (TT reading) with the same visuals (movement chart,
      skeleton + angles legend, ball path + 3D).
    - Key moments: **KeyMoments** (tap a time to play) + **Moment clips**.
  - **Coaching**: `Advice | Practice | Details | Ask`.
    - Advice: **read-aloud**, **Focus next session**, **What's working / What to improve**, summary +
      **since last time**.
    - Practice: **drills checklist** + progress + drill detail.
    - Details: clip caveats, limits, **Save / export** (Markdown, HTML, highlight reel, share card).
    - Ask: grounded Q&A, **voice input** + **read aloud**, replay.
  - **Diagnostics**: **calls** (with probe flag), **tools**, **tokens/usage (incl. cached)**,
    **stage timeline**.
- **Theme**: light/dark.
- **Readiness/Environment**: model reachable, media permissions, models present.

## 11. Feature-parity checklist (nothing forgotten)

| # | Current feature | Android |
|---|---|---|
| 1 | Sessions list + delete | Compose list + swipe/confirm |
| 2 | Session thumbnail (pose/motion/frames/source) | same rule, from artifacts/files |
| 3 | Stats (sessions, open issues) | Compose header |
| 4 | New analysis: sample / upload / path | photo picker + bundled sample |
| 5 | Advanced: agentic, region box | Compose toggles/sliders |
| 6 | Live stage feed + cancel/retry | coroutine job + Flow |
| 7 | Compare two sessions (diff + side-by-side) | Compose + two ExoPlayers synced |
| 8 | Video player: scrub, frame-step, slow-mo | Media3 ExoPlayer + custom controls |
| 9 | Draw / angle tool (telestration) + save | Compose Canvas + gestures |
| 10 | Trim & export (mp4/GIF/vertical) | MediaCodec/MediaMuxer |
| 11 | Movement over time chart (playhead, tap-seek) | Compose Canvas |
| 12 | Active spans | Compose Canvas |
| 13 | Frames read (contact sheet) + provenance | image + details sheet |
| 14 | Movement map / Position map | Bitmap/Canvas |
| 15 | Side-to-side movement (axes, band %, dots) | Compose Canvas |
| 16 | Skeleton / Body angles / Body 3D | MediaPipe + Canvas + SceneView |
| 17 | Fast-hand events | chips |
| 18 | Object path / Object trajectory (3D) | YOLO + Canvas + SceneView |
| 19 | Observations findings (Play/Player/Ball, TT) | same grouping from `tt_reading` |
| 20 | Key moments (AI) + Moment clips | list + ExoPlayer |
| 21 | Advice (focus, working/improve, summary, since-last) | Compose |
| 22 | Practice (drills checklist + detail) | Compose |
| 23 | Details (caveats, limits, export) | Compose + share sheet |
| 24 | Ask (+ voice in/out) | TextToSpeech + SpeechRecognizer |
| 25 | Diagnostics (calls/tools/tokens/timeline) | Compose |
| 26 | Provenance ("how" + "details") on every item | bottom sheet |
| 27 | Export md/html/pdf, reel, card | files + share intent |
| 28 | Light/dark theme | Material 3 dynamic theme |
| 29 | Environment/readiness | settings check screen |
| 30 | Photo input (posture-only) | same |

## 12. Permissions & platform

- `INTERNET` (models). `READ_MEDIA_VIDEO` / `READ_MEDIA_IMAGES` (Android 13+). `CAMERA` (optional
  in-app capture). `RECORD_AUDIO` (voice ask). Optional: notifications for a running job.
- Min SDK ~26; target latest. Bundle models in `assets/` (pose ~6 MB, ball ~28 MB).

## 13. Settings

- API: base URL, key, text model, vision model (defaults from `.env`).
- Analysis: agentic on/off, frame budget, region box default.
- Appearance: theme. Language (later).
- A **"Test connection"** button (health check against the model endpoint).

## 14. Phased delivery

- **P0 — Skeleton**: Compose shell, storage, settings, DeepSeek client, report model.
- **P1 — MVP (core value)**: pick video → sample frames → **vision + text** → report → render
  **Observations + Coaching**. (No CV charts yet.)
- **P2 — Measure**: metrics + maps + contact sheet → **Analysis** (Heat maps, Movement, Frames).
- **P3 — Pose**: MediaPipe → Skeleton, Body angles, Body 3D, Fast-hand events.
- **P4 — Ball**: YOLO → Object path/trajectory, Active spans.
- **P5 — Review tools**: telestration, trim/export/reel/card, Compare.
- **P6 — Polish/parity**: Ask + voice, Diagnostics, readiness, theme, full checklist green.

## 15. Risks & mitigations

- **On-device compute** (pose/ball) → sample densely but capped; run offline passes in parallel;
  short clips only; NNAPI/GPU delegate.
- **Model packaging** (MediaPipe/ONNX/TFLite) → all three have official Android artifacts; models are
  already in the repo.
- **ffmpeg licensing** → use `MediaCodec`/`MediaMuxer`/Media3 instead of shipping ffmpeg.
- **3D charts effort** → reuse a WebView canvas or SceneView; keep it simple orthographic like today.
- **API cost/latency** → same frame budgets + token guard as desktop; show progress.
- **Parity drift** → §11 checklist is the source of truth; each phase closes rows.

## 16. Open questions

- Cross-platform instead of native (Kotlin Multiplatform / Flutter) to share one UI for iOS too?
- Bundle a **local** fallback model for offline stories, or stay cloud-only?
- Multi-sport models (retrain the ball detector per sport)?
- Release on Play Store (adds signing, policy, privacy disclosures)?

---

*This plan deliberately mirrors the current app so the Android version shows the **same rubrics** —
Analysis, Observations, Coaching, Diagnostics — with no code reuse and no backend.*

---

# Development appendices

These appendices make the plan a **build spec**: what to port, with the exact parameters,
contracts, and schema. Source references are to the current app (read them, then reimplement).

## Appendix A — Module port map

| Current (Python) | Android target | Responsibility |
|---|---|---|
| `core/config.py` | `data/Settings.kt` | the same knobs (see B) |
| `core/stages/measure/sampling.py` | `media/Sampler.kt` | motion-weighted & even/burst/window sampling + cache |
| `core/video/metrics.py` | `media/Metrics.kt` | activity, subject region/track, mechanics, posture, maps, `analyze`, `text` |
| `core/video/imaging.py` | `media/Imaging.kt` | contact sheet, overlays |
| `core/stages/measure/ball.py` | `media/Ball.kt` | heuristic + tracker + segmentation |
| `integrations/ballmodel.py` | `media/BallModel.kt` | ONNX YOLO detect (ORT Mobile/TFLite) |
| `core/stages/measure/strokes.py` | `media/Strokes.kt` | fast-hand events from pose wrists |
| `core/stages/measure/quality.py` | `media/Quality.kt` | footage-quality gate |
| `integrations/pose.py` | `media/Pose.kt` | MediaPipe Tasks PoseLandmarker → landmarks/angles/3D |
| `core/stages/observe/*` | `pipeline/Observe.kt` | contact sheet, zoom windows, **vision** calls, JSON parse |
| `core/stages/coach/*` | `pipeline/Coach.kt` + `llm/ReportTools.kt` | report prompt, tools, verification, retrieval, clips |
| `domain/game_reading.py` | `domain/GameReading.kt` | CV → table-tennis findings + moments |
| `domain/report.py` | `data/Report.kt` | normalize / validate / calibrate |
| `domain/evaluate.py` | `domain/Evaluate.kt` | quality score |
| `domain/compare.py` | `domain/Compare.kt` | two-session diff |
| `domain/progress.py`, `drills.py` | `domain/*.kt` | themes, drill catalog |
| `integrations/reporting.py` | `export/Reporting.kt` | Markdown / HTML |
| `integrations/media.py` | `media/Clips.kt` | reel, moment clips, trim, GIF, vertical |
| `integrations/cards.py` | `media/Cards.kt` | share card PNG |
| `surfaces/gui2/client/**` | `ui/**` (Compose) | every screen & component (§10) |
| `surfaces/gui2/server/read.py` | `data/ReadModel.kt` | shapes the report for the UI (tt_reading, drill_details) |

## Appendix B — Algorithm & parameter reference

**Sampling** (`Sampler.kt`)
- Probe: downscale **160×90**, grayscale; probe budget **64**; interval energy = mean abs diff of
  consecutive probes.
- Allocate frame budget (default **12**) across intervals weighted **`0.3 + e/peak`** (0.3 baseline);
  place frames evenly inside each interval; always keep **first & last**.
- Also: `sample_window` (even in [start,end]), `sample_burst` (target fps **8**, cap 20),
  `sample_even` (ball pass), `max_width` **768**, `max_seconds` **0** (whole clip).
- Vision zoom: **6** frames/ window, **3** windows max, zoom fps **8**.

**Metrics** (`Metrics.kt`)
- Activity: downscale **320×180** grayscale, mean abs frame diff = energy; global shift via **FFT
  phase correlation** (`dx, dy`).
- Subject region: background = per-pixel **median**, foreground = `|g-bg| > 18`, largest connected
  blob; `region_box` (l,t,r,b) overrides.
- Body regions: three horizontal thirds; per-frame foreground threshold **18**, min **10 px**;
  lower-body lateral range = `max(cx) − min(cx)`; direction changes = sign flips with **|Δ| > 0.005**.
- Mechanics keys: `lower_lateral_range, lower_vertical_range, upper_lateral_range,
  lower_direction_changes, crouch_box_range`; plus `footwork_series` (per-frame lower `cx`).
- Maps: motion map (summed diffs → red overlay), position heatmap (subject-centre histogram, blur).

**Ball** (`Ball.kt` / `BallModel.kt`)
- Heuristic: warm/white blob masks, area ≥ **2**, aspect 0.4–2.5, fill ≥ 0.4; optional Hough circles.
- Tracker: constant velocity, max link **0.16** (normalized), tolerate **2** missed frames, keep
  tracks ≥ **3** points and travel ≥ **0.05**; velocity smoothing `0.6·new + 0.4·old`.
- ONNX: letterbox to **640**, class-agnostic NMS, conf **0.25**; model `ball.onnx`
  (YOLOv5, in `[1,3,640,640]`, out `[1,25200,6]`).
- Segmentation: threshold `max(median·1.3, median+0.5)`; spans ≥ **0.4 s**.

**Strokes** (`Strokes.kt`)
- Track pose wrists (landmarks **15 / 16**); faster wrist per step; local maxima above
  **0.35 ×** peak speed; merge events within **0.4 s**.

**Quality score** (`Evaluate.kt`)
- `30·evidence_coverage + 20·has_summary + 15·has_focus + 10·has_limitations + 10·has_issues +
  15·(no hallucination flags)`. Forbidden words: `spin, rpm, km/h, kph, mph, ball speed, degrees,
  exact angle`.

**Config knobs** (`Settings.kt`, same defaults): `VISION_MAX_FRAMES 12`, `VISION_MAX_WIDTH 768`,
`VISION_ZOOM_FRAMES 6`, `VISION_MAX_WINDOWS 3`, `VISION_ZOOM_FPS 8`, `VISION_PROBE_BUDGET 64`,
`VISION_MAX_SECONDS 0`, `BALL_SAMPLE_FPS 10`, `BALL_MAX_FRAMES 400`, `AGENTIC_MODE false`,
`VERIFY_REPORTS true`, `HIGHLIGHT_CLIPS true`, `RETRIEVAL true`, `DEMO_FALLBACK true`.

## Appendix C — DeepSeek API & prompt contract

**Client**: `POST {API_BASE}/chat/completions`, `Authorization: Bearer {API_KEY}`.
- **Vision call**: model `VISION_MODEL_NAME`; content = text prompt + **images** (base64 data-URL
  frames). Two passes (coarse → fine). Must return **only JSON**.
- **Text call**: model `MODEL_NAME`; content = the report prompt + metrics + findings; **tools** =
  JSON schemas of the ported tools; handle the tool-call loop.
- Record per-call **tokens/latency** and the **stage timeline** (for Diagnostics).

**Prompts** — port verbatim from `core/stages/observe/prompts.py` and `core/stages/coach/prompts.py`.
- `VISION_AGENT_SYSTEM` — "racket-sport video analyst… never invent measurements: no spin, ball
  speed, or exact angles… reply with ONLY the requested JSON".
- `COARSE_PROMPT` → `{ overall, attentive_windows:[{start,end,why}], limitations[] }`.
- `FINE_PROMPT` → `{ observations, signals:[{signal, evidence_times[], confidence}], limitations[] }`.

**Tools** (`ReportTools.kt`, schemas auto-derived from signatures):
- `get_profile()` → JSON `{sport, level, dominant_hand, goal}`.
- `recent_reports(n:int=5)` → JSON array of past reports.
- `save_report(report_json:str)` → validates + persists; returns "report saved" (+ warnings).

## Appendix D — Report schema (data model)

Port `domain/report.py` + the runtime additions. Fields:

```
date, sport, summary, strengths[], focus, progress, limitations[],
issues[{ issue, evidence_times[], confidence: high|medium|low }],
drills[],                       # + drill_details[] (catalog lookup)
metrics { activity[], track[], posture{}, mechanics{...}, footwork_series[],
          pose[], pose_summary{}, pose3d_summary{}, calibration{}, calibrated{},
          ball { path[], segments[], stats{}, trajectory3d[] }, strokes[], ... }
artifacts { frames, motion, heatmap, pose, pose_hero, ball, metrics, observability }  # file paths
clips { "<key>": path }         # moment clips
annotations                     # user drawings
usage, timeline[], calls[], tools[],   # observability
tt_reading { findings[], moments[], text },   # computed on read
quality { score, warnings[], ... }
source, stem, fallback
```

`normalize()` coerces model output (bare strings → issue dicts; unknown keys dropped);
`validate()` returns problems; `calibrate()` caps confidence by footage quality.

## Appendix E — Acceptance test (parity) + P0 de-risking

**Parity test**: run the **same sample clip** on desktop and Android; assert:
- report `focus`, `issues.length`, `strengths.length` match;
- `metrics.mechanics` within a small tolerance; `footwork_series` present;
- every screen in §11 renders with the same items (no blanks).

**P0 spikes (de-risk first, one day each):**
1. Decode a real phone video and sample motion-weighted frames (perf).
2. **MediaPipe Android** pose landmarks vs the Python numbers on one frame (angle/bone parity).
3. **ONNX Runtime Mobile** runs `ball.onnx` on-device and returns detections.
4. One **DeepSeek vision** call from the device returns parseable JSON.
5. One **Compose** chart (movement) draws and stays in sync with an ExoPlayer playhead.

If all five pass, the remaining work is filling in Appendix A row by row.

## Appendix F — Prompts (verbatim — port exactly)

**Vision agent system**
```
You are a racket-sport video analyst. You inspect images (contact sheets, motion
maps, pose overlays, frames) by calling the read_file tool on the file paths you
are given. Reason from what you see and the measured metrics. Never invent
measurements: no spin, ball speed, or exact angles. Reply with ONLY the requested
JSON object, with no prose outside it.
```

**COARSE_PROMPT** (`{n} {sport} {level} {hand} {goal} {metrics} {duration}`)
```
These are {n} frames sampled in time order from a {sport} session video,
shown as one contact sheet (top-left to bottom-right).
Player: level {level}, {hand}-handed, working on: {goal}.

Measured motion metrics (authoritative):
{metrics}

Pick the windows most worth a closer look (e.g. around the peak-motion time or a
change in direction). Reply with ONLY a JSON object:
{
  "overall": "one or two sentences on what the clip shows",
  "attentive_windows": [{"start": <seconds>, "end": <seconds>, "why": "short reason"}],
  "limitations": ["short limitation", "..."]
}
Give 1-3 windows within [0, {duration}]. No prose outside the JSON.
```

**FINE_PROMPT** (`{z} {sport} {level} {hand} {goal} {metrics} {windows}`)
```
You are given the contact sheet plus {z} extra frames zoomed from the
windows you asked about, a motion map (red = movement), and measured metrics.
...
Return ONLY a JSON object:
{
  "observations": "a few sentences describing stance, footwork, weight shift, recovery and stroke shape, citing timestamps like t=2.9s",
  "signals": [
    {"signal": "short finding", "evidence_times": [<seconds>, ...], "confidence": "high|medium|low"}
  ],
  "limitations": ["short limitation", "..."]
}
Every signal must be supported by the frames. Do not claim spin, ball speed or
exact angles. No prose outside the JSON.
```

**STILL_PROMPT** (`{sport} {level} {hand} {goal}`) — photo input (posture only; motion cannot be
assessed; must say so in `limitations`).

**Report agent system (REPORT_AGENT_SYSTEM)** — you are Topspin Review; tools
`get_profile` / `recent_reports(n)` / `save_report(report_json)`; save EXACTLY this shape:
```json
{"date":"...","sport":"...","summary":"...","strengths":["..."],
 "issues":[{"issue":"...","evidence_times":[2.9,3.8],"confidence":"high|medium|low"}],
 "drills":["..."],"focus":"...","progress":"...","limitations":["..."]}
```
Most impactful issues first; **every issue must cite `evidence_times`**; never invent spin/speed/angles;
if unclear, say so in `limitations` and keep confidence low; reply with a short plain-text summary.

**VERIFY_PROMPT** (`{issues} {evidence}`) →
`{"supported":[<0-based indices>],"unsupported_reasons":{"<index>":"why"}}` — strict; drop unsupported.

**Agentic system (AGENTIC_SYSTEM)** — tools `get_measurements()`, `inspect_window(start,end,frame_count)`
+ report tools; procedure: get_measurements → inspect_window (1-3) → save_report; same JSON shape.

**Deterministic report query** (the user message that drives the report agent):
```
Today is {date}. Write my coaching report for a {sport} session.
Player: {profile_line}.

History: {progress_note}[ Recurring themes: {repeated}.]
[Related past sessions:\n{related}]

Analysis ({n} sampled frames, windows examined: {window_label}):
{observations}

Measured motion/mechanics:
{metrics_text}

Game reading (those measurements read in {sport} terms):
{reading_text}

Footage quality: {quality_note}.

[Baseline (previous session):\n{baseline}]

Check the player against this technique rubric (issues should map to it):
{rubric}

Save the report with save_report (schema with evidence_times and confidence), then give me a short summary.
```

**`observations_text(coarse, fine)` format:**
```
Overview: {coarse.overall}
Detailed observations: {fine.observations}
Signals (with evidence):
  - {signal} (t={t1, t2}; confidence {conf})
Limitations:
  - ...
```

**Rubrics** (`RUBRICS[sport]`, 6 criteria each): table tennis, tennis, badminton, squash, padel —
e.g. TT: ready stance/balance · split-step on contact · footwork into the ball · weight transfer ·
early compact prep · recovery.

## Appendix G — DeepSeek payload examples & error handling

**Vision call** (OpenAI-compatible images):
```json
POST {API_BASE}/chat/completions
{
  "model": "{VISION_MODEL_NAME}",
  "temperature": 0,
  "messages": [
    {"role": "system", "content": "<VISION_AGENT_SYSTEM>"},
    {"role": "user", "content": [
      {"type": "text", "text": "<COARSE_PROMPT>"},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<frame>"}}
    ]}
  ]
}
```
Parse the assistant `content` as JSON (strip ``` fences). Two passes (coarse → fine).

**Text/tools call:**
```json
{
  "model": "{MODEL_NAME}",
  "messages": [{"role": "system", "content": "<REPORT_AGENT_SYSTEM>"},
               {"role": "user", "content": "<query>"}],
  "tools": [
    {"type":"function","function":{"name":"get_profile","description":"...","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"recent_reports","parameters":{"type":"object","properties":{"n":{"type":"integer"}}}}},
    {"type":"function","function":{"name":"save_report","parameters":{"type":"object","properties":{"report_json":{"type":"string"}},"required":["report_json"]}}}
  ],
  "tool_choice": "auto"
}
```
Loop: if `tool_calls`, execute locally and append `tool` messages, repeat (max ~25 iterations).

**Error handling:** retries `LLM_RETRIES` (2) with backoff; timeout `LLM_TIMEOUT`; on hard failure
**fall back to the last recorded report** for the clip (badge "recorded run"), else show the error.

## Appendix H — UI spec (mobile)

**Design tokens** (from the web app):
- Palette: `accent #4f46e5`, `accent2 #818cf8`, `good #34d399`, `bad #fb7185`, `warn #fbbf24`.
- Surfaces (dark → light): bg `11,11,15` → `251,251,253`; panel `21,21,29` → `244,244,248`;
  line `38,38,47` → `226,226,236`; text `236,236,242` → `18,18,26`; muted `156,163,175` → `100,116,139`.
- Type: **display = Space Grotesk**, **body = Inter**. Radius: cards **20 dp**, media **14 dp**;
  borders 2 dp. Material 3 dynamic color maps to these.

**Navigation graph** (Compose `NavHost`):
```
sessions ─▶ new            (mode = video/photo; sample picker)
sessions ─▶ result/{stem}  (tabs: video|analysis|observations|coaching|diagnostics)
sessions ─▶ compare        (earlier/later, diff, synced players)
any      ─▶ settings       (api key/base/models, defaults, test connection)
result sub-nav: video( motion|frames ) · analysis( heatmaps|movement|pose|object )
                observations( findings|moments ) · coaching( advice|practice|details|ask )
```

**Screens (wireframe-level):**
- **Sessions**: top bar (🏓 name · Settings), stats row (Sessions · Open issues), **＋ New analysis**,
  session carousel/list (thumbnail | name · date · sport | focus | issues), **Compare two sessions**.
- **New**: source picker (Photo/Video from phone, Sample), advanced (agentic, region box),
  **Analyze**; live **stage feed** (preparing → vision: overview → vision: detail → pose → agent →
  verify → clips) with **Cancel/Retry**; **Readiness** (model reachable, models present, permissions).
- **Result header**: session name, sport · date, "recorded run" badge.
- **Video/Motion**: player (ExoPlayer) + controls (play, ◀/▶ frame-step, 0.25×/0.5×/1×, scrub),
  **Draw / Angle tool** (finger), **Trim & export** (trim, GIF, vertical); then **Movement over time**
  (full-width chart, tap-to-seek) and **Active spans**. **Video/Frames**: contact sheet + provenance.
- **Analysis**: item = label + plain "how" + a **"details"** sheet (method/engine/source).
  Heat maps (2 images), Movement (Side-to-side: chart with axes + shaded band % + direction-change
  dots, then the two stat cards), Pose (Skeleton, Body angles chart, interactive 3D, Fast-hand chips),
  Tracked object (path image, interactive 3D trajectory).
- **Observations/Findings**: three cards **Play / Player / Ball** (TT terms) with the same visuals;
  **Moments**: Key moments list (tap to play) + moment clips.
- **Coaching/Advice**: read-aloud, **Focus next session** (prominent), **What's working / What to
  improve** (2-col), summary + "since last time". **Practice**: drill checklist + progress.
  **Details**: caveats, limits, Save/export (MD, HTML, reel, card). **Ask**: input + **mic** + answers
  (read aloud + replay).
- **Diagnostics**: model calls (with probe flag), tools, tokens (incl. cached), stage timeline.

**States** (every screen): loading · empty · error · offline · permission-denied. Charts render from
`metrics`; missing data → the item is hidden (e.g. no `footwork_series` → no chart), never a blank box.

## Appendix I — Edge cases

- **Photo input** → STILL_PROMPT; posture only; movement/pose-over-time items hidden.
- **No ball detected** → "no object detected" note; Object path/chips hidden; rest normal.
- **Pose fails** → skeleton/angles/3D/fast-hand hidden; everything else works.
- **No source file** (old report) → show report; hide player/trim; badge.
- **Failed run** → fall back to the last recorded report (`DEMO_FALLBACK`), badge "recorded run".
- **Long clip** → `VISION_MAX_SECONDS` cap; progress; cancel/retry mid-run.
- **Offline** → clear message; keep past reports browsable; Ask/analyze disabled.
- **Permissions denied** → explain + deep-link to settings; no crash.

## Appendix J — Tests & delivery

- **Golden parity test**: bundle a short sample clip + its expected report; on Android assert
  `focus`, `issues.length`, `strengths.length` match; `metrics.mechanics` within tolerance;
  `footwork_series` present; all §11 screens render (instrumented UI smoke test).
- **Unit tests**: `Sampler` (index selection), `Metrics` (activity/mechanics numbers), `Ball`
  (tracker/NMS), `Evaluate` (score), `Report.normalize/validate`.
- **Delivery**: Gradle (Kotlin DSL), release signing, Play Store listing + **privacy disclosure**
  (video processed on-device; only sampled frames + metrics are sent to the model provider).
  Min SDK 26, target latest. Bundle pose (~6 MB) + ball (~28 MB) in `assets/`.

## Appendix K — Non-functionals

- **Performance targets**: ≤ ~90 s per ~10 s clip on a mid phone; pose/ball sampled (not every frame).
- **Battery/thermals**: run offline passes off the main thread; cap frame counts; show progress.
- **Accessibility**: TalkBack labels on controls/charts, ≥48 dp targets, contrast ≥ 4.5:1, no color-only
  meaning (pair the ✓/dots with text).
- **Privacy**: local-first; explicit consent before sending frames to the model; one-tap delete.
- **Cost**: same frame budgets + a per-run token guard; show token usage in Diagnostics.

## Appendix L — Inlined module behaviour (current code)

### L1. `metrics.text()` — metrics rendered for prompts (exact lines)
```
- overall motion: mean energy {mean_energy}, peak {max_energy} at t={peak_motion_time}s, net shift (dx,dy)=({dx}, {dy}) px
- activity timeline: t={t}s E={energy} shift=({dx},{dy}); ...          # one per step
- subject box: mean height {box_height_mean} width {box_width_mean} (aspect {aspect_mean}), lateral drift {lateral_range}
- mechanics: lower-body lateral range {lower_lateral_range}, direction changes (step proxy) {lower_direction_changes}, upper-body lateral range {upper_lateral_range}, crouch change {crouch_box_range}
- ball (heuristic): {summary} [visible {n} frames, max speed {v}/s, x-range {x}, y-range {y}, {h} hit(s), {b} bounce(s)]
- pose joints (degrees/normalized): {k=v, ...}
- pose 3D (degrees, world-landmark): {k=v, ...}
- footwork (pose estimate): {steps} lateral step(s), {hops} hop(s)/split-step(s), base travel {base_travel}
- calibrated (body-relative, distance-independent): {k=v, ...}
- strokes (wrist-speed peaks, pose): {n} candidate(s) at {t}s({hand}), ...
```

### L2. Image rendering
- **Contact sheet** (`contact_sheet`): `cols=4`, `cell=384×216`, bg `(18,18,22)`; paste each frame resized
  into the grid; label `#<i+1> t=<t:.2f>s` in yellow `(255,235,60)` over a black `108×16` box at `(x+4,y+3)`.
- **Motion map** (`motion_map`): 640×360; sum `|gray[i]-gray[i-1]|`; zero outside the subject mask;
  divide by peak; overlay on frame 0 → `R += acc·200`, `G,B ·= (1 − 0.6·acc)`.
- **Position heatmap** (`position_heatmap`): 640×360; grid `(w/4, h/4)`, add **60** per subject centre
  (clamp 255); `resize` bilinear + `GaussianBlur(w/60)`; normalise by peak; overlay →
  `R += heat·200`, `G,B ·= (1 − 0.7·heat)`.

### L3. Footage-quality gate (`quality.evaluate`) — exact rules
```
score = 100
height < 480                       → "low resolution"                 −20
single still image                 → "single still image — only static posture can be judged …"  −15
else:  fps and fps < 25            → "low frame rate (<fps> fps) — fast footwork may be missed"  −25
       duration and duration < 3   → "very short clip (a few rallies are better)"  −15
       len(frames) < 8             → "few frames sampled"  −10
       not mean_energy             → "little visible movement detected"  −30
subject_coverage is None (video)   → "could not isolate the player from the background"  −20
return { score: max(0,score), usable: score >= 40, warnings }
```

### L4. Game reading (`game_reading.summarize`) — TT translation
Groups **Play / Player / Ball**. Findings (`{group,label,value,note}`):
- **Play** — `Rallies` (count) · `Phases` (segment labels) · `Contacts / bounces` (hits/bounces) ·
  `Activity` (busy ≥8 / moderate ≥3 / quiet).
- **Player** — `Strokes` (count + L/R) · `Knee bend` (extended ≥150 / moderate ≥120 / deep) ·
  `Elbow bend` (l/r) · `Stance` (loaded if crouch>0.25 else upright) · `Torso lean` · `Rotation`
  (shoulder/hip) · `Footwork` ("moving well around the table" if lateral>0.15 else "mostly stationary"
  + note "side-to-side travel…, ~N changes of direction").
- **Ball** — `Tracked` (visible frames) · `Pace` (relative, max speed) · `Path extent` (x/y).
- **Moments** (`moments`): from CV events — segment starts ("active span"), contacts
  ("direction change"), strokes ("<hand> fast-hand"); sorted, merged within 0.3 s.
- Returns `{ findings[], moments[], text }` (`text` = `label: value (note)` joined by `; `).

### L5. Annotations schema (`domain/annotations`)
```
types = arrow | line | circle | pen | angle ;  default color "#f97316" (≤16 chars)
coords normalized 0..1 (clamped, 4dp)
line/arrow/circle: {type,color,x1,y1,x2,y2}
pen: {type,color,points:[[x,y]…]}   # ≥2 pts, ≤500
angle: {type,color,points:[[x,y],[x,y],[x,y]]}  # exactly 3
```

### L6. Drill catalog (`domain/drills.lookup`, keyword → entry)
`split-step/split step/timing hop` → **Split-step** ("Small hop as the opponent contacts; land as the
ball leaves their racket." / "Add it to shadow footwork, then to multi-ball.") ·
`footwork/shuffle/step-and-plant/step then/step into` → **Footwork** ·
`recovery/re-set/reset` → **Recovery** · `weight transfer/load/crouch/dip-and-drive` → **Load & drive** ·
`shadow/no ball` → **Shadow swings** · `multi-ball/multiball` → **Multi-ball** · `serve/toss` → **Serve** ·
`forehand` → **Forehand** · `backhand` → **Backhand**. (Each has `name`, `cue`, `progression`.)

### L7. Compare (`domain/compare.compare(older,newer)`)
Themes via `progress.classify`: `improved = old − new`, `regressed = new − old`,
`unchanged = old ∩ new`. `metric_deltas` = per-mechanics-key `new − old`. `energy_delta` =
`mean_energy` diff. `text` = `"<old> -> <new>; improved: …; regressed: …; still open: …; mean energy ±"`.

### L8. Progress themes (`domain/progress`)
`THEMES` keywords → `footwork|stroke|preparation|recovery|serve`; `classify(text)` returns the set;
`summarize` computes theme_trend, repeated_themes (≥2 sessions), focus_status
(`achieved` / `still open` / `no longer flagged`), and a one-line `text`.

### L9. Exports (`integrations/reporting`)
- **Markdown**: `# Topspin Review report — <video>` · `- Sport/Date` · summary ·
  `## Strengths/Drills/Limitations` (bulleted) · `## Issues` (`issue_line`) · `## Focus next session` ·
  `## Progress`.
- **HTML**: same sections, self-contained; embeds **data-URI** images for `motion`, `pose`, `frames`;
  inline `<style>` (system-ui, max-width 860). **PDF** via `reportlab` (A4, wrap at 100 chars) else
  HTML-to-print.

### L10. Media (`integrations/media`)
- **Clip**: `ffmpeg -ss -to -c copy` (fast) → fallback `libx264 -preset veryfast -an` (accurate).
- **Clips** (`make_clips`): up to **3**, centred at `t−1.0 … t+2.0`, named `moment_<i>_<t>s.mp4`.
- **Reel** (`make_reel`): concat, `scale=1280:720:…decrease,pad=1280:720,setsar=1`, `libx264 -an`.
- **Export** (`export_clip`): **gif** → optional `crop=ih*9/16`, `fps=12`, `scale=720`, palettegen/use;
  **mp4** → optional vertical `crop=ih*9/16` + `scale=720:1280`, `setsar=1`.

### L11. Share card (`integrations/cards`, 1200×630 PNG)
bg = `pose_hero || motion || frames`, brightness ×0.42; `"Topspin Review"` (38) at (60,60);
`"{sport} · {date}"` (24) at (60,118); `"{n} thing(s) to fix"` (56) at (60,210); focus wrapped (28,
≤4 lines) from y=320; quality score line (24, accent) at bottom-left.

### L12. UI copy catalog (`outputs.js`) — every item, grouped by tab
Each item carries: **how** (plain, player), **method** (technical), **detail** (source), **engine**.

| Tab / group | Item | how | method (short) | detail | engine |
|---|---|---|---|---|---|
| Video · Your clip | Video | your uploaded clip; moments are in Key moments | — | — | — |
| Video · Your clip | Frames read | the exact stills the AI looked at; favours busy moments | motion-weighted sampling: 64 probes @160×90, budget split 0.3+e/peak, keep first/last, tiled | `sampling.py + imaging.py · contact_sheet()` | ffmpeg + Pillow |
| Video · Motion | Movement over time | movement energy moment-to-moment; a peak = burst | 320×180 gray, mean abs diff (in subject region); shift via FFT phase correlation | `metrics.py · activity()` | NumPy |
| Video · Motion | Active spans | stretches of consistent activity, calm gaps between | energy ≥ max(median·1.3, median+0.5); spans ≥0.4s; summarized by reversals | `ball.py · phase_segments()` | — |
| Analysis · Movement | Side-to-side movement | how far hips/legs travelled left–right | lower third of subject box tracked; spread of centre = lateral range; reversals counted | `metrics.py · body_regions()` | NumPy |
| Analysis · Movement | Movement map | heat map of where the picture changed (red=action) | summed grayscale diffs 640×360, subject-restricted, normalised, red overlay | `metrics.py · motion_map()` | Pillow |
| Analysis · Movement | Position map | where the subject spent most time | 2D histogram of subject centre, blurred, red overlay | `metrics.py · position_heatmap()` | Pillow |
| Analysis · Pose | Skeleton | your body as a stick figure at a key moment | PoseLandmarker (lite) 33 landmarks/frame; connections drawn; hero=peak motion | `pose.py · overlay()` | mediapipe |
| Analysis · Pose | Body angles | knee/elbow angles through the clip | angles from 3 points (knee=hip-knee-ankle, elbow=shoulder-elbow-wrist) + stance/crouch | `pose.py · estimate()` | mediapipe |
| Analysis · Pose | Body 3D | spin-around 3D model; depth is a best guess | world landmarks (3D metres) → 3D angles + torso lean + shoulder/hip twist | `pose.py · estimate()` | mediapipe |
| Analysis · Pose | Fast-hand events | moments a hand moved fastest (+ which hand) | wrists (landmarks 15/16), faster wrist, local maxima >0.35×peak, merge <0.4s | `strokes.py · segment()` | mediapipe |
| Analysis · Tracked object | Object path | route the tracked object took (rough) | YOLO ONNX (letterbox 640, NMS) or blob detect; constant-velocity tracker (jump 0.16, 2 misses, ≥3 pts) | `ballmodel.py detect()` / `ball.py candidates()` | onnxruntime / NumPy |
| Analysis · Tracked object | Object trajectory | route in 3D; shape useful, distances not | depth z = √(median_area/area) + screen (x,y) → rotatable 3D path | `ball.py · trajectory3d()` | — |

Item keys map to `report.artifacts` (image items), `report.metrics` (charts/3D), `report.clips`, and
`tt_reading` (Observations findings).

### L13. `format.js` helpers
- `movementSeries(report)` → `metrics.activity` as `{t, energy}`.
- `fmtTime(s)` → `"m:ss.s"` or `"s.sss"`; `moments(report)`/`issueGroups(report)` flatten issues×times.
- `POSE_SERIES` = `[{l_knee,"Left knee",#4f46e5},{r_knee,"Right knee",#818cf8},{l_elbow,"Left elbow",#34d399},{r_elbow,"Right elbow",#fbbf24}]`.
- `CONF_TONE` high→`text-bad`, medium→`text-warn`, low→`text-muted`; `CONF_HELP` text.
- `STEP_NAME`, `STEP_GROUP`, `GROUP_ORDER` (`Setup · Measure · Vision (observe) · Report (coach) · Finalize`),
  `MODEL_STEP`, `STEP_SHORT` — the step naming used by the live feed and Diagnostics (verbatim in source).
- `captionFor(report)` share text; `scoreTone` (≥80 good, ≥60 warn, else bad).

### L14. Diagnostics (`Technical.svelte`)
Two cards — **Model calls** (n, vision/text split) and **Tokens billed** (total, vision/text, cached) —
then tabs **Stages | Calls & tools**.
- **Stages**: the `timeline` grouped by `STEP_GROUP`, durations as bars, total seconds; a `vision`/`text`
  tag on model steps (`MODEL_STEP`), hover = `STEP_SHORT`.
- **Calls & tools**: model calls + tool calls merged by `seq`, grouped by `stage`; each model call
  expands to **Input** (messages) · **Images sent** (via `/callmedia/<stem>/<name>`) · **Output**
  (text) or **requested tool** (`name` + arguments); **probe** calls show the image-support self-check
  ("What color is this image?" → `output`). Tool events show arguments + result/error.
- Report fields: `usage {vision{calls,total_tokens,cached_tokens,…}, text{…}, total_tokens, models{text,vision,provider,api_base}}`, `calls[]` (with `seq, stage, model, prompt/completion/cached tokens, seconds, input, output, images[], requested[], probe`), `tools[]` (`name, arguments, result, error, seconds, seq, stage`), `timeline[]` (`stage, seconds`).

## Appendix M — Reference pin + example report JSON

**Target the desktop app at commit `5e9b89c517c93553acfb0fb1544304e7a25f3c15`** (this plan was written
against it). Diff the ported code against that rev.

**Example report** (`<stem>_report.json`, real shape):
```json
{
  "date": "2026-10-08", "sport": "table tennis",
  "summary": "…", "focus": "…", "progress": "…",
  "strengths": ["…"],
  "issues": [{"issue":"Footwork is near-static … t=2.9, 3.0, 4.5, 4.7 …",
              "evidence_times":[2.9,3.0,4.5,4.7],"confidence":"medium"}],
  "drills": ["…"], "limitations": ["…"],
  "observations": "…", "windows": [{"start":1.0,"end":4.0}], "signals": ["…"],
  "source": "runtime/data/sample.mp4", "frames": 14, "frame_times": [0,0.75,…], "region_box": null,
  "metrics": { "activity":[…], "track":[…], "posture":{…}, "mechanics":{…}, "footwork_series":[…],
               "pose":[…], "pose_summary":{…}, "pose3d_summary":{…}, "calibration":{…}, "calibrated":{…},
               "ball":{"segments":[…],"path":[…],"stats":{…},"trajectory3d":[…]}, "strokes":[…],
               "mean_energy":…, "max_energy":…, "peak_motion_time":…, "net_shift":[…], "footwork":{…} },
  "artifacts": {"frames":"…","motion":"…","heatmap":"…","pose":"…","pose_hero":"…","ball":"…",
                "metrics":"…","observability":"…"},
  "usage": {"vision":{"calls":4,"total_tokens":34766,"cached_tokens":0,"prompt_tokens":31679,"completion_tokens":3087,"seconds":18.21,"vision_calls":[…]},
            "text":{"calls":4,"total_tokens":45234,…}, "calls":8, "total_tokens":80000,
            "models":{"text":"deepseek-v4-pro","vision":"deepseek-v4-flash-vision-exp","provider":"OpenAI","api_base":"https://api.deepseek.com"}}
}
```
(On read the server adds: `stem`, `calls[]` with `probe` flags, `tools[]`, `timeline[]`, `score`,
`has_source`, `drill_details[]`, `tt_reading`.)

## Appendix N — Project setup

- **Gradle (Kotlin DSL)** modules: `:app` (Compose UI + DI) and `:core` (pipeline/llm/media) so the
  heavy logic is testable without Android UI.
- **Key dependencies** (verify latest at build time): Compose BOM, Material3, `androidx.navigation`,
  `androidx.work`, `androidx.media3` (exoplayer + transformer), Hilt (+dagger), OkHttp + kotlinx.serialization,
  **OpenCV Android**, **com.google.mediapipe:tasks-vision**, **onnxruntime-android** (or
  TFLite + `ultralytics` export).
- **SDK**: `minSdk 26`, `targetSdk` latest, `compileSdk` latest. **ABIs**: `arm64-v8a` + `armeabi-v7a`
  (add `x86_64` for emulators). Bundle pose + ball models in `assets/`.
- **R8/ProGuard**: keep rules for MediaPipe Tasks, ONNX Runtime, OpenCV (JNI); keep serialized models.
- **Size budget**: ≤ ~80 MB APK (models ~34 MB of it); use App Bundle + per-ABI splits.

## Appendix O — App internals

- **Pattern**: unidirectional — `StateFlow<UiState>` from a `ViewModel`; UI is stateless Compose.
- **DI**: Hilt modules for `LlmClient`, `SettingsStore`, `ReportStore`, `Pipeline`.
- **Long job**: the analysis runs in a **WorkManager** `CoroutineWorker` (survives backgrounding/process
  death); progress via `setProgress()` → `WorkInfo` `Flow` → the live stage feed. Cancel = `cancelWork()`.
- **Threading**: decode/CV on a dispatcher-backed worker; the two model calls are suspend; artifacts on IO.
- **Streaming**: none required — stage events (ticks) plus a spinner; token streaming optional later.

## Appendix P — Legal / licensing + privacy

- **Bundled third-party**: MediaPipe Tasks (Apache-2.0), ONNX Runtime (MIT), OpenCV (Apache-2.0),
  the ball model `pingpongball-yolo` (**MIT**), fonts (Inter = OFL, Space Grotesk = OFL). Ship a
  **NOTICE/attributions** screen + file.
- **Privacy**: video is processed **on-device**; only **sampled frames + metrics** are sent to the
  configured model provider. Consent dialog before the first upload; one-tap delete; no analytics.
  A short **privacy policy** text must accompany any store listing.

## Appendix Q — Localization

- All UI strings in `strings.xml` (EN default; add values-zh). Report language follows the UI language
  where the model supports it. **Note:** the current prompts are English-only (no Chinese text exists
  in the code) — translating prompts is future work, not parity.

## Appendix R — Distribution / ops

- **Crash reporting**: optional (e.g. Play Console vitals) — keep privacy-respecting.
- **Play**: internal → closed → open test tracks; **App Bundle**; versionCode/versionName from Gradle.
- **CI**: a GitHub Actions job that builds the debug APK, runs unit tests, and (optionally) an
  instrumented smoke test on an emulator.

## Appendix S — Glossary, definition of done, cost, extras

- **Glossary**: *Session/Report* = one analyzed clip (`<stem>_report.json`); *Metrics* = measured
  numbers; *Issue* = a finding with `evidence_times` + `confidence`; *Artifacts* = contact sheet, maps,
  pose, ball, metrics/observability JSON; *Usage* = tokens/latency per model call.
- **Definition of done (per phase)**:
  - *P0* — app runs; Settings saves; a "Test connection" call succeeds.
  - *P1* — pick video → report with Observations+Coaching renders; stored; list shows it.
  - *P2* — Analysis (Heat maps, Movement, Frames) + provenance render.
  - *P3* — Pose items render (skeleton/angles/3D/fast-hand).
  - *P4* — Ball items render (path/3D trajectory/active spans).
  - *P5* — telestration, trim/GIF/vertical, reel, card, Compare work.
  - *P6* — every §11 row green; Ask+voice, Diagnostics, readiness, theme.
- **Cost estimate**: per the sample usage → ~**80k tokens / run** (≈35k vision + 45k text). At current
  DeepSeek pricing that's a few cents per session; show it in Diagnostics; keep the token guard.
- **Share-into-app / share-out**: register an `ACTION_SEND`/`ACTION_VIEW` intent filter (video/photo →
  New analysis); share results via `ACTION_SEND` (reel mp4 / card png / report html).
- **Retention/cleanup**: cap stored reports (e.g. last N) and prune artifacts/cache; expose in Settings.
- **Import existing desktop reports**: offer a one-time import of `<stem>_report.json` + artifacts
  (matching schema) so old sessions appear in the app.
