# R265 — S146 draft rejection before freeze

Workspace: local Mac checkout. Review of the 2026-10-10 draft; source snapshot at commit 532c29ee4d26674634a91d9f6786cbb24978e5cf, with untracked/concurrently edited stage files identified separately in Appendix A.

**Verdict: reject freezing the current draft unchanged; accept the bounded replication after the corrections below.** The room substitution is defensible as a disclosed metadata amendment, the window arithmetic works for the supplied counts, and anisotropic resizing is not itself a fatal flaw. The actual blockers are incomplete dataset/loader transport, an unspecified camera-convention contract, insufficient retrieval validation, and an analysis implementation that does not enforce the proposed primary gate. This is a prospective test of a fixed retrieval package on a small new panel, not a new-method experiment.

Scope: source/protocol inspection, public documentation, and the read-only CPU arithmetic in Appendix A. No model inference, GPU, training, weights or dataset download, cluster access, or contact with others. Raw 12-Scenes metadata and archive hashes are not present among the local S146 files listed in Appendix A; the room counts, invalid-pose counts, and the assertion of no prior image inspection remain **UNVERIFIED** here. They are not promoted to measurements by quoting the draft. No original deliverable, protocol, ledger, or executable source was modified. The idea-evaluator skill was applied only for targeted flaw/feasibility review; the requested findings/specification format governs this output.

## Findings

Severity means: **BLOCKER** prevents freezing/executing an interpretable assay as currently specified; **MAJOR** needs an explicit protocol or implementation correction; **MINOR** is a bounded clarification. Numerical derivations below are **DERIVED**, conditional on the draft inputs, with the exact command and complete output in Appendix A. Thresholds are proposed/frozen design choices, not measured effects.

