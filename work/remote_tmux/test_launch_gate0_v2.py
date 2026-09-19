#!/usr/bin/env python3
"""Software-only dispatch guard regressions; no tmux server, SSH, Slurm or model run."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
GUARD = HERE / 'launch_gate0_v2_in_tmux.sh'
GENERIC = HERE / 'launch_slurm_in_tmux.sh'
MONITOR = HERE / 'monitor_slurm_job.sh'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def protocol_sha(protocol):
    return hashlib.sha256(json.dumps(protocol, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, sort_keys=True))
    return path

def setup(mode='ready'):
    root = Path(tempfile.mkdtemp(prefix='gate0-v2-launch-test-'))
    remote = root / 'remote_tmux'
    remote.mkdir()
    shutil.copy2(GUARD, remote / GUARD.name)
    shutil.copy2(GENERIC, remote / GENERIC.name)
    shutil.copy2(MONITOR, remote / MONITOR.name)
    (remote / GUARD.name).chmod(0o755)
    tmux_log = root / 'tmux.calls'
    tmux = write(root / 'bin/tmux', '''#!/bin/sh
set -eu
if [ "$1" = has-session ]; then exit 1; fi
if [ "$1" = new-session ]; then echo "$*" >> "$TMUX_LOG"; exit 0; fi
exit 1
''')
    tmux.chmod(0o755)
    # The validator is a controlled software stub, never a scientific runner.
    stub = write(root / 'validator_stub.py', '''#!/usr/bin/env python3
import json, os, sys
mode = os.environ.get("STUB_MODE", "ready")
out = {"schema": "gwm-gate0-staged-v2", "stage": "pre-run",
       "scope": "development_baseline", "run_id": "TEST_RUN_V2",
       "protocol_sha256": os.environ["PROTO_SHA"], "pre_run_ready": mode == "ready",
       "status": "PRE_RUN_READY" if mode == "ready" else "BLOCKED",
       "errors": [] if mode == "ready" else ["synthetic blocked fixture"]}
print(json.dumps(out))
raise SystemExit(0 if mode in {"ready", "legacy"} else 2)
''')
    stub.chmod(0o755)
    protocol = {"status": "FROZEN", "run_id": "TEST_RUN_V2",
                "scope": "development_baseline", "author": "test_author",
                "predictor_wrapper_ref": None,
                "isolation": {"execution_boundary_id": "synthetic-boundary-v1"}}
    wrapper = write(root / 'predictor_wrapper.py', '# synthetic guarded wrapper; never executed\n')
    protocol["predictor_wrapper_ref"] = {"path": str(wrapper), "sha256": sha(wrapper), "bytes": wrapper.stat().st_size}
    contract = write(root / 'contract.json', {"schema": "gwm-gate0-staged-v2", "protocol": protocol})
    sbatch = write(root / 'run.slurm', "# synthetic sbatch; never submitted\n")
    validator = stub
    manifest = write(root / 'dispatch.json', {
        "schema": "gwm-gate0-v2-dispatch-manifest-v1", "status": "FROZEN", "stage": "pre-run",
        "run_id": protocol["run_id"], "scope": protocol["scope"], "protocol_sha256": protocol_sha(protocol),
        "contract_sha256": sha(contract), "sbatch_script_sha256": sha(sbatch),
        "validator_sha256": sha(validator), "predictor_wrapper_sha256": sha(wrapper),
        "execution_boundary_id": "synthetic-boundary-v1"})
    env = os.environ.copy()
    env.update({"PATH": str(root / "bin") + os.pathsep + env["PATH"],
                "TMUX_LOG": str(tmux_log), "GWM_GATE0_PYTHON": sys.executable,
                "GWM_GATE0_V2_VALIDATOR": str(validator), "PROTO_SHA": protocol_sha(protocol),
                "STUB_MODE": mode})
    args = [str(remote / GUARD.name), "test-v2", str(contract), str(manifest), str(sbatch), str(root / "formal.log")]
    return root, args, env, contract, manifest, sbatch, validator, tmux_log

def run_case(name, mutate=None, mode='ready', expect_ok=False, repeat=False):
    root, args, env, contract, manifest, sbatch, validator, log = setup(mode)
    try:
        if mutate:
            mutate(root, contract, manifest, sbatch, validator)
        first = subprocess.run(args, env=env, text=True, capture_output=True)
        second = None
        if repeat:
            second = subprocess.run(args, env=env, text=True, capture_output=True)
        calls = log.read_text().splitlines() if log.exists() else []
        formal_receipt = Path(str(root / 'formal.log') + '.formal_launch_guard_receipt.json')
        ok = (first.returncode == 0) if expect_ok else (first.returncode != 0)
        if expect_ok:
            guard = json.loads(formal_receipt.read_text()) if formal_receipt.is_file() else {}
            required = {'schema', 'status', 'validator_receipt_sha256', 'manifest_sha256',
                        'validator_receipt_raw',
                        'contract_sha256', 'protocol_sha256', 'validator_sha256',
                        'sbatch_script_sha256', 'generic_launcher_sha256',
                        'predictor_wrapper_sha256', 'execution_boundary_id',
                        'run_id', 'scope', 'session', 'remote_log', 'state_dir', 'exact_command'}
            ok = ok and guard.get('schema') == 'gwm-formal-launch-guard-receipt-v1' \
                and guard.get('status') == 'PASS' and required <= set(guard)
            embedded = guard.get('validator_receipt', {})
            generic = root / 'remote_tmux' / GENERIC.name
            ok = ok and guard.get('run_id') == 'TEST_RUN_V2' \
                and guard.get('scope') == 'development_baseline' \
                and guard.get('session') == 'test-v2' \
                and guard.get('remote_log') == str(root / 'formal.log') \
                and guard.get('state_dir') == str(root / 'formal.log.state') \
                and guard.get('manifest_sha256') == sha(manifest) \
                and guard.get('contract_sha256') == sha(contract) \
                and guard.get('validator_sha256') == sha(validator) \
                and guard.get('sbatch_script_sha256') == sha(sbatch) \
                and guard.get('generic_launcher_sha256') == sha(generic) \
                and guard.get('protocol_sha256') == json.loads(manifest.read_text())['protocol_sha256'] \
                and guard.get('predictor_wrapper_sha256') == sha(root / 'predictor_wrapper.py') \
                and guard.get('execution_boundary_id') == 'synthetic-boundary-v1' \
                and guard.get('exact_command') == f'bash {generic} test-v2 {sbatch} {root / "formal.log"}' \
                and embedded.get('schema') == 'gwm-gate0-staged-v2' \
                and embedded.get('stage') == 'pre-run' \
                and embedded.get('status') == 'PRE_RUN_READY' \
                and embedded.get('pre_run_ready') is True \
                and embedded.get('errors') == [] \
                and embedded.get('run_id') == 'TEST_RUN_V2' \
                and embedded.get('scope') == 'development_baseline' \
                and embedded.get('protocol_sha256') == json.loads(manifest.read_text())['protocol_sha256'] \
                and len(guard.get('validator_receipt_sha256', '')) == 64 \
                and guard.get('validator_receipt_sha256') == hashlib.sha256(guard.get('validator_receipt_raw', '').encode()).hexdigest()
        if repeat:
            ok = ok and second is not None and second.returncode != 0 and len(calls) == 1
        return {"name": name, "passed": ok, "first_exit": first.returncode,
                "second_exit": None if second is None else second.returncode,
                "tmux_dispatches": len(calls), "formal_receipt": formal_receipt.is_file(), "stdout": first.stdout[-300:], "stderr": first.stderr[-300:]}
    finally:
        shutil.rmtree(root, ignore_errors=True)

def mutate_validator(root, contract, manifest, sbatch, validator):
    validator.write_text(validator.read_text() + "\n# changed after freeze\n")

def mutate_sbatch(root, contract, manifest, sbatch, validator):
    sbatch.write_text(sbatch.read_text() + "# changed after freeze\n")

def mutate_contract(root, contract, manifest, sbatch, validator):
    obj = json.loads(contract.read_text()); obj["protocol"]["author"] = "changed"; contract.write_text(json.dumps(obj))

def mutate_scope(root, contract, manifest, sbatch, validator):
    obj = json.loads(manifest.read_text()); obj["scope"] = "heldout_baseline"; manifest.write_text(json.dumps(obj))

def mutate_wrapper_binding(root, contract, manifest, sbatch, validator):
    obj = json.loads(manifest.read_text()); obj["predictor_wrapper_sha256"] = "0" * 64; manifest.write_text(json.dumps(obj))

def mutate_wrapper_file(root, contract, manifest, sbatch, validator):
    wrapper = root / 'predictor_wrapper.py'; wrapper.write_text(wrapper.read_text() + '# tampered\n')

def main():
    cases = [
        run_case("valid v2 receipt dispatches once; duplicate state is rejected", expect_ok=True, repeat=True),
        run_case("blocked v2 receipt rejects before tmux", mode="blocked"),
        run_case("legacy validator schema rejects despite zero exit", mode="legacy"),
        run_case("changed validator rejects before execution", mutate_validator),
        run_case("changed sbatch rejects before execution", mutate_sbatch),
        run_case("changed contract rejects before execution", mutate_contract),
        run_case("manifest scope mismatch rejects before execution", mutate_scope),
        run_case("wrapper binding mismatch rejects before execution", mutate_wrapper_binding),
        run_case("wrapper file tamper rejects before execution", mutate_wrapper_file),
    ]
    receipt = {"schema": "gate0-v2-launch-regression-v1",
               "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "guard_sha256": sha(GUARD), "test_sha256": sha(Path(__file__)),
               "scope": "Software-only stub validator/tmux checks; no remote deployment or job submission.",
               "status": "PASS" if all(c["passed"] for c in cases) else "FAIL",
               "cases": cases}
    path = HERE / "LAUNCH_GATE0_V2_REGRESSION_RECEIPT.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "passed": sum(c["passed"] for c in cases),
                      "total": len(cases), "receipt": str(path)}, indent=2))
    return 0 if receipt["status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
