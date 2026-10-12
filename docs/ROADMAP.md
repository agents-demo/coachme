# Topspin Review — Roadmap & Competitor Feature Plan

*Planning document for later implementation. Precise, code-grounded, and deliberately broad —
it lists far more than we will build, grouped by phase so we can cherry-pick.*

Scope: close the gap to commercial "film your sport → get coaching" apps, then extend past
them with our agentic, evidence-grounded, self-hosted angle.

---

## 0. Conventions used below

- **Files** are given relative to `topspin_review/` unless noted.
- **Effort** is a rough t-shirt size for one focused engineer: `S` ≈ a day, `M` ≈ a few days,
  `L` ≈ 1–2 weeks, `XL` ≈ multi-week / needs a new model.
- Layers are `surfaces → core → integrations → domain` (enforced by
  `tests/unit/test_architecture.py`). Every feature says **where it lands** so we don't
  break the layering.
- "Competitor ref" abbreviates the apps we compared against: **CE** Coach's Eye · **SB** Sportsbox AI ·
  **OF** Onform · **SV** SwingVision · **HC** HomeCourt · **V1** V1 Sports · **HL** Hudl/Veo.

---

## 1. Where we are today (baseline)

**What ships now**
- Automatic analysis of a racket-sport clip → LLM **coaching report**: `summary`, `focus`,
  `strengths`, `issues[{issue, evidence_times, confidence}]`, `drills`, `progress`, `limitations`,
  plus a deterministic `quality` score (`domain/evaluate.py`).
- **Measured** signals (`core/video/metrics.py`): motion energy timeline, global shift, subject
  box/track, upper/lower-body lateral range, direction changes, crouch trend, heuristic ball/rally.
- **Pose** via mediapipe Tasks `PoseLandmarker` (`integrations/pose.py`): per-frame knee/elbow
  angles, stance width, crouch, landmarks → single-frame **pose hero** + **pose sheet** (`pose`).
- Surfaces: **gui2** (FastAPI + SvelteKit SPA) — Watch / Coaching / Notes / Diagnostics; moments
  playlist that seeks the video; motion chart; model-ratio + per-step grouped **Diagnostics**
  (calls/tools, tokens incl. cached, stages); **gui** (Streamlit); **cli**; **api**; **mcp**.
- Storage: one `<stem>_report.json` per video under `runtime/data/`; artifacts under
  `runtime/data/artifacts/` (`_frames/_motion/_pose/_pose_hero.png`, `_metrics.json`,
  `_observability.json`); key-moment clips under `<stem>_clips/`.
- Progress: session table + `domain/compare.py` diff (improved / unchanged / regressed + metric deltas).

**What competitors have that we don't (summary)**
- Frame-accurate **scrub / step / slow-mo**, **on-frame drawing (telestration)**, **angle tools** (CE, V1).
- **A/B video compare slider** and **overlay** (CE, OF, V1).
- **Voice narration / voice coaching** (OF), **capture guidance** (OF).
- **3D biomechanics**, kinematic sequence (SB, Uplift), **trained ball tracking** + shot type/stats (SV).
- **Auto highlight reels**, **line calls / scoring**, **real-time audio** (SV, HC).
- **Coach/team accounts, sharing, annotations, playlists** (HL, OF), **mobile app** (all), **live capture**.
- **Personalized plans / progress memory**, **injury-risk / load** (Zone7-adjacent), **social/leaderboards**.

---

## 2. Architecture placement (cheat sheet)

| Concern | Where it must live |
|---|---|
| Pure rules & schemas (report, progress, compare, a new `annotations` schema, a `compare` diff) | `domain/` (stdlib only) |
| Video math / CV primitives (angles, charts data, ball) | `core/video/` |
| Pipeline steps (new stages/ticks) | `core/stages/<name>/`, wired in `core/strategies/base.py` |
| External engines: ffmpeg, mediapipe, a new ball model, speech | `integrations/` (`media.py`, `pose.py`, `ball.py`, …) |
| HTTP endpoints & data shaping | `surfaces/gui2/server/` (`routes/*.py`, `read.py`) |
| UI | `surfaces/gui2/client/src/` (Svelte 5 runes) |
| Config toggles | `core/config.py` (app) · `integrations/agents/settings.py` (endpoint) |

