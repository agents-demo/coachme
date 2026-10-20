# CoachMe — 12-Minute All-to-All Demo Scenario

> **Presenter note:** Michael is the player in the demo clip. Use that. The pitch is
> stronger as a first-person story: “This is me playing. The report is about my
> technique. I can verify the findings myself.”

---

## The rule

**Minimal orientation, then demo. Context second. One-pager answers third.**

Give the room only enough to know what they are about to watch: what the app does,
who is in the clip, and what to look for. Then open the app and let the report do the
selling. Use the one-pager as the answer key for questions, not as the agenda.

**One narrative:** one player -> one real clip -> one evidence-backed finding -> one
drill -> one product path.

**Do not run a live analysis.** Use the preloaded Michael session. A fresh Guided
run can take minutes. The demo must be reliable in the room.

---

## Run of show

| Time | Focus |
|---|---|
| 0:00-0:50 | Minimal orientation: what CoachMe does, who is in the clip |
| 0:50-1:10 | "This is me" - open the session |
| 1:10-3:40 | Personal demo: video -> one finding -> drill -> Ask |
| 3:40-5:00 | "What you just saw": my problem, target user, value |
| 5:00-6:25 | Market, competition, Huawei/Ascend angle |
| 6:25-8:05 | Demo-to-product |
| 8:05-12:00 | All-to-all Q&A and close |

**10-minute cut:** keep the 40-second orientation and the demo, skip Android,
compress market to 45 seconds, and keep the same close.

---

## 0:00-0:50 - Minimal orientation, then make it personal

Do not start with a full company story. Give only three sentences.

> "CoachMe is an AI coaching app for racket sports. You give it a practice video, and
> it gives back a coaching report: what to fix, the exact moment it happened, and
> which drill to use. I'm going to show you that on a real clip, and the player in
> the clip is me."

Then:

> "In the next three minutes, I'll show you one clip, one finding and one drill. Then
> I'll explain the problem, the market and how this becomes a product."

Open Sessions -> **Michael Osher - Backhand Topspin Drill**.

> "This is my session. Let's look at what it found."

No architecture, no market numbers, no roadmap yet. Just enough orientation to make
the demo legible.

---

## 0:50-3:40 - Personal demo

### Sessions

> “These are my real sessions. Michael is me.”

### Video tab

Show the clip, skeleton overlay and motion map.

> “That’s my backhand drill. The app measured my pose and movement before the model
> wrote anything.”

Scrub once. Do not play the whole clip.

### Coaching → Advice

Show **one finding only**.

> “The app flagged that my elbow drops below wrist level at 1.5, 3.1 and 7.0
> seconds. I know this drill. I thought my backswing was fine. I did not notice this
> until the report showed me. That is why my stroke arc is flat.”

Pause.

> “And because it’s me, I can tell you whether the finding is right. It is.”

That is the credibility moment. Do not read all seven findings.

### Coaching → Practice

Open one drill and tick it.

> “This is the drill I would do next: shadow loops with the elbow at waist height,
> brushing upward, finishing at chin height.”

### Ask

Open **Ask**. Use one predefined question:

> “What should I focus on next session?”

When the answer appears, switch to **Video** or **Analysis** while the panel stays
open.

> “I can keep reviewing my own session and ask questions in context.”

Close the panel.

### Android

Optional, 15 seconds. Show the phone or one screenshot.

> “The same report model runs on Android, on-device and local-first.”

---

## 3:40-5:00 - What you just saw

Now explain the demo.

### Problem

> “I train several times a week. I have a coach, but not for every session. I
> already film myself, but reviewing my own footage is slow and I don’t always know
> what to look for. Generic AI tells me generic things. This told me something
> specific about my own movement.”

### Target user

> “I am user zero: a serious amateur who trains regularly, films himself, and wants
> to improve between lessons.”

Then widen:

> “There are tens of millions of players like me. Parents of juniors are the other
> buyer. Coaches and clubs are the multiplier: one coach brings 10–20 active users.”

### Value

