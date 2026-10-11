# R267 — Preserve the strict failure; run one explicitly amended operational comparison

Local Mac checkout. Decision/rejection review for the brief dated 2026-10-11. Only this document is written. new_method_validated=false; novelty_authorization=NONE.

**Recommendation: choose (d), specifically (a) as the preserved validity record plus a narrowed (b) using ORIGINAL historical KPS.** Keep the rooms, banks, targets, nearest-4 rule, generator and evaluation seeds unchanged. Freeze a separately named operational assay before step A. Remove geometry-dependent coverage/warp/ranking work from its critical path. Do not introduce KPS-R, replace the primary comparator with mem_pose, or search for easier banks in this run.

This can answer whether nearest-4 transfers as a useful context-selection package against the project's historical VMem/KPS implementation on this fixed panel. It cannot establish that nearest-4 beats a geometrically valid retrieval system, that the generator rejects better evidence, or that the published VMem method fails. If that stronger mechanism claim is the actual goal, the answer is **not identifiable from the proposed operational comparison**.

The idea-evaluator skill is applied only to the targeted fatal flaws: changing the comparator while claiming baseline continuity, and making a mechanism claim the experiment cannot identify. This is a replication/design decision, not a novelty score or a new-method proposal.

## 1. Verified evidence changes the premise

Source aliases used below:

- S = work/S146_fresh12/
- H = work/S139_crossseq_revisit/
- C = work/S143_context_ranking/
- P = data/S134_tacc/vmem_src/modeling/pipeline.py
- O = data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py
- R265 = work/agents/CODEX_R265_S146_DRAFT_REJECTION.md
- R266 = work/agents/CODEX_R266_KPSR_REJECTION.md

Every abbreviated file:line citation expands to that exact path. Appendices A–B contain the exact read-only CPU commands and complete outputs for the numerical/provenance checks. They do not rerun reconstruction, retrieval or generation.

**DERIVED from archived MEASURED diagnostic records:** the following counts describe returned initialization objectives, not step-A success or geometric accuracy. Sources: [shard 0](../S146_fresh12/diag/KPS_DIAG_0.json), [shard 1](../S146_fresh12/diag/KPS_DIAG_1.json), [shard 2](../S146_fresh12/diag/KPS_DIAG_2.json); complete aggregation in Appendix A.

| Room | Finite objective at 5 / 20 / 32 frames | Windows with all three returned objectives finite | Minimum dense raw positive-and-finite depth fraction at 20 / 32 frames |
|---|---|---|---|
| apt1/kitchen | 8/8; 8/8; 6/8 | 6/8 | 0.999959290028 / 0.999959290028 |
| apt2/luke | 8/8; 8/8; 7/8 | 7/8 | 0.534271240234 / 0.534215271473 |
| office2/5a | 8/8; 0/8; 0/8 | 0/8 | 0.605941772461 / 0.605941772461 |

Corrections and limits:

1. The brief omits the non-finite apt2_luke_s0971 construction at 32 frames (S/diag/KPS_DIAG_1.json:375–436). Kitchen is essentially, but not literally, all-positive at 20 frames (S/diag/KPS_DIAG_0.json:22–49). Overall, returned objectives are finite in 53/72 calls and in all three calls for 13/24 windows (DERIVED, Appendix A). Thus “most windows fail the finite-objective gate” is not supported by this proxy alone. Stricter downstream eligibility remains unmeasured.

2. The logged objective is a mean of per-view penalized medians: each residual adds a bad-depth penalty to the median reprojection distance (S/kps_diag.py:18–41). Luke's finite values spanning approximately 112.305–159.563 in the 32-frame calls are **not** pure reprojection error or ground-truth geometry error (DERIVED, Appendix A). “Kitchen fine” is too strong: finite objectives and positive depth do not validate scale, calibration or surfaces.

3. The diagnostic reconstructs each prefix independently, with depths=None, niter=0 and CPU (S/diag_kps_s146.py:24–36). Actual step A accumulates state and forwards the configured optimizer settings (S/run_retrieval_s139.py:99–113); the pipeline passes cached depths and accumulates focals (P:980–997). The local configuration mirror specifies niter=400 (data/S134_tacc/vmem_src/configs/inference/inference.yaml:35–36), but the remote effective configuration was not checked. These files are **not a replay of incremental step A**.

4. “grid_valid_any” examines every eighth scale, not the entire search grid (S/kps_diag.py:15,42,100). The JSON also omits the objective curve and grid minimum (S/diag_kps_s146.py:34–36). The original estimator overwrites the grid incumbent with unchecked refinement (S/kps_diag.py:42–55). Therefore an infinite returned objective does not establish an infinite objective at every grid point, let alone every continuous scale. Amendment 2's stronger explanation is not established by these files (S/PROTOCOL.md:51–53).

5. Every view has a finite residual at some sampled scale in 71/72 calls (DERIVED, Appendix A). For those calls, a full-grid support union cannot simply discard the troublesome views, conditional on R266's additional finite-input/focal checks. Whether the safeguarded grid incumbent would rescue them is unknown. R266-fixed-support is not a guaranteed unblocker.

