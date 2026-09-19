#!/usr/bin/env python3
"""Seal S103 predictor outputs before any future outcome is made visible."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import numpy as np


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def descriptor(container_path: Path, host_root: Path) -> dict:
    resolved = container_path.resolve()
    root = container_path.parent.resolve()
    require(resolved.is_relative_to(root), "output path escapes output root")
    host_path = host_root / container_path.name
    return {"path": str(host_path), "bytes": resolved.stat().st_size, "sha256": sha(resolved)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--host-output-dir", required=True)
    parser.add_argument("--predictor-exit-code", required=True, type=int)
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    output = Path(args.output_dir).resolve()
    host_output = Path(args.host_output_dir)
    require(bundle.is_dir() and output.is_dir(), "bundle/output directory missing")
    manifest_path = bundle / "dispatch_manifest.json"
    contract_path = bundle / "contract.json"
    predictor_path = bundle / "predictor_s103.py"
    validator_path = bundle / "validate_gate0_v2.py"
    sbatch_path = bundle / "run_s103_vmem_base.slurm"
    manifest = json.loads(manifest_path.read_text())
    contract = json.loads(contract_path.read_text())
    protocol = contract.get("protocol", {})
    formal = protocol.get("formal_execution", {})
    require(contract.get("schema") == "gwm-gate0-staged-v2" and protocol.get("status") == "FROZEN",
            "contract schema/status invalid")
    require(manifest.get("schema") == "gwm-gate0-v2-dispatch-manifest-v1", "wrong dispatch manifest")
    require(manifest.get("status") == "FROZEN", "dispatch manifest not frozen")
    require(manifest.get("stage") == "pre-run", "dispatch manifest stage mismatch")
    require(sha(contract_path) == manifest.get("contract_sha256"), "contract SHA mismatch")
    require(canonical_sha(protocol) == manifest.get("protocol_sha256"), "protocol SHA mismatch")
    require(sha(predictor_path) == manifest.get("predictor_wrapper_sha256"), "predictor SHA mismatch")
    require(sha(Path(__file__).resolve()) == manifest.get("prediction_sealer_sha256") ==
            (formal.get("sealer_ref") or {}).get("sha256"), "sealer identity mismatch")
    require(sha(validator_path) == manifest.get("validator_sha256") ==
            (formal.get("validator_ref") or {}).get("sha256"), "validator identity mismatch")
    require(sha(sbatch_path) == manifest.get("sbatch_script_sha256") ==
            (formal.get("sbatch_ref") or {}).get("sha256"), "sbatch identity mismatch")
    require(manifest.get("formal_bundle_preparer_sha256") ==
            (formal.get("bundle_preparer_ref") or {}).get("sha256"), "preparer identity mismatch")
    require(manifest.get("launch_guard_sha256") ==
            (formal.get("launch_guard_ref") or {}).get("sha256"), "launch guard identity mismatch")
    require(manifest.get("generic_launcher_sha256") ==
            (formal.get("generic_launcher_ref") or {}).get("sha256"), "generic launcher identity mismatch")
    require(manifest.get("formal_chain_regression_receipt_sha256") ==
            (formal.get("formal_chain_regression_receipt_ref") or {}).get("sha256"),
            "formal-chain regression receipt mismatch")
    require(manifest.get("runtime_binding_sha256") ==
            (protocol.get("runtime_binding_ref") or {}).get("sha256"), "runtime binding mismatch")
    require(manifest.get("isolation_receipt_sha256") ==
            (((protocol.get("isolation") or {}).get("receipt_ref") or {}).get("sha256")),
            "isolation receipt mismatch")
    require(protocol.get("run_id") == manifest.get("run_id"), "run_id mismatch")
    require((protocol.get("isolation") or {}).get("execution_boundary_id") ==
            manifest.get("execution_boundary_id"), "execution boundary mismatch")

    receipt_path = output / "PREDICTION_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
    files = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "PREDICTION_SEAL.json":
            files.append(descriptor(path, host_output))

    success = args.predictor_exit_code == 0
    if success:
        require(receipt.get("schema") == "s103-vmem-development-prediction-v1",
                "success receipt schema mismatch")
        require(receipt.get("status") == "PREDICTION_COMPLETE", "success lacks completion receipt")
        require(receipt.get("run_id") == protocol.get("run_id"), "prediction receipt run_id mismatch")
        require(receipt.get("execution_boundary_id") == manifest.get("execution_boundary_id"),
                "prediction receipt boundary mismatch")
        require(receipt.get("future_outcome_files_opened") is False and
                receipt.get("future_gt_opened") is False and
                receipt.get("unauthorized_input_reads") == 0,
                "predictor reported forbidden input access")
        expected = {row["path"]: row for row in receipt.get("output_files", [])}
        for name in ("predicted_target_rgb_fp32.npy", "all8_latents_fp32.npy"):
            path = output / name
            require(path.is_file(), f"required prediction output missing: {name}")
            item = expected.get(str(path)) or expected.get(str(host_output / name))
            require(isinstance(item, dict), f"prediction receipt does not bind: {name}")
            require(item.get("bytes") == path.stat().st_size and item.get("sha256") == sha(path),
                    f"prediction receipt identity mismatch: {name}")
        rgb = np.load(output / "predicted_target_rgb_fp32.npy", mmap_mode="r", allow_pickle=False)
        latents = np.load(output / "all8_latents_fp32.npy", mmap_mode="r", allow_pickle=False)
        require(rgb.shape == (4, 3, 576, 576) and rgb.dtype == np.float32,
                "predicted RGB shape/dtype mismatch")
        require(latents.dtype == np.float32 and latents.ndim >= 2,
                "latent output dtype/rank mismatch")
        require(np.isfinite(rgb).all() and np.isfinite(latents).all(), "non-finite prediction output")
        names = {path.name for path in output.iterdir() if path.is_file()}
        require(names == {"PREDICTION_RECEIPT.json", "predicted_target_rgb_fp32.npy",
                          "all8_latents_fp32.npy"}, "unexpected prediction output file")

    seal = {
        "schema": "s103-prediction-seal-v1",
        "status": "PREDICTION_SEALED" if success else "FAILED_PREDICTION_ATTEMPT_SEALED",
        "sealed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_id": protocol.get("run_id"),
        "protocol_sha256": manifest.get("protocol_sha256"),
        "contract_sha256": manifest.get("contract_sha256"),
        "dispatch_manifest_sha256": sha(manifest_path),
        "predictor_wrapper_sha256": manifest.get("predictor_wrapper_sha256"),
        "prediction_sealer_sha256": manifest.get("prediction_sealer_sha256"),
        "validator_sha256": manifest.get("validator_sha256"),
        "sbatch_script_sha256": manifest.get("sbatch_script_sha256"),
        "predictor_receipt_sha256": sha(receipt_path) if receipt_path.is_file() else None,
        "predictor_completed_at_utc": receipt.get("completed_utc"),
        "execution_boundary_id": manifest.get("execution_boundary_id"),
        "predictor_exit_code": args.predictor_exit_code,
        "unauthorized_input_reads": receipt.get("unauthorized_input_reads", None),
        "future_outcome_files_opened": receipt.get("future_outcome_files_opened", None),
        "future_gt_opened": receipt.get("future_gt_opened", None),
        "files": files,
        "prediction_complete": success,
        "future_scoring_permitted": success,
        "scientific_result": False,
        "new_method_validated": False,
        "novelty_authorization": "NONE",
    }
    target = output / "PREDICTION_SEAL.json"
    require(not target.exists(), "prediction seal already exists")
    temporary = output / f".PREDICTION_SEAL.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, target)
    print(json.dumps({"status": seal["status"], "seal_sha256": sha(target),
                      "future_scoring_permitted": seal["future_scoring_permitted"]}, indent=2))
    return 0 if success else args.predictor_exit_code or 1


if __name__ == "__main__":
    raise SystemExit(main())
