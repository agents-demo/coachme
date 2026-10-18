# Analysis Pipeline Improvement Ideas
# Topspin Review — Coach-Driven Pipeline Research

*Research document: what a table-tennis coach would want the pipeline to measure, assessed
against the current implementation. Revised for technical accuracy: each proposal states its
data prerequisites, platform scope, acceptance criteria and failure modes.*

---

## 0. Current baseline

| Layer | What the pipeline produces today |
|---|---|
| **Movement** | Lateral range (lower/upper), direction changes, crouch depth, `footwork_series` |
| **Pose** | Per-sampled-frame landmarks (2D + world 3D); knee/elbow angles; torso lean; per-frame shoulder/hip twist (Python); summaries |
| **Strokes** | Wrist-speed peaks → timestamp, hand, relative strength (no stroke type) |
| **Ball** | 2D path, approximate monocular 3D trajectory, relative speed, hit/bounce timestamps, rally segments |
| **LLM** | Coarse/fine vision passes → observations → issues/strengths/drills, evidence-checked |
| **Progress** | Pairwise compare + multi-session trends (issues, a few metrics, drill total) |

Deliberate constraints: no invented spin rate, no real-unit speed, no exact angles. Every claim
must cite a frame/time.

## 1. Prerequisites that gate most “cheap” features

These are not features; they are the conditions that make the Tier A numbers trustworthy.

1. **Sampling density around strokes.** The default budget is ~12 sampled frames for a whole
   clip. Recovery (A1), late feet (A2), arcs (A5) and sequencing (A3) need pose at **10–20 fps
   inside a ±0.5 s stroke window**, not 12 frames across 50 s. Reuse `sample_burst` and run pose
   on that window; cache it with the checkpoint. Without this, Tier A is noise.
2. **Single-player assumption.** PoseLandmarker is currently used for one pose per frame. In
   two-player footage it may lock onto the opponent. Multi-player clips must be excluded from
   per-stroke metrics until C2 (or the user must crop to one player).
3. **Calibration for cross-session claims.** Body-relative metrics already help; real distances,
   speeds and table positions need an explicit calibration (table corners or floor plane).
   A9/C3 must not compare absolute numbers across clips without it.
4. **Platform parity.** The Python pipeline and the Android on-device pipeline diverge: Python
   stores per-frame twists; Android stores world landmarks per frame and would compute twists
   on-device. Every item below states whether it is **server**, **Android**, or **both**.

### Sampling plan for stroke features

- Detect candidate strokes at the current sample rate.
- For each stroke, re-sample the source at **15–20 fps for [t−0.6 s, t+0.6 s]** (pose + ball).
- Store a `stroke_windows[]` block in the report: landmarks, ball points, relative times.
- Cap total extra frames (e.g., 3 strokes × 24 frames) to bound cost.

---

## 2. Tier A — existing data + dense stroke windows (no new CV model)

| # | Feature | Value | Prerequisite | Platform | Effort |
|---|---|---|---|---|---|
| A1 | Recovery time per stroke | High | dense stroke window | both | S |
| A2 | Footwork-to-stroke timing (“late feet”) | Highest | dense footwork + stroke times | both | S |
| A3 | Hip→shoulder sequencing | High | per-frame twist (Python has it) | both | S |
| A4 | Elbow position at contact (body frame) | Medium | 3D landmarks at stroke | both | S |
| A5 | Backswing / follow-through arc | Medium | dense window at 15–20 fps | both | S–M |
| A6 | Ready-position quality between shots | High | dense pose, thresholds | both | S |
| A7 | Technique drift / fatigue | Medium | ≥6 strokes, long clip | both | S |
| A8 | Rally length distribution | Medium | reliable ball hits/bounces | server | S |
| A9 | Numeric cross-session evolution | High | calibrated metrics | both | S–M |
| A10 | Structured drills | High | schema + prompt change | both | M |

### A1. Recovery time per stroke
**What:** seconds from each wrist-speed peak until the player returns to a ready configuration
(ankle separation near shoulder width, knee ≈ a player-specific baseline, hands near hip height).

**Why:** the most actionable intermediate-player metric — they are still finishing the
follow-through when the next ball arrives.

**Method:** scan the dense stroke window forward until the ready criteria hold for 2 consecutive
frames. Report median and range; omit strokes with no recovery inside the window.

