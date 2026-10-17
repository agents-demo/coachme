# Analysis Pipeline Improvement Ideas
# Topspin Review — Coach-Driven Pipeline Research

*Research document: what a TT coach would want the pipeline to measure, assessed for
technical feasibility against the current implementation. Two-stage format: proposals
first, honest feasibility verdict second.*

---

## Current pipeline capabilities (baseline)

| Layer | What it measures today |
|---|---|
| **Movement** | Lateral range (lower/upper body), direction changes, crouch depth, footwork series |
| **Pose** | Knee/elbow angles (2D + 3D world coords), torso lean, shoulder-hip twist *mean* |
| **Strokes** | Wrist-speed peaks → timestamp, which hand, raw strength magnitude |
| **Ball** | 2D path, monocular 3D trajectory (size-cue depth), speed (normalised), hits, bounces |
| **LLM** | Two-stage: observations → signals → issues/strengths/drills, cross-checked against evidence frames |

The pipeline deliberately does **not** invent spin rates, exact angles, or ball speed in
real units — all claims must be backed by a frame timestamp.

---

## Tier A — high coaching value, zero new dependencies

These use only data already produced by the pipeline (`pose_3d`, `strokes`,
`footwork_series`, `activity`, `segments`). They are pure computation.

### A1. Recovery time per stroke
**What it is:** After every wrist-speed peak, measure how many seconds until the pose
landmarks return to a ready-position configuration (shoulder-width feet, elbows near hips,
knees bent to 140–160°).

**Why it matters:** Long recovery is the most actionable single metric for intermediate
players — they are still finishing the follow-through when the next ball arrives.

**How to implement:** `strokes[]` gives the stroke frame. Scan forward through `pose_3d[]`
until ankle separation, knee angle, and elbow-to-hip distance all meet threshold.
Zero external dependencies.

---

### A2. Footwork-to-stroke timing gap ("late feet")
**What it is:** Time delta between the last large lateral footwork event and the wrist-speed
peak. Negative delta means feet arrived *after* the arm started.

**Why it matters:** "Late feet" is the single most common coaching correction at
intermediate level — the player is arm-swinging without being positioned first.

**How to implement:** `footwork_series[]` gives lower-body lateral position per frame.
Find the last directional reversal in that series before each stroke event. Compute the
delta to the wrist-speed peak. Pure arithmetic on existing data.

---

### A3. Hip-shoulder rotation sequencing (kinetic chain check)
**What it is:** Per-frame timeline of hip-twist angle vs. shoulder-twist angle around each
stroke. If they peak simultaneously, the player is arm-hitting. Hips must rotate before
shoulders to generate power through the kinetic chain.

**Why it matters:** Explains *why* a player generates weak topspin even with good
footwork.

**How to implement:** `shoulder_hip_twist_mean` is already computed as a single summary.
Remove the `.mean()` aggregation and store the raw per-frame series. Two-line change to
the metrics stage.

---

### A4. Elbow position at contact relative to torso
**What it is:** Elbow X/Y/Z in the body frame (relative to mid-shoulder, mid-hip) at the
stroke frame. "Elbow flies out" = elbow X coordinate significantly outside the shoulder
width.

**Why it matters:** For forehand topspin, a flared elbow causes inconsistency and
eventually shoulder injury.

**How to implement:** 3D shoulder and elbow landmarks already exist in `pose_3d`. Body-
frame computation is a rotation and translation. Zero external dependencies.

---

### A5. Backswing depth and follow-through arc
**What it is:** Integrate the wrist-landmark path in the 0.3 s before and 0.3 s after
the wrist-speed peak to get backswing arc length and follow-through arc length and
direction.

**Why it matters:** Short backswing → weak stroke. Abbreviated follow-through → arm-stop,
no full kinetic chain.

**How to implement:** Wrist position in `pose_3d` exists per frame. Arc computation is
simple numerical integration. Zero external dependencies.

---

### A6. Ready position quality between shots
**What it is:** Between every pair of stroke events, measure what fraction of frames meet
ready-position criteria: ankle separation ≈ shoulder width, knee angle 140–160°, hands
near hip height.

**Why it matters:** A player who collapses to upright posture between shots cannot react
quickly to the next ball.

**How to implement:** All required landmarks are in `pose_3d`. Outputs a 0–100 %
ready-position score per session.

---

### A7. Technique drift / fatigue detection
**What it is:** Compare technical metrics from the first 30 % of the video to the last
30 %. Flag if knee flexion decreases, lateral range shrinks, or stroke strength drops.

**Why it matters:** Tells the coach whether conditioning is the limiting factor — the
player can execute correctly when fresh but not under fatigue.

**How to implement:** Partition existing metrics by time. No new data required.

---

### A8. Rally length distribution
**What it is:** Group consecutive ball-hit events into rally-length bins: 1 shot (serve
winner/error), 2–3 shots, 4–7 shots, 8+ shots. Output percentages.

