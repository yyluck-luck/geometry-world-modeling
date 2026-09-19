#!/usr/bin/env python3
"""S106 development multi-arm context comparison.

Scope: DEVELOPMENT ONLY.  This is not a formal Gate0 run and its numbers are not
formal results.  It runs outside the signed bundle chain, on a window whose
future RGB was already opened during the 594155 baseline scoring, so it creates
no new outcome exposure.

Question: does the geometric-coverage explanation for the baseline's monotonic
PSNR decay survive a budget-matched context swap?

Arms, all with k = 4 so capacity is matched:
  A  [0, 15, 30, 45]   reproduces the formal baseline; also validates this
                       harness by byte-comparison against job 594155
  B  [40, 45, 50, 55]  four most recent frames
  C  [55, 55, 55, 55]  the frame VMem retrieval actually found visible,
                       duplicated to fill the budget (pseudo-evidence arm)

Everything else is held fixed: target cameras, intrinsics, seed, steps, cfg,
resolution, dtype, weights.
"""
import datetime as dt, hashlib, io, json, os, random, socket, sys, time
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
BANK = Path(os.environ['BANK_STAGE'])
OUT = Path(os.environ['ARM_OUT'])
SEED = 42; STEPS = 50; CFG = 2.0; CFG_MIN = 1.2; GUIDER = 1; DECODING_T = 1; CHUNK = 1
# Full arm matrix.  Every arm uses k = 4 so capacity, forward count and cost are
# matched; only the identity and multiplicity of the context frames change.
ARMS = {
    # --- coverage gradient: how far the context sits from the targets ---
    'A_baseline_spread':  [0, 15, 30, 45],     # the formal baseline choice
    'B_recent_matched':   [40, 45, 50, 55],    # nearest four
    'D_earliest':         [0, 5, 10, 15],      # furthest four
    'E_mid':              [20, 25, 30, 35],    # middle four
    'F_wide_span':        [0, 20, 40, 55],     # spans the whole bank
    # --- N04 evidence multiplicity at fixed unique-observation count ---
    # X = frame 55 (the only frame retrieval found visible), Y = frame 40
    'C_XXXX_dup4':        [55, 55, 55, 55],
    'G_XXXY':             [55, 55, 55, 40],
    'H_XXYY':             [55, 55, 40, 40],
    'I_XYYY':             [55, 40, 40, 40],
    # --- ordering placebo: identical multiset, different slot order ---
    'J_order_XYXY':       [55, 40, 55, 40],
    'K_order_YXYX':       [40, 55, 40, 55],
    # --- two unique frames spread far apart, matched multiplicity to H ---
    'L_XXYY_far':         [55, 55, 0, 0],
}
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

_T = {('liguang0115', 'vmem_weights.pth'): WEIGHTS / 'vmem_weights.pth',
      ('liguang0115', 'cut3r_512_dpt_4_64.pth'): WEIGHTS / 'cut3r_512_dpt_4_64.pth'}
def local_hf(repo_id, filename, *a, **k):
    p = WEIGHTS / filename
    require(p.exists(), f'unbound HF request {repo_id}/{filename}')
    return str(p)
huggingface_hub.hf_hub_download = local_hf
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

device = 'cuda'; dtype = torch.float32
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
# Match the formal predictor exactly: it sets interop threads and seeds the
# stdlib random module too.  Job 594704 arm A diverged from job 594155 because
# both were missing here.
torch.set_num_threads(8); torch.set_num_interop_threads(1)

model = VMemModel(VMemModelParams()).to(device, dtype)
state = torch.load(WEIGHTS / 'vmem_weights.pth', map_location='cpu', weights_only=False)
state = {k.replace('module.', '') if 'module.' in k else k: v for k, v in state.items()}
info = model.load_state_dict(state, strict=True)
require(not info.missing_keys and not info.unexpected_keys, 'VMem state mismatch')
del state
model = VMemWrapper(model).eval()
ae = AutoEncoder(chunk_size=CHUNK).to(device, dtype).eval()
clip = CLIPConditioner().to(device, dtype).eval()
print('[models_ready]', flush=True)

