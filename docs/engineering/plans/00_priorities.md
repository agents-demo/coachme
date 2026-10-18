# Topspin Review — Roadmap & Priorities

**Role:** master roadmap and sequencing guide. Start here for "what next."
Each feature has its own plan file (linked below); this file is the index,
priority table, and product strategy.

> **North star — evidence-backed adaptive coaching.** The pipeline measures
> before it writes, ties every finding to measured evidence, and — in
> Investigator mode — adapts the investigation to what is found. Standard mode
> (fixed pipeline, evidence-grounded) is the reliable default. Investigator
> mode is opt-in until the benchmark gates pass.

---

## 1. Where we are today

**Shipped:** Android app, English/Chinese UI and reports, ask-by-voice, 3D body
view, automatic rally segments, footage-quality guidance, progress/compare,
share card and vertical/GIF/reel exports, one-click session delete.

**In progress:** Investigator mode — see [03_investigator.md](03_investigator.md).
Remains behind a feature flag until benchmark gates pass ([01_benchmark.md](01_benchmark.md)).

**What competitors have that we don't (summary)**
- 3D biomechanics / kinematic sequence (Sportsbox AI, Uplift).
- Shot type / stats (SwingVision).
- Line calls / scoring, real-time audio (SwingVision, HomeCourt).
- Coach/team accounts, sharing, annotations, playlists (Hudl/Veo, Onform).
- iOS app, live capture.
- Personalized plans / progress memory; injury-risk / load; social/leaderboards.

---

## 2. Architecture placement (cheat sheet)

| Concern | Where it must live |
|---|---|
| Pure rules & schemas | `domain/` (stdlib only) |
| Video math / CV primitives | `core/video/` |
| Pipeline steps | `core/stages/<name>/`, wired in `core/strategies/base.py` |
| External engines (ffmpeg, mediapipe, models, speech) | `integrations/` |
| HTTP endpoints & data shaping | `surfaces/gui2/server/routes/*.py` |
| UI | `surfaces/gui2/client/src/` (Svelte 5 runes) |
| Config toggles | `core/config.py` (app) · `integrations/agents/settings.py` (endpoint) |

Never import `openjiuwen` outside `integrations/agents/`. Keep `domain/` pure.
New endpoints go in a `routes/*.py` and register in `surfaces/gui2/server/app.py`.

---

## 3. Phase 0 — Foundations (do first)

Quality, trust, and reliability — not user-visible, but they decide whether
visible features are worth anything.

| # | Feature | File | Effort |
|---|---|---|---|
| 0.1 | Eval harness & prompt regression | [04_eval-harness.md](04_eval-harness.md) | M |
| 0.2 | Calibration & normalization | [05_calibration.md](05_calibration.md) | L |
| 0.3 | Feedback loop (thumbs / corrections) | [06_feedback-loop.md](06_feedback-loop.md) | S |
| 0.4 | UX fundamentals (session library, streaming) | [07_ux-fundamentals.md](07_ux-fundamentals.md) | M+M |
| 0.6 | Model portability & offline | [08_model-portability.md](08_model-portability.md) | M |
| 0.7 | Privacy & compliance | [09_privacy-compliance.md](09_privacy-compliance.md) | S–M |
| 0.8 | Deployment & ops | [10_deployment-ops.md](10_deployment-ops.md) | M |

---

## 5. Phase B — Core review experience (remaining)

| # | Feature | File | Effort |
|---|---|---|---|
| B4 | Overlay compare (blend / side-by-side) | [11_overlay-compare.md](11_overlay-compare.md) | M |
| B5 | Pro / reference comparison | [12_reference-comparison.md](12_reference-comparison.md) | M |
| B6 | Multi-sport generalization | [13_multi-sport.md](13_multi-sport.md) | L |

---

## 6. Phase B.5 — Measure-stage expansion (analysis core)

**Priority within B.5:** M3 first (enabler) → M5/M6 → I1/I2 → I4/I5/M7/M8.

