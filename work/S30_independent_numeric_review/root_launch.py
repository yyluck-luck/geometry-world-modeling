#!/usr/bin/env python3
"""One bounded execution of the reviewed S30 saved-data audit."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/S30_independent_numeric_execution'
assert not OUT.exists(), 'Preserve any previous execution'
c = json.loads((HERE / 'candidate.json').read_text())
bindings = {
    HERE / 'recompute.py': c['script_sha256'],
    HERE / 'protocol.md': c['protocol_sha256'],
    ROOT / 'work/S28_independent_numeric_review/recompute.py': c['helper_sha256'],
    ROOT / 'work/S30_scale_optimization_preparation/contract.json': c['s30_final_contract_sha256'],
    ROOT / 'scripts/s26b_consumer_baseline.py': '61e00503829dad7e9d1260fb408b81e8b281198e3cbf4bcab8367a493f982834',
}
for path, digest in bindings.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
for mode in ('C2t', 'C2a', 'scoring'):
    assert json.loads((ROOT / 'results/S30_scale_optimization' / mode / 'receipt.json').read_text())['status'] == 'PASS'
OUT.mkdir()
record = dict(status='STATIC_REVIEW_PASS_READY_FOR_ONE_RUN', recorded_utc=datetime.now(timezone.utc).isoformat(),
              reviewer='root', full_source_review_completed_before_launch=True,
              reviewed_files={str(p): s for p, s in bindings.items()},
              scope='Complete adapter and protocol read; unchanged independent S28 numerical helper reused; no model/GA/backward.',
              command=c['command_template'], wall_limit_seconds=180, rss_limit_bytes=2 * 1024**3, cpu_threads=1)
(OUT / 'root_pre_execution_review.json').write_text(json.dumps(record, indent=2) + '\n')
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
spec = importlib.util.spec_from_file_location('s30_audit_parent_supervisor', ROOT / 'scripts/s26b_consumer_baseline.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
b.WORK = OUT
b.supervised(c['command_template'], 'review', 180, 2 * 1024**3)
print((OUT / 'review/receipt.json').read_text())
