"""Sequential continuation: require completed S21 callers before S22 compute."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/S22_filt_preparation/continuation.json'
assert not OUT.exists()
r=dict(started_utc=datetime.now(timezone.utc).isoformat(),status='WAITING_FOR_S21')
def save():OUT.write_text(json.dumps(r,indent=2)+'\n')
save();start=time.monotonic()
while True:
    statuses=[]
    for mode in ['cut3r','ttt3r']:
        p=ROOT/'work/S21_execution'/mode/'receipt.json'
        try:statuses.append(json.loads(p.read_text())['status'])
        except (FileNotFoundError,json.JSONDecodeError):statuses.append('WAITING')
    if 'FAILED'in statuses:raise RuntimeError('S21 failed; no automatic S22 execution')
    if statuses==['PASS','PASS']:break
    if time.monotonic()-start>1800:raise TimeoutError('S21 wait limit; inspect actual processes')
    time.sleep(3)
r.update(status='S22_DISPATCH_STARTED',started_models_utc=datetime.now(timezone.utc).isoformat());save()
q=subprocess.run([sys.executable,str(ROOT/'scripts/s22_filt_baseline.py'),'dispatch'],cwd=ROOT)
r.update(status='PASS'if q.returncode==0 else'FAILED',returncode=q.returncode,completed_utc=datetime.now(timezone.utc).isoformat());save()
raise SystemExit(q.returncode)
