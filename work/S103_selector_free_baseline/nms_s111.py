#!/usr/bin/env python3
"""S111: same question as S109, now including VMem's DEFAULT NMS-on retrieval.

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
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
SEEDS = [int(x) for x in os.environ.get('SEEDS', '42,7').split(',')]
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

OUT.mkdir(parents=True, exist_ok=True)
index, t0 = [], time.time()
for scene, (rel, nframes) in SCENES.items():
    root = DATA / rel; seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()),
                    dtype=np.float32).reshape(3, 3)
    qK = model_grid_K(K0).to(device)
    for start in WINDOW_STARTS:
        if start + max(TARGET_OFFSETS) >= nframes: continue
        targets = [start + o for o in TARGET_OFFSETS]
        qc2w = torch.tensor(np.stack([load_pose(seq, f) for f in targets]), device=device, dtype=torch.float32)
        bank_ids = [start + i for i in range(0, BANK_SPAN, BANK_STEP)]

        # ---------- MEMORY arms: prime the NMS threshold, then retrieve ----------
        # get_context_info assigns self.initial_threshold only inside
        #   if use_non_maximum_suppression: if is_second_step:   # len(pil_frames)==5
        # so with NMS enabled and any other frame count it raises AttributeError
        # (observed in job 594691).  The upstream source is pinned and is NOT
        # patched.  Instead the natural sequence is reproduced: the pipeline is
        # driven through the exact five-frame state in which the real application
        # computes the threshold.  The threshold is a median of pairwise geodesic
        # distances among STORED cameras and does not depend on the query, so the
        # priming query is one of the bank's own camera poses.  No target pose and
        # no future information is used for priming.
        retrieved = {'nms_off': None, 'nms_on': None}
        mem_err = {}
        try:
            pipe.initialize(load_rgb(seq, bank_ids[0]).unsqueeze(0).to(device, pipe.dtype),
                            load_pose(seq, bank_ids[0]), K0)
            def _append(fid):
                img = load_rgb(seq, fid).unsqueeze(0).to(device, pipe.dtype)
                with torch.inference_mode():
                    pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
                    pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
                pipe.c2ws.append(load_pose(seq, fid)); pipe.Ks.append(K0)
                pipe.pil_frames.append(tensor_to_pil(img))
            for fid in bank_ids[1:5]:
                _append(fid)
            require(len(pipe.pil_frames) == 5, 'priming state must hold exactly five frames')
            pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                           niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
            prime_q = torch.tensor(np.stack([load_pose(seq, bank_ids[4])]),
                                   device=device, dtype=torch.float32)
            pipe.get_context_info(prime_q)          # natural threshold assignment
            primed = float(getattr(pipe, 'initial_threshold', float('nan')))
            for fid in bank_ids[5:]:
                _append(fid)
            pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                           niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
            for variant, flag in (('nms_off', False), ('nms_on', True)):
                try:
                    ctx = pipe.get_context_info(qc2w, use_non_maximum_suppression=flag)
                    sel = [int(i) for i in ctx['context_time_indices'].detach().cpu().numpy().ravel()]
                    retrieved[variant] = [bank_ids[i] for i in sel]
                except Exception as exc:
                    mem_err[variant] = f'{type(exc).__name__}: {exc}'
        except Exception as exc:
            primed = None
            mem_err['setup'] = f'{type(exc).__name__}: {exc}'

        for arm in ('static', 'memory_nms_off', 'memory_nms_on'):
            if arm == 'static':
                ctx_ids = [start + o for o in STATIC_CTX_OFFSETS]
            else:
                got = retrieved[arm.replace('memory_', '')]
                if got is None: continue
                ctx_ids = (got * 4)[:4]
            imgs = torch.stack([load_rgb(seq, f) for f in ctx_ids]).to(device, dtype)
            Ks_t = torch.stack([model_grid_K(K0) for _ in ctx_ids]).to(device)
            c2ws = torch.tensor(np.stack([load_pose(seq, f) for f in ctx_ids]), device=device, dtype=torch.float32)
            with torch.inference_mode():
                lat = encode_vae_image(imgs, ae, device, dtype)
                emb = encode_image(imgs, clip, device, dtype)
            for seed in SEEDS:
                tgt = sample(lat, emb, c2ws, Ks_t, qc2w, qK, seed)
                tag = f'{scene}__w{start:04d}__{arm}__s{seed}'
                f = OUT / f'{tag}.npy'; np.save(f, tgt, allow_pickle=False)
                index.append({'tag': tag, 'scene': scene, 'window_start': start, 'arm': arm,
                              'seed': seed, 'context_frame_ids': ctx_ids,
                              'target_frame_ids': targets, 'bank_frame_ids': bank_ids,
                              'retrieved_frame_ids': retrieved, 'memory_error': mem_err,
                              'primed_threshold': primed,
                              'unique_context_frames': len(set(ctx_ids)),
                              'output': {'path': str(f), 'bytes': f.stat().st_size, 'sha256': sha_file(f)}})
                print(f'[done] {tag} ctx={ctx_ids}', flush=True)

receipt = {'schema': 's111-nms-on-vs-off-vs-static-v1', 'status': 'RUNS_COMPLETE_UNSCORED',
           'scope': ('development only; both arms receive identical real history frames; '
                     'the only difference is whether surfel memory and retrieval select the context'),
           'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'hostname': socket.gethostname(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
           'seeds': SEEDS, 'window_starts': WINDOW_STARTS, 'target_offsets': TARGET_OFFSETS,
           'static_context_offsets': STATIC_CTX_OFFSETS, 'bank_step': BANK_STEP,
           'threshold_priming': ('driven through the natural five-frame state with a bank camera as priming query; upstream source not patched'),
           'total_runs': len(index), 'elapsed_seconds': round(time.time() - t0, 1),
           'runs': index, 'scored': False, 'scientific_result': False,
           'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'NMS_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'runs'}, indent=2, sort_keys=True))
