# Engineering

## Reference

| Doc | One-line summary | Use when |
|---|---|---|
| [Architecture](reference/architecture.md) | Layers, dependency direction, package map and runtime structure. | Changing structure or adding a module |
| [Analysis pipeline research](plans/45_analysis-pipeline-research.md) | Feasibility assessment of coach-driven CV metrics; Tier A–C items with effort/risk. | Looking for analysis improvements or planning pipeline analytics |

## Plans (`plans/`)

Files are numbered `XX_name.md`. `00` is the master roadmap. `01`–`03` are
full implementation specs (ready to build from). `04`–`44` are stubs (goal,
effort, dependencies defined; full spec to be written before building).
`45` is the pipeline analytics research reference. `46`–`56` are analytics
stubs derived from that research.

### Full specs — ready to build from

| File | What it covers |
|---|---|
| [00_priorities.md](plans/00_priorities.md) | Master roadmap: all features, phases, effort, sequence. Start here for "what next." |
| [01_benchmark.md](plans/01_benchmark.md) | Benchmark protocol: clips, coach labels, blind A/B, 12 release gates. |
| [02_benchmark-ui.md](plans/02_benchmark-ui.md) | Benchmark UI: local FastAPI + SvelteKit for run control, labelling and rating. |
| [03_investigator.md](plans/03_investigator.md) | Investigator mode: model-directed investigation, evidence ledger, budgets, rollout. |

### Stubs — Phase 0 Foundations

| File | Item | Effort |
|---|---|---|
| [04_eval-harness.md](plans/04_eval-harness.md) | 0.1 Eval harness & prompt regression | M |
| [05_calibration.md](plans/05_calibration.md) | 0.2 Calibration & normalization | L |
| [06_feedback-loop.md](plans/06_feedback-loop.md) | 0.3 Feedback loop (thumbs / corrections) | S |
| [07_ux-fundamentals.md](plans/07_ux-fundamentals.md) | 0.4 UX fundamentals (session library, streaming) | M+M |
| [08_model-portability.md](plans/08_model-portability.md) | 0.6 Model portability & offline | M |
| [09_privacy-compliance.md](plans/09_privacy-compliance.md) | 0.7 Privacy & compliance | S–M |
| [10_deployment-ops.md](plans/10_deployment-ops.md) | 0.8 Deployment & ops | M |

### Stubs — Phase B Core Review + B.5 Measure Expansion

| File | Item | Effort |
|---|---|---|
| [11_overlay-compare.md](plans/11_overlay-compare.md) | B4 Overlay compare (blend / side-by-side) | M |
| [12_reference-comparison.md](plans/12_reference-comparison.md) | B5 Pro / reference comparison | M |
| [13_multi-sport.md](plans/13_multi-sport.md) | B6 Multi-sport generalization | L |
| [14_stroke-segmentation.md](plans/14_stroke-segmentation.md) | M3 Stroke / repetition segmentation | M |
| [15_footage-rally-detection.md](plans/15_footage-rally-detection.md) | M5+M6 Footage quality + rally detection | S+S |
| [16_handedness-sampling.md](plans/16_handedness-sampling.md) | M7+M8 Handedness auto-detect + thorough sampling | S+S |
| [17_person-segmentation.md](plans/17_person-segmentation.md) | I1+I2 Person detection + subject segmentation | M+M |
| [18_depth-ocr.md](plans/18_depth-ocr.md) | I4+I5 Monocular depth + scoreboard OCR | L+S |

### Stubs — Phase C Analysis Depth

