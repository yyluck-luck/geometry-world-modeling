# Independent adversarial review — S103-VMemBase contract v9 (2026-09-17)

## 0. Status, identity, and what this document is NOT

- **Reviewer identity:** `claude-session-review-20260917` (this session). This identity is **not** in
  `REVIEWER_ROLE_ALLOWLIST` in `work/S102_gate0_tum/validate_gate0_v2.py:44-47`, which admits only
  `codex-agent-protocol-review-20260916` for the `protocol` role.
- **Therefore this document does NOT and CANNOT unblock Gate0.** It is not a
  `PRE_RUN_APPROVED` artifact, it must not be bound into `review_ref`, and binding it would fail
  the validator. No attempt was made to impersonate the allowlisted identity or to modify the
  allowlist.
- **Purpose:** substantive third-party scrutiny of the frozen protocol before the allowlisted
  reviewer issues its decision, so that the eventual approval is made against a hardened target.
- **Scope of review:** `GATE0_CONTRACT_ADAPTER_BOUND_v9.json`
  (file SHA-256 `b426a63ee5274f880369b73d6a8bdf40966c37ebe9d45a29b103d78e01fade9b`,
  canonical `protocol` SHA-256 `96187c8dc44dd3d1b77c452889d7b558ffd591deab55daa8e61fc313da9bed66`,
  `protocol.status = FROZEN`, `review_ref = null`).
- **Method:** static reading of the contract, predictor, scorer, sealer, bundle preparer, validator,
  both Slurm scripts and both input manifests, plus **line-level cross-checking against the pinned
  official VMem source** at `/home/yliutz/gwm_source_transport_20260915/vmem/`. No job was
  submitted; no model, dataset, future RGB/depth/pose, or GT byte was opened by this review.
- **Framework:** `sci-scientific-critical-thinking` skill (methodology critique, bias detection,
  claim evaluation) applied to an engineering protocol rather than a paper; severity labels follow
  the project's existing BLOCKER/HIGH/MEDIUM/LOW convention.

`new_method_validated=false`; `novelty_authorization=NONE`. Nothing here changes either.

---

## 1. Independently re-verified as CORRECT (not merely trusted)

These were checked by recomputation or by reading the pinned upstream source, not by accepting the
author's assertion. Recording them matters: a review that only lists complaints gives the author no
way to tell a checked-and-passed item from an unchecked one.

**V-1 — Preprocessing is numerically faithful to the pinned official pipeline.**
`predictor_s103.py:103` does `interpolate(t,(576,768),mode='area')[:,:,:,96:672]`. Upstream
`utils/util.py:354-405` (`transform_img_and_K`, `mode="crop"`) does
`F.interpolate(image,(rh,rw),mode="area",antialias=False)` then
`TF.crop(top=ct,left=cl,height=H,width=W)`. For source `(h,w)=(480,640)` and target `(H,W)=(576,576)`,
`get_resizing_factor` with `cover_target=True` yields `1.2`, so `(rh,rw)=(576,768)` — exactly the
hardcoded pair. Centre crop gives `cx_center=int(0.5*768)=384`, `cl=384-288=96`;
`cy_center=int(0.5*576)=288`, `ct=288-288=0`. So `TF.crop(top=0,left=96,h=576,w=576)` is the same
tensor slice as `[:,:,:,96:672]`. **Equivalent.** I initially suspected `mode='area'` was wrong for
upscaling (it degenerates toward nearest-neighbour); it is not a defect here because upstream uses
the identical call, so the predictor reproduces upstream behaviour including that quirk. Do not
"fix" this — fixing it would break fidelity to the frozen baseline.

**V-2 — Normalisation reordering is safe.**
Upstream `modeling/pipeline.py:170` maps to `[-1,1]` *before* encoding (`/127.5 - 1.0`); the
predictor maps *after* resizing (`/255`, resize, `*2-1`). Area interpolation is a convex weighted
average (weights sum to 1) and `x ↦ 2x-1` is affine, so the two orders commute exactly up to float
rounding. **No finding.** Documented here so a later reader does not "correct" it into a real
divergence.

