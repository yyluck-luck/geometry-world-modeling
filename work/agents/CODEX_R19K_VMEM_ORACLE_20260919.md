# Round 19-K — VMem oracle archival audit

**Disposition: `NO-DEFENSIBLE-ORACLE`.** The sealed material contains a measured selection/output effect, but no artefact executes the required purely public metamorphic comparison. The repository therefore does not license a VMem defect claim from this material.

## Provenance and audit boundary

The current repository tip is `c1c8eb614fb92f19c872cfa09b7e50fc1ed50fae`. The cited scripts, pinned source copies, `app.py`, and report bundle were last committed locally in `a92a88f20038670f1c510fd12cf65aae6a27f919`; the retrieval result file has a later local commit `7f0dfbf8aaa5d3965c434400bae645f69e2498a7`. The pinned public VMem identity is upstream commit `39291e4f272f6b4f270691d930926ab5930f942e`, and `vendor/provenance.json:2-8` records the upstream repository and the `pipeline.py` SHA-256. The three local `pipeline.py` copies named in the brief have the same SHA-256 (`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`) and agree at every line cited below (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:149-185,505-522,674-750,1249-1265,1293-1298`; the corresponding ranges in `work/S17_cpu_preflight/original/modeling/pipeline.py` and `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`; local commit `a92a88f`, upstream commit `39291e4`).

The audit is archival. No sealed job was rerun, no GPU was used, and no existing file was modified.

In each artefact subsection below, a citation written as `:N-M` refers to that subsection's named file and its stated local commit; citations that introduce another file spell out its path, lines, and commit.

## Q1 — What each artefact actually executed

### `arm_state_isolation_test.py` (job 595599)

The script constructs **one** `VMemPipeline` on CUDA (`work/S103_selector_free_baseline/arm_state_isolation_test.py:82-85`, local `a92a88f`). For each of three windows it runs:

* A: `isolate_arm_state` → `build_bank` → NMS-on selection (`:136-138`).
* B: `isolate_arm_state` → `build_bank` → public `get_context_info(..., False)` → `isolate_arm_state` → `build_bank` → NMS-on selection (`:140-145`).
* C: `isolate_arm_state` → `build_bank` → NMS-off → NMS-on without the second isolation, to reproduce the contaminated ordering (`:147-150`).

Inside `build_bank`, the public calls are `initialize` (`:109`), `construct_and_store_scene` (`:112-113,118-119`), the five-frame priming `get_context_info` (`:114-115`), and the final public NMS selection (`:121-123`). However, the harness also writes `latents`, `encoder_embeddings`, `c2ws`, `Ks`, and `pil_frames` directly (`:101-108,116-117`), and `isolate_arm_state` performs `reset()` followed by direct list/dictionary/global-step mutation and `delattr(pipe, 'initial_threshold')` (`:68-80`). It is therefore not a fresh object versus a previously used object followed only by public `initialize(...)`; it is one reused object with a test/worker-defined enhanced isolation routine.

The recorded comparison is equality of effective threshold, ordered frame IDs, and padding multiplicities (`:152-167`), plus a non-vacuity check against the deliberately contaminated sequence (`:168-175`). It is a valid check of that enhanced harness isolation, not a public lifecycle metamorphic test.

### `leak_regime_census.py` (job 595614)

This script also constructs one CUDA pipeline (`work/S103_selector_free_baseline/leak_regime_census.py:93-95`, local `a92a88f`). Each window first uses the same enhanced isolation routine (`:82-91`), then `build_bank` calls `initialize`, directly appends internal fields, constructs the scene, primes `get_context_info`, appends more fields, and reconstructs (`:107-130`). Its first build calls NMS-on, NMS-off, then NMS-on (`:167-173`); a second rebuild again uses enhanced isolation and calls NMS-off then NMS-on (`:175-194`). The direct writes and `delattr` are outside the public API (`:82-91,110-116`), and no fresh pipeline is constructed for comparison. This is a zero-diffusion selection census, not the requested public sequence.

The bundled JSON records 16 attempted windows, 14 successful windows, two `w0` setup errors, and `CONTENT=8`, `NULL=2`, `PERMUTATION=4`; it also records slot-0 invariance and no ground-truth reads (`docs/report/bundle/LEAK_REGIME_CENSUS.json:1-42`, local `a92a88f`). The authoritative result describes the same census as zero-diffusion retrieval metadata collected before scoring (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:82-103`, local `7f0dfbf`; the script itself is local `a92a88f`).

### `nms_off_threshold_independence.py` (job 595625)

