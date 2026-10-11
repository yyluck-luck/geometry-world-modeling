# P2: observed-source state in the UC input of S141 A

Pre-run protocol, local date 2026-10-10. PROTOCOL_FREEZE.json preserves the initial preflight; FINGERPRINT.json binds the final protocol, code, plans and input manifest before remote dispatch, new generation or score inspection. Owner explicitly resumed autonomous execution. This is a causal mechanism pilot toward a method contribution, not an established CCF-A method. No training, retrieval change, warp conditioning, output fusion or candidate selection. B, W2 and P1 stay closed. S143-S146 belong to another agent and are not duplicated or interrupted.

## Hypothesis and causal scope

MEASURED antecedent (existing S141 final review): adapted A improves over base but memory benefit is not demonstrated. SOURCE INSPECTION: train_s141.py presents UC with forward-noised observed source latents; the target-only training loss does not explicitly supervise context predictions. At inference, UC reads the context part of one evolving, guided joint state; C substitutes observed context latents. There is no independently unconditional trajectory.

UNVERIFIED hypothesis: the source-state input to UC affects the useful geometry-conditioned guidance residual, and using correctly camera-aligned observed sources improves target predictions beyond resetting the noise path or merely reducing guidance. A native sampled context can be a legitimate joint posterior; this experiment does not presume it invalid. Fixed-noise resetting matches per-step source-noise marginals, not the entire training or sampling distribution.

Minimum intervention: after packing UC/C, replace ONLY UC context rows 0:4 before the original DiscreteDenoiser. Do not directly change the persistent sampler state. Preserve source IDs/order, poses/intrinsics, scale, masks, CLIP, C inputs and UC dictionaries, model, target state, original sampler and every RNG draw. Downstream states naturally diverge. Capture eps_H from the existing initial Gaussian's context rows BEFORE sampler scaling (the original CPU draw moved to GPU). No extra noise draw. Use sigma_q = den.idx_to_sigma(den.sigma_to_idx(sigma_hat)).

| Arm | UC context input | Guidance |
| --- | --- | --- |
| native | evolving joint state | original cfg=2.0, cfg_min=1.2 |
| real | observed z_H + sigma_q eps_H | original |
| zero | sigma_q eps_H | original |
| permuted | roll(z_H, 1, frame-axis) + sigma_q eps_H; keep slot noise/cameras fixed | original |
| low_cfg | evolving joint state | cfg=cfg_min=1.2 |

Zero and permutation are deliberately artificial controls; beating them alone is weak evidence. Low CFG excludes only this prespecified scalar alternative, not every possible guidance schedule. A pass supports the fixed input substitution against these controls, not a proof that drift caused all previous failures, improved memory use, broad generalization or method novelty.

## Fixed inputs and exposure

Use final S141 A step10000 adapter SHA256 635e6e319d4dbf40d5db58d42498303c5f15fb32107f976e8c315d173de87818; unmodified base weights; original fp32/autocast/TF32 settings and 50 sampler steps. PLAN.json contains exactly S139 mem_vmem contexts for s0150 and s0550 in each seq-01→02, seq-04→03 and seq-06→05 pair. Seeds 3 and 4. This is an exposed chess discovery panel; choice is by fixed temporal offsets and pair balance, not current per-cell outcome. No target depth. Query RGB is scoring-only after all outputs are sealed. Hashing query files for provenance before execution is allowed and is explicitly not a claim that their bytes were unread.

Native outputs are reused from completed S141 A after matching all selected file hashes to S141 RUNS receipts and one exact unchanged replay: first PLAN context, seed3. This necessary replay is not a new S141 evaluation chain. Replay is also traced; no full native rerun. ANALYTICAL counts: 60 scored cells; 48 new intervention/control generations plus one native replay = 49 new clips. No existing job is duplicated.

## Validity and saved intermediate quantities

