# TopSpin Review — Pitch for Huawei Internal Stakeholders

> **One-sentence pitch:** Film a practice session. The app watches it like a coach and tells you exactly what to fix — specific to your technique, at the exact moment it went wrong.

---

## The Problem

A good table tennis coach charges $60–120 per hour.
Most recreational players practice 4–5 times a week — largely alone, with zero expert feedback.
They repeat the same mistakes for years without ever knowing it.

This is not a niche problem. Table tennis alone has approximately 300 million recreational players (ITTF estimate); across table tennis, tennis, badminton, padel and squash, the combined participant base exceeds 500 million. Most train regularly with little or no expert feedback between sessions.

**China is the primary market.** Approximately 85 million people play at a club level daily in China; around 10 million compete seriously. The 双减 policy (2021) banned for-profit academic tutoring and redirected ¥400B+ of parental spending toward sport — a structural, policy-driven demand shift that directly benefits table tennis coaching. For junior players, the buyer is the parent, not the child. English-speaking markets are the second priority.

---

## What This Is

A player records a practice session. The app watches it — frame by frame, measuring body mechanics, footwork and ball behaviour. Then it writes a coaching report: every finding tied to an exact timestamp, every claim grounded in a measured value the player can verify by rewinding the video. Specific drills, matched to what went wrong. Progress compared to the last session.

The report reads like what a good coach says after watching a session: "Your elbow dropped below your wrist at second 1.5, 3.1 and 7.0 — that is why your stroke arc is flat and the ball stays low." Findings from this video, this session. Not general technique principles.

The app is deliberately **backend-agnostic** — the coaching logic does not depend on any specific AI provider or compute hardware. Ascend and the openJiuwen/Ascend integration are the Huawei scale path: a working app with real recurring users creates the kind of batch inference and training demand that Ascend is built to serve.

---

## Why This Is Different — And Why It Matters

**What exists today**

A good coach watches a player and investigates. They notice something unexpected — a head tilt, a grip change, a timing shift — and they follow that thread. They form a hypothesis, look for evidence, connect cause to effect. The insight comes from the investigation, not from a list. The problem: most players have that coach for sixty minutes a week, if they are lucky. Everything that happens in the other four sessions goes unseen.

Every app that has tried to close this gap runs a fixed pipeline. Measure elbow angle. Check knee bend. Track footwork range. The same checklist, every session, for every player. Measurements come out. This is useful — and fundamentally limited. A fixed pipeline finds only what it was programmed to look for. It cannot notice something unexpected. It cannot change what it examines based on what it sees. It cannot investigate.

**What this app does instead**

The analysis in this app is not directed by a fixed pipeline. It is directed by a model.

The model watches the clip and decides what to examine — choosing which moments matter, which signals to follow, which to ignore. If it notices something unexpected, it investigates. The investigation is not predetermined. It responds to the video in front of it. Every finding it produces is anchored to measured evidence — a tracked position, a counted occurrence, a measured angle, an exact timestamp. The player can rewind to the moment and verify it themselves. But what led the model there was an investigation, not a script.

That is the differentiator: **evidence-backed adaptive coaching.**

**What that looks like**

In one clip — no instructions, no checklist — the model noticed that in 6 of 8 strokes, the player's head tilted down 0.3 seconds before contact. It cross-referenced this against ball quality: all 6 strokes with the head dip produced flat trajectories; the 2 without it produced measurably more topspin. It traced the pattern to the moment of brush contact — the player was losing sight of the ball at the critical instant.

The coach had not spotted it. Not after weeks of sessions with this player.

Nobody programmed "check head position." The model found the pattern itself, in the first clip, because the investigation led it there.

Four more moments like this: [03-the-moments.md](03-the-moments.md).

---

## Multi-modal throughout

| What | Modality |
|------|----------|
| Video input | Vision |
| Pose detection (MediaPipe) | Vision → structured landmarks |
| Ball tracking | Vision → trajectory data |
| LLM coaching report | Text generation grounded in vision data |
| **Roadmap:** Voice coaching | Audio output |
| **Roadmap:** Real-time overlay | Vision + AR |

Three modalities today. The roadmap adds two more. Every modality is a real GPU/NPU workload.

---

## A Recurring Workload for Huawei Ascend

Every time a user analyzes a video:
- pose inference runs across the clip;
- ball detection runs per frame;
- the vision model reads sampled frames;
- the LLM reasons over structured metrics and frames.

This is a batch video-inference workload, not a one-off chat request. Pose, ball and vision batches can run on **Ascend 310/310P inference** hardware; models can be trained on **Ascend 910-class** systems through **CANN** and **MindSpore**. Private or regional cloud deployment is a natural fit; on-device inference is a separate optimisation, not the Ascend story.

A committed player analyses every practice session — potentially five times a week. This is not a user who sends one text message. This is a user who creates meaningful, recurring compute demand every time they train.

The app does not need Ascend to be useful. The win-win: a useful app, adopted repeatedly, creates exactly the kind of recurring inference and training demand that Ascend is built to serve.

---

## The Demo

### What it does today
- Upload any video → structured coaching report in 30–90 seconds
- Report includes: summary, specific observations with timestamps, recommended drills, detected metrics (knee angle, elbow angle, footwork range, rotation values)
- Web app (SvelteKit) + Android app both functional
- Session history and progress tracking

