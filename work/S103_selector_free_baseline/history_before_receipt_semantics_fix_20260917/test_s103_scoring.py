#!/usr/bin/env python3
"""Synthetic regression for the S103 scorer/verifier; reads no research data."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
SCORER = ROOT / "scorer_s103.py"
VERIFIER = ROOT / "verify_s103_scores.py"
METRIC = ROOT / "METRIC_DEFINITION_v1.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="s103-score-test-") as temp:
        root = Path(temp)
        records = []
        for frame in range(4, 8):
            yy, xx = np.mgrid[:480, :640]
            image = np.stack(((xx + frame) % 256, (yy * 2 + frame) % 256,
                              (xx + yy + frame * 3) % 256), axis=-1).astype(np.uint8)
            path = root / f"frame-{frame:06d}.color.png"
            Image.fromarray(image).save(path)
            records.append({"dataset_id": "synthetic", "scene_id": "fixture",
                            "sequence_id": "seq-01", "frame_id": str(frame),
                            "role": "future_rgb", "file": ref(path)})
        manifest_path = root / "scorer_inputs.json"
        write(manifest_path, {"records": records})

        protocol = {
            "status": "FROZEN", "run_id": "S103_SYNTHETIC_TEST", "author": "test-author",
            "scorer_ref": ref(SCORER), "scorer_inputs_ref": ref(manifest_path),
            "scope": "development_baseline",
            "runtime_binding_ref": {"sha256": "1" * 64},
            "isolation": {"execution_boundary_id": "synthetic-boundary-v1",
                          "receipt_ref": {"sha256": "2" * 64}},
            "windows": [{"dataset_id": "synthetic", "scene_id": "fixture",
                         "sequence_id": "seq-01", "history_ids": ["0", "1", "2", "3"],
                         "target_ids": ["4", "5", "6", "7"], "chronological": True}],
            "budget": {"metric_definition_ref": ref(METRIC)}
        }
        component_shas = {
            "validator_sha256": "3" * 64, "predictor_wrapper_sha256": "4" * 64,
            "prediction_sealer_sha256": "5" * 64, "sbatch_script_sha256": "6" * 64,
            "formal_bundle_preparer_sha256": "7" * 64, "launch_guard_sha256": "8" * 64,
            "generic_launcher_sha256": "9" * 64,
            "formal_chain_regression_receipt_sha256": "a" * 64,
        }
        protocol["formal_execution"] = {
            "validator_ref": {"sha256": component_shas["validator_sha256"]},
            "predictor_ref": {"sha256": component_shas["predictor_wrapper_sha256"]},
            "sealer_ref": {"sha256": component_shas["prediction_sealer_sha256"]},
            "sbatch_ref": {"sha256": component_shas["sbatch_script_sha256"]},
            "bundle_preparer_ref": {"sha256": component_shas["formal_bundle_preparer_sha256"]},
            "launch_guard_ref": {"sha256": component_shas["launch_guard_sha256"]},
            "generic_launcher_ref": {"sha256": component_shas["generic_launcher_sha256"]},
            "formal_chain_regression_receipt_ref": {
                "sha256": component_shas["formal_chain_regression_receipt_sha256"]},
        }
        contract_path = root / "contract.json"
        write(contract_path, {"schema": "gwm-gate0-staged-v2", "protocol": protocol})

        dispatch = {"schema": "gwm-gate0-v2-dispatch-manifest-v1", "status": "FROZEN",
                    "stage": "pre-run", "run_id": protocol["run_id"], "scope": protocol["scope"],
                    "contract_sha256": sha(contract_path), "protocol_sha256": canonical(protocol),
                    "runtime_binding_sha256": "1" * 64, "isolation_receipt_sha256": "2" * 64,
                    "execution_boundary_id": "synthetic-boundary-v1", **component_shas}
        dispatch_path = root / "dispatch_manifest.json"
        write(dispatch_path, dispatch)
        launch_time = datetime.now(timezone.utc) - timedelta(seconds=3)
        completed_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        guard = {"schema": "gwm-formal-launch-guard-receipt-v1", "status": "PASS",
                 "recorded_at_utc": launch_time.isoformat(), "manifest_sha256": sha(dispatch_path),
                 "contract_sha256": sha(contract_path), "protocol_sha256": canonical(protocol),
                 "run_id": protocol["run_id"], "scope": protocol["scope"],
                 "execution_boundary_id": "synthetic-boundary-v1", **component_shas}
        guard_path = root / "launch_guard.json"
        write(guard_path, guard)

        prediction = np.linspace(-1.0, 1.0, 4 * 3 * 576 * 576, dtype=np.float32).reshape(4, 3, 576, 576)
        prediction_path = root / "predicted_target_rgb_fp32.npy"
        np.save(prediction_path, prediction, allow_pickle=False)
        seal = {
            "schema": "s103-prediction-seal-v1", "status": "PREDICTION_SEALED",
            "run_id": protocol["run_id"], "protocol_sha256": canonical(protocol),
            "contract_sha256": sha(contract_path), "dispatch_manifest_sha256": sha(dispatch_path),
            "predictor_wrapper_sha256": component_shas["predictor_wrapper_sha256"],
            "prediction_sealer_sha256": component_shas["prediction_sealer_sha256"],
            "validator_sha256": component_shas["validator_sha256"],
            "sbatch_script_sha256": component_shas["sbatch_script_sha256"],
            "execution_boundary_id": "synthetic-boundary-v1", "prediction_complete": True,
            "future_scoring_permitted": True, "future_outcome_files_opened": False,
            "future_gt_opened": False, "predictor_exit_code": 0, "unauthorized_input_reads": 0,
            "predictor_completed_at_utc": completed_time.isoformat(),
            "sealed_at_utc": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
            "files": [ref(prediction_path)]
        }
        seal_path = root / "seal.json"
        write(seal_path, seal)

        score_dir = root / "score"
        scored = subprocess.run([sys.executable, str(SCORER), "--contract", str(contract_path),
                                 "--prediction-seal", str(seal_path),
                                 "--prediction-seal-sha256", sha(seal_path),
                                 "--dispatch-manifest", str(dispatch_path),
                                 "--dispatch-manifest-sha256", sha(dispatch_path),
                                 "--launch-guard-receipt", str(guard_path),
                                 "--launch-guard-receipt-sha256", sha(guard_path),
                                 "--output-dir", str(score_dir)], capture_output=True, text=True)
        checks.append(["valid sealed fixture scores", scored.returncode == 0])
        receipt_path = score_dir / "SCORING_RECEIPT.json"
        verified_path = root / "verification.json"
        verified = subprocess.run([sys.executable, str(VERIFIER), "--contract", str(contract_path),
                                   "--prediction-seal", str(seal_path),
                                   "--scoring-receipt", str(receipt_path),
                                   "--scoring-receipt-sha256", sha(receipt_path),
                                   "--reviewer", "synthetic-independent-reviewer",
                                   "--output", str(verified_path)], capture_output=True, text=True)
        checks.append(["independent recomputation matches", verified.returncode == 0])
        if verified_path.exists():
            checks.append(["full fixed denominator",
                           json.loads(verified_path.read_text())["recomputed_full_frame_count"]
                           == 4 * 576 * 576 * 3])
        else:
            checks.append(["full fixed denominator", False])

        rejected = dict(seal)
        rejected["unauthorized_input_reads"] = 1
        rejected_path = root / "rejected_seal.json"
        write(rejected_path, rejected)
        blocked = subprocess.run([sys.executable, str(SCORER), "--contract", str(contract_path),
                                  "--prediction-seal", str(rejected_path),
                                  "--prediction-seal-sha256", sha(rejected_path),
                                  "--dispatch-manifest", str(dispatch_path),
                                  "--dispatch-manifest-sha256", sha(dispatch_path),
                                  "--launch-guard-receipt", str(guard_path),
                                  "--launch-guard-receipt-sha256", sha(guard_path),
                                  "--output-dir", str(root / "must_not_exist")],
                                 capture_output=True, text=True)
        checks.append(["unauthorized-read seal rejected", blocked.returncode != 0])

        forged = {"run_id": protocol["run_id"], "protocol_sha256": canonical(protocol),
                  "predictor_exit_code": 0, "unauthorized_input_reads": 0,
                  "sealed_at_utc": datetime.now(timezone.utc).isoformat(), "files": [ref(prediction_path)]}
        forged_path = root / "forged_seal.json"
        write(forged_path, forged)
        forged_run = subprocess.run([sys.executable, str(SCORER), "--contract", str(contract_path),
                                     "--prediction-seal", str(forged_path),
                                     "--prediction-seal-sha256", sha(forged_path),
                                     "--dispatch-manifest", str(dispatch_path),
                                     "--dispatch-manifest-sha256", sha(dispatch_path),
                                     "--launch-guard-receipt", str(guard_path),
                                     "--launch-guard-receipt-sha256", sha(guard_path),
                                     "--output-dir", str(root / "forged_must_not_exist")],
                                    capture_output=True, text=True)
        checks.append(["fabricated legacy seal rejected", forged_run.returncode != 0])

        result = {"schema": "s103-scoring-synthetic-regression-v1",
                  "scope": "synthetic fixtures only; no model/data/GT/GPU",
                  "checks": checks,
                  "status": "PASS" if all(row[1] for row in checks) else "FAIL",
                  "scorer_failure_if_any": scored.stderr[-2000:],
                  "verifier_failure_if_any": verified.stderr[-2000:]}
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