| Issue | Severity | Evidence | Concrete change |
|---|---|---|---|
| 1. Replacement is legitimate before outcome inspection, but changes E1 eligibility | MAJOR | The draft rejects a room if either entire traversal contains any invalid pose (work/S146_fresh12/PROTOCOL_DRAFT.md:14–17). R264 requires valid selected frames, without compressing gaps, rather than every unselected pose being valid (work/agents/CODEX_R264_IDEATION_AFTER_S143.md:177–180). The new stager checks all traversal poses (work/S146_fresh12/stage_12scenes_s146.py:36–40). | Keep apt1/kitchen, apt2/luke, office2/5a, but label the complete-traversal rule a metadata-informed amendment. Do not claim apt2/bed necessarily failed the original selected-frame rule. Preserve all inspected candidate names, exact rejected frame IDs/reasons, metadata hashes, and when the rule was chosen. No subsequent replacement based on geometry, retrieval, RGB, or scores. This targets rooms with complete pose tracking, not an unbiased sample of all rooms. |
| 2. Traversal and calibration assertions lack locally checkable receipts | BLOCKER | Draft :13–21 gives counts and a bare zips.sha256 filename. Appendix A lists only the draft and staging script in the local stage. The stager extracts anonymous start/end pairs with a regex and uses the first two, without validating sequence labels (stage_12scenes_s146.py:28–33). Public dataset documentation supports multiple aligned scans, not these exact split entries; see L1 below. | Before freeze, attach exact archive/hash identities, info.txt and split.txt contents/hashes, parsed sequence labels/ranges, and pose-validation/exposure receipts at named paths. Assert sequence0/sequence1 identities, inclusive endpoints, disjoint ranges, and no gaps in the original IDs; do not infer them merely from regex order. Report remote/unavailable receipts as unverified until inspected by the executing agent. |
| 3. “The existing pipeline runs unchanged” is false | BLOCKER | pose_arms_s139.py:16 appends chess; convention_check_s139.py:12–13 fixes the chess manifest/root; baselines_s139.py:16–18 fixes root/K/manifest. S143 build_pool_s143.py:14–17 imports old chess data and old retrieval plans; warps_s143.py:20 and score_warps_s143.py:10 do likewise. build_plan_s143.py:14 hardcodes scene_dir=chess/convention=gl, and :20 looks up the new first window in the old plan. | Use S146-owned adapters of these helpers with explicit per-room root, K, manifest, convention, and fresh retrieval inputs. Preserve algorithms; do not edit old stage sources. Use a separate exposed replay plan. Require room-qualified frame identities and unique ordered-package cache keys. Hash the actual transported sources, not just the original helpers. |
| 4. Raw-to-staged K is sound under its stated pixel convention; the full chain is not exact | MAJOR disclosure; MINOR numerical approximation | The stager applies the half-pixel affine map at :29–31. gen_s141.py:75–83 applies area resize/crop but scales principal points without the half-pixel term. VMem uses image coordinates i+0.5 (data/S134_tacc/vmem_src/utils/util.py:65–72,141–165). Integer-center projection is used in work/S137_geometry_baselines/geometry_baselines.py:49–61. Appendix A gives staged fx=572.0, not draft :20's 571.99, and the resulting principal-point discrepancy. | Keep both axis factors. Explicitly distinguish zero-based pixel-center K for staged geometry from the frozen legacy VMem K. For the primary replication retain the legacy generation conversion identically across all arms, disclose its nominal 0.6 model-pixel edge-coordinate discrepancy, and check the known mapping on exposed/synthetic fixtures. Do not silently apply a +0.1 “fix”: it does not resolve the ray convention. A corrected ray-K path is a separate intervention. |
| 5. CUT3R/KPS do not consume the supplied anisotropic K end to end | MAJOR interpretation | Step A only passes dataset K to KPS under INIT=kpsK, not INIT=kps (run_retrieval_s139.py:66–67,92–93). KPS uses one estimated focal and centered principal point; even known_K averages fx/fy (kps.py:25–30,94–97,114–120). The pipeline reconstructs without a K argument and renders with averaged estimated focal, a 0.65 factor, and centered principal point (pipeline.py:980–996,635–645). | Freeze INIT=kps and report learned/estimated focal geometry as part of the repaired VMem package. Do not switch to kpsK or call the surfel query physically calibrated. The nominal resized fx and fy are nearly equal here, so anisotropy alone is not a reason to reject the data. Record KPS residuals/focals and the distinction from K-based projection. |
| 6. Color-camera extrinsics and pose convention are unresolved; a per-room winner is not propagated by the old helpers | BLOCKER | The stager reads the color intrinsic only and copies poses unchanged (:29–31,39–45). The convention detector compares gl/native using only the first bank's first five frames per pair (convention_check_s139.py:22–29). Step A converts by the selected convention (:74–81), then VMem flips Y/Z (pipeline.py:950–955). S143 geometry instead passes raw poses and projects with raw poses (build_pool_s143.py:65–67; warps_s143.py:44–49). | Verify what camera the released pose describes and whether a color extrinsic is already incorporated; do not apply or omit an extrinsic by guesswork. Specify the detector's exact five H frames, finite residual/tie failure handling, and one result per room. Carry the resulting coordinate convention through retrieval, generation, coverage, and warps, as specified below. Finite poses and determinant near one alone do not establish a valid rigid transform or calibration. |
| 7. CUT3R crop/depth mapping can be reused after staging, but has a reduced field of view | MAJOR disclosure | The actual PIL path resizes the 576-square image to 512-square and crops to 512×384 when square_ok=False (data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py:298,338–343,446–488). The inverse lookup is explicitly hardcoded for 640×480 at work/S143_context_ranking/warps_s143.py:30–33 and build_pool_s143.py:42–45. | Keep those grids and formulas only after asserting staged dimensions. Preserve zero depth outside the supported crop, one-pixel splatting and nearest fill; do not extrapolate depth into discarded regions. Report crop support, projected coverage, and holes. The claim concerns the central 576×576 scoring view, not the full raw RGB frame. No raw dataset depth is used; predicted CUT3R depth is used extensively. |
| 8. Step A is mostly dataset-generic, but repaired priming and NMS state are essential | BLOCKER if omitted | Its root/ref parser is generic (run_retrieval_s139.py:71–81). It clears persistent state and initial_threshold (:83–88), initializes five frames and calls retrieval at that point (:99–107), then temporarily sets target_num_frames to each priming chunk (:109–114). NMS chooses sorted pairwise distance index int(n×0.5), i.e. the upper-middle of ten distances, not an interpolated median (pipeline.py:674–698). | Run per-room manifests: the combined staging manifest lacks the top-level scene_dir required by Step A (stage_12scenes_s146.py:59–64 versus run_retrieval_s139.py:72). Freeze 5+15+12 coverage, reset per window, restore target_num_frames=4, and explicitly enable NMS at both the initialization call and final query. Save threshold, candidate identities/order, device/numeric settings, and final ordered contexts. Do not recompute the threshold on all 32 frames. |
| 9. Existing receipts do not enforce all draft validity gates | BLOCKER | Step A repeat-fills short retrieval results at :118 and records KPS/memory coverage without asserting them at :128–137. It catches errors and emits PARTIAL instead of necessarily stopping (:135–140). KPS can log FALLBACK (kps.py:74–77). S143 warp construction only logs KPS status (warps_s143.py:43–54), unlike pool construction's finite checks (build_pool_s143.py:74–76). | Before generation, require every window valid, exactly four distinct raw contexts, exact 32-frame memory coverage, and successful finite KPS at every construction/warp call. Reject short sets rather than repeat-fill. Validate bounds and finiteness of depth/warp/output arrays and exact expected cells. Save all failures; no dropping windows/rooms or treating missing cells as negative scientific evidence. |
| 10. Different traversals do not establish useful revisit overlap at selected targets | MAJOR | L1 supports repeated captures/common coordinates. R264:178–181 separately requires genuine overlap. The S139 history-favourable test is only min pose distance to the last target, H versus C (pose_arms_s139.py:49–57); it neither tests visibility nor absolute proximity. | Keep H=sequence0, C=sequence1 as assay availability order, not acquisition chronology. Report target/H pose distances, orientation changes, and bank-derived historical projected support without reading target RGB or selecting alternative windows. Do not call a room label or dH<dC proof of a visible revisit. If overlap cannot be established, retain the fixed-panel retrieval comparison but drop the revisit interpretation. |
| 11. Window arithmetic passes; global hidden-target wording would fail | MAJOR leakage/dependence clarification | Appendix A: all supplied counts yield eight distinct starts, 32 distinct targets, zero own-window target/bank collisions, and the final target exactly at N_C−1. In apt2/luke, twelve target identities occur in other windows' C banks. The stager decodes all frames, including targets (:36–45). R264:180,194 permits context sharing and requires predictions sealed before scoring. | State the boundary per window: target RGB/depth cannot enter that window's model/geometry/rule choice. Deterministic staging may decode targets; later windows may legitimately use those frames as context. Reset all inference state and forbid score-driven adaptation across windows. Hash all outputs before any target-scoring phase. Do not claim all target bytes globally unread. |
| 12. Frame offsets are not verified physical time offsets | MAJOR claim limitation | Draft :25–26 uses frame IDs. The release/paper and Microsoft documentation checked in L1/L2 do not establish the effective archived sampling cadence for this comparison. Step A indexes integer IDs, not timestamps (:75–81). | Keep the fixed frame-index assay, not “matched seconds” or matched motion. Verify timestamps/cadence if available and report camera displacement/rotation over the offsets. Without timestamps, mark effective 12-Scenes versus 7-Scenes frame-rate equivalence UNVERIFIED. Do not infer it from the sensor's advertised rate or invent a replacement stride after inspecting performance. |
| 13. Primary definition is good, but S143 confirmation code implements another gate | BLOCKER | Draft :41–47 requires three positive room means. analyze_s143_confirm.py:66,77 merely rejects two negative pairs, allowing one negative or zero room. Its rule contrast uses discovery-selected r_disc (:82–85). score_s140.py:30–45 pools target SSE inside each generation before converting to PSNR. | Compute the S146 primary with rule 4 fixed now, explicit equal room/seed weighting, all three room means strictly >0, and at least three positive seed panels. Average per-generation PSNR differences after target pooling; do not pool image SSE over the entire dataset or replace rule 4 with r_disc. |
| 14. Discovery seeds are useful only for the separate secondary question; selector sealing is weaker in current code | MAJOR | R264:192–209 adopts both blocks and target-informed selector diagnostics. analyze_s143_confirm.py:11,43 reads evaluation scores before writing frozen selections at :57. The original fold/null procedures are at analyze_s143.py:11,44–57,60–99. | Retain seeds 3–6 unconditionally only because the ranking/headroom secondary is retained; they cannot select the primary rule or decide whether to run evaluation seeds. Split discovery selection and evaluation-score reading into separate invocations. Treat nulls and window bootstraps as descriptive/model-based diagnostics; they do not create independent rooms. |
| 15. Nearest-versus-mem is an ordered-package comparison, not an NMS or geometry ablation | MAJOR interpretation | Nearest uses all-bank fp64 mean distances to four targets (build_pool_s143.py:24–26,59–62). Native retrieval uses the last target at K=4, surfel-filtered candidates and device-side ranking/NMS (pipeline.py:635–645,655–750). Order affects the first-camera scale/reference (pipeline.py:1099–1119,1136–1140). | Keep native-order mem outside the six-rule pool and apply the full gate to it before broadening wording. Merge only identical ordered packages, not equal memberships in different orders. Report history fractions and nearest−static. Neither a pass nor a failure isolates NMS, historical memory, geometry usefulness, or an autoregressive video mechanism. |
| 16. Budget is plausible only as a conditional cap; the queue is missing | MAJOR | DERIVED upper bound is 1,344 generations and 16.8 GPU-hours at an assumed 45 seconds, leaving 7.2 hours inside the 24-hour cap (Appendix A). This is generation arithmetic, not new runtime evidence. S144 already has a frozen cap/order (work/S144_A_wgs/PROTOCOL.md:6,28); S145 follows S144 (work/S145_B_diagnosis/PROTOCOL.md:5–6,16). Their chains wait for S143 confirmation and S144 respectively (s144_chain.sh:7; s145_chain.sh:6). | Count retrieval, replay, loading, generation and GPU checks against the cap; separately bound CPU preparation/scoring and waiting time. Preserve the existing queue, then run S146 on released capacity. S146 need not depend scientifically on S144/S145 passing. Do not infer that R264's “E1 first” overrides those existing jobs or promise a one-day elapsed completion. |
| 17. Scorer reuse needs explicit package indexing and numeric checks | MAJOR | score_s140.py:39–43 caches warp summaries by window_id, although S146 has multiple context-set warps per window. It iterates files and skips unknown keys (:26–30), and pred_u8 infers normalization from the minimum value (:15–18). S143 score_warps_s143.py:43–47 is set-indexed. | Use the set-indexed S143 warp table as Q_W; never use S140's window-keyed warp summary for set ranking. Preserve the generator/scorer normalization contract with exposed fixtures, assert valid shape/range/finiteness, and validate complete expected cells externally. A new range policy is not silently introduced under “unchanged scorer.” |