| # | Feature | File | Effort |
|---|---|---|---|
| M3 | Stroke / repetition segmentation | [14_stroke-segmentation.md](14_stroke-segmentation.md) | M |
| M5+M6 | Footage quality + rally/scene detection | [15_footage-rally-detection.md](15_footage-rally-detection.md) | S+S |
| M7+M8 | Handedness auto-detect + thorough sampling | [16_handedness-sampling.md](16_handedness-sampling.md) | S+S |
| I1+I2 | Person detection + subject segmentation | [17_person-segmentation.md](17_person-segmentation.md) | M+M |
| I4+I5 | Monocular depth + scoreboard OCR | [18_depth-ocr.md](18_depth-ocr.md) | L+S |

All land in `core/stages/measure/*` or `integrations/*`; `test_architecture.py`
must stay green.

---

## 7. Phase C — Analysis depth (the hard moat)

| # | Feature | File | Effort | Key dependency |
|---|---|---|---|---|
| C1 | Ball shot-type & pace | [19_ball-shot-type.md](19_ball-shot-type.md) | L | existing ball tracker |
| C2 | Whole-session auto-segmentation | [20_session-segmentation.md](20_session-segmentation.md) | L | C1 |
| C3 | Real-time / live capture | [21_live-capture.md](21_live-capture.md) | XL | C1, C2, 3D pose |
| C4 | Multi-player attribution | [22_multi-player.md](22_multi-player.md) | L | I1 |
| C5 | Higher-fidelity sampling (thorough mode) | [23_high-fidelity-sampling.md](23_high-fidelity-sampling.md) | M | — |
| C6 | Line calls / scoring / match stats | [24_line-calls.md](24_line-calls.md) | L | C1 + court detection |
| C7 | Multi-camera / dual-angle | [25_multi-camera.md](25_multi-camera.md) | L | C1, depth |
| C8 | 3D biomechanics / kinematic sequence | [26_3d-biomechanics.md](26_3d-biomechanics.md) | L | 3D pose |
| C9 | Spin estimation (stretch; likely non-goal) | [27_spin-estimation.md](27_spin-estimation.md) | XL | — |
| C10 | Audio understanding (listen) | [28_audio-understanding.md](28_audio-understanding.md) | M | — |
| C11 | Service detection (table tennis) | [29_service-detection.md](29_service-detection.md) | M | pose + ball |
| C12 | Racket-angle proxy (table tennis) | [30_racket-angle.md](30_racket-angle.md) | M | pose + contact timing |
| C13 | Table contact-point heatmap (table tennis) | [31_table-heatmap.md](31_table-heatmap.md) | L | ball + table calibration |

**Go/no-go gate — C1:** accuracy must clear stated threshold on a labelled set,
else descope C1 and C6 and keep the heuristic with a "low confidence" label.

---

## 8. Phase D — Product, platform & growth

| # | Feature | File | Effort | Key dependency |
|---|---|---|---|---|
| D1 | iOS app | [32_ios-app.md](32_ios-app.md) | XL | — |
| D2 | Coach / team layer | [33_coach-team.md](33_coach-team.md) | XL | auth (0.8) |
| D3 | Personalized training plan + memory | [34_training-plans.md](34_training-plans.md) | L | report history + 0.3 |
| D4 | Share links & socials | [35_share-links.md](35_share-links.md) | M | — |
| D5 | Assessments / skill ratings | [36_skill-ratings.md](36_skill-ratings.md) | M | 0.2 calibration |
| D6 | Injury-risk / load flags | [37_injury-risk.md](37_injury-risk.md) | L | pose metrics |
| D7 | Audio coaching playback | [38_audio-coaching-playback.md](38_audio-coaching-playback.md) | M | voice-over (shipped) |
| D8 | Integrations & ecosystem | [39_integrations-ecosystem.md](39_integrations-ecosystem.md) | M–XL | varies |
| D9 | Coach comments + drill assignments | [40_coach-comments.md](40_coach-comments.md) | M | D2 |
| D10 | Gamification — challenges & leaderboards | [41_gamification.md](41_gamification.md) | M | accounts |
| D11 | Cross-device sync | [42_cross-device-sync.md](42_cross-device-sync.md) | M–L | D2 |
| D12 | Multi-session trend view | [43_multi-session-trends.md](43_multi-session-trends.md) | M | ≥3 sessions + 0.2 |
| D13 | Annotated coaching clips | [44_annotated-clips.md](44_annotated-clips.md) | M | trim/reel (shipped) |

**Go/no-go gate — D2:** pilot with ≥N coaches retained 4 weeks; else park.

---

## 9. Cross-cutting work

