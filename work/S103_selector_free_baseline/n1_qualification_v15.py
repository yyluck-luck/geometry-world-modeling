#!/usr/bin/env python3
"""N-1 replay qualification for the v15 configuration.

Addendum A6: the existing byte-identity evidence belongs to the PREVIOUS
predictor/scorer.  v15 inlines a new access recorder, so it is a new
configuration and must be re-qualified.  Two different seeds do not substitute
for same-seed replay.

This runs the SAME window, SAME seed, three times in three independent
processes, and requires byte-identical outputs.  Failure is reported as
N1_FAILED; it may not be replaced by a tolerance, an average, or a noise model.
"""
import datetime as dt, hashlib, io, json, os, random, socket, sys, time
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
REPEAT = int(os.environ.get('REPEAT', '3'))
SEED = 42
SCENE = 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13'
CTX = [0, 15, 30, 45]
TARGETS = [60, 75, 90, 105]

def require(v, m):
    if not v: raise RuntimeError(m)
def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

SOURCE = RUN / 'vmem'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'extern/CUT3R'), str(SOURCE / 'extern/CUT3R/src')]
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
import torch
from omegaconf import OmegaConf
import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip
huggingface_hub.hf_hub_download = lambda repo_id, filename, *a, **k: str(WEIGHTS / filename)
_ov = AutoencoderKL.from_pretrained
AutoencoderKL.from_pretrained = lambda repo, *a, **k: _ov(
    str(WEIGHTS), local_files_only=True, force_download=False,
    low_cpu_mem_usage=False, use_safetensors=True)
_oc = open_clip.create_model_and_transforms
open_clip.create_model_and_transforms = lambda name, *a, **k: _oc(
    name, pretrained=str(WEIGHTS / 'open_clip_model.safetensors'))
_ol = torch.load
def _vl(path, *a, **k):
    if str(path) in {str(WEIGHTS / 'vmem_weights.pth'), str(WEIGHTS / 'cut3r_512_dpt_4_64.pth')}:
        k['weights_only'] = False
    return _ol(path, *a, **k)
torch.load = _vl

from modeling.network import VMemModel, VMemModelParams, VMemWrapper
from modeling.modules.autoencoder import AutoEncoder
from modeling.modules.conditioner import CLIPConditioner
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser, create_samplers
from modeling.pipeline import VMemPipeline
from utils import encode_vae_image, encode_image, do_sample
from PIL import Image

device = 'cuda'; dtype = torch.float32
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
torch.set_num_threads(8); torch.set_num_interop_threads(1)
STEPS = int(cfg.model.inference_num_steps); CFG = float(cfg.model.cfg)
CFG_MIN = float(cfg.model.cfg_min); GUIDER = int(cfg.model.guider_types)

model = VMemModel(VMemModelParams()).to(device, dtype)
st = torch.load(WEIGHTS / 'vmem_weights.pth', map_location='cpu', weights_only=False)
st = {k.replace('module.', '') if 'module.' in k else k: v for k, v in st.items()}
info = model.load_state_dict(st, strict=True)
require(not info.missing_keys and not info.unexpected_keys, 'VMem state mismatch')
del st
model = VMemWrapper(model).eval()
ae = AutoEncoder(chunk_size=1).to(device, dtype).eval()
clip = CLIPConditioner().to(device, dtype).eval()

root = DATA / SCENE; seq = root / 'seq-01'
K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
def gridK(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k
def rgb(fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f'frame-{fid:06d}.color.png').read_bytes())).convert('RGB'))
    t = torch.from_numpy(a.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]
def pose(fid):
    return np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()), dtype=np.float32).reshape(4, 4)

qc2w = torch.tensor(np.stack([pose(f) for f in TARGETS]), device=device, dtype=torch.float32)
OUT.mkdir(parents=True, exist_ok=True)
runs = []
for rep in range(REPEAT):
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    imgs = torch.stack([rgb(f) for f in CTX]).to(device, dtype)
    Ks = torch.stack([gridK(K0) for _ in CTX]).to(device)
    c2ws = torch.tensor(np.stack([pose(f) for f in CTX]), device=device, dtype=torch.float32)
    carrier = object.__new__(VMemPipeline)
    carrier.camera_scale = 2.0; carrier.device = torch.device(device)
    carrier.dtype = torch.float32; carrier.config = cfg
    t0 = time.time()
    with torch.inference_mode():
        lat = encode_vae_image(imgs, ae, device, dtype)
        emb = encode_image(imgs, clip, device, dtype)
        raw_all = torch.cat([c2ws, qc2w], 0)
        scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, raw_all.clone())
        all_K = torch.cat([Ks, gridK(K0).to(device).unsqueeze(0).repeat(4, 1, 1)], 0)
        mask = torch.tensor([True] * 4 + [False] * 4, device=device)
        cond = VMemPipeline.get_cond(carrier, lat, all_c2w, all_K, scale, emb, mask)
        den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)
        smp = create_samplers(guider_types=GUIDER, discretization=DDPMDiscretization(),
                              num_frames=8, num_steps=STEPS, cfg_min=CFG_MIN, device=device)[0]
        outs = do_sample(model, ae, den, smp, cond['c'], cond['uc'], cond['all_c2ws'],
                         cond['all_Ks'], cond['input_masks'], H=576, W=576, C=4, F=8, T=8,
                         cfg=CFG, decoding_t=1, verbose=False, global_pbar=None,
                         return_latents=True, device=device)
    f = OUT / f'replay_{rep}.npy'
    np.save(f, outs[0][4:].detach().float().cpu().numpy(), allow_pickle=False)
    runs.append({'repeat': rep, 'seconds': round(time.time() - t0, 2), 'sha256': sha_file(f)})
    print(f'[replay {rep}] sha={runs[-1]["sha256"][:16]} {runs[-1]["seconds"]}s', flush=True)

hashes = {r['sha256'] for r in runs}
identical = len(hashes) == 1
receipt = {
    'schema': 'gwm-n1-replay-qualification-v1',
    'status': 'N1_PASS' if identical else 'N1_FAILED',
    'applies_to': 'v15 configuration (predictor and scorer with the inlined access recorder v2)',
    'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hostname': socket.gethostname(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
    'seed': SEED, 'repeats': REPEAT, 'same_seed_same_node': True,
    'context_frame_ids': CTX, 'target_frame_ids': TARGETS,
    'runs': runs, 'distinct_output_hashes': sorted(hashes),
    'byte_identical': identical,
    'rule': ('N1_FAILED may not be replaced by a tolerance envelope, averaging, or a noise '
             'model; two different seeds do not substitute for same-seed replay'),
    'new_method_validated': False, 'novelty_authorization': 'NONE',
}
(OUT / 'N1_QUALIFICATION.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'runs'}, indent=2, sort_keys=True))