## Corrected minimal specification

### 1. Scope, provenance, and stopping population

Freeze one S146 protocol for the exact panel apt1/kitchen, apt2/luke, office2/5a, in that order. Declare the complete-traversal validity amendment and its metadata exposure history. The claim is **project-fresh, prospective finite-panel replication of a chess-derived fixed rule**. Freshness must be checked against named project manifests/hashes; it does not establish absence from VMem/CUT3R pretraining.

Before decoding fresh RGB for experiment preparation, seal the exposure audit, archive hashes, raw metadata, parsed split ranges, selected IDs, and pose checks. Validate finite 4×4 matrices, last row [0,0,0,1], rotation orthogonality/determinant with declared numerical tolerances, metric translation units, positive finite intrinsics, and camera/extrinsic identity. The staged code's determinant check alone is insufficient (stage_12scenes_s146.py:39–40). Use immutable fresh output directories; its current “skip existing color file” behavior (:41–44) must not accept a stale resize mixed with newly copied poses/K. Attach full source/config/checkpoint hashes and exact execution commands before a future run. This review has not verified weight bytes.

No substitutions, frame compression, alternate starts, different geometry settings, or new selectors after fresh geometry/output inspection. A technical failure is INELIGIBLE/INVALID_ASSAY; a complete valid comparison that misses its gate is a scientific non-replication. A valid small estimate with a wide uncertainty range is not evidence of equivalence.