Rule of thumb: **never** import `openjiuwen` outside `integrations/agents/`; keep `domain/` pure;
new endpoints go in a `routes/*.py` and are registered in `surfaces/gui2/server/app.py`.

---

## 3. Phase A — Demo quick wins (ship first)

### A1. A/B video compare slider
- **Ref:** CE, OF, V1. Most persuasive "look, I improved" visual.
- **Goal:** pick two sessions; show the two videos side-by-side with a draggable vertical divider
  and (optionally) an overlay mode (50% blend). Sync scrub/seek across both.
- **Where:** gui2 client only (+ existing `GET /compare?a=&b=` for the text/metric diff).
- **UI:** new `surfaces/gui2/client/src/lib/components/CompareVideos.svelte`; add a "Compare" section
  on the **Progress** route (we already have two selects there) rendering the slider.
- **Data:** `/source/{stem}` already serves each clip. Also surface `frame_times` so both videos seek
  to the same moment (they're different clips; sync by normalized progress, not absolute time).
- **Effort:** `M`.
- **Acceptance:** two clips side-by-side; drag divider changes the reveal; a "sync play" toggle plays
  both; works when clips have different durations; degrades to a static before/after for photos.
- **Risks:** mismatched aspect ratios/fps — letterbox and sync by percent.

### A2. Voice-over summary
- **Ref:** OF (its signature). 
- **Goal:** a "🔊 Play summary" button that reads the focus + top 2–3 issues aloud.
- **Where:** gui2 client; text already in the report.
- **UI:** button in `Coaching` (and `Watch`); use `window.speechSynthesis` with `SpeechSynthesisUtterance`;
  pick a voice, allow speed 0.8–1.2, stop on navigation. No server work.
- **Effort:** `S`.
- **Acceptance:** reads `focus` + top issues; stops on click/route change; no speech engine → button hidden.
- **Risks:** none meaningful; keep it optional.

### A3. Auto highlight reel
- **Ref:** SV, HC.
- **Goal:** stitch the key-moment clips (already produced: `media.make_clips` → `report["clips"]`)
  into one downloadable `highlight.mp4` with short cross-fades/labels.
- **Where:** `integrations/media.py` (add `make_reel`), a route in `surfaces/gui2/server/routes/media.py`
  (`GET /reel/{stem}`), and a button on `Watch`.
- **Data:** clips are on disk under `<stem>_clips/`; concat via ffmpeg (`imageio-ffmpeg`), re-encode to
  a uniform codec/size, add a title card per moment (timestamp).
- **Effort:** `M`.
- **Acceptance:** "Download highlight reel" produces a single mp4 of the flagged moments; empty when no
  clips; cached by stem+mtime.
- **Risks:** mixed clip sizes — normalize with `scale`/`pad` in the ffmpeg filter graph.

### A4. Share card (Wrapped-style PNG)
- **Ref:** the "shareable card" pattern (our own taketwo had one).
- **Goal:** a branded PNG teaser: `sport · date · score/100 · N issues · focus` + the pose hero frame,
  for sharing.
- **Where:** `integrations` (new `cards.py`, like taketwo), route `GET /cards/{stem}`, button in `Notes`.
- **Library:** Pillow (already a dep via imageio/PIL).
- **Effort:** `M`.
- **Acceptance:** PNG renders with the pose hero + key numbers; download works; sane for photo sessions.
- **Risks:** fonts (bundle a permissive font or use PIL default).

### A5. Pose angles over time
- **Ref:** SB/Uplift (biomech charts).
- **Goal:** chart `l_knee/r_knee/l_elbow/r_elbow/stance_width/crouch` across the clip's sampled frames.
- **Where:** `metrics` already yields per-frame pose (`metrics.pose[i]`, incl. landmarks and angles);
  chart in gui2 (`components/PoseChart.svelte`, SVG like `MotionChart.svelte`).
- **Effort:** `S` (`M` if we add per-frame angles — see B1).
- **Acceptance:** dual-axis line chart of knee/elbow angles vs time; synced playhead.
- **Risks:** none; data exists.

### A6. Frame-step + slow-mo
- **Ref:** CE, V1 (the core review instrument).
- **Goal:** step ±1 frame and slow to 0.25×/0.5×/1× on the Watch video.
- **Where:** gui2 `VideoReview.svelte`; `frame_times`/fps already in the report (`meta`).
- **Effort:** `S`.
- **Acceptance:** ⏮/⏭ buttons step by `1/fps`; speed menu; keyboard shortcuts.
- **Risks:** `st.video`-style `start_time` quirks don't apply (native `<video>`); fine.

### A7. Capture guide
- **Ref:** OF.
- **Goal:** a short, illustrated "how to film" screen (side-on, full body, 60fps, distance, lighting),
  shown before upload and in an empty state.
- **Where:** gui2 `app` (a modal/card) + reuse the text from `data.footage_check` hints.
- **Effort:** `S`.
- **Acceptance:** a static guide card; links from the Analyze screen.
- **Risks:** none.

---

## 4. Phase B — Core review experience (make it feel pro)

### B1. 3D biomechanics from pose world-landmarks
- **Ref:** SB, Uplift. Our biggest credible leap.
- **Goal:** compute 3D joint angles (not just 2D image angles) and add swing-plane / weight-transfer
  / knee-valgus style metrics.
- **Where:** `integrations/pose.py` — mediapipe `PoseLandmarker` already returns `pose_world_landmarks`
  (metric 3D). Extend `estimate()` to return 3D angles + torso/hip/shoulder rotation; add derived
  metrics in `core/video/metrics.py`; extend `domain/report.py` issue vocabulary + prompts.
- **Data:** add `metrics.pose3d` block; keep `pose` (2D) for back-compat.
- **Effort:** `L`.
- **Acceptance:** 3D knee/elbow angles + at least one rotation/sequencing metric per frame; surfaced in
  the report and a chart; degrades to 2D when world landmarks absent.
- **Risks:** world-landmark noise; needs calibration notes (camera angle matters).

### B2. Telestration / on-frame drawing
- **Ref:** CE, V1 (their defining feature).
- **Goal:** draw arrows/lines/circles/angles on a frozen frame; persist per session; show in the report.
- **Where:** gui2 client (a canvas overlay on the paused video) + storage of shapes.
- **Data:** new `annotations` block in the report (`domain/annotations.py` schema: shape type, points,
  color, frame time). Save via a `POST /reports/{stem}/annotations`.
- **Effort:** `L` (UI-heavy).
- **Acceptance:** draw/undo/delete shapes; persisted; re-render on load; export bakes shapes into the
  HTML/Markdown report.
- **Risks:** coordinate space across responsive layouts — store normalized (0..1).

### B3. Angle / line measurement tools
- **Ref:** CE, V1.
- **Goal:** draw a 3-point angle or a line and read degrees; ruler.
- **Where:** same canvas as B2; reuse `core/video/pose._angle` math in `domain`.
- **Effort:** `S` (after B2).
- **Acceptance:** angle readout in degrees; snap to pose joints optionally.
- **Risks:** none.

### B4. Overlay compare (blend) + side-by-side (A1 extension)
- **Ref:** CE, V1, OF.
- **Goal:** beyond the slider: a 50% **blend/onion-skin** mode and a "ghost" overlay of an earlier
  session, plus a synchronized dual scrubber.
- **Where:** gui2 client (canvas compositing), builds on A1.
- **Effort:** `M`.
- **Acceptance:** slider ⇄ blend ⇄ side-by-side; synced playhead; both sessions same normalized progress.
- **Risks:** performance of dual `<video>` + canvas on low-end devices.

### B5. Session timeline with issue markers
- **Ref:** SV (event timeline), CE (bookmarks).
- **Goal:** a single timeline strip under the video with markers for every issue/evidence time and
  rally segments; click to seek; zoom.
- **Where:** gui2 (extend `MotionChart.svelte` or new `Timeline.svelte`), data from `issues[].evidence_times`
  + `metrics.activity` + new `metrics.rallies`.
- **Effort:** `M`.
- **Acceptance:** markers map to issues; hover shows the issue; seek on click; playhead follows.
- **Risks:** crowded markers — cluster/zoom.

### B6. Drill library with how-to cards
- **Ref:** SB, OF.
- **Goal:** each `drill` becomes a card with a short description, a cue, a progression, and an optional
  image/GIF.
- **Where:** `domain` drill catalog + gui2 cards.
- **Effort:** `M` (content-heavy).
- **Acceptance:** drills show as cards; searchable; link drill → the issue it addresses.
- **Risks:** content authoring.

### B7. Progress dashboard (charts + streaks)
- **Ref:** OF, SB.
- **Goal:** richer Progress than a table: metric trends over sessions (lower-body range, crouch,
  issue count, focus-achieved rate), streaks, and a "personal bests" panel.
- **Where:** gui2 `progress` route + `domain/progress.py` (already computes trend).
- **Effort:** `M`.
- **Acceptance:** at least 3 trend lines across sessions; streak counter; degrade with <2 sessions.
- **Risks:** none.

---

## 5. Phase C — Analysis depth (the hard moat)

### C1. Trained ball tracking → shot/rally model
- **Ref:** SV (its whole product is this).
- **Goal:** replace the heuristic blob (`core/stages/measure/ball.py`) with a real detector/tracker →
  ball trajectory, bounce/contact events, shot type (forehand/backhand/serve), rally segmentation,
  and (estimated) pace.
- **Where:** new `integrations/ball.py` (external model — ONNX/TFLite, e.g. a small tracknet-style
  detector), measured in `core/video/`, surfaced as `metrics.ball2`.
- **Effort:** `XL` (model + data + integration).
- **Acceptance:** per-frame ball position with confidence; rally segments; shot classification on a
  labeled set with a stated accuracy; graceful fallback to the heuristic.
- **Risks:** dataset/licensing; CPU speed; generalization across sports.

### C2. Auto session segmentation
- **Ref:** SV, HL.
- **Goal:** feed a **whole** session file; auto-detect rallies (using C1 + motion gaps) and analyze
  each, producing per-rally reports + an aggregate.
- **Where:** new `core/stages/measure/segment.py`; strategy orchestrates per-rally runs; report gains
  `rallies[]`.
- **Effort:** `L` (after C1).
- **Acceptance:** a long clip yields N rally reports + an aggregate; user can drill into one rally.
- **Risks:** segmentation errors; cost (one LLM pass per rally — budget).

### C3. Real-time / live capture with instant feedback
- **Ref:** HC, SV (live), OF.
- **Goal:** stream from the device camera; on-device ball/pose; **instant** audio/text cue (e.g.
  "split-step", "too upright").
- **Where:** mobile/desktop capture surface + a low-latency loop; pose already per-frame; ball needs C1.
- **Effort:** `XL`.
- **Acceptance:** <1s feedback latency for a pose-based cue; graceful when the device can't keep up.
- **Risks:** latency, battery, platform permissions.

### C4. Multi-player / court-role attribution
- **Ref:** HL, SV.
- **Goal:** detect and separate multiple people (near/far player) and attribute metrics per player.
- **Where:** `core/video/` (person detection + tracking), report gains `players[]`.
- **Effort:** `L`.
- **Acceptance:** two players tracked; metrics per player; the report addresses the selected player.
- **Risks:** occlusion/crossing; CPU.

### C5. Higher-fidelity analysis inputs
- **Ref:** all.
- **Goal:** configurable higher sampling (`VISION_MAX_FRAMES/MAX_WIDTH`), multi-scale contact sheets,
  and an "analyze at 60fps burst around the peak" pass for footwork.
- **Where:** `core/config.py`, `core/stages/measure/sampling.py`, `observe/*`.
- **Effort:** `M`.
- **Acceptance:** a "thorough" mode that doubles frames around peaks; report notes the extra sampling.
- **Risks:** token/time cost (gate it).

---

## 6. Phase D — Product, platform & growth

### D1. Mobile app (capture-first)
- **Ref:** all.
- **Goal:** iOS/Android capture + on-device pose (mediapipe mobile) + upload-to-analyze; review on phone.
- **Where:** new surface(s); reuse `core/service.py` + gui2 API.
- **Effort:** `XL`.
- **Acceptance:** record → analyze → view a report on the phone.
- **Risks:** app-store builds, native mediapipe, distribution.

### D2. Coach / team layer
- **Ref:** HL, OF (the B2B path).
- **Goal:** accounts, roster, assign sessions, coach annotations/comments, shared library, playlists.
- **Where:** new auth + a multitenant store in `integrations/storage/`; routes; gui2 pages.
- **Effort:** `XL`.
- **Acceptance:** coach sees an athlete's sessions; comments persist; share links.
- **Risks:** auth/security, data model, scope creep — treat as a separate product line.

### D3. Personalized training plan + memory
- **Ref:** OF (progress), our agentic edge.
- **Goal:** a **weekly plan** generated from report history: targeted drills, load, and a progress
  review; the agent remembers past focuses and adapts.
- **Where:** new `core/stages/plan/` + agentic strategy; store plans in `runtime/data/plans/`.
- **Effort:** `L`.
- **Acceptance:** "Plan my week" produces a plan referencing past issues/foci; check-off; next week adapts.
- **Risks:** grounding (must cite evidence), not overselling.

### D4. Share links & socials
- **Ref:** OF, HL, consumer apps.
- **Goal:** public read-only report/proof links; export to Instagram/TikTok-friendly vertical clips.
- **Where:** tokenized read-only route + a "video card" renderer (ffmpeg/Pillow).
- **Effort:** `M`.
- **Acceptance:** a share URL renders the report read-only; a vertical highlight clip exports.
- **Risks:** privacy defaults (opt-in).

### D5. Assessments / skill ratings
- **Ref:** SB, HC.
- **Goal:** a per-skill rubric (footwork, preparation, transfer, recovery) with a score 1–5 and a
  "level" estimate; reassessed each session.
- **Where:** `domain` rubric + coach prompt; chart in Progress.
- **Effort:** `M`.
- **Acceptance:** 4 skill scores per session; a radar/line chart over time; explainable (evidence-linked).
- **Risks:** subjective — must tie to measured evidence.

### D6. Injury-risk / load
- **Ref:** Zone7-adjacent.
- **Goal:** flag risky patterns (deep knee valgus, asymmetry, fatigue drift in the last reps).
- **Where:** `core/video/` derived metrics + report issue category.
- **Effort:** `L`.
- **Acceptance:** a "watch this" risk flag with evidence + a disclaimer (not medical advice).
- **Risks:** regulatory/liability — keep it non-diagnostic and clearly disclaimed.

### D7. Real-time audio coaching (non-live, playback)
- **Ref:** HC, OF.
- **Goal:** during review, an audio cue track aligned to the timeline ("here — split-step").
- **Where:** gui2 (TTS + timeline markers), builds on A2/B5.
- **Effort:** `M`.
- **Acceptance:** toggle plays cues at evidence times.
- **Risks:** none serious.

### D8. Integrations & ecosystem
- **Ref:** HL, generic.
- **Goal:** calendar/coach tools, wearables (HR/IMU), Apple Health, Strava-style export; MCP already done.
- **Where:** `integrations/` adapters.
- **Effort:** varies (`M`–`XL`).
- **Acceptance:** per-integration.
- **Risks:** auth/API churn.

---

## 7. Cross-cutting work

- **Data model:** add optional blocks to the report without breaking the schema:
  `pose3d`, `ball2`, `rallies[]`, `players[]`, `annotations[]`, `skills{}`, `plan`, `reel`.
  Keep `domain/report.normalize/validate` tolerant (unknown keys dropped, new keys optional).
- **Telemetry:** new model passes (ball, 3D pose, plan) must show in Diagnostics — attribute them to a
  **step** (the stage-provider mechanism in `integrations/agents/telemetry/traces.py`) and count tokens.
- **Cost controls:** every extra LLM pass gated by a `core/config.py` toggle + `TOKEN_BUDGET`; the
  vision "thorough" mode is opt-in.
- **Testing:** unit tests for new `domain` schemas and `core/video` math; a `tests/integration/`
  harness for the ball/3D paths; keep `test_architecture.py` green.
- **Accessibility & i18n:** captions for voice-over; keep copy short; the UI is already responsive.
- **Privacy:** local-first stays the default; share is opt-in; never send more frames than needed.

---

## 8. Prioritization (recommended sequence)

| # | Feature | Ref | Effort | Demo? | Impact |
|---|---|---|---|---|---|
| A1 | A/B video compare slider | CE/OF/V1 | M | ✅✅ | High |
| A2 | Voice-over summary | OF | S | ✅ | Medium |
| A3 | Auto highlight reel | SV/HC | M | ✅ | High |
| A4 | Share card PNG | — | M | ✅ | Medium |
| A5 | Pose angles over time | SB | S | ✅ | Medium |
| A6 | Frame-step + slow-mo | CE/V1 | S | ✅ | Medium |
| A7 | Capture guide | OF | S | ✅ | Low |
| B1 | 3D biomechanics | SB | L | — | High |
| B2 | Telestration | CE/V1 | L | ✅ | High |
| B3 | Angle tools | CE/V1 | S | ✅ | Medium |
| B5 | Issue timeline | SV | M | ✅ | High |
| C1 | Ball tracking | SV | XL | — | High |
| C2 | Auto segmentation | SV | L | — | High |
| D3 | Personalized plan + memory | OF | L | ✅ | High |
| D2 | Coach/team | HL | XL | — | High (B2B) |
| D1 | Mobile app | all | XL | — | High |

**Build order:** A6 → A5 → A2 → A1 → A3 → A4 → B1 → B2 → B3 → B5 → D3 → C1 → C2 → D1/D2 → C3/D5/D6.

**Milestones**
- **M1 (demo-ready):** A1–A7. One polished, shareable result with compare, voice, reel, pose charts.
- **M2 (pro review):** B1, B2, B3, B5, B6, B7. Telestration + 3D metrics + a real review timeline.
- **M3 (depth):** C1, C2, C5. Ball tracking + auto segmentation + thorough mode.
- **M4 (platform):** D1–D5. Mobile, coach/team, plans, shares, skills.

---

## 9. Non-goals / guardrails

- **Not medical.** D6 stays non-diagnostic and disclaimed.
- **No fabricated measurements.** Keep the "measured-only" stance (`domain/evaluate.py` flags
  spin/speed/angle claims); new features must cite evidence.
- **Local-first by default.** Anything that leaves the machine (share, team) is opt-in.
- **Don't break the layering.** New external engines land in `integrations/`; pure rules in `domain/`.
- **Don't bloat one run.** Every extra pass is a toggle; Diagnostics must show it.

---

*Last updated: planning draft — not yet implemented beyond Phase 0.*
