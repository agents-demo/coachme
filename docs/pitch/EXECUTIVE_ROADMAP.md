# Simple Roadmap — from demo to real product

*A plain-English plan for management. One line per item. No jargon. Completed items have been
removed.*

---

## The product in one line

Film a training session and get back what to fix and how to practice — a coach you can replay.

## The core idea — it is multimodal (in and out)

It doesn't just *read* video and *write* text — it works across senses in **both directions**:

**Takes in**
- **Watch** — reads **video/photos** (a vision model reads the frames). **Done**
- **Read** — reads **its own numbers** (movement, body, ball). **Done**
- **Listen** — hears **audio**, e.g. a coach's spoken notes. **Remaining**

**Puts out**
- **Write** — writes **text**: the coaching in plain words. **Done**
- **Speak** — speaks **audio**: it reads the report aloud. **Done**
- **Show** — shows **video & images**: highlight clips, overlays, share cards. **Done**

The remaining multimodal gap is **audio in** (coach notes, racket sound).

## Where we are today

- Video or photo in, a coaching report out — on web and Android.
- English and Chinese UI and reports; Ask-by-voice; on-device pose/ball analysis.
- Pairwise progress comparison, 3D body mechanics, automatic rally splits, footage-quality checks,
  filming guidance, saved-result fallback and one-click delete are in place.
- The report is honest — every point points to a moment in the video.

---

## The work, by workstream

**Groups at a glance**

| # | Workstream | In one line | Type | Items |
|---|-----------|-------------|------|:---:|
| 1 | Product | Make it usable by strangers. | Build stage | 6 |
| 2 | Sharper analysis | Read the play more deeply. | Market area | 6 |
| 3 | Match play | Score and call a real game. | Market area | 3 |
| 4 | Live & mobile | Use it in the moment. | Market area | 2 |
| 5 | Coaches & teams | Work with a coach or a team. | Market area | 5 |
| 6 | Improve over time | Track progress and plan. | Market area | 7 |

**Senses legend:** **Watch** / **Read** / **Listen** = in · **Write** / **Speak** / **Show** = out ·
**—** = no new sense.

### Workstream 1 — Product *(stage: beta)*

| Item | Senses |
|------|--------|
| Accounts + log-in | — |
| Hosted — nothing to install | — |
| Session feedback (like / dislike) | — |
| Track and limit cost per session | — |
| Broader multi-sport support | Watch |
| Annotated coaching clips (issue text burned into a clip) | Write · Show |

### Workstream 2 — Sharper analysis *(market area)*

| Item | Senses |
|------|--------|
| Name the shot (forehand / backhand / serve / block) | Watch · Write |
| Feedback per stroke, not just per session | Watch · Write |
| Service detection (toss, no prior contact) | Watch |
| Racket-angle proxy (wrist/forearm; not the racket face) | Watch |
| Table landing heatmap (needs 4-corner calibration) | Watch · Show |
| **Understand audio too — voice notes, racket sound** | Listen |

*Shot speed and spin are stretch/non-goals — ship only if honest.*

### Workstream 3 — Match play *(market area)*

| Item | Senses |
|------|--------|
| Automatic scoring | Watch · Show |
| In/out line calls (reviewable) | Watch · Show |
| Match statistics | Read · Write |

### Workstream 4 — Live & mobile *(market area)*

| Item | Senses |
|------|--------|
| Live feedback while playing | Watch · Speak · Show |
| Spoken cues during playback | Speak |

### Workstream 5 — Coaches & teams *(market area)*

| Item | Senses |
|------|--------|
| Coach / team accounts | — |
| Share one session with a coach | Write · Show |
| Compare your motion to a pro's | Watch · Show |
| Track more than one player | Watch · Show |
| Use two cameras | Watch |

### Workstream 6 — Improve over time *(market area)*

| Item | Senses |
|------|--------|
| Multi-session trend view (issues, drills, metrics) | Read · Show |
| Skill ratings per area | Read · Write · Show |
| A weekly plan from your history | Write · Show |
| Challenges + leaderboards | — |
| Injury / training-load awareness | Read |
| Sync across phone and computer | — |
| Connect to watches and health apps | Read (sensor) |

*Details, effort sizes and ordering are in the full plan: [ROADMAP.md](../engineering/ROADMAP.md).*

---

## What could go wrong (and the plan)

- **Bad video gives bad advice** → guide users on filming; warn when the clip is poor. *(done)*
- **Costs grow with usage** → measure and cap the cost per session.
- **Video is personal data** → keep it local by default; clear consent; easy delete. *(delete done;
  hosted privacy policy still to do)*
- **Promising too much** → stay honest; every claim ties to the video.

## Rough timing

- **Demo:** essentially ready.
- **Product:** a few months.
- **Market areas:** ongoing.

## The one thing to remember

The pipeline works and is honest. Our edge is that it is **multimodal in and out** — it watches,
reads, writes, speaks, and shows — and the remaining work is mostly **audio input, packaging, and
scale**.