**V-3 — Intrinsics arithmetic is correct and asserted.**
`model_grid_K` (`predictor_s103.py:88-93`): `fx=fy=540.021232*1.2=648.0254784`;
`cx=320*1.2-96=288`; `cy=240*1.2=288`. On the 576×576 grid the principal point is exactly the
centre, consistent with the declared 0.5-pixel-centre convention. The predictor additionally
asserts the homogeneous row, `cx=288`, and equality across all eight K matrices
(`predictor_s103.py:130-135`). The all-eight camera centring is verified by a relative-translation
invariance check to `atol=1e-5` (`:124-127`). This closes the intrinsics/camera-frame inconsistency
recorded in the 2026-09-16T18:44 ledger entry.

**V-4 — Prior blocker C-001 is CLOSED.** `ADVERSARIAL_GATE0_AGENT_C.json` reported that the bundle
preparer executed a caller-supplied `--validator`. `prepare_formal_bundle_s103.py:80-81` now
requires every caller-supplied path to equal the contract-bound path, and `resolve_ref` enforces
byte count and SHA-256. Line 64 additionally refuses to build unless `review_ref` is a dict.

**V-5 — Prior blocker C-002 is CLOSED.** `canonical_identity` (`validate_gate0_v2.py:60-67`)
rejects any non-lowercase or non-canonical alias, and `REVIEWER_ROLE_ALLOWLIST` (`:44-47`) is a
per-role frozenset. Case/alias self-spoofing is no longer possible.

**V-6 — Prior blocker C-003 is SUBSTANTIALLY CLOSED.** The scorer no longer accepts a bare
self-describing seal: `scorer_s103.py:149-220` binds the dispatch manifest, the launch-guard
receipt, every component SHA, the runtime binding, the isolation receipt and the execution boundary
id, and enforces the temporal ordering `launched_at ≤ completed_at ≤ sealed_at` before a single
future RGB byte is opened. This is a genuinely strong chain. (One residual gap: see F-1.)

**V-7 — Prior finding C-004 is CLOSED.** The stale regression receipt is superseded by
`FORMAL_CHAIN_SOFTWARE_RECEIPT_20260917_v2.json`
(SHA `4a89539bd96e614eebf4bea02e898556bce98a314652dd9300ba6827c39370b7`, 2026-09-17T05:37:38Z),
which is the receipt actually bound at `protocol.formal_execution.formal_chain_regression_receipt_ref`.
Its self-declared scope — "CPU-only code and synthetic-fixture checks; no GPU, model, research data,
or future payload" — is stated correctly and is not overclaimed.

**V-8 — Isolation evidence transfers to the formal run.** `exact_boundary_probe.slurm:27-35` and
`run_s103_vmem_base.slurm:31-43` use the same flags (`--nv --containall --no-home --cleanenv`) and
the same four read-only host binds (`ENVROOT`, `SOURCE`, `WEIGHTS`, `STAGE`) plus one read-only
bundle and one read-write output. Only the bundle contents and the two container-internal mount
points differ (`/opt/gwm-boundary`→`/opt/gwm-formal`, `/mnt/receipt`→`/mnt/predictions`). The
isolation-relevant property — which host paths are reachable and with what permissions — is
identical, so job 591500's `EXACT_BOUNDARY_PROBE_PASS` legitimately transfers.

---

## 2. Findings

### F-1 — HIGH — The three "no future access" seal fields are hardcoded literals, and the scorer's gate on them is therefore vacuous

**Evidence.** `predictor_s103.py:144` writes the receipt dict containing, verbatim:
`'future_outcome_files_opened':False, 'future_gt_opened':False, 'unauthorized_input_reads':0`.
These are **constants in the source**, not measurements. Nothing counts reads, traces syscalls, or
compares an observed file set against the manifest. The predictor will emit exactly these three
values on every successful run, by construction.

