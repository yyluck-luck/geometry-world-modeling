"""S76 one-arm observer. Reads reviewed bindings; no automatic retries or baseline rerun."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import traceback

D=Path(__file__).absolute().parent
R=D.parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    p.chmod(0o444)
def kill(child):
    if child.poll() is None:
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:raise RuntimeError('Stopped process not reaped within10seconds')

def main():
    if sys.argv[1:]==['--compile-only']:
        compile(Path(__file__).read_bytes(),__file__,'exec');print('COMPILE_ONLY_NO_EXECUTION');return 0
    binding=D/'ROOT_RUN_BINDING.json'
    need(len(sys.argv)==2 and sha(binding)==sys.argv[1],'Expected exact root run binding SHA')
    b=json.loads(binding.read_text());need(b['status']=='ACCEPTED_S76_SOURCE_SET','Exact source set not accepted')
    for path,h in b['reviewed_files_sha256'].items():need(sha(path)==h,'Reviewed source changed: '+path)
    c=json.loads((D/'RUN_CONTRACT.json').read_text());limits=c['limits']
    need(limits==dict(worker_seconds=3540,external_seconds=3600,rss_bytes=45*1024**3,minimum_free_bytes=10*1024**3),'Frozen resource limit differs')
    argv=[str(R/'.venv-cut3r/bin/python'),'-B',str(D/'run_single_yaw.py'),sha(D/'RUN_CONTRACT.json')]
    need(b['argv']==argv,'Bound argv differs')
    need(not (D/'execution_01').exists(),'Existing execution preserved')
    need(shutil.disk_usage(D).free>=limits['minimum_free_bytes'],'Insufficient free disk')
    import psutil
    sys.path.insert(0,str(R/'scripts'));from research_log import append_event
    out=D/'external_01';out.mkdir(exist_ok=False)
    env=os.environ.copy();env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',
        HF_HUB_DISABLE_IMPLICIT_TOKEN='1',TOKENIZERS_PARALLELISM='false',KORNIA_CHECK_VERSION='0',
        PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8')
    t=time.monotonic();started=utc();child=None;reason=None;error=None;peak=0;count=0
    try:
        with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr,(out/'monitor.jsonl').open('x') as monitor:
            child=subprocess.Popen(argv,cwd=R,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            save(out/'started.json',dict(started_utc=started,pid=child.pid,pgid=child.pid,argv=argv,
                binding_sha256=sys.argv[1],observer_sha256=sha(__file__),limits=limits,sample_interval_seconds=.5))
            append_event('S76单yaw相机响应实际启动','复用已接受S70 A0，仅新生成+5度目标yaw臂，保持图像网格实际随机流；外部1小时与采样RSS45GiB、磁盘10GiB守卫。',
                         ['work/S76_relative_camera_response/external_01/started.json'],'真实返回后核完整随机流与条件，再评分全部四目标；不重跑A0。',occurred_at=started)
            while child.poll() is None:
                rss=0;pids=[]
                try:
                    parent=psutil.Process(child.pid)
                    for process in [parent]+parent.children(recursive=True):
                        try:rss+=process.memory_info().rss;pids.append(process.pid)
                        except psutil.NoSuchProcess:pass
                except psutil.NoSuchProcess:pass
                elapsed=time.monotonic()-t;free=shutil.disk_usage(D).free;peak=max(peak,rss);count+=1
                monitor.write(json.dumps(dict(utc=utc(),elapsed_seconds=elapsed,rss_bytes=rss,pids=pids,free_disk_bytes=free))+'\n');monitor.flush()
                if elapsed>=limits['external_seconds']:reason='WALL_TIME_LIMIT'
                elif rss>limits['rss_bytes']:reason='SAMPLED_PROCESS_TREE_RSS_LIMIT'
                elif free<limits['minimum_free_bytes']:reason='FREE_DISK_LIMIT'
                if reason:kill(child);break
                try:child.wait(timeout=.5)
                except subprocess.TimeoutExpired:pass
            code=child.wait()
    except BaseException as e:
        error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
        if child is not None:kill(child)
        code=None if child is None else child.returncode
        reason=reason or 'OBSERVER_ERROR'
    result=dict(started_utc=started,completed_utc=utc(),elapsed_seconds=time.monotonic()-t,
        returncode=code,stop_reason=reason,observer_error=error,monitor_samples=count,peak_sampled_process_tree_rss_bytes=peak,
        rss_scope='0.5 second live process-tree samples, not instantaneous RSS hard guarantee',binding_sha256=sys.argv[1])
    save(out/'receipt.json',result)
    append_event('S76单yaw进程实际返回',f"外部{result['elapsed_seconds']:.6f}秒，return{code}，停止原因{reason}；科学结论尚待保存量核验和四目标方向评分。",
        ['work/S76_relative_camera_response/external_01/receipt.json'],'保存失败或完整输出；不把执行器成功等同相机遵从/创新成立。',occurred_at=result['completed_utc'])
    print(json.dumps(result),flush=True)
    return 0 if code==0 and reason is None else 1

if __name__=='__main__':raise SystemExit(main())
