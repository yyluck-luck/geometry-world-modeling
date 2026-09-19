#!/usr/bin/env python3
"""Synthetic namespace read-boundary probe; no model, real data, or GPU allocation."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import socket
import subprocess
import sys
import uuid

BASE = Path(__file__).resolve().parent
STAGED = BASE / 'fixture_staged'
OUTSIDE = BASE / 'fixture_outcomes'
STAGED.mkdir(exist_ok=True)
OUTSIDE.mkdir(exist_ok=True)
history = STAGED / 'history.txt'
history.write_text('SYNTHETIC_ALLOWED_HISTORY\n')
outcome = OUTSIDE / 'outcome.txt'
outcome.write_text('SYNTHETIC_FORBIDDEN_OUTCOME\n')
archive = OUTSIDE / 'whole_archive.zip'
archive.write_bytes(b'SYNTHETIC_ARCHIVE_FIXTURE_NOT_REAL_DATA')
link = STAGED / 'outcome_link.txt'
if not link.exists() and not link.is_symlink():
    link.symlink_to(outcome)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

probe = STAGED / 'probe.py'
probe.write_text('''import json,os,pathlib,sys
history,outcome,archive,symlink=sys.argv[1:]
attempts=[]
for label,path,expected in [('allowed_history',history,True),('denied_outcome',outcome,False),('denied_archive',archive,False),('denied_symlink',symlink,False),('denied_proc_root_escape','/proc/1/root'+outcome,False)]:
 try:
  with open(path,'rb') as f:data=f.read(128)
  opened=True;error=None
 except OSError as e:
  opened=False;error={'type':type(e).__name__,'errno':e.errno,'message':str(e)};data=b''
 attempts.append({'label':label,'path':path,'expected_open':expected,'opened':opened,'pass':opened==expected,'error':error,'fixture_content':data.decode() if opened else None})
status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line}
caps_ok=int(status['CapEff'],16)==0 and int(status['CapPrm'],16)==0 and int(status['CapBnd'],16)==0 and status['NoNewPrivs']=='1'
result={'schema':'gwm-isolation-fixture-probe-v1','scope':'synthetic_fixture_login_node_only','pid':os.getpid(),'attempts':attempts,'capabilities':{k:status[k] for k in ['CapEff','CapPrm','CapBnd','NoNewPrivs']},'caps_dropped':caps_ok,'real_data_read':False,'gpu_used':False,'passed':all(x['pass'] for x in attempts) and caps_ok}
print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 2)
''')
pred = BASE / 'fixture_predictor_inputs.json'
pred.write_text(json.dumps({'scope':'synthetic only','records':[{'role':'history_text_fixture','path':str(history),'sha256':sha(history)}]},indent=2))
scorer = BASE / 'fixture_scorer_inputs.json'
scorer.write_text(json.dumps({'scope':'synthetic only','records':[{'role':'future_text_fixture','path':str(outcome),'sha256':sha(outcome)}]},indent=2))
runtime = BASE / 'fixture_runtime_binding.json'
runtime.write_text(json.dumps({'scope':'synthetic only','executable':sys.executable,'probe_sha256':sha(probe),'checkpoint_paths':{}},indent=2))
policy = {'schema':'gwm-predictor-isolation-v1','scope':'synthetic_fixture_login_node_only',
          'execution_boundary_id':'namespace-fixture-'+uuid.uuid4().hex,
          'predictor_inputs_sha256':sha(pred),'scorer_inputs_sha256':sha(scorer),
          'runtime_binding_sha256':sha(runtime),'readonly_paths':[str(STAGED)],'readwrite_paths':[],
          'denied_paths':[str(outcome),str(archive)],'working_directory':str(STAGED),
          'command':[sys.executable,str(probe),str(history),str(outcome),str(archive),str(link)],
          'allow_nvidia_devices':False}
policy_path = BASE / 'fixture_policy.json'
policy_path.write_text(json.dumps(policy,indent=2)+'\n')
wrapper = BASE / 'isolated_predictor.py'
command = [sys.executable,str(wrapper),'--policy',str(policy_path),'--receipt',str(BASE/'FIXTURE_LAUNCH_RECEIPT.json')]
result = subprocess.run(command,text=True,capture_output=True)
parsed = None
if result.returncode == 0:
    try: parsed=json.loads(result.stdout)
    except json.JSONDecodeError: pass
receipt={'schema':'gwm-isolation-fixture-driver-v1','scope':'synthetic_fixture_login_node_only',
         'recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'host':socket.gethostname(),
         'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'raw_command':command,'exit_code':result.returncode,
         'stdout':result.stdout,'stderr':result.stderr,'probe_result':parsed,
         'predictor_wrapper_sha256':sha(wrapper),'execution_boundary_id':policy['execution_boundary_id'],
         'predictor_inputs_sha256':sha(pred),'scorer_inputs_sha256':sha(scorer),'runtime_binding_sha256':sha(runtime),
         'allowed_history_probe_passed':bool(parsed and parsed['attempts'][0]['pass']),
         'denied_outcome_probe_passed':bool(parsed and parsed['attempts'][1]['pass']),
         'full_archive_unavailable':bool(parsed and parsed['attempts'][2]['pass']),
         'actual_open_tests_passed':bool(parsed and parsed['passed']),
         'production_acceptance':False,'compute_node_tested':False,'gpu_job_submitted':False,'real_data_read':False}
(BASE/'FIXTURE_PROBE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
sys.exit(0 if receipt['actual_open_tests_passed'] else 2)