### 2. Windows and traversal meaning

Parse the named sequence0 and sequence1 metadata entries explicitly. H is available before C in the assay; this does not assert physical recording order or use the relocalization training/test labels as a temporal guarantee.

Use original frame IDs:
- H_j = H_first + floor(j(N_H−1)/19), j=0,…,19.
- s_i = C_first + floor(i(N_C−106)/7), i=0,…,7.
- Bank = H20 followed by C[s+0,5,…,55]; targets = C[s+60,75,90,105]; static = C[s+0,15,30,45].

**DERIVED**, conditional on the unverified counts in the draft:

| Room | C-relative starts | Last target, C-relative | Distinct target IDs |
|---|---|---:|---:|
| apt1/kitchen | 0,36,72,108,144,180,216,252 | 357 | 32 |
| apt2/luke | 0,69,139,208,278,347,417,487 | 592 | 32 |
| office2/5a | 0,61,122,183,244,305,366,428 | 533 | 32 |

These fit a 106-frame inclusive span. The frames within a room share H20 and nearby trajectory content; different targets do not make windows independent. Preserve the cross-window context overlaps listed in Appendix A and disclose them. Report the frozen S139 history-favourable stratum without choosing or discarding windows by it. Add descriptive historical projected support from the already permitted bank-only geometry and target poses; no support or ambiguous overlap means no supported revisit claim. No new overlap threshold is tuned on target scores.

Effective sampling cadence is unresolved. The primary uses frame indices. Do not translate 60–105 frames into seconds without an archive-specific cadence/timestamp receipt; even equal frame rates would not ensure equal camera motion.

### 3. Explicit image and camera contract

Adopt the stager's zero-based integer-center convention for the supplied raw color K, after checking metadata interpretation. For raw coordinates:

x_stage = (x_raw + 0.5)·640/1296 − 0.5,
y_stage = (y_raw + 0.5)·480/968 − 0.5.

Use PIL BOX once to create 640×480 RGB PNGs, both for allowed context and scoring references. Preserve source-ID mapping and full-precision calibration in the manifest; declare any text serialization precision. All later loaders must consume this same staged representation, not resize the raw JPG by an alternate shortcut.

**DERIVED** nominal K from the draft constants:
- fx=572.000000000, fy=571.998347107;
- cx=320.240740741, cy=239.500000000.

The axis scales are 0.493827160494 and 0.495867768595. Their ratio is 1.004132231405; different raw focal lengths almost cancel this anisotropy in the staged K. A blanket rejection for nonuniform scaling would be unjustified.

The frozen legacy model input remains staged 640×480 → area resize 768×576 → columns [96,672), giving 576×576. Keep gen_s141.py:75–83 unchanged for the primary's VMem K, with nominal principal point (288.288888889,287.4). The exact integer-center affine map would give (288.388888889,287.5); expressed for VMem's edge-based i+0.5 ray grid it would give (288.888888889,288.0). Thus the frozen path is an inherited nominal 0.6-pixel principal-point approximation under this convention, not exact physical ray preservation. This is a coordinate discrepancy with unmeasured output impact, not a bound on score error; applying it to all arms does not prove cancellation. Record it and do not choose between K policies from fresh-room scores.

CUT3R's additional 512 resize and vertical crop by 64 are retained. The staged-to-CUT3R depth lookup remains:
x_d = round(((u+0.5)·1.2−96)·512/576−0.5),
y_d = round((v+0.5)·1.2·512/576−64−0.5).
Out-of-range samples remain zero. These are pixel-center correspondences, not a guarantee that estimated depth is accurate. KPS keeps estimated scalar focal/centered principal point; dataset K remains the projection calibration for coverage/warps. The scalar geometry assumption, reduced depth support and default calibration are limitations.

