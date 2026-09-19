"""Root orchestration: exact V9 dual review, then the existing unique prepare."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = ROOT / 'work/S47B_c2_confirmation_generation_v9'
OUT = ROOT / 'work/resumption_20260909/C2_V9_PREPARE_ORCHESTRATION.json'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
candidate = D / 'CANDIDATE_STATIC_SELFTEST_V9.json'
assert sha(candidate) == 'aa3f9e4280494590e416446c128e004547afc0e9ec180e35f6f99ce411296fac'
pins = json.loads(candidate.read_text())['production_candidate_sha256']
reviews = []
for kind, digest in [('PRIMARY', sys.argv[1]), ('ADVERSARIAL', sys.argv[2])]:
    path = D / f'SOURCE_REVIEW_{kind}_V9.json'
    assert sha(path) == digest
    review = json.loads(path.read_text())
    assert review['status'] == f'PASS_S47_C2_V9_{kind}_SOURCE_REVIEW'
    assert review['blocking_findings'] == []
    assert {k: v['sha256'] for k, v in review['reviewed_files'].items()} == pins
    reviews.append(review)
assert len({r['reviewer_role'] for r in reviews} | {'/root/c2_v9_recovery_author'}) == 3
for name, digest in pins.items():
    assert sha(D / name) == digest, name
argv = ['/opt/homebrew/bin/python3', '-I', '-B', '-S', str(D / 'freeze_c2_manifest.py'), '--mode', 'prepare', '--out', str(D / 'freeze_attempt_01')]
start = datetime.now(timezone.utc).isoformat()
run = subprocess.run(argv, cwd='/private/tmp', capture_output=True, text=True, timeout=600)
receipt = dict(started_utc=start, completed_utc=datetime.now(timezone.utc).isoformat(), argv=argv, returncode=run.returncode, stdout=run.stdout, stderr=run.stderr, verified_source_sha256=pins, scope='EXACT_REVIEW_THEN_EXISTING_PREPARE_ONLY_NOT_GENERATION', model_runs=0)
OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
sys.path.insert(0, str(ROOT / 'scripts'))
from research_log import append_event
append_event('C2 V9双独立源码票后执行既定唯一prepare', f'root重核八源与两票的精确SHA及不同作者身份，执行原有freeze工具，returncode={run.returncode}。准备包仅固定输入和运行条件，非模型生成；若失败保留原路径不自动重试。', [str(OUT.relative_to(ROOT)), 'work/S47B_c2_confirmation_generation_v9/freeze_attempt_01'], '按实际终端结果审查prepare核心，再接续既定附件流程。')
print(json.dumps(dict(returncode=run.returncode, stdout=run.stdout[-2500:], stderr=run.stderr[-2500:], receipt=str(OUT)), ensure_ascii=False))
