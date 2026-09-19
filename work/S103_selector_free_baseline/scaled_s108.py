#!/usr/bin/env python3
"""S108 scaled context experiment: 2 scenes x N windows x arms x seeds.

Design corrections carried in from S106/S107:
  * Job 594717 showed slot order shifts PSNR by up to 0.87 dB.
  * Job 594733 showed the shift is structured, not noise: within a multiset the
    scores split by which frame occupies slot 0.  That matches
    get_plucker_coordinates(extrinsics_src=all_w2cs[:1], ...) in pipeline.py,
    where the first context camera defines the reference frame for every ray.
  * Therefore slot 0 is treated as an explicit controlled factor.  Arms that are
    meant to compare context CONTENT hold the reference frame identical; arms
    that probe the gauge vary it deliberately and are labelled as such.

DEVELOPMENT scope.  Reads history RGB/pose and target pose only; target RGB is
never opened here -- scoring is a separate process.
"""
import datetime as dt, hashlib, io, json, os, random, socket, sys, time
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
SEEDS = [int(x) for x in os.environ.get('SEEDS', '42,7').split(',')]
STEPS = 50; CFG = 2.0; CFG_MIN = 1.2; GUIDER = 1; DECODING_T = 1; CHUNK = 1

SCENES = {'scene_13': ('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13', 462),
          'scene_14': ('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14', 659)}
WINDOW_STARTS = list(range(0, 400, 50))          # up to 8 per scene, bounded below
TARGET_OFFSETS = [60, 75, 90, 105]

def arms_for(start):
    """Context sets, all k=4.  R marks the reference (slot-0) frame."""
    R = start + 40                                # common reference for content arms
    return {
        # --- content contrasts, reference frame held IDENTICAL ---
        'content_recent':   [R, start + 45, start + 50, start + 55],
        'content_spread':   [R, start + 0,  start + 20, start + 55],
        'content_early':    [R, start + 0,  start + 5,  start + 10],
        'content_mid':      [R, start + 20, start + 25, start + 30],
        # --- multiplicity at fixed reference: 1 vs 2 vs 4 unique frames ---
        'mult_1unique':     [R, R, R, R],
        'mult_2unique':     [R, R, start + 55, start + 55],
        'mult_4unique':     [R, start + 45, start + 50, start + 55],
        # --- deliberate gauge probe: same multiset, different slot 0 ---
        'gauge_alt_ref':    [start + 55, start + 45, start + 50, R],
    }

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

device = 'cuda'; dtype = torch.float32
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
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

def model_grid_K(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k

from PIL import Image
def load_rgb(seq, fid):
    p = seq / f'frame-{fid:06d}.color.png'
    arr = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert('RGB'))
    t = torch.from_numpy(arr.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]
def load_pose(seq, fid):
    return np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()),
                      dtype=np.float32).reshape(4, 4)

OUT.mkdir(parents=True, exist_ok=True)
index, t_start, n_done = [], time.time(), 0
for scene, (rel, nframes) in SCENES.items():
    root = DATA / rel
    seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()),
                    dtype=np.float32).reshape(3, 3)
    for start in WINDOW_STARTS:
        if start + max(TARGET_OFFSETS) >= nframes:
            continue
        targets = [start + o for o in TARGET_OFFSETS]
        qc2w = torch.tensor(np.stack([load_pose(seq, f) for f in targets]),
                            device=device, dtype=torch.float32)
        for arm, ctx in arms_for(start).items():
            for seed in SEEDS:
                random.seed(seed); np.random.seed(seed)
                torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
                images = torch.stack([load_rgb(seq, f) for f in ctx]).to(device, dtype)
                Ks = torch.stack([model_grid_K(K0) for _ in ctx]).to(device)
                c2ws = torch.tensor(np.stack([load_pose(seq, f) for f in ctx]),
                                    device=device, dtype=torch.float32)
                carrier = object.__new__(VMemPipeline)
                carrier.camera_scale = 2.0; carrier.device = torch.device(device)
                carrier.dtype = torch.float32; carrier.config = cfg
                with torch.inference_mode():
                    lat = encode_vae_image(images, ae, device, dtype)
                    emb = encode_image(images, clip, device, dtype)
                    raw_all = torch.cat([c2ws, qc2w], 0)
                    scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, raw_all.clone())
                    qK = model_grid_K(K0).to(device)
                    all_K = torch.cat([Ks, qK.unsqueeze(0).repeat(len(targets), 1, 1)], 0)
                    mask = torch.tensor([True] * 4 + [False] * 4, device=device)
                    cond = VMemPipeline.get_cond(carrier, lat, all_c2w, all_K, scale, emb, mask)
                    den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)
                    sampler = create_samplers(guider_types=GUIDER, discretization=DDPMDiscretization(),
                                              num_frames=8, num_steps=STEPS, cfg_min=CFG_MIN, device=device)[0]
                    outs = do_sample(model, ae, den, sampler, cond['c'], cond['uc'], cond['all_c2ws'],
                                     cond['all_Ks'], cond['input_masks'], H=576, W=576, C=4, F=8, T=8,
                                     cfg=CFG, decoding_t=DECODING_T, verbose=False, global_pbar=None,
                                     return_latents=True, device=device)
                tgt = outs[0][4:].detach().float().cpu().numpy()
                tag = f'{scene}__w{start:04d}__{arm}__s{seed}'
                f = OUT / f'{tag}.npy'
                np.save(f, tgt, allow_pickle=False)
                index.append({'tag': tag, 'scene': scene, 'window_start': start, 'arm': arm,
                              'seed': seed, 'context_frame_ids': ctx, 'target_frame_ids': targets,
                              'reference_frame_id': ctx[0], 'unique_context_frames': len(set(ctx)),
                              'output': {'path': str(f), 'bytes': f.stat().st_size,
                                         'sha256': sha_file(f)}})
                n_done += 1
                if n_done % 20 == 0:
                    print(f'[progress] {n_done} runs, {time.time()-t_start:.0f}s', flush=True)

receipt = {'schema': 's108-scaled-context-experiment-v1', 'status': 'RUNS_COMPLETE_UNSCORED',
           'scope': 'development only; outside the signed Gate0 chain; target RGB not opened here',
           'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'hostname': socket.gethostname(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
           'scenes': list(SCENES), 'window_starts': WINDOW_STARTS, 'seeds': SEEDS,
           'target_offsets': TARGET_OFFSETS, 'total_runs': len(index),
           'elapsed_seconds': round(time.time() - t_start, 1),
           'design_note': ('Slot 0 is the Plucker reference camera; content arms hold it '
                           'identical and gauge_alt_ref varies it deliberately.'),
           'runs': index, 'scored': False, 'scientific_result': False,
           'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'SCALED_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'runs'}, indent=2, sort_keys=True))