> “For the player: what to fix, which drill, and whether it improved. For the coach:
> leverage. The AI does the watching; the coach does the coaching. We are not
> replacing coaches.”

### Differentiator

> “Every claim has a timestamp and a measured value. Unsupported claims are dropped.
> In the advanced mode, the model also decides what to inspect — but it still cannot
> produce a finding without tool evidence.”

**Current demo:** 7 findings and 6 drills. Do not quote the one-pager’s stale
“5 findings.”

---

## 5:00-6:25 - Market, competition, Huawei

### Market

- **China first:** ~85M daily club players, ~10M competitive. Parents are the buyer
  for juniors.
- **Global:** ~300M table-tennis players; 500M+ across racket sports.
- **Serviceable:** ~40M serious table-tennis players worldwide.

Use planning ranges, not audited precision.

### Competition

- **SwingVision:** validates the category, but Apple-only — no Android, no China.
- **Sportsbox / Onform:** deep mechanics, golf-first.
- **HomeCourt:** strong basketball tracking, not racket sports.
- **V1 / Hudl / Veo:** coach and team review, less automated consumer coaching.
- **Generic AI:** broad language ability, no reliable sport-specific measurement.
- **PingPi:** direct China competitor in table-tennis video analysis.
- **ByteDance / Douyin:** distribution threat if they prioritise coaching.

Do not volunteer the full list unless asked.

**Differentiator:** the full loop — measurement → plain-language coaching → drills →
progress — with every claim tied to evidence.

### Huawei / Ascend

> “Every session is recurring inference: pose, ball, vision and LLM. Those batches
> can run on Ascend 310/310P; training can run on Ascend 910-class systems. The app
> works without Ascend, but real usage creates the workload Ascend is built for.”

> “The app is backend-agnostic. The user sees the coaching, not the engine.
> openJiuwen is the Huawei deployment path; repeated usage becomes recurring
> inference and training demand.”

---

## 6:25-8:05 - Demo-to-product

### Now

Working local prototype: web + Android, real coaching report, measured evidence,
drills and session history.

### Next: make the demo undeniable

- Harden Standard so output is always specific, never generic
- Finish the benchmark and coach labels
- Add mode selection, cancellation and session comparison
- Move toward 60-second analysis
- Keep Investigator opt-in while it is validated

### Then: first paying users

- Accounts and sync
- Payments and subscriptions
- Coach workspace and share links
- iOS after retention is proven
- First consumer and club users in China

### Later: platform

- Table detection and stroke classification
- Voice coaching and audio input
- Tennis, badminton and padel
- Live feedback between points
- Ascend cloud/edge deployment
- API and white-label for hardware partners and federations

### China entry sequence

1. WeChat MiniProgram — upload inside WeChat, no app-store install
2. Android apps for Huawei AppGallery and top Chinese stores
3. AppGallery partnership and Ascend co-marketing

Pricing in China: RMB 30–50/month, not a USD conversion.

---

## 8:05-12:00 - All-to-all Q&A and close

Open the room:

> “What would you challenge first: the evidence quality, the China go-to-market, or
> the path to Ascend?”

Then close with the four asks:

1. **Phase 1 approval**
2. **Evaluation clips and coach labels**
3. **Ascend/CANN access and deployment guidance**
4. **One UX/UI design pass**

If they ask “how do we proceed?”, have the near-term answer ready:

> “Week 1: openJiuwen API integration. Week 2: first end-to-end run through the
> platform. Week 4: something you can show to the next level up.”

---

## One-pager answer key

