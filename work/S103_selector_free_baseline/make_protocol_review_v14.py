#!/usr/bin/env python3
"""Record the project owner's pre-run protocol review decision for S103 v11.

AUTHORSHIP AND RESPONSIBILITY
-----------------------------
The decision recorded here is the human project owner's.  This script is a
transcription and hashing tool: it computes evidence digests and serialises the
decision text that the owner approved.  Per ICLR 2026 Reviewer Guide, AI use in
a review must be disclosed and the named reviewer takes full responsibility for
the content; both facts are stated explicitly in the review body.

This tool writes a review file only.  It cannot bind the review into a contract,
cannot run the validator, and cannot submit a job.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/yliutz/geometry-world-modeling")
CODE = ROOT / "work/S103_selector_free_baseline"
WIN = CODE / "window_scene13_w001_20260916"
AGENTS = ROOT / "work/agents"
OUT = CODE / "reviews/PROTOCOL_REVIEW_20260917_HUMAN_V14.json"

# The exact adapter-bound protocol this decision applies to.
TARGET_PROTOCOL_SHA = "bfdb1068b4a3bc39ec35339547d137c8998f845227e16c707d43461089e78517"

EVIDENCE = [
    WIN / "GATE0_CONTRACT_ADAPTER_BOUND_v14.json",
    WIN / "GATE0_CONTRACT_CANDIDATE_v14.json",
    WIN / "RUNTIME_BINDING_v5.json",
    WIN / "EXACT_ISOLATION_RECEIPT_v5_594089.json",
    WIN / "predictor_inputs.json",
    WIN / "scorer_inputs.json",
    WIN / "WINDOW_MANIFEST.json",
    WIN / "SOURCE_MANIFEST_v1.json",
    CODE / "predictor_s103.py",
    CODE / "seal_predictions_s103.py",
    CODE / "scorer_s103.py",
    CODE / "prepare_formal_bundle_s103.py",
    CODE / "run_s103_vmem_base.slurm",
    CODE / "METRIC_DEFINITION_v1.json",
    CODE / "FORMAL_CHAIN_SOFTWARE_RECEIPT_20260917_v6.json",
    CODE / "reviews/ADAPTER_REVIEW_20260917_CLAUDE_V3.json",
    CODE / "reviews/HUMAN_REVIEW_CHECKLIST_20260917.md",
    ROOT / "work/S102_gate0_tum/validate_gate0_v2.py",
    AGENTS / "independent_adversarial_review_s103_v9_20260917.md",
    AGENTS / "field_practice_evidence_for_human_review_20260917.md",
]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path) -> dict:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> int:
    contract = json.loads((WIN / "GATE0_CONTRACT_ADAPTER_BOUND_v14.json").read_text())
    protocol = contract["protocol"]
    actual = hashlib.sha256(json.dumps(protocol, sort_keys=True, separators=(",", ":"),
                                       allow_nan=False).encode()).hexdigest()
    if actual != TARGET_PROTOCOL_SHA:
        raise SystemExit(f"protocol SHA drifted: {actual} != {TARGET_PROTOCOL_SHA}\n"
                         "The reviewed protocol changed; the decision must be re-made.")

    review = {
        "schema": "gwm-s103-protocol-prerun-review-v1",
        "verdict": "PRE_RUN_APPROVED",
        "status": "PRE_RUN_APPROVED",
        "reviewer": "yliutz-human-review-20260917",
        "reviewer_role": "project owner; human decision maker of record",
        "reviewed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "protocol_sha256": TARGET_PROTOCOL_SHA,
        "contract_ref": ref(WIN / "GATE0_CONTRACT_ADAPTER_BOUND_v14.json"),
        "approved_scope": (
            "One selector-free S103-VMemBase development forward on the frozen "
            "rgbd-scenes-v2 scene_13 seq-01 window (history 0/15/30/45, targets 60/75/90/105). "
            "Execution permission only. This approval does not authorise any held-out claim, "
            "any comparison against another arm, any geometry claim, any memory or selection "
            "benefit claim, or any novelty claim."),
        "evidence_checked": [ref(path) for path in EVIDENCE],
        "checks": {
            "scope_is_development_baseline_and_exposed_data_declared": True,
            "target_pose_supplied_as_command_is_positively_disclosed": True,
            "metric_is_rgb_only_so_pose_is_never_input_and_outcome": True,
            "access_accounting_is_measured_not_a_hardcoded_constant": True,
            "checkpoint_identity_reverified_in_process_before_deserialisation": True,
            "calibration_status_is_self_limiting_with_written_basis": True,
            "isolation_receipt_binds_the_predictor_that_will_run": True,
            "sampling_and_runtime_knobs_are_declared_in_expected_config": True,
            "all_software_regressions_and_validator_self_test_pass": True,
            "adapter_review_is_bound_and_by_a_different_reviewer": True,
            "claim_boundary_excludes_heldout_comparison_and_novelty": True,
            "prior_versions_are_snapshotted_and_not_overwritten": True,
        },
        "findings": [
            "The adapter-bound v11 protocol canonical SHA-256 was independently recomputed at "
            "decision time and equals bfdb1068b4a3bc39ec35339547d137c8998f845227e16c707d43461089e78517. "
            "If the protocol changes in any byte, this approval is void by construction.",
            "Supplying the four target-frame camera poses as predeclared commands matches the "
            "standard protocol of the model this work builds on. VMem (arXiv 2506.18903v3) states "
            "that generation proceeds 'along the ground truth camera trajectories' of each "
            "ground-truth test sequence and defines the task as camera-conditioned autoregressive "
            "view generation with M=4 target views. The v11 contract additionally encodes this as a "
            "machine-readable future_modality_disclosure enforced by the validator, which is "
            "stricter than the source paper's prose-only statement.",
            "Because the frozen metric (METRIC_DEFINITION_v1.json) scores RGB only and explicitly "
            "does not open future depth or pose, target pose is an input and never also an outcome. "
            "There is therefore no circularity in the primary score.",
            "The three prediction-receipt access fields are no longer source constants. They are "
            "derived from a CPython sys.addaudithook 'open' event record, and both the sealer and "
            "the scorer now refuse a seal that does not declare that measurement method. This "
            "closes a gate that was previously vacuous.",
            "All four checkpoints (vmem, cut3r, clip, vae) are hash-verified inside the prediction "
            "process immediately before the first torch.load(weights_only=False), removing the "
            "cross-job interval between probe-time and load-time verification.",
            "Isolation receipt from Slurm job 593971 (dgx-21, COMPLETED, exit 0:0, 26 s) binds "
            "predictor SHA d98569c667067b2375b819d5205753f1bc284a5e2dd3239b58047c90d0fa43ed, which "
            "is the predictor that will execute, and reports project root invisible, dataset root "
            "invisible, all declared outcome paths invisible, and read-only mounts non-writable.",
            "calibration_status was downgraded from 'verified' to "
            "'dataset_declared_intrinsics_no_independent_calibration' with a written basis. This is "
            "supported by Brachmann et al., 'On the Limits of Pseudo Ground Truth in Visual Camera "
            "Re-localisation', ICCV 2021 (arXiv 2109.00524), which shows that benchmarks built on a "
            "reference algorithm measure how well a method replicates that reference algorithm, and "
            "that evaluation outcomes vary with the choice of reference algorithm.",
            "Five software regressions plus the validator self-test pass, and the previous file "
            "versions are preserved under history_before_receipt_semantics_fix_20260917/ rather "
            "than overwritten.",
        ],
        "limitations": [
            "N-1 REPLAY ENVELOPE AND CROSS-NODE VARIANCE. This is a single run: N=4 target frames, "
            "one window, one sequence, one scene, one seed, no repeat and no control arm. The "
            "resulting number MUST NOT be compared with any other number until a replay envelope "
            "has been established by at least three byte-identical repeats ON THE SAME NODE TYPE, "
            "and until cross-node variance has been measured and reported separately. This project's "
            "own Slurm accounting shows prior jobs were scheduled across dgx-09, dgx-21 and dgx-27, "
            "and Slurm does not guarantee node affinity. Hochlehnert et al., 'A Sober Look at "
            "Progress in Language Model Reasoning', COLM 2025 (arXiv 2504.07086v2) demonstrates that "
            "even with torch.use_deterministic_algorithms(True), fixed CUDA seeds and cuDNN "
            "benchmarking disabled, cross-hardware differences persisted and exceeded the standard "
            "deviation. The assumption that a fixed seed alone guarantees exact replay is therefore "
            "UNVERIFIED for this setup and must not be assumed.",
            "N-1b SMALL-SAMPLE INSTABILITY. The same study reports 5-15 percentage point standard "
            "deviation across seeds and concludes that single-seed evaluation on small datasets is "
            "highly unstable, naming a 30-sample benchmark as yielding unreliable comparisons. This "
            "run uses four target frames. It is adequate as an end-to-end executability check and is "
            "not adequate as a basis for any comparative claim.",
            "N-2 REFERENCE-ALGORITHM SEMANTICS AND SHARED-SOURCE BIAS. The RGB-D Scenes v2 poses are "
            "RGB-D Mapping estimates, not motion-capture ground truth, and no independent "
            "calibration was performed by this project. Any result from this run must be reported as "
            "agreement with the RGB-D Mapping reference algorithm's output, NOT as agreement with "
            "physical geometry. Furthermore, because the pipeline contains CUT3R, itself a geometry "
            "estimation method, there is a concrete risk of the similarity-to-reference bias that "
            "Brachmann et al. (ICCV 2021) require to be taken into account before any ranking claim. "
            "This must be stated in the results document.",
            "EXPOSED DEVELOPMENT DATA. scene_13 metadata was exposed before freezing. This run is "
            "not blind, not held-out, and cannot become held-out retroactively. "
            "heldout_exposure_review_ref and baseline_acceptance_ref are null, correctly, for this "
            "scope.",
            "MEASUREMENT COVERAGE OF THE AUDIT HOOK. The sys.addaudithook record observes CPython "
            "'open' events. It does not observe reads performed by native code that bypasses the "
            "CPython file API. It strengthens but does not replace the Apptainer mount whitelist as "
            "the primary enforcement of the boundary.",
            "REVIEW INDEPENDENCE. This is a different-author review by the project owner, not an "
            "external independent reproduction, and must never be recorded as the latter. The "
            "adapter-role review for this revision was issued by an AI session identity "
            "(claude-session-review-20260917), not by an external party.",
            "DISCLOSURE OF AI ASSISTANCE. Per ICLR 2026 Reviewer Guide practice, AI assistance is "
            "disclosed: the adversarial analysis, the source cross-checks against the pinned VMem "
            "code, the literature retrieval, the evidence hashing and the drafting of this text were "
            "performed by an AI assistant. The reviewer named above read the findings, made the "
            "approve/reject decision, and takes full responsibility for this review's content. The "
            "reviewer did not personally re-derive every numerical check listed under 'checks'.",
            "PARTIAL RE-AUDIT. For the 2026-09-17 revision, seal_predictions_s103.py and "
            "scorer_s103.py were reviewed only along the access-semantics and disclosure paths that "
            "changed. Their remaining logic was not exhaustively re-audited in this pass.",
            "LAUNCHER DEFECT AND RE-APPROVAL. This revision exists because the previously "
            "approved protocol v11 was not runnable: run_s103_vmem_base.slurm derived the bundle "
            "path from BASH_SOURCE, but Slurm copies the batch script to a spool directory, so "
            "the spool copy was bind-mounted at /opt/gwm-formal and job 594034 failed after 11 s "
            "on dgx-10. The sbatch now pins the absolute bundle root and refuses to run against an "
            "incomplete bundle, and the regression test that had encoded the defective behaviour "
            "as a requirement was corrected. The protocol diff from v11 is exactly five mechanical "
            "fields (bundle_root, sbatch bytes/SHA, regression receipt path/SHA); the window, "
            "budget, metric, disclosure, calibration, checkpoints, predictor and isolation receipt "
            "are byte-identical. The reviewer re-approved on this basis and all other limitations "
            "carry over unchanged.",
            "PRECISION POLICY CHANGE AND RE-APPROVAL. This revision changes one substantive "
            "field: budget.dtype moves from fp16_cuda_model_fp32_saved_outputs to "
            "fp32_params_cuda_autocast_fp32_saved_outputs, with a written basis. The previous fp16 "
            "setting was a divergence from the pinned reference, where VMemPipeline defaults to "
            "torch.float32, app.py does not override it, and do_sample applies CUDA autocast. Job "
            "594069 exposed the divergence as an index-put dtype error at pipeline.py:1156. The fix "
            "restores fidelity to the reference rather than masking the mismatch. Nineteen further "
            "field changes are purely downstream re-hashing (predictor, runtime binding v5, isolation "
            "receipt from job 594089, adapter review v2, bundle root v6, regression receipt v5, sbatch, "
            "boundary id). The frozen window, selection_k, sampling steps, output count, seed, metric "
            "definition, future_modality_disclosure, calibration declaration, checkpoints, scope and "
            "claim_boundary are byte-identical to the previously approved protocol. All other "
            "limitations carry over unchanged.",
            "RUN IDENTITY FIX AND FIRST SUCCESSFUL FORWARD (this revision). No scientific field "
            "changed. Job 594105 executed the fp32 predictor and produced a complete prediction "
            "(4 target frames, 15,925,376 bytes fp32 RGB) with a clean access record: no forbidden "
            "root opens, zero opens outside the allowlist, withheld future modalities never opened, "
            "and access accounting recorded as measured rather than constant. The seal stage then "
            "correctly refused the run because the sbatch passed a literal EXECUTION_BOUNDARY_ID "
            "still reading v3 while the contract declared v5. The sbatch now derives both the "
            "boundary id and the run id from the bundled contract and aborts if either is absent, "
            "and a regression assertion rejects any reintroduced literal. The stale receipt was not "
            "edited and the prediction from 594105 is not carried forward; the run is repeated under "
            "the corrected identity. Eight protocol fields changed, all mechanical: adapter review "
            "v3, bundle root v7, regression receipt v6, and the sbatch hash. Precision, seed, "
            "sampling steps, window, scope, boundary id, metric and predictor hash are unchanged "
            "from the previously approved protocol, and all limitations carry over.",
            "NO SCIENTIFIC OR NOVELTY IMPLICATION. Approval grants scoped execution permission "
            "only. It is not acceptance of any result. Post-run acceptance is a separate stage. "
            "new_method_validated=false; novelty_authorization=NONE.",
        ],
        "post_run_conditions": [
            "Report the score as RGB reconstruction agreement with the RGB-D Mapping reference, "
            "with the N-2 shared-source bias caveat stated in the same paragraph.",
            "Do not open a second arm or make any comparison until the N-1 same-node replay "
            "envelope exists and cross-node variance has been separately measured.",
            "Record the executing node from sacct alongside the score so cross-node effects remain "
            "auditable.",
        ],
        "attestation": (
            "I approve execution of this exact frozen protocol at the declared development scope, "
            "subject to every limitation and post-run condition recorded above. I understand that "
            "this authorises one run and no claim."),
        "new_method_validated": False,
        "novelty_authorization": "NONE",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing review: {OUT}")
    OUT.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"written": ref(OUT), "reviewer": review["reviewer"],
                      "verdict": review["verdict"],
                      "protocol_sha256": review["protocol_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
