"""One P2 waiting queue; select a truly idle card on this authorized host."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

OPS = Path(__file__).resolve().parent
ROOT = OPS.parent
PY = '/mnt/gluster_dcpu/yiyangliu/gwm_s134/env/bin/python'
DEADLINE = datetime.datetime.fromisoformat('2026-10-12T04:06:05.649259+00:00')


def candidates(csv, occupied, reserved):
    result = []
    for line in csv.splitlines():
        parts = [x.strip() for x in line.split(',')]
        if len(parts) != 6:
            raise ValueError('GPU inventory unavailable; never treat driver errors as idle')
        index, uuid, model, mem, util, driver = parts
        if 'RTX 3090' in model and int(index) not in reserved and uuid not in occupied and int(mem) < 100 and int(util) < 5:
            result.append({'index': int(index), 'uuid': uuid, 'model': model, 'driver': driver})
    return sorted(result, key=lambda x: x['index'])


def main():
    host = socket.gethostname()
    assert host in ('gpu13', 'gpu14')
    claim = json.loads((ROOT/'MOBILITY_CLAIM_V2'/'owner.json').read_text())
    assert claim['host'] == host
    lock = ROOT/'MOBILITY_CLAIM_V2'/'queue_started.json'
    with lock.open('x') as f:
        json.dump({'pid': os.getpid(), 'host': host, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}, f)
    frozen = json.loads((OPS/'FREEZE.json').read_text())
    assert all(hashlib.sha256((OPS/k).read_bytes()).hexdigest() == v for k,v in frozen['files'].items())
    seen = {}
    while datetime.datetime.now(datetime.timezone.utc) < DEADLINE:
        sessions = subprocess.run(['tmux','list-sessions','-F','#S'],capture_output=True,text=True,timeout=10,check=True).stdout.splitlines()
        reserved = {3,4} if any(x.startswith(tuple('s'+str(k) for k in range(143,150))) for x in sessions) else set()
        query = subprocess.run(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
        apps = subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
        query.check_returncode(); apps.check_returncode()
        available = candidates(query.stdout, set(apps.stdout.splitlines()), reserved)
        current = time.monotonic()
        seen = {g['uuid']: seen.get(g['uuid'],current) for g in available}
        ready = [g for g in available if current-seen[g['uuid']] >= 120]
        status = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'READY' if ready else 'WAITING_AVAILABLE_OWNER_AUTHORIZED_GPU',
                  'host':host,'reserved_indices':sorted(reserved),'gpu_csv':query.stdout,'idle_candidates':available,'sessions':sessions,'operational_fingerprint':frozen['fingerprint']}
        (ROOT/'QUEUE_STATUS.json').write_text(json.dumps(status)+'\n')
        if ready:
            allocation = {**ready[0], 'host':host, 'utc':status['utc'], 'two_idle_observations':True}
            with (ROOT/'ALLOCATION_MOBILITY_V2.json').open('x') as f:
                json.dump(allocation,f,indent=2)
            result = subprocess.run([PY,str(OPS/'run_experiment.py')])
            (ROOT/'RUN_EXIT_CODE.txt').write_text(str(result.returncode)+'\n')
            raise SystemExit(result.returncode)
        time.sleep(120)
    (ROOT/'RESULT.json').write_text(json.dumps({'status':'BLOCKED_CAPACITY','reason':'Original queue deadline exhausted; no GPU allocated.'})+'\n')


if __name__ == '__main__':
    main()