6. Raw dense validity includes the root and all dense pixels before the depth setter; fitting instead uses confidence-selected/subsampled points from non-root views (S/kps_diag.py:85–98,112–117). R266 requires usable valid support and sourced focal/consumer geometry, not a universal all-pixels-positive threshold (R266:60–76). Neither the observed fractions nor finite objectives alone determine strict eligibility. Do not invent a new percentage or residual cutoff from this panel.

7. The H20 prefix is shared within a room by the frozen bank construction (S/PROTOCOL.md:18–20). Repeated history-prefix failures are repeated observations of the same input bank, not independent room failures. “Multi-area banks caused the failure” is a hypothesis: the receipts do not isolate scene extent from root choice, learned correspondences, convention/calibration, or scale search.

**Historical check:** archived S139 step-A receipts contain 72/72 OK calls with finite scale/objective and positive finite focals; the S143 pool contains 24/24 such rule-5 calls (DERIVED, Appendix B, [S139 receipt](../S139_crossseq_revisit/results/stepA_superpod/RETRIEVAL_RECEIPT.json), [S143 pool](../S143_context_ranking/POOL.json)). This verifies the stated historical count, not accurate geometry or equivalence after changing KPS. The archived S143 fresh-seed contrast is +0.7382526642964204 dB (MEASURED, archived analysis, [S143_FRESH.json](../S143_context_ranking/results/S143_FRESH.json):44–64); this review did not recompute it from prediction arrays.

**Current status:** preserve the original geometry-qualified protocol as **INVALID_ASSAY at preflight / primary unexecuted**, reflecting the unresolved construction/qualification failure, not a completed scientific non-replication. Do not report actual mem_vmem eligibility counts before actual step A. The absence of S146 retrieval/generation/target scoring is the executing agent's statement in the brief; it was not verified on clusters here.

## 2. Attack every option

| Option | What is legitimate | Why it is insufficient or dangerous | Decision |
|---|---|---|---|
| (a) Preserve strict geometry gates | Correct for a claim requiring usable reconstructed geometry. It retains the failure instead of manufacturing a clean comparator. | It does not answer the generator package question. “Most windows INELIGIBLE” and “VMem memory fails” exceed the diagnostic evidence. Gate failure is not a negative PSNR result. | Keep this validity record, with the qualifications above. Do not spend another full generation budget merely to certify it. |
| (b), original KPS, operational interpretation | Compare valid ordered RGB/camera packages produced by a fully specified historical policy, including its source-defined numerical degeneracies. | Valid IDs are necessary, not sufficient: the same offered bank, code identity, state/reset rules, leakage boundary, full panel, paired seeds and valid generator outputs must also hold. A weak implementation can lose without demonstrating a consumer-versus-geometry paradox. It is not unmodified deployed VMem. | Recommended only with the explicit amendment below. |
| (b), corrected fixed-support KPS-R | A separately named repaired-system experiment could be legitimate if fixed in advance and failures remain failures. | Changes the comparator after diagnostic exposure; fixed support does not validate excluded views or guarantee a finite joint solution. It cannot inherit historical equivalence from finite winning calls (R266:23,29–56). Dynamic-support KPS-R currently in S/kps.py:39–58 remains rejected. | Do not use either KPS-R version for this primary. |
| (c) Co-visible banks, shorter histories, different roots or rooms | Can define a separate future task if selection is algorithmic, applied identically to all arms, frozen before its outcomes, and every attempted case is retained. | Pose-only does not prove co-visibility; walls/occlusion can defeat it. Selection changes available evidence and the task distribution, can remove nearest-4's difficult cases or eliminate retrieval distinctions, and is informed by observed failures even without target RGB. Further room replacement contradicts the current freeze (S/PROTOCOL.md:11–14; R265:37–41). | No redesign to rescue S146. A later diagnostic-informed follow-up is not an untouched replication of the original panel. |
| (d), promote mem_pose | Gives a useful comparison between two executable pose rules. | Changes the primary question. mem_pose also differs in query, arithmetic and NMS (S/build_pool_s146.py:42–58,85–89); a win does not test VMem retrieval or isolate NMS. | Keep mem_pose secondary. Never substitute it after mem_vmem fails. |
| (d), preserve (a) and narrow (b) | Separates geometry qualification from downstream package utility, keeps the failed cases in view, and tests the fixed practical rule. | Requires admitting that the revised question was chosen after bank diagnostics. No strict-assay “pass” can be recovered by renaming the operational result. | **One recommended path.** |

### Why operational comparison is defensible, and where it stops

For this assay, the intervention is the ordered selection package. VARIANT=A generation loads the selected RGB, supplied context/target poses and K; only VARIANT=B reads warp files (S/gen_s141.py:171–190). The step-A surfels and fitted depths are not passed into the base generator there. Hence geometry accuracy is not a logical prerequisite for observing the downstream effect of the selection package.

