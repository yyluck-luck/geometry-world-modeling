#!/usr/bin/env python3
"""Exact allowlist/isolation probe for S103; never loads the model or outcome bytes."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import socket
import sys
from pathlib import Path


BUNDLE = Path("/opt/gwm-boundary")
OUT = Path("/mnt/receipt")
PROJECT = Path("/home/yliutz/geometry-world-modeling")
DATASET = Path("/home/yliutz/datasets/heldout_3dmatch_scene13")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_ref(item: dict) -> dict:
    path = Path(item["path"])
    actual_size = path.stat().st_size
    actual_sha = sha(path)
    if actual_size != item["bytes"] or actual_sha != item["sha256"]:
        raise RuntimeError(f"identity mismatch: {path}")
    return {"path": str(path), "bytes": actual_size, "sha256": actual_sha}


def main() -> None:
    runtime_path = BUNDLE / "RUNTIME_BINDING_v2.json"
    source_path = BUNDLE / "SOURCE_MANIFEST_v1.json"
    predictor_path = BUNDLE / "predictor_s103.py"
    scorer_path = BUNDLE / "scorer_inputs.json"
    runtime = json.loads(runtime_path.read_text())
    source = json.loads(source_path.read_text())
    predictor_manifest = json.loads((Path(runtime["predictor_root"]) / "predictor_inputs.json").read_text())
    scorer_manifest = json.loads(scorer_path.read_text())

    if sha(source_path) != runtime["source_manifest_sha256"]:
        raise RuntimeError("source manifest bundle does not match runtime binding")
    if sha(predictor_path) != runtime["predictor_wrapper_sha256"]:
        raise RuntimeError("predictor wrapper bundle does not match runtime binding")
    if sha(scorer_path) != runtime["scorer_inputs"]["sha256"]:
        raise RuntimeError("scorer manifest bundle does not match runtime binding")
    if sha(Path(runtime["predictor_root"]) / "predictor_inputs.json") != runtime["predictor_inputs"]["sha256"]:
        raise RuntimeError("predictor manifest does not match runtime binding")

    role_counts: dict[str, int] = {}
    verified_inputs = []
    stage = Path(runtime["predictor_root"]).resolve()
    for row in predictor_manifest["records"]:
        role_counts[row["role"]] = role_counts.get(row["role"], 0) + 1
        resolved = Path(row["file"]["path"]).resolve()
        if not resolved.is_relative_to(stage):
            raise RuntimeError(f"predictor path escapes stage: {resolved}")
        verified_inputs.append(verify_ref(row["file"]))
    expected_roles = {"history_rgb": 4, "history_pose": 4, "command_camera": 4, "camera_intrinsics": 1}
    if role_counts != expected_roles:
        raise RuntimeError(f"wrong role counts: {role_counts}")

    verified_sources = [verify_ref(item) for item in source["files"]]
    verified_checkpoints = {name: verify_ref(item) for name, item in runtime["checkpoints"].items()}

    outcome_paths = [Path(row["file"]["path"]) for row in scorer_manifest["records"]]
    outcome_visibility = {str(path): path.exists() for path in outcome_paths}
    if any(outcome_visibility.values()) or DATASET.exists() or PROJECT.exists():
        raise RuntimeError("unbound project or future outcome path is visible")

    write_checks = {}
    for name, base in {
        "stage": stage,
        "source": Path(source["source_root"]),
        "weights": Path(runtime["checkpoints"]["vmem"]["path"]).parent,
        "receipt": OUT,
    }.items():
        candidate = base / ".s103_write_probe"
        try:
            candidate.write_text("probe")
            write_checks[name] = True
            candidate.unlink(missing_ok=True)
        except OSError as exc:
            write_checks[name] = f"{type(exc).__name__}: {exc}"
    if write_checks["stage"] is True or write_checks["source"] is True or write_checks["weights"] is True:
        raise RuntimeError(f"read-only mount writable: {write_checks}")
    if write_checks["receipt"] is not True:
        raise RuntimeError("receipt output is not writable")

    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    left = torch.randn(512, 512, device="cuda")
    right = torch.randn(512, 512, device="cuda")
    product = left @ right
    if not bool(torch.isfinite(product).all().item()):
        raise RuntimeError("CUDA matmul non-finite")

    receipt = {
        "schema": "gwm-s103-exact-isolation-receipt-v1",
        "status": "EXACT_BOUNDARY_PROBE_PASS",
        "method": "container_mount_whitelist",
        "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "slurm_job_id": os.environ.get("GWM_BOUNDARY_JOB_ID"),
        "execution_boundary_id": runtime["execution_boundary_id"],
        "predictor_root": runtime["predictor_root"],
        "predictor_inputs_sha256": runtime["predictor_inputs"]["sha256"],
        "runtime_binding_sha256": sha(runtime_path),
        "scorer_inputs_sha256": runtime["scorer_inputs"]["sha256"],
        "predictor_wrapper_sha256": runtime["predictor_wrapper_sha256"],
        "source_manifest_sha256": runtime["source_manifest_sha256"],
        "allowed_history_probe_passed": True,
        "denied_outcome_probe_passed": True,
        "full_archive_unavailable": True,
        "project_root_visible": False,
        "dataset_root_visible": False,
        "all_declared_outcome_paths_invisible": True,
        "predictor_role_counts": role_counts,
        "verified_predictor_records": len(verified_inputs),
        "verified_source_files": len(verified_sources),
        "verified_checkpoints": verified_checkpoints,
        "mount_write_checks": write_checks,
        "cuda": {"available": True, "torch": torch.__version__, "device": torch.cuda.get_device_name(0),
                 "matmul_shape": list(product.shape), "finite": True},
        "model_loaded": False,
        "model_forward": False,
        "future_outcome_bytes_opened": False,
        "future_ground_truth_opened": False,
        "formal_prediction_authorized": False,
        "scientific_result": False,
        "claim_boundary": "exact technical isolation binding only; independent pre-run review remains required",
    }
    target = OUT / "EXACT_ISOLATION_RECEIPT.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "EXACT_BOUNDARY_PROBE_FAIL", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        raise
