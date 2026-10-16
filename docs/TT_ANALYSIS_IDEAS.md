# Table Tennis — Analysis Gaps & Feature Ideas

*Findings from a design review session. Covers two angles: (1) product-level features
missing from the coaching loop, (2) table-tennis-specific CV/AI signals not yet measured.*

---

## 1. Product features — closing the coaching loop

The app already does the hard part: vision-based CV + LLM coaching from a single clip.
What is missing is the **feedback loop** — knowing whether the coaching is working over time.

### 1.1 Progress tracking across sessions
Every session is currently isolated. A "trend" view aggregating data across sessions would
show whether coaching is landing.

**Signals already stored per session, just not aggregated:**
- Issue recurrence rate (same issue appearing across multiple sessions)
- Drill completion rate
- Key metrics over time: elbow angle mean, lateral range, direction-change count

**Implementation path:** purely data-aggregation over existing `Report` objects;
no new CV required. A `GET /sessions/trends` endpoint + a chart in the Compare tab.

### 1.2 Drill completion persistence
Drill checkboxes reset on every visit. Persisting them (server-side keyed by stem, or
`localStorage`) and linking completed drills back to the next session's analysis
("Last time you worked on X — here is how it showed up today") closes the practice loop.

### 1.3 Video annotation export
The app timestamps issues but does not burn them into the clip. Generating a trimmed
clip with overlaid text (e.g. `"right elbow too high — 0:04"`) as a shareable coaching
note would be high value. The clip-trimming infrastructure (highlight reel export) is
already in the codebase; it needs a text-overlay pass added.

---

## 2. Table-tennis-specific measurements

The current pipeline measures **general** movement, pose angles, and ball tracking.
What follows are signals that are specific to table tennis and not yet measured.

### 2.1 Stroke classification *(high value, low CV cost)*
The pipeline already detects "fast-hand events" and labels them by hand (left/right) and
timestamp. The next step is labelling **stroke type**:

| Stroke | Key signals |
|--------|------------|
| Forehand topspin | right-hand fast event, elbow extends forward, ball rises then dips steeply |
| Backhand push | left-of-body contact, flat or slightly open racket angle, ball floats |
| Block | short arm movement, contact close to body, ball kicked back quickly |
| Serve | ball toss above table, no prior ball contact, player at own end |

A temporal window ±0.5 s around each stroke event — using the existing pose landmarks
plus ball trajectory direction — is likely enough for an LLM classifier without new CV
models. Start with a prompt-based approach over the existing JSON metrics.

### 2.2 Racket angle at contact *(highest coaching value)*
**The most important technical variable in table tennis.**
- Tilt forward (closed) → topspin
- Vertical → flat drive
- Tilt back (open) → backspin / lift

Derivation: wrist–forearm angle relative to ball travel direction at the moment of contact.
The existing pose landmarks give wrist and elbow positions; the ball trajectory gives
contact direction. A geometric computation on the stroke frames would produce a "racket
angle at contact" value in degrees.

Coaching output example: *"Your backhand contact angle is 55° (open). For a loop, aim
for 70–80°. Cue: brush up the back of the ball, not through it."*

This requires the most new CV work of the ideas listed here but would differentiate the
app most clearly from general sports-analysis tools.

### 2.3 Ball spin estimation *(medium cost, detectable indirectly)*
Spin type is detectable from **post-bounce trajectory curvature** without a high-speed
camera:
- **Topspin:** ball dips sharply before the bounce, kicks forward and accelerates
- **Backspin:** ball floats, loses speed, skids or stops after bounce
- **Sidespin:** ball curves laterally in flight

The existing 3D ball trajectory data could feed a physics fit (simple quadratic or
parabola fitting) to estimate spin type — not magnitude, but topspin / backspin / none.
This is a pure analytics step over already-collected data.

### 2.4 Table contact point heatmap *(tactically useful)*
Where on the table the ball lands determines pattern and tactics. With an angled or
top-down view the landing zone is estimable from the ball's 3D trajectory at bounce time.

Output: a top-down table diagram with a heatmap of landing zones across the session —
immediately reveals cross-court bias, middle-heavy patterns, or short-long imbalances.

This is geometry over the existing `trajectory3d` data. It requires a coordinate
transformation to map the camera frame onto the table frame (a one-time homography
calibration step if the table corners are visible).

### 2.5 Service detection *(prerequisite for service analysis)*
Serves are the most complex technical element and completely absent from current analysis.

Detection heuristic:
1. Player is at own end of table (pose centroid in lower half of frame)
2. Ball is tossed above table height from an open palm (no prior contact)
3. No prior rally ball contact in the last 3 seconds

Separating serve strokes from rally strokes allows the coaching prompt to treat them
differently: serve variety, serve placement, and serve spin are distinct coaching topics
from rally technique.

---

## 3. Priority ranking

| # | Item | Coaching value | CV effort | Recommended next |
|---|------|---------------|-----------|-----------------|
| 1 | Progress tracking across sessions | High | None (data already there) | Yes |
| 2 | Stroke classification | High | Low (prompt-based over existing data) | Yes |
| 3 | Drill completion persistence | Medium | None | Yes |
| 4 | Ball spin estimation | Medium | Low (analytics over trajectory3d) | Yes |
| 5 | Table contact point heatmap | High | Medium (homography calibration) | Deferred |
| 6 | Service detection | High | Medium (heuristic on pose + ball) | Deferred |
| 7 | Racket angle at contact | Highest | High (new CV geometry) | Deferred |
| 8 | Video annotation export | Medium | Low (existing infra, add text overlay) | Yes |
