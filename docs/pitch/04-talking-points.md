# Pitch Talking Points — Huawei Internal Managers

These are the strategic insights for the conversation, not slide content. What to say, what order, what to emphasise, what to avoid.

---

## Who you are talking to

Huawei internal stakeholders. Their three filters for any project:

1. **Does it drive GPU/NPU usage?** They want apps that make hardware work hard in daily real use — not benchmarks.
2. **Is it genuinely multi-modal?** Not "uses AI" — specifically multiple input/output modalities.
3. **Is there a business?** Not a research demo. Something people pay for, repeatedly.

Every answer you give should map back to one of these three. If you are talking about a feature and it does not connect to one of these three, skip it.

## The Huawei win-win - app first, Ascend second

Managers do not buy one app; they want many apps that create recurring accelerator demand. The app must stand on user value first: if players do not use it, there is no compute. If it works, every session is inference and every improvement cycle is a training opportunity that can run on Ascend.

openJiuwen/Ascend integration makes that deployment path easy. The app is deliberately backend-agnostic: that is a strength: Huawei can choose the compute layer without changing the user experience.

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

Do not call the fixed pipeline "agentic" and leave it there. Say:

> "The app is backend-agnostic: the user sees the coaching, not the engine. The reliable product runs a fixed pipeline today. Investigator mode goes further: the model chooses which tools and windows to inspect, may ignore ball tracking if irrelevant, and must cite evidence returned by a tool. openJiuwen is our Huawei deployment path; when paired with Ascend, repeated usage becomes recurring inference and training demand."

The last sentence answers the obvious objection ("couldn't ChatGPT just do this?") before it is asked. Be clear that the fixed pipeline is the baseline and Investigator remains opt-in while the benchmark runs.
---

## The Ascend point - make it concrete

Do not say "heavy AI workload." Say:

> "Pose estimation runs at 30 frames per second for the full clip. That is up to 1,800 inference calls per session, and a committed player does this five times a week. Those batches can run on Ascend 310/310P inference hardware through CANN; models can be trained on Ascend 910-class systems. That is a real, recurring Ascend workload, not a benchmark."

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
- **Phase 1** (4-6 weeks): make Standard reliable every time, harden Investigator, add session comparison
- **Phase 2** (6–10 weeks): cloud accounts, payment, first paying users
- **Phase 3** (3-5 months): Ascend cloud/edge deployment, voice coaching, expand to other sports

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

Answer: "They can generate generic advice. They cannot tell you that your elbow dropped below your wrist at second 1.5 in your video, because that requires computer vision running before the LLM sees anything. In the reliable Standard mode the model is forced to cite measured evidence. In Investigator mode it also chooses what to examine - but it still cannot produce a finding without a tool evidence ID. That is the difference between a pipeline and a chatbot."

---

## What success looks like in the room

They ask: "How do we proceed?" or "What do you need from us?"

That means they are sold on the concept. The ask is four things: Phase 1 approval, evaluation clips and coach labels, Ascend/CANN access, and one UX/UI design pass. Have these ready as a clear list — do not improvise it.

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
For Huawei markets, deployment control matters as much as the model.

A cloud-only competitor requires uploading personal video - of people, their movements, their training sessions - to servers operated by third parties, potentially in foreign jurisdictions. Topspin can offer two modes: a **local-first** mode where the clip stays on the device, and a **hosted** mode running on **Ascend in a private or regional cloud**, under the operator's control. These are different deployment choices, not the same privacy claim.

Frame it as: "Clubs can keep video local. Hosted deployments can run on Ascend in-region, under your control. We do not require a foreign cloud to make this work."
---

## What "agentic" means — explain it in ten seconds

Many people in the room may not know what agentic AI means. Do not assume they do. The explanation that works:

> "A regular AI app takes your input and gives you one output. In Investigator mode, the model makes a chain of decisions itself: it chooses what to measure, what to look at next, what evidence is sufficient, and when to stop. The reliable Standard mode does not do that - it follows a fixed pipeline. Investigator is the mode where the model is actually in control."

That is the differentiator. Do not describe the fixed pipeline as agentic. Do not go deeper unless they ask.
---

## The competitive landscape — be ready but do not volunteer it

There are real competitors. Know them, but do not bring them up unless asked.

