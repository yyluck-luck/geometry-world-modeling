#!/usr/bin/env python3
"""Create the immutable formal S103 bundle only after real PRE_RUN_READY."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def resolve_ref(ref: dict, base: Path, label: str) -> Path:
    require(isinstance(ref, dict), f"{label}: descriptor missing")
    path = Path(ref.get("path", ""))
    path = (path if path.is_absolute() else base / path).resolve()
    require(path.is_file(), f"{label}: file missing")
    require(path.stat().st_size == ref.get("bytes"), f"{label}: byte count mismatch")
    require(sha(path) == ref.get("sha256"), f"{label}: SHA mismatch")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--validator", required=True)
    parser.add_argument("--predictor", required=True)
    parser.add_argument("--sealer", required=True)
    parser.add_argument("--sbatch", required=True)
    parser.add_argument("--launch-guard", required=True)
    parser.add_argument("--generic-launcher", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    paths = {key: Path(getattr(args, key)).resolve()
             for key in ("contract", "validator", "predictor", "sealer", "sbatch",
                         "launch_guard", "generic_launcher")}
    if not all(path.is_file() for path in paths.values()):
        raise RuntimeError("all input artifacts must be existing files")
    contract = json.loads(paths["contract"].read_text())
    require(contract.get("schema") == "gwm-gate0-staged-v2", "wrong contract schema")
    protocol = contract.get("protocol", {})
    require(protocol.get("status") == "FROZEN", "protocol is not frozen")
    require(isinstance(contract.get("review_ref"), dict), "final protocol review is not bound")
    formal = protocol.get("formal_execution", {})
    require(isinstance(formal, dict), "formal_execution missing")
    base = paths["contract"].parent
    bound = {
        "preparer": resolve_ref(formal.get("bundle_preparer_ref"), base, "bundle preparer"),
        "validator": resolve_ref(formal.get("validator_ref"), base, "validator"),
        "predictor": resolve_ref(formal.get("predictor_ref"), base, "predictor"),
        "sealer": resolve_ref(formal.get("sealer_ref"), base, "sealer"),
        "sbatch": resolve_ref(formal.get("sbatch_ref"), base, "sbatch"),
        "launch_guard": resolve_ref(formal.get("launch_guard_ref"), base, "launch guard"),
        "generic_launcher": resolve_ref(formal.get("generic_launcher_ref"), base, "generic launcher"),
        "regression_receipt": resolve_ref(formal.get("formal_chain_regression_receipt_ref"), base,
                                          "formal-chain regression receipt"),
    }
    require(bound["preparer"] == Path(__file__).resolve(), "contract binds a different bundle preparer")
    for key in ("validator", "predictor", "sealer", "sbatch", "launch_guard", "generic_launcher"):
        require(paths[key] == bound[key], f"caller-selected {key} differs from reviewed protocol")
    require(formal.get("validator_ref") == protocol.get("validator_ref"),
            "formal/top-level validator refs differ")
    require(formal.get("predictor_ref") == protocol.get("predictor_wrapper_ref"),
            "formal/top-level predictor refs differ")
    target = Path(args.target).resolve()
    require(target == Path(formal.get("bundle_root", "")).resolve(),
            "target differs from reviewed formal bundle root")
    require(not target.exists(), f"target already exists: {target}")

    check = subprocess.run([sys.executable, os.fspath(paths["validator"]), os.fspath(paths["contract"]),
                            "--stage", "pre-run"], text=True, capture_output=True)
    try:
        receipt = json.loads(check.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"validator did not emit JSON: {exc}") from exc
    if check.returncode != 0 or receipt.get("schema") != "gwm-gate0-staged-v2" or \
            receipt.get("stage") != "pre-run" or receipt.get("status") != "PRE_RUN_READY" or \
            receipt.get("pre_run_ready") is not True or receipt.get("errors") != [] or \
            receipt.get("opens_future_outcome_files") is not False:
        raise RuntimeError("formal bundle refused: validator is not zero-error PRE_RUN_READY")

    protocol_sha = canonical_sha(protocol)
    if receipt.get("protocol_sha256") != protocol_sha:
        raise RuntimeError("validator protocol SHA mismatch")
    require(receipt.get("run_id") == protocol.get("run_id") and
            receipt.get("scope") == protocol.get("scope"), "validator identity mismatch")
    boundary = (protocol.get("isolation") or {}).get("execution_boundary_id")
    dispatch = {
        "schema": "gwm-gate0-v2-dispatch-manifest-v1",
        "status": "FROZEN",
        "stage": "pre-run",
        "run_id": protocol["run_id"],
        "scope": protocol["scope"],
        "protocol_sha256": protocol_sha,
        "contract_sha256": sha(paths["contract"]),
        "bundle_root": str(target),
        "sbatch_script_sha256": sha(paths["sbatch"]),
        "validator_sha256": sha(paths["validator"]),
        "predictor_wrapper_sha256": sha(paths["predictor"]),
        "prediction_sealer_sha256": sha(paths["sealer"]),
        "formal_bundle_preparer_sha256": sha(Path(__file__).resolve()),
        "launch_guard_sha256": sha(paths["launch_guard"]),
        "generic_launcher_sha256": sha(paths["generic_launcher"]),
        "formal_chain_regression_receipt_sha256": sha(bound["regression_receipt"]),
        "runtime_binding_sha256": (protocol.get("runtime_binding_ref") or {}).get("sha256"),
        "isolation_receipt_sha256": ((protocol.get("isolation") or {}).get("receipt_ref") or {}).get("sha256"),
        "validator_receipt_sha256": canonical_sha(receipt),
        "execution_boundary_id": boundary,
        "validator_receipt": receipt,
        "future_outcome_access": False,
        "scorer_in_bundle": False,
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=target.name + ".tmp.", dir=target.parent))
    try:
        shutil.copy2(paths["contract"], temp / "contract.json")
        shutil.copy2(paths["predictor"], temp / "predictor_s103.py")
        shutil.copy2(paths["sealer"], temp / "seal_predictions_s103.py")
        shutil.copy2(paths["sbatch"], temp / "run_s103_vmem_base.slurm")
        shutil.copy2(paths["validator"], temp / "validate_gate0_v2.py")
        (temp / "dispatch_manifest.json").write_text(json.dumps(dispatch, indent=2, sort_keys=True) + "\n")
        expected_copies = {"contract.json": sha(paths["contract"]),
                           "predictor_s103.py": sha(paths["predictor"]),
                           "seal_predictions_s103.py": sha(paths["sealer"]),
                           "run_s103_vmem_base.slurm": sha(paths["sbatch"]),
                           "validate_gate0_v2.py": sha(paths["validator"])}
        for name, expected_sha in expected_copies.items():
            require(sha(temp / name) == expected_sha, f"copied artifact changed: {name}")
        for path in temp.iterdir():
            path.chmod(0o550 if path.suffix in {".py", ".slurm"} else 0o440)
        temp.chmod(0o550)
        os.replace(temp, target)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    print(json.dumps({"status": "FORMAL_BUNDLE_FROZEN", "target": str(target),
                      "dispatch_manifest_sha256": sha(target / "dispatch_manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
