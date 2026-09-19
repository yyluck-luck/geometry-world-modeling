#!/usr/bin/env python3
"""Launcher guard regression check; uses stub tmux, never calls SSH or Slurm."""
import hashlib, json, os, pathlib, subprocess, tempfile, datetime
ROOT=pathlib.Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
results=[]
with tempfile.TemporaryDirectory(prefix='gwm-launcher-test-') as raw:
    p=pathlib.Path(raw); bindir=p/'bin'; bindir.mkdir()
    stub=bindir/'tmux'
    stub.write_text('#!/bin/bash\nif [[ "$1" == has-session ]]; then exit 1; fi\nprintf "%s\\n" "$*" >> "$TMUX_TEST_CALLS"\n')
    stub.chmod(0o755)
    calls=p/'tmux_calls'; validator=p/'validator.py'; validator.write_text('raise SystemExit(0)\n')
    script=p/'job with spaces.slurm'; script.write_text('#!/bin/bash\nexit 0\n')
    contract=p/'contract.json'; contract.write_text('{}\n')
    manifest=p/'manifest.json'
    doc={'status':'FROZEN','gate0_contract_sha256':hashlib.sha256(contract.read_bytes()).hexdigest(),'sbatch_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest()}
    manifest.write_text(json.dumps(doc))
    env={**os.environ,'PATH':str(bindir)+':'+os.environ['PATH'],'GWM_GATE0_VALIDATOR':str(validator),'TMUX_TEST_CALLS':str(calls)}
    def check(name,args,expect,environment=env):
        run=subprocess.run(['bash',str(ROOT/'launch_formal_slurm_in_tmux.sh'),*map(str,args)],env=environment,text=True,capture_output=True)
        assert run.returncode==expect,(name,run.returncode,run.stderr,run.stdout)
        results.append({'name':name,'exit_code':run.returncode,'pass':True})
    args=['test-good',contract,manifest,script,p/'log with spaces.log']
    check('valid fixture reaches stub tmux once',args,0)
    assert calls.read_text().count('new-session')==1
    command=calls.read_text().strip().split('exec bash ',1)[1]
    subprocess.run(['bash','-n'],input='exec bash '+command,text=True,check=True)
    doc['sbatch_script_sha256']='0'*64; manifest.write_text(json.dumps(doc))
    check('changed script hash blocks dispatch',['test-hash',contract,manifest,script,p/'hash.log'],1)
    doc['status']='DRAFT'; manifest.write_text(json.dumps(doc))
    check('draft manifest blocks dispatch',['test-draft',contract,manifest,script,p/'draft.log'],1)
    actual_env={**env,'GWM_GATE0_VALIDATOR':str(PROJECT/'work/S102_gate0_tum/validate_gate0_contract.py')}
    blocked=PROJECT/'work/S102_gate0_tum/gate0_contract_v1.json'
    check('real blocked Gate0 stops before tmux',['test-blocked',blocked,manifest,script,p/'blocked.log'],4,actual_env)
    assert calls.read_text().count('new-session')==1
result={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'LOCAL_LAUNCHER_CONTROL_TEST_ONLY','ssh_calls':0,'slurm_submissions':0,'real_gpu_runs':0,'checks':results,'status':'PASS'}
(ROOT/'LAUNCHER_TEST_RECEIPT_20260916.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
