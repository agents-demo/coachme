# The Architecture That Makes It Possible

The four scenarios in [03-the-moments.md](03-the-moments.md) are not features.
They require a different architecture. This document explains why.

---

## Pipeline vs investigation

In the current pipeline, application code is the orchestrator. It calls pose
detection, calls ball tracking, dumps the measurements into a model prompt. The
model is a function at each step — it receives whatever the programmer decided
to feed it and has no say in what happens next.

In an AI-directed system, the model is the orchestrator. It decides which tools
to call, in what order. It can look deeper at something, change direction based
on what it finds, call something it was not expected to call, or stop early. The
programmer provides tools; the model composes them.

This distinction is trivial when the right analysis path is known in advance and
fixed. It becomes critical when it is not — which is most real-world video.

---

## Where the architecture becomes genuinely necessary

**When the video is not what you expected.**
Real clips contain two players, overhead cameras, mid-clip lighting changes,
someone walking through the shot. A hardcoded pipeline fails silently. An agent
notices the unexpected and reasons about it: which bounding box to focus on,
which frames to exclude, what to note as a limitation. No one programmed these
decisions — the agent reasoned to them.

**When findings drive the investigation.**
A fixed pipeline measures everything, then hands it to the model to write about.
The model is a scribe. In an agent, an initial finding opens a new line of
investigation: "the ball trajectory is flatter than expected for a topspin
stroke — let me look at the contact-moment frames specifically." The measurement
decisions are made after findings exist, not before.

**When two measurements contradict.**
Pose data says the elbow is at the correct height, but ball trajectory is still
flat. A pipeline hands both to the model without knowing they conflict. An agent
notices the contradiction, investigates which is more reliable, and either
resolves it or flags it honestly.

**When the answer requires cross-session reasoning.**
Useful longitudinal coaching requires: fetching historical sessions mid-analysis,
forming a hypothesis from the pattern, changing the recommendation accordingly.
A pipeline produces session-level outputs; statistical comparison is a separate
layer. An agent reasons across sessions as part of a single coherent thought.

**When live coaching is the target.**
Phone on a tripod, player playing, AI gives voice feedback between points. This
is not a harder version of the current architecture. It requires a continuously
running, stateful, event-driven agent that maintains context across all points
played. There is no request/response version of this.

---

## What does not require this architecture

- Retry logic and checkpointing — a job queue.
- Parallel analysis — async/await API calls.
- Cost routing to different models — an if/else in application code.
- Logging and observability — middleware.
- Human review for edge cases — a queue and a webhook.

These are real conveniences of a platform. They are not the reason the
architecture has to change.

---

## For technical questions: the honest answer

Direct model calls are enough to prove the concept — the demo app does exactly
that.

> "Direct model calls prove the concept. The platform becomes necessary when the
> AI has to handle unexpected video conditions intelligently, investigate findings
> rather than just describe measurements, and eventually run as a continuous agent
> during live play. Those are not problems you solve by making more API calls.
> They require the model to be in control of the investigation."

One concrete example:

> "Imagine the player switches strokes midway through the clip. The current
> pipeline was built for one stroke type — it produces confused measurements.
> An agent notices the switch, segments the clip and analyses each part
> separately. Nobody programmed that specific case. The agent reasoned to it.
> That is the difference."
