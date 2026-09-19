#!/usr/bin/env python3
"""Two-window canary executed INSIDE the formal isolation environment.

The earlier canary ran in a plain interpreter with only an audit hook installed.
That is a NEGATIVE CONTROL: it demonstrates the hook's limits, and the observed
child-process read there is expected, not an isolation failure.

This run is the POSITIVE acceptance test.  It executes inside the same Apptainer
configuration the predictor uses, with only window A's staging directory bound.
The question it answers is narrow and decisive:

    with the formal mount configuration, can a child process read a file that
    belongs to window B but not to window A?

If that read succeeds here, isolation is FAILED, not UNMEASURED.
"""
import json, os, subprocess, sys
from pathlib import Path

STAGE = Path(os.environ["WINDOW_STAGE"])         # only A's approved files
FORBIDDEN = os.environ["FORBIDDEN_PATH"]         # B's history == A's target
OUT = Path(os.environ["CANARY_OUT"])
SEQ_DIR = os.environ.get("SEQUENCE_DIR", "")     # must not be mounted

results = {}

def probe(name, fn):
    try:
        fn()
        results[name] = {"read_succeeded": True}
    except Exception as exc:
        results[name] = {"read_succeeded": False, "error": f"{type(exc).__name__}: {exc}"}

# 1. A's own staged history must be readable.
staged = sorted((STAGE / "history").glob("*"))
probe("own_staged_history_readable", lambda: staged[0].read_bytes())

# 2. Direct read of the forbidden file from inside the container.
probe("direct_read_forbidden", lambda: Path(FORBIDDEN).read_bytes())

# 3. Child process read of the same file.  This is the discriminating probe.
def child():
    r = subprocess.run([sys.executable, "-c",
                        f"open({FORBIDDEN!r},'rb').read()"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr else "child failed")
probe("child_process_read_forbidden", child)

# 4. Directory listing of the source sequence, if it were mounted.
probe("sequence_directory_listable",
      lambda: os.listdir(SEQ_DIR) if SEQ_DIR else (_ for _ in ()).throw(FileNotFoundError("not configured")))

blocked = (not results["direct_read_forbidden"]["read_succeeded"]
           and not results["child_process_read_forbidden"]["read_succeeded"]
           and not results["sequence_directory_listable"]["read_succeeded"])
own_ok = results["own_staged_history_readable"]["read_succeeded"]

receipt = {
    "schema": "gwm-container-window-isolation-acceptance-v1",
    "environment": "formal Apptainer configuration with only the window stage bound",
    "test_role": "positive acceptance test, not the audit-hook negative control",
    "window_stage": str(STAGE),
    "forbidden_path": FORBIDDEN,
    "probes": results,
    "own_permitted_read_works": own_ok,
    "all_forbidden_reads_blocked": blocked,
    "isolation_status": "PASS" if (blocked and own_ok) else "FAILED",
    "interpretation": ("A successful forbidden read here is an isolation FAILURE, not "
                       "UNMEASURED. UNMEASURED applies only where the instrument cannot "
                       "observe, not where a forbidden read was observed to succeed."),
    "hostname": os.uname().nodename,
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "CONTAINER_ISOLATION_ACCEPTANCE.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
