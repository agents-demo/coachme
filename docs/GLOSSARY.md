# Glossary

One place for the terms used across the product, pitch and engineering docs.

## Canonical terms

| Term | Use it for | Do not use it for |
|---|---|---|
| **Standard** | The deterministic, reliable default analysis pipeline. | Calling it “the agent” or “agentic”. |
| **Guided** | The existing opt-in mode where fixed measurement runs first, then the model chooses a few windows to review. The UI label is Guided; the code/API name is `agentic`. | The new Investigator mode. |
| **Investigator** | The new opt-in analysis mode where the model chooses tools and time windows, may ignore irrelevant signals, and must cite evidence for every finding. | The platform, the model API, or the fixed pipeline. |
| **Model-as-orchestrator (MaO)** | The architecture pattern: the model, not application code, decides the sequence of tool calls. Expand the acronym the first time. | A user-facing mode name. |
| **Model-directed investigation** | The plain-language description of Investigator behaviour. Best term for pitch and external docs. | A synonym for “autonomous” or “uncontrolled”. |
| **Evidence-grounded** | Every finding must cite tool evidence (IDs, measurements, timestamps). | A guarantee that the finding is true; provenance is not truth. |
| **Finding-driven investigation** | A description of the loop: a finding triggers the next probe. | The mode name; use **Investigator** for the mode. |
| **Investigation loop** | The technical sequence: observe → choose tool → inspect → update evidence → decide next step. | A product name. |
| **ReAct loop** | The implementation pattern (thought → action → observation) inside openjiuwen. | External pitch language unless the audience is technical. |
| **Agentic** | Broad adjective for an AI system that can take multiple actions/tools. | A synonym for Investigator; the fixed pipeline is not agentic. |
| **Ascend** | Huawei’s AI processor family and software/systems path (Ascend 310/310P inference, Ascend 910-class training, CANN, MindSpore, Atlas). | The phone SoC; on-device NPU is separate. |

## Recommended sentence

> **Evidence-backed adaptive coaching is the differentiator. Investigator is the mode. Model-as-orchestrator is the architecture. Model-directed investigation is the mechanism.**

## Terms to use carefully

- **“Free investigation”** — internal shorthand only. Say **model-directed investigation** externally.
- **“Agentic analysis”** — ambiguous because the existing Guided mode is also agentic. Say **Investigator** or **model-directed analysis**.
- **“Autonomous analysis”** — overclaims. The model is bounded by tools, budgets and evidence.
- **“LLM as orchestrator”** — understandable but informal; use **model-as-orchestrator** in architecture docs.
- **“Open-ended agent”** — vague; avoid.
- **“Finding-driven”** — good as a description, not as a mode name.
- **“Adaptive investigation”** — acceptable only if you mean the model changes its next step based on evidence; define it.

## Reading rule

For pitch and product docs: **evidence-backed adaptive coaching**, **Standard / Guided / Investigator**, **model-directed** (explanation), **Ascend**.
For engineering docs: add **model-as-orchestrator**, **InvestigationContext**, **evidence ledger**, **ReAct loop**.
