# Four Moments

Four things this AI does that no coaching pipeline can.

---

## The discovery nobody knew to look for

A player uploads a practice clip. The app was not told to look at head position.
Nobody programmed "check gaze before contact." The AI noticed a pattern itself:

> "In 6 of the 8 strokes in this clip, the player's head tilts downward 0.3
> seconds before contact. I cross-referenced this with ball impact quality — all
> 6 strokes with the head dip resulted in flat trajectories. The 2 strokes where
> the head stayed level produced measurably more topspin. The player is losing
> sight of the ball at the critical brush moment."

The player did not know this. The coach did not know this. No measurement list
contained it.

A human coach might notice this habit after 10 sessions together. The AI noticed
it in the first clip.

---

## One problem, not four

Most coaching apps return a list: elbow drops, arc too flat, no weight transfer,
late contact. Four things to fix. The player does not know which to start with —
or whether these are four separate problems or four symptoms of one thing.

The AI traced the chain, each tool call building on the previous:

> "The wrist locks rigid 0.4 seconds before contact. That rigidity begins at the
> grip-tighten moment. With the wrist locked, the elbow cannot stay at waist height
> — it drops to compensate. The elbow drop then forces the paddle forward rather
> than upward. This is one problem, not four. The root cause is grip tension. If
> grip tension is corrected, elbow position, swing arc and ball trajectory follow.
> Drilling elbow position while grip tension remains will produce partial and
> unstable improvement."

The player drills one thing. The improvement sticks because it targets the
root, not the symptoms.

---

## From coach to advisor

Post-session analysis tells a player what went wrong technically. But a
continuously running AI watching a live match can shift from technical coach
to real-time tactical advisor:

> "You have played 12 backhand-to-backhand rallies in this set. Your opponent
> has placed 9 of them to your backhand corner and followed with a body shot.
> You are losing 7 of these. This is not a mechanics issue — your technique is
> holding. Your opponent has read your preferred return direction. For the next
> 3 rallies, return to the wide forehand corner. If they adjust within 3 points,
> they are adaptive — switch to the middle body shot."

This is not coaching. This is the kind of real-time match intelligence a
professional courtside advisor provides. The kind most players never have access
to.

Until now.

---

## When the right answer is not coaching

A pipeline produces a coaching report. Every session. That is all it knows how
to do.

After comparing this session against the previous four, the AI did not produce
a coaching report:

> "Average stroke cycle time has increased 18%. Step frequency to the ball has
> dropped 22%. Reaction window before contact has widened 0.3 seconds. These
> are not technique regressions — the mechanics on each stroke are consistent.
> This pattern looks like accumulated fatigue or the early signal of a physical
> strain. I am not producing coaching recommendations. I am flagging this session
> for coach review and recommending rest before the next training block."

Nobody programmed "detect fatigue." Nobody programmed "change your output when
the data is not about technique." The AI looked at three independent metrics,
noticed they degraded together across the session, and changed what it produced.

The question nobody thinks to ask: what does the AI do when the right answer is
not coaching? A pipeline answers anyway. This AI decides.

---

*The architecture that makes this possible: [07-architecture.md](07-architecture.md)*
