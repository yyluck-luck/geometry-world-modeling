"""One read-only P2 status/result collection through the existing SSH master."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
BASE=Path('/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo')
OUT=BASE/'outputs/s141-workflow/pilot-p2-20261010';WF=BASE/'work/week1-wt/work/S141_autonomous_workflow'
script=r'''
from pathlib import Path
import json,hashlib,datetime,subprocess
p=Path('/mnt/gluster_dcpu/yiyangliu/gwm_codex_p2_20261011')
names=['QUEUE_STATUS.json','GPU_STARTED.json','GPU_FINISHED.json','REPLAY_TIMING.json','RESULT.json','EXECUTION_FAILURE.json','OUTPUT_SEAL.json','RUN_EXIT_CODE.txt','ENVIRONMENT.json','FINGERPRINT.json']
files={}
for f in [p/x for x in names]+sorted((p/'results').glob('SCORES_*.json')):
 if f.exists():files[str(f.relative_to(p))]={'text':f.read_text(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
for f in p.glob('*.log'):
 files[str(f.relative_to(p))]={'text':f.read_text()[-4000:],'tail_only':True}
if (p/'OUTPUT_SEAL.json').exists() or (p/'EXECUTION_FAILURE.json').exists() or (p/'RESULT.json').exists():
 for f in sorted((p/'results').glob('*/*.trace.json'))+sorted((p/'results').glob('*/RUNS*.jsonl')):
  files[str(f.relative_to(p))]={'text':f.read_text(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
alive=subprocess.run(['tmux','has-session','-t','codexp2_20261011'],capture_output=True).returncode==0
counts={x.name:len(list(x.glob('*.npy'))) for x in (p/'results').glob('*') if x.is_dir()}
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'session_alive':alive,'prediction_counts':counts,'files':files}))
'''
if __name__=='__main__':
    r=subprocess.run(['ssh','-S','/Users/rocket/.ssh/cm-yiyangliu@gpu13','-o','ControlMaster=auto','-o','ControlPersist=10m',
        '-o','BatchMode=yes','-o','ConnectTimeout=15','gpu13','python3 -'],input=script,text=True,capture_output=True,timeout=60)
    assert r.returncode==0,r.stderr
    d=json.loads(r.stdout);snap=OUT/('collection-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));snap.mkdir()
    for name,item in d['files'].items():
        p=snap/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(item['text'])
        if 'sha256' in item:assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
    state=json.loads((WF/'WORKFLOW_STATE.json').read_text());pilot=state['active_pilot'];assert pilot['job_id']=='codexp2_20261011'
    pilot.update(last_collection=str(snap),last_observed_utc=d['observed_utc'],prediction_counts=d['prediction_counts'])
    if 'RESULT.json' in d['files'] or 'EXECUTION_FAILURE.json' in d['files'] or 'RUN_EXIT_CODE.txt' in d['files']:
        state['phase']='verifying';pilot['status']='RESULT_OR_EXIT_REQUIRES_RECONCILIATION'
        state['next_action']='Read P2 result/failure; if full scored output exists independently verify arithmetic, fingerprints and gates. If scientific gates fail retire this policy. Do not rerun or tune. If compute/queue cap exhausted pause exact automation and report blocker.'
    elif 'GPU_STARTED.json' in d['files']:state['phase']='running_pilot';pilot['status']='GPU_RUN_OBSERVED'
    elif d['session_alive']:state['phase']='waiting';pilot['status']='WAITING_EXISTING_OWNER_JOBS_OR_GPU'
    else:state['phase']='blocked';pilot['status']='SESSION_ABSENT_RECONCILE_NO_RELAUNCH'
    state['last_remote_check_utc']=d['observed_utc'];state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (WF/'WORKFLOW_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    compact={k:v for k,v in d.items() if k!='files'};compact['collection']=str(snap);compact['phase']=state['phase']
    (snap/'SNAPSHOT.json').write_text(json.dumps(compact,indent=2)+'\n');print(json.dumps(compact,indent=2))