`scorer_s103.py:212-214` then gates on them:
```
require(seal.get("unauthorized_input_reads") == 0, "predictor reported unauthorized reads")
require(seal.get("future_outcome_files_opened") is False and seal.get("future_gt_opened") is False,
        "seal reports future access")
```
A check that can only ever pass provides zero information. This is the *begging the question*
pattern the project's own principles forbid ("不以'未解码'冒充'未读字节'",
`RESEARCH_PRINCIPLES.md` 实验与证据要求 §3).

**Why it is HIGH, not BLOCKER.** The *real* enforcement — the Apptainer mount whitelist — is sound
and was independently probed (V-8). The substantive isolation property holds. The defect is that
the **audit trail misrepresents how it is known to hold**, which is precisely the failure mode this
project has spent a hundred work directories trying to avoid.

**Recommendation.** Either (a) rename to self-attested fields
(`predictor_declares_no_future_read: true`) and have the scorer require the *isolation receipt*
rather than the self-report, or (b) make them real: have the predictor record the resolved realpath
of every `open()` it performs (it already accumulates `reads[]`) and assert the set equals the
manifest set, then derive the booleans from that set. Option (b) is ~5 lines and makes the scorer's
gate meaningful.

---

### F-2 — HIGH — Target-frame pose ground truth is supplied to the predictor; path-level isolation is not information-level isolation

**Evidence.** `predictor_inputs.json` supplies `command_camera` for frames **60, 75, 90, 105**.
`scorer_inputs.json` declares `future_pose` for frames **60, 75, 90, 105** — the same four frames.
The C2W matrices handed to the predictor as "commands" are the dataset's RGB-D-Mapping estimated
poses for the target frames, i.e. the future-pose modality of the outcome set. The isolation
receipt's `all_declared_outcome_paths_invisible: true` is true **at the path level** (a second,
staged copy is what the predictor reads), and simultaneously the same information is inside the
container.

**This is disclosed, not hidden.** `protocol.target_camera_policy = "predeclared_command"`,
`protocol.scope = "development_baseline"`, `protocol.development_data_exposed = true`, and
`protocol.claim_boundary` explicitly excludes held-out claims. `PROTOCOL_PREREVIEW_AGENT_B.json`
finding #3 states it outright. The metric (`METRIC_DEFINITION_v1.json`) is **RGB-only** and declares
"Future depth and pose are not opened by this metric", so there is **no circularity in the score
itself** — pose is an input and is never an outcome. I verified this and it is correct.

**The residual risk is downstream misreading.** A reader six weeks from now sees a seal stamped
`future_gt_opened: false` and an isolation receipt stamped `all_declared_outcome_paths_invisible:
true` on a run that consumed target-pose GT. Combined with F-1 (those flags are constants), the
audit trail actively invites the error.

**Recommendation.** Add an explicit positive declaration to the prediction receipt and seal schema,
e.g. `target_pose_gt_provided_as_command: true` and
`future_modalities_withheld: ["future_rgb","future_depth"]`, and have the scorer *require* the
positive declaration to match the contract's `target_camera_policy`. State the same in one sentence
at the top of any results document. This costs nothing and permanently removes the ambiguity.

---

### F-3 — MEDIUM — Checkpoints are deserialised with `weights_only=False` without in-process hash verification (TOCTOU)

**Evidence.** `predictor_s103.py:45-49` installs a `torch.load` shim that forces
`weights_only=False` for `vmem_weights.pth` and `cut3r_512_dpt_4_64.pth`, i.e. **full pickle
deserialisation with arbitrary-code-execution semantics**. Line 82 then loads the VMem state dict.
The predictor verifies SHA-256 for the 13 staged manifest files (`read()` at `:62-65`) but performs
**no SHA verification of the four checkpoints**. Their hashes were verified in a *different Slurm
job at a different time* (591500).

The `WEIGHTS` bind is `:ro`, which mitigates substantially, and the read-only-ness itself was probed.
But the property "the bytes at load time are the bytes that were reviewed" is currently inferred
across a job boundary rather than asserted in-process.

