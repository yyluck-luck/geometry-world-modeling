"""One-shot persistent CPU dispatch; reconcile any ambiguous outcome, never retry blindly."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile

BASE = Path('/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo')
STAGE = Path(__file__).resolve().parent
OUT = BASE/'outputs/s141-workflow/pilot-p1-20261010'
WF = BASE/'work/week1-wt/work/S141_autonomous_workflow'
REMOTE = '/mnt/gluster_dcpu/yiyangliu/gwm_codex_p1_20261010'
SESSION = 'codexp1_20261010'
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
names = ['PROTOCOL.md', 'AMENDMENTS.md', 'pilot.py', 'preflight.py', 'test_pilot.py',
         'run.sh', 'INPUT_MANIFEST.json', 'INPUT_PROVENANCE_CHECK.json', 'POSE_ARMS.json']

if __name__ == '__main__':
    assert not (OUT/'DISPATCH_INTENT.json').exists(), 'Existing intent: reconcile, do not duplicate.'
    state = json.loads((WF/'WORKFLOW_STATE.json').read_text())
    assert state['active_pilot'] is None and state['s141_final_review']['status'] == 'COMPLETE'
    files = {name: sha(STAGE/name) for name in names}
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    intent = {'recorded_utc': now(), 'job_id': SESSION, 'remote_stage': REMOTE, 'files': files,
              'fingerprint': fingerprint, 'cpu_threads': 2, 'wall_cap_seconds': 3600, 'gpu_hours': 0,
              'status': 'PREPARED_BEFORE_DISPATCH', 'candidate': 'P1_cross_pair_region_frequency_residual_policy'}
    (OUT/'DISPATCH_INTENT.json').write_text(json.dumps(intent, indent=2)+'\n')
    (STAGE/'FINGERPRINT.json').write_text(json.dumps(intent, indent=2)+'\n')
    for name in names + ['FINGERPRINT.json']:
        dest = OUT/name
        if dest.exists():
            assert sha(dest) == sha(STAGE/name)
        else:
            shutil.copy2(STAGE/name, dest)
    shutil.copy2(WF/'WORKFLOW_STATE.json', WF/'continuity_backups/WORKFLOW_STATE_pre_p1_dispatch.json')
    state.update(updated_utc=now(), phase='innovating', active_pilot=intent,
                 experiment_fingerprint=fingerprint, current_hypothesis=intent['candidate'],
                 next_action='Reconcile this unique dispatch outcome; if running, inspect/resume P1 only. Never launch a duplicate. On completion independently verify its frozen gates; stop failed policy. S141 final review is complete; B and W2 remain closed.')
    (WF/'WORKFLOW_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as t:
        for name in names + ['FINGERPRINT.json']:
            t.add(STAGE/name, arcname=name)
    q = shlex.quote
    check = "import pathlib,json,hashlib; p=pathlib.Path('.'); d=json.loads((p/'FINGERPRINT.json').read_text()); assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in d['files'].items()); print('fingerprint_ok')"
    command = (f"set -e; test ! -e {q(REMOTE)}; mkdir {q(REMOTE)}; tar -xf - -C {q(REMOTE)}; "
               f"cd {q(REMOTE)}; python3 -c {q(check)}; command -v timeout; command -v tmux; "
               "/mnt/gluster_dcpu/yiyangliu/gwm_s134/env/bin/python -c 'import numpy,scipy,torch; print(numpy.__version__,scipy.__version__,torch.__version__)'; "
               f"tmux new-session -d -s {q(SESSION)} {q('bash '+REMOTE+'/run.sh > '+REMOTE+'/run.log 2>&1')}; "
               f"tmux display-message -p -t {q(SESSION)} '#{{pane_pid}}'; date -u +%FT%TZ")
    ssh = ['ssh','-S','/Users/rocket/.ssh/cm-yiyangliu@gpu13','-o','ControlMaster=auto','-o','ControlPersist=10m',
           '-o','BatchMode=yes','-o','ConnectTimeout=15','gpu13',command]
    try:
        r = subprocess.run(ssh,input=archive.getvalue(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
        receipt = {'finished_utc':now(),'returncode':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode(),
                   'job_id':SESSION,'fingerprint':fingerprint,'execution_command':command}
    except subprocess.TimeoutExpired as e:
        receipt = {'finished_utc':now(),'error':'ambiguous SSH timeout; reconcile only','job_id':SESSION,'fingerprint':fingerprint}
    (OUT/'DISPATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    state['active_pilot']['status'] = 'DISPATCHED' if receipt.get('returncode') == 0 else 'DISPATCH_AMBIGUOUS_OR_FAILED'
    state['phase'] = 'running_pilot' if receipt.get('returncode') == 0 else 'innovating'
    state['updated_utc'] = now()
    (WF/'WORKFLOW_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    with (WF/'CHECK_LEDGER.jsonl').open('a') as f:
        f.write(json.dumps({'observed_utc':now(),'phase':state['phase'],'event':'One distinct CPU pilot dispatch',
                            'job_id':SESSION,'fingerprint':fingerprint,'receipt':str(OUT/'DISPATCH_RECEIPT.json'),
                            'gpu_hours':0,'new_jobs':1 if receipt.get('returncode') == 0 else 'unknown','W2_reopened':False})+'\n')
    print(json.dumps(receipt,indent=2))