This script constructs one CUDA pipeline (`work/S103_selector_free_baseline/nms_off_threshold_independence.py:77-79`, local `a92a88f`). Each window uses enhanced isolation and a bank builder that calls `initialize`, directly appends internal fields, constructs the scene, and primes the selector (`:66-112`). It then calls public NMS-disabled `get_context_info` (`:114-117`) after directly assigning `pipe.initial_threshold` to several values (`:135-138`), deletes the attribute and calls the selector again (`:140-147`). This is an attribute-intervention test of the disabled branch. It is not a fresh-versus-used `initialize` comparison and does not stay inside the public API.

### Sealed S111/S113 receipts as context

The sealed S111 runner likewise constructs one pipeline (`work/S103_selector_free_baseline/nms_s111.py:79-81`, local `a92a88f`), calls `initialize`, directly appends bank state, primes at five frames, then calls NMS-off followed by NMS-on on that object (`:143-172`). Its receipt is `NMS_RECEIPT.json`, job 594957, 88 runs, explicitly marked `RUNS_COMPLETE_UNSCORED` and using natural five-frame threshold priming (`docs/report/bundle/NMS_RECEIPT.json:4818-4841`, local `a92a88f`). The clean S113 receipt is job 595887, 28 unscored runs, and explicitly says it replaces the withdrawn arm with an isolated retrieval state (`docs/report/bundle/NMS_ON_CLEAN_RECEIPT.json:1453-1469`, local `a92a88f`). Neither receipt is a fresh-pipeline/public-`initialize` metamorphic pair.

## Receipt inventory

The report bundle lists `LEAK_REGIME_CENSUS.json`, `NMS_ON_CLEAN_RECEIPT.json`, and `NMS_RECEIPT.json`, but does not list standalone `ARM_STATE_ISOLATION.json` or `NMS_OFF_THRESHOLD_INDEPENDENCE.json` (`docs/report/TECHNICAL_REPORT_20260918.md:549-566`, local `a92a88f`). The two missing gate JSONs are only output destinations in their generators (`arm_state_isolation_test.py:181-191`; `nms_off_threshold_independence.py:156-166`, local `a92a88f`). Thus the auditable sealed JSON is the census plus the S111/S113 receipts; the gate results are also described in the report, with their exact scopes: 595599 is 11/11 enhanced-isolation checks over three scene-13 windows, while 595625 is a six-window forced-threshold check (`docs/report/TECHNICAL_REPORT_20260918.md:254-265`, local `a92a88f`).

## Q2 — Does any artefact already constitute the metamorphic test?

**No. The reading in the brief is correct.**

`isolate_arm_state` calls public `reset()` but then clears mutable lists, a dictionary, `global_step`, and `initial_threshold` directly (`work/S103_selector_free_baseline/arm_state_isolation_test.py:68-80`, local `a92a88f`). The generated receipt text itself labels this as “reset plus clearing every mutable retrieval field plus deleting `initial_threshold`” and records that reset alone is insufficient (`:181-186`). That proves what the worker/harness needed to make its arms comparable. It does not prove that VMem's public reset contract promises a particular cross-history observable result.

The three artefacts license only these narrower statements:

* 595599: under the enhanced isolation routine, the selected retrieval order and padding match between the clean and isolated-after-NMS-off executions, and the gate detects the contaminated ordering (`arm_state_isolation_test.py:152-175`; report `TECHNICAL_REPORT_20260918.md:254-261`).
* 595614: on the successful 14-window panel, the leaked threshold gives the recorded NULL/PERMUTATION/CONTENT census and slot-0 invariant, before diffusion or ground-truth scoring (`LEAK_REGIME_CENSUS.json:1-42`; retrieval report `RETRIEVAL_ARMS_RESULT_20260918.md:82-103`).
* 595625: the NMS-disabled selection is unchanged under the tested threshold values and deletion probe, within six windows (`nms_off_threshold_independence.py:133-165`; report `TECHNICAL_REPORT_20260918.md:262-265`).

None compares a newly constructed pipeline with a previously used pipeline followed only by public `initialize(...)` and then the same public observation. Direct `delattr` is evidence about the harness's isolation needs and the likely source of the measured effect; it is not, by itself, a public-contract violation.

The measured effect remains real as a measurement of the executed arms: `memory_nms_on_clean − memory_nms_on (leaked) = +0.245 dB`, SD 0.711, positive in 6/14 windows (`docs/RETRIEVAL_ARMS_RESULT_20260918.md:40-49`, local `7f0dfbf`). The report explicitly limits the validity gate to retrieval selection and separates it from generated-output invariance (`docs/report/TECHNICAL_REPORT_20260918.md:254-261`, local `a92a88f`). That effect cannot be promoted to a lifecycle defect without an oracle.

## Q3 — Is a defensible public relation derivable?

The relation required for a defect claim would have to be stated in advance and supported by public semantics: equivalent public initial conditions, followed by two public call sequences, must imply equal publicly observable outcomes. None of the three proposed sources supplies that implication.

