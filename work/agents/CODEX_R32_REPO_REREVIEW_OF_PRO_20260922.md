# Round 32 repository re-review of R29-P1, R30-P2, and R31-P3

Date: 2026-09-22

This is a read-only repository review. I used the pinned source, the execution scripts, receipts, the technical report, the retrieval-arms report, the audit records, and the append-only log. No GPU, training, weight download, data download, or Slurm submission was used. The mandated Astra invocation was attempted with the required flags, but the local app-server failed before analysis with `Operation not permitted`; the findings below therefore rest on direct repository evidence, not on an external model's repository reading. The project flags remain `new_method_validated=false` and `novelty_authorization=NONE` (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:1-4`).

## Executive findings

1. R31-P3's statement that `Delta_leak` was never measured is wrong. The fourth row of the authoritative report is `memory_nms_on_clean - memory_nms_on (leaked) = +0.245 dB`, SD 0.711, positive in 6/14 windows (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:40-47`). The score receipt gives the unrounded mean `+0.24457135965017165` for 14 windows (`docs/report/bundle/S113_SCORES.json:2423-2426`). With the user's definition
   `Delta_leak = Y(NMS-on, inherited state) - Y(NMS-on, valid state)`, the signed estimate is therefore `-0.244571... dB`, conventionally `-0.245 dB`. The report's positive number uses the reverse subtraction order.

2. This is a legitimate finite-panel estimate of the contrast between the operational leaked and isolated states. It uses the same 14 windows, two seeds, bank, targets, sampler, and frozen configuration, with sealed arms reused only after explicit state and byte-identity gates (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:9-23`; `docs/report/TECHNICAL_REPORT_20260918.md:143-150,252-277`). It is not a population estimate, a held-out result, or proof of a general performance cost (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:11-20`).

3. The inherited value is natively reachable: movement calls NMS-off, which writes `1e8`; turning calls NMS-on through the default, and at a non-five-frame bank the enabled branch reads the old value (`navigation.py:185-187,234-236,321-322`; `configs/inference/inference.yaml:16`; `docs/ENTRY_PATH_CORRECTION_20260918.md:34-48`). The S111 harness is structurally different from the released trajectory because it manually primes a five-frame bank and then holds a fixed 12-frame bank (`docs/report/TECHNICAL_REPORT_20260918.md:154-166`). Thus the state value and branch mechanism are native, while the measured trajectory is an operational finite-panel reproduction, not a run of the demo itself.

4. “Replay envelope = 0” is valid only for the exact S103 selector-free baseline configuration: one scene/window, one seed, fixed history and target cameras, fixed software/weights, and four same-model H800 executions on dgx-21/dgx-09 (`RESEARCH_LOG.md:14158-14170`; `work/S103_selector_free_baseline/run_receipts_594155/PREDICTION_RECEIPT.json:1-33`). It does not certify S111/S113 branch semantics, arbitrary arm differences, cross-scene or cross-trajectory behavior, or semantic validity. R31's caution about deterministic wrong experiments stands; the broader implication that the replay proves nothing is too broad.

5. The original `0/20 measured under frozen weights` tally meant (b): no N=20 system had a C5-qualified defect-specific downstream causal measurement in that audit. It did not mean that no frozen forward had ever run. R15-F explicitly marked C5 `UNVERIFIED` for every system (`work/agents/CODEX_R15F_AUDIT_EXPANSION_20260919.md:1-5`), while the contemporaneous VMem material already recorded a real frozen-generator `+0.245 dB` contrast (`work/agents/PROMPT_R15G_CONDITION5_WITHOUT_GPU_20260919.md:15-20`). R18-J defines the tally in exactly that restricted sense (`work/agents/CODEX_R18J_REAUDIT_20260919.md:64-73`).

## 1. Repository-fact audit of the three Pro rounds

