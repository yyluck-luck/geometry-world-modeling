#!/usr/bin/env python3
"""Synthetic formal-chain regression; no GPU, model, research data, or future payload."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np


HERE = Path(__file__).resolve().parent
SEALER = HERE / "seal_predictions_s103.py"
SBATCH = HERE / "run_s103_vmem_base.slurm"
PREPARER = HERE / "prepare_formal_bundle_s103.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path: Path) -> dict:
    path = path.resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def canonical(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def fixture(root: Path, *, future_opened=False):
    root.mkdir(parents=True)
    bundle, output, host = root / "bundle", root / "output", root / "host-output"
    bundle.mkdir(); output.mkdir(); host.mkdir()
    predictor = bundle / "predictor_s103.py"; predictor.write_text("# synthetic predictor identity only\n")
    validator = bundle / "validate_gate0_v2.py"; validator.write_text("# synthetic validator identity only\n")
    shutil.copy2(SBATCH, bundle / "run_s103_vmem_base.slurm")
    launch = root / "launch_guard.sh"; launch.write_text("#!/bin/sh\n")
    generic = root / "generic_launcher.sh"; generic.write_text("#!/bin/sh\n")
    regression = root / "regression.json"; write(regression, {"status": "PASS"})
    formal = {
        "bundle_root": str(bundle), "bundle_preparer_ref": ref(PREPARER),
        "validator_ref": ref(validator), "predictor_ref": ref(predictor),
        "sealer_ref": ref(SEALER), "sbatch_ref": ref(SBATCH),
        "launch_guard_ref": ref(launch), "generic_launcher_ref": ref(generic),
        "formal_chain_regression_receipt_ref": ref(regression),
    }
    protocol = {"status": "FROZEN", "run_id": "S103-VMemBase-scene13-w001-v1",
                "scope": "development_baseline", "formal_execution": formal,
                "predictor_wrapper_ref": formal["predictor_ref"],
                "validator_ref": formal["validator_ref"],
                "runtime_binding_ref": {"sha256": "1" * 64},
                "isolation": {"execution_boundary_id": "s103-boundary-v3",
                              "receipt_ref": {"sha256": "2" * 64}}}
    contract = bundle / "contract.json"
    write(contract, {"schema": "gwm-gate0-staged-v2", "protocol": protocol})
    manifest = {"schema": "gwm-gate0-v2-dispatch-manifest-v1", "status": "FROZEN", "stage": "pre-run",
                "run_id": protocol["run_id"], "scope": protocol["scope"], "bundle_root": str(bundle),
                "contract_sha256": sha(contract), "protocol_sha256": canonical(protocol),
                "predictor_wrapper_sha256": sha(predictor), "prediction_sealer_sha256": sha(SEALER),
                "validator_sha256": sha(validator), "sbatch_script_sha256": sha(SBATCH),
                "formal_bundle_preparer_sha256": sha(PREPARER), "launch_guard_sha256": sha(launch),
                "generic_launcher_sha256": sha(generic),
                "formal_chain_regression_receipt_sha256": sha(regression),
                "runtime_binding_sha256": "1" * 64, "isolation_receipt_sha256": "2" * 64,
                "execution_boundary_id": "s103-boundary-v3"}
    write(bundle / "dispatch_manifest.json", manifest)
    rgb, lat = output / "predicted_target_rgb_fp32.npy", output / "all8_latents_fp32.npy"
    np.save(rgb, np.zeros((4, 3, 576, 576), dtype=np.float32), allow_pickle=False)
    np.save(lat, np.zeros((8, 4, 8, 8), dtype=np.float32), allow_pickle=False)
    receipt = {"schema": "s103-vmem-development-prediction-v1", "status": "PREDICTION_COMPLETE",
               "run_id": protocol["run_id"], "execution_boundary_id": manifest["execution_boundary_id"],
               "future_outcome_files_opened": future_opened, "future_gt_opened": False,
               "unauthorized_input_reads": 0, "completed_utc": datetime.now(timezone.utc).isoformat(),
               "output_files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}
                                for path in (rgb, lat)]}
    write(output / "PREDICTION_RECEIPT.json", receipt)
    return bundle, output, host


def run_seal(bundle, output, host, code=0):
    return subprocess.run([sys.executable, os.fspath(SEALER), "--bundle", os.fspath(bundle),
                           "--output-dir", os.fspath(output), "--host-output-dir", os.fspath(host),
                           "--predictor-exit-code", str(code)], text=True, capture_output=True)


def preparer_fixture(root: Path, ready: bool, wrong_validator: bool = False):
    root.mkdir(parents=True)
    predictor = root / "predictor_s103.py"; predictor.write_text("# synthetic predictor identity only\n")
    launch = root / "launch_guard.sh"; launch.write_text("#!/bin/sh\n")
    generic = root / "generic_launcher.sh"; generic.write_text("#!/bin/sh\n")
    regression = root / "regression.json"; write(regression, {"status": "PASS"})
    validator = root / "validator.py"
    validator.write_text("""#!/usr/bin/env python3
