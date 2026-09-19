"""Root orchestration: exact V7 dual review, then the existing unique prepare."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = ROOT / 'work/S47_c2_confirmation_generation'
OUT = ROOT / 'work/resumption_20260908/C2_V7_PREPARE_ORCHESTRATION.json'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
candidate = D / 'CANDIDATE_STATIC_SELFTEST_V7.json'
assert sha(candidate) == '55f69c0c03b4692db9471a98ddeb2d3715e5691422501210a528d7d72706d79f'
pins = json.loads(candidate.read_text())['production_candidate_sha256']
reviews = []
for kind, digest in [('PRIMARY', '0833ab0bd99a67cd9ac87433634e1104e87605e7d2f78e89e7133847c2071c5c'), ('ADVERSARIAL', '79309c1ab195bea8c34c57795ef16750548c5c14979cb9031728da7605fbd1de')]:
    path = D / f'SOURCE_REVIEW_{kind}_V7.json'
    assert sha(path) == digest
    review = json.loads(path.read_text())
    assert review['status'] == f'PASS_S47_C2_V7_{kind}_SOURCE_REVIEW'
    assert review['blocking_findings'] == []
    assert {k: v['sha256'] for k, v in review['reviewed_files'].items()} == pins
    reviews.append(review)
assert len({r['reviewer_role'] for r in reviews} | {'/root/c2_generation_builder'}) == 3
for name, digest in pins.items():
    assert sha(D / name) == digest, name
argv = ['/opt/homebrew/bin/python3', '-I', '-B', '-S', str(D / 'freeze_c2_manifest.py'), '--mode', 'prepare', '--out', str(D / 'freeze_attempt_01')]
start = datetime.now(timezone.utc).isoformat()
run = subprocess.run(argv, cwd='/private/tmp', capture_output=True, text=True, timeout=600)
receipt = dict(started_utc=start, completed_utc=datetime.now(timezone.utc).isoformat(), argv=argv, returncode=run.returncode, stdout=run.stdout, stderr=run.stderr, verified_source_sha256=pins, scope='EXACT_REVIEW_THEN_EXISTING_PREPARE_ONLY_NOT_GENERATION', model_runs=0)
OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
sys.path.insert(0, str(ROOT / 'scripts'))
from research_log import append_event
append_event('C2 V7双独立源码票后执行既定唯一prepare', f'root重核八源与两票的精确SHA及不同作者身份，执行原有freeze工具，returncode={run.returncode}。准备包仅固定输入和运行条件，非模型生成；若失败保留原路径不自动重试。', [str(OUT.relative_to(ROOT)), 'work/S47_c2_confirmation_generation/freeze_attempt_01'], '按实际终端结果审查prepare核心，再接续既定附件流程。')
print(json.dumps(dict(returncode=run.returncode, stdout=run.stdout[-2500:], stderr=run.stderr[-2500:], receipt=str(OUT)), ensure_ascii=False))