For poses, let F=diag(1,−1,−1,1), and let P be the verified released color-camera pose after any documented extrinsic composition. If the convention detector selects gl: P_generator=P·F and P_geometry=P. If it selects native: P_generator=P and P_geometry=P·F. The latter geometry transform applies to both context and target in CUT3R/coverage/warps. Do not send native to generation while leaving a gl-only CPU baseline unchanged. Use the first five fixed H frames per room for the existing detector, choose the lower finite diagnostic, and fail on nonfinite or exactly tied diagnostics rather than selecting via generation quality. Its median_reproj_px field is actually the mean of per-view penalized median residuals (kps.py:18–41,99,118–120); retain that existing scalar rather than silently changing the statistic. A bank-only multi-view projection check must agree with the declared physical camera convention; a lower residual alone cannot certify calibration.

Before fresh inference, verify the affine/crop/depth mapping and room routing on exposed or synthetic fixtures, and replay one preselected archived exposed generation with its original K and ordering. The new dataset's preprocessing has no pre-existing prediction archive to replay; do not confuse these checks.

### 4. Retrieval and six-rule construction

Run Step A separately on each room manifest, with INIT=kps, POSE_CONVENTION from qualification, four context frames, four targets, translation weight 0.1, NMS enabled, and the declared RTX 3090 numerical configuration. Preserve initial five H frames, then chunks [15,12]. Freeze/reset the first-five threshold per window. Log configuration values and effective geometry behavior; copying a helper name does not pin its loaded inference.yaml.

At every construction require successful KPS, finite positive scale/focals and usable depth, four unique retrieved raw IDs, and exact bank memory coverage. Save candidates, counts, first-five threshold, raw order, sorted order and full receipts. If a fresh room yields insufficient candidates, preserve the failure rather than repeating frames or substituting pose-nearest contexts. Preserve and disclose that pipeline.py:996 extends surfel_Ks with the full reconstruction's focal estimates at each priming stage; the retrieval average at :637 therefore contains repeated earlier-frame estimates. Do not silently replace it with a once-per-frame mean. Save the actual selection-call inputs rather than treating the later diagnostic render as identical: Step A uses raw q[-1] for that render (:124–126), whereas selection applies average_camera_pose (pipeline.py:635).

The six rules remain:
1. fixed static;
2. original S139 pose/NMS rule;
3. freshly retrieved repaired mem_vmem, sorted by bank index;
4. four minimum all-bank mean fp64 pose distances to all four targets, no NMS;
5. existing context-only CUT3R/KPS coverage-greedy rule;
6. random without replacement using one PCG64/default_rng(259) stream across the complete declared room/window order.

Preserve each rule's original arithmetic and tie policy; do not pretend all rules use fp64 or identical queries. Coverage and per-set B2 retain niter=0, SPLAT=1 and nearest fill (build_pool_s143.py:66; warps_s143.py:46; geometry_baselines.py:23,67–75). Step A separately forwards its pinned inference.yaml niter (run_retrieval_s139.py:106,112); record that setting instead of assuming it is zero. Do not reset the random stream per room. The all-room pool needs per-window scene_dir/K/convention metadata. Merge identical ordered tuples inside each window. Add native-order mem as one separately keyed package outside the selector pool; merge its generation only if its full ordered tuple is identical to an existing package. Keep one independent geometry reconstruction per ordered package where required.

### 5. Generation, scoring, and leakage

Use the frozen base via gen_s141 with VARIANT=A, ADAPTER=NONE, zero-initialized adapters, fixed sampler/config and paired seed resets. Separate cache identities by room, window and ordered package; no cache or geometry state crosses window boundaries. gen_s141.py:170–188 makes ctx_group correctness consequential.

Generate both blocks unconditionally: discovery 3,4,5,6 and evaluation 42,7,1,2. Seal/hash all planned predictions and all context/geometry packages before target scoring. Deterministic target staging is permitted; neither human/model inspection of target content for decisions nor per-window target leakage is permitted. Target poses/K are allowed common inputs. Raw target depth remains unused.

Score the same staged reference view for every rule with the frozen S140 per-generation metric: SSE pooled over all four targets and RGB channels, then −10log10 of normalized MSE; SSIM averaged over targets. Preserve/report uint8 conversion. Validate four-target shape, finite arrays, declared value range, correct identities, exactly one score per expected package/seed, and no missing or extra cells. Do not rely on file count or process exit alone.

Use S143's per-set warp/copy table for Q_W and same-set/whole-bank references. Do not interpret S140's window-keyed warp summary as a per-package table. All score-producing helpers run only after the seal, including baselines_s139 paths that score while constructing outputs (baselines_s139.py:27–30,68–71).

### 6. Primary and wording

For r in the three rooms and s in the four evaluation seeds, define:

d_(r,s) = (1/8) Σ_w [PSNR(nearest4,r,w,s) − PSNR(sorted_mem,r,w,s)].

D_r = mean_s d_(r,s), D_s = mean_r d_(r,s), D = mean_(r,s) d_(r,s).

The **fixed-panel pass** requires D≥0.20 dB, every D_r>0, and at least three D_s>0. All cells are required. No discovery-selected rule can replace nearest4. This is an explicit practical replication gate, not a p-value or a claim of twelve independent room/seed replicates.