It remains essential to distinguish a real policy output from a harness invention. The runner currently repeat-fills the retrieved list (S/run_retrieval_s139.py:117–118). The selector can have too few candidates and accesses the first ranked candidate without an empty-list guard (P:655–671,707–711); its native distance top-up also requires an explicit uniqueness check because candidates may repeat (P:655–658,744–750). “Always four valid IDs” is therefore not verified.

Original KPS can return an arbitrary boundary/refinement result when its objective is non-finite, then initialize depths while leaving a non-finite focal unset (H/kps.py:39–56,99–120). The optimizer sanitizes invalid depths through log storage and exponentiation (O:235–248). These source-defined behaviors may be retained as part of the named operational policy. They must be disclosed, never relabeled as successful geometry. New repair/fallback behavior would be a different policy.

The relevant verified literature is arXiv:2506.18903v3, **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,”** §3.1–3.2, §4.3, §4.4/Table 4 ([paper](https://arxiv.org/html/2506.18903v3)). It separates surfel-based view selection from image/camera-conditioned generation and evaluates camera-distance alternatives under autoregressive cycle trajectories. S146's real-image banks and project KPS wrapper define a different assay. A positive S146 operational result would not reproduce or overturn that paper's ablation, nor establish failure of its intended long-range setting.

## 3. Exact proposed protocol amendment

The following text is the recommended amendment. It is **not applied by this review**. The executing agent must record its actual adoption time and artifact hashes before new step-A execution. The future execution described below is outside this review's no-GPU/no-SSH scope.

> **Amendment 3 — 2026-10-11: diagnostic-informed operational assay, original KPS**
>
> **Status and exposure.** Preserve PROTOCOL.md and Amendments 1–2 as history. The original geometry-qualified S146 primary remains INVALID_ASSAY at preflight and unexecuted; there is no scientific non-replication result. R266's rejection of dynamic-support KPS-R is retained. This amendment is chosen after reading the bank-only KPS_DIAG_0/1/2 records and before S146 step-A selection, generation or target scoring, as attested in the adoption receipt. If any of those outputs has already been inspected for decisions, disclose the actual exposure and do not label this target-outcome-blind.
>
> **Question and estimand.** On the unchanged fixed S146 room/window panel, does the frozen nearest-4 ordered context package improve the frozen generator's PSNR relative to the project's historical coverage-primed VMem/original-KPS retrieval package? This is an operational comparison that permits unqualified internal geometry. It is not a valid-geometry comparison, a causal test of NMS, or a reproduction of published VMem deployment.
>
> **Population and inputs.** Retain apt1/kitchen, apt2/luke and office2/5a, their order, all original eight windows per room, H20 over the complete sequence0, recent C12, own-window targets, static contexts, staging/K/camera conventions and availability order exactly as in the original protocol and R265. No change of bank, room, root, frame stride, selected targets, input resolution, or threshold based on diagnostics or scores. All arms are offered the same declared 32 unique bank identities. Own-window target RGB/depth remains unavailable to retrieval, geometry, generation and design decisions; target poses/K remain common allowed inputs. Preserve cross-window overlap disclosure and reset all state between windows.
>
> **Policy identity.** Name the comparator VMem-KPS-original-operational-v1. Use the original S139 KPS computational implementation, SHA-256 71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f, with observer-only logging in an explicitly versioned S146 module. Do not use the current S146 dynamic-support KPS-R or R266-fixed-support in this assay. Preserve the original objective, complete scale grid, refinement, depth setter behavior, default-focal behavior and retained-depth/surfel accumulation. Do not apply a raw-depth mask to this policy's computations under the guise of logging. Record the original source hash and the instrumented-module hash separately.
>
> Retain INIT=kps, the all-known-pose star rooted at bank[0], chunks 5+15+12, original source/configured optimization settings and dtype/device, first-five NMS threshold semantics, both NMS calls enabled, and target_num_frames restored to four. Retain the original surfel candidate construction, source-defined NMS relaxation/top-up and accumulated focal list. An unexpected KPS-to-MST FALLBACK is an execution-identity failure; native NMS relaxation/top-up is part of the pinned policy. No new pose, calibration, estimator, root or nearest-frame rescue is allowed.
>
> **Provenance before execution.** In the new namespace, seal the adopted amendment, diagnostic input hashes, full staged-data/metadata/manifest receipts, actual VMem/CUT3R/helper/config/weight hashes and environment, numeric settings, source-ID mapping and rerun commands. Reuse the two convention receipts only if both are bound to the same original detector/input hashes and pass Amendment 1. Otherwise recompute only those originally fixed bank checks using the original detector; require agreement with the declared convention or stop, without selecting a new convention from target outcomes. Verify observer-only policy parity on exposed archived inputs, including the actual ordered retrieval IDs; preserve the existing exposed generator replay gate. Hashes of local source mirrors alone do not verify remote execution or weights.
>
> **Retained packages and seeds.** Keep rule 1 static, rule 2 mem_pose, rule 3 bank-sorted original-KPS mem_vmem, rule 4 nearest-4, and native-order mem_vmem as a separately keyed package. Rule 4 retains its original mean distance to all four targets, arithmetic and tie policy. Rule 2 and native VMem retain their respective original queries and tie policies. Deduplicate generation only for identical ordered tuples within the same window. Static and mem_pose are fixed secondary comparators; neither can replace rule 3.
>
> Run evaluation seeds 42,7,1,2 unconditionally for every retained package. Prospectively delete discovery seeds 3–6, random rule 6, coverage rule 5, all warp/copy superiority or covered/hole-region claims, Q_W selectors, hindsight ranking and local-versus-global analyses from this operational assay. Their deleted status is explicit, not missing-cell imputation. No invalid geometry is used to manufacture a coverage comparator or a warp score. The preserved bank diagnostics remain available as diagnostic evidence.
>
> **Hard input/execution gates.** Require exact original panel identities and order; valid supplied cameras/K and staged RGB; complete offered-bank coverage and the declared chunk sequence; exactly three ordered KPS construction records with non-root counts [4,19,31]; correct source/config identity; no unexpected initializer FALLBACK, exception, or unlogged policy switch. A KPS “OK” string denotes branch execution, not geometry validity.
>
> Validate the raw selector output BEFORE integer coercion or Python indexing: integer-valued index representation consistent with the pinned API, exactly four entries, no duplicates, all indices in [0,31], and exact mapping to four distinct bank frame identities with no own-window target collision. Reject fractional/negative/out-of-range/short outputs. Set consumer_contexts equal to the validated raw list; prohibit repeat-fill. Save both raw and bank-sorted order and the actual selection-call candidate/threshold/query trace. Preserve a successful selection receipt before optional ancillary diagnostic rendering; a diagnostic failure is recorded separately and cannot silently change the selected package.
>
> **Internal geometry is diagnostic for this operational estimand.** Do not exclude a window because of a non-finite KPS objective, bad raw depth fraction, default focal, flat/boundary scale profile, or incomplete surfel-to-frame representation. Exact 32-frame input opportunity remains a hard requirement; exact 32-frame surfel representation becomes a reported internal outcome, explicitly superseding R265's representation gate for this assay only. No arbitrary accuracy or positive-depth-percentage threshold is introduced.
>
> Record all such events, including full-grid objective/profile and grid minimum, chosen-scale per-view residual/focal and support counts, root provenance, raw dense validity before sanitization, retained-depth origin, effective post-alignment focal values, actual memory-frame coverage, and selection candidate/NMS behavior. Observers may not mutate policy state or RNG. Store non-finite values as typed status/null fields with reasons in new receipts. Preserve old diagnostic files unchanged.
>
> Maintain separate fields for policy_available and strict_geometry_status. The latter is FAIL with a witnessed R265/R266 violation, UNKNOWN when evidence is insufficient, and PASS only when all applicable required-view/raw-support/focal/actual-consumer conditions are demonstrated. Finite objective alone cannot set PASS; original KPS is never labeled a validated KPS-R implementation. Do not invent a new cross-call consistency tolerance from fresh results. An unestablished calibration/tolerance leaves the relevant strict condition UNKNOWN. Strict status does not select the operational panel. Any geometry-qualified subset summary is descriptive, with its full original denominator and missing rooms reported; it cannot replace the primary or certify a mechanism.
>
> **Global pre-generation gate and failures.** Attempt only the declared policy on each planned window, saving every failure. Require all retained packages for all original windows before fresh generation. If any policy output is unavailable, stop the complete-panel comparison with OPERATIONAL_PANEL_UNAVAILABLE; report availability counts and reasons over the full panel. Do not drop windows, replace rooms or promote mem_pose. A failed optional diagnostic alone does not count as unavailable selection, but missing mandatory provenance/execution evidence does.
>
> **Generation, sealing and scoring.** Retain the frozen gen_s141 base, VARIANT=A, ADAPTER=NONE, generator weights/config/sampler, camera conversion and paired seed resets. Use no step-A geometry as generation conditioning. Preserve ordered-package cache identity and require finite correctly shaped predictions and the frozen normalization contract. Seal every planned prediction, selected package, source/input manifest and available diagnostic receipt before any target-scoring invocation. Scoring uses the unchanged S140 reference/prediction conversion, per-output PSNR from SSE pooled across the four targets/channels, and mean target SSIM; its operational branch must not read warp files or emit artificial warp/region numbers. Enforce exact expected identities, no duplicate/extra/missing cells, and finite metrics before analysis.
>
> **Primary gate.** For each room r and evaluation seed s, d(r,s) is the mean across all eight windows of PSNR(nearest-4) minus PSNR(bank-sorted mem_vmem). D_r, D_s and D retain equal room/seed weighting. Pass iff D >= +0.20 dB, every D_r > 0, and at least three of the four D_s > 0. Require the same complete gate against native-order mem_vmem for a claim covering both slot policies; otherwise report the corresponding slot-policy-dependent result. No selector is chosen from discovery or evaluation outputs.
>
> Report both orderings' full room-by-seed matrices, room/seed means, room range, leave-one-room-out means, descriptive window uncertainty, package identity overlaps and history fractions; report nearest-minus-static and nearest-minus-mem_pose as secondary. An overall paired SSIM decline beyond 0.01 for an ordering blocks a quality recommendation against that ordering; a recommendation covering both orderings requires neither block. PSNR findings remain reportable with the SSIM qualification. These are finite-panel practical gates, not population-level significance tests or independent-window claims.
>
> **Budget and namespace.** Use a new immutable operational_v1 subtree beneath the declared S146 output root; on the currently scripted transport this maps to /mnt/gluster_dcpu/yiyangliu/gwm_s146/operational_v1. Keep previous outputs and rejected geometry versions intact. Maximum planned generation count before deduplication is 24 windows × 5 packages × 4 seeds = 480 four-target outputs (DERIVED design arithmetic). Retain the total S146 cap of 24 RTX 3090 GPU-hours, subtracting already consumed S146 compute; retrieval, parity/replay and overhead count. Preserve the queue and allocation rules. Stop at the cap; a complete-cell failure or cap truncation is INCOMPLETE, not negative evidence. No runtime fit is claimed from this arithmetic. Record an explicit bounded CPU preparation allowance before execution.
>
> **Terminal interpretation.** A complete operational comparison missing the PSNR gate is “no operational transfer at the frozen practical threshold on this panel.” An unavailable/incomplete panel has no primary superiority conclusion. A pass uses only the claim wording below. The original strict-assay invalidity and all diagnostic exposure remain disclosed. new_method_validated=false and novelty_authorization=NONE remain unchanged.

The evaluation-only reduction is an explicit scientific narrowing, permitted prospectively by R265:130–136; deleting the additional geometry-dependent secondaries is a new disclosed choice here. It is not a claim that the full original six-rule experiment was completed.

## 4. Exact permissible claim wording

**Current diagnostic finding:**

> “On the frozen S146 banks, independent-prefix CPU reconstruction with the project's original KPS initializer returned non-finite objectives in 19 of 72 constructions, affecting 11 of 24 windows. These records expose an initialization/geometry-qualification problem in this full-traversal-bank assay. They do not measure actual incremental retrieval or generated-image quality, and they do not establish that scene extent is the cause.”

The counts are DERIVED in Appendix A. Add the room table and dependent-prefix qualification whenever presenting them.

**If both complete operational PSNR gates pass:**

> “After a disclosed bank-diagnostic-informed amendment, the fixed nearest-4 package passed the preregistered finite-panel PSNR transfer gate against both bank-sorted and native-order outputs of the project's frozen VMem/original-KPS retrieval implementation on the three S146 rooms. The comparison includes the implementation's geometry-degenerate behavior and uses the same frozen generator. It does not show superiority over geometrically valid retrieval, isolate NMS or geometry as the cause, or reproduce the published autoregressive VMem benchmark.”

Append the measured D values and room/seed matrices from the future sealed analysis; none exists yet. Include the SSIM qualification even if PSNR passes.

**If only the sorted gate passes:**

> “Nearest-4 passed the operational PSNR gate against bank-sorted VMem/original-KPS contexts, but the full gate was not established against native-order contexts. The advantage is slot-policy dependent.”

**If complete but the primary gate fails:**

> “The fixed nearest-4 advantage did not transfer at the frozen practical threshold in this operational S146 assay. This is not evidence of equivalence, and it does not repair or validate the internal geometry.”

**If the policy cannot provide a complete panel:**

> “The historical VMem/original-KPS policy did not produce an eligible complete set of context packages under the frozen interface contract. The operational PSNR comparison is unavailable; availability failures are reported over all planned windows.”

Do not shorten any positive result to “nearest-4 beats VMem on fresh rooms” without the implementation/regime qualifications. “Project-fresh” remains conditional on the exposure audit, does not mean unknown to pretraining, and does not erase the fact that this amendment was informed by fresh-bank geometry.

## 5. Minimal implementation changes, not implemented here

| Location | Smallest necessary change and reason |
|---|---|
| S/run_retrieval_s139.py:92–93; H/kps.py:18–120 | Import an explicitly versioned original-KPS observer module. Leave historical KPS and rejected S146 KPS files untouched. Keep the numerical policy unchanged; add evidence-only raw validity, profile and focal-origin records. An AST match of estimator functions, verified in Appendix A, is not full runtime parity. |
| S/run_retrieval_s139.py:99–140; P:635–750 | Record offered IDs/chunks and exact construction/selection traces; make first NMS True explicit; validate raw indices before coercion/indexing; remove repeat-fill; preserve output before ancillary render; separate policy failure from diagnostic failure. Log native candidate/NMS fallback rather than replacing it. |
| S/build_pool_s146.py:82–113,123–140 | Add a separately named operational mode retaining rules (1,2,3,4) and native mem. Skip CUT3R/rule-5 construction entirely in that mode; validate receipt status before raw-context lookup; split input opportunity from internal representation; retain failure rows. Replace the hard-coded six-rule loop only within this mode. Preserve the original geometry mode. |
| S/build_plans_s146.py:10–21; S/gen_s141.py:164–194 | Plans already iterate packages. Add exact-panel/package/provenance checks and versioned output paths; omit inactive warp dependencies. No generator algorithm change is needed. Existing-file skips must require matching sealed identities, not existence alone. |
| work/S140_warp_guided/score_s140.py:10–24,30–50 | Create an S146-owned generation-only scorer adapter; preserve image conversion and PSNR/SSIM equations exactly. Remove the unconditional warp read at line 35 and omit unavailable region/warp fields. Do not edit the old scorer or fabricate empty warp arrays. |
| S/analyze_s146.py:16–47,51–76 | Add an operational primary mode requiring the exact fixed room/window/seed identities, not merely whatever windows a pool supplies. Preserve both primary orderings and PSNR gate; replace the hard-coded coverage contrasts with mem_pose secondary. Apply the SSIM quality block to both relevant orderings. Do not emit the PSNR threshold “gate” as if it were an SSIM test. |
| S/s146_cpu_prep.sh:7–26; S/s146_chain.sh:5–45 | Use an explicit versioned chain: metadata/convention identity → geometry-free pool → original-policy step A → global availability gate → exposed replay → evaluation-only generation → complete-cell seal → generation-only scores → operational analysis. Remove warp/discovery dependencies in this mode, change expected seed count, and capture every worker status. DONE text/file counts are not acceptance receipts. |
| Strict record | Preserve existing diagnostics/rejected protocol, attach observer receipts and witnessed FAIL/UNKNOWN reasons. Do not implement a geometry repair merely to relabel the operational comparator healthy. |

Before future execution, use small exposed/CPU fixtures to check that instrumentation preserves original scale/focal/state results, the index validator rejects duplicates/negative/fractional/short outputs, ordered-package deduplication is correct, and the generation-only scorer matches original whole-image scores on an archived exposed cell. Then verify the actual historical retrieval and generator replay under the pinned execution environment. These are **required future checks, not checks claimed as run here**.

No production code, protocol or ledger was changed. No model was initialized; no dataset/weight download, GPU work, cluster access or communication with others was performed. No repository test suite/linter was run because the deliverable is a review document and no executable source changed. The source/numerical review was divided among read-only review agents; the commands below are the parent review's complete computations.

Changed file: work/agents/CODEX_R267_S146_PATH_DECISION.md only.

Follow-up worth a new session: implement and freeze this single operational version, then perform its bounded availability gate. If it cannot supply the full panel, stop and report; do not open another repair/audit loop or move the primary to mem_pose.

## Appendix A — Diagnostic aggregation, source identity and design arithmetic

Working directory: /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling.

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path
import ast, collections, hashlib, json, math, subprocess
base=Path('work/S146_fresh12')
files=[base/'PROTOCOL.md',Path('work/agents/CODEX_R265_S146_DRAFT_REJECTION.md'),Path('work/agents/CODEX_R266_KPSR_REJECTION.md'),base/'diag_kps_s146.py',base/'kps_diag.py',base/'kps.py',Path('work/S139_crossseq_revisit/kps.py'),base/'run_retrieval_s139.py',base/'build_pool_s146.py',base/'gen_s141.py',base/'analyze_s146.py',base/'s146_chain.sh',Path('data/S134_tacc/vmem_src/modeling/pipeline.py')]+sorted((base/'diag').glob('KPS_DIAG_*.json'))
print('HEAD', subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
print('GIT_STATUS_BEGIN')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('GIT_STATUS_END')
for p in files: print('SHA256',str(p),hashlib.sha256(p.read_bytes()).hexdigest())
rows=[]
for p in sorted((base/'diag').glob('KPS_DIAG_*.json')):
 a=json.loads(p.read_text())['rows']; print('SHARD',p.name,'rows',len(a)); rows.extend(a)
assert len(rows)==len({r['window_id'] for r in rows})==24
for room in ['apt1_kitchen','apt2_luke','office2_5a']:
 rr=[r for r in rows if r['room']==room]
 print('ROOM',room,'windows',len(rr),'all_3_returned_objectives_finite',sum(all(math.isfinite(c['err']) for c in r['constructions'].values()) for r in rr))
 for n in ['5','20','32']:
  cc=[r['constructions'][n] for r in rr]; fe=[c['err'] for c in cc if math.isfinite(c['err'])]
  print('SIZE',n,'finite',sum(math.isfinite(c['err']) for c in cc),'of',len(cc),'finite_err_minmax',None if not fe else [round(min(fe),9),round(max(fe),9)],'min_raw_positive_fraction',round(min(min(c['positive_depth_frac']) for c in cc),12),'all_views_sparse_grid_supported',sum(c['n_grid_valid']==c['n_views'] for c in cc))
 print('NONFINITE',[(r['window_id'],n,c['views_not_finite_at_best']) for r in rr for n,c in r['constructions'].items() if not math.isfinite(c['err'])])
cc=[c for r in rows for c in r['constructions'].values()]
print('TOTAL','calls',len(cc),'finite',sum(math.isfinite(c['err']) for c in cc),'windows_all_finite',sum(all(math.isfinite(c['err']) for c in r['constructions'].values()) for r in rows),'calls_all_views_sparse_grid_supported',sum(c['n_grid_valid']==c['n_views'] for c in cc))
def functions(path):
 return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(path).read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a=functions('work/S139_crossseq_revisit/kps.py'); b=functions(base/'kps_diag.py')
print('ORIGINAL_DIAG_FUNCTION_AST_EQUAL',{k:a[k]==b[k] for k in ['_proj_residual','estimate_sigma','pixel_grid']})
print('GRID_DIAGNOSTIC_STRIDE',8,'SUBGRID_COUNT',len(range(0,241,8)),'FULL_COUNT',241)
print('PROPOSED_MAX_GENERATIONS',24*5*4,'PRIMARY_PACKAGE_SEED_CELLS',24*2*4)
print('LOCAL_S143_FRESH_JSON_PRESENT',Path('work/S143_context_ranking/results/S143_FRESH.json').exists())
PY
```

Complete output (exit code 0):

```text
HEAD 7733e0d94376f9538021d767b23c2890abd303ae
GIT_STATUS_BEGIN
?? work/agents/CODEX_R266_KPSR_REJECTION.md
?? work/agents/prompts/R266_FULL.md
?? work/agents/prompts/R266_PROMPT.md
?? work/agents/prompts/R267_FULL.md
?? work/agents/prompts/R267_PROMPT.md
GIT_STATUS_END
SHA256 work/S146_fresh12/PROTOCOL.md 65c93df1fcee2841ada3d7c3164d7f5a8fe1ba711c14a7d143416a80cce52e64
SHA256 work/agents/CODEX_R265_S146_DRAFT_REJECTION.md 4ab05b3eb6632c5045c45bbc5aed01943188adc5a126e38db7cb804fb3fb16d3
SHA256 work/agents/CODEX_R266_KPSR_REJECTION.md 6ab2eb51ab1028080aeb746125030ac1be8845ede1343860a7ed701af0fc698f
SHA256 work/S146_fresh12/diag_kps_s146.py 1ba985b5f5843c1d3610075c0857ce2592b3e54793cfe0d3ee2d167248ba9894
SHA256 work/S146_fresh12/kps_diag.py 92866ad14ff703b7a7099c38fb3d0bd4d0d065327a5b0763f70bd67d1eb2e0f3
SHA256 work/S146_fresh12/kps.py fc463275ab03a7e33459b2bd96514060622e9be5e632f5b83df1ed194d8fc1d5
SHA256 work/S139_crossseq_revisit/kps.py 71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f
SHA256 work/S146_fresh12/run_retrieval_s139.py 6670478ca26001eb2a011e2f801360893c0d6e2ca67a068b4ba32ab587b039fc
SHA256 work/S146_fresh12/build_pool_s146.py e3c9f9421a9939c6c2898ec0b0129c0003a219d2bef1596f5a692f9d03dfe946
SHA256 work/S146_fresh12/gen_s141.py c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121
SHA256 work/S146_fresh12/analyze_s146.py 10d93a8f13eb33a0b264c51ef208a0ce61645b684b99fefc842761619a38aa30
SHA256 work/S146_fresh12/s146_chain.sh 5945323bdbecfdc6051782280c6ce4c72d96b9bc496ec9fc43fbefb2e0e68d9d
SHA256 data/S134_tacc/vmem_src/modeling/pipeline.py 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255
SHA256 work/S146_fresh12/diag/KPS_DIAG_0.json c5c629364c34331ed2c7a31cfa31e16c3809d6ed766323ff4338dbe326400396
SHA256 work/S146_fresh12/diag/KPS_DIAG_1.json b7e5e8e9f8ec10154e1575e4886bef40ee434dfd1c65ed1407e4310ce03a7aea
SHA256 work/S146_fresh12/diag/KPS_DIAG_2.json 6e6970452868dbb2a595e73e9c167f5f9099e9a70a4aac42395c7c504c1fb17e
SHARD KPS_DIAG_0.json rows 8
SHARD KPS_DIAG_1.json rows 8
SHARD KPS_DIAG_2.json rows 8
ROOM apt1_kitchen windows 8 all_3_returned_objectives_finite 6
SIZE 5 finite 8 of 8 finite_err_minmax [32.247622481, 32.270248432] min_raw_positive_fraction 1.0 all_views_sparse_grid_supported 8
SIZE 20 finite 8 of 8 finite_err_minmax [56.890735074, 56.890735074] min_raw_positive_fraction 0.999959290028 all_views_sparse_grid_supported 8
SIZE 32 finite 6 of 8 finite_err_minmax [55.720047461, 69.297672835] min_raw_positive_fraction 0.999959290028 all_views_sparse_grid_supported 8
NONFINITE [('apt1_kitchen_s0465', '32', [16]), ('apt1_kitchen_s0537', '32', [4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 25, 26, 27, 28, 29])]
ROOM apt2_luke windows 8 all_3_returned_objectives_finite 7
SIZE 5 finite 8 of 8 finite_err_minmax [140.266124857, 140.266124857] min_raw_positive_fraction 1.0 all_views_sparse_grid_supported 8
SIZE 20 finite 8 of 8 finite_err_minmax [144.523916025, 144.523916025] min_raw_positive_fraction 0.534271240234 all_views_sparse_grid_supported 8
SIZE 32 finite 7 of 8 finite_err_minmax [112.304609103, 159.562866889] min_raw_positive_fraction 0.534215271473 all_views_sparse_grid_supported 7
NONFINITE [('apt2_luke_s0971', '32', [7, 12, 17, 20, 23, 24])]
ROOM office2_5a windows 8 all_3_returned_objectives_finite 0
SIZE 5 finite 8 of 8 finite_err_minmax [15.646815419, 15.646815419] min_raw_positive_fraction 1.0 all_views_sparse_grid_supported 8
SIZE 20 finite 0 of 8 finite_err_minmax None min_raw_positive_fraction 0.605941772461 all_views_sparse_grid_supported 8
SIZE 32 finite 0 of 8 finite_err_minmax None min_raw_positive_fraction 0.605941772461 all_views_sparse_grid_supported 8
NONFINITE [('office2_5a_s0619', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0619', '32', [4, 5, 6, 7, 8, 18, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]), ('office2_5a_s0802', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0802', '32', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0497', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0497', '32', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0680', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0680', '32', [4, 5, 6, 7, 8, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]), ('office2_5a_s0863', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0863', '32', [4, 5, 6, 7, 8, 18, 24, 26, 27, 30]), ('office2_5a_s0558', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0558', '32', [4, 5, 6, 7, 8, 18, 25, 26]), ('office2_5a_s0741', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0741', '32', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0925', '20', [4, 5, 6, 7, 8, 18]), ('office2_5a_s0925', '32', [4, 5, 6, 7, 8, 18, 20, 28, 29, 30])]
TOTAL calls 72 finite 53 windows_all_finite 13 calls_all_views_sparse_grid_supported 71
ORIGINAL_DIAG_FUNCTION_AST_EQUAL {'_proj_residual': True, 'estimate_sigma': True, 'pixel_grid': True}
GRID_DIAGNOSTIC_STRIDE 8 SUBGRID_COUNT 31 FULL_COUNT 241
PROPOSED_MAX_GENERATIONS 480 PRIMARY_PACKAGE_SEED_CELLS 192
LOCAL_S143_FRESH_JSON_PRESENT True
```

## Appendix B — Archived historical finite-call counts and reported contrast

Working directory: /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling.

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import hashlib, json, math
from pathlib import Path
for name, path, key in [('S139_stepA','work/S139_crossseq_revisit/results/stepA_superpod/RETRIEVAL_RECEIPT.json','records'),('S143_rule5','work/S143_context_ranking/POOL.json','windows')]:
 p=Path(path); obj=json.loads(p.read_text()); logs=[entry for row in obj[key] for entry in row['kps_log']]
 finite=sum(e.get('kps')=='OK' and math.isfinite(e['sigma']) and math.isfinite(e['median_reproj_px']) for e in logs)
 focals=sum(all(x is not None and math.isfinite(x) and x>0 for x in e['focals']) for e in logs)
 print('SHA256',path,hashlib.sha256(p.read_bytes()).hexdigest())
 print(name,'rows',len(obj[key]),'calls',len(logs),'OK_finite_sigma_objective',finite,'all_focals_finite_positive',focals)
p=Path('work/S143_context_ranking/results/S143_FRESH.json'); obj=json.loads(p.read_text())
print('SHA256',str(p),hashlib.sha256(p.read_bytes()).hexdigest())
print('S143_fresh_nearest_minus_mem',obj['rule_contrasts']['r_disc(rule 4) - rule 3 (mem_vmem)']['mean'])
PY
```

Complete output (exit code 0):

```text
SHA256 work/S139_crossseq_revisit/results/stepA_superpod/RETRIEVAL_RECEIPT.json abf5f79caac64f537aa56d426f99596eec88a916ccd9166da0c5de67b08937ed
S139_stepA rows 24 calls 72 OK_finite_sigma_objective 72 all_focals_finite_positive 72
SHA256 work/S143_context_ranking/POOL.json 0eea09978b17f71491a459651e9c39a2925af97f948c9b597406b48d7957cad5
S143_rule5 rows 24 calls 24 OK_finite_sigma_objective 24 all_focals_finite_positive 24
SHA256 work/S143_context_ranking/results/S143_FRESH.json ebe355b4c5bd28e710c614cd06a6646a82e8c4fc2e46fa97b7425a51834ed80d
S143_fresh_nearest_minus_mem 0.7382526642964204
```
