# Research Automation Configuration (English)

**Task ID:** `automation`  
**Cadence:** every 30 minutes  
**Thread:** `01a071cd-ee82-7e03-a421-4f092ae4a13a`  
**Notification policy:** notify only on a meaningful change, completion, failure, or required user action.

## Run procedure

1. Read `AGENTS.md`, `RESEARCH_PRINCIPLES.md`, `RESEARCH_MEMORY.md`, the newest `RESEARCH_LOG.md`, `docs/RESEARCH_HANDOFF_CURRENT.md`, and `docs/RESEARCH_PLANS_EN.md`.
2. Inspect real local and remote process state and existing receipts before starting work. Do not repeat a completed experiment.
3. Evaluate seven checks: skill execution, innovation/nearest-work evidence, experiment authenticity and answer isolation, local tools/GPU use, literature retrieval, agent role/failure status, and memory/artefact records.
4. Use English for literature searches and model consultations. Report findings and summaries to the user in simple Chinese.
5. Continue the most important executable step. Plans, protocols, gates, and scheduler prompts remain in English; Chinese documents are historical or beginner-facing snapshots.
6. Preserve negative results, failed transfers, missing data, and all denominators. Never convert environment/import success into scientific validation.

## Active scientific guardrails

- The current candidate is GRC-Memory, but `new_method_validated=false` and `novelty_authorization=NONE` remain active.
- Formal GRC requires an accepted declared VMem baseline, independent future geometry ground truth, same candidate pool, fixed computation budget, strong baselines, cross-scene confirmation, and independent readback.
- ICL-NUIM is currently conditional synthetic controlled access only. It cannot support a real-world or cross-scene claim by itself.
- The H800 queue is S101 environment/weight qualification, S102 Gate 0, and S103 declared VMem baseline. Do not open held-out answers before prediction artefacts are sealed.
- If the low-risk-history hypothesis fails under the frozen protocol, stop the GRC method claim and reframe the result as a diagnostic or benchmark finding.

## Current queue

- Finish and verify the interrupted remote weight transfer.
- Verify checkpoint/config identity and run a no-data model-load smoke on H800.
- Execute calibration/development VMem baseline, seal predictions, then score held-out data.
- Run matched-budget selector baselines, followed by GRC only if the baseline and data gates pass.
- Maintain English plan registry and Chinese progress/memory summaries in sync.