manifest = json.loads((BANK / 'BANK_MANIFEST.json').read_text())
K0 = np.loadtxt(io.StringIO((BANK / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)

def model_grid_K(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k

def load_rgb(fid):
    from PIL import Image
    p = BANK / 'bank' / f'frame-{fid:06d}.color.png'
    arr = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert('RGB'))
    t = torch.from_numpy(arr.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]

def load_pose(fid, sub):
    p = BANK / sub / f'frame-{fid:06d}.pose.txt'
    return np.loadtxt(io.StringIO(p.read_text()), dtype=np.float32).reshape(4, 4)

query_c2w = torch.tensor(np.stack([load_pose(f, 'query') for f in TARGETS]), device=device, dtype=torch.float32)
results = {}
OUT.mkdir(parents=True, exist_ok=True)

for name, ctx_ids in ARMS.items():
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    images = torch.stack([load_rgb(f) for f in ctx_ids]).to(device, dtype)
    Ks = torch.stack([model_grid_K(K0) for _ in ctx_ids]).to(device)
    c2ws = torch.tensor(np.stack([load_pose(f, 'bank') for f in ctx_ids]), device=device, dtype=torch.float32)
    carrier = object.__new__(VMemPipeline)
    carrier.camera_scale = 2.0; carrier.device = torch.device(device)
    carrier.dtype = torch.float32; carrier.config = cfg
    t0 = time.time()
    with torch.inference_mode():
        lat = encode_vae_image(images, ae, device, dtype)
        emb = encode_image(images, clip, device, dtype)
        raw_all = torch.cat([c2ws, query_c2w], 0)
        scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, raw_all.clone())
        qK = model_grid_K(K0).to(device)
        all_K = torch.cat([Ks, qK.unsqueeze(0).repeat(len(TARGETS), 1, 1)], 0)
        mask = torch.tensor([True] * 4 + [False] * 4, device=device)
        cond = VMemPipeline.get_cond(carrier, lat, all_c2w, all_K, scale, emb, mask)
        den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)
        sampler = create_samplers(guider_types=GUIDER, discretization=DDPMDiscretization(),
                                  num_frames=8, num_steps=STEPS, cfg_min=CFG_MIN, device=device)[0]
        outs = do_sample(model, ae, den, sampler, cond['c'], cond['uc'], cond['all_c2ws'],
                         cond['all_Ks'], cond['input_masks'], H=576, W=576, C=4, F=8, T=8,
                         cfg=CFG, decoding_t=DECODING_T, verbose=False, global_pbar=None,
                         return_latents=True, device=device)
    samples, _ = outs
    tgt = samples[4:].detach().float().cpu().numpy()
    f = OUT / f'{name}_target_rgb_fp32.npy'
    np.save(f, tgt, allow_pickle=False)
    results[name] = {'context_frame_ids': ctx_ids, 'seconds': round(time.time() - t0, 2),
                     'output': {'path': str(f), 'bytes': f.stat().st_size, 'sha256': sha_file(f)}}
    print(f'[arm_done] {name} {results[name]["seconds"]}s sha={results[name]["output"]["sha256"][:16]}', flush=True)

receipt = {
    'schema': 's106-development-multiarm-context-v1',
    'status': 'ARMS_COMPLETE_UNSCORED',
    'scope': ('development only; outside the signed Gate0 bundle chain; not a formal result; '
              'window future RGB was already opened by the 594155 baseline scoring'),
    'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hostname': socket.gethostname(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
    'held_fixed': {'targets': TARGETS, 'seed': SEED, 'steps': STEPS, 'cfg': CFG,
                   'cfg_min': CFG_MIN, 'resolution': [576, 576], 'dtype': 'fp32_autocast', 'k': 4},
    'arms': results,
    'baseline_reference_job': 594155,
    'baseline_reference_sha256': 'c6169974a24b9fc6d4ecf53c46f2badfddbbd53c063e051e3609362d3b99c79f',
    'arm_A_reproduces_formal_baseline': (
        results['A_baseline_spread']['output']['sha256'] ==
        'c6169974a24b9fc6d4ecf53c46f2badfddbbd53c063e051e3609362d3b99c79f'),
    'scored': False, 'scientific_result': False,
    'new_method_validated': False, 'novelty_authorization': 'NONE',
    'claim_boundary': ('Establishes only what each context choice produces under fixed '
                       'conditions. No memory-benefit, geometry or method claim follows.'),
}
(OUT / 'MULTIARM_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps(receipt, indent=2, sort_keys=True))