- **Homecourt** (basketball): AI video coaching, US-based, has venture funding. Proof the category works, but basketball-specific and no openJiuwen/Ascend angle.
- **SwingVision** (tennis): Shot tracking and basic analysis. More data analytics than coaching. No LLM coaching layer.
- **Generic "LLM + video"**: Anyone can point GPT-4o at a sports video and ask for feedback. The output is generic because there is no CV pipeline feeding grounded measurements. This is the most common misconception about what we built.

If asked: "We are aware of Homecourt and SwingVision. They validate the market. The difference is that our findings are grounded in computer vision measurements — the LLM cannot make a claim without citing a measured value. That verification step is what separates a coaching report from a chatbot response."

---

## Talking about quality

At some point someone will ask "how accurate is it really?" The wrong answer is to oversell. The right answer builds more trust:

> "High-confidence findings — where the CV has clear measurements — are accurate. Medium-confidence findings depend on camera conditions and we mark them clearly. We are conservative by design: the verification stage would rather drop a finding than include an unsupported one. The goal is that every finding in the report is something you could verify yourself by watching the video. If you disagree with a finding, the timestamps are right there."

Clear confidence levels make the high-confidence findings more credible.

---

## The Chinese market specifically

Table tennis in China is not a sport — it is culture. China has dominated international table tennis for decades. There are an estimated 300 million table tennis players in China alone. Huawei managers will understand this market intuitively in a way that requires no explanation.

This matters for the pitch because it means the first paying users are not an abstract number — they are a real, identifiable, culturally resonant community that already trains seriously and already spends money on equipment and coaching. The product fits into existing behaviour rather than trying to create new habits.

---

## If the demo fails or looks wrong

Have a fallback prepared. If the app has a technical issue during the demo:

1. The report JSON is pre-loaded and committed to the repo — you can show it directly as formatted text if the UI fails
2. The key finding (elbow drops on backswing, timestamp 1.5s/3.1s/7.0s, 88° measured elbow angle) can be stated from memory
3. "The demo is a working product prototype; Phase 1 closes the remaining rough edges" is a clear and reasonable thing to say

If a technical glitch happens, keep composure and return quickly to the ideas.

---

## Meeting dynamics — how Huawei internal meetings actually work

This is different from a Western startup pitch. Several specific things to know:

**Do not expect a "yes" in the room.** Chinese internal business meetings are consensus-building events, not decision events. The manager present may be genuinely interested but will want to discuss with peers or a senior before committing. A successful meeting ends with "this is interesting, I want to share it with [name]" — not a signed approval. Do not interpret the absence of immediate commitment as rejection.

**There is usually one person whose opinion matters more than everyone else's.** Read the room in the first five minutes. When that person speaks, everyone else listens. Direct your most important points toward them without being obvious about it. If they nod or ask a follow-up question, that is the signal.

**Questions are a good sign. Silence is harder to read.** If managers are asking questions, they are engaged. In Chinese business settings, polite silence or very few questions can mean either deep thought or polite disengagement. Do not rush to fill silence — let them process. If the silence extends, ask a direct question to re-engage: "Does this match what you have seen in the market?"

**Never put anyone in a position where they must admit they do not know something.** Explain technical concepts as information-sharing, not as tests. "You may already know this, but..." is better than a question that requires an answer.

**Measured confidence, not American-style enthusiasm.** Huawei internal culture values precision and understatement over excitement. Claim what you can prove. Acknowledge what remains to validate. This builds more credibility than projecting certainty everywhere.

---

## The openJiuwen deployment point

State this clearly and move on.

The Investigator mode is where the model owns the investigation; it remains opt-in while the benchmark is completed. If a manager asks to see openJiuwen in action, the answer is:

> "The app runs on openJiuwen today. Standard mode is the reliable fixed pipeline. Investigator is the next step: the model chooses tools and windows, while every finding must cite measured evidence. It stays opt-in until the benchmark confirms better outcomes."

The sequencing is deliberate: working product first, platform scale second.
---

## The openJiuwen platform play — what this means beyond one app

There is a strategic argument for Huawei that goes beyond "this is a useful sports app."

Every successful commercial application built on openJiuwen makes the platform more valuable and more credible to other developers. This is a classic platform dynamic: the first working consumer product on a developer platform is not just a product — it is proof that the platform is capable of powering real commercial applications.

If Huawei can say to other developers "here is a working consumer product with real users, built on openJiuwen," that is a fundamentally different pitch than "here is a platform that could theoretically enable applications."

