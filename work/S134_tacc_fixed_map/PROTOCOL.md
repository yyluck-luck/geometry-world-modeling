# S134 protocol — does repairing VMem's surfel map change its memory retrieval and memory-arm quality?

Authorization: owner approval in conversation, 2026-10-09 ("ok do S134 on tacc gpu13/gpu14"), recorded under
the AGENTS.md owner authorization rule. Written before any S134 GPU run. Diagnostic, not a method claim.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Question
S133 found VMem's surfel map mis-scaled by more than 10× in 8/14 windows, caused by a silent PnP identity fallback.
With the map repaired by the S133 fix:
(A) is the map scale correct, and do the retrieved contexts change?
(B) does the memory arm's generation quality change, against itself (orig map) and against static?

## Hardware and code
- TACC gpu13, one free RTX 3090 per process (GPU 3/4 were idle at setup; gpu14 unusable because of an NVML
  driver/library mismatch). FP32 as in all sealed runs.
- Not byte-identical to H800. **All compared arms are regenerated on gpu13.** Sealed H800 outputs are used
  only for the retrieval-reproduction check.
- Source: the SuperPOD transport tree `gwm_source_transport_20260915/vmem`, the one behind every sealed run.
  It differs from `work/S17C_interface_preparation/isolated_vmem_source` only in device handling
  (`modeling/pipeline.py`, `utils/util.py`).
- Env: uv Python 3.11.16, exact SuperPOD `pip freeze` (torch 2.7.0 cu126, diffusers 0.32.2, ...).
- Weights SHA-256 must match `work/S101_env_bootstrap/VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json`. CUT3R,
  CLIP and VAE come from HF (LFS hashes pre-checked). vmem_weights comes from the local verified copy (gated repo).

## Leakage boundary
Model processes get `stage/`: bank color+pose and target pose only, with no depth and no target color.
`eval_map_s134.py` (target depth) and `score_s134.py` (target RGB) are separate CPU processes reading `datasets/`.

## Step A — maps and contexts (native convention, as sealed)
`run_retrieval_s134.py` with PNP_FIX=0 (orig) and PNP_FIX=1 (fix), 14 windows (scene_13/14, w50–w350).
- Reproduction check: orig raw contexts vs the sealed C8 job 609623 contexts (reported; numerics may differ).
- Map gate on fix: window scale ratio (median rendered depth / median dataset depth) within [0.5, 2] in
  ≥ 12/14 windows, none > 10 or < 0.1. **If the gate fails, stop after step A.**
- Report how many windows change contexts (NMS-on, NMS-off). If fewer than 3 of the affected windows change
  NMS-on contexts, step B runs anyway (cheap), but the primary contrast is reported as structurally near-null.
- Exploratory, secondary: the same two variants under `gl`, maps only.

## Step B — generation (only if the gate passes)
Arms per window: static (offsets 0,15,30,45), mem_on_orig, mem_on_fix (VMem default clean NMS-on),
mem_off_orig, mem_off_fix. Identical (window, ordered context) tuples are generated once.
Seeds 42, 7, 1, 2, 3, 4, 5, 6. Consumer contract as S111, with contexts in retrieval order.

## Metric and analysis
PSNR (dB) over the four targets, using the S103/S106/C9 scorer functions unchanged. Unit: window mean over 8 seeds.
- Affected windows: orig stage-1 construct had ≥ 1 PnP failure on gpu13.
- **Primary:** mem_on_fix − mem_on_orig over affected windows.
- Secondary: mem_off_fix − mem_off_orig (affected); each memory arm − static (all windows and affected).
- 95% CI from a window-cluster bootstrap (10k resamples, rng seed 0). Per-seed means reported.
- Verdicts: IMPROVES (mean ≥ +0.2 dB and CI > 0) · WORSENS (≤ −0.2 and CI < 0) ·
  NO_MATERIAL_CHANGE (|mean| < 0.2 and CI covers 0) · otherwise INCONCLUSIVE.
- With ~8 affected windows this is a pilot-scale estimate on an exposed panel. It is not a general claim.

## Stopping rule
Step A gate fail → stop and report. After step B: report, update the ledger, no follow-up without a new protocol.

## Outputs
Remote `/mnt/gluster_dcpu/yiyangliu/gwm_s134/out/`. Receipts, evaluations, scores and analysis are copied to
`work/S134_tacc_fixed_map/results/`. Generated arrays stay remote.

## Amendment 1 (2026-10-09, before any S134 GPU run) — two sites, convention gate
Owner asked to use SuperPOD and TACC together. GPT's second review (14-window gate, single end-to-end
convention, w200 IndexError) is folded in.
- **Canonical contexts come from SuperPOD H800.** Step A runs there for native and gl × orig and fix. The plan
  is built from the H800 receipts, and both sites generate from the same context lists. TACC step A also runs,
  but only as a cross-hardware reproduction check.
- **Generation is split by seed.** H800: 42, 7, 1, 2. gpu13 RTX 3090 (GPU 3/4): 3, 4, 5, 6. Every
  (window, seed) cell is produced on one site, so paired contrasts stay within-hardware. Contrasts are also
  reported per site.
- **Harness gate:** H800 static outputs for seeds 42 and 7 must be byte-identical to the sealed S111 static
  outputs (job 594957), as in C9. If this fails, H800 rows are reported but flagged.
- **gl arms.** If gl+fix passes the scale gate and its median own-render correlation is ≥ 0.5, step B adds gl
  arms: static_gl, mem_on_orig_gl, mem_on_fix_gl. Key secondary: mem_on_fix_gl − static_gl.
  If gl does not pass, no gl generation.
- **Gate scope:** all 14 windows is the target. With 12–13 passing, the primary is also reported on the
  passing subset and the claim is limited to it. A BLOCKED window (e.g. the C9 gl scene_13 w200 IndexError)
  is recorded, never silently dropped.
