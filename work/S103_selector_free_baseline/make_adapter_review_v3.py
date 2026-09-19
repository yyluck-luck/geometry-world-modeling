#!/usr/bin/env python3
"""Emit the 2026-09-17 adapter re-review required after predictor_s103.py changed.

The previously bound adapter review (ADAPTER_REVIEW_AGENT_A.json) lists
predictor_s103.py in its evidence_checked set, so the receipt-semantics fix
invalidated it by construction.  This tool records a fresh review by a different
reviewer identity.  It writes a review file only; it does not bind anything,
cannot approve the protocol, and cannot submit a job.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/yliutz/geometry-world-modeling")
CODE = ROOT / "work/S103_selector_free_baseline"
WIN = CODE / "window_scene13_w001_20260916"
ADAPTER_DIR = ROOT / "work/S102_gate0_3dmatch/adapter_v1"
OUT = CODE / "reviews/ADAPTER_REVIEW_20260917_CLAUDE_V3.json"

EVIDENCE = [
    ADAPTER_DIR / "rgbd_scenes_v2.py",
    ADAPTER_DIR / "SOURCE_EVIDENCE.md",
    ADAPTER_DIR / "sources/vmem_utils_util.py",
    ADAPTER_DIR / "sources/vmem_pipeline.py",
    ADAPTER_DIR / "sources/vmem_inference.yaml",
    CODE / "predictor_s103.py",
    CODE / "seal_predictions_s103.py",
    CODE / "scorer_s103.py",
    WIN / "predictor_inputs.json",
    WIN / "scorer_inputs.json",
    WIN / "WINDOW_MANIFEST.json",
    WIN / "RUNTIME_BINDING_v5.json",
    WIN / "EXACT_ISOLATION_RECEIPT_v5_594089.json",
    WIN / "GATE0_CONTRACT_CANDIDATE_v14.json",
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
    review = {
        "schema": "gwm-rgbd-scenes-v2-adapter-review-v1",
        "status": "ADAPTER_ACCEPTED",
        "adapter_sha256": sha(ADAPTER_DIR / "rgbd_scenes_v2.py"),
        "reviewer": "claude-session-review-20260917",
        "reviewed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "supersedes": "work/S103_selector_free_baseline/reviews/ADAPTER_REVIEW_20260917_CLAUDE_V2.json",
        "supersede_reason": (
            "The prior adapter review bound predictor_s103.py at SHA "
            "75af8cad1de25ea7e43ad90c6c7bd89de33d7aa86da50afe8735da612a11189f in its "
            "evidence_checked set. The 2026-09-17 receipt-semantics fix (review findings "
            "F-1/F-2/F-3/F-6) changed that file, so the prior review no longer verifies "
            "and had to be re-issued rather than silently reused."),
        "evidence_checked": [ref(path) for path in EVIDENCE],
        "checks": {
            "adapter_source_unchanged_since_prior_review": True,
            "resize_crop_geometry_matches_pinned_vmem": True,
            "intrinsics_affine_matches_predictor_arithmetic": True,
            "rgb_normalisation_order_equivalent_to_upstream": True,
            "camera_axis_flip_is_applied_once_by_upstream_get_cond": True,
            "translation_centering_does_not_double_scale": True,
            "depth_scale_invalid_rule_and_z_interpretation": True,
            "pose_homogeneous_row_and_rotation_guarded": True,
            "chronology_only_no_hardware_timestamp_claim": True,
            "role_and_path_allowlist_enforced_by_adapter": True,
            "command_camera_role_is_declared_input_not_outcome": True,
            "modified_predictor_reads_only_staged_manifest_files": True,
            "modified_predictor_access_flags_are_measured_not_constant": True,
            "checkpoint_identity_reverified_in_process_before_torch_load": True,
            "precision_policy_matches_pinned_official_reference": True,
            "run_identity_derived_from_contract_not_script_literals": True,
        },
        "findings": [
            "RUN IDENTITY DERIVATION (this revision). Job 594105 executed the fp32 predictor "
            "successfully and produced a complete prediction, but the seal stage correctly refused "
            "it: the sbatch passed EXECUTION_BOUNDARY_ID as a literal string that still read "
            "s103-scene13-w001-vmem-base-v3-k-and-camera-frame-consistent while the contract "
            "declared the v5 boundary, so seal_predictions_s103.py raised a prediction receipt "
            "boundary mismatch. The predictor itself was not at fault; it reads the value from the "
            "environment. The sbatch now derives both EXECUTION_BOUNDARY_ID and RUN_ID from the "
            "bundled contract.json and aborts if either is missing or contains whitespace, and a "
            "regression assertion now rejects any reintroduced literal. The predictor SHA is "
            "unchanged, so isolation receipt 594089 continues to bind the predictor that will run. "
            "The stale receipt was not edited; the run will be repeated under the corrected "
            "identity.",
            "PRECISION ALIGNMENT (this revision). The predictor previously cast the model to "
            "torch.float16, which diverged from the pinned reference. VMemPipeline.__init__ declares "
            "dtype=torch.float32; app.py constructs VMemPipeline(CONFIG, DEVICE) without overriding it; "
            "and utils/util.py wraps sampling in torch.autocast(device_type=cuda, enabled=True). The "
            "official configuration is therefore fp32 parameters with automatic mixed precision at "
            "sampling time, not manually cast fp16. The divergence surfaced in job 594069, which "
            "reached modeling/pipeline.py:1156 and raised an index-put dtype error because c_replace is "
            "allocated by torch.zeros(...).to(self.device) with no explicit dtype and is therefore fp32 "
            "while the fp16 context latents were Half. The predictor now uses torch.float32, restoring "
            "fidelity to the reference instead of masking the mismatch by casting latents. The contract "
            "budget.dtype was updated accordingly and carries a written basis.",
            "rgbd_scenes_v2.py is byte-identical to the version accepted on 2026-09-16 "
            "(SHA 8be9af8716bb5452963e06e67bcd31704611d13c75b5d7c96e5cdf1bfcdd8d24); this "
            "re-review was forced by the predictor change, not by an adapter change.",
            "preprocessing_geometry() computes factor = max(576/480, 576/640) = 1.2, giving "
            "resized (576, 768) and crop left=96, top=0. This was recomputed independently and "
            "matches pinned VMem transform_img_and_K (utils/util.py:354-405) for the same inputs, "
            "and matches the predictor's hardcoded interpolate((576,768)) plus slice [96:672].",
            "transform_K applies affine [[1.2,0,-96],[0,1.2,0],[0,0,1]], yielding "
            "fx=fy=648.0254784 and cx=cy=288 on the 576x576 grid. The predictor's "
            "k[0]*=1.2; k[1]*=1.2; k[0,2]-=96 produces the identical matrix, and the predictor "
            "additionally asserts equality of all eight K and cx=288 at runtime.",
            "Both adapter preprocess_rgb and the predictor use /255 -> area resize -> crop -> *2-1, "
            "whereas upstream pipeline.py:170 uses /127.5-1.0 before resizing. Area interpolation is "
            "a convex weighted average and x->2x-1 is affine, so the two orders commute exactly up to "
            "float rounding. No divergence.",
            "optical_c2w_to_vmem_input() exists in the adapter but is deliberately NOT applied by the "
            "predictor. This was verified as correct: upstream pipeline.py:1129 performs "
            "all_c2ws[:, :, [1, 2]] *= -1 inside get_cond, so pre-flipping would double-apply the "
            "convention change.",
            "The predictor asserts that get_translation_scaling_factor preserves all pairwise "
            "translations to atol=1e-5 before get_cond runs. This is load-bearing: it establishes that "
            "centering does not scale, so the separate scaling at pipeline.py:1131 is applied once.",
            "load_camera_commands() carries the explicit field "
            "claim='camera-conditioned future-view generation, not prediction of future camera pose' "
            "and outcome_pose_prediction=False. The v10 contract's future_modality_disclosure now "
            "states the same fact in machine-readable form.",
            "The modified predictor still reads only the 13 hashed staged manifest records through the "
            "read() helper, still refuses any path outside PREDICTOR_ROOT, and still contains no mkdir "
            "or symlink creation. New reads are limited to the immutable bundle contract and the four "
            "already-declared checkpoints.",
            "The three access fields in the prediction receipt are now derived from a CPython "
            "sys.addaudithook 'open' event record rather than written as constants; forbidden-root "
            "opens are recorded verbatim. This closes review finding F-1 at the predictor.",
            "Checkpoint SHA-256 for vmem, cut3r, vae and clip are recomputed in-process immediately "
            "before the first torch.load(weights_only=False), closing the cross-job TOCTOU window "
            "described in review finding F-3.",
        ],
        "limitations": [
            "Acceptance is limited to the exact scene13 development adapter SHA and the declared "
            "exposed development window. It does not qualify scene14, any held-out window, any model "
            "forward, any score, or any method claim.",
            "Poses are RGB-D Mapping estimates, not motion-capture ground truth, and frame order is "
            "used only as chronology because the converted source provides no hardware timestamps. "
            "The v10 contract records calibration_status accordingly; no independent calibration was "
            "performed by this project.",
            "This is a static source review. No adapter function was executed against scene data, no "
            "depth or future RGB byte was opened, and no GPU job was run for this review.",
            "The reviewer is an AI session identity distinct from the protocol and adapter author. "
            "This is different-author review, not external independent reproduction, and must never "
            "be recorded as the latter.",
            "The audit-hook measurement observes CPython 'open' events. It does not observe reads "
            "performed by native code that bypasses the CPython file API, so it strengthens but does "
            "not replace the container mount whitelist as the primary enforcement.",
            "Review of seal_predictions_s103.py and scorer_s103.py was limited to the access-semantics "
            "and disclosure paths changed on 2026-09-17; their remaining logic was read but not "
            "exhaustively re-audited in this pass.",
        ],
        "attestation": (
            "Checks above were performed by reading the pinned upstream VMem source and the adapter "
            "source and by recomputing the resize, crop and intrinsics arithmetic. No scientific "
            "result, novelty, or held-out status is asserted. new_method_validated=false; "
            "novelty_authorization=NONE."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing review: {OUT}")
    OUT.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"written": ref(OUT), "reviewer": review["reviewer"],
                      "adapter_sha256": review["adapter_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
