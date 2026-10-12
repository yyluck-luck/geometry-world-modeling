#!/usr/bin/env python3
"""S141 evaluation generator: the S139/S140 VMem sampler (gen_s140.py header, unchanged) with the S141 adapters.
VARIANT=A: LoRA. VARIANT=B: LoRA + warp input branch; [warp latent, coverage] of the plan's warp files is appended to
concat for the targets (zeros for contexts) in both c and uc, as in training. ADAPTER=<adapter .pt> or NONE (adapters at
their zero initialisation: must reproduce the base model byte-for-byte). Plan contexts as gen_s140 (ctx_group, warp_files).
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



# ---------------- S141 adapters ----------------
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
os.environ.setdefault('RUN_ROOT', str(RUN)); os.environ.setdefault('WEIGHTS', str(WEIGHTS))
import s141_common as C
VARIANT = os.environ['VARIANT']; ADAPTER = os.environ.get('ADAPTER', 'NONE'); RANK = int(os.environ.get('RANK', '16'))
WARP_DIR = Path(os.environ.get('WARP_DIR', '.'))
torch.manual_seed(0)
n_attn, _ = C.add_adapters(pipe.model, r=RANK, alpha=float(RANK), warp=(VARIANT == 'B'))
ADAPTER_SHA = None
if ADAPTER != 'NONE':
    st = torch.load(ADAPTER, map_location='cpu', weights_only=False)
    assert st['variant'] == VARIANT and st['rank'] == RANK, (st['variant'], st['rank'])
    res = pipe.model.load_state_dict(st['adapter'], strict=False)
    assert not res.unexpected_keys and not [k for k in res.missing_keys if '.down.' in k or '.up.' in k or '.warp.' in k], res
    ADAPTER_SHA = sha_file(ADAPTER)
pipe.model.eval()
print(f'[s141] variant {VARIANT} adapter {ADAPTER} attn {n_attn}', flush=True)

def convert(c2w_batch, convention):  # identical to C9 convention_test_c9.convert
    if convention == 'native':
        return c2w_batch
    out = c2w_batch.clone(); out[:, :, [1, 2]] *= -1
    return out

def sample_s141(lat, emb, c2ws, Ks, qc2w, qK, seed, w5):   # gen_s140 sample() + concat extension for B
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
        c, uc = cond['c'], cond['uc']
        if w5 is not None:
            c = C.extend_concat(c, w5); uc = C.extend_concat(uc, w5)
        den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)
        sampler = create_samplers(guider_types=GUIDER, discretization=DDPMDiscretization(),
                                  num_frames=8, num_steps=STEPS, cfg_min=CFG_MIN, device=device)[0]
        outs = do_sample(model, ae, den, sampler, c, uc, cond['all_c2ws'],
                         cond['all_Ks'], cond['input_masks'], H=576, W=576, C=4, F=8, T=8,
                         cfg=CFG, decoding_t=1, verbose=False, global_pbar=None,
                         return_latents=True, device=device)
    return outs[0][4:].detach().float().cpu().numpy()

OUT.mkdir(parents=True, exist_ok=True)
P = json.loads(PLAN.read_text()); plan = P['contexts']
jobs = [(c, s) for c in plan for s in SEEDS]
jobs = [j for k_, j in enumerate(jobs) if k_ % SHARD_N == SHARD_I]
log = OUT / f'RUNS_{socket.gethostname()}_{os.getpid()}.jsonl'
t0 = time.time(); cache = {}
for c, seed in jobs:
    f = OUT / f"{c['ctx_key']}__s{seed}.npy"
    if f.exists(): continue
    root = DATA / c['scene_dir']
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
    qK = model_grid_K(K0).to(device)
    sp = lambda r: (root / r.split('/')[0], int(r.split('/')[1]))
    key0 = c['ctx_group']
    if key0 not in cache:
        cache.clear()
        imgs = torch.stack([load_rgb(*sp(r)) for r in c['ctx_refs']]).to(device, dtype)
        w5 = None
        with torch.inference_mode():
            lat = encode_vae_image(imgs, ae, device, dtype); emb = encode_image(imgs, clip, device, dtype)
            if VARIANT == 'B':
                ws = [np.load(WARP_DIR / wf) for wf in c['warp_files']]
                wimg = torch.stack([torch.from_numpy(z['filled'].astype(np.float32) / 255. * 2 - 1).permute(2, 0, 1) for z in ws]).to(device, dtype)
                cov = torch.stack([torch.nn.functional.avg_pool2d(torch.from_numpy(z['valid'].astype(np.float32))[None, None], 8)[0] for z in ws]).to(device)
                zw = encode_vae_image(wimg, ae, device, dtype)
                w5 = torch.cat([zw, cov], 1)
        cache[key0] = (lat, emb, w5)
    lat, emb, w5 = cache[key0]
    Ks_t = torch.stack([model_grid_K(K0) for _ in c['ctx_refs']]).to(device)
    c2ws = torch.tensor(np.stack([load_pose(*sp(r)) for r in c['ctx_refs']]), device=device, dtype=torch.float32)
    qc2w = torch.tensor(np.stack([load_pose(*sp(r)) for r in c['target_refs']]), device=device, dtype=torch.float32)
    conv = c.get('convention', 'gl'); c2ws = convert(c2ws, conv); qc2w = convert(qc2w, conv)
    ts = time.time()
    tgt = sample_s141(lat, emb, c2ws, Ks_t, qc2w, qK, seed, w5)
    # R254 F4: a numerical failure must stay a failure (no NaN-cast black frames reaching the scorer)
    if tgt.shape != (4, 3, 576, 576) or not np.isfinite(tgt).all():
        raise RuntimeError(f"bad output {c['ctx_key']} s{seed}: shape {tgt.shape} finite {bool(np.isfinite(tgt).all())}")
    tmp = f.with_suffix('.tmp.npy'); np.save(tmp, tgt, allow_pickle=False); tmp.rename(f)
    rec = {'ctx_key': c['ctx_key'], 'variant': VARIANT, 'adapter': ADAPTER, 'adapter_sha256': ADAPTER_SHA, 'window_id': c['window_id'],
           'seed': seed, 'seconds': round(time.time() - ts, 2), 'output': {'path': str(f), 'sha256': sha_file(f)},
           'hostname': socket.gethostname(), 'gpu': torch.cuda.get_device_name(0), 'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    with log.open('a') as fh: fh.write(json.dumps(rec, sort_keys=True) + '\n')
    print(f"[done] {c['ctx_key']} s{seed} {rec['seconds']}s", flush=True)
print(json.dumps({'jobs': len(jobs), 'seconds': round(time.time() - t0, 1)}))
