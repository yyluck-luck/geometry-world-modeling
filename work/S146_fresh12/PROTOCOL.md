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

## Amendment 1 (2026-10-11 ≈ 00:00 UTC; before any S146 generation or target scoring) — convention gate
The implemented convention gate required both residuals to be finite, stricter than R265 §3 ("fail on non-finite, tied or
ambiguous diagnostics" for the decision). Result on the five fixed H frames: apt1/kitchen gl 32.3 px vs native 109.8 px;
apt2/luke gl 140.3 px vs native non-finite; office2/5a gl 15.6 px vs native non-finite. A non-finite residual means no scale
makes that convention consistent. Corrected rule, fixed now: the winner's residual must be finite and the loser's must be
non-finite or ≥ 2× the winner's; AND an independent bank-only agreement check on a second fixed frame set per room — the
first window's recent C frames C[s0, s0+5, …, s0+20] (bank frames, never targets) — must select the same convention
under the same rule. Disagreement or failure → that room INELIGIBLE (no substitution). The 12-Scenes README does not state
the axis convention; the release's pose family is that of 7-Scenes, for which the same detector selected gl (S139).

## Amendment 2 (2026-10-11 ≈ 02:20 UTC; before any S146 step-A retrieval, generation or target scoring) — robust KPS (KPS-R)
Phase-1 preparation stopped at window apt1_kitchen_s0465: in the 32-frame bank star one history view had < 50 valid
points relative to the root view, so its KPS residual was infinite; KPS averages residuals over views, so the objective
was infinite for every scale and the reported scale meaningless (the gate correctly refused it). Apartment traversals span
several areas; chess (one small room) never produced this: S139 step-A KPS calls 72/72 finite, S143 rule-5 calls 24/24 finite
(so the change below reproduces every chess retrieval exactly). Disclosed side finding: S141 B training warps had 47/2032
clips with a non-finite KPS objective.
**KPS-R** (S146 copy of kps.py only; S139/S143 code unchanged): the scale objective is the mean residual over views with a
finite residual, defined only if at least half of the non-root views are finite (else infinite → gate failure). Identical
to KPS when all views are finite (unit-checked). Applies to every S146 KPS call: rule-5 bank geometry, step-A repaired
memory (VMem's own retrieval), and per-package warps. Gates: kps OK, variant KPS-R, finite positive scale, finite objective,
≥ half of the views with finite positive focal. Fraction of finite views recorded per call. A gate failure remains
INELIGIBLE/INVALID_ASSAY (no substitution).

## Amendment 3 (2026-10-11 ≈ 03:40 UTC; after the bank-only KPS diagnostic, before any S146 step-A selection, generation or target scoring) — operational assay with the original KPS
Adopted in full: codex `gpt-6-astra` (ultra) decision round R267 (`work/agents/CODEX_R267_S146_PATH_DECISION.md`), §3
"Exact proposed protocol amendment" (binding text) and §4 claim wording. Exposure: chosen after reading the bank-only
KPS_DIAG records (`diag/`), which found non-finite original-KPS objectives in 19/72 constructions (11/24 windows) and views
with ~40–47% non-positive depth in apt2/luke and office2/5a. No step-A selection, generation or target score existed.
- The original geometry-qualified primary is INVALID_ASSAY at preflight and unexecuted (not a non-replication).
  Amendment 2's dynamic KPS-R is withdrawn (rejected by R266; file kept as `kps_R_dynamic_REJECTED.py`, never used on TACC).
- Comparator **VMem-KPS-original-operational-v1**: original S139 KPS (SHA 71528da4…) with observer-only logging
  (`kps_orig_obs.py`), step A via `run_retrieval_s146op.py` (NMS explicit at both calls; selector output validated before
  coercion: exactly four integer, unique, in-range indices, no target collision; no repeat-fill; selection receipt before
  the optional render). Observer parity on an exposed chess window (identical contexts, surfels, scales) is a hard gate.
  Internal geometry is diagnostic only (no exclusion for non-finite objectives, depth fractions, default focals).
- Packages: rule 1 static, 2 mem_pose, 3 mem_vmem (bank-sorted), 4 nearest-4, native-order mem_vmem. Deleted prospectively:
  rule 5, rule 6, discovery seeds 3–6, warps/Q_W, hindsight/local-vs-global and region claims.
- Global gate: every one of the 24 windows must yield a validated policy output with the declared construction sequence
  (non-root KPS counts [4, 19, 31]); otherwise OPERATIONAL_PANEL_UNAVAILABLE (no dropping, no substitution, no mem_pose promotion).
- Evaluation seeds 42, 7, 1, 2 only; exposed generator replay; sealing before scoring; generation-only scorer
  (`score_gen_s146.py`, S140 metric, no warp reads). Primary as before (D ≥ 0.20, all D_r > 0, ≥ 3/4 D_s > 0) against
  bank-sorted and, for the broader wording, native-order mem_vmem; SSIM block per ordering; nearest − static and
  nearest − mem_pose secondary. Namespace `operational_v1`; ≤ 480 generations; total cap 24 GPU-h.
