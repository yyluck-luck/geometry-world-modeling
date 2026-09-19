#!/usr/bin/env python3
"""Slot-utilisation control: does the shipped retrieval's duplicated context slot matter?

Observation being tested (recorded before these outputs existed, in
`docs/UNCONTAMINATED_RETRIEVAL_RESULT_20260918.md`): the shipped NMS-disabled
retrieval delivers only three distinct frames into four context slots in 10 of 14
windows.  The cause is in the pinned source: the selection is seeded with
`sorted_frames[0]` (surfel-nearest candidate) and then `len(self.c2ws) - 1` (most
recent stored frame).  Under forward extrapolation those two collide, and the fill
step cannot recover the slot because the duplicate already counts toward
`len(selected_indices)`.

The intervention is the smallest one that is still the pipeline's own decision:
deduplicate the selection and let the remaining slots be filled from the
pipeline's own distance-ranked candidate list.  Nothing is trained, no weights
change, no new ranking or selection criterion is introduced, and no frame outside
the pipeline's own candidates is ever used.

Obtaining the ranked list without re-implementing it
----------------------------------------------------
`get_context_info` returns only the chosen indices.  Re-deriving `sorted_frames`
by hand would be a re-implementation, so the ranking is read out of the pipeline
itself by asking it for a longer selection.

`max_frames = min(config.model.context_num_frames, len(candidates), len(latents))`
and `average_c2w = average_camera_pose(target_c2ws[-context_num_frames//4:])`.
Python floor division gives -4//4 = -1 but -5//4 = -2, so simply raising
`context_num_frames` would also change which target poses define the query centre
and hence the ranking.  That is compensated exactly: the oracle call passes
`target_c2ws[-1:]` (length one), for which `[-2:]` and `[-1:]` select the same
single pose.  The ranking is therefore identical by construction, and only
`max_frames` differs.

This is verified rather than assumed: the first four oracle indices must equal the
normal call's indices in every window, or the window is refused.

Internal null control
---------------------
In the four windows where the shipped selection already has four distinct frames,
deduplication is a no-op, so the repaired arm must reproduce the sealed
`memory_nms_off` output byte for byte.  Those windows are not evidence for the
hypothesis; they are the check that the harness introduced nothing else.

Prospective decision rule, fixed before any score is computed: the duplication
explanation is retained only if the repaired arm beats the sealed shipped arm by
at least 0.20 dB in mean over the affected windows AND every unaffected window
reproduces byte-identically.  Below 0.20 dB the explanation is discarded and the
negative result stands with no mechanical account.  No novelty claim attaches to
this experiment under any outcome.
"""
import io, os, sys, json, time, random, socket, hashlib
import datetime as dt
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
SEEDS = [int(x) for x in os.environ.get('SEEDS', '42,7').split(',')]

BANK_STEP = 5; BANK_SPAN = 60
TARGET_OFFSETS = [60, 75, 90, 105]
SCENES = {'scene_13': ('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13', 462),
          'scene_14': ('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14', 659)}
WINDOW_STARTS = [0, 50, 100, 150, 200, 250, 300, 350]
ORACLE_CONTEXT_FRAMES = 7

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

from modeling.sampling import DDPMDiscretization, DiscreteDenoiser, create_samplers
from modeling.pipeline import VMemPipeline, encode_vae_image, encode_image, tensor_to_pil
from utils import do_sample

device = 'cuda'; dtype = torch.float32
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
NATIVE_CONTEXT_FRAMES = int(cfg.model.context_num_frames)
assert NATIVE_CONTEXT_FRAMES == 4, f'unexpected native context_num_frames {NATIVE_CONTEXT_FRAMES}'
torch.set_num_threads(8); torch.set_num_interop_threads(1)
STEPS = int(cfg.model.inference_num_steps); CFG = float(cfg.model.cfg)
CFG_MIN = float(cfg.model.cfg_min); GUIDER = int(cfg.model.guider_types)

