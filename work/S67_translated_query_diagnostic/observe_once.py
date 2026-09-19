"""Run one reviewed fixed diagnostic with an actual bounded external receipt."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import time

D=Path(__file__).resolve().parent
R=D.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv)==2, 'Delivered source-review SHA required'
assert sha(D/'diagnose.py')=='4a6c2e5d6438346ed4a83743cef4ca462b9bc7cf44c0c6b6d2a186ee37d5b4bc'
assert sha(D/'AUTHOR_DELIVERY.json')=='597cd12cd9bf14b16ca402619a36a49914cb5293e78f3d0bde4f13a1b694cd4a'
assert sha(D/'SOURCE_REVIEW.json')==sys.argv[1]
review=json.loads((D/'SOURCE_REVIEW.json').read_text())
assert review['status'].startswith('PASS') and not review.get('blockers')
for item in json.loads((D/'AUTHOR_DELIVERY.json').read_text())['files'].values():
    assert sha(Path(item['path']))==item['sha256']
assert not (D/'execution_01').exists()
out=D/'external_01';out.mkdir(exist_ok=False)
argv=[str(R/'.venv-cut3r/bin/python'),'-B',str(D/'diagnose.py')]
sys.path.insert(0,str(R/'scripts'));from research_log import append_event
started=datetime.now(timezone.utc).isoformat();t0=time.monotonic();timed_out=False
with (out/'stdout.txt').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
    child=subprocess.Popen(argv,cwd=R,stdout=stdout,stderr=stderr)
    start=dict(started_utc=started,argv=argv,pid=child.pid,source_sha256=sha(D/'diagnose.py'),
               source_review_sha256=sys.argv[1],observer_source_sha256=sha(Path(__file__)))
    (out/'started.json').write_text(json.dumps(start,ensure_ascii=False,indent=2)+'\n')
    append_event('S67一次固定配对诊断实际启动','使用已有环境，外控120秒；同query/不同径向depth，读取原小数值档案，无新模型/RGB/生成。以真实返回和不同作者核验判定。',[str((out/'started.json').relative_to(R))],'保留两臂全部结果或兼容性失败；不按结果调参数重跑。')
    try:
        code=child.wait(timeout=120)
    except subprocess.TimeoutExpired:
        timed_out=True;child.kill();code=child.wait(timeout=10)
receipt=dict(**start,completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-t0,
             returncode=code,external_timeout=timed_out,stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'))
result=D/'execution_01/receipt.json'
if result.is_file():
    receipt['worker_receipt_sha256']=sha(result)
    receipt['worker_status']=json.loads(result.read_text()).get('status')
with (out/'receipt.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
(out/'receipt.json').chmod(0o444)
append_event('S67固定诊断实际外部返回',f'returncode={code}, timeout={timed_out}, elapsed={receipt["elapsed_seconds"]:.6f}秒；终态={receipt.get("worker_status", "missing")}。原结果保留，不将return0自动当创新或收益。',[str((out/'receipt.json').relative_to(R))],'核实际两臂/兼容性与全部投影、ID/context证据，再做不同作者结果验证。')
print(json.dumps(receipt,ensure_ascii=False))