Unit checks: hook leaves packed rows4:16 and original input/storage unchanged, uses quantized sigma, captures noise before in-place scaling, and does not advance RNG. End-to-end replay must match archived bytes exactly. Save every generated prediction, output hash, source/checkpoint/code/input hashes, package versions, GPU ID, duration and exit state. Save per-step raw/quantized sigma, native-to-forward-noised-context RMS, intervention RMS, context/source/noise RMS, target C-U prediction RMS, CPU/CUDA RNG hashes and initial context-noise hash. Traces of real/zero/permuted/low_cfg for each cell must have identical RNG streams and initial noise. Native replay trace is compared on its one cell. Structural invariants do not assert later trajectories should be equal.

Any failed identity, shape, finite-value, source/checkpoint/hash, missing/duplicate cell, RNG or fidelity check gives INVALID_ASSAY. Do not score a partial panel as a negative or remove cells. Seal all outputs before target RGB decoding. Baseline and prediction scores use the unchanged S140 scorer, with PSNR pooled over four target frames and SSIM averaged over them. Preserve its image conversion exactly. A second independent arithmetic implementation checks the resulting table.

## Frozen decision and kill rules

For every comparator native/zero/permuted/low_cfg, first average seeds per window and then give the six windows equal weight. A GO_TO_REPLICATION_DIAGNOSTIC requires ALL:

- real minus comparator mean PSNR >=0.20 dB;
- 95% percentile interval lower bound >0, using 10000 equal-window bootstrap samples with numpy default_rng(0), shared resamples;
- mean SSIM difference >=0;
- each of the three pair-level mean PSNR differences >0;
- removing the two largest positive-difference windows leaves mean PSNR difference >=0.10 dB (no deletion from primary).

Report every arm/window/pair and the best-two positive-gain share. Any failed scientific gate is STOP_TESTED_POLICY: no strength/noise/schedule/threshold/panel tuning or relabeling. A GO only permits proposing a separately frozen replication within applicable authorization; it does not validate novelty. new_method_validated=false; novelty_authorization=NONE throughout.

## Compute and queue

At most one RTX3090 (GPU3 from the verified owner allocation), maximum 7200 seconds total GPU reservation including loading/replay/all generation. Before GPU acquisition wait for s145chain and s146op plus any other owner S143-S149 generator processes to finish. Require two idle observations 120 seconds apart with GPU3 <100MiB and <5% utilization; do not displace anyone. Wait at most24 hours, then BLOCKED_CAPACITY; remote waiting does not reserve GPU. A concurrent allocation race causes abort, not cancellation of another job.

After the one replay, but before inspecting target quality, project remaining time as replay generation seconds ×48×1.25 plus600 seconds loading overhead. If it exceeds remaining7200 seconds, stop COMPUTE_CAP before interventions; do not drop a control. Hard wall timeout enforces total cap. CPU scoring uses two threads after GPU processes exit. Persistent unique tmux job codexp2_20261011; remote namespace /mnt/gluster_dcpu/yiyangliu/gwm_codex_p2_20261011. Record protocol/code/input fingerprint and dispatch intent before starting it. Never blind-retry an ambiguous dispatch.

## Prior work and remaining novelty obligation

[History-Guided Video Diffusion, arXiv:2502.06764](https://arxiv.org/abs/2502.06764), section5, already composes scores from differently noised histories. [No Training, No Problem: Rethinking Classifier-Free Guidance for Diffusion Models, arXiv:2407.02687](https://arxiv.org/abs/2407.02687), ICLR2025, changes the reference condition for guidance. Therefore noisy history and negative-branch modification are not novel primitives. This pilot isolates an observed-source versus evolving-state input in an existing camera-conditioned joint sampler, with matched controls. If successful, a CCF-A method still needs a distinct general principle, evidence beyond these controls, fresh-scene replication and strongest relevant methods; a compatibility repair alone is insufficient. This requirement is kept separate from whether a cheap causal test is informative.

One bounded Astra Ultra design/rejection pass recommended this executable diagnostic with quantized sigma, captured original noise, and the low-CFG control. No further pre-experiment review round is planned; implementation checks remain required.