The Pro rounds were decision and literature reviews conducted without repository access. I distinguish repository facts from their judgments. “Unverifiable” below means not a repository fact established by that round; it does not mean the associated idea is false.

### R29-P1

| R29-P1 claim or input | Verdict | Repository evidence and correction |
|---|---|---|
| “Five A-side candidates are all ADJACENT; none is OCCUPIED.” | UNVERIFIABLE as a repository claim | This is a literature/positioning judgment recorded at `RESEARCH_MEMORY.md:2790-2810`, not a code, job, or measured-result fact. R29 itself records that it had no Codex repository review (`RESEARCH_MEMORY.md:2865-2869`). |
| R29's warning that the candidates do not yet support a competitive method paper. | UNVERIFIABLE as a repository fact | It is a judgment about contribution strength, not a repository measurement. The ledger records it as a Pro decision, not as a code result (`RESEARCH_MEMORY.md:2792-2810`). |
| The proposal uses lineage-aware fusion while retrieval is held fixed, and was marked NO-GO after a numerical algebra check. | VERIFIED for the proposal record, but not a VMem experiment | The proposal says “Retrieval is held fixed” and reports the algebraic check at `RESEARCH_MEMORY.md:2917-2922`; the numerical table gives maximum identity error `4.4e-16` (`docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md:174-186`). This is a checked algebraic identity, not a model-quality measurement. |
| `4.4e-16`. | VERIFIED as the proposal's computed maximum identity error | `docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md:177-186`. It must not be described as a GPU job, PSNR result, or VMem effect. |
| “800 GPU-hours remain withdrawn.” | VERIFIED as project governance state, not an experiment | `RESEARCH_MEMORY.md:2865-2869`; the same status is repeated for the later decision at `RESEARCH_MEMORY.md:3055-3060`. No job measuring 800 hours exists in the cited material. |

R29 therefore supplied no new measured repository result. Its strongest repository-adjacent inputs were inherited governance and proposal records, not an independently inspected source tree.

### R30-P2

