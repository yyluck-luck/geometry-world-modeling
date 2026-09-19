"""Fetch fixed, required public companions; preserve declared VAE identity."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import time
from download_original import safe

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
ASSETS = [
    dict(role='declared_ft_mse_config', repo='stabilityai/sd-vae-ft-mse', revision='31f26fdeee1355a5c34592e401dd41e45d25a493',
         filename='config.json', directory='data/vae_official_ft_mse', bytes=547,
         sha256='92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e'),
    dict(role='declared_ft_mse_weight', repo='stabilityai/sd-vae-ft-mse', revision='31f26fdeee1355a5c34592e401dd41e45d25a493',
         filename='diffusion_pytorch_model.safetensors', directory='data/vae_official_ft_mse', bytes=334643276,
         sha256='a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815'),
    dict(role='original_clip_weight', repo='laion/CLIP-ViT-H-14-laion2B-s32B-b79K', revision='1c2b8495b28150b8a4922ee1c8edee224c284c0c',
         filename='open_clip_model.safetensors', directory='data/clip_original', bytes=3944517836,
         sha256='0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5'),
]

def utc():
    return datetime.now(timezone.utc).isoformat()

def main():
    receipt = dict(started_utc=utc(), status='RUNNING', original_sd21_vae_identity='UNKNOWN',
                   scientific_execution=False, assets=[])
    dst = HERE/'companion_download_receipt.json'
    def save():
        dst.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    save()
    env = os.environ.copy()
    env.update(HF_HOME='/Users/rocket/.cache/huggingface-research-s39', HF_HUB_DISABLE_TELEMETRY='1',
               HF_HUB_DISABLE_UPDATE_CHECK='1', HTTPS_PROXY='http://127.0.0.1:7897', HTTP_PROXY='http://127.0.0.1:7897')
    for item in ASSETS:
        record = dict(item, started_utc=utc(), status='DOWNLOADING')
        receipt['assets'].append(record); save()
        command = [str(HERE/'cli-env/bin/hf'),'download',item['repo'],item['filename'],'--revision',item['revision'],
                   '--local-dir',str(ROOT/item['directory']),'--max-workers','1']
        t = time.monotonic()
        with (HERE/(item['role']+'_download_redacted.log')).open('x') as log:
            child = subprocess.Popen(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            record['child_pid']=child.pid; save()
            for line in child.stdout:
                clean=safe(line); log.write(clean); log.flush(); print(clean,end='',flush=True)
            code=child.wait()
        record.update(exit_code=code,download_wall_seconds=time.monotonic()-t,download_finished_utc=utc())
        target=ROOT/item['directory']/item['filename']
        if code!=0 or not target.is_file():
            record['status']='DOWNLOAD_FAILED';receipt['status']='FAILED';save();return 1
        record['actual_bytes']=target.stat().st_size
        with target.open('rb') as f:
            record['actual_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
        if record['actual_bytes']!=item['bytes'] or record['actual_sha256']!=item['sha256']:
            record['status']='IDENTITY_MISMATCH';receipt['status']='FAILED';save();return 1
        record.update(status='VERIFIED_COMPLETE_DECLARED_ASSET',hash_finished_utc=utc(),path=str(target));save()
        print(json.dumps(record,ensure_ascii=False),flush=True)
    receipt.update(status='ALL_COMPANIONS_VERIFIED',completed_utc=utc());save();return 0

if __name__=='__main__':
    raise SystemExit(main())
