# Brief R254 — REJECTION: hostile review of S141 design and code before evaluation (2026-10-10)

S141 (work/S141_finetune) fine-tunes the VMem generator; training is running on TACC RTX 3090s now (A on GPU 3;
B starts when the warp precompute finishes). The protocol was frozen at commit 7cefe20e before training. Evaluation
has NOT run. I want every flaw that could make the result wrong or uninterpretable, so I can fix evaluation-side
problems before evaluation and report training-side problems honestly. Try hard to kill the experiment.

Files: PROTOCOL.md, s141_common.py, prep_latents_s141.py, build_clips_s141.py (clips_s141.json is the built list),
warps_s141.py (+ warpcheck_compare.py, warpcheck_clips.json), train_s141.py, gen_s141.py (header copied from
work/S140_warp_guided/gen_s140.py), build_eval_plan_s141.py, build_rgbd_plan_s141.py, plan_*.json, analyze_s141.py,
self_audit_s141.py, tacc_s141.sh, s141_chainB.sh, s141_chainEval.sh. VMem source: data/S134_tacc/vmem_src.
S139/S140 code and plans: work/S139_crossseq_revisit, work/S140_warp_guided.

Check, citing file:line, rerunning on CPU where feasible (a CPU torch env: `PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python`;
the VMem model weights are NOT in this checkout, so tests must not need them):
1. Objective vs sampler. Does train_s141.py reproduce exactly what DiscreteDenoiser / EulerEDMSampler / MultiviewCFG
   feed the network at sampling time (c_in, c_noise = discrete index, replace channel and its mask, concat order,
   dense_vector, crossattn, num_frames)? Is the epsilon-MSE target right for EpsScaling (c_out = -sigma, c_skip = 1)?
   Is "all 8 frames noised at one sigma, contexts replaced only in c, left noisy in uc" consistent with what the
   context positions look like during sampling? Is the uniform-index sigma distribution a mismatch with the
   log_snr_shift=2.4 sampling schedule that matters?
2. Numerics. bf16 autocast in training vs fp16 autocast at sampling; activation checkpointing (ckpt_forward) vs
   VMemModel.forward equivalence; LoRA placement (all Attention to_q/to_k/to_v/to_out[0]) and zero-init equality.
3. Variant B. Warp channels appear in both c and uc. Does that change what classifier-free guidance amplifies in a
   way that biases B-mem vs the B2 warp comparison? Training warps are computed with CUT3R on GPU; evaluation warps
   are the S140 CPU warps (28-42 dB apart on 3 chess windows). Is that a train/test mismatch that matters?
4. Leakage and splits. Any chess or RGB-D Scenes frame in training? Monitor split really unused? Does the memory-
   context construction in build_clips_s141.py match S139's pose-only selection (pose_arms_s139.py)?
5. Evaluation. Do the eval plans reproduce the exact S139 static_recent / mem_vmem contexts and the S140 warp files?
   Is the fidelity gate (zero-init adapters reproduce the base S139 RTX 3090 output byte-for-byte) a valid check and
   is it implemented correctly? Does analyze_s141.py implement the frozen primaries, unit, bootstrap and verdict
   exactly? Is comparing against base outputs generated earlier by gen_s139.py legitimate?
6. Interpretation. Even if B beats the warp, what alternative explanations remain (e.g. B learned to copy the warp
   and denoise splat cracks; the RGB-D panel is exposed; 24 windows from 3 sequence pairs are not independent;
   one seed set; training on 7-Scenes makes chess "in-domain")? Even if both are null, is 10000 LoRA steps on 2000
   clips a fair test? State what claim each outcome would and would not support.

Output: write exactly one file, work/agents/CODEX_R254_S141_HOSTILE_REVIEW.md: findings table (issue | severity
blocker/major/minor | evidence file:line | fix | fixable before evaluation without a protocol change? yes/no), then
details. I prefer a correct negative to an encouraging answer.
