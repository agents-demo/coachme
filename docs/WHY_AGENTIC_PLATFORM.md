# Why an Agentic Platform — Honest Analysis

The direct question: is openJiuwen (or any agentic platform) genuinely necessary here, or is direct LLM/VLM usage enough?

First, what the previous version of this document got wrong: it listed things like checkpointing, parallelism, and cost routing as agentic arguments. Those are engineering problems. Any competent developer solves them in application code without a platform. They are not real arguments for agentic architecture.

The real question is harder: **what does an agentic platform enable that is qualitatively different — not just more convenient — from calling an LLM as a function?**

---

## The fundamental architectural difference

In the current pipeline, **application code is the orchestrator**. It calls pose detection, calls ball tracking, dumps the measurements into an LLM prompt, calls the LLM, takes the output. The LLM is a function at each step. It has no say in what happens next. It receives whatever the programmer decided to give it.

In an agentic system, **the LLM is the orchestrator**. It decides which tools to call, in what order, with what parameters. It can decide to look deeper at something, change direction based on what it finds, call a tool it wasn't expected to call, or stop early. The programmer provides tools; the model composes them.

This difference is trivial when the correct analysis path is known in advance and fixed. It becomes critical when it is not.

---

## Where it actually matters

### 1. The video is not what you expected

The current pipeline assumes: one player, reasonable lighting, side-on camera, 10–60 seconds of single-stroke drill.

Real videos: two players rallying, overhead camera, player half out of frame, someone walks through the shot at second 4, the lighting changes mid-clip, the player switches from forehand to backhand mid-drill.

A hardcoded pipeline fails silently or handles these badly — it was not programmed for them. An agent notices something unexpected and reasons about it:

> "I'm detecting two bounding boxes. The one on the left has higher pose confidence and is closer to the net — I'll focus analysis there and note the second player in limitations."

> "Pose confidence drops sharply between frames 60–90. Something occluded the player. I'll exclude those frames from mechanics measurements rather than averaging corrupted data in."

No one programmed these decisions. The agent reasoned to them. Every edge case in a hardcoded pipeline requires a programmer to have predicted it. An agent handles novel situations through reasoning.

### 2. Findings drive the investigation, not the other way around

In the current architecture: measure everything → hand measurements to LLM → LLM writes about what it was given. The LLM is a scribe. The investigation is predetermined by what the CV pipeline measured.

In an agentic system, an initial finding opens a new line of investigation:

> "I found what looks like inconsistent elbow position. Let me call the pose tool again, specifically requesting elbow angle measurements at backswing frames only, across all detected strokes — not averaged across the whole clip."

> "The ball trajectory after contact is flatter than expected for a topspin stroke. Let me look at the contact-moment frames specifically to check racket angle. This might explain the stroke arc issue."

This is targeted, finding-driven investigation. The model decides what evidence it needs and goes to get it. A pipeline cannot do this because the measurement decisions are made before any findings exist.

### 3. Cross-validation between evidence sources

The pose data says the player's elbow is at 88°. The ball trajectory after contact is relatively flat. These are consistent — elbow too low causes flat arc. The agent can notice this consistency and state it with higher confidence.

But what if they contradict? Pose says the elbow is at a correct height, but the ball trajectory is still flat. Now something is wrong — maybe the wrist angle is the issue, or the contact point is late, or the pose measurement was corrupted by motion blur at that specific frame. An agent can notice the contradiction, investigate which measurement is more reliable, and either resolve it or flag it honestly.

A pipeline cannot do this. It produces measurements and hands them to the LLM without knowing whether they are consistent or contradictory. The LLM at that point has no way to go back and check.

### 4. Longitudinal reasoning that actually uses the past

The current trend analysis: compare numeric metrics across sessions. If elbow angle was 88° last week and 94° this week, that is improvement.

Genuinely agentic longitudinal reasoning looks different:

> "Fetch the last 8 sessions for this player. [tool call] I see that the elbow issue has been present since session 2. It was worse in sessions 5 and 6 — the notes say the player switched paddle weight. It partially improved in session 7 after the shadow drill was prescribed. It has not improved further in sessions 8–10 despite continued drilling. This suggests the issue may be habitual rather than strength-related. The coaching recommendation changes accordingly."

This requires: fetching external data mid-reasoning, forming a hypothesis from the data, and changing the coaching output based on the hypothesis. A pipeline produces session-level outputs and a separate trend layer compares them statistically. An agent reasons across sessions as part of a single coherent thought.

### 5. The coaching knowledge base becomes a live tool

Currently: LLM uses its parametric knowledge about table tennis coaching. What it knows is fixed at training time.

Agentic: when the agent identifies an issue, it queries a coaching knowledge base as a tool call:

> "Elbow drops on backswing — search for: root causes, standard correction sequence, drill options, typical improvement timeline, common mistakes when fixing this."

The knowledge base returns coach-validated content. The agent integrates it with the specific measurements from this player's video. The finding is grounded in both measured evidence AND validated coaching knowledge, not just LLM parametric memory.

As the knowledge base grows from real coaching experience, every agent session benefits — without retraining the model. This is impossible in a direct LLM call: you would need to stuff the entire knowledge base into the prompt on every call.

### 6. Real-time live coaching — structurally different architecture

The roadmap includes: phone on a tripod, player playing, AI gives voice feedback between points.

This is not a "harder version" of the current architecture. It is a different architecture entirely.

The agent must: watch a continuous video stream, detect that a stroke just occurred, decide whether this stroke is worth analyzing, call the analysis tools on just that stroke, generate a short coaching note, deliver it as voice, then continue watching — maintaining context about what has already been said this session so it does not repeat itself.

This is a stateful, event-driven, continuously running agent with a persistent memory of the session. There is no meaningful way to implement this as request/response LLM calls from application code. The agent runtime IS the architecture.

---

## What is not a strong agentic argument

Being honest about what does NOT require an agentic platform:

- **Retry logic and checkpointing**: application code with a job queue. Standard engineering.
- **Parallel analysis**: async/await API calls. Not agentic.
- **Logging and observability**: logging middleware. The platform makes it easier but it is not what makes agentic necessary.
- **Cost routing to different models**: an if/else in application code.
- **Human-in-the-loop for simple cases**: a queue and a webhook. Straightforward.

These are real benefits of a platform, but they are "more convenient" not "fundamentally required." Do not use them as core arguments.

---

## The honest pitch framing

For V1 — direct LLM calls are fine and the Android demo proves it.

The agentic platform becomes genuinely necessary when:

1. The product must handle real-world video variability, not just clean demo clips
2. The coaching quality must improve through targeted investigation rather than fixed measurement dumps
3. Cross-session reasoning requires tool calls to historical data mid-analysis
4. A coaching knowledge base needs to be queried as evidence, not stuffed into context
5. Live real-time coaching is the target — a fundamentally different runtime model

The honest version to say in the meeting:

> "Direct model calls are enough to prove the concept — the Android app does exactly that. The platform becomes genuinely necessary when we want the AI to handle unexpected video conditions intelligently, to investigate findings rather than just describe measurements, and eventually to run as a continuous agent during live play. Those are not problems you solve by making more API calls. They require the model to be in control of the investigation, not the application code."

---

## The one scenario that makes the case most clearly

If a manager asks for one concrete example of why the architecture has to change:

> "Imagine the player switches from backhand to forehand midway through the clip. The current pipeline was programmed for one stroke type — it produces confused measurements. An agent notices the switch, segments the clip, and analyzes each part separately. Nobody programmed that specific case. The agent reasoned to it. That is the difference."