| R30-P2 claim or input | Verdict | Repository evidence and correction |
|---|---|---|
| A B4 gate must alter state commit; a detector without write-back is not a gate. | UNVERIFIABLE as a repository fact | This is a method-contract judgment (`RESEARCH_MEMORY.md:2940-2963`), not a claim that a particular checked code path was executed. |
| Old trajectories cannot substitute for a closed-loop intervention. | UNVERIFIABLE as a repository measurement; methodologically sound | The statement is a causal-design constraint recorded at `RESEARCH_MEMORY.md:2962-2963`; no new closed-loop job was run in this review. |
| VMem has a cross-call `initial_threshold` residue. | VERIFIED | The pinned source's disabled branch writes `1e8`, the enabled branch assigns only in the five-frame state, and the following code reads the field (`work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py:694-708`). `reset()` does not clear it (`:135-147`). |
| R30's reliance on the pinned VMem copy and its mutation/consumer anchors. | VERIFIED | The three project copies have the same SHA-256 and the cited consumer/mutation anchors are recorded at `work/agents/CODEX_R28T_CONTRACT_FILTER_B36_B55_20260920.md:46-50` and `work/agents/CODEX_R15G_CONDITION5_ROUTES_20260919.md:19-33`. |
| The VMem residue proves a lifecycle/state-scope issue but not general geometry harm. | VERIFIED as the correctly limited interpretation | R30 states this limit at `RESEARCH_MEMORY.md:3021-3028`; the source and the finite-panel reports support the lifecycle part, while the reports explicitly reject population/general geometry claims (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:11-20,138-146`). |
| GEN3C has a stale readiness/admission flag after cache clearing. | VERIFIED as a static audit finding, not as a completed dynamic consumer experiment | The locked-code audit records the outer `model_seeded` write/read and the inner cache clearing at `work/agents/CODEX_R18J_REAUDIT_20260919.md:22`; R30 correctly limits the direct support to readiness/resource lifecycle (`RESEARCH_MEMORY.md:3021-3028`). No GEN3C frozen-weight generation job is recorded. |
| `500–2,000 H800-hours` is required. | WRONG if treated as a measured or logically necessary number; UNVERIFIABLE as a resource estimate | R30 itself calls it a route quotation rather than a theorem (`RESEARCH_MEMORY.md:2983-2987`). It is neither a measured number nor an authorization. |
| “No complete locked-version reproduction materials were obtained.” | VERIFIED as Pro's limitation disclosure, not as a repository scientific result | `RESEARCH_MEMORY.md:3040-3041` says Pro did not claim independent reproduction. |
| `800 H800-hours` remain withdrawn. | VERIFIED as governance state | `RESEARCH_MEMORY.md:3055-3060`. It does not establish that no future budget could ever be authorized. |

### R31-P3

| R31-P3 claim or input | Verdict | Repository evidence and correction |
|---|---|---|
| There was no complete paper and the strongest current asset was a narrow VMem forensic study. | UNVERIFIABLE as a repository measurement; consistent with project status | This is a publication judgment at `RESEARCH_MEMORY.md:3068-3077`, not a code or job result. |
| The measured contrast was only `Delta_setting = clean NMS-on - NMS-off = -0.726 dB`. | WRONG as an exhaustive description | `-0.726 dB` is verified (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:42-47`; `docs/report/TECHNICAL_REPORT_20260918.md:202-225`), but the same tables also contain the leaked-versus-clean row `+0.245 dB` (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:42-47`). |
| R31's pinned-source anchors and native move/turn entry-path claims. | VERIFIED | The source hash and anchors are recorded at `work/agents/CODEX_R28T_CONTRACT_FILTER_B36_B55_20260920.md:46-50`; the native call sites and default are directly shown at `work/S17C_interface_preparation/isolated_vmem_source/navigation.py:185-187,234-236,321-322` and `configs/inference/inference.yaml:16`. |
| `Delta_leak` was never measured. | WRONG | The row, script, receipt, and score file measure the reverse-signed paired contrast. See §2 below and `docs/report/bundle/S113_SCORES.json:2423-2426`. |
| “The clean arm cannot quantify the leaked turn.” | WRONG as stated; NARROWED as a caution about naming | The clean arm alone does not identify a leaked-versus-clean contrast, but S111 supplies the leaked arm and S113 supplies the isolated arm. The paired row is exactly the two-arm comparison (`docs/report/TECHNICAL_REPORT_20260918.md:213-225`). |
| The replay asset proves only no observed replay difference under measured conditions, not semantic validity. | PARTLY STANDS, but the scope must be stated exactly | The exact baseline scope and four-run hashes are in `RESEARCH_LOG.md:14158-14170`; the claim must not be extended to S111/S113 or arbitrary arm differences. |
| The four-run replay was a one-config, one-window, one-seed, one-scene test on two same-model H800 nodes. | VERIFIED | `RESEARCH_LOG.md:14168-14170` and the baseline receipt `work/S103_selector_free_baseline/run_receipts_594155/PREDICTION_RECEIPT.json:1-33`. |
| `0/20 measured under frozen weights` is ambiguous. | VERIFIED as a wording problem; resolved as meaning (b) by the original audit | `RESEARCH_MEMORY.md:3121-3127` raises the ambiguity. The original audit definition and C5 tally resolve it to no C5-qualified defect-specific downstream measurement (`work/agents/CODEX_R18J_REAUDIT_20260919.md:64-73`). |
| The repair result was `-0.016 dB` against a predeclared `+0.20 dB` retention criterion. | VERIFIED | `docs/report/TECHNICAL_REPORT_20260918.md:10-18,241-245`. The correct interpretation is failure of that branch's continuation criterion, not proof of a universal zero effect (`RESEARCH_MEMORY.md:3123-3127`). |
| The VMem and GEN3C findings are not two completed dynamic causal demonstrations. | VERIFIED as an evidence-status statement | VMem has the finite-panel frozen-generator contrast; GEN3C remained a static lifecycle audit with C5 unverified (`work/agents/CODEX_R18J_REAUDIT_20260919.md:64-73`; `RESEARCH_MEMORY.md:3101-3108`). This does not say GEN3C's code path is imaginary; it says its downstream frozen-model effect was not measured. |
| A1 replay has little independent novelty and does not prove experimental semantics. | UNVERIFIABLE as a repository fact; the semantic limitation STANDS | The novelty ranking is a judgment (`RESEARCH_MEMORY.md:3101-3114`). The exact deterministic scope and its limitations are verified in §3 below. |
| The finite-panel numbers do not support cross-scene population generalization. | VERIFIED | `docs/RETRIEVAL_ARMS_RESULT_20260918.md:9-20,138-146`. |

## 2. Was `Delta_leak` actually measured?

### State history

The pinned source has three relevant facts. `reset()` clears ordinary lists but not `initial_threshold` (`work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py:135-147`). The NMS-enabled branch assigns a threshold only in the five-frame condition; the disabled branch writes `1e8`; the subsequent selector reads the field (`:694-718`). The source is pinned identically in all three project copies, with SHA-256 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e` (`work/agents/CODEX_R28T_CONTRACT_FILTER_B36_B55_20260920.md:46-50`; `work/agents/CODEX_R15G_CONDITION5_ROUTES_20260919.md:19-33`).

The leaked S111 arm was created in job 594957. In `nms_s111.py`, each window primes the natural five-frame state, fills the bank, and then executes `nms_off` before `nms_on` in the same pipeline object (`work/S103_selector_free_baseline/nms_s111.py:130-170`). The receipt identifies job 594957, seeds 42 and 7, target offsets 60/75/90/105, 88 total runs, and the five-frame priming protocol (`docs/report/bundle/NMS_RECEIPT.json:4818-4845`). At full bank size, the enabled call does not reassign the threshold and therefore consumes the `1e8` left by the immediately preceding disabled call.

The clean S113 arm was job 595887. Its isolation routine calls `reset()`, empties mutable fields, and deletes `initial_threshold` (`work/S103_selector_free_baseline/nms_on_clean_s113.py:101-115`). It then initializes, appends exactly four more frames, assigns the enabled threshold at the natural five-frame state, appends the remaining bank frames, and performs the enabled selection without a preceding NMS-off call (`:165-195`). Its receipt records job 595887, 28 runs, and `no_arm_saw_a_leaked_threshold: true` (`docs/report/bundle/NMS_ON_CLEAN_RECEIPT.json:1-19,1453-1469`).

### Is the leaked state native or artificial?

The *state value and read path* are native. The released navigation layer passes `use_non_maximum_suppression=False` for movement and passes no argument for turning (`work/S17C_interface_preparation/isolated_vmem_source/navigation.py:185-187,234-236,321-322`). The app routes turn and movement commands to those methods (`app.py:208-215`), and the default config is NMS-on (`configs/inference/inference.yaml:16`). The released sequence `initialize -> move_forward -> move_forward -> turn_left` therefore writes `1e8` during movement and can read it during a later turn, when the bank is no longer at five frames (`docs/ENTRY_PATH_CORRECTION_20260918.md:34-48`; `docs/report/TECHNICAL_REPORT_20260918.md:125-136`).

The *full harness trajectory* is not identical to that native interaction. The diagnostic primes a fixed five-frame state and then uses a fixed 12-frame bank, whereas the demo writes generated frames back and grows its bank (`docs/report/TECHNICAL_REPORT_20260918.md:154-166`; `docs/ENTRY_PATH_CORRECTION_20260918.md:62-76`). Therefore “same native inherited-threshold regime” is supported; “we ran the released demo's move, move, turn sequence” is false. The demo itself was not run (`docs/ENTRY_PATH_CORRECTION_20260918.md:50-60`).

### Were the arms otherwise held equal?

For the paired score, yes within the finite-panel design, with explicit limits:

- The authoritative scope is the same two exposed sequences, 14 windows, two seeds, one dependency group, one frozen consumer, and RGB PSNR (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:9-20`).
- The scripts use the same target offsets, bank construction, sampler settings, seeds, and frozen configuration; S113 states that these are copied unchanged from S111 (`work/S103_selector_free_baseline/nms_s111.py:21-31`; `work/S103_selector_free_baseline/nms_on_clean_s113.py:20-36`).
- The clean and leaked arms use the same bank frame universe and target poses. The selection itself is intentionally allowed to differ because the threshold state is the intervention. The candidate ranking/pool was checked from the pipeline at multiple requested context sizes and was exactly nested in every evaluated window (`docs/report/TECHNICAL_REPORT_20260918.md:174-184`).
- Static, NMS-off, and leaked NMS-on outputs were reused rather than regenerated only after the census reproduced the leaked selections frame-for-frame and the threshold-independence and byte-identity gates passed (`work/S103_selector_free_baseline/nms_on_clean_s113.py:20-30`; `docs/report/TECHNICAL_REPORT_20260918.md:254-277`).

This is enough for a paired finite-panel contrast. It is not evidence that the clean arm is the authors' intended production configuration; the report defines “clean” operationally as an isolated threshold assigned at the five-frame priming state (`docs/report/TECHNICAL_REPORT_20260918.md:154-166`). Nor is there a branch-specific four-run S111/S113 cross-node replay envelope; the four-run replay discussed in §3 is S103 selector-free.

### Estimand and verdict

The row `memory_nms_on_clean - memory_nms_on (leaked) = +0.245 dB` is a measured, finite-panel estimate of the isolated-state advantage over the inherited-state arm (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:42-47`; `docs/report/TECHNICAL_REPORT_20260918.md:202-225`). Reversing the order to the user's definition gives:

`Delta_leak = leaked - clean = -0.244571... dB`, rounded `-0.245 dB`, SD 0.711 in the report's reverse-order convention, with 6/14 windows positive for clean-minus-leaked (`docs/report/bundle/S113_SCORES.json:2423-2426,2498-2500`).

It is therefore legitimate to say: **on this fixed panel and under this operational native-reachable state intervention, the inherited-threshold arm was 0.245 dB lower on mean PSNR than the isolated arm.** It is not legitimate to say that this proves a universal leak cost, a released-demo average, or paper-result contamination. R31-P3's central “never measured” retraction is overturned; its warning against generalization and semantic overclaiming stands.

The withdrawn `-0.729 dB` number is a different contrast. The score file labels it `leaked_nms_on_minus_static`, with mean `-0.7291387376562318` over 14 windows (`docs/report/bundle/S113_SCORES.json:2502-2505`). S113's script explains that this earlier number was withdrawn as an estimate of the independently initialized NMS-on effect (`work/S103_selector_free_baseline/nms_on_clean_s113.py:4-14`). It is not the leaked-minus-clean `Delta_leak`; it is the earlier leaked-versus-static contrast. The corrected clean-versus-static result is `-0.485 dB` (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:44-47`).

## 3. What “replay envelope = 0” covered

The original replay chain was the S103 selector-free baseline, not the S111/S113 retrieval-arm comparison. The receipt fixes history frames `[0,15,30,45]`, target command frames `[60,75,90,105]`, context count 4, target count 4, 50 sampling steps, and seed 42 (`work/S103_selector_free_baseline/run_receipts_594155/PREDICTION_RECEIPT.json:1-33`). The later log records baseline 594155 on dgx-21, replays 594674 and 594676 on dgx-09, and replay 594680 on dgx-21; all output hashes were identical (`RESEARCH_LOG.md:14158-14170`). The summary reports the same four jobs as byte-identical (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:8-14,25-37`).

The exact honest claim is:

> For one selector-free scene_13 window, one seed, one fixed input/configuration, one frozen software/weight bundle, and four executions on two same-model H800 nodes (dgx-21 and dgx-09), the sealed RGB and latent outputs were byte-identical; the observed numerical replay envelope for that configuration was zero.

The baseline's execution-path correction matters: its predictor constructed a bare `VMemPipeline` carrier and did not execute VMem initialization, surfel construction, or memory retrieval (`RESEARCH_LOG.md:14148-14156`). Thus the replay does not cover the retrieval-state bug.

It cannot honestly claim any of the following:

- that S111's leaked arm and S113's clean arm have a measured zero replay envelope;
- that every difference between arbitrary arms is free of replay noise;
- that deterministic repetition proves correct experimental semantics;
- that the result generalizes across scenes, trajectories, hardware architectures, or seeds; or
- that the demo or the published paper was semantically reproduced.

There is a separate S111-specific linkage result: contaminated ordering and selections were reproduced 28/28 byte-identically against the sealed run (`docs/report/TECHNICAL_REPORT_20260918.md:271-275`). That certifies the stored S111 linkage and reuse gate; it is not the broad S103 replay envelope.

The unrelated “1 of 12 bank frames visible” measurement belongs to the S105 memory probe, not to the replay. The summary records `frame_count_raw = [(11, 1)]` and only frame 55 visible from a 12-frame bank (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:43-48`).

## 4. What the N=20 `0/20` tally meant

R15-F explicitly says it audited static conditions 1–4 and marked condition 5, “measurable behaviour under frozen weights,” `UNVERIFIED` for every system (`work/agents/CODEX_R15F_AUDIT_EXPANSION_20260919.md:1-5`). R18-J defines the strict denominator as 20 non-OUT, non-modality candidates and reports 2/20 static HIT, 2/20 NEAR, 15/20 CLEAN, 1/20 SUSPECT-UNTRACED, followed by “frozen-weight measured behavior HIT = 0/20 measured” because C5 had not been run in that audit (`work/agents/CODEX_R18J_REAUDIT_20260919.md:15,64-73`).

The wording therefore means **(b), no system had a defect-specific downstream causal measurement satisfying the audit's C5 criterion**. It does not mean **(a), no system ever ran a frozen forward**. The contemporaneous C5 planning prompt explicitly records a real frozen-generator VMem `+0.245 dB` clean-versus-leaked result (`work/agents/PROMPT_R15G_CONDITION5_WITHOUT_GPU_20260919.md:15-20`), and the authoritative retrieval report contains the full finite-panel measurement (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:40-47`).

The clean wording for future use is: **“In the N=20 static audit, 0/20 systems had a C5-qualified defect-specific frozen-weight downstream measurement at the audit snapshot.”** “No system ever ran a frozen forward” is false.

## 5. Requested numerical and job ledger

| Item supplied to R29/R30/R31 | Verdict | Exact evidence |
|---|---|---|
| `+0.242 dB` | VERIFIED | NMS-off minus static, 8/14 windows, SD 1.270 (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:42-45`; `docs/report/TECHNICAL_REPORT_20260918.md:204-209`). |
| `-0.726 dB` | VERIFIED, but it is `clean NMS-on - NMS-off` | `docs/RETRIEVAL_ARMS_RESULT_20260918.md:42-47`; absolute means reproduce it at `docs/report/TECHNICAL_REPORT_20260918.md:213-225`. |
| `-0.016 dB` versus `+0.20 dB` | VERIFIED, with a narrow interpretation | Repair result and predeclared threshold are at `docs/report/TECHNICAL_REPORT_20260918.md:10-18,241-245`; it is not a universal null-effect proof (`RESEARCH_MEMORY.md:3123-3127`). |
| `5.6 dB` | VERIFIED as a context-span result | S106 summary, 594717, reports the span at `docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:15-18,50-62`. |
| `0.55 dB` | VERIFIED as the first-slot effect in one tested multiset | S107 job 594733 table (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:16-18,64-73`). |
| “1 of 12 bank frames visible” | VERIFIED for the S105 probe, not a replay result | `frame_count_raw=[(11,1)]`, only frame 55 visible (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:43-48`). |
| Replay byte-identical across dgx-21/dgx-09 | VERIFIED only for S103 selector-free baseline | Jobs and hashes are recorded at `RESEARCH_LOG.md:14158-14170`; exact inputs are in `work/S103_selector_free_baseline/run_receipts_594155/PREDICTION_RECEIPT.json:1-33`. |
| N=20 audit tallies | VERIFIED as static-audit tallies | N=20 definition and 2/20, 2/20, 15/20, 1/20, 0/20 C5 wording (`work/agents/CODEX_R18J_REAUDIT_20260919.md:15,64-73`). They are not a prevalence estimate (`:85-89`). |
| `4.4e-16` | VERIFIED as a proposal algebra identity error | `docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md:174-186`; not a performance or job result. |
| `+0.245 dB`, SD 0.711, 6/14 | VERIFIED as clean-minus-leaked | Report row (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:42-47`) and unrounded score (`docs/report/bundle/S113_SCORES.json:2423-2426,2498-2500`). Under `Delta_leak = leaked-clean`, the sign is `-0.245 dB`. |
| `-0.729 dB` | VERIFIED as leaked NMS-on minus static in the earlier arm, not `Delta_leak` | `docs/report/bundle/S113_SCORES.json:2502-2505`; withdrawal explanation (`work/S103_selector_free_baseline/nms_on_clean_s113.py:4-14`). |
| Jobs 594957 and 595887 | VERIFIED as leaked S111 and isolated S113 arms | `docs/report/bundle/NMS_RECEIPT.json:4818-4845`; `docs/report/bundle/NMS_ON_CLEAN_RECEIPT.json:1453-1469`. |
| Jobs 595599, 595614, 595625 | VERIFIED as zero-diffusion state/order, census, and NMS-off threshold gates | `docs/report/TECHNICAL_REPORT_20260918.md:148-150,252-277`; S113 receipt gate list (`docs/report/bundle/NMS_ON_CLEAN_RECEIPT.json:5-8`). |

## Final disposition of the three Pro rounds

**STAND**

- R29's caution that the A-side ideas were not thereby validated as competitive methods; this is a judgment, not a repository measurement, and no repository evidence here upgrades it.
- R30's distinction between a lifecycle/state-correctness finding and a demonstrated world-model method or general geometry harm (`RESEARCH_MEMORY.md:3021-3030`).
- R31's limits on finite-panel generalization, its warning that deterministic replay does not prove semantic validity, and its correction that `-0.016 dB` only failed an internal continuation threshold.

**OVERTURNED**

- R31's central statement that `Delta_leak` was never measured. The paired leaked-versus-isolated row is real; its correct user-defined sign is `-0.245 dB`.
- Any reading of `0/20 measured under frozen weights` as “no frozen forward ever ran.” The original audit meant no C5-qualified defect-specific downstream measurement.

**NARROWED**

- “Replay envelope = 0”: valid for the exact S103 selector-free baseline only, not for S111/S113 semantics or all arm differences.
- “The leak costs performance”: supported as a finite-panel inherited-versus-isolated state contrast under the operational native-reachable regime, not as a universal released-demo or paper-result claim.
- The relation of `-0.729 dB`: it is the earlier leaked-versus-static contrast and was withdrawn as an independently initialized NMS-on estimate; it is not the leaked-versus-clean Delta_leak.
- The clean arm: it is an isolated five-frame-primed operational comparator, not a verified statement of the authors' intended configuration.
