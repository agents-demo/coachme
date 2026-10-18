# Topspin Review — Roadmap & Competitor Feature Plan

*Planning document for the work **still ahead**. Completed features have been removed; this lists only
open items, grouped by phase so we can cherry-pick.*

Scope: close the remaining gap to commercial "film your sport → get coaching" apps, then extend past
them with our agentic, evidence-grounded, self-hosted angle.

> **North star — multimodal in and out.** The product *watches* the clip (a vision model reads the
> frames), *reads* the numbers it measured itself, and *listens* to audio; then it *writes* the
> coaching in plain language, *speaks* it, and *shows* it as video/images (highlight clips, overlays,
> share cards) — fusing **pictures + numbers + words** into one coach, every claim tied to a moment.
> Most tools do one sense (pure computer vision, or pure text); doing all of them is the core
> advantage. Keep it central in every feature and every demo.

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

## 1. Where we are today

What the app does today is documented in [architecture.md](architecture.md) and
[USAGE.md](../guides/USAGE.md); this roadmap lists only the work that is **not** done.

**Shipped since the last revision:** Android app, English/Chinese UI and reports, ask-by-voice,
3D body view, automatic rally segments, footage-quality guidance, progress/compare, share card and
vertical/GIF/reel exports, and one-click session delete.

Table-tennis-specific ideas (service detection, racket-angle proxy, table heatmap, annotated clips,
multi-session trends) are merged into C11–C13 and D12–D13 below.

**What competitors have that we don't (summary)**
- **3D biomechanics** kinematic sequence, **shot type/stats** (SB, Uplift, SV).
- **Line calls / scoring**, **real-time audio** (SV, HC).
- **Coach/team accounts, sharing, annotations, playlists** (HL, OF), **iOS app**, **live capture**.
- **Personalized plans / progress memory**, **injury-risk / load** (Zone7-adjacent), **social/leaderboards**.

---

## 2. Architecture placement (cheat sheet)

| Concern | Where it must live |
|---|---|
| Pure rules & schemas (report, progress, compare, `annotations` schema, a `compare` diff) | `domain/` (stdlib only) |
| Video math / CV primitives (angles, charts data, ball) | `core/video/` |
| Pipeline steps (new stages/ticks) | `core/stages/<name>/`, wired in `core/strategies/base.py` |
| External engines: ffmpeg, mediapipe, a new ball/person model, speech | `integrations/` (`media.py`, `pose.py`, `ballmodel.py`, …) |
| HTTP endpoints & data shaping | `surfaces/gui2/server/` (`routes/*.py`, `read.py`) |
| UI | `surfaces/gui2/client/src/` (Svelte 5 runes) |
| Config toggles | `core/config.py` (app) · `integrations/agents/settings.py` (endpoint) |

Rule of thumb: **never** import `openjiuwen` outside `integrations/agents/`; keep `domain/` pure;
new endpoints go in a `routes/*.py` and are registered in `surfaces/gui2/server/app.py`.

---

## 3. Phase 0 — Foundations (do first)

Quality, trust, and reliability — cheap items that de-risk every feature above and make the
demos believable. These are **not** user-visible features but they decide whether the visible ones
are worth anything.

### 0.1 Evaluation & prompt regression
- **Goal:** a labeled benchmark + regression tests so issue quality and tokens don't silently drift.
- **Where:** extend `tests/eval/expected.json` and add a **graded** suite to
  `tests/integration/evaluate_reports.py` (per-clip expected issues/metrics), plus a `pytest` marker
  that runs it offline on shipped reports.
- **Acceptance:** `pytest -m eval` prints per-clip issue precision/recall vs labels; CI fails on
  regression below thresholds; a golden report snapshot test for the prompt.
- **Effort:** `M`. **Risks:** label authoring (needs a coach or careful build).

### 0.2 Calibration & normalization
- **Goal:** make metrics **comparable across sessions** (camera distance/angle/zoom change the
  pixel-relative numbers today — so "progress" can be an artifact).
- **Where:** `core/video/metrics.py` — add a normalization step; options: (a) table/court detection
  as a scale reference, (b) subject-height normalization (pose shoulder→ankle), (c) an explicit user
  "distance/height" input stored in the profile (`core/config.py` + profile store).