Apply the same full gate against native-order mem before saying nearest4 beats the native-order repaired VMem retrieval package on this panel. If only the sorted comparison passes, call it a slot-policy-dependent advantage. Even when both pass, candidate filtering, query aggregation, NMS, arithmetic and membership all still differ; none is identified as the cause.

Report room means, seed panels, full room×seed matrix, room range, leave-one-room-out means and descriptive window bootstrap. Report nearest−static, nearest−coverage and coverage−mem, same-set/whole-bank copy and warp, history fractions, and SSIM for both primary comparator orderings. An overall paired SSIM decline beyond 0.01 blocks a quality recommendation while leaving the PSNR finding reportable. No superiority over coverage/copy/warp is inferred from beating mem.

### 7. Discovery and ranking secondary

The discovery block is unnecessary for the fixed primary but justified by the separately retained S143 ranking question. Keep it for that purpose only. Use the original folds [3,4] versus [5,6], tie rules, bootstrap RNG, and null algorithm for R_2seed_hindsight/local-versus-global; recompute null thresholds on this panel.

After all predictions are sealed, compute Q_W/discovery scores and write/hash c_W, c_G_discovery and r_discovery using only those tables. A second invocation may then load evaluation scores and evaluate the sealed selectors. The existing eager-load confirmation script does not enforce this boundary. These are target-informed assay selectors, not deployable selectors; window bootstraps/null simulations do not establish room-population inference.

If budget is deliberately reduced to evaluation seeds only before any new outcomes, explicitly delete these discovery-dependent secondary claims and amend the protocol. Do not opportunistically decide after seeing the primary. Keeping both blocks as drafted is acceptable; it is not required to rescue the fixed-rule comparison.

### 8. Budget, order, and terminal decisions

The retained design has at most 24×7×8=1,344 four-target generations before ordered-package deduplication. **DERIVED planning arithmetic:** at an assumed 45 seconds each this is 16.8 GPU-hours; the 24 GPU-hour cap leaves 7.2 for retrieval/replay/other GPU overhead. Evaluation-only would be 672 generations/8.4 GPU-hours, but would be a narrowed protocol. These are not S146 timings.

Use complete-cell timing from the exposed replay/timing pilot, including actual loading and checks, to decide whether the frozen workload fits before fresh scoring. Record occupied GPU time separately from elapsed waiting and CPU work. A bounded CPU preparation/scoring allowance is required; full-bank and per-set CUT3R work is not free merely because it is on CPU. No guaranteed one-day turnaround follows.

Default execution order: already committed S143 confirmation → S144 → S145 → S146, with nonconflicting CPU preparation in parallel. No remote state was checked here, so the chain files establish intended order, not current job activity. S146 is scientifically independent of S144/S145 outcomes. A different allocation/priority requires a prospective scheduling amendment, not another outcome-dependent design round.

At the cap or a failed interface gate, stop with the appropriate incomplete/invalid status and retain all artifacts. A valid failed primary means “no replicated fixed-rule advantage on this panel.” If only target-informed headroom survives, report that diagnostic without proposing a fresh-room-trained selector on the same targets. No NMS causal claim, general memory-benefit claim, new-method validation, or temporal video-quality claim follows.

## Verified public sources and unresolved literature details

