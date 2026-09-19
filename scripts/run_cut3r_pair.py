#!/usr/bin/env python3
"""Continue the already authorized two-image run once dependencies are verified.

This is a local job waiting on its own download/import prerequisites, not a
recurring automation. Every stage is recorded and failed outputs are retained.
"""
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import re
from pathlib import Path
import subprocess
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/cut3r"
PYTHON = ROOT / ".venv-cut3r/bin/python"
REPO = Path("/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local")
STATE = DATA / "pair_pipeline_state.json"


def record(phase, **extra):
    value = {"recorded_utc":datetime.now(timezone.utc).isoformat(),"phase":phase,**extra}
    STATE.write_text(json.dumps(value,indent=2)+"\n")
    with (DATA / "pair_pipeline_events.jsonl").open("a") as stream:
        stream.write(json.dumps(value)+"\n")
    print(json.dumps(value),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=REPO)
    parser.add_argument("--prerequisite-timeout-hours",type=float,default=4)
    parser.add_argument("--signed-rope-check",type=Path)
    parser.add_argument("--run-suffix",default="")
    args = parser.parse_args()
    if args.run_suffix and not re.fullmatch(r"[a-zA-Z0-9_-]+",args.run_suffix):
        parser.error("run-suffix must use letters, digits, underscores or hyphens")
    suffix = "_"+args.run_suffix if args.run_suffix else ""
    repo = args.repo.resolve()
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA / ".pair_pipeline.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record("waiting_for_verified_download_and_environment",deadline_hours=args.prerequisite_timeout_hours,run_suffix=args.run_suffix)
        deadline = time.monotonic()+args.prerequisite_timeout_hours*60*60
        while time.monotonic() < deadline:
            downloaded = DATA / "download_manifest.json"
            smoke = repo / "local_readiness/smoke_verified.json"
            if downloaded.exists() and smoke.exists():
                if json.loads(downloaded.read_text()).get("status") == "verified_download" and json.loads(smoke.read_text()).get("ok") is True:
                    break
            time.sleep(10)
        else:
            raise TimeoutError("Prerequisites not verified within four hours; partial files remain")
        inputs = json.loads((DATA / "inference_inputs.json").read_text())
        for image in inputs["images"]:
            if hashlib.sha256(Path(image["path"]).read_bytes()).hexdigest() != image["sha256"]:
                raise RuntimeError("Frozen input image changed before inference")
        command = [str(PYTHON),str(ROOT/"scripts/run_cut3r_local.py"),"--repo",str(repo),
                   "--checkpoint",str(DATA/"cut3r_224_linear_4.pth"),"--images",*[image["path"] for image in inputs["images"]],
                   "--input-source","TUM freiburg1_xyz; first two frozen S2 QA indices [0,34], selected before CUT3R output"]
        if args.signed_rope_check:
            command += ["--signed-rope-check",str(args.signed_rope_check.resolve())]
        cpu = ROOT / f"results/CUT3R_cpu_2frames{suffix}"
        mps = ROOT / f"results/CUT3R_mps_2frames{suffix}"
        for device, output in (("cpu",cpu),("mps",mps)):
            record("starting_inference",device=device,output=str(output))
            args = command+["--device",device,"--output",str(output)]
            if device == "mps": args += ["--compare",str(cpu)]
            log = DATA / f"{device}_2frames{suffix}.log"
            with log.open("x") as stream:
                result = subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT,timeout=2*60*60)
            if result.returncode:
                raise RuntimeError(f"{device} protocol returned {result.returncode}; inspect {log}")
            record("inference_verified",device=device,output=str(output))
        record("complete",cpu_output=str(cpu),mps_output=str(mps))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        record("failed",error=traceback.format_exc())
        raise