pipe = VMemPipeline(cfg, torch.device(device))
print('[pipeline_ready]', flush=True)
model = pipe.model_wrapper; ae = pipe.vae; clip = pipe.image_encoder

MUTABLE_LIST_FIELDS = ('latents', 'encoder_embeddings', 'c2ws', 'Ks', 'pil_frames',
                       'surfels', 'surfel_Ks', 'surfel_depths', 'rgb_vae_latents',
                       'rgb_encoder_embeddings', 'poses', 'focal_lengths', 'all_pil_frames')

def isolate_arm_state(pipe):
    pipe.reset()
    for name in MUTABLE_LIST_FIELDS:
        if hasattr(pipe, name): setattr(pipe, name, [])
    if hasattr(pipe, 'surfel_to_timestep'): pipe.surfel_to_timestep = {}
    pipe.global_step = 0
    if hasattr(pipe, 'initial_threshold'): delattr(pipe, 'initial_threshold')

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

def raw_selection(qc2w):
    ctx = pipe.get_context_info(qc2w, use_non_maximum_suppression=False)
    return [int(i) for i in ctx['context_time_indices'].detach().cpu().numpy().ravel()]

def oracle_ranked(qc2w):
    """Longer selection from the pipeline itself, with the query centre held fixed."""
    pipe.config.model.context_num_frames = ORACLE_CONTEXT_FRAMES
    try:
        return raw_selection(qc2w[-1:])
    finally:
        pipe.config.model.context_num_frames = NATIVE_CONTEXT_FRAMES

def dedup(seq):
    out = []
    for x in seq:
        if x not in out: out.append(x)
    return out

OUT.mkdir(parents=True, exist_ok=True)
index, t0 = [], time.time()
for scene, (rel, nframes) in SCENES.items():
    root = DATA / rel; seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
    qK = model_grid_K(K0).to(device)
    for start in WINDOW_STARTS:
        if start + max(TARGET_OFFSETS) >= nframes: continue
        targets = [start + o for o in TARGET_OFFSETS]
        qc2w = torch.tensor(np.stack([load_pose(seq, f) for f in targets]), device=device, dtype=torch.float32)
        bank_ids = [start + i for i in range(0, BANK_SPAN, BANK_STEP)]
        rec = {'scene': scene, 'window_start': start, 'bank_frame_ids': bank_ids,
               'target_frame_ids': targets, 'arm': 'memory_nms_off_dedup'}
        try:
            isolate_arm_state(pipe)
            pipe.initialize(load_rgb(seq, bank_ids[0]).unsqueeze(0).to(device, pipe.dtype),
                            load_pose(seq, bank_ids[0]), K0)
            def _append(fid):
                img = load_rgb(seq, fid).unsqueeze(0).to(device, pipe.dtype)
                with torch.inference_mode():
                    pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
                    pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
                pipe.c2ws.append(load_pose(seq, fid)); pipe.Ks.append(K0)
                pipe.pil_frames.append(tensor_to_pil(img))
            for fid in bank_ids[1:5]: _append(fid)
            pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                           niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
            pipe.get_context_info(torch.tensor(np.stack([load_pose(seq, bank_ids[4])]),
                                               device=device, dtype=torch.float32))
            for fid in bank_ids[5:]: _append(fid)
            pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                           niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)

            shipped_raw = raw_selection(qc2w)
            ranked = oracle_ranked(qc2w)
            agrees = ranked[:len(shipped_raw)] == shipped_raw
            rec['oracle_prefix_agrees'] = agrees
            rec['shipped_raw_indices'] = shipped_raw
            rec['oracle_raw_indices'] = ranked
            if not agrees:
                rec['status'] = 'ORACLE_PREFIX_MISMATCH'
                index.append(rec)
                print(f'[refuse] {scene} w{start}: oracle prefix {ranked[:4]} != shipped {shipped_raw}', flush=True)
                continue
            shipped_ids = ([bank_ids[i] for i in shipped_raw] * 4)[:4]
            repaired_ids = dedup([bank_ids[i] for i in ranked])[:4]
            rec.update({'shipped_context_ids': shipped_ids, 'context_frame_ids': repaired_ids,
                        'shipped_unique': len(set(shipped_ids)),
                        'unique_context_frames': len(set(repaired_ids)),
                        'is_noop_window': repaired_ids == shipped_ids})
            if len(repaired_ids) < 4:
                rec['status'] = 'INSUFFICIENT_DISTINCT_CANDIDATES'
                index.append(rec)
                print(f'[refuse] {scene} w{start}: only {len(repaired_ids)} distinct candidates', flush=True)
                continue
        except Exception as exc:
            rec['status'] = 'SETUP_FAILED'; rec['error'] = f'{type(exc).__name__}: {exc}'
            index.append(rec); print(f'[skip] {scene} w{start}: {rec["error"]}', flush=True); continue

        ctx_ids = rec['context_frame_ids']
        imgs = torch.stack([load_rgb(seq, f) for f in ctx_ids]).to(device, dtype)
        Ks_t = torch.stack([model_grid_K(K0) for _ in ctx_ids]).to(device)
        c2ws = torch.tensor(np.stack([load_pose(seq, f) for f in ctx_ids]), device=device, dtype=torch.float32)
        with torch.inference_mode():
            lat = encode_vae_image(imgs, ae, device, dtype)
            emb = encode_image(imgs, clip, device, dtype)
        for seed in SEEDS:
            tgt = sample(lat, emb, c2ws, Ks_t, qc2w, qK, seed)
            tag = f'{scene}__w{start:04d}__memory_nms_off_dedup__s{seed}'
            f = OUT / f'{tag}.npy'; np.save(f, tgt, allow_pickle=False)
            index.append({**rec, 'tag': tag, 'seed': seed, 'status': 'OK',
                          'output': {'path': str(f), 'bytes': f.stat().st_size, 'sha256': sha_file(f)}})
            print(f'[done] {tag} shipped={rec["shipped_context_ids"]} -> repaired={ctx_ids} '
                  f'noop={rec["is_noop_window"]}', flush=True)

