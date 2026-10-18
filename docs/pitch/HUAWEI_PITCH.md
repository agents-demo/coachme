# TopSpin Review — Pitch for Huawei Internal Stakeholders

> **One-sentence pitch:** AI personal sports coach in your pocket — record a practice session, and the app watches it like a coach and tells you exactly what to fix.

---

## The Problem

A good table tennis coach charges $60–120 per hour.
Most recreational players practice 4–5 times a week — largely alone, with zero expert feedback.
They repeat the same mistakes for years without ever knowing it.

This is not a niche problem. There are 300 million recreational racket sport players worldwide (table tennis, tennis, badminton, padel, squash) who train regularly but have no consistent access to coaching.

---

## What This Is

A mobile + web app that accepts a practice video and returns a structured coaching report — specific observations tied to timestamps, concrete drills, and progress tracking over time.

**Not** a chatbot. Not "describe your swing and I'll give tips." The AI *watches* the video, detects body mechanics and ball behavior, and writes findings that are grounded in what it actually measured.

---

## Why This Matters for Huawei / openJiuwen

### 1. This is agentic AI in a real vertical

The analysis pipeline is a textbook multi-step agent:

```
Video input
    → Stage 1: Observe (frame sampling, motion mask)
    → Stage 2: Measure (pose landmarks, ball trajectory, stroke detection)
    → Stage 3: Coach (LLM reasons over measurements, writes structured report)
    → Output: coaching report with citations to timestamps
```

This is exactly what openJiuwen is built to do: orchestrate a pipeline of specialized AI steps into a coherent result. The app is a concrete, non-trivial showcase of that pattern in the real world.

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

### 3. Heavy GPU/NPU usage per session

Every time a user analyzes a video:
- MediaPipe pose runs on NPU (30fps × clip length landmark inference)
- Ball detection model runs per-frame
- LLM processes structured metrics + frames
- **Kirin NPU opportunity:** on-device pose inference would make offline analysis possible and fast, while demonstrating Kirin's AI capability concretely

This is not a user who sends one text message. This is a user who burns meaningful compute every time they practice — potentially 5 times a week.

---

## Current Demo Status — Honest Assessment

### What works today
- Upload any video → get a real, structured coaching report
- Report has: summary, specific observations with timestamps, recommended drills, detected metrics (knee angle, elbow angle, footwork range, rotation values)
- Web app (SvelteKit) + Android app both functional
- Session history and progress tracking

### What is not yet product-ready
- **Output quality depends heavily on video conditions** — bad angle, dark gym, player too small in frame all degrade the result significantly
- **No user accounts** — everything is local per-device, no cloud sync
- **Analysis takes 30–90 seconds** depending on clip length — acceptable for demo, borderline for daily use
- **One sport only** — table tennis works; other sports are technically supported but not validated

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
| openJiuwen integration for agentic pipeline | Replace the current linear pipeline with openJiuwen-orchestrated agents — each stage becomes a named tool call, observable and improvable |
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
| Kirin NPU on-device mode | Pose inference fully offline, no cloud needed for basic analysis — Huawei differentiator |

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
- Table tennis alone: 875 million players globally (ITF estimate), ~40M serious recreational players in the tier who would pay
- Racket sports combined (tennis, badminton, padel, squash): 500M+ recreational participants
- At $10/month × 0.1% of addressable serious players: $5M ARR from table tennis alone

---

## What openJiuwen Gains From This

1. **A reference vertical agent** — sports coaching is easy to understand, visually impressive, and real-world useful. Perfect for showing what the platform can do.
2. **Multi-modal showcase** — video in, text + metrics out, voice next. Not a synthetic demo.
3. **Kirin NPU proof point** — on-device pose inference is a concrete demonstration of Kirin AI capabilities in daily life.
4. **A monetizable product** — not a research demo. An app people pay for, built on openJiuwen.

---

## What We Need to Proceed

1. **Green light on Phase 1** — 4–6 weeks of focused engineering to make the demo bulletproof
2. **Access to openJiuwen API** for Phase 2 integration
3. **Kirin NPU SDK / MediaPipe optimization guidance** for Phase 3 on-device mode
4. **Design support** — one UX/UI pass to make the app look like a Huawei product, not a prototype
