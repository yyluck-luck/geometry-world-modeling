"""One fresh-process startup probe; only --help, no manifest/data/GA entry."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    candidate=HERE/'contract_candidate.json'
    expected='f5f02d45a461c1d9448aad517a760c9550214676ded121f7cac0c553d5014598'
    assert sha(candidate)==expected
    c=json.loads(candidate.read_bytes())
    for p,h in c['identities'].items():assert sha(p)==h,p
    tree=ast.parse((HERE/'continue.py').read_text())
    assigned=[n.value for n in tree.body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='BOOTSTRAP' for t in n.targets)]
    assert len(assigned)==1 and ast.literal_eval(assigned[0])==c['bootstrap']
    runner=ROOT/'scripts/s26b_consumer_baseline.py'
    python=ROOT/'.venv-cut3r/bin/python'
    command=[str(python),'-c',c['bootstrap'],str(runner),'--help']
    started=datetime.now(timezone.utc).isoformat();start=time.monotonic()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=20)
    assert result.returncode==0 and '--manifest-sha256' in result.stdout and '{dispatch,worker}' in result.stdout
    assert result.stderr==''
    for p,h in c['identities'].items():assert sha(p)==h,p
    assert not (ROOT/'results/S26B_consumer_baseline').exists()
    assert sorted(p.name for p in (ROOT/'work/S26B_execution').iterdir())==['dispatch_receipt.json','import']
    stdout=HERE/'bootstrap_help_stdout.txt';stderr=HERE/'bootstrap_help_stderr.txt'
    assert not stdout.exists() and not stderr.exists()
    stdout.write_text(result.stdout);stderr.write_text(result.stderr)
    receipt={'status':'PASS_HELP_STARTUP_ONLY','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
             'wall_seconds':time.monotonic()-start,'command':command,'returncode':result.returncode,
             'candidate_sha256':expected,'input_identities_before_after':c['identities'],
             'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr),'original_failure_and_no_outputs_preserved':True,
             'real_array_reads':0,'sensor_GT_reads':0,'real_imports':0,'model_runs':0,'GA_runs':0,
             'scope':'Exact frozen bootstrap in a fresh target-Python process, unchanged runner --help only; importer and numerical compatibility are not rerun.'}
    target=HERE/'bootstrap_help_receipt.json';assert not target.exists();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'wall_seconds':receipt['wall_seconds'],'receipt_sha256':sha(target)}))


if __name__=='__main__':main()
