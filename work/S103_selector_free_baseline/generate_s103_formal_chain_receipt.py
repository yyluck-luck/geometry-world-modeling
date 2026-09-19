#!/usr/bin/env python3
"""Run CPU-only formal-chain regressions and write a code-bound v2 receipt."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path("/home/yliutz/geometry-world-modeling")
CODE = ROOT / "work/S103_selector_free_baseline"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path: Path) -> dict:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def run_json(command: list[str]) -> dict:
    run = subprocess.run(command, text=True, capture_output=True)
    if run.returncode != 0:
        raise RuntimeError(f"regression failed ({run.returncode}): {' '.join(command)}\n{run.stdout}\n{run.stderr}")
    value = json.loads(run.stdout)
    if value.get("status") != "PASS":
        raise RuntimeError(f"regression did not report PASS: {' '.join(command)}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        raise RuntimeError(f"receipt already exists: {output}")
    tests = {
        "validator_self_test": [sys.executable, os.fspath(ROOT / "work/S102_gate0_tum/validate_gate0_v2.py"),
                                "--self-test"],
        "review_order": [sys.executable, os.fspath(CODE / "test_assemble_s103_reviewed_contract.py")],
        "predictor_static": [sys.executable, os.fspath(CODE / "test_predictor_static_contract.py")],
        "formal_chain": [sys.executable, os.fspath(CODE / "test_s103_formal_chain.py")],
        "scoring": [sys.executable, os.fspath(CODE / "test_s103_scoring.py")],
    }
    results = {name: run_json(command) for name, command in tests.items()}
    component_paths = {
        "bundle_preparer": CODE / "prepare_formal_bundle_s103.py",
        "validator": ROOT / "work/S102_gate0_tum/validate_gate0_v2.py",
        "predictor": CODE / "predictor_s103.py",
        "sealer": CODE / "seal_predictions_s103.py",
        "sbatch": CODE / "run_s103_vmem_base.slurm",
        "launch_guard": ROOT / "work/remote_tmux/launch_gate0_v2_in_tmux.sh",
        "generic_launcher": ROOT / "work/remote_tmux/launch_slurm_in_tmux.sh",
        "scorer": CODE / "scorer_s103.py",
        "verifier": CODE / "verify_s103_scores.py",
    }
    test_paths = {
        "receipt_generator": CODE / "generate_s103_formal_chain_receipt.py",
        "review_order": CODE / "test_assemble_s103_reviewed_contract.py",
        "predictor_static": CODE / "test_predictor_static_contract.py",
        "formal_chain": CODE / "test_s103_formal_chain.py",
        "scoring": CODE / "test_s103_scoring.py",
    }
    receipt = {
        "schema": "s103-formal-chain-software-regression-v2",
        "status": "PASS",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "CPU-only code and synthetic-fixture checks; no GPU, model, research data, or future payload",
        "component_refs": {name: ref(path) for name, path in component_paths.items()},
        "test_source_refs": {name: ref(path) for name, path in test_paths.items()},
        "checks": [{"name": name, "passed": value.get("status") == "PASS",
                    "reported_check_count": len(value.get("checks", []))}
                   for name, value in results.items()],
        "stale_candidate_assertions_present": False,
        "scientific_result": False,
        "future_payload_opened": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=output.parent, prefix=output.name + ".tmp.",
                                     delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    os.replace(temporary, output)
    print(json.dumps({"status": "PASS", "output": ref(output), "checks": receipt["checks"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
