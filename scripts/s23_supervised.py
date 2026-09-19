"""Resource-bounded S23 launcher; also records the pre-access boundary."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, sys, time
import psutil

root=Path(__file__).resolve().parents[1]
out=root/'work/S23_geometry_execution';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def save(name,x):(out/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
inputs=[root/'work/S23_geometry_preparation/manifest.json',
        root/'work/S21_baseline_preparation/run_manifest.json',
        root/'work/S23_innovation_2_geometry/s23_pre_review_v2.json',Path(__file__)]
contract=dict(frozen_utc=utc(),identities={str(p):sha(p)for p in inputs},
              max_seconds=900,max_tree_rss=8*2**30,
              boundary='GT depth access may occur any time after child launch; its initial gt_png_read=false record is only a before-read snapshot, not evidence of no reads after interruption.')
save('launch_contract.json',contract)
cmd=[sys.executable,str(root/'scripts/s23_geometry_diagnostic.py'),'run']
start=time.perf_counter();peak=0;status='RUNNING'
with (out/'stdout.txt').open('w')as stdout,(out/'stderr.txt').open('w')as stderr:
    child=subprocess.Popen(cmd,cwd=root,stdout=stdout,stderr=stderr)
    save('receipt.json',dict(status=status,pid=child.pid,started_utc=utc(),command=cmd,gt_access_may_have_started=True))
    while child.poll() is None:
        try:
            p=psutil.Process(child.pid);rss=p.memory_info().rss+sum(c.memory_info().rss for c in p.children(recursive=True));peak=max(peak,rss)
        except psutil.Error:pass
        if time.perf_counter()-start>contract['max_seconds'] or peak>contract['max_tree_rss']:
            status='RESOURCE_LIMIT';child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()
            break
        time.sleep(.25)
    if status=='RUNNING':status='PASS' if child.returncode==0 else 'FAILED'
save('receipt.json',dict(status=status,returncode=child.returncode,elapsed_seconds=time.perf_counter()-start,peak_tree_rss=peak,completed_utc=utc(),gt_access_may_have_started=True,launch_contract_sha256=sha(out/'launch_contract.json')))
print(json.dumps(dict(status=status,seconds=time.perf_counter()-start,peak_tree_rss=peak)))
sys.exit(0 if status=='PASS' else 1)
