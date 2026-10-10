# S146 protocol — project-fresh replication of the S143 retrieval finding on 12-Scenes (frozen)

Frozen 2026-10-11 ≈ 00:10 UTC, before any 12-Scenes image was inspected for a decision or scored (metadata files read;
JPEG frames decoded only by the deterministic staging resize). Supersedes `PROTOCOL_DRAFT.md`. Idea: codex R264 E1;
corrected by codex `gpt-6-astra` (ultra) rejection round R265 — its "Corrected minimal specification" (§1–8,
`work/agents/CODEX_R265_S146_DRAFT_REJECTION.md`) is adopted in full and is part of this protocol.
`new_method_validated=false`, `novelty_authorization=NONE`. Claim type: project-fresh, prospective finite-panel replication
of a chess-derived fixed rule (not absence from VMem/CUT3R pretraining).

## Binding summary (R265 governs where shorter)
- Panel: apt1/kitchen, apt2/luke, office2/5a (in that order). **Metadata-informed amendment:** R264 named apt2/bed; a
  complete-traversal rule (sequence0 and sequence1 all-valid poses; else first alphabetical room of the collection that
  passes) selected apt2/luke after apt2/bed (40 + 6 invalid), apt2/kitchen (20 + 0), apt2/living (10 + 1) failed. This targets
  rooms with complete tracking, not an unbiased room sample. No further substitution after any geometry/RGB/score.
- Receipts sealed before preparation outputs are used: archive SHA-256s, info.txt/split.txt contents and hashes, explicit
  parsing of the `sequence0`/`sequence1` labels and ranges (inclusive, disjoint, gap-free), pose validation (finite 4×4,
  last row [0,0,0,1], orthonormal rotation, det ≈ 1), color extrinsic identity, intrinsics (`METADATA_RECEIPT.json`).
- Windows (original frame ids): H_j = H_first + floor(j(N_H − 1)/19); s_i = C_first + floor(i(N_C − 106)/7); bank = H20 +
  C[s..s+55 step 5]; targets C[s+60, 75, 90, 105]; static C[s, 15, 30, 45]. H/C = assay availability order. Frame offsets are
  frame indices (cadence unverified). Window dependence and cross-window context overlap disclosed.
- Images/cameras: one PIL BOX resize 1296×968 → 640×480 for all frames; K by the zero-based pixel-centre map; the legacy
  gen_s141 VMem K conversion is kept unchanged for every arm (≈ 0.6 px principal-point approximation disclosed).
  CUT3R crop/depth lookup unchanged. Pose convention per room by the S139 detector on the five fixed H frames (fail on
  non-finite or tie); F = diag(1, −1, −1, 1): gl → generator P·F, geometry P; native → generator P, geometry P·F.
- Retrieval: step A per room (INIT=kps, chunks 5 + 15 + 12, NMS on at both calls, threshold reset per window); validity
  gates — finite KPS at every construction, four unique raw ids (no repeat-fill), exact 32-frame memory coverage.
- Pool: rules 1–6 as S143 (2 = S139 pose/NMS rule; 3 = fresh mem_vmem sorted; 4 = nearest-4; 5 = coverage-greedy; 6 =
  one default_rng(259) stream over the declared room/window order) + native-order mem_vmem outside the pool.
- Generation: frozen base (gen_s141, VARIANT=A, ADAPTER=NONE), RTX 3090, discovery seeds 3–6 and evaluation seeds 42, 7,
  1, 2, both unconditional; all predictions and geometry packages hashed (sealed) before any target scoring. Replay of one
  archived exposed cell first. Scoring: S140 per-generation metric; S143 per-set warp/copy table.
- **Primary (evaluation seeds):** d(r,s) = mean_w [PSNR(nearest-4) − PSNR(mem_vmem, bank-sorted)]; D = mean over r,s;
  pass iff D ≥ +0.20 dB, every room mean D_r > 0, and ≥ 3 of 4 seed means D_s > 0. The same full gate against native-order
  mem_vmem is required for the broader wording; otherwise "slot-policy-dependent advantage". Secondary as R265 §6–7
  (room × seed matrix, LOO, SSIM with the 0.01 quality block, nearest − static/coverage, coverage − mem, copy/warp,
  history fractions, discovery R_2seed_hindsight and local-vs-global with nulls recomputed, two-invocation sealing).
- Budget: cap 24 RTX 3090 GPU-hours (generation ≤ 1,344 four-target outputs before deduplication + step A + replay).
  Queue: S143 confirmation → S144 → S145 → S146 (CPU preparation in parallel). INELIGIBLE/INVALID_ASSAY ≠ negative result.