**L1.** arXiv:1603.05772v1, **“Learning to Navigate the Energy Landscape,”** §7.3 describes the Structure.io/iPad captures, raw color resolution and separate capture/alignment process; its relocalization training procedure also uses synthesized views. Use the original captured release images here, not that synthesized training protocol. The [paper](https://arxiv.org/pdf/1603.05772) and [current official release](https://graphics.stanford.edu/projects/reloc/) are not interchangeable specifications: the current release states multiple globally aligned scans, camera-to-world poses, default intrinsics without performed calibration, and CC BY-NC-SA 4.0. The paper's calibration wording is stronger. Use release metadata and preserve uncertainty. Neither source verifies the draft's exact local sequence ranges or effective archive frame cadence.

**L2.** The [official Microsoft 7-Scenes documentation](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/) describes handheld Kinect sequences at 640×480 and raw uncalibrated images/default depth intrinsics. It does not establish matching effective temporal sampling with these 12-Scenes archives. A commonly repeated sensor frame rate is insufficient evidence for an archived frame-ID-to-time conversion; no verified equality is asserted here.

**L3.** arXiv:2506.18903v3, **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,”** §3.1, §4.3 and §4.4/Table 4 distinguish the memory mechanism, autoregressive revisitation evaluation, and camera-distance ablation. [Verified paper](https://arxiv.org/html/2506.18903v3). S146 is a fixed real-image-bank, repaired implementation assay with a different nearest rule and ordering policy; it is not a reproduction of the paper's camera-distance row or an autoregressive memory benchmark. The implementation-specific last-target/candidate/NMS claims above come from pinned source, not extrapolation from the paper.

## Verification record and delivery boundary

Appendix A contains the complete new numerical/provenance computation used by this review; Appendix B records a subsequent source-dependency and draft-hash check. Neither imports model code or reads images. The numerical command treats the draft counts/calibration constants as inputs. Source inspections are cited directly at file:line above; none of the proposed replay/geometry/model checks is claimed as executed. No repository test suite or linter was run because this task changes only the review document.

The initial checkout already contained untracked S143 RESULT, S146 files, R264 and review prompts; they were left untouched. Follow-up work belongs to implementation/freeze of the corrected transport and then the one bounded experiment, not another unbounded review loop.

Changed file: work/agents/CODEX_R265_S146_DRAFT_REJECTION.md only.
State remains new_method_validated=false; novelty_authorization=NONE.

## Appendix A — Exact command and complete output

~~~sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
from fractions import Fraction
import hashlib, json, subprocess
print('HEAD', subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip())
files = ['work/S146_fresh12/PROTOCOL_DRAFT.md','work/S146_fresh12/stage_12scenes_s146.py','work/S139_crossseq_revisit/run_retrieval_s139.py','work/S143_context_ranking/build_pool_s143.py','work/S141_finetune/gen_s141.py','work/S140_warp_guided/score_s140.py','data/S134_tacc/vmem_src/modeling/pipeline.py','data/S134_tacc/vmem_src/utils/util.py']
for f in files:
 p=Path(f); print('SHA256',f,hashlib.sha256(p.read_bytes()).hexdigest())
print('S146_LOCAL_FILES', sorted(p.name for p in Path('work/S146_fresh12').iterdir()))
for room,nh,nc in [('apt1/kitchen',357,358),('apt2/luke',624,593),('office2/5a',497,534)]:
 starts=[i*(nc-106)//7 for i in range(8)]
 hist=[j*(nh-1)//19 for j in range(20)]
 targets=[[s+o for o in [60,75,90,105]] for s in starts]
 banks=[{s+o for o in range(0,60,5)} for s in starts]
 flat=[t for ts in targets for t in ts]
 crosses=sorted({t for i,ts in enumerate(targets) for t in ts if any(t in b for j,b in enumerate(banks) if i!=j)})
 print('WINDOWS',room,json.dumps({'counts_are_draft_inputs':True,'starts_relative_to_C_first':starts,'history_indices_relative_to_H_first':hist,'last_target_relative_to_C_first':max(flat),'unique_targets':len(set(flat)),'own_bank_target_collisions':sum(t in banks[i] for i,ts in enumerate(targets) for t in ts),'target_ids_used_in_other_banks':crosses},sort_keys=True))
sx=Fraction(640,1296); sy=Fraction(480,968)
K=[float(Fraction('1158.3')*sx),float(Fraction('1153.53')*sy),float((Fraction(649)+Fraction(1,2))*sx-Fraction(1,2)),float((Fraction('483.5')+Fraction(1,2))*sy-Fraction(1,2))]
print('STAGED_K_fx_fy_cx_cy', [round(v,9) for v in K])
print('SCALE_sx_sy_sy_over_sx', [round(float(v),12) for v in [sx,sy,sy/sx]])
print('MODEL_K_legacy_fx_fy_cx_cy',[round(K[0]*1.2,9),round(K[1]*1.2,9),round(K[2]*1.2-96,9),round(K[3]*1.2,9)])
print('MODEL_K_integer_center_exact_cx_cy',[round((K[2]+.5)*1.2-.5-96,9),round((K[3]+.5)*1.2-.5,9)])
print('MODEL_K_edge_coordinate_exact_cx_cy',[round((K[2]+.5)*1.2-96,9),round((K[3]+.5)*1.2,9)])
for nseeds in [4,8]:
 n=24*7*nseeds
 print('BUDGET',json.dumps({'seed_count':nseeds,'max_generations':n,'gpu_hours_at_45s':n*45/3600,'reserve_inside_24_gpu_hours':24-n*45/3600},sort_keys=True))
PY
~~~

Complete output (exit code 0):

~~~text
HEAD 532c29ee4d26674634a91d9f6786cbb24978e5cf
SHA256 work/S146_fresh12/PROTOCOL_DRAFT.md bdb55b19d2f96063b267cd4272b16dd3958011bdbf3b7f6dcc6a3aebd892b103
SHA256 work/S146_fresh12/stage_12scenes_s146.py 2262a9b465abfe39aba80b13e415663cfac1da5ea4452be5b368fbd5dabc58f1
SHA256 work/S139_crossseq_revisit/run_retrieval_s139.py 6670478ca26001eb2a011e2f801360893c0d6e2ca67a068b4ba32ab587b039fc
SHA256 work/S143_context_ranking/build_pool_s143.py a338a7cc54fc9d64701f11c5c9c2de6e56f9cd6f12d175069275d2a80f6165d1
SHA256 work/S141_finetune/gen_s141.py c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121
SHA256 work/S140_warp_guided/score_s140.py 61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79
SHA256 data/S134_tacc/vmem_src/modeling/pipeline.py 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255
SHA256 data/S134_tacc/vmem_src/utils/util.py 30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e
S146_LOCAL_FILES ['PROTOCOL_DRAFT.md', 'stage_12scenes_s146.py']
WINDOWS apt1/kitchen {"counts_are_draft_inputs": true, "history_indices_relative_to_H_first": [0, 18, 37, 56, 74, 93, 112, 131, 149, 168, 187, 206, 224, 243, 262, 281, 299, 318, 337, 356], "last_target_relative_to_C_first": 357, "own_bank_target_collisions": 0, "starts_relative_to_C_first": [0, 36, 72, 108, 144, 180, 216, 252], "target_ids_used_in_other_banks": [], "unique_targets": 32}
WINDOWS apt2/luke {"counts_are_draft_inputs": true, "history_indices_relative_to_H_first": [0, 32, 65, 98, 131, 163, 196, 229, 262, 295, 327, 360, 393, 426, 459, 491, 524, 557, 590, 623], "last_target_relative_to_C_first": 592, "own_bank_target_collisions": 0, "starts_relative_to_C_first": [0, 69, 139, 208, 278, 347, 417, 487], "target_ids_used_in_other_banks": [144, 159, 174, 283, 298, 313, 422, 437, 452, 492, 507, 522], "unique_targets": 32}
WINDOWS office2/5a {"counts_are_draft_inputs": true, "history_indices_relative_to_H_first": [0, 26, 52, 78, 104, 130, 156, 182, 208, 234, 261, 287, 313, 339, 365, 391, 417, 443, 469, 496], "last_target_relative_to_C_first": 533, "own_bank_target_collisions": 0, "starts_relative_to_C_first": [0, 61, 122, 183, 244, 305, 366, 428], "target_ids_used_in_other_banks": [], "unique_targets": 32}
STAGED_K_fx_fy_cx_cy [572.0, 571.998347107, 320.240740741, 239.5]
SCALE_sx_sy_sy_over_sx [0.493827160494, 0.495867768595, 1.004132231405]
MODEL_K_legacy_fx_fy_cx_cy [686.4, 686.398016529, 288.288888889, 287.4]
MODEL_K_integer_center_exact_cx_cy [288.388888889, 287.5]
MODEL_K_edge_coordinate_exact_cx_cy [288.888888889, 288.0]
BUDGET {"gpu_hours_at_45s": 8.4, "max_generations": 672, "reserve_inside_24_gpu_hours": 15.6, "seed_count": 4}
BUDGET {"gpu_hours_at_45s": 16.8, "max_generations": 1344, "reserve_inside_24_gpu_hours": 7.199999999999999, "seed_count": 8}
~~~

## Appendix B — Local CPU dependency and source stability

The CPU helper selects the isolated CUT3R source (work/S135_scale_init/repro_kps.py:24–25), while Step A uses RUN_ROOT/vmem (run_retrieval_s139.py:26–27). The checked PIL-inference and KPS files are byte-identical across the local copies, as recorded below. This is not a hash verification of the entire dependency tree or the remote runtime. The draft and stager hashes remain those in Appendix A.

Exact command:

~~~sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import hashlib
p=Path('work/S135_scale_init/repro_kps.py')
for i,line in enumerate(p.read_text().splitlines(),1):
 if 23<=i<=26: print(f'{p}:{i}:{line}')
pairs=[('data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py','work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/surfel_inference.py'),('work/S139_crossseq_revisit/kps.py','work/S135_scale_init/kps.py')]
for left,right in pairs:
 a=Path(left).read_bytes(); b=Path(right).read_bytes()
 print('SAME_BYTES',a==b,left,right)
 print('SHA256',left,hashlib.sha256(a).hexdigest())
for name in ['work/S146_fresh12/PROTOCOL_DRAFT.md','work/S146_fresh12/stage_12scenes_s146.py']:
 print('RECHECK_SHA256',name,hashlib.sha256(Path(name).read_bytes()).hexdigest())
print('REVIEW_EXISTS',Path('work/agents/CODEX_R265_S146_DRAFT_REJECTION.md').is_file())
PY
~~~

Complete output (exit code 0):

~~~text
work/S135_scale_init/repro_kps.py:23:sys.path.insert(0, str(Path(__file__).resolve().parent))
work/S135_scale_init/repro_kps.py:24:SRC = REPO / 'work/S17C_interface_preparation/isolated_vmem_source'
work/S135_scale_init/repro_kps.py:25:CUT3R = SRC / 'extern/CUT3R'
work/S135_scale_init/repro_kps.py:26:WEIGHTS = REPO / 'data/cut3r/cut3r_512_dpt_4_64.pth'
SAME_BYTES True data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/surfel_inference.py
SHA256 data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py 8a348645cd387147c35635f0a6b432d85bcf844e3839bd5a000d8147a85b17d5
SAME_BYTES True work/S139_crossseq_revisit/kps.py work/S135_scale_init/kps.py
SHA256 work/S139_crossseq_revisit/kps.py 71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f
RECHECK_SHA256 work/S146_fresh12/PROTOCOL_DRAFT.md bdb55b19d2f96063b267cd4272b16dd3958011bdbf3b7f6dcc6a3aebd892b103
RECHECK_SHA256 work/S146_fresh12/stage_12scenes_s146.py 2262a9b465abfe39aba80b13e415663cfac1da5ea4452be5b368fbd5dabc58f1
REVIEW_EXISTS True
~~~