**Recommendation.** Re-verify the four checkpoint SHA-256 values from `RUNTIME_BINDING_v3.json`
inside the predictor before the first `torch.load`, and record them in `PREDICTION_RECEIPT.json`.
Hashing ~12.5 GB costs tens of seconds against a 3600 s budget. This also makes the prediction
receipt self-contained for provenance.

---

### F-4 — MEDIUM — No replay-variance envelope; the resulting number will not be comparable to anything

**Evidence.** The design is N = 4 target frames, 1 window, 1 sequence, 1 scene, 1 seed (42), 1
forward. `METRIC_DEFINITION_v1.json` aggregates integer numerators over all four targets into a
single scalar MSE. There is no repeat, no no-op control, and no variance estimate.

For the declared `development_baseline` scope this is acceptable — the stated purpose is to prove
the forward runs end-to-end under the boundary. The risk is **scope creep at interpretation time**:
the moment an S104 arm produces a second number, the difference will be read as a result, with no
basis for distinguishing it from execution noise.

This project already learned exactly this lesson: S86's `B − A0 = −0.005878` was interpretable
*only because* A0 and A1 were byte-identical replays, which established the noise floor as zero.

**Recommendation.** Add to the post-run acceptance stage an explicit precondition: **no cross-arm
comparison is permitted until ≥3 byte-identical exact replays of this exact configuration have
established the replay envelope.** Encode it as a field in `post_run` so the validator can enforce
it, rather than leaving it to prose.

---

### F-5 — MEDIUM — `calibration_status: "verified"` overstates what the adapter review supports

**Evidence.** `protocol.datasets.rgbd-scenes-v2.camera.calibration_status = "verified"` is a frozen,
unqualified string. The bound adapter review (`ADAPTER_REVIEW_AGENT_A.json`) limits itself
explicitly: poses are "RGB-D Mapping estimates rather than motion-capture ground truth", and frame
order is used "only as chronology because the converted source does not provide hardware
timestamps". Elsewhere the same protocol is careful —
`pose_time_association` says "no hardware timestamp claim" — which makes the bare word "verified"
inconsistent with its own neighbours.