Apply these rules to every new feature:

- **Data model:** add optional blocks to the report without breaking the schema
  (`ball2`, `rallies[]`, `players[]`, `skills{}`, `plan`, `match`,
  `biomechanics{}`, `audio{}`). Keep `domain/report.normalize/validate`
  tolerant — unknown keys dropped, new keys optional.
- **Telemetry:** new model passes must show in Diagnostics — attribute to a
  step and count tokens.
- **Cost controls:** every extra LLM pass gated by a `core/config.py` toggle +
  `TOKEN_BUDGET`; thorough mode is always opt-in.
- **Testing:** unit tests for new `domain` schemas and `core/video` math; keep
  `test_architecture.py` green.
- **Accessibility:** captions for voice-over; short copy; responsive UI.
- **Privacy:** local-first stays the default; share is opt-in; never send more
  frames than needed.

---

## 10. Prioritization (recommended sequence)

| # | Feature | File | Effort | Impact |
|---|---|---|---|---|
| 0.1–0.8 | Foundations | 04–10 | M–L | High |
| M3 | Stroke / repetition segmentation | 14 | M | High |
| M5 | Extended footage check | 15 | S | Medium |
| M6 | Scene / rally detection | 15 | S | Medium |
| M7 | Handedness auto-detect | 16 | S | Low |
| M8 | Thorough sampling mode | 16 | S | Low |
| I1 | Person detection | 17 | M | Medium |
| I2 | Subject segmentation model | 17 | M | Medium |
| I4 | Monocular depth (MiDaS) | 18 | L | Low |
| I5 | OCR scoreboard | 18 | S | Low |
| B4 | Overlay compare (blend) | 11 | M | Medium |
| B5 | Pro / reference comparison | 12 | M | Medium |
| B6 | Multi-sport generalization | 13 | L | High |
| C1 | Ball: shot-type & pace | 19 | L | High |
| C2 | Whole-session segmentation | 20 | L | High |
| C3 | Real-time / live capture | 21 | XL | High |
| C4 | Multi-player attribution | 22 | L | Medium |
| C5 | Higher-fidelity inputs (thorough) | 23 | M | Medium |
| C6 | Line calls / scoring / match stats | 24 | L | High |
| C7 | Multi-camera / dual-angle | 25 | L | Medium |
| C8 | 3D biomechanics / kinematic sequence | 26 | L | High |
| C9 | Spin estimation (stretch; likely non-goal) | 27 | XL | Low |
| C10 | Audio understanding (listen) | 28 | M | High |
| C11 | Service detection | 29 | M | High |
| C12 | Racket-angle proxy (wrist/forearm) | 30 | M | Medium |
| C13 | Table contact heatmap | 31 | L | Medium |
| D1 | iOS app (Android shipped) | 32 | XL | High |
| D2 | Coach / team | 33 | XL | High (B2B) |
| D3 | Personalized plan + memory | 34 | L | High |
| D4 | Share links & socials | 35 | M | Medium |
| D5 | Assessments / skill ratings | 36 | M | Medium |
| D6 | Injury-risk / load | 37 | L | Medium |
| D7 | Real-time audio coaching (playback) | 38 | M | Medium |
| D8 | Integrations & ecosystem | 39 | M–XL | Medium |
| D9 | Coach comments + drill assignments | 40 | M | Medium |
| D10 | Gamification — challenges & leaderboards | 41 | M | Medium |
| D11 | Cross-device sync | 42 | M–L | Medium |
| D12 | Multi-session trend view | 43 | M | High |
| D13 | Annotated coaching clips | 44 | M | Medium |

**Build order:** 0.2 → 0.1 → 0.3 → M3 → M5/M6 → I1 → I2 → B4 → B5 →
C1 → C2 → C8 → C10 → C6 → C3 → D3 → D1/D2 → D4/D5/D6/D7/D8/D9/D10/D11 →
D12/D13. C11–C13 run alongside the analysis depth work. 0.4–0.8 and B6 run
in parallel throughout.

**Milestones:**
- **M-foundations:** 0.1–0.8.
- **M-measure:** M3, M5–M8 + I1–I2.
- **M-review:** B4–B6.
- **M-depth:** C1–C13.
- **M-platform:** D1–D13.

---

## 11. Metrics of success

