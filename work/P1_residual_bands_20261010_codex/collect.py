"""One bounded read-only collection of the existing P1 job. Never launches work."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path('/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo')
OUT = BASE/'outputs/s141-workflow/pilot-p1-20261010'
WF = BASE/'work/week1-wt/work/S141_autonomous_workflow'
script = r'''
import pathlib,json,subprocess,hashlib,datetime
p=pathlib.Path('/mnt/gluster_dcpu/yiyangliu/gwm_codex_p1_20261010')
paths=[p/'run.log',p/'RUN_EXIT_CODE.txt']+sorted((p/'results').glob('*.json'))
files={str(x.relative_to(p)):{'text':x.read_text(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in paths if x.is_file()}
alive=subprocess.run(['tmux','has-session','-t','codexp1_20261010'],capture_output=True).returncode==0
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'job_id':'codexp1_20261010','session_alive':alive,'prediction_files':len(list((p/'results/predictions').glob('*.npy'))),'files':files}))
'''

if __name__ == '__main__':
    r = subprocess.run(['ssh','-S','/Users/rocket/.ssh/cm-yiyangliu@gpu13','-o','ControlMaster=auto',
        '-o','ControlPersist=10m','-o','BatchMode=yes','-o','ConnectTimeout=15','gpu13','python3 -'],
        input=script.encode(),capture_output=True,timeout=60)
    if r.returncode:
        raise RuntimeError(r.stderr.decode())
    data = json.loads(r.stdout)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    snap = OUT/f'collection-{stamp}';snap.mkdir()
    for name, item in data['files'].items():
        path=snap/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(item['text'])
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    snapshot={k:v for k,v in data.items() if k!='files'}
    snapshot['file_hashes']={k:v['sha256'] for k,v in data['files'].items()}
    (snap/'SNAPSHOT.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    state=json.loads((WF/'WORKFLOW_STATE.json').read_text())
    state['active_pilot']['last_collection']=str(snap)
    state['active_pilot']['last_observed_utc']=data['observed_utc']
    state['active_pilot']['prediction_files']=data['prediction_files']
    if 'results/RESULT.json' in data['files']:
        state['phase']='verifying';state['active_pilot']['status']='RESULT_AVAILABLE_REQUIRES_INDEPENDENT_CHECK'
        state['next_action']='Independently verify P1 copied scores, coefficients and frozen gates; do not run more experiments or S141 audits. Retire P1 if any gate fails.'
    elif 'RUN_EXIT_CODE.txt' in data['files']:
        state['active_pilot']['status']='EXITED_WITHOUT_RESULT'
        state['next_action']='Read saved P1 error once. Do not classify integrity/runtime failure as scientific negative or relaunch blindly; preserve artifacts.'
    else:
        state['phase']='running_pilot';state['active_pilot']['status']='RUNNING_OBSERVED' if data['session_alive'] else 'SESSION_ABSENT_RECONCILE'
    state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (WF/'WORKFLOW_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    print(json.dumps({**snapshot,'saved_to':str(snap),'tail':data['files'].get('run.log',{}).get('text','')[-1500:]},indent=2))
