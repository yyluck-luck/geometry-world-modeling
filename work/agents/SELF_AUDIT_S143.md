# Self-audit S143 (context-ranking audit) — verification by the main agent

Ideation/rejection: codex gpt-6-astra (ultra) R259 (idea), R260 and R261 (rejection rounds). This file verifies execution.
| check | result |
|---|---|
| pool: 24 windows × 6 unique ordered sets, all rule-5 KPS records finite/OK (build aborts otherwise) | pass |
| warps: 576 files, all KPS OK; Q_W scored once per (window, set) | pass |
| replay gate (S139 mem_vmem window 0 seed 3) byte-identical, 913394e0… | pass |
| discovery: 576 cells, receipts 576, RTX 3090, adapter NONE, seeds 3–6 | pass |
| fresh: provenance gate (gen_s141, s141_common, plan, scorer hashes = discovery) | pass |
| fresh: 576 cells, receipts 576, RTX 3090, seeds 42/7/1/2; strict validation status VALID | pass |
| frozen selections written before fresh contrasts (`*_FROZEN_SELECTIONS.json`) | pass |
| independent recomputation: R 0.320443; nearest-4 − mem_vmem +0.747 (disc) / +0.738 (fresh) | match |
| amendments committed before the outcomes they govern (0cabac3c, 3ce97f83, 043edd3f, 532c29ee) | pass |
Limits: exposed room; target-informed selectors (not deployable); seed-level (not scene-level) replication; one consumer.
Self-audit, no codex repository-level review of the executed run.