| Question | Short answer |
|---|---|
| **1. Demo name** | CoachMe — an AI coaching team for racket sports. Today: table tennis. Vision: a multimodal practice companion for players, coaches and clubs. |
| **2. Short description** | Upload a practice clip. Get what to fix, the exact timestamp, and the drill. Every finding is grounded in measured evidence. |
| **3. Problem** | Coaching is scarce and expensive; video review is manual; generic AI is untrustworthy; progress is hard to see. |
| **4. Users** | Serious amateurs 18–45 and parents of juniors. Coaches and clubs are the growth multiplier. China first. |
| **5. Value** | Player: a specific practice decision. Coach: leverage — the AI does the watching, the coach does the coaching. |
| **6. Market** | China ~85M daily club players, ~10M competitive; ~300M table-tennis players globally; 500M+ racket-sport participants. |
| **7. AI domain** | Multimodal video, pose, ball tracking, LLM report generation, progress comparison. Standard is the reliable fixed pipeline; Investigator is opt-in adaptive investigation. |
| **8. Competitors** | SwingVision (Apple-only), Sportsbox/Onform (golf-first), HomeCourt (basketball), V1/Hudl/Veo (coach tools), generic AI, PingPi, ByteDance. Differentiator: evidence-backed full loop. |
| **9. Potential product** | Consumer practice companion → coach/club workspace → API and white-label. China: WeChat MiniProgram → Android stores → AppGallery. |
| **10. Open source** | Foundation and reproducible evaluation → coach channel → sharper coaching → live/multi-sport → ecosystem. Local-first video, consent for minors, deletion, cost caps, disclosed limits. |

---

## Objection answers

### “Why can’t someone just use ChatGPT with video?”

> “It can generate generic advice. It cannot tell you your elbow dropped below your
> wrist at 1.5 seconds, because that requires a CV pipeline running before the LLM
> sees anything. Standard mode forces measured evidence; Investigator must cite tool
> evidence.”

### “How accurate is it?”

> “High-confidence findings are grounded in clear measurements; medium-confidence
> findings depend on camera conditions and are marked. The verification stage drops
> unsupported claims. We are compared with zero feedback, not with a perfect human
> observer.”

### “Why table tennis? It seems niche.”

> “300M recreational players globally, 85M daily club players in China, and the
> cleanest mechanics to measure with a side camera. The engine transfers to tennis,
> badminton and padel.”

### “How is this defensible?”

> “The technology is not the moat. The session history and labelled coaching
> outcomes are. Progress tracking creates retention, and retention creates data a
> new entrant cannot copy quickly.”

### “Is Investigator ready?”

> “No, and we do not present it as ready. Standard is the reliable product today.
> Investigator is opt-in while the benchmark runs.”

### “What if the AI is wrong?”

> “The pipeline is conservative by design: unsupported findings are dropped, and
> confidence is shown. If the camera angle is bad, the report says so. The
> comparison is not AI versus a perfect coach; it is feedback versus no feedback.”

### “Why would someone pay when YouTube is free?”

> “YouTube shows you what good looks like. It cannot tell you that your elbow drops
> at second 1.5 in your video. YouTube is reference material. This is a mirror.”

---

## Guardrails

- Keep the personal story to 15–20 seconds per beat. Do not turn it into a long
  autobiography.
- Be self-critical once, not repeatedly. “I didn’t notice my elbow” is enough.
- Do not say “the AI is always right.” Say: “This finding is right, and I can check
  it because it’s my clip.”
- Do not claim medical or injury advice. Keep it technical.
- Do not lead with architecture. Lead with the player and the finding.
- Do not read the full report. One finding, maximum two.
- Do not show Diagnostics unless asked.
- Do not call Standard mode “agentic.”
- Do not promise training-data improvements unless asked.
- Do not mention ball spin, racket angle or live mode as present capabilities.

---

## If the demo fails

1. Switch to the preloaded report JSON or a screenshot.
2. State the key finding from memory: “Elbow drops below wrist at 1.5, 3.1 and 7.0
   seconds; that is why the arc is flat.”
3. Say: “This is a working prototype; Phase 1 closes the remaining rough edges.”
4. Do not debug live.

---

## Pre-flight checklist

- [ ] Web app running at `http://127.0.0.1:8000/gui2/`
- [ ] Michael session is first in Sessions
- [ ] Ask panel is closed
- [ ] Browser zoom is readable on the room display
- [ ] Volume is at a sensible level; answers speak only after an explicit question
- [ ] Android app installed and openable as backup
- [ ] One-pager open in a background tab for exact numbers
- [ ] No live analysis planned
- [ ] Close the loop with the four asks
