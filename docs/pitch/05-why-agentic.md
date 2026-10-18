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

## The three scenarios for a WOW moment in a presentation

The scenarios above are true and important. These three are for the room. They are the scenarios where a technical audience stops and thinks: *"I had not thought of that."*

---

### WOW 1: The agent finds something no programmer knew to look for

This is the scenario that breaks the "AI describes what it measures" mental model entirely.

A coaching pipeline can only find what it was programmed to measure: elbow angle, knee bend, stroke arc. These are predefined measurements fed into a scribe.

An agent with vision access and the ability to cross-reference measurements freely can discover patterns that are **not in any coaching textbook and not in any programmer's mental model**.

A real example of what this looks like in practice:

> "I notice that in 6 of the 8 strokes in this clip, the player's head tilts downward 0.3 seconds before contact. I cross-referenced this with ball impact quality scores — all 6 strokes with the head dip resulted in flat ball trajectories. The 2 strokes where the head stayed level produced measurably more topspin. This pattern is consistent enough to be causal, not coincidental. The player is losing sight of the ball at the critical brush moment."

Nobody told the agent to look for head position. Nobody programmed "correlate gaze with stroke outcome." Nobody even knew this player had this habit — not the player, not their coach.

A human coach watching this clip might notice it after 10 sessions. The agent noticed it in the first analysis, because it was free to look at everything and cross-reference freely.

**This is the scenario that answers: "what can an agentic AI find that a human coach cannot?"** Not better — faster. The agent looked at relationships no human would think to check on a first viewing. That is a qualitatively different product.

---

### WOW 2: Causal chain, not a list of problems

Every coaching app lists problems. Elbow drops. Arc too flat. No weight transfer.

A scribe pipeline reports each measurement as a separate finding. The player receives a list of 4 things to fix. They do not know which to fix first, because they do not know whether these are 4 independent problems or 4 symptoms of one root cause.

An agent can trace a causal chain across multiple evidence sources, each requiring a separate tool call:

> "Frame-by-frame wrist angle data shows the wrist locks rigid 0.4 seconds before contact [tool call: wrist kinematics]. That rigidity begins at the grip-tighten moment [tool call: hand pressure proxy from finger spread]. With the wrist locked, the elbow cannot remain at waist height through the swing — it drops to compensate for lost wrist mobility [tool call: elbow trajectory against wrist state]. The elbow drop then mechanically forces the paddle to swing forward rather than upward, producing the flat arc [tool call: ball trajectory after contact].
>
> This is one problem, not four. The root cause is grip tension before contact. If grip tension is corrected, elbow position, swing arc, and ball trajectory will follow. Drilling elbow position while grip tension remains will produce partial and unstable improvement."

A pipeline reports 4 issues. An agent delivers one diagnosis with a causal chain and a single point of intervention.

The coaching output is not just more accurate — it is categorically different. The player drills one thing instead of four. The prescriptions land because they target the root, not the symptoms.

**This is the scenario that answers: "why does agentic coaching produce better outcomes than a pipeline?"** Not because it knows more about table tennis. Because it can reason across dynamic evidence — calling tools based on what previous calls returned — in a way that a fixed pipeline structurally cannot.

---

### WOW 3: The agent becomes a tactical advisor, not just a technical coach

This is the scenario that describes a different product category entirely — unlocked only by a continuously running agent.

Today: player records a drill clip, uploads it, receives technical feedback on stroke mechanics.

This is useful. It is also static.

A continuously running agent watching a **live match** can shift from technical coach to tactical advisor in real time:

> "You have played 12 backhand-to-backhand rallies in this set. Your opponent has placed 9 of them to your backhand corner and followed with a body shot. You are losing 7 of these. This is not a mechanics issue — your technique is holding. Your opponent has read your preferred return direction. For the next 3 rallies, return to the wide forehand corner. If they adjust within 3 points, you'll know they're adaptive — switch to the middle body shot."

This is not coaching anymore. This is real-time tactical analysis — the kind a professional match coach sitting at the table provides. The kind most recreational players never have access to.

It requires: persistent session memory across all points played, opponent pattern modeling built incrementally as the match progresses, the ability to switch reasoning mode from "technical" to "tactical" based on what the data shows, and delivery in seconds between points.

None of these are possible in a request/response LLM call from application code. There is no "session" to maintain between points. There is no opponent model. There is no memory of points 1 through 12 at the moment of point 13.

**This scenario is the product roadmap in one paragraph.** The demo app proves the concept. An agentic platform running continuously is how it becomes a personal coach that knows your game, knows your opponent, and changes what it tells you based on what it observed — not based on what it was programmed to say.

---

### WOW 4: The agent changes what it produces entirely — because something is wrong

The three scenarios above are about coaching quality. This one is different. It is about the agent recognising that the situation does not call for a coaching report at all.

A hardcoded pipeline has one output mode: coaching findings. Every session, regardless of what the data shows, produces a coaching report. The pipeline was programmed to produce a coaching report. It produces one.

An agent can look at the data and decide the data is not saying something about technique — it is saying something about the player's physical state.

> "Comparing this session to the previous four: average stroke cycle time has increased by 18%. Step frequency to the ball has dropped 22%. Reaction window before contact has widened by 0.3 seconds. These are not technique regressions — the mechanics on each stroke are consistent. This pattern across the session looks like accumulated fatigue or the early signal of a physical strain. I am not going to produce coaching recommendations. I am flagging this session for coach review and recommending the player rest before the next training block."

Nobody programmed "detect fatigue." Nobody programmed "do not produce coaching output if the player seems injured." Nobody programmed the concept of switching output mode based on what the data shows.

The agent noticed that three independent metrics degraded in a correlated pattern across the session — not on a single stroke, but as a trend — and changed what it produced accordingly.

**This is the scenario that answers a question nobody in the room will have thought to ask:** "What does the AI do when the right answer is not coaching?" In a pipeline, the answer is: it produces coaching anyway, because that is all it knows how to do. In an agent, the answer is: it decides.

This is also where the product touches Huawei's broader health ecosystem. A system that can detect physical fatigue or early overtraining signals from motion data — not from a wearable, but from a camera — is a health monitoring capability, not just a coaching capability. That is a product category expansion that costs nothing to add if the architecture already supports it.

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