**Acceptance:** median recovery + count recovered/total; manual spot-check on 10 strokes.
**Risks:** thresholds are individual; store a configurable baseline, not hard-coded 140–160°.

### A2. Late-feet timing gap
**What:** time between the last large lateral footwork reversal before a stroke and the
wrist-speed peak. Negative = feet arrived after the arm started.

**Why:** “late feet” is the most common correction at intermediate level.

**Method:** find the last direction reversal in the dense `footwork_series` before the stroke;
delta = stroke_t − reversal_t. Report per stroke and session median.

**Acceptance:** flags late feet only when |delta| exceeds a stated threshold; degrades to
“unknown” with sparse footwork data. **Risks:** footwork proxy is lower-body centroid, not feet.

### A3. Hip→shoulder sequencing
**What:** per-stroke relative timing of hip and shoulder twist peaks; hips should lead.

**Method (server):** the Python pose entries already include per-frame `hip_twist` and
`shoulder_twist`; use them directly on the dense window. **Android:** compute the same angles
from stored world landmarks. Report lead/lag in seconds and a confidence label.

**Acceptance:** hip-leads / simultaneous / shoulder-leads classification with evidence frames.
**Risks:** twist angles are noisy at monocular depth; require the side view.

### A4. Elbow position at contact
**What:** elbow coordinates in a body frame (mid-shoulder/mid-hip origin) at the stroke frame.

**Why:** a flared elbow is a common forehand inconsistency and injury risk.

**Method:** rotate/translate existing 3D landmarks; compare elbow X against shoulder width.
**Acceptance:** flags only when outside a stated margin, with the frame shown.
**Risks:** world-landmark drift; do not present as clinical measurement.

### A5. Backswing and follow-through arcs
**What:** wrist path length/direction in the 0.3 s before and after the stroke.

**Why:** short backswing → weak stroke; abbreviated follow-through → arm-stop.

**Method:** numeric integration over dense wrist landmarks. A 12-frame session sample is too
coarse; this requires the stroke-window sampling above.
**Acceptance:** arc length + direction per stroke; omit if <3 frames in a window.
**Risks:** wrist-speed peak is a proxy for contact, not the true contact instant.

### A6. Ready-position quality
**What:** fraction of inter-stroke frames meeting ready criteria (stance width, knee flex,
hands near hips).

**Method:** dense pose between strokes; player-specific thresholds; output 0–100 % plus the
worst moments as evidence.
**Acceptance:** score moves in the expected direction on a before/after clip.
**Risks:** criteria differ by sport and level; expose thresholds in settings or learn a baseline.

### A7. Technique drift / fatigue
**What:** compare first vs last 30 % of strokes (knee flex, lateral range, stroke strength).

**Why:** distinguishes skill from conditioning.
**Method:** only for clips with enough strokes (≥6); use stroke medians, not raw frames.
**Acceptance:** flags drift only when the effect exceeds a stated minimum; otherwise “no clear drift”.
**Risks:** short highlight clips are not fatigue tests; label as a hint.

### A8. Rally length distribution
**What:** group consecutive ball contacts into 1, 2–3, 4–7, 8+ shot bins and report percentages.

**Why:** short rallies imply serve-and-attack; long rallies imply consistency.
**Method:** use existing `ball.hits[]`/`bounces[]` timestamps and rally segments. Exclude
segments with implausible contact spacing.
**Acceptance:** distribution shown with the number of rallies used; low-confidence tag when hit
detection is weak. **Risks:** miss-detected hits change the distribution; no point-end detection.

### A9. Numeric cross-session evolution
**What:** trend lines for `lower_lateral_range`, elbow angle mean, direction changes, stroke
strength, etc. — not just repeated issue text.

**Method:** extend the existing `/trends` endpoint and Android trend view. Store metric points per
session. Current endpoint already aggregates a few metrics; add the stroke-level ones once they exist.
**Acceptance:** ≥3 sessions, per-series sample count, and an “uncalibrated” warning when the
clips differ in distance/angle.
**Risks:** comparing absolute numbers across cameras is invalid without calibration.

### A10. Structured drills
**What:** drill becomes `{drill, stroke_type, cue, reps, success_condition}` instead of a string.

