# TopSpin Review — Pitch for Huawei Internal Stakeholders

> **One-sentence pitch:** AI personal sports coach in your pocket — record a practice session, and the app watches it like a coach and tells you exactly what to fix.

---

## The Problem

A good table tennis coach charges $60–120 per hour.
Most recreational players practice 4–5 times a week — largely alone, with zero expert feedback.
They repeat the same mistakes for years without ever knowing it.

This is not a niche problem. Table tennis alone has approximately 300 million recreational players (ITTF estimate); across table tennis, tennis, badminton, padel and squash, the combined participant base exceeds 500 million. Most train regularly with little or no expert feedback between sessions.

---

## What This Is

A mobile + web app that accepts a practice video and returns a structured coaching report — specific observations tied to timestamps, concrete drills, and progress tracking over time.

**Not** a chatbot. Not "describe your swing and I'll give tips." The AI *watches* the video, detects body mechanics and ball behavior, and writes findings that are grounded in what it actually measured.

The app is deliberately **backend-agnostic** (the coaching logic does not depend on any specific AI provider or compute hardware). Its value is the coaching loop, not the engine underneath it. Different model providers and compute backends can run it. Ascend and the openJiuwen/Ascend integration are the Huawei scale path: if the app earns repeated consumer use, that use creates recurring inference and training demand that can be served on Ascend.

---

## Why This Matters for Huawei / openJiuwen

### 1. The differentiator: evidence-backed adaptive coaching

The differentiator is **evidence-backed adaptive coaching**: the pipeline measures before it writes,
ties every finding to measured evidence and a timestamp, and adapts the investigation to what is
found. It is one differentiator, with two layers of implementation.

**Standard mode** (the reliable default, demo-ready): a fixed pipeline — observe, measure, focused
vision, write, verify. Every finding cites a timestamp and a measured value; the pipeline drops any
claim it cannot support. This is what the demo shows and what users can verify by checking the
timestamps. It already separates the product from generic AI chatbots, which produce advice without
measurements.

**Investigator mode** (the adaptive layer, opt-in while being benchmarked): the model directs its
own investigation — choosing which tools and time windows to use, ignoring ball tracking if
irrelevant, digging into wrist/racket mechanics when the evidence leads there. Every claim still
requires a cited evidence ID. Whether it produces better outcomes than Standard is the hypothesis;
the benchmark measures it.

### 2. Multi-modal throughout

| What | Modality |
|------|----------|
| Video input | Vision |
| Pose detection (MediaPipe) | Vision → structured landmarks |
| Ball tracking | Vision → trajectory data |
| LLM coaching report | Text generation grounded in vision data |
| **Roadmap:** Voice coaching | Audio output |
| **Roadmap:** Real-time overlay | Vision + AR |

Three modalities today. The roadmap adds two more. Every modality is a real GPU/NPU workload.

### 3. A recurring workload for Huawei Ascend

Every time a user analyzes a video:
- pose inference runs across the clip;
- ball detection runs per frame;
- the vision model reads sampled frames;
- the LLM reasons over structured metrics and frames.

**Ascend opportunity:** this is a batch video-inference workload, not a one-off chat request.
Pose, ball and vision batches can run on **Ascend 310/310P inference** hardware, and models can be
trained on **Ascend 910-class** systems through **CANN** and **MindSpore**. Private or regional cloud
deployment is a natural fit; on-device inference is a separate optimization, not the Ascend story.

This is not a user who sends one text message. This is a user who burns meaningful compute every time
they practice — potentially five times a week.

The app does not need Ascend to be useful. The win-win is that a useful app, adopted repeatedly, creates the kind of recurring inference and training demand that Ascend is built to serve.

---

## Current Demo

### What works today
- Upload any video → get a real, structured coaching report
- Report has: summary, specific observations with timestamps, recommended drills, detected metrics (knee angle, elbow angle, footwork range, rotation values)
- Web app (SvelteKit) + Android app both functional
- Session history and progress tracking

### Honest current state

- **Zero paying users today.** The product is a working prototype, not a commercial launch.
- **Benchmark not yet run.** Investigator mode is opt-in while the evaluation set is built; its quality advantage over Standard is the hypothesis, not yet a measured result.
- **One sport validated.** Table tennis mechanics are the only proven domain; tennis and badminton are on the roadmap but untested.
- **No accounts or cloud sync.** Session history is device-local.
- These are not reasons to reject the concept. They are reasons the Phase 1 ask is modest and the timeline is short: validation is the goal of Phase 1, not scaling.

### Next product milestones
- **Video robustness:** filming guidance and quality checks are in place; wider angle/lighting support is on the roadmap
- **Accounts and sync:** the next product milestone for cross-device history
- **Analysis time:** 30-90 seconds today; the Phase 1 target is under 60 seconds
- **Sports coverage:** table tennis is validated; tennis, badminton and padel are the expansion path
- **Investigator rollout:** opt-in while the benchmark is completed; Standard remains the reliable default

