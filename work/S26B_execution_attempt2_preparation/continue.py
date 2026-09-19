"""Explicit second launch envelope after pre-data stdlib import failure.

Original frozen runner/scorer and original FAILED dispatch/import are retained.
The only execution adaptation is pre-importing Python's importlib.util before
the unchanged worker script. Original GA math, seeds, inputs and paths remain.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ATTEMPT=ROOT/'work/S26B_execution_attempt2'
PARENT=ROOT/'work/S26B_preparation/run_manifest.json'
RUNNER=ROOT/'scripts/s26b_consumer_baseline.py'
SCORER=ROOT/'scripts/score_s26b_consumer.py'
BOOTSTRAP="import importlib.util, runpy, sys; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')"
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def now():return datetime.now(timezone.utc).isoformat()
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    contract=read(HERE/'contract.json')
    assert contract['bootstrap']==BOOTSTRAP and contract['status']=='FROZEN'
    for p,h in contract['identities'].items():assert sha(p)==h,p
    assert not ATTEMPT.exists(),'Explicit attempt may run only once'
    assert not (ROOT/'results/S26B_consumer_baseline').exists(),'Previous attempt must have produced no scientific outputs'
    old=read(ROOT/'work/S26B_execution/dispatch_receipt.json')
    assert old['status']=='FAILED' and old['phases']==[]
    assert read(ROOT/'work/S24_execution/dispatch_receipt.json')['status']=='PASS'
    spec=importlib.util.spec_from_file_location('frozen_s26b_supervisor',RUNNER)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    runner.manifest(contract['parent_manifest_sha256'])
    # Reuse only the unchanged resource supervisor in the caller process.
    # Child runpy loads a fresh unchanged runner with its original WORK/OUT.
    runner.WORK=ATTEMPT
    ATTEMPT.mkdir()
    receipt=dict(status='RUNNING',started_utc=now(),parent_manifest_sha256=sha(PARENT),
        envelope_contract_sha256=sha(HERE/'contract.json'),phases=[],
        prior_dispatch_status='FAILED_PRESERVED',adaptation='Explicit standard-library importlib.util bootstrap; original child globals/code unchanged')
    write(ATTEMPT/'receipt.json',receipt)
    try:
        for phase,seconds,gib in [('import',120,2),('cut3r',1200,16),('ttt3r',1200,16),('filt3r',1200,16)]:
            command=[sys.executable,'-c',BOOTSTRAP,str(RUNNER),'worker','--phase',phase,'--manifest-sha256',contract['parent_manifest_sha256']]
            runner.supervised(command,phase,seconds,gib*1024**3)
            receipt['phases'].append(phase);write(ATTEMPT/'receipt.json',receipt)
        runner.supervised([sys.executable,str(SCORER),'score','--manifest',str(PARENT),'--manifest-sha256',contract['parent_manifest_sha256']],'scoring',180,2*1024**3)
        receipt['phases'].append('scoring')
        for p,h in contract['identities'].items():assert sha(p)==h,p
        receipt.update(status='PASS',completed_utc=now(),old_failure_preserved=True)
    except BaseException as exc:
        receipt.update(status='FAILED',failed_utc=now(),error=repr(exc));write(ATTEMPT/'receipt.json',receipt);raise
    write(ATTEMPT/'receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
