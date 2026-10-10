# S143 protocol DRAFT — same evidence, different consumers: does the context the warp prefers match the context the generator prefers?

Draft 2026-10-10 ≈ 15:40 UTC, from codex R258/R259 ideation (R259 §6 Experiment 1 adopted as the base design).
To pass a codex gpt-6-astra (ultra) rejection round before freezing. Training-free; frozen VMem (byte-faithful sampler:
`work/S141_finetune/gen_s141.py` with zero-init adapters = base, fidelity-verified). `new_method_validated=false`,
`novelty_authorization=NONE`. Independent of S141/S142 outcomes.

## Question
Among a fixed pool of valid four-frame context sets drawn from the same 32-frame history bank, is the set that maximises
the geometric predictor's PSNR (CUT3R+KPS forward warp) also the set that maximises VMem's generated-frame PSNR? A
reproducible shortfall would show that "useful evidence" is consumer-dependent (archived exploratory hint: +0.31 dB
consumer-oracle advantage over the warp-selected set across seed folds; R259 §5.1).

## Panel and pool (frozen before any scoring)
24 S139 chess windows (exposed panel), same banks, targets, gl, RTX 3090, seeds 3, 4, 5, 6. Six construction rules:
1. S139 static_recent; 2. S139 mem_pose; 3. S139 mem_vmem;
4. nearest-4: the four bank frames with the smallest mean VMem pose distance (angle + 0.1·translation, fp64) to the four
   target cameras, no NMS (ties: bank index);
5. coverage-greedy: greedy maximisation of the summed target-view coverage of the union of selected frames, with
   per-bank-frame CUT3R+KPS depth estimated once from the 32 bank frames only (context-only geometry; ties: bank index);
6. random: four distinct bank frames, numpy default_rng(259) drawn sequentially over windows in manifest order.
Every set is sorted by bank index (common slot policy). Identical sets within a window are generated once and keep all
labels. Target poses are allowed; target RGB/depth never enter construction or generation.

## Measurements
Q_W(w,c): PSNR of the B2 warp of set c (warps recomputed for all six sorted sets with the S139 CPU pipeline; context
order is part of the CUT3R input). Q_G(w,c,F): mean generated PSNR over seed fold F ∈ {{3,4},{5,6}}.
c_W(w) = argmax_c Q_W; c_G(w,F) = argmax_c Q_G(·,F) (ties: rule index).
- **Primary R** = window mean of ½{[Q_G(c_G(w,{3,4}),{5,6}) − Q_G(c_W,{5,6})] + [Q_G(c_G(w,{5,6}),{3,4}) − Q_G(c_W,{3,4})]}.
  Claim "consumer-dependent evidence utility" only if R ≥ +0.20 dB, window-bootstrap 95% lower bound > 0 (10k, rng 0),
  no negative pair mean in 2 of 3 sequence pairs, **and** the pool's mean best-minus-worst Q_W spread ≥ 1 dB.
- **Global-rule control** (cross-fitted): choose the single rule with the best mean Q_G on one fold, evaluate on the
  other, exchange. Window-specific structure is claimed only if per-window oracle − global rule ≥ +0.20 dB with lower
  bound > 0; otherwise report "globally biased geometric proxy".
- Secondary: all Q_W/Q_G pairs and ranks per window; Spearman(Q_W, Q_G) within window; SSIM versions; copy-nearest
  from each set and from the whole bank; per pair; seed-fold rank stability.
- Exploratory (only if S141 finished): the same R for the S141 A adapter (does fine-tuning move the consumer's
  preference toward the warp's?).

## Controls and gates
One unchanged replay (S139 mem_vmem window 0, original order, seed 3) must match the S139 output byte-for-byte. Exact
cell counts; finite outputs; fresh directories. Coverage-greedy failures are logged, not replaced.

## Cost and stopping
≤ 6 sets × 24 windows × 4 seeds = 576 generations (≈ 5.8 GPU-h; two RTX 3090 ≈ 3 h) + CPU warps/geometry. Cap 8 GPU-h.
One run; no pool enlargement after scoring; a miss is reported as a miss (not equivalence).
