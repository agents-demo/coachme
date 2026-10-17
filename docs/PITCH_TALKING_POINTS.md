# Pitch Talking Points — Huawei Internal Managers

These are the strategic insights for the conversation, not slide content. What to say, what order, what to emphasise, what to avoid.

---

## Who you are talking to

Huawei internal stakeholders. Their three filters for any project:

1. **Does it drive GPU/NPU usage?** They want apps that make hardware work hard in daily real use — not benchmarks.
2. **Is it genuinely multi-modal?** Not "uses AI" — specifically multiple input/output modalities.
3. **Is there a business?** Not a research demo. Something people pay for, repeatedly.

Every answer you give should map back to one of these three. If you are talking about a feature and it does not connect to one of these three, skip it.

---

## The one sentence to open with

> "We built an AI coach that watches a player's practice video and tells them exactly what to fix — the same thing a human coach would say, but available to anyone, any time, for a fraction of the cost."

Do not open with technology. Open with the human problem. The technology follows.

---

## The three things managers need to hear, in order

**1. The problem is real and large.**
A good table tennis coach costs $60–120/hour. 300 million recreational racket sport players train regularly with zero coaching feedback. This is not a niche — it is an underserved mass market with a clear, daily pain.

**2. The AI is doing something real, not pretending.**
The key credibility moment: show one finding from the demo report that is specific, surprising, and demonstrably true. Not "your footwork could be better." Something like: "your elbow drops below your wrist on backswing in frames 1.5s, 3.1s, and 7.0s — this is why your stroke arc is too horizontal and you are producing a drive instead of a topspin." That specificity is what separates this from a chatbot. If they see that, they believe the rest.

**3. This is a subscription business, not a one-time tool.**
A player practices 4–5 times a week. Every session is a reason to use the app. Progress tracking means they stay — their data is here. This is the business model argument. Monthly recurring revenue from daily habits.

---

## The openJiuwen angle — say it simply

Do not say "multi-step agentic pipeline with tool calls." Say:

> "The app runs four AI stages in sequence — it observes the video, measures the body mechanics, writes the coaching findings, then checks its own work. openJiuwen orchestrates all four. The LLM cannot invent findings — it is forced to cite timestamps and measured values from the computer vision stage."

The last sentence is important. It answers the obvious objection ("couldn't ChatGPT just do this?") before it is asked.

---

## The Kirin NPU point — make it concrete

Do not say "heavy AI workload." Say:

> "Pose estimation runs at 30 frames per second for the full clip. That is up to 1,800 NPU inference calls per session. A committed player does this five times a week. Moving that inference on-device — onto Kirin — means no cloud, no latency, and a performance advantage that only works on Huawei hardware."

Concrete numbers. A specific advantage that is hardware-exclusive. That is what they want to hear.

---

## The demo flow — three beats, in this order

1. **Show the video** (10 seconds of real club training footage)
2. **Show the pipeline running** (progress screen, stages ticking through)
3. **Show one finding** (just one — the elbow-drops-on-backswing finding, with the timestamp citation and the measured angle)

Do not walk through the whole report. One finding, done well, is more convincing than five findings skimmed. The finding should be something a non-table-tennis person can still understand visually.

---

## The roadmap — frame it as a gap, not a wishlist

The wrong framing: "here are all the features we will build."
The right framing: "here is the specific gap between what works today and what a paying customer needs, and here is how we close it in three steps."

The three steps:
- **Phase 1** (4–6 weeks): make the demo output reliable every time, integrate openJiuwen pipeline, add session comparison
- **Phase 2** (6–10 weeks): cloud accounts, payment, first paying users
- **Phase 3** (3–5 months): Kirin on-device, voice coaching, expand to other sports

Emphasise Phase 1 is short. They can see results fast.

---

## What to avoid

- Do not lead with technology. Lead with the human problem.
- Do not show the full report in the demo. One finding, maximum two.
- Do not use the words "agentic platform" without immediately explaining what that means in plain terms.
- Do not make promises about training data or model improvement unless asked — it is true but it sounds like a hedge on current quality.
- Do not mention what the app cannot do yet (ball spin rate, racket angle). Only mention limitations if asked directly.

---

## The one question that will be asked

> "Why can't someone just use ChatGPT with video?"

Answer: "They can generate generic advice. They cannot tell you that your elbow dropped below your wrist at second 1.5 in your video, because that requires computer vision running before the LLM ever sees anything. The LLM in our pipeline is forced to cite measured evidence — it physically cannot produce a finding without a timestamp. That is the pipeline doing its job."

---

## What success looks like in the room

They ask: "How do we proceed?" or "What do you need from us?"

That means they are sold on the concept. The ask is four things: Phase 1 approval, openJiuwen API access, Kirin NPU SDK, and one UX/UI design pass. Have these ready as a clear list — do not improvise it.
