"""Render the existing S46 contract only after a delivered numeric result review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import runpy
import subprocess
import sys

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = R / 'work/S46_c1_blind_scoring_preparation'
W = R / 'work/S46_c1_blind_scoring_wrapper_v3'
N = R / 'work/S45B_c1_numeric_camera_guard_supervised_v12/INDEPENDENT_RESULT_REVIEW_V12.json'
WSHA = '3c8f931da47403cd5b249a6680790107136ffea0267f871679e77e7b27150463'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p, value):
    with p.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
    p.chmod(0o444)

assert len(sys.argv) == 2 and sha(N) == sys.argv[1]
assert sha(W / 'score_c1_blind_wrapper.py') == WSHA
assert sha(D / 'bind_identity_only.py') == '32f80b585ab8e511a64df08c8bb230e1a03835cf6ec33f98c6e8d2a80175ee60'
namespace = runpy.run_path(str(W / 'score_c1_blind_wrapper.py'), run_name='s46_identity_only_context')
real = namespace['validate_current_real_metadata']()
assert real['body_bytes_read'] == 0
numeric_record = {'path': str(N), 'sha256': sha(N)}
namespace['validate_numeric_review'](numeric_record, real['identities'])
now = datetime.now(timezone.utc).isoformat()
numeric = json.loads(N.read_text())
assert datetime.fromisoformat(numeric['completed_utc']) <= datetime.fromisoformat(now)
input_path = D / 'C1_UPSTREAM_IDENTITY_BINDING.json'
contract_path = D / 'C1_SCORING_BOUND_CONTRACT.json'
assert not input_path.exists() and not contract_path.exists()
assert not namespace['OUTPUT'].exists()
records = [dict(label=label, path=str(item['path']), sha256=item['sha256'],
                expected_json_fields=item['fields']) for label,item in namespace['FIXED_UPSTREAM'].items()]
fields = {('/'+key): numeric[key] for key in ('schema','status','row','passed','requested_pose_K_guard_pass',
          'numeric_guard_terminal_schema','numeric_guard_terminal_status','numeric_guard_terminal_authority',
          'observed_supervisor_returncode','pixels_decoded','images_viewed')}
fields.update({('/row_validity_assertions/'+key): True for key in namespace['REQUIRED_VALIDITY']})
records.append(dict(label='row_validity_review', **numeric_record, expected_json_fields=fields))
binding = dict(schema='s46-c1-upstream-identity-binding-v1',
    status='READY_TO_BIND_C1_IDENTITIES_AFTER_INDEPENDENT_READBACK',row='C1',completed_utc=now,
    upstream_records=records,authorized_attempt=1,authorized_output_path=str(namespace['OUTPUT']),
    authoritative_pixel_identities=real['identities'],archive_tensor_directory=str(namespace['TENSOR_DIR']),
    pixel_identity_source_record_label='row_validity_review',pixel_identities_json_pointer='/authoritative_pixel_identities',
    row_validity_assertions_json_pointer='/row_validity_assertions')
write_new(input_path,binding)
argv=['/opt/homebrew/bin/python3','-I','-B','-S',str(D/'bind_identity_only.py'),
      '--kind','score','--binding',str(input_path),'--out',str(contract_path)]
run=subprocess.run(argv,capture_output=True,text=True,timeout=30)
assert run.returncode == 0, (run.returncode,run.stdout,run.stderr)
contract_path.chmod(0o444)
namespace['validate_contract']({'bound_contract':{'path':str(contract_path),'sha256':sha(contract_path)},
                              'numeric_guard_independent_review':numeric_record},real['identities'])
receipt=dict(completed_utc=datetime.now(timezone.utc).isoformat(),returncode=run.returncode,
    argv=argv,stdout=run.stdout,stderr=run.stderr, numeric_review=numeric_record,
    identity_binding={'path':str(input_path),'sha256':sha(input_path)},
    bound_contract={'path':str(contract_path),'sha256':sha(contract_path)},
    real_pixel_body_bytes_read=0,images_viewed=0,model_calls=0,scorer_calls=0,
    scope='IDENTITY_BINDING_ONLY_AFTER_FINAL_INDEPENDENT_V12_RESULT; dual review and blindness still required')
out=R/'work/resumption_20260908/S46_C1_CONTRACT_BINDING_OBSERVATION.json'
write_new(out,receipt)
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('C1真实数值独立结果通过后绑定既有盲评分合同',
    '先核最终V12结果票、七份已有JSON和九sidecar，再用原identity-only binder建立attempt01合同；冻结数学与原像素身份保持。尚未评分或看图。',
    [str(out.relative_to(R)),str(contract_path.relative_to(R))],
    '两名独立审查者按exact scorer、wrapper、合同和S42规则审查，再如实形成盲态证明并运行唯一评分。')
print(json.dumps(receipt,ensure_ascii=False))
