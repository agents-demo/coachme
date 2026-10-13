# Simple Roadmap — from demo to real product

*A plain-English plan for management. One line per item. No jargon.*

---

## The product in one line

Film a training session and get back what to fix and how to practice — a coach you can replay.

## The core idea — it is multimodal

- It **watches** your video — a vision model reads the frames.
- It **reads** the numbers (movement, body, ball) it measured itself.
- It **writes** the coaching in plain words — and can **speak** it.
- It ties **pictures + numbers + words** together; every point points to a moment.

Most tools do **one sense** — pure computer vision, or pure text. This one does **all of them at
once**, which is why the advice reads like a coach, not a chart.

## The base — the multimodal core (already built)

Everything sits on these four senses. They are **done today**, which is why they are the floor every
item stands on — and what competitors don't have.

| Sense | What it does | Status |
|-------|--------------|:------:|
| **Watch** | A vision model reads the video frames | Done |
| **Read** | It uses the numbers (movement, body, ball) it measured itself | Done |
| **Write** | It writes the coaching in plain words | Done |
| **Speak** | It reads the report aloud | Done |

The **Senses** column in the item tables below shows **which senses each item uses or adds** — so
multimodality is visible on every relevant row.

## Where we are today

- A working demo exists: video goes in, a coaching report comes out.
- It runs on a normal computer; the video never leaves the machine.
- The report is honest — every point points to a moment in the video.

---

## The work, by workstream

Seven workstreams: two build stages (**Demo**, **Product**) and five market areas.

**Groups at a glance**

| # | Workstream | In one line | Type | Items |
|---|-----------|-------------|------|:---:|
| 1 | Demo | Make it show-ready. | Build stage | 8 |
| 2 | Product | Make it usable by strangers. | Build stage | 13 |
| 3 | Sharper analysis | Read the play more deeply. | Market area | 8 |
| 4 | Match play | Score and call a real game. | Market area | 3 |
| 5 | Live & mobile | Use it on a phone, in the moment. | Market area | 3 |
| 6 | Coaches & teams | Work with a coach or a team. | Market area | 5 |
| 7 | Improve over time | Track progress and plan. | Market area | 6 |

**Senses legend:** **Watch** = vision reads the frames · **Read** = uses its own numbers ·
**Write** = language · **Speak** = voice out · **Listen** = voice in · **—** = no new sense.

### Workstream 1 — Demo  *(stage: show-ready)*

| # | Item | Senses |
|---|------|--------|
| 1 | One demo clip + a clear "before/after" story | Watch · Write |
| 2 | Make every screen clean | — |
| 3 | Sample footage that always works | — |
| 4 | A short guided tour | Watch · Write |
| 5 | Reliable runs (no mid-demo crashes) | — |
| 6 | Saved-result fallback | — |
| 7 | Plain, simple wording | — |
| 8 | Rehearse end to end | — |

### Workstream 2 — Product  *(stage: beta)*

| # | Item | Senses |
|---|------|--------|
| 9 | Accounts + log-in | — |
| 10 | Easy phone upload | — |
| 11 | Hosted — nothing to install | — |
| 12 | Progress over time | Read |
| 13 | Guide users to film well | — |
| 14 | Private + one-click delete | — |
| 15 | Session feedback (like / dislike) | — |
| 16 | Track and limit cost per session | — |
| 17 | More sports | Watch |
| 18 | More languages | Write |
| 19 | Coach / team view | — |
| 20 | **Ask by voice — hear the answer** | Speak · Listen |
| 21 | **Keep it multimodal: photo + video in, text + speech out** | Watch · Write · Speak |

### Workstream 3 — Sharper analysis  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 22 | Name the shot (forehand / backhand / serve) | Watch · Write |
| 23 | Estimate shot speed | Watch |
| 24 | 3D body mechanics (how the body moves in sequence) | Watch |
| 25 | Split a session into rallies automatically | Watch |
| 26 | Feedback per stroke, not just per session | Watch · Write |
| 27 | Footage-quality check + how to film better | Watch |
| 28 | Spin — only if it can be done honestly | Watch |
| 29 | **Understand audio too — voice notes, racket sound** | Listen |

### Workstream 4 — Match play  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 30 | Automatic scoring | Watch |
| 31 | In/out line calls (reviewable) | Watch |
| 32 | Match statistics | Read · Write |

### Workstream 5 — Live & mobile  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 33 | Phone app | Watch |
| 34 | Live feedback while playing | Watch · Speak |
| 35 | **Spoken cues during playback** | Speak |

### Workstream 6 — Coaches & teams  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 36 | Coach / team accounts | — |
| 37 | Share one session with a coach | Write |
| 38 | Compare your motion to a pro's | Watch |
| 39 | Track more than one player | Watch |
| 40 | Use two cameras | Watch |

### Workstream 7 — Improve over time  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 41 | Skill ratings per area | Read · Write |
| 42 | A weekly plan from your history | Write |
| 43 | Challenges + leaderboards | — |
| 44 | Injury / training-load awareness | Read |
| 45 | Sync across phone and computer | — |
| 46 | Connect to watches and health apps | Watch (sensor) |

*Details, effort sizes and ordering are in the full plan: [ROADMAP.md](ROADMAP.md).*

---

## What could go wrong (and the plan)

- **Bad video gives bad advice** → guide users on filming; warn when the clip is poor.
- **Costs grow with usage** → measure and cap the cost per session.
- **Video is personal data** → keep it local by default; clear consent; easy delete.
- **Promising too much** → stay honest; every claim ties to the video.

## Rough timing

- **Workstream 1 — Demo:** a few weeks.
- **Workstream 2 — Product:** a few months.
- **Workstreams 3–7 — market areas:** ongoing.

## The one thing to remember

The pipeline works and is honest. Our edge is that it is **multimodal** — it watches, reads its own
numbers, writes, and speaks — and the remaining work is mostly **polish, packaging, and scale**.