import hashlib,json,sys
c=json.load(open(sys.argv[1])); p=c['protocol']
h=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
ready=%s
print(json.dumps({'schema':'gwm-gate0-staged-v2','stage':'pre-run','status':'PRE_RUN_READY' if ready else 'BLOCKED','pre_run_ready':ready,'errors':[] if ready else ['blocked'],'opens_future_outcome_files':False,'protocol_sha256':h,'run_id':p['run_id'],'scope':p['scope']}))
raise SystemExit(0 if ready else 2)
""" % ("True" if ready else "False"))
    validator.chmod(0o750)
    target = root / "formal_bundle"
    formal = {"bundle_root": str(target), "bundle_preparer_ref": ref(PREPARER),
              "validator_ref": ref(validator), "predictor_ref": ref(predictor),
              "sealer_ref": ref(SEALER), "sbatch_ref": ref(SBATCH),
              "launch_guard_ref": ref(launch), "generic_launcher_ref": ref(generic),
              "formal_chain_regression_receipt_ref": ref(regression)}
    protocol = {"status": "FROZEN", "run_id": "TEST_READY", "scope": "development_baseline",
                "predictor_wrapper_ref": formal["predictor_ref"], "validator_ref": formal["validator_ref"],
                "formal_execution": formal, "isolation": {"execution_boundary_id": "test-boundary-v1"}}
    contract = root / "contract.json"
    write(contract, {"schema": "gwm-gate0-staged-v2", "protocol": protocol, "review_ref": {}})
    supplied_validator = validator
    if wrong_validator:
        supplied_validator = root / "fake_validator.py"
        shutil.copy2(validator, supplied_validator); supplied_validator.write_text(supplied_validator.read_text() + "# changed\n")
    run = subprocess.run([sys.executable, os.fspath(PREPARER), "--contract", os.fspath(contract),
                          "--validator", os.fspath(supplied_validator), "--predictor", os.fspath(predictor),
                          "--sealer", os.fspath(SEALER), "--sbatch", os.fspath(SBATCH),
                          "--launch-guard", os.fspath(launch), "--generic-launcher", os.fspath(generic),
                          "--target", os.fspath(target)], text=True, capture_output=True)
    return run, target


def main() -> int:
    checks = []
    with tempfile.TemporaryDirectory(prefix="s103-formal-chain-") as tmp:
        root = Path(tmp)
        bundle, output, host = fixture(root / "valid")
        valid = run_seal(bundle, output, host)
        seal = json.loads((output / "PREDICTION_SEAL.json").read_text())
        checks.append(("valid prediction seals and unlocks scoring", valid.returncode == 0 and
                       seal["status"] == "PREDICTION_SEALED" and seal["future_scoring_permitted"] is True))
        checks.append(("existing seal cannot be overwritten", run_seal(bundle, output, host).returncode != 0))
        bundle, output, host = fixture(root / "future", future_opened=True)
        checks.append(("reported future access blocks success seal", run_seal(bundle, output, host).returncode != 0))
        bundle, output, host = fixture(root / "failed")
        failed = run_seal(bundle, output, host, 17)
        failed_seal = json.loads((output / "PREDICTION_SEAL.json").read_text())
        checks.append(("failed attempt never unlocks scoring", failed.returncode == 17 and
                       failed_seal["future_scoring_permitted"] is False))
        ready, target = preparer_fixture(root / "prepare-ready", True)
        dispatch = json.loads((target / "dispatch_manifest.json").read_text()) if target.is_dir() else {}
        checks.append(("bound PRE_RUN_READY creates scorer-free bundle", ready.returncode == 0 and
                       dispatch.get("status") == "FROZEN" and not (target / "scorer_s103.py").exists()))
        blocked, target = preparer_fixture(root / "prepare-blocked", False)
        checks.append(("blocked validator creates no bundle", blocked.returncode != 0 and not target.exists()))
        fake, target = preparer_fixture(root / "prepare-fake", True, wrong_validator=True)
        checks.append(("caller-selected fake validator is rejected", fake.returncode != 0 and not target.exists()))
    text = SBATCH.read_text()
    checks.extend([
        ("formal job binds source weights and stage read-only", all(x in text for x in
         ('"$SOURCE:$SOURCE:ro"', '"$WEIGHTS:$WEIGHTS:ro"', '"$STAGE:$STAGE:ro"'))),
        ("formal job exposes only prediction output read-write", '"$PREDICTOR_OUT:/mnt/predictions:rw"' in text),
        ("formal job derives bundle from submitted script", 'dirname "${BASH_SOURCE[0]}"' in text),
        ("formal job contains no scorer invocation", "scorer_s103.py" not in text and "future_rgb" not in text),
    ])
    status = "PASS" if all(ok for _, ok in checks) else "FAIL"
    print(json.dumps({"scope": "synthetic software/static checks only", "status": status,
                      "checks": [{"name": name, "passed": ok} for name, ok in checks]}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
