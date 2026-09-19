"""Record the one authorized S34 producer dispatch; per-worker limits live there."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
def utc(): return datetime.now(timezone.utc).isoformat()
def write(path, obj): path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
def main(expected):
    contract = ROOT / 'work/S34_preparation/contract.json'
    assert hashlib.sha256(contract.read_bytes()).hexdigest() == expected
    c = json.loads(contract.read_text())
    assert c['status'] == 'FROZEN'
    out = ROOT / 'work/S34_launch'
    out.mkdir(exist_ok=False)
    cmd = [str(ROOT / '.venv-cut3r/bin/python'), c['runner'], 'dispatch', '--contract', str(contract), '--sha256', expected]
    env = os.environ.copy()
    for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
        env[name] = '8'
    r = dict(status='RUNNING', started_utc=utc(), contract_sha256=expected, command=cmd,
             resource_enforcement='Original supervised worker limits: common120s4GiB, each arm240s8GiB, min10GiB free; sequential CPU8')
    start = time.monotonic()
    write(out / 'receipt.json', r)
    with (out / 'stdout.txt').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
        proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
        r['pid'] = proc.pid
        write(out / 'receipt.json', r)
        code = proc.wait()
    r.update(status='PASS' if code == 0 else 'FAILED', completed_utc=utc(), wall_seconds=time.monotonic()-start, returncode=code)
    write(out / 'receipt.json', r)
    print(json.dumps(r, ensure_ascii=False))
    raise SystemExit(code)

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--sha256', required=True)
    main(p.parse_args().sha256)