**(a) `initialize(image, c2w, K)` docstring/signature.** The docstring says that initialization uses one image and camera parameters and sets up internal state without generating additional frames (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:149-161`, local `a92a88f`, upstream `39291e4`). It does not say that the result is history-independent, deterministic across a reused object, or equivalent to a fresh constructor. The signature alone cannot add that promise. The shipped README only gives installation/demo usage (`work/S17C_interface_preparation/isolated_vmem_source/README.md:42-57`, local `a92a88f`), with no lifecycle equivalence statement.

**(b) `initialize()` calling `reset()` and rebuilding `c2ws`.** `reset()` has no docstring and clears a set of fields (`pipeline.py:135-147`); `initialize()` then encodes the image and rebuilds `latents`, `encoder_embeddings`, `c2ws`, `Ks`, and `pil_frames` (`:162-185`). The inline comment “Reset internal state” (`:162`) is implementation commentary, not a complete public contract. In particular, `initial_threshold` is not cleared by `reset()` (`:135-147`), while `get_context_info` reads it after the conditional assignment branch (`:674-708`). The source has `self.c2ws = [c2w]` at `:180`, appends generated target poses at `:1297`, and only pops them in undo at `:1360`; no setter exists. This confirms the requested c2ws fact, but the `initialize` assignment means c2ws asymmetry is attribution evidence, not an oracle. The documented consumer path is `get_context_info` (`:505-522,674-750`) and generation concatenates/normalizes context and target cameras at `:1249-1265`; these code paths do not create a public history-independence promise.

**(c) `Choose New Image`.** `app.py` constructs a module-level `MODEL = VMemPipeline(...)` and an empty `NAVIGATORS` list (`work/S17_cpu_preflight/original/app.py:19-23`, local `a92a88f`). A new navigator wraps that same `MODEL` and calls `initialize` only when `NAVIGATORS` is empty (`:178-192`). The button labelled “Choose New Image” clears `NAVIGATORS` and UI values (`:687-698`); the upload/selection handlers likewise clear the visualization directory and `NAVIGATORS` (`:357-370,424-437`). The explicit visualization comment concerns preventing users from seeing one another's files (`:362-363,426-427`), not equality of pipeline selection outputs. A user-facing session boundary is a plausible intent, but the source does not state the needed observable relation “same image/camera/intrinsics produce the same retrieval selection regardless of prior pipeline history.” Treating the label as that exact contract would be an auditor's inference.

Therefore no defensible public metamorphic relation R is currently available. The code establishes a stale-read mechanism and a reachable reused singleton; it does not establish the semantic oracle needed to call that mechanism a defect.

## Q4 — Conditional cheapest test and true cost

If an owner first supplies and pre-registers a public relation R, the cheapest meaningful observation would be **ordered retrieval identity**, not generated pixels:

1. Sequence A: fresh `VMemPipeline` → public `initialize(I, P, K)` → the same public preparation of a nontrivial bank → public context selection.
2. Sequence B: a pipeline after an allowed public history → public `initialize(I, P, K)` → the same public preparation and query → context selection.
3. Compare ordered `context_time_indices`/frame IDs returned in the public context result (`pipeline.py:752-764`, local `a92a88f`). A preregistered difference would license a selector/lifecycle defect claim only. It would not license claims about hidden state, generated pixels, PSNR, or the whole app.

This is not a zero-GPU test for the real VMem implementation. The constructor loads VMem, VAE, CLIP, and CUT3R components (`pipeline.py:47-90`); `initialize` performs VAE and image encoding (`:173-177`); nontrivial context selection uses surfel rendering (`:631-647`); and public trajectory preparation runs diffusion and appends generated state (`:1269-1298`). Selection identity can avoid the final diffusion/PSNR scoring **once an equivalent bank already exists**, but reusing sealed JSON or manually pre-populating fields leaves the public sequence and therefore does not test R. The archival scripts themselves declare `device='cuda'` (`arm_state_isolation_test.py:82-85`; `leak_regime_census.py:93-96`; `nms_off_threshold_independence.py:77-80`, local `a92a88f`). With no GPU authorization, this conditional test must not be run in this round.

## Q5 — Disposition

`NO-DEFENSIBLE-ORACLE`.

VMem should be recorded as a worked example with a measured effect and no defect claim. The honest project inventory is therefore: **GEN3C is the one defensible HIT, with no measured consequence; VMem is the one measured effect, with no defensible defect oracle** (`RESEARCH_MEMORY.md:2048-2056`, local `c1c8eb6`). Keep `new_method_validated=false` and `novelty_authorization=NONE` as recorded in the same ledger (`:2056`).