### Where the product stands today
Working prototype, not yet a commercial launch. The stage is deliberate:

- **One sport validated** — table tennis mechanics are proven; tennis, badminton and padel are the expansion path once the core is hardened
- **Investigator mode opt-in** — the benchmark is in progress; Standard is the reliable default today
- **Accounts and cloud sync in Phase 2** — session history is device-local for now
- **First paying users in Phase 2** — Phase 1 makes the demo compelling enough to acquire them

These are sequenced development stages. Phase 1 is short precisely because the foundation is already working.

### The demo
A real training clip (Michael Osher, club session, professional table) analyzed to produce:
- 5 specific coaching findings, each grounded in what the AI measured, each citing exact timestamps
- Measured readings: shoulder rotation 14°, hip rotation 9° (both far below optimal), footwork coverage 5% of frame (stationary), knee bend moderately bent
- 5 concrete drills with progression cues matched to the findings

Real output from a real clip.

---

## Roadmap — Three Phases

### Phase 1 — Bulletproof Demo (4–6 weeks)

**Goal:** Every person who sees the demo asks "how do I get this?"

| Task | Why |
|------|-----|
| Harden prompt pipeline — output always specific, never generic | The current risk: LLM occasionally falls back to generic advice. Must be eliminated. |
| Multi-session comparison in UI | "Last week vs. this week" makes the subscription value self-evident |
| Demo video with annotated overlay | Visually show the AI watching the player — the most compelling moment in any demo |
| 60-second analysis target | Eliminate the perceived wait |

**Deliverable:** A demo that lands every time, with anyone in the room.

---

### Phase 2 — Real Users, Real Revenue (6–10 weeks after Phase 1)

**Goal:** 50 users using it weekly, paying or on a trial.

| Task | Why |
|------|-----|
| Cloud accounts + sync | Users need their session history on any device |
| Subscription payment | Even $5/month from 100 users is a concrete market signal |
| Video robustness improvements | Handle more lighting conditions, camera distances, angles |
| Harden Investigator mode | Finish budgets, permissions, cancellation and evaluation; make the model-directed path reliable |
| Android polish — share report, export PDF | Users want to send their report to their coach |

**Deliverable:** A working, paying product. Not large — real.

---

### Phase 3 — Platform Play (3–5 months after Phase 2)

**Goal:** Data moat. Expansion. Hard to catch up.

| Task | Why |
|------|-----|
| Table detection | Unlocks 5+ new metrics: player position on court, shot placement, distance from table |
| Stroke classifier | Forehand topspin / backhand / serve / push automatically — per-stroke-type breakdown |
| Voice coaching output | LLM narrates the report — coaching feedback while watching the video. Third modality. |
| Expand to tennis + badminton | Same engine, 3× market |
| Ascend cloud/edge deployment | All inference and training on Huawei hardware; private or regional deployment with no change to user experience |

**Deliverable:** A platform, not just an app. Every session trains the next one.

---

## Business Model

**Freemium subscription:**
- Free: 3 sessions per month, basic report
- Pro ($8–12/month): unlimited sessions, full metrics, progress charts, export
- Club ($40–80/month per coach): coach dashboard across all students, progress tracking, share links

China pricing: RMB 30–50/month (~USD 4–7) — not a USD conversion of a Western price point applied to a different market.

**Why subscription is the right model:**
- Value compounds over time — users stay to see whether they improved
- High frequency of use — a committed player analyses every practice session
- Data advantage — every session improves coaching quality; the longer the platform runs, the harder it is to replicate

**The market:**

| Segment | Size |
|---|---|
| Primary — China (daily club players) | ~85M daily / ~10M competitive |
| China children's sports industry (双减-driven) | ¥400B+, growing 15%+/year |
| Table tennis globally | ~300M recreational (ITTF), ~40M serious |
| Racket sports combined | 500M+ participants globally |
| Serious table tennis players reachable at launch | ~40M worldwide |

Unit economics: at $10/month, 0.1% of serious table-tennis players = $5M ARR from one sport. China is a separately-sized, RMB-denominated market on top.

---

## What Huawei Gains

1. **A reference vertical AI app** — sports coaching is visually impressive, immediately understandable, and demonstrably real-world useful
2. **Recurring Ascend demand** — every analysed session is inference; every improvement cycle is training. Consumer adoption converts directly to hardware utilisation
3. **A clear Huawei deployment path** — the app works without Ascend; openJiuwen/Ascend integration means that when it earns real use, that use runs on Huawei infrastructure with no change to the user experience
4. **A monetisable product, not a research demo** — real subscriptions, daily use, compounding data

---

## What We Need to Proceed

1. **Phase 1 approval** — 4–6 weeks of focused engineering to make the demo compelling every time
2. **Evaluation clips and coach labels** — the benchmark set that validates whether Investigator is ready
3. **Ascend/CANN access and deployment guidance** — for Phase 3 cloud/edge inference and training
4. **Design support** — one UX/UI pass to make the app look like a Huawei product

---

*For how to present this in the room: [04-meeting-guide.md](04-meeting-guide.md)*
*For the four scenarios that make the case most concretely: [03-the-moments.md](03-the-moments.md)*