- **Data:** store `calibration` in the report; re-state metrics in calibrated units where possible.
- **Acceptance:** two clips of the same player at different distances produce comparable ranges
  (within a stated tolerance); report notes the calibration basis; `compare` warns when uncalibrated.
- **Effort:** `L`. **Risks:** detection robustness; may need a calibration UI later.

### 0.3 Feedback loop (thumbs / corrections)
- **Goal:** capture 👍/👎 and "this is wrong" per issue; store it; use it to improve prompts.
- **Where:** report gains `feedback[]`; route `POST /reports/{stem}/feedback`; small UI on each issue.
- **Acceptance:** feedback persists; a `tools/` view lists disagreements per prompt version; prompt
  changes reference the feedback.
- **Effort:** `S`. **Risks:** building the loop is easy; acting on it is the real work.

### 0.4 UX fundamentals
- **Goal:** first-run onboarding, empty states, a **session library** (search / filter / tags /
  rename / notes / bulk delete), and **token streaming** so the report appears as it's written.
- **Where:** gui2 (`routes`, `read.py`, a new `tags` field) + streaming via SSE on the analyze path.
- **Acceptance:** tag/rename/search sessions; report streams progressively; clear loading/empty/error
  states everywhere.
- **Effort:** `M` (search/tags) + `M` (streaming). **Risks:** SSE plumbing with the job manager.

### 0.6 Model portability & offline
- **Goal:** run against any provider (OpenAI / Anthropic / vLLM / Ollama) and, ideally, **fully
  offline** with a local model.
- **Where:** `integrations/agents/settings.py` (provider, per-stage model names) — verify all three
  model clients work; add per-**stage** model choice (cheap model for verification, strong for the
  report).
- **Acceptance:** switch provider via `.env`; an offline/local run produces a report with no network.
- **Effort:** `M`. **Risks:** provider quirks (tool-calling, vision).

### 0.7 Privacy & compliance
- **Goal:** video of a person is sensitive — be explicit.
- **Where:** a short data-handling doc; consent line on the Analyze screen; retention setting
  (`core/config.py`, e.g. `RETENTION_DAYS`, auto-prune on `runtime.setup()`); keep local-first as the default and share opt-in.
- **Acceptance:** retention prunes old data; consent recorded; no frames leave the machine unless
  sharing is on.
- **Effort:** `S`–`M`. **Risks:** none technical; policy.

### 0.8 Deployment & ops
- **Goal:** make gui2 safely hostable.
- **Where:** optional **auth** + HTTPS behind a reverse proxy; a `Dockerfile`; CORS tightening;
  structured logs + error tracking; a health/ready endpoint for orchestration.
- **Acceptance:** one-command container run; auth-gated when exposed; errors surfaced with run ids.
- **Effort:** `M`. **Risks:** auth scope creep — keep it minimal or behind a flag.

---

## 5. Phase B — Core review experience (remaining)

### B4. Overlay compare (blend) + side-by-side
- **Ref:** CE, V1, OF.
- **Goal:** beyond the basic slider: a 50% **blend/onion-skin** mode and a "ghost" overlay of an
  earlier session, plus a synchronized dual scrubber.
- **Where:** gui2 client (canvas compositing), builds on the compare slider.
- **Effort:** `M`.
- **Acceptance:** slider ⇄ blend ⇄ side-by-side; synced playhead; both sessions same normalized progress.
- **Risks:** performance of dual `<video>` + canvas on low-end devices.

### B5. Pro / reference comparison
- **Ref:** Onform, V1.
- **Goal:** compare your motion to a **reference** — a pro template or your own best session — as an
  overlay or side-by-side, aligned by phase.
- **Where:** gui2 (phase-aligned playback) + a `domain` phase model.
- **Effort:** `M`. **Acceptance:** pick a reference; see a phase-aligned comparison at contact.
- **Risks:** reference licensing; alignment robustness.

### B6. Multi-sport generalization
- **Ref:** —
- **Goal:** take the pipeline beyond table tennis (tennis, badminton, squash, padel): sport-aware
  prompts, terms, and calibration.
- **Where:** `domain/` sport profiles/terms, prompts, `core/config.py`.
- **Effort:** `L`. **Acceptance:** a tennis clip yields a sensible report through the same pipeline.
- **Risks:** per-sport tuning; must not dilute quality for the beachhead sport.

---

## 6. Phase B.5 — Measure-stage expansion (the analysis core)