This app could be the reference implementation that opens a developer ecosystem. Frame it to managers who care about openJiuwen adoption: you are not asking them to support one sports app. You are asking them to create the platform's first proof point in the consumer vertical AI market.

---

## The B2B coach tier — the biggest growth opportunity, often overlooked

The Pro individual subscription ($8–12/month) is the steady revenue base. But the Club tier ($40–80/month per coach) is where the growth multiplier lives.

The dynamic: a player uses the app and gets a specific report. They show it to their coach. "Look what the AI found about my backhand." Two things can happen:
1. The coach is impressed — they want to use the app for all their students. One Club subscription brings in 10–20 student users.
2. The coach is sceptical about one finding — the player and coach watch the video together. If the coach confirms the finding, the player's trust in the app doubles.

Either outcome benefits the product. But the first outcome creates a growth engine: sports coaches are a concentrated, reachable sales channel. One conversation with a club director converts the whole club. The unit economics of acquiring a Club customer are far better than acquiring 20 individual Pro customers.

This growth loop — player → report → shows to coach → coach converts students — is built into the product, not added as a marketing layer.

---

## Tell the story of one user over three months

Abstract metrics do not land in a meeting. A specific user story does.

> "A player comes home from Tuesday practice. They record 10 minutes of their session. The app tells them their elbow drops on backswing — with the timestamp, the measured angle, the specific drill to fix it. On Thursday they run the drill. The following Tuesday they record again. The elbow measurement improved from 88° to 97°. They can see it. Three months later their club coach notices their backhand has gotten sharper. They attribute it to the app. They are still subscribing."

That story makes churn, LTV, and daily retention into something a person can visualise. It also answers the implicit question every manager has: "Would I or someone I know actually use this?"

Note what makes this story work: the player is not coming back because the app sent them a push notification. They are coming back because they want to see if they got better. That is intrinsic motivation created by measurement — the app's core mechanic, not a retention trick.

---

## What they are silently comparing this against

Internal managers are always unconsciously asking: "instead of this, what else could we do?" Know the implicit alternatives:

**"Build something like this internally."** Means no external users, no market validation, much higher cost, much longer timeline. This team built a working version without corporate resources first. That signals efficiency. You are not asking for the team to build — you are asking the platform to support what already exists.

**"Wait and see if the market develops."** The data moat builds daily. Whoever accumulates user sessions first builds a compounding quality advantage. Waiting means buying into a more expensive and more competitive market in 12–18 months.

**"Partner with an existing player (Homecourt, etc.)."** Existing players are Western-built, running on competing AI infrastructure, and have no alignment with openJiuwen or Ascend. Partnership serves none of the platform goals.

The implicit reframe: you are not asking for funding to build a concept. The concept is built and working. You are asking for platform access to the thing that already exists.

---

## The incremental commitment strategy

The four asks are not equally urgent. If you sense hesitation, do not withdraw the whole ask — narrow it.

The critical path is exactly two things: Phase 1 approval and the evaluation/coach-label set. These two unblock everything. Ascend/CANN deployment is months away (Phase 3). The UX design pass is useful but not blocking.

If the room feels uncertain, offer the minimum viable green light:

> "The only thing we need to start is Phase 1 approval and the first evaluation set. We can show you a working Investigator mode with measured evidence in four weeks. Everything else - NPU SDK, design resources - we can discuss after you've seen that."

Lower the activation energy. Let them say yes to the small thing. A small yes leads to a larger yes after Phase 1 delivers.

---

## The broader vision — say it once, do not dwell

At some point the "where does this go in 5 years" question arises, or deserves one pre-emptive sentence.

The one sentence: "Sports coaching is where we are validating the pattern — record yourself doing a physical skill, AI watches, gives grounded specific feedback. The same pattern applies to music, physical therapy, language pronunciation, surgical training. We are starting where the outcomes are most objectively measurable. But the platform opportunity is everything humans learn by doing."

Say it once. Let it land. Come back immediately to table tennis and Phase 1. The vision gives scale without replacing the focus.

---

## What you want them saying to each other after you leave

When the managers talk among themselves after the meeting, you want the conversation to be:

- "The demo found something specific about a real player. It wasn't generic."
- "The market is bigger than I expected. I didn't know table tennis was that large in China."
- "Phase 1 is short. The ask is small relative to the potential."
- "The product already works. They are not asking us to build something."

