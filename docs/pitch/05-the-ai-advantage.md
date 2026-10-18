# What This AI Can See

A coaching pipeline reports what it was programmed to measure.
This AI reports what it finds.

The difference is structural. In a pipeline, the programmer decides in advance what
to look at. In an AI-directed investigation, the AI decides what to look at next based
on what it has already found — calling tools, changing direction, stopping when the
evidence is sufficient.

The four scenarios below show what that makes possible.

---

## 1 — The discovery no programmer knew to look for

A coaching app can only find what it was built to measure: elbow angle, knee bend,
stroke arc. These are predefined checks. The AI is a scribe — it describes what it
was told to report.

Here is what happens when the AI is free to look at anything and cross-reference
freely:

> "I notice that in 6 of the 8 strokes in this clip, the player's head tilts
> downward 0.3 seconds before contact. I cross-referenced this with ball impact
> quality — all 6 strokes with the head dip resulted in flat ball trajectories. The
> 2 strokes where the head stayed level produced measurably more topspin. This
> pattern is consistent enough to be causal, not coincidental. The player is losing
> sight of the ball at the critical brush moment."

Nobody told the AI to look for head position. Nobody programmed "correlate gaze with
stroke outcome." Nobody knew this player had this habit — not the player, not the
coach.

A human coach watching this clip might notice it after 10 sessions. The AI noticed it
in the first analysis, because it was free to look at everything and cross-reference
freely.

**This is what changes when the AI investigates rather than just measures.**

---

## 2 — One root cause, not four problems

Every coaching app lists problems. Elbow drops. Arc too flat. No weight transfer. The
player receives a list of four things to fix and does not know where to start — or
whether these are four independent issues or four symptoms of one root cause.

An AI that calls tools dynamically, each building on what the previous returned, can
trace the full causal chain:

> "Frame-by-frame wrist data shows the wrist locks rigid 0.4 seconds before contact
> [tool call: wrist kinematics]. That rigidity begins at the grip-tighten moment [tool
> call: hand pressure proxy from finger spread]. With the wrist locked, the elbow
> cannot remain at waist height — it drops to compensate for lost wrist mobility [tool
> call: elbow trajectory against wrist state]. The elbow drop then forces the paddle
> to swing forward rather than upward, producing the flat arc [tool call: ball
> trajectory after contact].
>
> This is one problem, not four. The root cause is grip tension before contact. If
> grip tension is corrected, elbow position, swing arc and ball trajectory will
> follow. Drilling elbow position while grip tension remains will produce partial and
> unstable improvement."

A pipeline reports four issues. This AI delivers one diagnosis and one point of
intervention.

**The player drills one thing instead of four. The improvement sticks because it
targets the root, not the symptoms.**

---

## 3 — From technical coach to tactical advisor

Today: a player records a drill clip, uploads it, receives technical feedback. Useful.
Static.

A continuously running AI watching a live match can shift from technical coach to
tactical advisor in real time:

> "You have played 12 backhand-to-backhand rallies in this set. Your opponent has
> placed 9 of them to your backhand corner and followed with a body shot. You are
> losing 7 of these. This is not a mechanics issue — your technique is holding. Your
> opponent has read your preferred return direction. For the next 3 rallies, return to
> the wide forehand corner. If they adjust within 3 points, you will know they are
> adaptive — switch to the middle body shot."

This is not coaching anymore. This is real-time match intelligence — the kind a
professional courtside coach provides. The kind most recreational players never have
access to.

It requires: memory of every point played, opponent pattern modeling built as the
match progresses, the ability to switch reasoning modes from technical to tactical,
and delivery in seconds between points.

**This is the product roadmap in one paragraph.** The demo proves the concept. This
is where it goes.

---

## 4 — When the right answer is not a coaching report

A hardcoded pipeline produces a coaching report. Every session. Regardless of what
the data shows. That is all it knows how to produce.

An AI can look at the data and decide the data is not saying something about
technique at all:

> "Comparing this session to the previous four: average stroke cycle time has
> increased by 18%. Step frequency to the ball has dropped 22%. Reaction window
> before contact has widened by 0.3 seconds. These are not technique regressions —
> the mechanics on each stroke are consistent. This pattern across the session looks
> like accumulated fatigue or the early signal of a physical strain.
>
> I am not producing coaching recommendations. I am flagging this session for coach
> review and recommending the player rest before the next training block."

Nobody programmed "detect fatigue." Nobody programmed "do not produce coaching output
if the player seems injured." Nobody programmed switching output modes based on what
the data shows.

The AI noticed that three independent metrics degraded in a correlated pattern across
the session — not on a single stroke, but as a trend — and changed what it produced
accordingly.

**This answers a question nobody will have thought to ask:** what does the AI do when
the right answer is not coaching? A pipeline produces coaching anyway. This AI decides.

And it touches Huawei's broader health ecosystem: detecting early overtraining signals
from motion data — from a camera, not a wearable — is health monitoring, not just
coaching. That product expansion is free if the architecture already supports it.

---

## The architecture behind this

In the current pipeline, application code is the orchestrator. It calls pose detection,
calls ball tracking, dumps the measurements into a model prompt. The model is a
function at each step — it receives whatever the programmer decided to feed it and has
no say in what happens next.

In an AI-directed system, the model is the orchestrator. It decides which tools to
call, in what order. It can look deeper at something, change direction based on what
it finds, call something it was not expected to call, or stop early. The programmer
provides tools; the model composes them.

This distinction is trivial when the right analysis path is known in advance. It
becomes critical when it is not — which is most real video.

---

## What does not require this architecture

Being direct about what is engineering, not architecture:

- Retry logic and checkpointing — a job queue. Standard.
- Parallel analysis — async/await API calls. Not agentic.
- Cost routing to different models — an if/else in application code.
- Logging and observability — middleware. Easier on a platform, not the reason for it.
- Human review for edge cases — a queue and a webhook.

These are real conveniences of a platform. They are not why the architecture has to
change.

---

## For technical questions: the honest framing

Direct model calls are enough to prove the concept — the demo app does exactly that.

The architecture becomes genuinely necessary when:

1. The product must handle real-world video variability, not just clean demo clips
2. Coaching quality must improve through targeted investigation, not fixed measurement
3. Cross-session reasoning requires calling historical data mid-analysis
4. A coaching knowledge base needs to be queried as evidence, not stuffed into context
5. Live real-time coaching is the target — a fundamentally different runtime model

> "Direct model calls prove the concept. The platform becomes necessary when the AI
> has to handle unexpected video conditions intelligently, investigate findings rather
> than just describe measurements, and eventually run as a continuous agent during
> live play. Those are not problems you solve by making more API calls. They require
> the model to be in control of the investigation."

One concrete example, if asked:

> "Imagine the player switches strokes midway through the clip. The current pipeline
> was built for one stroke type — it produces confused measurements. An agent notices
> the switch, segments the clip and analyses each part separately. Nobody programmed
> that specific case. The agent reasoned to it. That is the difference."