The `measure` stage is where signal quality is won or lost. Remaining work below.

### Steps (in `core/stages/measure/`)
- **M3. Stroke / repetition segmentation** — new `segment.py`. Strokes/reps from motion peaks + wrist
  velocity → `segments[]`. The **enabler** for per-rep metrics, consistency, and per-stroke feedback. **M**.
  *Acceptance:* N segments with start/end; per-rep metrics + variance; degrades gracefully.
- **M5. Extended footage check** — grow `quality.py`: full-body framing / pose completeness, lighting,
  **camera shake**, distance, fps → usable/limits + actionable tips. **S**.
- **M6. Scene / cut detection** — detect cuts in multi-rally recordings (rally segments already exist). **S**.
- **M7. Handedness auto-detect** — infer left/right from which arm swings more; suggest profile. **S**.
- **M8. Thorough sampling mode** — config-gated extra burst around motion peaks (uses `sample_burst`). **S**.

### Integrations (in `integrations/`)
- **I1. Person detection** — real **person** detection/tracking (`person.py`); enables multi-player
  (C4). **M**.
- **I2. Subject segmentation model** — mediapipe SelfieSegmentation or a small model to isolate the
  player (better than the current background-subtraction). **M**.
- **I4. Monocular depth (MiDaS)** — rough depth/scale to assist calibration. **L**.
- **I5. OCR** — read a **scoreboard/scoreline** from the video for match context. **S**.

### Priority within B.5
1. **M3 segmentation** (correctness/enabler) → 2. **M5/M6** footage+rally → 3. **I1/I2**
   (raw-signal upgrades) → 4. **I4/I5/M7/M8**.

All land in the existing layering (steps in `core/stages/measure/*`, engines in `integrations/*`) →
`tests/unit/test_architecture.py` stays green.

---

## 7. Phase C — Analysis depth (the hard moat)

### C1. Ball: shot-type & pace
- **Ref:** SV (its whole product is this).
- **Goal:** on top of the working ball tracker, classify **shot type** (forehand/backhand/serve) and
  estimate **pace** per contact; rally segmentation from contacts.
- **Where:** `core/video/` (features from the ball track + pose); prompts in `domain/report.py`.
- **Effort:** `L`.
- **Acceptance:** shot labels on a labeled set with a stated accuracy; graceful fallback.
- **Risks:** dataset/licensing; generalization across sports.

### C2. Whole-session auto segmentation
- **Ref:** SV, HL.
- **Goal:** feed a **whole** session file; auto-detect rallies (using the ball signal + motion gaps) and
  analyze each, producing per-rally reports + an aggregate.
- **Where:** new `core/stages/measure/segment.py`; strategy orchestrates per-rally runs; report gains
  `rallies[]`.
- **Effort:** `L` (after C1).
- **Acceptance:** a long clip yields N rally reports + an aggregate; user can drill into one rally.
- **Risks:** segmentation errors; cost (one LLM pass per rally — budget).

### C3. Real-time / live capture with instant feedback
- **Ref:** HC, SV (live), OF.
- **Goal:** stream from the device camera; on-device ball/pose; **instant** audio/text cue (e.g.
  "split-step", "too upright").
- **Where:** mobile/desktop capture surface + a low-latency loop (per-frame pose + ball).
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

### C6. Line calls / scoring / match stats
- **Ref:** SV (its headline feature).
- **Goal:** automatic **scorekeeping**, in/out calls (advisory, with a "review" affordance), rally
  stats, and a **match summary**.
- **Where:** needs court detection + the ball track; `domain` match model; report gains `match{}`.
- **Effort:** `L`. **Acceptance:** score tracked with reviewable calls + a match summary; calls clearly
  labelled advisory. **Risks:** accuracy/liability — never present as official.

### C7. Multi-camera / dual-angle
- **Ref:** pro tools (Onform/V1 multi-cam).
- **Goal:** analyze two **synced** captures (front + side) for depth/3D fusion and a better read.
- **Where:** multi-file submission; sync by audio/pose; fusion in `core/video/`.
- **Effort:** `L`. **Acceptance:** two clips analyzed together with better depth cues. **Risks:** sync;
  more compute.

### C8. 3D biomechanics — kinematic sequence
- **Ref:** SB (its core product).
- **Goal:** joint-by-joint **kinematic sequence** (hips → torso → shoulder → arm) and phase timing
  (backswing, contact, follow-through) per stroke.
