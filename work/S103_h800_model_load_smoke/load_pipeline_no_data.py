import json, os, time, hashlib
from pathlib import Path
import torch
from omegaconf import OmegaConf

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
SRC = RUN / 'vmem'
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
os.chdir(SRC)
import sys
sys.path.insert(0, str(SRC))

import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip

def local_hf(repo_id, filename, *args, **kwargs):
    mapping = {
        ('liguang0115/vmem','vmem_weights.pth'): WEIGHTS/'vmem_weights.pth',
        ('liguang0115/cut3r','cut3r_512_dpt_4_64.pth'): WEIGHTS/'cut3r_512_dpt_4_64.pth',
    }
    p = mapping.get((repo_id, filename))
    if p is None or not p.exists():
        raise RuntimeError(f'Unexpected or missing checkpoint request: {repo_id}/{filename}')
    return str(p)

huggingface_hub.hf_hub_download = local_hf

orig_vae = AutoencoderKL.from_pretrained
vae_dir = RUN / 'local_vae_smoke'
vae_dir.mkdir(exist_ok=True)
for name in ['config.json','diffusion_pytorch_model.safetensors']:
    src = WEIGHTS / ('diffusion_pytorch_model.safetensors' if name.endswith('safetensors') else name)
    dst = vae_dir / name
    if not dst.exists(): dst.symlink_to(src)
def local_vae(repo, *args, **kwargs):
    return orig_vae(str(vae_dir), local_files_only=True, force_download=False,
                    low_cpu_mem_usage=False, use_safetensors=True)
AutoencoderKL.from_pretrained = local_vae

orig_clip = open_clip.create_model_and_transforms
def local_clip(name, *args, **kwargs):
    return orig_clip(name, pretrained=str(WEIGHTS/'open_clip_model.safetensors'))
open_clip.create_model_and_transforms = local_clip

orig_load = torch.load
def verified_load(path, *args, **kwargs):
    if str(path) in {str(WEIGHTS/'vmem_weights.pth'), str(WEIGHTS/'cut3r_512_dpt_4_64.pth')}:
        kwargs['weights_only'] = False
    return orig_load(path, *args, **kwargs)
torch.load = verified_load

from modeling.pipeline import VMemPipeline

cfg = OmegaConf.load('configs/inference/inference.yaml')
t0=time.time()
pipeline = VMemPipeline(cfg, device='cuda', dtype=torch.float16)
t1=time.time()
receipt = {
  'schema':'s103-h800-vmem-model-load-smoke-v1', 'status':'SUCCESS',
  'data_access':'NONE', 'gt_access':False, 'forward_completed':False,
  'device':torch.cuda.get_device_name(0), 'torch':torch.__version__,
  'cuda':torch.version.cuda, 'load_seconds':t1-t0,
  'peak_memory_bytes':torch.cuda.max_memory_allocated(),
  'checkpoint_bytes':WEIGHTS.joinpath('vmem_weights.pth').stat().st_size,
  'checkpoint_sha256':hashlib.sha256(WEIGHTS.joinpath('vmem_weights.pth').read_bytes()).hexdigest(),
  'components':['VMemModel','AutoEncoder','CLIPConditioner','ARCroco3DStereo'],
  'config':'configs/inference/inference.yaml', 'seed':42,
}
Path(os.environ.get('OUT_DIR','/tmp')).joinpath('RECEIPT.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt, indent=2))
