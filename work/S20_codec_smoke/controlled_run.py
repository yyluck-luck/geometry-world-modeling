"""External 60-second / 1-GiB RSS process-tree limit, codec smoke only."""
from pathlib import Path
import datetime, hashlib, json, os, signal, subprocess, time
import psutil
W=Path(__file__).resolve().parent
R=W.parents[1]
out=W/'caller_receipt.json'
assert not out.exists()
start=time.perf_counter()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
report={'schema':'s20-codec-external-caller-v1','status':'RUNNING','started_utc':utc(),'time_limit_seconds':60,'rss_limit_bytes':1073741824,'sampled_peak_process_tree_rss_bytes':0,'samples':0}
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8')
with (W/'worker.stdout.txt').open('x') as so,(W/'worker.stderr.txt').open('x') as se:
 p=subprocess.Popen([str(R/'.venv-cut3r/bin/python'),'-B',str(W/'codec_worker.py')],stdout=so,stderr=se,env=env,start_new_session=True)
 report['pid']=p.pid
 while p.poll() is None:
  rss=0
  try:
   proc=psutil.Process(p.pid)
   for q in [proc]+proc.children(recursive=True):
    try:rss+=q.memory_info().rss
    except psutil.Error:pass
  except psutil.Error:pass
  report['samples']+=1;report['sampled_peak_process_tree_rss_bytes']=max(report['sampled_peak_process_tree_rss_bytes'],rss)
  if time.perf_counter()-start>60 or rss>1073741824:
   report['limit_exceeded']='wall_time' if time.perf_counter()-start>60 else 'process_tree_rss'
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
   break
  time.sleep(.05)
 report['returncode']=p.wait()
report['ended_utc']=utc();report['elapsed_seconds']=time.perf_counter()-start
report['status']='PASS_EXTERNAL_LIMITS' if report['returncode']==0 and 'limit_exceeded' not in report else 'FAIL_EXTERNAL_OR_WORKER'
report['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
