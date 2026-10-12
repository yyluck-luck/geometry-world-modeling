"""One persistent dispatch; intent and all fingerprints precede remote mutation."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile

BASE=Path('/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo')
STAGE=Path(__file__).resolve().parent
OUT=BASE/'outputs/s141-workflow/pilot-p2-20261010'
WF=BASE/'work/week1-wt/work/S141_autonomous_workflow'
REMOTE='/mnt/gluster_dcpu/yiyangliu/gwm_codex_p2_20261011'
SESSION='codexp2_20261011'
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

if __name__=='__main__':
    assert not (OUT/'DISPATCH_INTENT.json').exists(),'Reconcile existing dispatch, never repeat blindly'
    state=json.loads((WF/'WORKFLOW_STATE.json').read_text());assert state['active_pilot'] is None
    names=[p.name for p in sorted(STAGE.iterdir()) if p.is_file() and p.name not in {'FINGERPRINT.json'}]
    files={n:sha(STAGE/n) for n in names}
    fingerprint=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    intent={'recorded_utc':now(),'job_id':SESSION,'remote_stage':REMOTE,'files':files,'fingerprint':fingerprint,
        'status':'PREPARED_BEFORE_DISPATCH','candidate':'P2_UC_OBSERVED_SOURCE_INPUT','gpu_index':3,'gpu_cap_hours':2,
        'queue_wait_cap_hours':24,'new_generation_cells':49,'scored_cells':60}
    (STAGE/'FINGERPRINT.json').write_text(json.dumps(intent,indent=2)+'\n')
    (OUT/'DISPATCH_INTENT.json').write_text(json.dumps(intent,indent=2)+'\n')
    for n in names+['FINGERPRINT.json']:
        p=OUT/n
        if p.exists():assert sha(p)==sha(STAGE/n)
        else:shutil.copy2(STAGE/n,p)
    shutil.copy2(WF/'WORKFLOW_STATE.json',WF/'continuity_backups/WORKFLOW_STATE_pre_P2_dispatch.json')
    state.update(updated_utc=now(),phase='waiting',active_pilot=intent,experiment_fingerprint=fingerprint,
        next_action='Reconcile codexp2_20261011 only. It waits for existing S145/S146 and idle GPU3, then runs frozen five-arm P2 within2GPUh. Do not submit duplicates, take their GPUs, or reopen B/W2/P1. On completion independently recompute frozen gates; stop unsupported P2. No outcome exists until scoring/seal complete.')
    (WF/'WORKFLOW_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    archive=io.BytesIO()
    with tarfile.open(fileobj=archive,mode='w') as t:
        for n in names+['FINGERPRINT.json']:t.add(STAGE/n,arcname=n)
    check="import pathlib,json,hashlib;p=pathlib.Path('.');d=json.loads((p/'FINGERPRINT.json').read_text());assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in d['files'].items());print('fingerprint_ok')"
    first_check="import pathlib,time;p=pathlib.Path('QUEUE_STATUS.json');time.sleep(3);print(p.read_text() if p.exists() else 'queue_status_not_yet_available')"
    q=shlex.quote
    command=(f"set -e; test ! -e {q(REMOTE)}; mkdir {q(REMOTE)}; tar -xf - -C {q(REMOTE)}; cd {q(REMOTE)}; "
        f"python3 -c {q(check)}; tmux new-session -d -s {q(SESSION)} {q('python3 '+REMOTE+'/p2_queue.py > '+REMOTE+'/queue.log 2>&1')}; "
        f"tmux display-message -p -t {q(SESSION)} '#{{pane_pid}}'; date -u +%FT%TZ; python3 -c {q(first_check)}")
    try:
        p=subprocess.run(['ssh','-S','/Users/rocket/.ssh/cm-yiyangliu@gpu13','-o','ControlMaster=auto',
            '-o','ControlPersist=10m','-o','BatchMode=yes','-o','ConnectTimeout=15','gpu13',command],
            input=archive.getvalue(),capture_output=True,timeout=60)
        receipt={'finished_utc':now(),'returncode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'job_id':SESSION,'command':command}
    except subprocess.TimeoutExpired:
        receipt={'finished_utc':now(),'error':'Ambiguous dispatch timeout: read existing namespace only; never resubmit','job_id':SESSION}
    (OUT/'DISPATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    state['active_pilot']['status']='QUEUED_DISPATCH_CONFIRMED' if receipt.get('returncode')==0 else 'DISPATCH_AMBIGUOUS_OR_FAILED'
    state['updated_utc']=now();(WF/'WORKFLOW_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    with (WF/'CHECK_LEDGER.jsonl').open('a') as f:f.write(json.dumps({'observed_utc':now(),'event':'P2 persistent queue dispatch; no GPU/model execution claimed yet','phase':'waiting','job_id':SESSION,'fingerprint':fingerprint,'receipt':str(OUT/'DISPATCH_RECEIPT.json')})+'\n')
    print(json.dumps(receipt,indent=2))