**Precedent within this project:** 7-Scenes Chess was rejected precisely for uncalibrated RGB/depth
(`GATE0_CANDIDATE_V2_RETRACTION_20260916.json` reason #1). A single word that reads as "calibrated
ground truth" is the same hazard in the opposite direction.

**Recommendation.** Replace with a self-limiting value such as
`"dataset_declared_intrinsics_no_independent_calibration"`, or make `calibration_status` an object
that binds the adapter review SHA and its evidence list. Cheap, and it removes a sentence that a
future reader could quote out of context.

---

### F-6 — LOW — Determinism-relevant runtime knobs live only in code, not in the frozen budget

**Evidence.** `predictor_s103.py:80` sets `torch.set_num_threads(8)` and
`torch.set_num_interop_threads(1)`; `:84` sets `AutoEncoder(chunk_size=1)`; `:140-141` hardcodes
`cfg_min=1.2`, `cfg=2.0`, `guider_types=1`, `decoding_t=1`. None appear in `protocol.budget` or
`protocol.expected_config`, so the validator cannot detect drift in them. The predictor SHA does
pin them transitively, which is why this is LOW rather than MEDIUM — but it means a predictor edit
that changes CFG would require re-review to *notice*, rather than failing a declarative check.

**Recommendation.** Lift `cfg`, `cfg_min`, `guider_types`, `decoding_t`, `chunk_size` and the thread
counts into `expected_config` and add them to the validator's `CONFIG_KEYS` comparison.

---

### F-7 — LOW — Operational: `mkdir` without `-p`

**Evidence.** `run_s103_vmem_base.slurm:28-29` uses bare `mkdir "$JOB_ROOT"` under `set -e`, and
`RUN_PARENT` (`/home/yliutz/gwm_prediction_runs/S103_VMEMBASE_SCENE13_W001`) is never created by the
script, yet `#SBATCH --output`/`--error` at `:10-11` write into it. If the parent does not exist at
submission time the job fails before any useful log exists, wasting a queue cycle. Create
`RUN_PARENT` before `sbatch` (or use `mkdir -p` for the parent only — keep the bare `mkdir` for
`JOB_ROOT` itself, since its collision-failure is a deliberate and correct anti-overwrite guard).

---

## 3. Overall assessment

**Design quality is high.** The dispatch→predict→seal→score chain with SHA binding at every hop,
timestamp ordering enforcement, a separate sealing container, the read-only mount whitelist, and a
negative control that refuses bundle creation unless the validator returns zero-error
`PRE_RUN_READY` — this is stronger provenance engineering than most published work in this area
carries. The three prior BLOCKERs from Agent C are genuinely closed, and I verified each rather
than taking it on report.

**The weaknesses are concentrated in one place: fields that *assert* a property the system does not
*measure* (F-1, F-2, F-5).** Ironically, the isolation itself is real; it is the bookkeeping about
the isolation that is weaker than it looks. Given that this project's entire contribution posture
rests on audit integrity, these are worth fixing before the first formal run rather than after.

**None of F-1…F-7 is a BLOCKER for a `development_baseline`-scoped run.** F-1, F-2 and F-5 are
wording/instrumentation fixes; F-3 is a hardening; F-4 is a post-run constraint; F-6/F-7 are
housekeeping. My assessment is that the protocol is **fit to run at the declared scope**, and that
F-1/F-2/F-5 should be fixed first because they are minutes of work and they permanently remove
three ways for this run to be misread later.

**What this run will and will not establish.** It will establish: VMem executes a complete forward
under an audited boundary on H800, and produces four sealed 576×576 RGB predictions with a
reproducible RGB reconstruction score. It will **not** establish: any held-out result (target poses
were given), any geometry claim (metric is RGB-only), any memory or selection benefit (there is no
selector and no comparison arm), any generalisation (N=4 frames, one scene), or any novelty.

---

## 4. Recommended action

1. Apply F-1 and F-2 (receipt/seal field semantics) and F-5 (`calibration_status` wording). These
   change the contract, so they produce a **v10** with a new canonical protocol SHA.
2. Optionally apply F-3 and F-6 in the same revision to avoid a second re-review cycle.
3. Have `codex-agent-protocol-review-20260916` review **v10**, not v9 — reviewing v9 and then
   editing would invalidate the binding, since the review must bind the exact final protocol SHA.
4. Run the validator; require zero errors and `PRE_RUN_READY`; build the immutable bundle; run the
   launch guard; submit one S103-VMemBase development forward from persistent remote `tmux`.
5. Record F-4 as a binding precondition in the post-run acceptance stage before any second arm.

If instead the decision is to ship v9 unchanged, that is defensible for a development-scope run —
but then F-1, F-2 and F-5 must be written verbatim into the results document's limitations section,
because the artifacts themselves will not carry them.

---

## 5. Limitations of this review

- Static analysis only. No execution, no GPU, no dataset, no future RGB/depth/pose, no GT.
- I did not verify the 217 artifact hashes myself; I relied on the validator's report of them, and
  on my own recomputation of the canonical protocol SHA and the v9 file SHA.
- I did not independently audit `seal_predictions_s103.py`, `verify_s103_scores.py`,
  `assemble_s103_reviewed_contract.py`, or the adapter `rgbd_scenes_v2.py` line by line; findings
  about them, if any, remain unknown rather than absent.
- I did not evaluate whether the *scientific design* is worth running — only whether the protocol
  does what it claims. Scientific merit is a separate judgement and is unaffected by this document.
- One reviewer, one pass. This is at best "different-author review"; it is **not** external
  independent reproduction, and per `RESEARCH_PRINCIPLES.md` it must not be recorded as such.
- This review is itself AI-generated and carries the biases of that process. It should be treated
  as a checklist of things to confirm, not as authority.