**Method:** prompt/schema change + report migration; keep plain strings for old reports.
**Acceptance:** new reports render structured drills; old reports still load.
**Risks:** the model can invent reps/success conditions — mark them as suggested, not measured.

---

## 3. Tier B — one new component each

### B1. Stroke-type classification (heuristic, then ML)
**Goal:** forehand/backhand topspin, drive, push, block, flick, smash, serve.

**Honest starting point:** a rule-based classifier over **relative** signals (hand, wrist speed,
ball height/exit direction, contact side) can reach ~60–70 % on clean single-player clips — not
the 65–75 % claimed before validation. Serve classification is unreliable without B2 (table/toss).

**Path:**
1. Build a small labeled set from your own clips (export timestamps + stroke type).
2. Heuristic rules + confidence; never present low-confidence labels as fact.
3. Only then consider an ML model (e.g., TTNet-style) with a separate training effort.

**Acceptance:** per-class precision on the labeled set; abstain when uncertain.

### B2. Table detection + homography (high leverage, high uncertainty)
**Goal:** map table-plane pixels to real-world table coordinates.

**Correction:** OpenCV is **not** currently a dependency. Adding it is fine server-side
(`opencv-python-headless`), but Android would need a port or a manual-corner fallback.

**Approach:** detect the table quad (colour + contour) or let the user tap the 4 corners once
per session. Compute a homography to the 2.74 × 1.525 m table plane.

**Reality check:** colour detection fails on non-green/blue tables, glare, occlusion and when the
near edge is cropped. Manual 4-corner calibration is the reliable fallback and should ship first.

**Acceptance:** if detection confidence is low, ask for corners; if calibration fails, disable all
downstream table metrics. **This is a spike with a no-go gate, not a guaranteed win.**

### B3. Ball speed (corrected)
**What was wrong:** a table-plane homography alone cannot give ball speed in km/h; it maps only
points **on the table plane**, while the ball travels above it.

**Feasible options:**
1. **Ball-size scale:** the known 40 mm ball gives a monocular size cue per frame (current
   trajectory already uses blob area). Gives approximate 3D, so approximate speed — label it
   “estimated”.
2. **Calibrated camera + table model:** camera height/angle + homography; project the trajectory
   and fit a ballistic model. Better, but needs intrinsics and a stable camera.
3. **High-frame-rate capture** during the stroke window for less motion blur and better tracking.

**Acceptance:** only show speed with a stated error band; otherwise keep “relative speed”.
**Risks:** monocular depth and 30 fps blur; do not market as radar-grade.

### B4. Bounce-point heatmap
**What:** project the ball’s table-plane intersection through B2; build a density map.

**Why:** reveals cross-court bias, short/long patterns.
**Acceptance:** only when calibrated; overlay the table diagram with a sample count.
**Risks:** bounce detection errors; near/far amplification.

### B5. Serve detection / classification
**What:** flag serves (toss, no prior contact, player at own end) and classify short vs long.

**Dependencies:** B2 + B1; without the table, “short/long” and second-bounce logic are guesses.
**Acceptance:** serve flag with confidence; short/long only when the bounce projection is valid.
**Risks:** toss often outside the frame; false positives on feeds.

### B6. Distance from the table (corrected)
**What was wrong:** projecting a foot landmark through the **table** homography is invalid — feet
are on the floor plane, not the table plane.

**Feasible:** a **floor-plane** homography (calibrate with floor points/table base) or scale from
the player’s known height + pose. Report a range, not a precise centimetre value.
**Acceptance:** distinguishes near/mid/far with an error band; hidden when uncalibrated.

### B7. Audio contact classification (experimental)
**What:** classify contact sounds (crisp topspin vs soft push vs smash) at stroke times.

**Reality:** phone mic distance, compression, crowd noise and rubber/blade differences make this
unreliable. Requires a new audio dependency (scipy/librosa) and a labeled set.
**Acceptance:** ship only as an optional, confidence-labelled evidence channel. Do not gate other
metrics on it. **Risks:** high false-positive rate.

### B8. MediaPipe Hands for a racket-face proxy
**What:** hand landmarks at stroke frames constrain palm orientation better than the forearm.

**Reality:** it is still a **proxy** — grip and wrist pronation/supination are not fully observable.
**Acceptance:** show “estimated face tendency (open/closed)” with confidence, never an exact angle.
**Risks:** extra per-stroke compute; hands often small/motion-blurred at 30 fps.

