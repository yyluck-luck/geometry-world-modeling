"""Bind the exact reviewed source, metadata correction and one encoder invocation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

D=Path(__file__).resolve().parent
R=D.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv)==2
expected={
    'encode_history.py':'52c51abe34ff7911c89951788cf5253e6c14ddb87a9a34b0e28223e61c21d3a9',
    'PROTOCOL.md':'ebadb65cf19e8ef186fdd3a630a6f504a5ebdaa43ba9a2936ed1b9f896511ddd',
    'INPUTS.json':'f14621d1988566f0fb09d314e02e0736e352fbe0a49c1055249c0011a34454bc',
    'AUTHOR_CHECK.json':'a398c5e74c84cbdaab6c3d356970d666344baac92c0b2f953374bd83c96fa4bd',
    'AUTHOR_DELIVERY.json':'dfcca08e06cce42f7a86ca5420c25a37ea54e6adc917e8343b7d2d058f308159',
    'ARGV_CORRECTION.json':'fa4125ab3bc507abc196f5a0291c6086790a7b74c83c884af4410cefcd7295d8',
    'SOURCE_REVIEW.json':sys.argv[1],
}
for name,value in expected.items():
    assert sha(D/name)==value,name
review=json.loads((D/'SOURCE_REVIEW.json').read_text())
assert review['status'].startswith('PASS') and not review.get('blockers')
correction=json.loads((D/'ARGV_CORRECTION.json').read_text())
argv=[str(R/'.venv-cut3r/bin/python'),'-B',str(D/'encode_history.py')]
assert correction['corrected_argv']==argv
assert not (D/'execution_01').exists() and not (D/'external_01').exists()
record={'bound_utc':datetime.now(timezone.utc).isoformat(),'status':'BOUND_ONE_REVIEWED_COMPONENT_RUN',
        'reviewed_files_sha256':{str(D/name):value for name,value in expected.items()},
        'argv':argv,'body_history_ids':[12,13,14,18,19],
        'worker_output_directory':str(D/'execution_01'),
        'worker_receipt_path':str(D/'execution_01/receipt.json'),
        'novelty_authorization':'NONE','new_method_validated':False,
        'scope':'Only five historical RGB appearances encoded; not online retrieval, full camera state or video.'}
with (D/'ROOT_RUN_BINDING.json').open('x') as f:
    json.dump(record,f,ensure_ascii=False,indent=2)
    f.write('\n')
(D/'ROOT_RUN_BINDING.json').chmod(0o444)
print(sha(D/'ROOT_RUN_BINDING.json'))
