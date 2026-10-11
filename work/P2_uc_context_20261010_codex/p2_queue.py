"""Wait without allocating GPU; yield to existing owner research chains."""
import datetime
import json
import subprocess
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PY='/mnt/gluster_dcpu/yiyangliu/gwm_s134/env/bin/python'
start=time.monotonic();clear=0
while time.monotonic()-start<86400:
    sessions=subprocess.run(['tmux','list-sessions','-F','#S'],capture_output=True,text=True).stdout.splitlines()
    reserved=any(x.startswith(('s143','s144','s145','s146','s147','s148','s149')) for x in sessions)
    procs=subprocess.check_output(['ps','-u','yiyangliu','-o','args='],text=True).splitlines()
    reserved=reserved or any('/src/s14' in x and not x.lstrip().startswith(('tmux ', 'tee '))
        and any(y in x for y in ['gen_','run_retrieval','chain.sh']) for x in procs)
    gpu=subprocess.check_output(['nvidia-smi','-i','3','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
    mem,util=map(int,gpu.split(','));idle=not reserved and mem<100 and util<5
    clear=clear+1 if idle else 0
    (ROOT/'QUEUE_STATUS.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'READY' if clear>=2 else 'WAITING_EXISTING_OWNER_JOBS_OR_GPU','sessions':sessions,
        'reserved_owner_chain':reserved,'gpu3_memory_MiB':mem,'gpu3_utilization':util,'consecutive_idle_checks':clear})+'\n')
    if clear>=2:
        p=subprocess.run([PY,str(ROOT/'run_experiment.py')])
        (ROOT/'RUN_EXIT_CODE.txt').write_text(str(p.returncode)+'\n')
        raise SystemExit(p.returncode)
    time.sleep(120)
(ROOT/'RESULT.json').write_text(json.dumps({'status':'BLOCKED_CAPACITY','reason':'24h queue wait exhausted; no GPU allocated.'})+'\n')
