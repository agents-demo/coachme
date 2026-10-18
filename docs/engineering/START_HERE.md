# Start Here — Investigator Implementation

This is the one-screen entry point. Do not start by reading the whole plan.

## Read these, in order

1. **This page** — current status and next action.
2. **[Investigator plan](plans/investigator.md)** — how it is designed. Use the table of contents; do not read end to end first.
3. **[Benchmark plan](plans/benchmark.md)** — what “done” means.

## Current status

**Working**

- Standard deterministic pipeline
- Investigator strategy and six tools
- Evidence ledger and report validation
- CLI/API `investigator` mode
- Settings persistence for Investigator availability
- Token usage sync and shared vision recorder
- Cooperative cancellation event
- 75 unit tests passing

**Partial**

- Inspector restriction is prompt-only; shell/list denial is pending
- Run-scoped storage exists; atomic publish and per-stem lock are pending
- Cancellation exists; job queue is not implemented
- Progress events exist; SSE/UI feed is not wired
- Partial-report path exists; not yet exercised under real timeout
- UI mode selector and Investigation panel are missing

**Not started**

- Coach-labelled benchmark clips
- Standard vs Investigator benchmark run
- Final budget calibration
- NewAnalysis selector and result Investigation panel
- Permission-level inspector restriction

## Choose the milestone first

Not every item is needed for every milestone.

| Milestone | Required | Not required yet |
|---|---|---|
| **Internal demo / pitch** | Inspector prompt restriction, NewAnalysis selector, Investigation panel, 3?5 manual A/B clips | Atomic publish, queue, SSE feed, full benchmark, budget calibration |
| **Experimental user release** | Everything above plus permission restriction, atomic publish, per-stem lock, cancellation queue, SSE feed, full coach-labelled benchmark, budget calibration | iOS, accounts/sync, coach workspace |
| **General availability** | Experimental release plus user pilot, privacy/cost review, regression suite, docs | Live coaching, multi-sport expansion |

**Recommendation:** do the internal demo first. It proves the experience and gives you pitch material. The production-hardening list is only needed before letting real users use Investigator.

## Step ? plan

| Step | Plan to read |
|---|---|
| 1. Mode selector | `plans/investigator.md` |
| 2. Settings toggle | `plans/investigator.md` |
| 3. Investigation panel | `plans/investigator.md` |
| 4. Run 3?5 clips | `START_HERE.md` |
| 5. Coach comparison | `plans/benchmark.md` |
| 6. Demo decision | `START_HERE.md` and `plans/benchmark.md` |
| 7. Inspector restriction | `plans/investigator.md` |
| 8. Atomic write/lock | `plans/investigator.md` |
| 9. Cancellation/queue/SSE | `plans/investigator.md` |
| 10. Benchmark | `plans/benchmark.md` |
| 11. Budgets | `plans/investigator.md` and `plans/benchmark.md` |
| 12. Pilot/hardening | `plans/investigator.md` and `plans/priorities.md` |

## Where each thing lives

| Work | Main files |
|---|---|
| Mode selector in Analyze New Session | `surfaces/gui2/client/src/lib/components/NewAnalysis.svelte`; `client/src/lib/api.js` |
| Mode request/backend | `surfaces/gui2/server/models.py`, `server/routes/analyze.py`, `server/jobs.py`, `core/strategies/resolve_strategy.py` |
| Settings toggle | `surfaces/gui2/client/src/routes/settings/+page.svelte`; `server/app.py` (`/settings`); `integrations/storage/store.py` |
| Investigation panel in Session Details | `surfaces/gui2/client/src/routes/result/+page.svelte`; `client/src/lib/components/ReportCard.svelte`; `server/read.py` |
| Report fields (evidence/coverage) | `domain/report.py`, `domain/evidence.py` |
| Inspector restriction | `core/stages/observe/build_agent.py`; `integrations/agents/agent/builder/vision.py`; `integrations/agents/agent/rails.py`; `core/stages/investigate/tools.py` |
| Atomic report write / per-video lock | `integrations/storage/store.py`; `core/strategies/investigator.py` |
| Cancellation / live job feed | `surfaces/gui2/server/jobs.py`; `server/routes/jobs.py`; `core/progress.py`; `client/src/lib/components/LiveJob.svelte` |
| Benchmark labels and gates | `docs/engineering/plans/benchmark.md`; `tests/eval/investigation/` |
| Budgets | `core/config.py`; `core/stages/investigate/context.py`; plan ?22 |

## What each doc contains

| Doc | What it contains | When to use it |
|---|---|---|
| `START_HERE.md` | Current status, milestone choice, next action, file map | First stop for implementation |
| `plans/investigator.md` | Full Investigator design, tools, schema, budgets, tests, rollout | Detailed implementation spec |
| `plans/benchmark.md` | Benchmark clips, coach labels, blind A/B, metrics, release gates | Before claiming Investigator is ready |
| `plans/priorities.md` | Product priorities and feature plan | Deciding what to build next |
| `reference/architecture.md` | Layer rules, package map, dependency direction | Before changing structure |
| `research/analysis-ideas.md` | Research backlog of measurement/CV ideas | Looking for analysis improvements; not an execution plan |

## Next engineering action (experimental release path)

**Implement this now, then update the status above.**

**Add permission-level restriction to the visual inspector** used by `look()`:
only `read_file` should be callable; deny `bash`, `list_files`, `grep`, and other
general tools. The current prompt-only restriction is not enough for a user-facing
mode.

After that:

1. Atomic publish + per-stem lock for final reports.
2. Cancellation queue + SSE investigation feed.
3. NewAnalysis mode selector + Investigation panel.
4. Benchmark run and budget calibration.

## Parallel non-engineering action

Select the **8 benchmark clips** and start coach labelling now. This is a 1–2 week
dependency and does not wait for code.

## What happens after that list?

The list ends at a **decision**, not at more Investigator work.

### Decision gate

After the benchmark run and budget calibration:

- **Pass:** Investigator may be released as an experimental user-facing mode
  (feature flag/toggle on), then hardened.
- **Fail:** Investigator stays opt-in/internal, or is narrowed to the specific
  cases where it works. Do not scale it on faith.

### If it passes

1. Enable the mode for users through the Settings toggle and NewAnalysis selector.
2. Run a small user pilot; watch retention, cost, latency and report quality.
3. Finish hardening: permissions, privacy, cost telemetry, docs and regression tests.
4. Then move to the next roadmap item ? not more Investigator features.

### If it fails

1. Keep Standard as the product.
2. Keep Investigator as an internal/experimental tool.
3. Use the benchmark to decide whether to narrow it, pause it, or return to research.

### Then what?

Investigator is one roadmap item. After the decision, the roadmap continues with
the next product milestone ? for example iOS, accounts/sync, coach workspace or
multi-sport validation. Live coaching is a separate later project (Phase 4).

## Definition of done

Investigator is ?done for this cycle? when:

- the safety, concurrency, cancellation and UI items above are complete;
- the benchmark has run against coach labels;
- the pass/fail decision is written down;
- the next roadmap item is chosen.

Anything beyond that is a new cycle, not unfinished work.

## Rule

If an item blocks **trust, correctness or the benchmark**, do it first.
If it only improves polish, do it later.
