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

If they say yes, have the immediate next step ready: "Week 1 we set up the openJiuwen API integration. Week 2 we have the first end-to-end run through the platform. Week 4 we have something you can show to the next level up." Specificity about the near term is more credible than a Gantt chart.

---

## More objections — prepared answers

**"Why would someone pay for this when YouTube has free coaching videos?"**

YouTube shows you what good looks like. It cannot watch you and tell you what you specifically are doing wrong. A tutorial about backhand topspin mechanics cannot tell you that your elbow drops at second 1.5 in your video. That specificity to the individual is what people pay human coaches for — and what this app provides. YouTube is reference material. This is a mirror.

**"What if the AI analysis is wrong?"**

Two points. First, the pipeline has a verification stage that drops any finding not backed by measured evidence — it is designed to be conservative. Three accurate findings are more valuable than seven uncertain ones. Second, the limitation is disclosed in every report. If the camera angle is bad, the report says so. But the more important framing: we are not comparing the AI to a perfect observer. We are comparing it to zero feedback, which is what most players have today. Even if the AI misses one thing, it catches four others that the player would never have noticed alone.

**"Why table tennis? It seems niche."**

Table tennis has 875 million registered players globally. It is the world's most-participated sport by player count after swimming. In China specifically it is a national sport with deep cultural significance — this is not a coincidence for a Huawei product. And the engine is sport-agnostic: the same pipeline with different coaching rubrics covers tennis, badminton, padel, squash. Table tennis is the starting point because the stroke mechanics are clearest to measure with a standard side camera. The market is not table tennis — the market is AI coaching for physical skills.

**"How is this defensible? A larger player could copy this in three months."**

The technology is not the moat. The data is. Every session generates labelled training data: real player video, real coaching findings, real outcomes. After 100,000 sessions the model quality compounds in ways a new entrant cannot replicate quickly. Additionally, user retention creates structural lock-in: their session history, personal trends, progress comparisons — switching means losing their coaching record. The players who stay are the players who improve, and they attribute that improvement to the platform.

**"The market numbers seem optimistic."**

The $40M ARR figure assumes 0.1% of serious recreational table tennis players at $10/month. That is a conservative conversion rate for a product with genuine daily utility. The subscription is cheaper than a single coaching session. The more important number for Huawei is not the table tennis TAM — it is the pattern: AI agent, daily real-world use, NPU-intensive, expandable to any physical skill domain. Sports is just where we validated it first.

---

## Why now — the timing argument

This is worth having ready if asked, and worth offering even if not asked.

Three technologies had to converge before this product was possible:

1. **Mobile camera quality** sufficient for reliable body landmark detection at distance — only reached in the last 3–4 years
2. **On-device pose estimation** (MediaPipe) fast enough to process 30fps in real time — became viable in 2022–2023
3. **LLMs** capable of writing coherent, specific, grounded coaching prose — 2023 onwards

A year before we built this, the pipeline would have been too slow, too inaccurate, or too expensive to deliver a useful product. The window where all three are good enough is recent and narrow. The companies that move now build the data advantage. The companies that wait are buying into a more expensive and more competitive market.

---

## Data privacy — the Huawei-specific angle

On-device inference is not just a performance feature. For Huawei's markets it is a compliance and trust feature.

A cloud-based competitor requires uploading personal video — of people, their movements, their training sessions — to servers operated by third parties, potentially in foreign jurisdictions. With Kirin NPU on-device mode, the user's video never leaves their device. The coaching happens locally. This is a strong alignment with data sovereignty expectations in key markets and with Huawei's own positioning around secure, private AI.

Frame it as: "Our users' training videos stay on their phone. We do not see them, store them, or send them anywhere. That is only possible because Kirin is powerful enough to run the AI locally."

---

## What "agentic" means — explain it in ten seconds

Many people in the room may not know what agentic AI means. Do not assume they do. The explanation that works:

> "A regular AI app takes your input and gives you one output. An agentic app is one where the AI makes a chain of decisions itself — it decides what to do next at each step without you telling it. In our case: the AI decides what frames to sample from the video, what measurements to take, what findings are actually supported by those measurements, and which drills are relevant to the findings. The user just provides the video. Everything else is the agent working."

That is it. Do not go deeper unless they ask.

---

## The competitive landscape — be ready but do not volunteer it

There are real competitors. Know them, but do not bring them up unless asked.

- **Homecourt** (basketball): AI video coaching, US-based, has venture funding. Proof the category works, but basketball-specific and no openJiuwen/Kirin angle.
- **SwingVision** (tennis): Shot tracking and basic analysis. More data analytics than coaching. No LLM coaching layer.
- **Generic "LLM + video"**: Anyone can point GPT-4o at a sports video and ask for feedback. The output is generic because there is no CV pipeline feeding grounded measurements. This is the most common misconception about what we built.

If asked: "We are aware of Homecourt and SwingVision. They validate the market. The difference is that our findings are grounded in computer vision measurements — the LLM cannot make a claim without citing a measured value. That verification step is what separates a coaching report from a chatbot response."

---

## The honest thing to say about current quality

At some point someone will ask "how accurate is it really?" The wrong answer is to oversell. The right answer builds more trust:

> "High-confidence findings — where the CV has clear measurements — are accurate. Medium-confidence findings depend on camera conditions and we mark them clearly. We are conservative by design: the verification stage would rather drop a finding than include an unsupported one. The goal is that every finding in the report is something you could verify yourself by watching the video. If you disagree with a finding, the timestamps are right there."

Honesty about the confidence model makes the high-confidence findings more credible, not less.

---

## The Chinese market specifically

Table tennis in China is not a sport — it is culture. China has dominated international table tennis for decades. There are an estimated 300 million table tennis players in China alone. Huawei managers will understand this market intuitively in a way that requires no explanation.

This matters for the pitch because it means the first paying users are not an abstract number — they are a real, identifiable, culturally resonant community that already trains seriously and already spends money on equipment and coaching. The product fits into existing behaviour rather than trying to create new habits.

---

## If the demo fails or looks wrong

Have a fallback prepared. If the app has a technical issue during the demo:

1. The report JSON is pre-loaded and committed to the repo — you can show it directly as formatted text if the UI fails
2. The key finding (elbow drops on backswing, timestamp 1.5s/3.1s/7.0s, 88° measured elbow angle) can be stated from memory
3. "The demo is a working prototype, not a production app — rough edges are expected and Phase 1 addresses them" is an honest and reasonable thing to say

Do not apologise excessively for a technical glitch. Move past it quickly and keep the conversation on the ideas.
