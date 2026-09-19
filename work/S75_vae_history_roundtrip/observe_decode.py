"""Bounded single local decode run; sampled process-tree memory monitor."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

D=Path(__file__).absolute().parent
R=D.parents[1]
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
def utc():return datetime.now(timezone.utc).isoformat()
def save(p,r):
    with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    p.chmod(0o444)

def main():
    review=json.loads((D/'ROOT_SOURCE_REVIEW.json').read_text())
    assert review['status']=='PASS_ROOT_INDEPENDENT_S75_SOURCE_REVIEW' and not review['blockers']
    for n,h in review['files_sha256'].items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h,n
    c=json.loads((D/'CONTRACT.json').read_text())
    assert not (D/'execution_01').exists()
    E=D/'external_01';E.mkdir(exist_ok=False)
    cmd=[str(R/'.venv-cut3r/bin/python'),'-B',str(D/'decode_history.py'),review['files_sha256']['CONTRACT.json']]
    append_event('S75五历史VAE解码实际启动','五已存latent只decode，原CPU8FP32wrapper；无encode/CLIP/VMem/采样。外部180秒与30GiB采样进程树RSS停止，每0.5秒采样，不声称瞬时硬内存保证。',['work/S75_vae_history_roundtrip/ROOT_SOURCE_REVIEW.json'],'实际返回后不同作者读取保存像素和匹配坐标复算。')
    start=time.monotonic();started=utc();peak=0;samples=0;stop_reason=None
    with (E/'stdout.txt').open('x') as out,(E/'stderr.txt').open('x') as err,(E/'monitor.jsonl').open('x') as monitor:
        p=subprocess.Popen(cmd,stdout=out,stderr=err,cwd=R,start_new_session=True)
        save(E/'started.json',dict(started_utc=started,pid=p.pid,pgid=p.pid,argv=cmd,
            wall_seconds=c['limits']['external_seconds'],sampled_tree_rss_limit=c['limits']['rss_bytes'],
            sample_interval_seconds=.5,supervisor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
        while p.poll() is None:
            proc=subprocess.run(['ps','-axo','pid=,ppid=,rss='],capture_output=True,text=True,check=True)
            rows={int(a):(int(b),int(m)*1024) for line in proc.stdout.splitlines() if len(parts:=line.split())==3 for a,b,m in [parts]}
            tree={p.pid};previous=set()
            while previous!=tree:
                previous=tree.copy();tree.update(pid for pid,(parent,_) in rows.items() if parent in tree)
            rss=sum(rows[pid][1] for pid in tree if pid in rows);peak=max(peak,rss);samples+=1
            elapsed=time.monotonic()-start
            monitor.write(json.dumps(dict(utc=utc(),elapsed_seconds=elapsed,pids=sorted(tree),rss_bytes=rss))+'\n');monitor.flush()
            if elapsed>=c['limits']['external_seconds']:stop_reason='WALL_TIME_LIMIT'
            elif rss>c['limits']['rss_bytes']:stop_reason='SAMPLED_TREE_RSS_LIMIT'
            if stop_reason:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                break
            try:p.wait(timeout=.5)
            except subprocess.TimeoutExpired:pass
        rc=p.wait()
    result=dict(started_utc=started,completed_utc=utc(),elapsed_seconds=time.monotonic()-start,
        returncode=rc,stop_reason=stop_reason,monitor_samples=samples,peak_sampled_process_tree_rss_bytes=peak,
        rss_scope='Periodic live RSS sum, not instantaneous peak guarantee; worker records macOS peak self RSS separately.')
    save(E/'receipt.json',result)
    append_event('S75五历史VAE解码进程返回',f"外部{result['elapsed_seconds']:.6f}秒，return{rc}，停止原因{stop_reason}；已保存实际输出，五图完整性和指标待复核。",['work/S75_vae_history_roundtrip/external_01/receipt.json','work/S75_vae_history_roundtrip/execution_01/receipt.json'],'完整查看返回行，再不同作者复算保存像素/坐标。')
    print(json.dumps(result));print((E/'stdout.txt').read_text());print((E/'stderr.txt').read_text())
    return 0 if rc==0 and stop_reason is None else 1

if __name__=='__main__':raise SystemExit(main())