- **Where:** `core/video/` (from pose 3D world landmarks) + `integrations/pose.py`; report gains
  `biomechanics{}`.
- **Effort:** `L`. **Acceptance:** sequence + timing per stroke with confidence; degrades without 3D.
- **Risks:** monocular 3D accuracy; needs a clean side view.

### C9. Spin estimation (stretch — likely stays a non-goal)
- **Ref:** SV.
- **Goal:** estimate **spin** (type and rough amount) if it can be done honestly.
- **Where:** `core/video/` ball cues (+ possibly a small model).
- **Effort:** `XL`. **Acceptance:** only if reliable; otherwise keep it as a clearly-stated limitation.
- **Risks:** single-camera spin is unreliable — do **not** ship a guess; the app stays honest.

### C10. Audio understanding (a new sense)
- **Ref:** — *(multimodal core).*
- **Goal:** add **audio** to the multimodal core — e.g. a coach's spoken notes, or racket/impact
  sounds as extra evidence. The pipeline already *watches + reads numbers + writes + speaks*; this
  adds *listening*.
- **Where:** `integrations/` (audio → text via a speech model) + `core/stages/observe/` (feed the
  transcript into the reasoning); report gains an `audio{}` block.
- **Effort:** `M`. **Acceptance:** a clip with spoken notes produces findings that cite them.
- **Risks:** transcription quality; keep it opt-in and privacy-safe.

---

## 8. Phase D — Product, platform & growth

### D1. iOS app (Android shipped)
- **Ref:** all.
- **Goal:** iOS capture + on-device pose (mediapipe mobile) + upload-to-analyze; review on phone.
- **Where:** new iOS surface; reuse `core/service.py` + gui2 API.
- **Effort:** `XL`.
- **Acceptance:** record → analyze → view a report on iPhone.
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
- **Where:** `domain` rubric + coach prompt; chart in the report / a progress view.
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
- **Where:** gui2 (TTS + timeline markers), builds on the voice-over + issue timeline.
- **Effort:** `M`.
- **Acceptance:** toggle plays cues at evidence times.
- **Risks:** none serious.

### D8. Integrations & ecosystem
- **Ref:** HL, generic.
- **Goal:** calendar/coach tools, wearables (HR/IMU), Apple Health, Strava-style export.
- **Where:** `integrations/` adapters.
- **Effort:** varies (`M`–`XL`).
- **Acceptance:** per-integration.
- **Risks:** auth/API churn.

### D9. Coach comments on frames + drill assignments
- **Ref:** HL, OF.
- **Goal:** a coach pins **comments to a frame/time** and **assigns drills**; the athlete sees them
  in-session and gets a notification.
- **Where:** builds on annotations + D2 (accounts).
- **Effort:** `M` (after D2). **Acceptance:** comments persist and surface; assignments trackable.
  **Risks:** scope — keep it to comments + assignment, not full LMS.

### D10. Gamification — challenges & leaderboards
- **Ref:** HC.
- **Goal:** drills as **challenges** with streaks, plus **leaderboards** — make practice sticky.
- **Where:** gui2 + a small store (opt-in).
- **Effort:** `M`. **Acceptance:** join/complete a challenge; an opt-in leaderboard ranks users.
- **Risks:** privacy/social moderation; keep everything opt-in.

### D11. Cross-device sync
- **Ref:** consumer apps.
- **Goal:** sync sessions and the plan across devices (phone ↔ web) once accounts exist.
- **Where:** builds on D2 (accounts) + a sync store.
- **Effort:** `M`–`L`. **Acceptance:** a session recorded on the phone shows up on the web.
- **Risks:** conflict handling; data privacy.

### C11. Service detection
- **Ref:** — *(table-tennis-specific).*
- **Goal:** flag likely serves (toss, no prior contact, player at own end) so serve technique,
  placement and variety get their own coaching instead of being treated as rally strokes.
- **Where:** `core/stages/measure/` from pose + ball segments; report `strokes[].type="serve"`.
- **Effort:** `M`. **Acceptance:** serves flagged with confidence and degrade gracefully when the toss
  is out of frame. **Risks:** false positives; toss often cropped.

### C12. Racket-angle proxy
- **Ref:** — *(table-tennis-specific).*
- **Goal:** estimate wrist/forearm orientation at contact as a coaching hint. This is a **proxy**, not
  the racket face — pose models do not track the racket.
