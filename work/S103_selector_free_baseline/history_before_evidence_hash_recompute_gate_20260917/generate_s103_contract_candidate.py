#!/usr/bin/env python3
"""Freeze the review-ready S103 Gate0 candidate without authorizing prediction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/home/yliutz/geometry-world-modeling")
WIN = ROOT / "work/S103_selector_free_baseline/window_scene13_w001_20260916"
CODE = ROOT / "work/S103_selector_free_baseline"
WEIGHTS = Path("/home/yliutz/gwm_weights_20260915")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> None:
    runtime = json.loads((WIN / "RUNTIME_BINDING_v3.json").read_text())
    protocol = {
        "status": "FROZEN",
        "run_id": "S103-VMemBase-scene13-w001-v1",
        "author": "codex-root-20260916",
        "scope": "development_baseline",
        "development_data_exposed": True,
        "effective_config_ref": ref(ROOT / "work/S102_gate0_3dmatch/adapter_v1/sources/vmem_inference.yaml"),
        "expected_config": {
            "model.height": 576,
            "model.width": 576,
            "model.context_num_frames": 4,
            "model.target_num_frames": 4,
            "model.num_frames": 8,
            "model.inference_num_steps": 50,
            "seed": 42,
        },
        "source_manifest_ref": ref(WIN / "SOURCE_MANIFEST_v1.json"),
        "runtime_binding_ref": ref(WIN / "RUNTIME_BINDING_v3.json"),
        "uses_cut3r": True,
        "checkpoints": {name: item for name, item in runtime["checkpoints"].items()
                        if name in {"vmem", "vae", "clip", "cut3r"}},
        "vae_variant": "original_verified",
        "predictor_inputs_ref": ref(WIN / "predictor_inputs.json"),
        "scorer_inputs_ref": ref(WIN / "scorer_inputs.json"),
        "target_camera_policy": "predeclared_command",
        "isolation": {
            "predictor_root": runtime["predictor_root"],
            "execution_boundary_id": runtime["execution_boundary_id"],
            "receipt_ref": ref(WIN / "EXACT_ISOLATION_RECEIPT_v3_591500.json"),
        },
        "datasets": {
            "rgbd-scenes-v2": {
                "camera": {
                    "calibration_status": "verified",
                    "K": [[540.021232, 0.0, 320.0], [0.0, 540.021232, 240.0], [0.0, 0.0, 1.0]],
                    "rgb_depth_registration": "registered",
                    "pixel_center_convention": "0.5 pixel centres; declared development compatibility convention",
                    "resize_crop_K_rule": "640x480 area-resize to 768x576 then centre crop x=[96,672); K left-multiplied by matching affine",
                    "pose_time_association": "same normalized frame id; RGB-D Mapping estimated C2W; no hardware timestamp claim",
                },
                "depth": {
                    "raw_to_metres_divisor": 1000.0,
                    "invalid_values": ["raw uint16 value 0"],
                    "interpretation": "optical_axis_z",
                },
                "adapter_ref": ref(ROOT / "work/S102_gate0_3dmatch/adapter_v1/rgbd_scenes_v2.py"),
                "adapter_author": "codex-root-20260916",
                "adapter_review_ref": None,
            }
        },
        "calibration_scene_ids": ["rgbd-scenes-v2-scene_13"],
        "heldout_exposure_review_ref": None,
        "baseline_acceptance_ref": None,
        "windows": [{
            "dataset_id": "rgbd-scenes-v2",
            "scene_id": "rgbd-scenes-v2-scene_13",
            "sequence_id": "seq-01",
            "history_ids": ["0", "15", "30", "45"],
            "target_ids": ["60", "75", "90", "105"],
            "chronological": True,
        }],
        "budget": {
            "candidate_count": 4,
            "selection_k": 4,
            "output_count": 4,
            "sampling_steps": 50,
            "dtype": "fp16_cuda_model_fp32_saved_outputs",
            "rng_policy": "Python, NumPy, torch CPU and all CUDA seeds fixed to 42 before model construction",
            "timeout_seconds": 3600,
            "metric_definition_ref": ref(CODE / "METRIC_DEFINITION_v1.json"),
        },
        "predictor_wrapper_ref": ref(CODE / "predictor_s103.py"),
        "scorer_ref": ref(CODE / "scorer_s103.py"),
        "verifier_ref": ref(CODE / "verify_s103_scores.py"),
        "validator_ref": ref(ROOT / "work/S102_gate0_tum/validate_gate0_v2.py"),
        "claim_boundary": "one exposed development baseline window; no held-out, comparison, method, geometry, or novelty claim",
    }
    contract = {
        "schema": "gwm-gate0-staged-v2",
        "protocol": protocol,
        "review_ref": None,
        "post_run": {},
    }
    target = WIN / "GATE0_CONTRACT_CANDIDATE_v7.json"
    target.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"contract": ref(target), "status": "FROZEN_PENDING_DIFFERENT_AUTHOR_REVIEW"}, indent=2))


if __name__ == "__main__":
    main()
