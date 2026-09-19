"""Root orchestration for the existing single blind score, under one nonblocking lock.

No scoring mathematics live here. The unchanged V3 wrapper performs its own
exact source, metadata, blinding and body checks before calling the sealed kernel.
Only run after both actual final source reviews have been delivered to root.
"""
from pathlib import Path
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
import runpy
import stat
import subprocess
import sys

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
W = R / 'work/S46_c1_blind_scoring_wrapper_v3'
D = R / 'work/S46_c1_blind_scoring_preparation'
WSHA = '3c8f931da47403cd5b249a6680790107136ffea0267f871679e77e7b27150463'
LOCK = D / '.c1_score.lock'
OBS = R / 'work/resumption_20260908/S46_C1_FORMAL_ORCHESTRATION.json'

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def entry(p, expected):
    assert sha(p) == expected, str(p)
    return {'path': str(p), 'sha256': expected}
def write_new(p, value):
    with p.open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    p.chmod(0o444)

assert len(sys.argv) == 5, 'numeric_review_sha contract_sha primary_review_sha adversarial_review_sha'
assert not OBS.exists()
assert sha(W / 'score_c1_blind_wrapper.py') == WSHA
ns = runpy.run_path(str(W/'score_c1_blind_wrapper.py'),run_name='s46_readonly_pre_score_context')
numeric = entry(R/'work/S45B_c1_numeric_camera_guard_supervised_v12/INDEPENDENT_RESULT_REVIEW_V12.json',sys.argv[1])
contract = entry(D/'C1_SCORING_BOUND_CONTRACT.json',sys.argv[2])
primary = entry(W/'SOURCE_REVIEW_PRIMARY_V3.json',sys.argv[3])
adversarial = entry(W/'SOURCE_REVIEW_ADVERSARIAL_V3.json',sys.argv[4])
binding = dict(schema='s46-c1-blind-scoring-wrapper-execution-binding-v1',
    status='BOUND_C1_BLIND_SCORING_WRAPPER_EXECUTION_AWAITING_EXACT_GATE_VALIDATION',
    row='C1',completed_utc=utc(),wrapper={'path':str(W/'score_c1_blind_wrapper.py'),'sha256':WSHA},
    scorer={'path':str(ns['SCORER']),'sha256':ns['SCORER_SHA256']},bound_contract=contract,
    primary_source_review=primary,adversarial_source_review=adversarial,
    numeric_guard_independent_review=numeric,authorized_output_path=str(ns['OUTPUT']))

flags=os.O_RDWR|os.O_CREAT|os.O_CLOEXEC|os.O_NOFOLLOW
fd=os.open(LOCK,flags,0o600)
with os.fdopen(fd,'r+b') as held_lock:
    before=os.fstat(fd)
    assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock_acquired=utc()
    canonical=LOCK.lstat()
    assert (canonical.st_dev,canonical.st_ino) == (before.st_dev,before.st_ino)
    assert not ns['OUTPUT'].exists() and not (D/'.C1_score_attempt_01.staging').exists()
    assert not ns['BINDING'].exists()
    real=ns['validate_current_real_metadata']()
    assert real['body_bytes_read'] == 0
    ns['validate_numeric_review'](numeric,real['identities'])
    ns['validate_contract'](binding,real['identities'])
    reviews=ns['validate_source_reviews'](binding,Path(contract['path']),contract['sha256'],WSHA)
    excluded={'/root/c1_blind_score_builder','/root/execution_resumption_audit','/root/c2_v5_lifecycle_review'}
    assert reviews[0][1]['reviewer_role']=='/root/figure_repo_reading_resume'
    assert reviews[1][1]['reviewer_role']=='/root/s46_v3_adversarial_review'
    assert all(r[1]['reviewer_role'] not in excluded for r in reviews)
    # Root's actual pre-score observation: no C1 images or metrics have been viewed,
    # and the preregistered pair, ROI, metric and threshold remain unchanged.
    attestation=dict(schema='s46-c1-blindness-attestation-v1',status='PASS_S46_C1_BLINDNESS_PRE_SCORE',
        row='C1',created_utc=utc(),issuer_role='/root',issuer_task_id='/root',
        scorer_path=str(ns['SCORER']),scorer_sha256=ns['SCORER_SHA256'],
        bound_contract_path=contract['path'],bound_contract_sha256=contract['sha256'],
        primary_source_review_path=primary['path'],primary_source_review_sha256=primary['sha256'],
        adversarial_source_review_path=adversarial['path'],adversarial_source_review_sha256=adversarial['sha256'],
        authorized_attempt=1,authorized_output_path=str(ns['OUTPUT']),
        generated_images_or_montages_viewed=False,
        c1_tensor_or_image_payload_bodies_read_for_metric_selection=False,
        c1_metrics_observed_before_attestation=False,
        roi_pair_metric_or_threshold_changed_after_generation_started=False,
        observation_basis='Actual root and delegated-agent work in this task; public figure-repository sample images are not C1 experimental images. Prior numeric-only camera validation does not expose C1 pixels. This is an external human-readable provenance attestation, not cryptographic identity proof.')
    att_path=D/'C1_BLINDNESS_ATTESTATION.json'
    write_new(att_path,attestation)
    binding['blindness_attestation']={'path':str(att_path),'sha256':sha(att_path)}
    binding['completed_utc']=utc()
    ns['validate_blindness'](binding,Path(contract['path']),contract['sha256'],reviews,datetime.now(timezone.utc))
    write_new(ns['BINDING'],binding)
    argv=[str(R/'.venv-cut3r/bin/python'),'-I','-B',str(W/'score_c1_blind_wrapper.py'),
          '--binding-sha256',sha(ns['BINDING']),'--wrapper-sha256',WSHA]
    started=utc()
    run=subprocess.run(argv,cwd='/private/tmp',capture_output=True,timeout=60)
    completed=utc()
    after=os.fstat(fd);canonical=LOCK.lstat()
    assert (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino)==(canonical.st_dev,canonical.st_ino)
    result=dict(started_utc=started,completed_utc=completed,argv=argv,returncode=run.returncode,
        stdout=run.stdout.decode(),stderr=run.stderr.decode(),
        orchestration_source={'path':str(Path(__file__).resolve()),'sha256':sha(Path(__file__))},
        lock={'path':str(LOCK),'acquired_utc':lock_acquired,'device':before.st_dev,'inode':before.st_ino,
              'nonblocking_exclusive':True,'held_through_child_completion':True},
        binding={'path':str(ns['BINDING']),'sha256':sha(ns['BINDING'])},
        scope='ONE_SAVED_C1_BLIND_MACHINE_SCORE_NO_MODEL_OR_IMAGE_VIEWING',
        independent_result_review_required=True)
    write_new(OBS,result)
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
append_event('C1在固定全局非阻塞锁下执行唯一盲评分',
    f'实际持有同一锁至wrapper子进程结束；先核独立数值结果、固定合同和两份不同作者票，再形成真实盲态证明。既定wrapper进程return={run.returncode}。结果待独立复核，未运行模型或查看图像。',
    [str(OBS.relative_to(R)),str(ns['BINDING'].relative_to(R)),str(att_path.relative_to(R))],
    '独立核评分终态和冻结数值，再按既有独立复算合同进行复算；C2仍未完成，不宣称创新。')
print(json.dumps(result,ensure_ascii=False))
