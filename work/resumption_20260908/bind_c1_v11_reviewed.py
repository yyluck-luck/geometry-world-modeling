"""Bind the existing V11 camera-only contract after both actual source reviews."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = ROOT / 'work/S45B_c1_numeric_camera_guard_supervised_v11'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
frozen = D / 'FROZEN_SOURCE_SET.json'
assert sha(frozen) == sys.argv[1]
out = D / 'C1_CAMERA_GUARD_BINDING_V11.json'
assert not out.exists()
binding = read(D / 'C1_CAMERA_GUARD_BINDING_TEMPLATE.json')
review_files = [('primary', 'SOURCE_REVIEW_PRIMARY_V11.json', '/root/figure_repo_reading_resume'),
                ('adversarial', 'SOURCE_REVIEW_ADVERSARIAL_V11.json', '/root/c1_v11_adversarial_review')]
reviews = []
for index, (kind, name, role) in enumerate(review_files):
    p = D / name
    assert sha(p) == sys.argv[index + 2], name
    doc = read(p)
    assert doc['status'] == 'PASS_S45B_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_SOURCE_REVIEW_V11'
    assert doc['verdict'] == 'PASS_SUPERVISED_SOURCE_NOT_EXECUTED'
    assert doc['review_kind'] == kind and doc['reviewer_role'] == role
    assert doc['author_role'] == '/root/execution_resumption_audit'
    assert doc['blocking_findings'] == [] and doc['executed'] is False
    assert doc['c1_tensor_bodies_read'] == doc['pixels_decoded'] == doc['images_viewed'] == 0
    reviews.append(doc)
    binding['source_set'][kind + '_source_review'] = sha(p)
assert reviews[0]['reviewed_identities'] == reviews[1]['reviewed_identities']
for name in ('camera_guard.py', 'supervise_camera_guard.py', 'PROTOCOL.md',
             'C1_CAMERA_GUARD_BINDING_TEMPLATE.json', 'synthetic_selftest.py'):
    digest = sha(D / name)
    assert digest in reviews[0]['reviewed_identities'].values(), name
    binding['source_set'][name] = digest
for name, item in binding['upstream'].items():
    digest = sha(Path(item['path']))
    if item['sha256'] is not None: assert item['sha256'] == digest, name
    item['sha256'] = digest
now = datetime.now(timezone.utc).isoformat()
assert all(datetime.fromisoformat(r['completed_utc']) <= datetime.fromisoformat(now) for r in reviews)
binding.update(schema='s45b-c1-numeric-camera-guard-binding-v4',
    status='FROZEN_C1_NUMERIC_CAMERA_GUARD_SUPERVISED_INPUT_BINDING_V11',
    placeholder_hashes=0, author_role='/root', author_task_id='/root',
    author_turn_id='c1-v11-actual-binding-' + now, created_utc=now,
    purpose='Exact V11 five-source, two fresh actual source-review, and ten upstream text identities. Independent binding review and existing governance attestation remain required before camera-only execution.')
with out.open('x') as f:
    json.dump(binding, f, ensure_ascii=False, indent=2); f.write('\n')
out.chmod(0o444)
sys.path.insert(0, str(ROOT / 'scripts'))
from research_log import append_event
append_event('C1 V11按两名真实非作者源码审查建立唯一绑定',
    'root作为独立于源码作者和两名源码审查者的绑定作者，核五源、双票与十份已有上游文本身份。尚无正式guard、相机张量正文或像素访问。',
    [str(out.relative_to(ROOT)), 'sha256=' + sha(out)],
    '交由另一真实agent核绑定；通过后按既定监督入口执行一次相机数值检查。')
print(json.dumps({'binding': str(out), 'sha256': sha(out), 'created_utc': now}))