If you hear any of those four things come back to you, the meeting worked.

The conversation you do not want: "Interesting technology but unclear who pays for this" or "Impressive demo but I'm not sure it works in real conditions." Pre-answer both: the paying customer is the serious recreational player who already spends money on coaching and equipment, and the demo report is based on real footage from a real training session.

---

## Things that earn respect vs things that lose it

**Earn respect:**
- Knowing exactly what the app cannot do yet, stated confidently - signals maturity
- Specific numbers (not "many players" — "875 million globally, 300 million in China")
- Clear communication about current quality versus roadmap
- Having thought about what failure looks like and how you'd handle it
- Having built the thing before asking for support

**Lose credibility:**
- Vague claims ("our AI is very powerful") without demonstration
- Inability to explain how the pipeline works in plain language
- Not knowing who the specific first target paying customer is
- Asking for too much at once without prioritising
- Showing every feature in the demo — signals the product has no focus

---

## The real moat is data, not technology

The technology — pose estimation, LLM calls, ball tracking — is copyable. A well-funded competitor replicates it in 6 months. Do not lead with technology as the competitive advantage.

The real moat: a coaching knowledge base validated against real sessions, where coaches correct the AI's findings, add edge cases, and confirm which drills produce improvement. That database compounds over time. After 10,000 sessions, the finding accuracy and drill relevance are things a new entrant cannot replicate quickly regardless of engineering budget.

When asked about defensibility, the strongest answer is not "our algorithm is good." It is: "Every session trains the next one. The longer we run, the harder we are to replace — not because the technology is patented, but because the validated coaching knowledge is ours."

---

## The Ascend latency argument - edge first
The on-device latency argument is usually framed as privacy. That is true but it is the weaker version.

The stronger version: **cloud round-trips can make real-time coaching impossible. Inference has to sit close to the player.**

A public-cloud call can take 1-3 seconds. Between points, the total window is 10-15 seconds. A round-trip plus processing can consume that window before coaching reaches the player. **Ascend 310 inference at the edge or in a private venue cloud** removes the internet round-trip. True on-device inference is a separate, later optimization.

Say it as: "Ascend is the right platform for batch session analysis and model training. For live coaching, the inference has to move to the edge or the device. The same vision stack can be deployed across that continuum."
---

## The coach is the customer, not the player

A player might use the app three times. A coach with 20 students needs it every week and has institutional budget — club, academy, or school — to pay for tools that systematically improve student outcomes.

This is not a nuance. It is the primary revenue model. Individual player subscriptions are the long tail. The coach is the concentrated, reachable, motivated customer.

Coaches have three things players do not:
1. **Budget** — they already spend on software, video tools, and analysis aids
2. **Systematic motivation** — their professional reputation is tied to player improvement
3. **Volume** — one coach conversion brings 10–20 active users

This also changes how you pitch. If you are pitching to a player, you are pitching convenience. If you are pitching to a coach, you are pitching professional capability — "this makes you better at your job." That is a different conversation with a different willingness to pay.

---

## The AI makes the coach smarter — never positions itself as replacing them

A coach with 20 students cannot watch 20 students' training sessions every week. They rely on what they see in the 60 minutes together. The AI watches the sessions the coach cannot attend and surfaces the specific patterns the coach would have spotted in 10 sessions — before the first session.

This is the framing that gets coach adoption: **the AI is the coach's analytical instrument, not their replacement.** It watches more video, catches more patterns, and presents findings for the coach to confirm or override. The coach gets credit for the improvement. The AI made them faster and sharper.

Every piece of product language directed at coaches should be: "Your AI assistant" — not "AI coaching." The distinction matters to a coach's professional identity and is the difference between adoption and rejection.

---

## Turn current gaps into milestones

Every current gap maps directly to a concrete product milestone:

- "Video robustness" -> Phase 1: handle more lighting, angles and multi-player clips
- "Stroke coverage" -> Phase 1: detect and adapt to stroke switches
- "Session comparison" -> Phase 2: longitudinal tracking and progress trends
- "Live coaching" -> Phase 3: edge/on-device inference; Ascend for cloud/edge batches

State each gap once, then give the milestone that closes it. This shows you know exactly what is missing, have a concrete plan for each gap, and the Phase 1 ask is short enough to show progress fast.

The demo proves the concept; the roadmap turns it into a product. The path is specific, not aspirational.
