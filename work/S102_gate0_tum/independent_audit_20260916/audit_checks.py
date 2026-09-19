#!/usr/bin/env python3
"""Read-only Gate0 evidence audit; fixtures are synthetic and cannot dispatch jobs."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CONTRACT = ROOT / 'work/S102_gate0_tum/gate0_contract_candidate_v2.json'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

files = [CONTRACT, ROOT / 'work/S102_gate0_7scenes/HELDOUT_ACQUISITION_PROTOCOL_v1.json',
         ROOT / 'work/S102_gate0_7scenes/HELDOUT_ARCHIVE_EVIDENCE.json',
         ROOT / 'work/S102_gate0_tum/validate_gate0_contract.py',
         ROOT / 'work/S102_gate0_tum/future_path_guard.py',
         ROOT / 'work/S20_environment/isolated_vmem_source/configs/inference/inference.yaml']
local = []
for p in files:
    s = p.stat()
    local.append({'path': str(p.relative_to(ROOT)), 'sha256': digest(p), 'size': s.st_size,
                  'birth_epoch': getattr(s, 'st_birthtime', None), 'mtime_epoch': s.st_mtime})
(OUT / 'INPUT_FILE_HASHES.json').write_text(json.dumps(local, indent=2) + '\n')

checks = []
with tempfile.TemporaryDirectory(prefix='gate0_synthetic_audit_') as tmp:
    tmp = Path(tmp)
    guard = ROOT / 'work/S102_gate0_tum/future_path_guard.py'
    for name, obj in [
        ('unlabelled_future_path', {'inputs': ['/home/yliutz/datasets/heldout_7scenes_chess/extracted/chess/seq-03/frame-000100.color.png']}),
        ('benign_boolean_metadata', {'history_inputs': ['/tmp/history.png'], 'future_data_visible': False}),
    ]:
        p = tmp / (name + '.json'); p.write_text(json.dumps(obj))
        r = subprocess.run([sys.executable, str(guard), str(p)], text=True, capture_output=True)
        checks.append({'name': name, 'synthetic': True, 'opens_data': False, 'exit_code': r.returncode,
                       'stdout': r.stdout, 'stderr': r.stderr})
    fake = json.loads(CONTRACT.read_text())
    fake['status'] = fake['formal_experiment_eligibility'] = 'PASS'
    for section in fake['sections'].values():
        section['status'] = 'PASS'
        for key in section['required']:
            if section['values'].get(key) is None:
                section['values'][key] = 'SYNTHETIC_NONEXISTENT_PLACEHOLDER'
    for k in ['prediction_output_hash_before_gt_open', 'future_rgb_depth_pose_gt_not_read_before_seal']:
        fake['sections']['future_gt_isolation']['values'][k] = True
    for k in ['post_run_manifest_recompute', 'metric_recompute', 'output_seal_check']:
        fake['sections']['independent_readback']['values'][k] = True
    p = tmp / 'SYNTHETIC_NOT_FOR_DISPATCH.json'; p.write_text(json.dumps(fake))
    r = subprocess.run([sys.executable, str(ROOT / 'work/S102_gate0_tum/validate_gate0_contract.py'), str(p)],
                       text=True, capture_output=True)
    checks.append({'name': 'declarations_without_real_artifacts', 'synthetic': True, 'opens_data': False,
                   'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
(OUT / 'SYNTHETIC_GUARD_CHECKS.json').write_text(json.dumps(checks, indent=2) + '\n')

remote_script = r'''
from pathlib import Path
import json,hashlib,zipfile,datetime
base=Path('/home/yliutz/datasets/heldout_7scenes_chess')
archive=base/'chess.zip'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
out={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),
     'scope':'Archive digest, outer ZIP directory, already-declared split text, and launcher receipts only. No nested frame/depth/pose decoding or member reads.'}
with zipfile.ZipFile(archive) as z:
 out['outer_entries']=[{'filename':i.filename,'size':i.file_size,'compressed':i.compress_size,'crc':i.CRC} for i in z.infolist()]
out['receipt_files']=[]
for p in sorted(base.glob('*')):
 if p.is_file() and p.suffix in ('.exit','.sha256'):
  out['receipt_files'].append({'path':str(p),'text':p.read_text(),'mtime_epoch':p.stat().st_mtime,'sha256':sha(p)})
out['splits']=[]
for name in ['TrainSplit.txt','TestSplit.txt']:
 p=base/'extracted/chess'/name
 out['splits'].append({'path':str(p),'sha256':sha(p),'text':p.read_text(),'mtime_epoch':p.stat().st_mtime})
print(json.dumps(out,indent=2))
'''
r = subprocess.run(['ssh', '-i', '/Users/rocket/.ssh/id_ed25519_superpod', '-o', 'BatchMode=yes',
                    '-o', 'ConnectTimeout=15', 'yliutz@superpod.ust.hk', 'python3 -'],
                   input=remote_script, text=True, capture_output=True, timeout=120)
(OUT / 'REMOTE_ARCHIVE_READBACK.json').write_text(r.stdout if r.returncode == 0 else json.dumps({'exit':r.returncode,'stderr':r.stderr}))
print(json.dumps({'time_utc':dt.datetime.now(dt.timezone.utc).isoformat(), 'local_input_count':len(local),
                  'synthetic_check_exit_codes':[x['exit_code'] for x in checks], 'remote_exit_code':r.returncode,
                  'output_directory':str(OUT)},indent=2))
if r.returncode:
    raise SystemExit(r.returncode)
