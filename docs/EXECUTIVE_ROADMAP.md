# Simple Roadmap — from demo to real product

*A plain-English plan for management. One line per item. No jargon.*

---

## The product in one line

Film a training session and get back what to fix and how to practice — a coach you can replay.

## The core idea — it is multimodal (in and out)

It doesn't just *read* video and *write* text — it works across senses in **both directions**:

**Takes in**
- **Watch** — reads **video/photos** (a vision model reads the frames).
- **Read** — reads **its own numbers** (movement, body, ball; later sensors).
- **Listen** — hears **audio**, e.g. a coach's spoken notes *(planned)*.

**Puts out**
- **Write** — writes **text**: the coaching in plain words.
- **Speak** — speaks **audio**: it reads the report aloud.
- **Show** — shows **video & images**: highlight clips, overlays, share cards.

Most tools do **one sense** (pure vision, or pure text). This one **watches, reads and listens — then
writes, speaks and shows**, all tied to the moments in your clip.

## The base — the multimodal core (mostly built)

These are the six senses. Five are **done today**; *Listen* is the one new one to add.

| Sense | Direction | Medium | What it does | Status |
|-------|:---------:|--------|--------------|:------:|
| **Watch** | In | Video / photos | A vision model reads the video frames | Done |
| **Read** | In | Its own numbers | Reads the movement/body/ball numbers it measured | Done |
| **Listen** | In | Audio | Hears a coach's notes, racket sounds | Planned |
| **Write** | Out | Text | Writes the coaching in plain words | Done |
| **Speak** | Out | Audio | Reads the report aloud | Done |
| **Show** | Out | Video / images | Highlight clips, overlays, share cards | Done |

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

**Senses legend:** **Watch** / **Read** / **Listen** = in · **Write** / **Speak** / **Show** = out ·
**—** = no new sense.

### Workstream 1 — Demo  *(stage: show-ready)*

| # | Item | Senses |
|---|------|--------|
| 1 | One demo clip + a clear "before/after" story | Watch · Write |
| 2 | Make every screen clean | — |
| 3 | Sample footage that always works | — |
| 4 | A short guided tour | Watch · Write · Show |
| 5 | Reliable runs (no mid-demo crashes) | — |
| 6 | Saved-result fallback | — |
| 7 | Plain, simple wording | Write |
| 8 | Rehearse end to end | — |

### Workstream 2 — Product  *(stage: beta)*

| # | Item | Senses |
|---|------|--------|
| 9 | Accounts + log-in | — |
| 10 | Easy phone upload | — |
| 11 | Hosted — nothing to install | — |
| 12 | Progress over time | Read · Show |
| 13 | Guide users to film well | — |
| 14 | Private + one-click delete | — |
| 15 | Session feedback (like / dislike) | — |
| 16 | Track and limit cost per session | — |
| 17 | More sports | Watch |
| 18 | More languages | Write |
| 19 | Coach / team view | Show |
| 20 | **Ask by voice — hear the answer** | Speak · Listen |
| 21 | **Keep it multimodal: photo + video in, text + speech out** | Watch · Write · Speak |

### Workstream 3 — Sharper analysis  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 22 | Name the shot (forehand / backhand / serve) | Watch · Write |
| 23 | Estimate shot speed | Watch |
| 24 | 3D body mechanics (how the body moves in sequence) | Watch · Show |
| 25 | Split a session into rallies automatically | Watch |
| 26 | Feedback per stroke, not just per session | Watch · Write |
| 27 | Footage-quality check + how to film better | Watch |
| 28 | Spin — only if it can be done honestly | Watch |
| 29 | **Understand audio too — voice notes, racket sound** | Listen |

### Workstream 4 — Match play  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 30 | Automatic scoring | Watch · Show |
| 31 | In/out line calls (reviewable) | Watch · Show |
| 32 | Match statistics | Read · Write |

### Workstream 5 — Live & mobile  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 33 | Phone app | Watch · Show |
| 34 | Live feedback while playing | Watch · Speak · Show |
| 35 | **Spoken cues during playback** | Speak |

### Workstream 6 — Coaches & teams  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 36 | Coach / team accounts | — |
| 37 | Share one session with a coach | Write · Show |
| 38 | Compare your motion to a pro's | Watch · Show |
| 39 | Track more than one player | Watch · Show |
| 40 | Use two cameras | Watch |

### Workstream 7 — Improve over time  *(market area)*

| # | Item | Senses |
|---|------|--------|
| 41 | Skill ratings per area | Read · Write · Show |
| 42 | A weekly plan from your history | Write · Show |
| 43 | Challenges + leaderboards | — |
| 44 | Injury / training-load awareness | Read |
| 45 | Sync across phone and computer | — |
| 46 | Connect to watches and health apps | Read (sensor) |

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

The pipeline works and is honest. Our edge is that it is **multimodal in and out** — it watches,
reads, listens, writes, speaks, and shows — and the remaining work is mostly **polish, packaging,
and scale**.
