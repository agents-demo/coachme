# Model Portability & Offline

**Status:** not started
**Phase:** 0.6 — Foundations
**Effort:** M
**Depends on:** nothing

## Goal

Run against any provider (OpenAI / Anthropic / vLLM / Ollama) and, ideally,
fully offline with a local model. Per-stage model choice via config so a cheap
model can handle verification and a strong model handles the final report.

## Where it lives

`integrations/agents/settings.py` — provider selection, per-stage model names.
Verify all three model clients (OpenAI, Anthropic, local) work end-to-end with
tool-calling and vision.

## Acceptance

- Switch provider via `.env` with no code change.
- An offline/local run (e.g. Ollama) produces a complete report with no
  network calls.

## Risks

Provider quirks: tool-calling schemas differ between providers; vision input
formats differ. Test each provider with the full pipeline, not just a simple
completion.

---
*See [00_priorities.md](00_priorities.md) §3 item 0.6 for sequencing context.*