**Why it matters:** Short-rally distribution → serve-and-attack style. Long-rally
distribution → consistency baseline player. Determines which coaching topics are
relevant.

**How to implement:** `ball.hits[]` already counts direction reversals. Grouping
consecutive events into rallies is signal processing on existing data.

---

### A9. Cross-session metric evolution
**What it is:** Track numeric metrics (`lower_lateral_range`, `r_elbow_mean`,
`stroke_strength`, etc.) across sessions to show whether technique is actually
changing — not just whether the same issues keep appearing.

**Why it matters:** The current trends feature tracks issue *text* recurrence. Tracking
*numbers* answers "is their footwork range actually growing?" after three weeks of drills.

**How to implement:** Small schema extension to the `GET /trends` endpoint. The numeric
values already exist in each session's `metrics` object.

---

### A10. Per-stroke drill parameterization
**What it is:** Change the drill schema from a string to a structured object:
`{drill, stroke_type, cue, reps, success_condition}`.

**Why it matters:** "Multi-ball forehand topspin drill" is less useful than "Multi-ball
forehand topspin, 30 reps, cue: brush 3-o'clock on the ball, success: elbow angle
variance < 15°."

**How to implement:** LLM prompt and output schema change only. No new computation.

---

## Tier B — achievable with one new component

### B1. Stroke type classification (heuristic)

**What it is:** Label each detected stroke event: forehand topspin, forehand drive,
forehand push, forehand flick, backhand topspin, backhand push, backhand block, smash,
serve.

**Why it matters:** Unlocks per-stroke-type coaching. Without this, every issue is
applied to "strokes in general." With it, the LLM can say "your backhand push is
technically sound but your forehand topspin elbow angle is inconsistent."

**Rule-based heuristic (no ML, no data):**

| Signal | Interpretation |
|---|---|
| Ball ascending before contact + player stationary | Serve |
| High wrist speed + ball trajectory gains height + elbow ≈120° | Forehand topspin |
| High wrist speed + steep downward ball exit | Smash |
| Low wrist speed + flat/descending ball + short follow-through | Push or block |
| High wrist speed + backhand side + ball rises | Backhand topspin |

Expected accuracy: 65–75 % for clean single-player footage.

**ML classifier (with labelled data):** Public dataset TTNet (ECCV 2020) contains
stroke labels and can be adapted. Expected accuracy: 88–93 %. Engineering effort: weeks.

**Prerequisite:** None for heuristic. Labelled dataset adaptation for ML version.

---

### B2. Table detection and real-world calibration

**What it is:** Detect the table rectangle in the frame (green or blue, known aspect
ratio 274 × 152.5 cm) and compute a homography from pixel coordinates to real-world
centimetres.

**Why it matters:** Five other features depend on this one component:
- Ball speed in km/h
- Bounce point heatmap
- Serve classification (short vs. long)
- Distance from table
- Spin direction from trajectory curvature vs. gravity

**How to implement:** OpenCV hue-range filtering + contour detection + 4-corner
homography. Already using OpenCV in the pipeline. Works reliably when the table is
fully visible (typical tripod-behind-endline setup). Degrades gracefully when the near
edge is cut off.

**Prerequisite:** OpenCV already present.

---

### B3. Ball speed in km/h
**Depends on:** Table detection (B2)

Once real-world coordinates are known, ball speed in km/h is trivial. A forehand loop
typically clocks 60–90 km/h; a smash 90–130 km/h. Players find this number motivating
and memorable.

---

### B4. Bounce point heatmap on the table
**Depends on:** Table detection (B2)

Project ball trajectory through the homography to find where the ball lands on the
table surface. Build a 2D density map. Consistent placement (always cross-court middle)
reveals tactical predictability.

---

### B5. Serve detection and classification
**Depends on:** Table detection (B2) + stroke classifier (B1 heuristic)

A serve has a unique signature: vertical ball upward motion (toss) before contact,
player stationary, ball contact at body height or above. Short serve: ball bounces
twice on table (detectable from bounce-point projection). Fast-long: ball exits table
at high speed without second bounce.

---

### B6. Distance from table estimation
**Depends on:** Table detection (B2)

Player foot landmark projected through the homography gives distance behind the table
end-line. Playing 1.5 m vs. 3 m from the table requires completely different tactical
coaching.

---

### B7. Audio contact classification
**What it is:** Extract audio at each detected stroke timestamp (±50 ms). Analyse
envelope shape and frequency content. A forehand topspin crack is 2–5 kHz, short
duration. A push is softer and lower. A flat smash is a broad thud.

**Why it matters:** Adds an independent evidence channel for spin type detection that
does not depend on high frame rate.

**Prerequisite:** Clean audio track. Works when the phone is within 2–3 m of the table.
Unreliable with background noise or pre-compressed video.

