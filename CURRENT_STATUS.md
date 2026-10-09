# Current status — read this first (updated 2026-10-09)

One page. Everything else in the repository is supporting evidence or history.

## Project in one sentence
A diagnostic study of a frozen VMem configuration (surfel-memory video world model + CUT3R) on 14 exposed
windows from two 3DMatch RGB-D scenes: does its geometry-based memory help, and if not, why?

## Strongest finished results
1. **Duplicate-slot repair: closed negative.** −0.016 dB against a +0.20 dB retention bar, fixed in advance
   (`docs/report/TECHNICAL_REPORT_20260918.md` §1).
2. **Finite-panel contrasts:** `memory_nms_off − static` +0.242 dB (8/14), `memory_nms_on_clean − static`
   −0.485 dB (6/14). Two seeds only; see the caveat from result 5.
3. **Slot 0 is a coordinate/scale intervention:** it sets the Plücker ray reference and the translation scale.
   Fixing both removes the slot-0 effect, and the native effect flips sign across seeds
   (`work/S130_C8_diagnostics/results_slot_job609617/RESULT.md`).
4. **Support is not scarce:** the delivered frames already observe 78–97% of the target surface, yet PSNR is
   ≤ 16 dB in 12/14 windows (`work/S130_C8_diagnostics/results_support_job609623/RESULT.md`).
5. **NEW (S133): VMem's surfel map was broken in 8/14 windows.** CUT3R confidence on these frames is often
   below the PnP mask threshold. MST PnP then silently falls back to identity poses, and the similarity
   registration scales the point cloud ×300–900 (5 windows) or ×0.02–0.08 (3 windows). A one-line adaptive
   threshold removes it (12/14 windows within [0.5, 2] of dataset depth). Pose convention is irrelevant to it
   (`work/S133_scale_debug/RESULT.md`).

## What result 5 means
The sealed memory-arm retrievals behind results 2 and 4 were selected from this broken map in 8/14 windows.
They describe a malfunctioning memory, not VMem's intended geometry retrieval. C9's convention test
(`work/S132_C9_convention/results_job609666/RESULT.md`) is also confounded by it.

## Active question
With the surfel map repaired, does VMem's memory retrieval change, and does memory-vs-static change?

## Next experiment (needs an owner-approved protocol file; see AGENTS.md)
S134. Rerun the C8 support retrieval (stage 1 + 2 + retrieval maps) with the S133 fix. Check own-render depth
ratio and correlation, and whether the selected context frames change. Only if the map is certified, regenerate
the memory arms (≥ 8 seeds) against the sealed static arm. GPU: SuperPOD H800 or TACC gpu13/gpu14.

## Closed or retired
- Duplicate-slot / NMS-repair tuning (closed by result 1).
- Hidden-surface / support-scarcity predictors (falsified on this panel by result 4).
- Generic selector-score ideas (crowded: Keepsake 2610.06588, AnchorWeave 2602.14941 and others).
- The R112–R249 owner-packet / signature / quorum gate loop (retired 2026-10-09, AGENTS.md).

## Limitations that always apply
One frozen consumer, two exposed scenes (not held-out), 14 windows, RGB PSNR only, two seeds for most
generation results. S133 is CPU stage-1 evidence and not byte-identical to the H800 runs.

## Where things are
Report `docs/report/TECHNICAL_REPORT_20260918.md` · GPU summary `S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md` ·
running ledger `RESEARCH_MEMORY.md` (newest first) · event log `research_events.jsonl` · rules `AGENTS.md`,
`RESEARCH_PRINCIPLES.md` · history `docs/history/`, `work/agents/` (R1–R249 memos).