### The demo we can show right now
A real 10-second training clip (Michael Osher, club session, professional table) analyzed to produce:
- 5 specific coaching findings grounded in what the AI measured, each citing exact timestamps
- Accurate reading: shoulder rotation 14°, hip rotation 9° (both far below optimal), footwork coverage 5% of frame (stationary), knee bend moderately bent
- 5 concrete drills with progression cues matched to the findings

This is a real output. Not mocked beyond the data input.

---

## Roadmap — What Actually Gets Built

### Phase 1 — Demo to Convincing Demo (4–6 weeks)

**Goal:** The demo always impresses. Every stakeholder who sees it asks "how do I get this?"

| Task | Why |
|------|-----|
| Harden prompt pipeline — ensure output is always specific, never generic | The current risk: LLM occasionally falls back to generic advice. This must be eliminated. |
| Multi-session comparison in UI | Show "last week vs. this week" — makes the subscription value obvious |
| Demo video with annotated overlay (hardcoded) | Visually show AI seeing the player — most compelling moment in any demo |
| 60-second analysis target | Reduce perceived wait time |

**Deliverable:** A repeatable demo that can be shown to anyone and lands every time.

---

### Phase 2 — MVP with Real Users (6–10 weeks after Phase 1)

**Goal:** 50 real users using it weekly, paying or on a trial.

| Task | Why |
|------|-----|
| Cloud accounts + sync | Users need their session history on any device |
| Subscription payment (basic) | Even $5/month from 100 users is a signal |
| Video robustness improvements | Handle more lighting conditions, camera distances, angles |
| Harden Investigator mode | Finish budgets, permissions, cancellation and evaluation; make the model-directed path observable and reliable |
| Android polish — share report, export PDF | Users want to send their report to their coach |

**Deliverable:** Working, paying product. Not large, but real.

---

### Phase 3 — Platform Play (3–5 months after Phase 2)

**Goal:** Expand the moat. Make it hard for anyone else to catch up.

| Task | Why |
|------|-----|
| Table detection (OpenCV homography) | Unlocks 5+ new metrics: player position on court, shot placement, distance from table |
| Stroke classifier (train on TTNet dataset) | Distinguish forehand topspin / backhand / serve / push automatically — enables per-stroke-type breakdown |
| Voice coaching output | LLM narrates the report — user hears coaching feedback while watching their video. Third modality. |
| Expand to tennis + badminton | Same engine, 3× market |
| Ascend cloud/edge deployment | Run pose, ball and vision batches on Ascend with CANN; private or regional deployment - Huawei differentiator |

**Deliverable:** A platform, not just an app. Network effects from user data improve the models.

---

## Business Model

**Freemium subscription:**
- Free: 3 sessions per month, basic report
- Pro ($8–12/month): unlimited sessions, full metrics, progress charts, export
- Club ($40–80/month per coach): coach sees multiple players' reports, tracks progress across students

**Why subscription is right:**
- Value compounds over time (users stay to see progress)
- High frequency of use: a committed player analyzes every practice session
- Data advantage: every session improves coaching quality over time

**TAM signal:**
- Table tennis: ~300 million recreational players globally (ITTF estimate), ~40M serious recreational players in the tier who would pay
- Racket sports combined (table tennis, tennis, badminton, padel, squash, pickleball): 500M+ participants — not additive; many players play more than one sport
- At $10/month × 0.1% of addressable serious table-tennis players: $5M ARR from table tennis alone

---

## What Huawei gains from this

1. **A reference vertical app** - sports coaching is easy to understand, visually impressive, and real-world useful.
2. **Recurring accelerator demand** - every analyzed session is inference; every improvement cycle is a training opportunity. Successful consumer usage is what turns apps into Ascend demand.
3. **An agentic-platform proof point** - openJiuwen/Ascend integration turns that demand into an easy deployment path, not a user-facing dependency.
4. **A monetizable product** - not a research demo. An app people pay for, whose compute can run on Huawei infrastructure.

---

## What We Need to Proceed

1. **Green light on Phase 1** — 4–6 weeks of focused engineering to make the demo bulletproof
2. **Evaluation clips and coach labels** — the benchmark set that decides whether Investigator is ready
3. **Ascend/CANN access and deployment guidance** for Phase 3 cloud/edge inference and training
4. **Design support** — one UX/UI pass to make the app look like a Huawei product, not a prototype

---

*For how to present this in the room: [04-meeting-guide.md](04-meeting-guide.md)*
*For the four scenarios that make the case most concretely: [03-the-moments.md](03-the-moments.md)*
