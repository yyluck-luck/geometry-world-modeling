#!/usr/bin/env python3
"""S137c warp4: S134 generator plus *virtual* contexts (geometric warps at the target poses).

A plan context with "virtual": "fill" | "hole" and "warp_dir" uses the four target-pose warps of that window as
context images, with context poses = target poses (hole: uncovered pixels -> 0 in [-1, 1]). Otherwise identical
to gen_s134.py, which follows.

S134 step B: generate target frames for planned contexts (static / memory orig / memory fixed).

Derived from work/S132_C9_convention/convention_test_c9.py; the sampler, conditioning, image/pose loading
and K transform are unchanged. Contexts come from PLAN (JSON list of unique (scene, window, ctx_ids, tags)),
built from step-A retrieval receipts. SHARD=i/N splits the work; existing outputs are skipped (resumable).
Original C9/S111 docstring follows.

S111: same question as S109, now including VMem's DEFAULT NMS-on retrieval.

Two arms see exactly the same real history frames.  The only difference is
whether the memory machinery is used to choose the conditioning context.

  STATIC   : hand-picked context, get_cond called directly (the S103 baseline path)
  MEMORY   : the same real frames are written into the pipeline, surfels are
             constructed with CUT3R, and get_context_info selects the context

Both then run the identical sampler with the same seed, steps, cfg and targets.

DEVELOPMENT scope.  Target RGB is never opened here; scoring is separate.
NMS is disabled through the documented parameter because get_context_info only
initialises self.initial_threshold when len(pil_frames)==5 (observed job 594691).
"""
import datetime as dt, hashlib, io, json, os, random, socket, sys, time
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path(os.environ.get('WEIGHTS', '/home/yliutz/gwm_weights_20260915'))
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
SEEDS = [int(x) for x in os.environ.get('SEEDS', '42,7,1,2,3,4,5,6').split(',')]
PLAN = Path(os.environ['PLAN']); SHARD_I, SHARD_N = map(int, os.environ.get('SHARD', '0/1').split('/'))
BANK_STEP = 5; BANK_SPAN = 60          # bank = start .. start+55 step 5  (12 frames)
TARGET_OFFSETS = [60, 75, 90, 105]
STATIC_CTX_OFFSETS = [0, 15, 30, 45]   # the formal baseline choice
SCENES = {'scene_13': ('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13', 462),
          'scene_14': ('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14', 659)}
WINDOW_STARTS = [0, 50, 100, 150, 200, 250, 300, 350]

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
import modeling.pipeline as _pm
_pm.hf_hub_download = huggingface_hub.hf_hub_download
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
from modeling.pipeline import VMemPipeline, encode_vae_image, encode_image, tensor_to_pil
from utils import do_sample

device = 'cuda'; dtype = torch.float32
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
torch.set_num_threads(8); torch.set_num_interop_threads(1)
STEPS = int(cfg.model.inference_num_steps); CFG = float(cfg.model.cfg)
CFG_MIN = float(cfg.model.cfg_min); GUIDER = int(cfg.model.guider_types)

pipe = VMemPipeline(cfg, torch.device(device))          # full __init__, loads CUT3R
print('[pipeline_ready]', flush=True)
model = pipe.model_wrapper; ae = pipe.vae; clip = pipe.image_encoder

from PIL import Image
def model_grid_K(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k
def load_rgb(seq, fid):
    arr = np.asarray(Image.open(io.BytesIO((seq / f'frame-{fid:06d}.color.png').read_bytes())).convert('RGB'))
    t = torch.from_numpy(arr.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]
def load_pose(seq, fid):
    return np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()),
                      dtype=np.float32).reshape(4, 4)

def sample(lat, emb, c2ws, Ks, qc2w, qK, seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    carrier = object.__new__(VMemPipeline)
    carrier.camera_scale = 2.0; carrier.device = torch.device(device)
    carrier.dtype = torch.float32; carrier.config = cfg
    with torch.inference_mode():
        raw_all = torch.cat([c2ws, qc2w], 0)
        scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, raw_all.clone())
        all_K = torch.cat([Ks, qK.unsqueeze(0).repeat(qc2w.shape[0], 1, 1)], 0)
        mask = torch.tensor([True] * 4 + [False] * 4, device=device)
        cond = VMemPipeline.get_cond(carrier, lat, all_c2w, all_K, scale, emb, mask)
        den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)
        sampler = create_samplers(guider_types=GUIDER, discretization=DDPMDiscretization(),
                                  num_frames=8, num_steps=STEPS, cfg_min=CFG_MIN, device=device)[0]
        outs = do_sample(model, ae, den, sampler, cond['c'], cond['uc'], cond['all_c2ws'],
                         cond['all_Ks'], cond['input_masks'], H=576, W=576, C=4, F=8, T=8,
                         cfg=CFG, decoding_t=1, verbose=False, global_pbar=None,
                         return_latents=True, device=device)
    return outs[0][4:].detach().float().cpu().numpy()


