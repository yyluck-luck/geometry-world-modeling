# S146 protocol DRAFT — fresh-room replication of S143 on 12-Scenes (codex R264 E1, "FRESH12_RETRIEVAL")

Draft 2026-10-10 ≈ 23:40 UTC, written before any 12-Scenes image was viewed or scored (only metadata files read:
info.txt, split.txt, pose files). To pass a codex gpt-6-astra (ultra) rejection round before freezing.
`new_method_validated=false`, `novelty_authorization=NONE`. Design adopted from
`work/agents/CODEX_R264_IDEATION_AFTER_S143.md` §5 E1 (binding where this draft is shorter).

## Question
Does the fixed rule frozen from S143 — nearest-4 (four bank frames with the smallest mean fp64 pose distance, angle +
0.1·translation, to the four targets; no NMS) — beat VMem's own retrieval (mem_vmem, repaired memory) for VMem's frozen
generator on rooms never used by this project? Secondary: does the S143 warp/generator ranking mismatch recur?

## Data (fresh by project record; 12-Scenes, CC BY-NC-SA 4.0; archive SHA-256 in `zips.sha256`)
Rooms: apt1/kitchen, **apt2/luke**, office2/5a. R264 proposed apt2/bed; by a metadata-only rule fixed here (use the named
room if its sequence0 and sequence1 have all-valid poses, else the first room of the same collection alphabetically that
does) apt2/bed (40 + 6 invalid poses), apt2/kitchen (20 + 0) and apt2/living (10 + 1) fail and apt2/luke (624 + 593
frames, 0 invalid) is used. apt1/kitchen (357 + 358, 0 invalid) and office2/5a (497 + 534, 0 invalid) qualify.
H = sequence0, C = sequence1 (official split.txt traversal boundaries; same scene frame).
Preprocessing (declared, applied to every frame used, including scoring targets): area-resize color 1296×968 → 640×480
(PIL BOX); intrinsics from info.txt scaled per axis with the pixel-centre map (fx 1158.3 → 571.99, fy 1153.53 → 572.00,
cx 649 → 320.24, cy 483.5 → 239.50); poses unchanged. Staged as stage12/<room>/seq-00|seq-01/frame-NNNNNN.{color.png,pose.txt}.
Depth never used.

## Windows (per room, 8; S139 structure)
H20 = sequence0 frames at floor(j·(N_H − 1)/19), j = 0..19; C starts s_i = C_first + floor(i·(N_C − 106)/7), i = 0..7;
bank = H20 + C[s, s+5, …, s+55]; targets C[s+60, +75, +90, +105]; static C[s, +15, +30, +45]. Distinct starts and target
identities checked; no window search. Pose convention chosen by the S139 KPS convention check on bank frames only
(frozen rule: lower median KPS reprojection residual), before any generation.

## Pool (frozen from S143) + one robustness arm
Rules 1–6 exactly as S143 (static, mem_pose [S139 pose_arms logic], mem_vmem [new step-A retrieval with the repaired
memory: KPS init, chunked priming 15/12, NMS-on, RTX 3090], nearest-4, coverage-greedy [32-bank CUT3R + KPS, CPU], random
[rng 259 over rooms/windows in manifest order]); sets sorted by bank index; duplicates merged. Extra arm outside the pool:
mem_vmem in its native retrieval order.

## Generation, seeds, scoring
Frozen VMem (gen_s141.py, zero-init adapters), RTX 3090; discovery seeds 3–6 and evaluation seeds 42, 7, 1, 2, both
generated unconditionally before any target scoring. Score with score_s140.py (PSNR pooled over targets, SSIM). Warps:
S139 CPU B2 pipeline per set (Q_W).

## Primary (evaluation seeds 42, 7, 1, 2)
d_room,s = mean over the room's 8 windows of PSNR(nearest-4) − PSNR(mem_vmem, bank-sorted). Pass if: room-equal mean
≥ +0.20 dB, all 3 room means > 0, ≥ 3 of 4 seed-panel means > 0; the broader wording ("nearest retrieval beats native
VMem retrieval") additionally requires the same against native-order mem_vmem. Secondary: the same on discovery seeds;
nearest − static, nearest − coverage, coverage − mem_vmem; SSIM (an overall decline > 0.01 blocks a quality
recommendation); S143's R_2seed_hindsight and local-vs-global on the 6-rule pool with nulls recomputed on this panel;
copy/warp references. Room and seed panels are the reporting units; window bootstraps descriptive.

## Gates, budget, stop
Replay of an archived exposed cell; exact cells; finite outputs; fresh dirs; four distinct contexts per set; finite KPS.
Cap 24 RTX 3090 GPU-hours. One run, no retuning; INELIGIBLE/INVALID outcomes are not negative results.