- **Where:** pose landmarks + ball direction; report `racket_angle_proxy` with an "approximate" label.
- **Effort:** `M`. **Acceptance:** proxy shown with a caveat and never presented as a measured racket
  angle. **Risks:** misleading if overclaimed; depends on contact timing.

### C13. Table contact-point heatmap
- **Ref:** — *(table-tennis-specific).*
- **Goal:** top-down heatmap of where the ball lands, revealing cross-court bias / short-long patterns.
- **Where:** manual 4-corner table calibration + trajectory/table-plane intersection; gui2 and Android
  overlay.
- **Effort:** `L`. **Acceptance:** calibrated sessions show a landing heatmap; uncalibrated sessions
  hide it. **Risks:** calibration UX, camera angle, monocular depth.

### D12. Multi-session trend view
- **Ref:** OF (progress).
- **Goal:** aggregate issue recurrence, drill completion and key metrics across all sessions, not just
  pairwise compare.
- **Where:** a trends endpoint over existing reports + a chart in gui2 and Android.
- **Effort:** `M`. **Acceptance:** trend lines with ≥3 sessions; warns when metrics are uncalibrated.
- **Risks:** sparse data; keep the pairwise compare as the fallback.

### D13. Annotated coaching clips
- **Ref:** CE, OF.
- **Goal:** burn issue text + timestamp into a trimmed clip (e.g. "right elbow too high — 0:04") for
  sharing.
- **Where:** existing trim/reel pipeline + a text-overlay pass (ffmpeg/Media3).
- **Effort:** `M`. **Acceptance:** exported clip shows the issue labels at their timestamps and is
  shareable. **Risks:** render cost/text layout.

---

## 9. Cross-cutting work

- **Data model:** add optional blocks to the report without breaking the schema:
  `ball2` (shot type), `rallies[]`, `players[]`, `skills{}`, `plan`, `match`, `biomechanics{}`. Keep
  `domain/report.normalize/validate` tolerant (unknown keys dropped, new keys optional). Multimodal
  additions (`audio{}` transcript) follow the same rule.
- **Telemetry:** new model passes (shot type, plan, person) must show in Diagnostics — attribute them
  to a **step** (the stage-provider mechanism in `integrations/agents/telemetry/traces.py`) and count
  tokens.
- **Cost controls:** every extra LLM pass gated by a `core/config.py` toggle + `TOKEN_BUDGET`; the
  vision "thorough" mode is opt-in.
- **Testing:** unit tests for new `domain` schemas and `core/video` math; a `tests/integration/`
  harness for the ball/person/3D paths; keep `test_architecture.py` green.
- **Accessibility:** captions for voice-over; keep copy short; keep the UI responsive.
- **Privacy:** local-first stays the default; share is opt-in; never send more frames than needed.

---

## 10. Prioritization (recommended sequence)

| # | Feature | Ref | Effort | Impact | Multimodal |
|---|---|---|---|---|---|
| 0.1–0.8 | Foundations: eval, calibration, feedback, UX, offline, privacy, ops | — | M–L | High | |
| M3 | Stroke / repetition segmentation | — | M | High | |
| M5 | Extended footage check | — | S | Medium | |
| M6 | Scene / rally detection | — | M | Medium | |
| M7 | Handedness auto-detect | — | S | Low | |
| M8 | Thorough sampling mode | — | S | Low | |
| I1 | Person detection | SV | M | Medium | |
| I2 | Subject segmentation model | — | M | Medium | |
| I4 | Monocular depth (MiDaS) | — | L | Low | |
| I5 | OCR scoreboard | — | S | Low | |
| B4 | Overlay compare (blend) | CE/V1 | M | Medium | |
| B5 | Pro / reference comparison | OF/V1 | M | Medium | |
| B6 | Multi-sport generalization | — | L | High | |
| C1 | Ball: shot-type & pace | SV | L | High | |
| C2 | Whole-session segmentation | SV | L | High | |
| C3 | Real-time / live capture | HC/SV/OF | XL | High | |
| C4 | Multi-player attribution | HL/SV | L | Medium | |
| C5 | Higher-fidelity inputs (thorough) | — | M | Medium | |
| C6 | Line calls / scoring / match stats | SV | L | High | |
| C7 | Multi-camera / dual-angle | — | L | Medium | |
| C8 | 3D biomechanics / kinematic sequence | SB | L | High | |
| C9 | Spin estimation (stretch; likely non-goal) | SV | XL | Low | |
| C10 | Audio understanding (a new sense — listen) | — | M | High | ✓ |
| C11 | Service detection | — | M | High | |
| C12 | Racket-angle proxy (wrist/forearm) | — | M | Medium | |
| C13 | Table contact heatmap | — | L | Medium | |
| D1 | iOS app (Android shipped) | all | XL | High | |
| D2 | Coach / team | HL | XL | High (B2B) | |
| D3 | Personalized plan + memory | OF | L | High | |
| D4 | Share links & socials | OF/HL | M | Medium | |
| D5 | Assessments / skill ratings | SB/HC | M | Medium | |
| D6 | Injury-risk / load | — | L | Medium | |
| D7 | Real-time audio coaching (playback — speak) | HC/OF | M | Medium | ✓ |
| D8 | Integrations & ecosystem | HL | M–XL | Medium | |
| D9 | Coach comments + drill assignments | HL/OF | M | Medium | |
| D10 | Gamification — challenges & leaderboards | HC | M | Medium | |
| D11 | Cross-device sync | — | M–L | Medium | |
| D12 | Multi-session trend view | OF | M | High | |
| D13 | Annotated coaching clips | CE/OF | M | Medium | |