# ---------------- S134 planned generation ----------------
OUT.mkdir(parents=True, exist_ok=True)
plan = json.loads(PLAN.read_text())['contexts']
jobs = [(c, s) for c in plan for s in SEEDS]
jobs = [j for k, j in enumerate(jobs) if k % SHARD_N == SHARD_I]
log = OUT / f'RUNS_{socket.gethostname()}_{os.getpid()}.jsonl'
t0 = time.time(); cache = {}
def convert(c2w_batch, convention):  # identical to C9 convention_test_c9.convert
    if convention == 'native':
        return c2w_batch
    out = c2w_batch.clone(); out[:, :, [1, 2]] *= -1
    return out
for c, seed in jobs:
    f = OUT / f"{c['ctx_key']}__s{seed}.npy"
    if f.exists(): continue
    scene, start, ctx_ids = c['scene'], int(c['window_start']), [int(x) for x in c['ctx_ids']]
    rel, _ = SCENES[scene]; root = DATA / rel; seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
    qK = model_grid_K(K0).to(device)
    targets = [start + o for o in TARGET_OFFSETS]
    key = c['ctx_key']
    virtual = c.get('virtual')
    if key not in cache:
        cache.clear()
        if virtual:
            ims = []
            for t in targets:
                z = np.load(Path(os.environ.get('WARP_DIR', c.get('warp_dir', ''))) / f"{scene}__w{start:04d}__t{t:06d}.npz")
                x = torch.from_numpy(z['filled'].astype(np.float32) / 255. * 2 - 1).permute(2, 0, 1)
                if virtual == 'hole': x = x * torch.from_numpy(z['valid'].astype(np.float32))[None]
                ims.append(x)
            imgs = torch.stack(ims).to(device, dtype)
        else:
            imgs = torch.stack([load_rgb(seq, i) for i in ctx_ids]).to(device, dtype)
        with torch.inference_mode():
            cache[key] = (encode_vae_image(imgs, ae, device, dtype), encode_image(imgs, clip, device, dtype))
    lat, emb = cache[key]
    Ks_t = torch.stack([model_grid_K(K0) for _ in ctx_ids]).to(device)
    c2ws = torch.tensor(np.stack([load_pose(seq, i) for i in (targets if virtual else ctx_ids)]), device=device, dtype=torch.float32)
    qc2w = torch.tensor(np.stack([load_pose(seq, i) for i in targets]), device=device, dtype=torch.float32)
    conv = c.get('convention', 'native'); c2ws = convert(c2ws, conv); qc2w = convert(qc2w, conv)
    ts = time.time(); tgt = sample(lat, emb, c2ws, Ks_t, qc2w, qK, seed)
    tmp = f.with_suffix('.tmp.npy'); np.save(tmp, tgt, allow_pickle=False); tmp.rename(f)
    rec = {'ctx_key': key, 'arms': c['arms'], 'virtual': virtual, 'convention': conv, 'scene': scene, 'window_start': start, 'seed': seed,
           'context_frame_ids': ctx_ids, 'target_frame_ids': targets, 'seconds': round(time.time() - ts, 2),
           'output': {'path': str(f), 'bytes': f.stat().st_size, 'sha256': sha_file(f)},
           'hostname': socket.gethostname(), 'gpu': torch.cuda.get_device_name(0),
           'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    with log.open('a') as fh: fh.write(json.dumps(rec, sort_keys=True) + '\n')
    print(f"[done] {key} s{seed} {rec['seconds']}s", flush=True)
print(json.dumps({'shard': f'{SHARD_I}/{SHARD_N}', 'jobs': len(jobs), 'seconds': round(time.time() - t0, 1)}))