- **Report usefulness** — % of sessions with 👍 on the focus issue. Target ≥ 70%.
- **Issue precision / recall** — vs the labelled benchmark (0.1); tracked per release.
- **Trust** — hallucination-flag rate must stay **0**; 100% of issues must cite evidence.
- **Adherence** — % of sessions where a drill was checked off and the athlete returned within 7 days.
- **Retention** — sessions per user per week; week-2 return rate.
- **Time-to-insight** — median analyze time, target ≲ 90s for a ~10s clip on a warm run.
- **Demo reliability** — % of demo runs that complete or fall back cleanly. Target **100%**.
- **Cost** — median tokens + $ per session, and cache-hit ratio.

---

## 12. Product strategy & validation

**Personas**
- **Primary:** the self-taught racket-sport amateur (plays 1–3×/week, no coach, films on a phone).
- **Secondary:** the club/intermediate player; the **coach** (a buyer for D2); the parent of a junior.

**Beachhead:** table tennis first, then tennis → badminton/squash/padel. Resist going broad before
one sport is great.

**Positioning:** *"the coach you can replay."* Automatic, evidence-grounded (every claim cites a
timestamp), private/local by default, and it writes a plan you can question — not just metrics.

**Moat vs table stakes**
- Moat: evidence-backed adaptive coaching; local/open pipeline; plan + memory (D3).
- Table stakes (competitors have): tracking, pose, charts, compare, reels.

**Business model (if productizing):** freemium (N sessions) → subscription; coach/team seats (D2);
self-host with bring-your-own-model (0.6).

**Go-to-market:** club partnerships, coach outreach, sport communities, shareable demos (D4).

**Validation plan:** interview ~5 coaches + ~10 amateurs. Two questions that matter: "is the report
useful?" (from 0.3 👍) and "would you pay?". Wire both to the metrics in §11.

---

## 13. Engineering foundations & risks

- **Schema versioning.** Add `schema_version` to the report; `domain/report.migrate()` for new
  blocks; reader tolerates missing keys. Migrate on read.
- **Prompt & model versioning.** Record prompt id/hash + model + provider per run. Keep a
  golden-report snapshot test (0.1).
- **Security.** Frame prompt-injection: treat on-screen text as data, not instructions; never let
  frame text trigger tools. Upload validation, rate limiting, auth before exposing (0.8).
- **Storage / scaling.** JSON-per-report + in-memory job manager won't scale: plan SQLite→Postgres,
  artifact retention policy, and a real worker pool (process pool or RQ/Celery).
- **Performance budgets.** Video first frame < 1s; chart render < 100ms; analyze ≲ 90s for ~10s
  clip (warm).
- **Test strategy.** Unit, architecture (`test_architecture.py`), API contract, gui2 end-to-end
  (Playwright), eval (0.1), load/latency.
- **Licenses & compliance.** Verify mediapipe, pose_landmarker, ball-detector model, share-card
  font, any dataset used for C1, and openjiuwen dependency terms.

---

## 14. Dependencies & go/no-go gates

**Key dependency edges**
- `0.1–0.8` → foundations for everything.
- `0.2` (calibration) → trustworthy compare/progress/D5.
- `B4` → builds on compare slider.
- `C2` → needs `C1`; `C6` → needs `C1` + court detection; `C3` → needs `C1` + `C2` + 3D pose.
- `C4` → needs I1.
- `D3` → needs report history + `0.3`; `D2`/`D9` → need auth (`0.8`).

**Go/no-go gates**
- **M-foundations:** eval harness green, calibration tolerance met, demo fallback 100%.
- **M-depth:** C1 accuracy clears threshold — else descope C1/C6.
- **M-platform:** D2 pilot retained 4 weeks — else park D2.

---

## 15. Non-goals / guardrails

- **Not medical.** D6 stays non-diagnostic and disclaimed.
- **No fabricated measurements.** Every finding cites evidence; `domain/evaluate.py` flags
  spin/speed/angle claims.
- **Local-first by default.** Anything leaving the machine is opt-in.
- **Don't break the layering.** New external engines land in `integrations/`; pure rules in `domain/`.
- **Don't bloat one run.** Every extra pass is a toggle; Diagnostics must show it.

---

*Per-feature detail (goal, where it lives, acceptance, risks) lives in the
numbered plan files 04–44. Write a full spec in the stub file before building.*