| File | Item | Effort |
|---|---|---|
| [19_ball-shot-type.md](plans/19_ball-shot-type.md) | C1 Ball shot-type & pace | L |
| [20_session-segmentation.md](plans/20_session-segmentation.md) | C2 Whole-session auto-segmentation | L |
| [21_live-capture.md](plans/21_live-capture.md) | C3 Real-time / live capture | XL |
| [22_multi-player.md](plans/22_multi-player.md) | C4 Multi-player attribution | L |
| [23_high-fidelity-sampling.md](plans/23_high-fidelity-sampling.md) | C5 Higher-fidelity sampling (thorough mode) | M |
| [24_line-calls.md](plans/24_line-calls.md) | C6 Line calls / scoring / match stats | L |
| [25_multi-camera.md](plans/25_multi-camera.md) | C7 Multi-camera / dual-angle | L |
| [26_3d-biomechanics.md](plans/26_3d-biomechanics.md) | C8 3D biomechanics / kinematic sequence | L |
| [27_spin-estimation.md](plans/27_spin-estimation.md) | C9 Spin estimation (stretch; likely non-goal) | XL |
| [28_audio-understanding.md](plans/28_audio-understanding.md) | C10 Audio understanding (listen) | M |
| [29_service-detection.md](plans/29_service-detection.md) | C11 Service detection (table tennis) | M |
| [30_racket-angle.md](plans/30_racket-angle.md) | C12 Racket-angle proxy (table tennis) | M |
| [31_table-heatmap.md](plans/31_table-heatmap.md) | C13 Table contact-point heatmap (table tennis) | L |

### Stubs — Phase D Product & Platform

| File | Item | Effort |
|---|---|---|
| [32_ios-app.md](plans/32_ios-app.md) | D1 iOS app | XL |
| [33_coach-team.md](plans/33_coach-team.md) | D2 Coach / team layer | XL |
| [34_training-plans.md](plans/34_training-plans.md) | D3 Personalized training plan + memory | L |
| [35_share-links.md](plans/35_share-links.md) | D4 Share links & socials | M |
| [36_skill-ratings.md](plans/36_skill-ratings.md) | D5 Assessments / skill ratings | M |
| [37_injury-risk.md](plans/37_injury-risk.md) | D6 Injury-risk / load flags | L |
| [38_audio-coaching-playback.md](plans/38_audio-coaching-playback.md) | D7 Audio coaching playback | M |
| [39_integrations-ecosystem.md](plans/39_integrations-ecosystem.md) | D8 Integrations & ecosystem | M–XL |
| [40_coach-comments.md](plans/40_coach-comments.md) | D9 Coach comments + drill assignments | M |
| [41_gamification.md](plans/41_gamification.md) | D10 Gamification — challenges & leaderboards | M |
| [42_cross-device-sync.md](plans/42_cross-device-sync.md) | D11 Cross-device sync | M–L |
| [43_multi-session-trends.md](plans/43_multi-session-trends.md) | D12 Multi-session trend view | M |
| [44_annotated-clips.md](plans/44_annotated-clips.md) | D13 Annotated coaching clips | M |

### Research reference + Pipeline Analytics stubs

| File | Item | Effort |
|---|---|---|
| [45_analysis-pipeline-research.md](plans/45_analysis-pipeline-research.md) | Research reference: Tier A–C feasibility with effort/risk (not a build plan) | — |
| [46_recovery-time.md](plans/46_recovery-time.md) | A1 Recovery time between shots | S |
| [47_late-feet-timing.md](plans/47_late-feet-timing.md) | A2 Late-feet timing | S |
| [48_hip-shoulder-sequencing.md](plans/48_hip-shoulder-sequencing.md) | A3 Hip / shoulder sequencing | S |
| [49_elbow-contact-position.md](plans/49_elbow-contact-position.md) | A4 Elbow position at contact | S |
| [50_stroke-arc.md](plans/50_stroke-arc.md) | A5 Backswing / stroke arc | S–M |
| [51_ready-position.md](plans/51_ready-position.md) | A6 Ready position frequency | S |
| [52_technique-drift.md](plans/52_technique-drift.md) | A7 Technique drift / fatigue detection | S |
| [53_rally-distribution.md](plans/53_rally-distribution.md) | A8 Rally length distribution | S |
| [54_structured-drills.md](plans/54_structured-drills.md) | A10 Structured drill schema | M |
| [55_stroke-consistency.md](plans/55_stroke-consistency.md) | C1* Stroke consistency score | M |
| [56_similar-session-retrieval.md](plans/56_similar-session-retrieval.md) | C3* Similar-session retrieval | M |

*A9 (numeric cross-session trends) is covered by [43_multi-session-trends.md](plans/43_multi-session-trends.md). C1*/C3* are pipeline-analytics variants distinct from the C1/C3 items in `00_priorities.md`.*

---

**Workflow:** pick the next item from `00_priorities.md` → write a full spec in
the stub file → build from the spec. Do not build from a stub alone.