**Multimodal** marks work that extends the core senses: **watch** (vision), **read** its own numbers,
**write**, **listen** (C10), **speak** (D7). The foundation of every item is the multimodal core.

**Build order:** 0.2 → 0.1 → 0.3 → **M3** → M5/M6 → I1 → I2 → B4 → B5 → **C1 (shot type)** → **C2** →
C8 → C10 → C6 → C3 → D3 → D1/D2 → D4/D5/D6/D7/D8/D9/D10/D11 → D12/D13. C11–C13 run with the analysis depth work. (0.4–0.8 and B6 run alongside.)

**Milestones (remaining)**
- **M-foundations:** 0.1–0.8. Eval harness, feedback, session library + streaming, offline, privacy,
  deploy/ops.
- **M-measure:** M3, M5–M8 + I1–I2. Stroke segmentation, footage check, rally detection, person/segmentation.
- **M-review:** B4–B6. Overlay compare, reference comparison, multi-sport.
- **M-depth:** C1–C13. Shot type, whole-session segmentation, line calls, thorough mode, 3D biomechanics, audio sense, serve detection, racket-angle proxy, table heatmap.
- **M-platform:** D1–D13. iOS, coach/team, plans, shares, skills, integrations, gamification, sync, trends, annotated clips.

---

## 11. Metrics of success

How we know it's working (not vanity features):

- **Report usefulness** — % of sessions with a 👍 on the focus/top issue (from 0.3). Target ≥ 70%.
- **Issue precision / recall** — vs the labeled benchmark (0.1); tracked per release.
- **Trust** — hallucination-flag rate must stay **0**; **100%** of issues must cite evidence.
- **Adherence** — % of sessions where a drill was checked off and the athlete returned within 7 days.
- **Retention** — sessions per user per week; week-2 return rate.
- **Time-to-insight** — median analyze time (target ≲ 90 s for a ~10 s clip on a warm run).
- **Demo reliability** — % of demo runs that complete or fall back cleanly. Target **100%**.
- **Cost** — median tokens + $ per session, and cache-hit ratio.

---

## 12. Product strategy & validation

**Personas**
- **Primary:** the self-taught racket-sport amateur (plays 1–3×/week, no coach, films on a phone).
- **Secondary:** the club/intermediate player chasing technique; the **coach** (a buyer for D2); the
  parent of a junior.

**Beachhead:** **table tennis** first (our sample is TT; tables are everywhere; self-taught players
abound), then tennis → badminton/squash/padel. Resist going broad before one sport is great.

**Positioning:** *"the coach you can replay."* Automatic, **evidence-grounded** (every claim cites a
timestamp), **private/local by default**, and it writes a **plan you can question** (agentic report +
Ask) — not just metrics.

**Moat vs table stakes**
- Moat: the **multimodal core** — takes in *watch* (vision) + *read* (its own numbers) + *listen*
  (audio), and puts out *write* (language) + *speak* (voice) + *show* (video/images) — fused and
  evidence-grounded — plus the agentic **plan + memory** (D3) over session history, the
  **local/open pipeline**, the evidence discipline, and the run diagnostics.