**How to implement:** `ffmpeg` audio extraction (already used) + short-time Fourier
transform (scipy or librosa) at each stroke timestamp. No new models.

---

### B8. MediaPipe Hands for racket orientation proxy
**What it is:** Run MediaPipe Hands (21 hand landmarks) at each stroke frame. The palm
normal vector constrains racket face angle far better than the forearm vector alone.
The wrist pronation/supination state (visible from hand landmark geometry) is the key
indicator of closed vs. open racket face.

**Why it matters:** Racket angle is the primary determinant of spin type on each stroke.
It is currently unmeasurable from body pose alone.

**Prerequisite:** MediaPipe Hands model (exists in MediaPipe library already used, runs
on mobile). Additional per-frame computation cost at stroke frames only.

---

## Tier C — significant engineering, worth planning

### C1. Stroke consistency score
**Prerequisite:** Stroke type classification (B1)

Once multiple instances of "forehand topspin" are labelled in a session, compute the
standard deviation of elbow angle, knee flexion, and wrist arc at those frames.
Normalised SD → consistency score 0–100 per stroke type. "Your forehand topspin elbow
angle varies ±18° across 7 attempts" is highly actionable drill feedback.

---

### C2. Opponent-side analysis (match footage)
MediaPipe can detect multiple bodies. When a second player is visible at the far end
of the table, run a symmetric analysis. This enables: which zones of the opponent's
court the player is targeting, and what tactical pattern is being executed in context.

**Main challenge:** Reliably distinguishing player vs. opponent when they move and
partially overlap. Requires tracking-by-assignment logic across frames.

---

### C3. Multi-session metric embedding for similar-session retrieval
Store each session as a vector of its key numeric metrics. When a new session is
analysed, surface the 2–3 most similar past sessions and highlight what changed
(better, worse, same). Creates a true longitudinal coaching narrative.

---

## What is genuinely not achievable with a single standard camera

### Ball spin rate (quantitative)
TT spin is 50–150 rev/s. At 30 fps the ball rotates 1.7–5 full turns per frame. The
Magnus force deflects the ball 2–5 mm per frame — within the noise floor of pixel-level
ball detection (position uncertainty ≈ 3–6 mm at typical shooting distances).

**Minimum requirement for reliable spin rate:** 120 fps (some modern phones). Ideal:
240 fps. At those rates, the pipeline's current coarse frame-sampling architecture
would need a targeted redesign for the stroke window.

**Partial workaround available now:** Qualitative spin type (topspin / backspin / flat)
from the shape of the 2D trajectory relative to expected gravity parabola. Topspin
curves down faster than gravity; backspin floats. The sign is detectable at 30 fps
even when the magnitude is not.

---

### True racket face angle
MediaPipe Pose's 33 landmarks include no racket points. The forearm vector
(wrist → elbow) is a rough proxy but misses wrist pronation/supination — a 40°
range that determines open vs. closed face. The MediaPipe Hands approach (B8)
improves the estimate but still does not give the exact racket face angle.

**Only fully reliable solutions:** Racket-mounted IMU (commercial products exist,
e.g. Butterfly Flarestorm sensor, Zepp TT), or a colour/AprilTag marker on the
blade visible to the camera.

---

## Implementation priority order

Based on coaching impact per engineering hour:

| Priority | Feature | Effort | Unlocks |
|---|---|---|---|
| 1 | Table detection + homography (B2) | ~1 week | B3, B4, B5, B6, spin direction |
| 2 | Recovery time per stroke (A1) | ~2 days | Standalone metric |
| 3 | Late feet detection (A2) | ~1 day | Standalone metric |
| 4 | Hip-shoulder sequencing per frame (A3) | ~1 day | Standalone metric |
| 5 | Stroke type heuristic classifier (B1) | ~1 week | C1, drill parameterization |
| 6 | Rally length distribution (A8) | ~1 day | Better LLM tactical context |
| 7 | Cross-session metric evolution (A9) | ~2 days | Longitudinal coaching |
| 8 | Backswing / follow-through arc (A5) | ~1 day | Standalone metric |
| 9 | Elbow position at contact (A4) | ~1 day | Standalone metric |
| 10 | Audio contact classification (B7) | ~1 week | Independent spin evidence |
| 11 | Stroke consistency score (C1) | after B1 | Drill quality feedback |
| 12 | MediaPipe Hands racket proxy (B8) | ~2 weeks | Better spin evidence |

Items 2–4 and 6, 8, 9 can be implemented in any order, independently, with no external
dependencies. Table detection (item 1) is the single component with the highest
leverage-to-effort ratio.

---

*Document based on: coach-driven pipeline review session, October 2025.*
*Cross-referenced against: `pipeline/Stages.kt`, `pipeline/Metrics.kt`,
`pipeline/Pose.kt`, `pipeline/Ball.kt`, `surfaces/gui2/server/routes/trends.py`.*
