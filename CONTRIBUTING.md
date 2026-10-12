# Contributing to Topspin Review

Record a racket-sport session video and get back a coaching report (strengths, issues with evidence, drills, focus).

## Setup

Use the repo venv (on this machine `python`/`pip` are not on PATH):

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
& $PY -m pip install -r requirements.txt
```

`.env` holds the model endpoint; copy `.env.example` if you need a fresh one.

## Run

```powershell
& $PY -m streamlit run topspin_review/surfaces/gui/ui.py    # Web UI
& $PY -m topspin_review.surfaces.cli analyze runtime/data/sample.mp4   # CLI
```

## Checks

```powershell
& $PY -m ruff check .
& $PY -m pytest -q
& $PY tests\integration\evaluate_reports.py    # offline quality gate (needs saved reports)
& $PY tests\integration\make_sample.py          # synthetic sample clip (no camera needed)
```

## Architecture (the one rule that matters)

Layers point **inward** only; `tests/unit/test_architecture.py` enforces it:

```
surfaces  ->  core  ->  integrations  ->  domain
```

- **Keep openjiuwen inside `integrations/agents/`.** Nothing outside imports it. Reach models/agents
  only through the façade (`build`, `TextParams`/`VisionParams`, `run_agent`, `run_text`).
- **`domain/` stays pure** — stdlib only, no I/O.
- **`integrations/`** are the outbound adapters: agents (openjiuwen), storage, reporting, media.
- **Stages** live in `core/stages/<name>/`; the pipeline orchestrator + strategies live in `core/`.
- `__init__.py` is docstring/imports only — no side effects. Wiring happens in `core/bootstrap.setup()`.

## Where to add things

- New **stage**: `core/stages/<name>/` + register in `core/stages/__init__.py` (`STAGES`)
  and call it from `core/strategies/base.py`.
- New **capability** (external system): a module under `integrations/`.
- New **surface**: a module/package under `surfaces/`; reuse the shared façade `core/service.py`.
- New **config knob**: application behaviour in `core/config.py`; endpoint/credentials in
  `integrations/agents/settings.py`.

## The GUIs (`surfaces/gui/` and `surfaces/gui2/`)

- **`surfaces/gui/`** — the Streamlit UI. `ui.py` (entry) builds the pages → `nav.py` holds the
  `PAGE_OBJS` registry + `go()`/`open_report()` → `app_pages/` (one module per page) →
  `components/` (reusable renderers) → `job.py` (worker + prelude) → `data.py`, `style.py`,
  `config.py`, `timeline.py`.
- **`surfaces/gui2/`** — the web app: `server/` (FastAPI `app.py` + read model `read.py` + `jobs.py`
  + `routes/`) serving `client/` (the SvelteKit SPA, built into `client/build/`) at `/gui2/`. Edit
  `client/src/` and rebuild with `npm run build` inside `client/`.

## Commits & PRs

Concise conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`). Describe the change, list the
checks you ran, and include a screenshot/recording for UI changes.
