"""Use official HF CLI authentication; never copy credentials into research logs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import subprocess
import time

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
TARGET = ROOT / 'data/vmem_original/vmem_weights.pth'
SIZE = 5056346672
SHA = '675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4'
REVISION = 'ac5921080a57f5a634f4b9acbbc8f3db67c9d113'

def utc():
    return datetime.now(timezone.utc).isoformat()

def safe(line):
    line = re.sub(r'https?://[^\s\x1b]+', lambda m: m[0].split('?')[0] + ('?[query-redacted]' if '?' in m[0] else ''), line)
    return re.sub(r'\bhf_[A-Za-z0-9]{12,}\b', '[credential-redacted]', line)

def main():
    receipt = {'started_utc': utc(), 'repo': 'liguang0115/vmem', 'revision': REVISION,
               'expected_bytes': SIZE, 'expected_sha256': SHA, 'target': str(TARGET),
               'source': 'Official author Hugging Face repository; authenticated official CLI 1.30.0',
               'auth': 'Official device flow succeeded; user completed webpage. No credential values in this receipt.',
               'scientific_execution': False, 'status': 'RUNNING'}
    receipt_path = HERE / 'vmem_download_receipt.json'
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    env = os.environ.copy()
    env.update(HF_HOME='/Users/rocket/.cache/huggingface-research-s39',
               HF_HUB_DISABLE_TELEMETRY='1', HF_HUB_DISABLE_UPDATE_CHECK='1',
               HTTPS_PROXY='http://127.0.0.1:7897', HTTP_PROXY='http://127.0.0.1:7897')
    cmd = [str(HERE / 'cli-env/bin/hf'), 'download', 'liguang0115/vmem', 'vmem_weights.pth',
           '--revision', REVISION, '--local-dir', str(TARGET.parent), '--max-workers', '1']
    start = time.monotonic()
    with (HERE / 'vmem_download_redacted.log').open('w') as log:
        child = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, bufsize=1)
        receipt['child_pid'] = child.pid
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        for line in child.stdout:
            clean = safe(line)
            log.write(clean)
            log.flush()
            print(clean, end='', flush=True)
        code = child.wait()
    receipt.update(download_exit_code=code, download_wall_seconds=time.monotonic() - start,
                   download_finished_utc=utc(), status='DOWNLOAD_FAILED')
    if code == 0 and TARGET.is_file():
        receipt['actual_bytes'] = TARGET.stat().st_size
        digest = hashlib.sha256()
        with TARGET.open('rb') as f:
            for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
                digest.update(chunk)
        receipt['actual_sha256'] = digest.hexdigest()
        receipt['hash_finished_utc'] = utc()
        receipt['status'] = 'VERIFIED_COMPLETE_ORIGINAL_WEIGHT' if receipt['actual_bytes'] == SIZE and digest.hexdigest() == SHA else 'FILE_IDENTITY_MISMATCH'
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    return 0 if receipt['status'] == 'VERIFIED_COMPLETE_ORIGINAL_WEIGHT' else 1

if __name__ == '__main__':
    raise SystemExit(main())