- Table stakes (competitors have): tracking, pose, charts, compare, reels.

**Business model (if productizing):** freemium (N sessions) → subscription; **coach/team seats** (D2);
self-host with **bring-your-own-model** (0.6).

**Go-to-market:** club partnerships, coach outreach, sport communities (forums/subreddits), and
shareable demos (highlight reel / share card / D4) as the top of the funnel.

**Validation plan:** interview ~5 coaches + ~10 amateurs; the two questions that matter —
"is the report useful?" (from 0.3 👍) and "would you pay?"; wire both to the Metrics of success (§11).

---

## 13. Engineering foundations & risks

- **Schema versioning.** Add `schema_version` to the report; a `domain/report.migrate()` so new
  blocks (`ball2`, `match`, `players`, `plan`) coexist with old reports; the reader tolerates missing
  keys. Migrate on read, write the new version on next save.
- **Prompt & model versioning / reproducibility.** Record the **prompt id/hash + model + provider**
  per run (the prompt isn't recorded yet). Re-running with the same inputs should
  be explainable; keep a golden-report snapshot test (§0.1).
- **Security.**
  - **Frame prompt-injection:** the vision model reads **OCR'd text from the video** — a user could
    put "ignore your instructions…" on screen. Mitigate: instruct the model to treat on-screen text as
    **data, not instructions**; strip/flag instruction-like text; never let frame text trigger tools.
  - Upload validation (extension + size + magic bytes), **rate limiting**, and **auth** before exposing
    (§0.8); generalize the media path guards (`/artifact`, `/callmedia`, `/clip`) to one helper.
- **Storage / scaling.** JSON-per-report + a single-process in-memory job manager won't scale: plan
  **SQLite→Postgres** for metadata, an artifact **retention/size** policy, and a real **worker pool**
  (process pool or RQ/Celery) for jobs. Keep runtime paths via `integrations/storage/runtime.py`.
- **Performance budgets.** Video first frame < 1 s; chart render < 100 ms; target analyze ≲ 90 s for a
  ~10 s clip (warm). Track in §11.
- **Test strategy.** Unit (`domain`, `core/video`), architecture (`test_architecture.py`), **API
  contract** tests for gui2 routes, **gui2 end-to-end** (Playwright), **eval** (§0.1), and a
  load/latency test. Keep `ruff` + `pytest` green as the merge gate.
- **Licenses & compliance.** Verify **mediapipe** + the `pose_landmarker` model asset licenses, the
  ball-detector model license, the share-card **font** license, any **dataset** used for C1, and the
  openjiuwen dependency terms.
- **Observability.** Structured logs with **run ids**; a small dashboard for eval drift and cost; error
  tracking (0.8).

---

## 14. Dependencies & go/no-go gates

**Dependency graph (key edges)**
- `0.1–0.8` → **foundations** for everything.
- `0.2` (calibration) → trustworthy `compare`/progress (`D5`).
- `B4` → builds on the compare slider.
- `C2` → needs `C1`; `C6` → needs `C1` (+ court detection); `C3` (live) → needs `C1`+`C2`+3D pose.
- `C4` → needs person detection (I1).
- `D3` (plan) → needs report history + `0.3` (feedback); `D2`/`D9` → need auth (`0.8`).

**Go/no-go gates**
- **M-foundations:** eval harness green & prompt-regression stable; calibration tolerance met; demo
  fallback 100%.
- **M-depth:** ball shot-type accuracy clears its stated threshold on the labeled set — else **descope
  C1/C6** and keep the heuristic + a "low confidence" label.
- **M-platform:** a coach/team pilot with ≥N coaches retained 4 weeks, else park D2.

---

## 15. Non-goals / guardrails

- **Not medical.** D6 stays non-diagnostic and disclaimed.
- **No fabricated measurements.** Keep the "measured-only" stance (`domain/evaluate.py` flags
  spin/speed/angle claims); new features must cite evidence.
- **Local-first by default.** Anything that leaves the machine (share, team) is opt-in.
- **Don't break the layering.** New external engines land in `integrations/`; pure rules in `domain/`.
- **Don't bloat one run.** Every extra pass is a toggle; Diagnostics must show it.

---

*Last updated: open items only — completed features removed.*
