"""Bound one explicit reviewed measurement and retain the actual external exit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import time

D = Path(__file__).resolve().parent
R = D.parents[1]
SOURCE_SHA = '55ab15381fb745f37af68a0978bb59c9d00e2ff1fa1870c969a3850aa117744a'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv) >= 3
mode, review_sha = sys.argv[1:3]
assert mode in ('camera', 'score', 'recompute')
assert sha(D/'measure.py') == SOURCE_SHA
assert sha(D/'SOURCE_REVIEW.json') == review_sha
extras = sys.argv[3:]
flags = {'camera': [], 'score': ['--camera-review', '--camera-review-sha256'],
         'recompute': ['--score-receipt-sha256', '--score-report-sha256']}[mode]
assert extras[::2] == flags and len(extras) == 2*len(flags)
out = D/('external_'+mode+'_01')
out.mkdir(exist_ok=False)
argv = [str(R/'.venv-cut3r/bin/python'), '-B', str(D/'measure.py'),
        '--mode', mode, '--source-sha256', SOURCE_SHA, *extras]
sys.path.insert(0, str(R/'scripts'))
from research_log import append_event
start = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
timed_out = False
with (out/'stdout.txt').open('xb') as stdout, (out/'stderr.txt').open('xb') as stderr:
    child = subprocess.Popen(argv, cwd=R, stdout=stdout, stderr=stderr)
    initial = dict(started_utc=start, mode=mode, argv=argv, pid=child.pid,
                   source_review_sha256=review_sha, observer_source_sha256=sha(Path(__file__)))
    (out/'started.json').write_text(json.dumps(initial, ensure_ascii=False, indent=2)+'\n')
    append_event('S66实际执行 '+mode, '一次明确mode已启动；外控120秒，使用已有环境，0模型/图像显示。结果以实际返回与不同作者复核为准。',
                 [str((out/'started.json').relative_to(R))], '保留真实退出、全部输出和失败；按相机、评分、独立复算顺序接续。')
    try:
        code = child.wait(timeout=120)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()
        code = child.wait(timeout=10)
receipt = dict(**initial, completed_utc=datetime.now(timezone.utc).isoformat(),
               elapsed_seconds=time.monotonic()-t0, returncode=code, external_timeout=timed_out,
               stdout_sha256=sha(out/'stdout.txt'), stderr_sha256=sha(out/'stderr.txt'))
receipt['sealed_outputs'] = {}
for name in ('report.json', 'receipt.json'):
    path = D/(mode+'_01')/name
    if path.is_file():
        path.chmod(0o444)
        receipt['sealed_outputs'][str(path)] = sha(path)
with (out/'receipt.json').open('x') as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
(out/'receipt.json').chmod(0o444)
append_event('S66外部返回 '+mode, f'returncode={code}，elapsed={receipt["elapsed_seconds"]:.6f}秒，timeout={timed_out}；已有report/receipt封存。',
             [str((out/'receipt.json').relative_to(R))], '核实际产物并完成相应不同作者验证，不据return0自动作科学结论。')
print(json.dumps(receipt, ensure_ascii=False))