ok = [r for r in index if r.get('status') == 'OK']
receipt = {
    'schema': 'slot-utilisation-control-v1', 'status': 'RUNS_COMPLETE_UNSCORED',
    'question': ('does removing the duplicated context slot from the shipped retrieval change '
                 'the output, using only the pipeline\'s own candidate ranking?'),
    'intervention': ('deduplicate the pipeline\'s own selection and let the freed slots be '
                     'filled from its own distance-ranked candidate list; no training, no '
                     'weight change, no new ranking or selection criterion'),
    'ranking_source': ('read from the pipeline by asking for a longer selection with the query '
                       'centre held fixed via target_c2ws[-1:], verified by requiring the first '
                       'four oracle indices to equal the normal call'),
    'oracle_context_num_frames': ORACLE_CONTEXT_FRAMES,
    'native_context_num_frames': NATIVE_CONTEXT_FRAMES,
    'prospective_decision_rule': ('retain the duplication explanation only if the repaired arm '
                                  'beats the sealed shipped arm by >= 0.20 dB in mean over the '
                                  'affected windows AND every no-op window reproduces the sealed '
                                  'output byte-identically'),
    'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hostname': socket.gethostname(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
    'seeds': SEEDS, 'window_starts': WINDOW_STARTS, 'target_offsets': TARGET_OFFSETS,
    'bank_step': BANK_STEP, 'bank_span': BANK_SPAN,
    'all_oracle_prefixes_agree': all(r.get('oracle_prefix_agrees', False)
                                     for r in index if 'oracle_prefix_agrees' in r),
    'total_runs': len(ok), 'elapsed_seconds': round(time.time() - t0, 1),
    'runs': index, 'scored': False, 'scientific_result': False,
    'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'SLOT_CONTROL_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'runs'}, indent=2, sort_keys=True))