---

## 4. Tier C — larger engineering

### C1. Stroke consistency score
Requires B1 labels. Compute per-type standard deviation of elbow angle, knee flexion and wrist
arc across attempts; output 0–100 with the attempt count. **Risk:** small samples (2–3 strokes)
must be labelled low-confidence.

### C2. Opponent-side analysis
MediaPipe PoseLandmarker can return multiple poses, but the current code takes one. This needs
**multi-pose detection + identity tracking** (near/far by size/position), handling overlap and
swaps. It is a separate tracking project, not a flag flip. Only then can you report targeting or
opponent zones.

### C3. Similar-session retrieval
Embed each session’s key metrics, retrieve nearest past sessions, and explain deltas. Needs
calibration-aware distance (A9) and a stable metric schema. Postpone until A9 is trusted.

---

## 5. Hard limits with a single standard camera

- **Quantitative spin rate:** at 30 fps a TT ball rotates ~1.7–5 turns/frame; Magnus deflection is
  within ball-detection noise. Qualitative **spin type** may be inferable from trajectory shape
  (topspin dips faster than gravity, backspin floats), but treat it as low-confidence and not
  “measured spin”.
- **True racket face angle:** pose has no racket; forearm/hand proxies miss grip and wrist
  pronation. Reliable options are a racket IMU or a visible marker on the blade.

---

## 6. Priority (revised)

| Priority | Item | Effort | Why now |
|---|---|---|---|
| 1 | Stroke-window sampling + dense pose (prerequisite) | S–M | Makes A1/A2/A3/A5 real |
| 2 | A2 late feet | S | Highest coaching value per hour |
| 3 | A3 hip→shoulder sequencing | S | Existing per-frame twists |
| 4 | A1 recovery time | S | High impact, same window |
| 5 | A5 backswing/follow-through | S–M | Uses the same dense window |
| 6 | A9 numeric trends | S–M | Extend the existing trends endpoint |
| 7 | A6 ready-position score | S | Same data; configurable thresholds |
| 8 | A8 rally distribution | S | Existing ball timestamps; caveat |
| 9 | A10 structured drills | M | Prompt/schema only |
| 10 | B1 stroke-type heuristic | M | Needs labeled validation, not just rules |
| 11 | B2 table/calibration **spike** | M | Go/no-go before B3/B4/B6 |
| 12 | B4 bounce heatmap | M | Only after B2 passes |
| 13 | B3 estimated ball speed | M | Needs calibration/size scale |
| 14 | B6 floor distance | M | Needs floor plane, not table plane |
| 15 | B5 serve classification | M | Depends on B1+B2 |
| 16 | B7 audio | M | Experimental; optional |
| 17 | B8 hand/racket proxy | M–L | Proxy only |
| 18 | C1 consistency | M | After B1 |
| 19 | C2 opponent tracking | L | Separate tracking project |
| 20 | C3 retrieval | M | After A9 calibration |

**Do not start B2 as a “guaranteed” feature.** Time-box it; if table detection is unreliable on
your test set, ship manual corner calibration instead and still get B4.

## 7. Definition of done

- Every new metric has: unit, sample count, confidence, evidence frame/time, and a fallback.
- Any per-stroke metric requires the dense stroke window; without it, return “insufficient data”.
- Cross-session claims require calibration or an explicit “uncalibrated” warning.
- New report blocks are optional and backward-compatible (`domain/report` tolerance).
- Android and gui2 both display or both hide an item; no server-only metric silently missing on phone.

## 8. Platform notes

| Capability | Python/server | Android |
|---|---|---|
| Dense stroke windows | `sample_burst` + pose | same via Sampler/Pipeline |
| Per-frame hip/shoulder twist | already in pose entries | compute from world landmarks |
| Table homography | OpenCV optional | needs native CV or manual corners |
| Audio analysis | ffmpeg + scipy/librosa (new) | native audio + FFT (new) |
| Multi-pose tracking | PoseLandmarker `num_poses` + tracker | same, currently first-only |
| Trends | `/trends` | local aggregation |

---

*Revised: technical corrections for plane geometry, dependencies and sampling; platform scope and
acceptance criteria added. Original coach-driven review: October 2025.*
