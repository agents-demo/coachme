# Simple Roadmap — from demo to real product

*A plain-English plan for management. One line per item. No jargon. Completed items have been
removed.*

---

## The product in one line

Film a training session and get back what to fix and how to practice — a coach you can replay.

## The core differentiator - evidence-backed adaptive coaching

The reliable product runs a fixed pipeline: watch the video, measure movement and body mechanics, write the coaching findings, then verify. That is the baseline.

**Evidence-backed adaptive coaching** means the coaching adapts to what the AI finds, and every finding must cite measured evidence. The **Investigator** mode is how it works: the model chooses which tools and time windows to inspect, may ignore ball tracking if irrelevant, and may dig into wrist or racket mechanics because the evidence led there.

The supporting advantage is **multimodal in and out**: it watches video, reads its own measurements, writes and speaks the coaching, and shows annotated video/images. Multimodal is how the coaching reaches the user; evidence-backed adaptive coaching is the differentiator.

Today: Standard mode is the reliable default. Investigator is opt-in while the benchmark confirms better outcomes at acceptable cost and latency.

## Where we are today

- Video or photo in, a coaching report out — on web and Android.
- English and Chinese UI and reports; Ask-by-voice; on-device pose/ball analysis.
- Pairwise progress comparison, 3D body mechanics, automatic rally splits, footage-quality checks,
  filming guidance, saved-result fallback and one-click delete are in place.
- The report is traceable - every point points to a moment in the video.
- **Investigator mode:** the model chooses what to examine and must cite evidence; it is opt-in while the benchmark runs, with Standard as the default.

---

## The work, by workstream

**Groups at a glance**

| # | Workstream | In one line | Type | Items |
|---|-----------|-------------|------|:---:|
| 1 | Product | Make it usable by strangers. | Build stage | 7 |
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
| Investigator mode: benchmark, permissions, budgets and per-run UI | - |
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

*Shot speed and spin are stretch goals; ship them only when the measurement quality supports the claim.*

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

*Details, effort sizes and ordering are in the full plan: [Priorities](../engineering/plans/priorities.md).*

---

## What could go wrong (and the plan)

- **Bad video gives bad advice** → guide users on filming; warn when the clip is poor. *(done)*
- **Costs grow with usage** → measure and cap the cost per session.
- **Video is personal data** → keep it local by default; clear consent; easy delete. *(delete done;
  hosted privacy policy still to do)*
- **Overclaiming** -> every claim ties to measured video evidence; unsupported claims are removed.

## Rough timing

- **Demo:** essentially ready.
- **Product:** a few months.
- **Market areas:** ongoing.

## The one thing to remember

The pipeline works and every finding is traceable to evidence. Our primary edge is **evidence-backed adaptive coaching**; multimodal input/output is the supporting delivery layer. The remaining work is
packaging, validation, audio input and scale.
