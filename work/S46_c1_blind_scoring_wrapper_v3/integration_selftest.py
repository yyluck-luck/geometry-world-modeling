#!/usr/bin/env python3
"""Source, real-metadata, and synthetic-body tests for the unbound wrapper."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
WRAPPER = HERE / "score_c1_blind_wrapper.py"
TEMPLATE = HERE / "WRAPPER_EXECUTION_BINDING_TEMPLATE.json"
FORMAL_BINDING = HERE / "WRAPPER_EXECUTION_BINDING.json"
FORMAL_OUTPUT = HERE.parents[1] / "work/S46_c1_blind_scoring_preparation/C1_score_attempt_01"
FORMAL_STAGE = FORMAL_OUTPUT.parent / ("." + FORMAL_OUTPUT.name + ".staging")


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_wrapper():
    spec = importlib.util.spec_from_file_location("s46_wrapper_under_test", WRAPPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metadata_suite(module):
    ast.parse(WRAPPER.read_text(encoding="utf-8"))
    ast.parse(Path(__file__).read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    require(template["schema"] == "s46-c1-blind-scoring-wrapper-execution-binding-template-v1" and template["status"] == "UNBOUND_SOURCE_ONLY_TEMPLATE_NOT_EXECUTABLE", "Unbound template header differs")
    require(template["completed_utc"] is None and template["wrapper"]["sha256"] is None, "Template is unexpectedly bound")
    require(all(template[key] == {"path": None, "sha256": None} for key in ("bound_contract", "primary_source_review", "adversarial_source_review", "blindness_attestation", "numeric_guard_independent_review")), "Template placeholders differ")
    require(not FORMAL_BINDING.exists() and not FORMAL_OUTPUT.exists() and not FORMAL_STAGE.exists(), "Formal C1 wrapper path exists before test")
    real = module.validate_current_real_metadata()
    require(len(real["documents"]) == 7 and len(real["identities"]) == 9 and len(real["descriptors"]) == 9, "Real metadata integration count differs")
    require(real["body_bytes_read"] == 0, "Real C1 body bytes were read")
    wrapper_sha = sha(WRAPPER)
    failed = subprocess.run(
        [sys.executable, "-I", "-B", str(WRAPPER), "--binding-sha256", "0" * 64, "--wrapper-sha256", wrapper_sha],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    require(failed.returncode != 0 and not FORMAL_OUTPUT.exists() and not FORMAL_STAGE.exists(), "Unbound formal entry did not fail closed")
    return {
        "real_json_files_read": 7,
        "real_json_bytes_read": real["json_bytes_read"],
        "real_pixel_descriptors_read": 9,
        "real_descriptor_bytes_read": real["descriptor_bytes_read"],
        "real_c1_tensor_body_bytes_read": 0,
        "real_c1_pixels_decoded": 0,
        "real_c1_images_viewed": 0,
        "formal_score_calls": 0,
        "model_generation_or_readback_calls": 0,
        "unbound_formal_entry_rejected": True,
    }


def synthetic_suite(module):
    import numpy as np
    require(np.__version__ == "1.26.4", "Synthetic integration requires NumPy 1.26.4")
    with tempfile.TemporaryDirectory(prefix="s46-c1-wrapper-synthetic-") as raw:
        tensor_dir = (Path(raw) / "tensors").resolve()
        tensor_dir.mkdir()
        identities = []
        for frame_id in range(9):
            value = 255 if frame_id == 8 else frame_id
            frame = np.full(module.SHAPE, value, dtype=np.uint8)
            body = frame.tobytes(order="C")
            body_sha = hashlib.sha256(body).hexdigest()
            descriptor = hashlib.sha256(("synthetic-c1-descriptor-%d" % frame_id).encode()).hexdigest()
            blob = tensor_dir / (descriptor + ".bin")
            blob.write_bytes(body)
            sidecar = {
                "blob": "tensors/" + descriptor + ".bin", "byteorder": "little",
                "bytes_sha256": body_sha, "dtype": "uint8", "kind": "tensor",
                "nbytes": module.NBYTES, "order": "C", "sha256": descriptor,
                "shape": list(module.SHAPE),
            }
            (tensor_dir / (descriptor + ".json")).write_text(json.dumps(sidecar, sort_keys=True), encoding="utf-8")
            identities.append({"id": frame_id, "tensor_descriptor_sha256": descriptor, "tensor_body_sha256": body_sha, "blob": str(blob)})
        metadata = module.validate_pixel_descriptors(identities, tensor_dir, open_bodies=False)
        require(metadata["body_bytes_read"] == 0, "Synthetic metadata-only path opened bodies")
        loaded = module.validate_pixel_descriptors(identities, tensor_dir, open_bodies=True, np=np)
        result = module.load_math_kernel()(loaded["frames"], np)
        require(result["primary"]["mse_float64_hex"] == float(1.0).hex() and result["event_MSE_gt_0_01"] is True, "Frozen kernel synthetic result differs")
        require(result["primary"]["pixels"] == 147456 and result["primary"]["rgb_scalars"] == 442368, "Frozen kernel counts differ")
        return {
            "synthetic_tensor_bodies_read": 9,
            "synthetic_tensor_body_bytes_read": loaded["body_bytes_read"],
            "synthetic_primary_mse_hex": result["primary"]["mse_float64_hex"],
            "strict_event": result["event_MSE_gt_0_01"],
            "frozen_kernel_called": 1,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("metadata-only", "full"), required=True)
    args = parser.parse_args()
    module = load_wrapper()
    metadata = metadata_suite(module)
    synthetic = synthetic_suite(module) if args.mode == "full" else None
    require(not FORMAL_BINDING.exists() and not FORMAL_OUTPUT.exists() and not FORMAL_STAGE.exists(), "A formal path appeared during self-test")
    print(json.dumps({
        "schema": "s46-c1-blind-scoring-wrapper-integration-selftest-v1",
        "status": "PASS_SOURCE_AND_REAL_METADATA_ONLY" if args.mode == "metadata-only" else "PASS_SOURCE_REAL_METADATA_AND_SYNTHETIC_BODY_INTEGRATION_ONLY",
        "mode": args.mode,
        "python": sys.version,
        "wrapper_sha256": sha(WRAPPER),
        "metadata": metadata,
        "synthetic": synthetic,
        "formal_binding_created": False,
        "formal_score_executed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
