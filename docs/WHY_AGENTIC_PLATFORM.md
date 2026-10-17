# Why an Agentic Platform — Honest Analysis

The direct question: is openJiuwen (or any agentic platform) genuinely necessary here, or is direct LLM/VLM usage enough?

Honest answer: **for the current demo, and even for a working V1 with a few hundred users, direct LLM calls are sufficient.** The Android app proves this — it calls the model directly and it works. The agentic platform becomes genuinely necessary as the product scales in specific ways. This document explains exactly when and why.

---

## Where direct LLM is genuinely not enough

### 1. Long-running jobs that must survive failures

A video analysis job takes 30–90 seconds across multiple stages. With a direct LLM call, if anything fails — network dropout, model timeout, crash mid-pose-estimation — the entire job fails and the user starts over.

An agentic platform checkpoints each stage. If the coaching stage (stage 3) fails, you restart from stage 3, not from frame extraction (stage 1). For a 10-minute video this is the difference between a 90-second retry and an 8-minute retry. At scale, this becomes a core reliability requirement, not a nice-to-have.

You can build your own checkpointing logic in application code. But then you have reinvented a fragile version of what the platform provides.

### 2. The verify-and-retry loop

The current pipeline runs: coach → verify → drop unsupported findings. If verification drops 3 of 5 findings, you may want to:
- Generate replacement findings based on the remaining evidence
- Or lower the minimum confidence threshold and re-run coaching

This is a conditional loop: the output of step N determines whether you re-run step N-1. A single LLM call cannot conditionally loop back. Application code can implement this, but it becomes tightly coupled to the specific pipeline logic and breaks every time the pipeline changes. An agentic platform makes conditional branching and retry a first-class primitive.

### 3. Parallelism for longer videos

A 10-minute training session might contain 40–50 stroke cycles. You want to:
- Analyze multiple stroke windows in parallel
- Run ball tracking and pose detection simultaneously
- Merge the results

A single LLM call is sequential. You can make parallel API calls from application code, but then you are managing concurrency, error handling, and result aggregation manually — all things the platform does natively.

### 4. Observability at scale — the quality iteration problem

This is the most underrated reason.

When you have 10,000 users and some of them get poor reports, you need to know:
- Which stage produced the problem?
- What inputs did the LLM receive?
- What did it output?
- Was there a retry?
- How long did each stage take?

With direct LLM calls and no platform: you have application logs at best. Debugging a bad report means reconstructing what happened from scattered logs. Improving the coaching quality means deploying a new prompt version and hoping nothing regressed.

With an agentic platform: every tool call, every model input and output, every stage timing is automatically logged, structured, and queryable. You can look at any session and see exactly what happened at every step. You can run a new prompt version on the same inputs and compare outputs. This is not optional once you care about quality improvement — it is the only practical way to iterate.

### 5. Human-in-the-loop escalation

Some cases the AI should not handle alone:
- Video is too dark or too short to analyze reliably — ask the user to retake
- Player appears injured — coaching advice could be harmful, flag for human review
- Children detected — different coaching protocols, potentially different privacy requirements

An LLM can decide to escalate, but a direct API call has no mechanism to actually pause execution and wait for a human response. The job either completes or fails. An agentic platform has human-in-the-loop as a native primitive: the agent can pause at a defined point, notify someone, and resume when approved.

### 6. Long-horizon multi-session reasoning

"Compare this player's progress across 20 sessions. Which issues have persisted the longest? Which have improved? What is the pattern?"

Twenty session reports easily exceed a practical LLM context window when you include the full data. Even if they fit, a single LLM call has no mechanism to fetch reports from storage, normalize findings across sessions, retrieve relevant video segments, and reason over all of it coherently.

This requires orchestrated steps: fetch → normalize → identify patterns → generate comparative insight → cite specific sessions. Each step is a tool call. The platform orchestrates them. A direct LLM call cannot.

### 7. Real-time streaming — the live coach feature

The roadmap includes real-time coaching during practice. The phone is on a tripod, the player is playing, the AI gives voice feedback between points.

This is structurally impossible with a direct LLM call model. You need:
- An agent running continuously, watching a video stream
- Event detection: "a stroke just happened"
- Within 2–3 seconds: analyze that stroke, generate a coaching note, speak it
- Continue watching for the next stroke, maintaining context across the session

This is a stateful, event-driven, continuously running agent. There is no way to do this with a single API call per user action. The entire architecture requires an agentic runtime.

### 8. Multi-agent for multi-player analysis

The demo video has two players. A future feature: analyze both and generate a comparative report. This requires:
- Detecting and tracking two separate bounding boxes
- Running separate analysis pipelines per player, in parallel
- A coordinator agent that compares findings and generates relational insights ("Player A has better footwork, Player B has better stroke preparation")

Two simultaneous pipelines with a coordinator is a multi-agent architecture by definition. A single LLM call produces one output for one implicit subject. Multi-player analysis requires the platform.

### 9. Cost and model routing at scale

For a production app with volume:
- Simple 30-second clip, good lighting, clear player → fast cheap model
- Complex 10-minute session, multiple players, poor lighting → expensive powerful model
- Batch processing overnight → different resource pool than real-time demo

Direct integration means you pick one model and use it for everything. An agentic platform can route to different models or resource pools based on task complexity, time of day, user tier, or cost budget — all without changing application code.

---

## Where direct LLM is genuinely sufficient

Being honest about this matters:

- **V1 with basic video analysis**: direct LLM calls work fine. The Android demo proves it.
- **Single sport, single player, single session**: no multi-agent needed.
- **Small user base (< ~1,000 sessions/day)**: the observability pain is manageable manually.
- **No real-time streaming requirement**: synchronous API calls are fine.
- **No human-in-the-loop needed**: if you are comfortable with AI handling all cases, no escalation logic needed.

The inflection point where direct LLM becomes the wrong architecture is roughly: **when the product tries to do more than one thing per session, or when quality iteration at scale becomes a priority.**

---

## The practical boundary

A useful way to think about it:

| Scenario | Direct LLM enough? |
|---|---|
| Analyze a single clip, return a report | Yes |
| Handle failure mid-analysis gracefully | No |
| Analyze a 10-minute session in parallel chunks | No |
| Debug why a specific user got a bad report | No at scale |
| Pause analysis and ask user to retake video | No |
| Compare 20 sessions for trend analysis | No |
| Live real-time coaching during play | No |
| Analyze two players in the same clip | No |
| Route to cheap model for simple clips | No |
| Improve coaching quality through prompt A/B testing | No |

---

## What this means for the pitch

The honest framing for the Huawei meeting:

> "For the current demo — and even for an initial product — we can run directly on the model. The Android app does exactly this. But the moment we need reliability at scale, quality observability, multi-session reasoning, or live coaching, the direct model call architecture hits a wall. That is when the platform is not a nice-to-have — it is what makes the product work at all."

This is more credible than claiming you need openJiuwen for the demo. You do not. You need it for what comes after.

---

## The specific value openJiuwen adds on top of "any agentic platform"

Beyond the generic agentic arguments, openJiuwen specifically adds:
- Integration with Kirin NPU for on-device inference stages
- Huawei cloud infrastructure for the stages that do run server-side
- Tooling designed for the Chinese developer ecosystem and regulatory context
- A deployment path to HarmonyOS that competing platforms do not have

These are the reasons to use openJiuwen specifically, rather than a generic agentic platform. The generic arguments above explain why an agentic platform is needed. These four explain why it should be openJiuwen.
