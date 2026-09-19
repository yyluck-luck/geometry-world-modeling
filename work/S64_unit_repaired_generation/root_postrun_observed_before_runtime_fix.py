"""Record one execution of the already independently reviewed S64 reader."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = R / 'work/S64_unit_repaired_generation'
O = D / 'external_postrun_readback_01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert len(sys.argv) == 3, 'Actual terminal-review path and SHA required'
review_path = Path(sys.argv[1]).resolve()
assert review_path.is_relative_to(D)
assert sha(review_path) == sys.argv[2]
assert sha(D/'POSTRUN_READBACK_DRAFT.py') == 'f750f88d7c203a32f9b33d4135970ce23112eb69467c6adfc44e7ce245b4b671'
assert sha(D/'POSTRUN_SOURCE_REVIEW.json') == '24da62b36ce1f3f6f3604c0ffec5fc1001609759f044afa58bd9c5dcd257f019'
manifest = D / 'review_attachment_01/manifest.json'
assert sha(manifest) == '34c2bad90c5627b6e9742fe65f8c8b4a1ff76da730a2c0d87bbcedcc38b28619'
external = D / 'external_launch_01/receipt.json'
commit = D / 'execution_01/supervisor_terminal_commit.json'
result = json.loads(external.read_text())
assert result['returncode'] == 0 and result['external_timeout'] is False
argv = ['/opt/homebrew/bin/python3', '-B', str(D/'POSTRUN_READBACK_DRAFT.py'),
        '--manifest-sha256', sha(manifest), '--external-receipt-sha256', sha(external),
        '--terminal-commit-sha256', sha(commit), '--out', str(D/'postrun_readback_01')]
O.mkdir(exist_ok=False)
sys.path.insert(0, str(R/'scripts'))
from research_log import append_event
start = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
timeout = False
with (O/'stdout.txt').open('xb') as out, (O/'stderr.txt').open('xb') as err:
    process = subprocess.Popen(argv, cwd=R, stdout=out, stderr=err)
    initial = dict(started_utc=start, argv=argv, pid=process.pid,
                   terminal_review_path=str(review_path), terminal_review_sha256=sys.argv[2])
    (O/'started.json').write_text(json.dumps(initial, ensure_ascii=False, indent=2)+'\n')
    append_event('开始一次已审S64结果读回', '实际完整外部返回和不同作者终态审查后，调用已审只读程序。将读取限定真实数值及RGB正文，0模型重算/图像显示/质量评分。',
                 [str((O/'started.json').relative_to(R))], '等待实际返回并独立核读回结果；不因prefix差异重跑模型。')
    try:
        code = process.wait(timeout=360)
    except subprocess.TimeoutExpired:
        timeout = True
        process.terminate()
        try:
            code = process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            code = process.wait(timeout=10)
receipt = dict(**initial, completed_utc=datetime.now(timezone.utc).isoformat(),
               elapsed_seconds=time.monotonic()-t0, returncode=code, external_timeout=timeout,
               stdout_sha256=sha(O/'stdout.txt'), stderr_sha256=sha(O/'stderr.txt'))
with (O/'receipt.json').open('x') as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
append_event('S64只读程序实际返回', f'外部returncode={code}，elapsed={receipt["elapsed_seconds"]:.6f}秒，timeout={timeout}。是否完成两批消费与prefix比较以结果及独立审查为准。',
             [str((O/'receipt.json').relative_to(R))], '保留全部产物，交由不同作者审查实际结果与读入清单。')
print(json.dumps(receipt, ensure_ascii=False))
