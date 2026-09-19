#!/usr/bin/env python3
"""Zero-diffusion census of what the leaked NMS threshold actually changes.

Motivation.  The sealed S111 comparison iterated ('nms_off', False) then
('nms_on', True) on one pipeline object, and `get_context_info` writes
`self.initial_threshold = 1e8` in its NMS-disabled branch.  The enabled branch
assigns the attribute only when the pipeline holds exactly five frames, so at
full bank the NMS-on arm inherited 1e8.  Job 595599 proved the worker's
`isolate_arm_state` removes that dependence (11/11, including a non-vacuity
check) and showed, on three scene_13 windows, that the leak's effect on the
selection is NOT uniform: one window was unchanged, one changed only the
ORDER of an identical frame multiset, one changed one frame.

This scan settles that question over the whole sealed panel BEFORE any
generation budget is spent, using only retrieval metadata.  It reads no ground
truth, decodes no target, and runs no diffusion.  Its output is the
pre-registration input for deciding which windows can carry which claim.

Three regimes are distinguished, on the PADDED context ids that actually reach
the consumer (S111 pads with `(got * 4)[:4]`):

    NULL         clean and leaked padded ids are identical
                 -> the leak cannot have changed this window's output at all
    PERMUTATION  identical multiset, different order
                 -> identical images, cameras, intrinsics and normalisation
                    input; any output difference is a pure slot-order effect
    CONTENT      the multiset differs
                 -> at least one different image enters the consumer

Per-window context c2ws are recorded so any normalisation scale can be derived
offline without re-running the model.
"""
import io, json, os, sys, time, hashlib
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])

# ---- sealed S111 panel definition, copied verbatim from nms_s111.py ----------
BANK_STEP = 5; BANK_SPAN = 60          # bank = start .. start+55 step 5 (12 frames)
TARGET_OFFSETS = [60, 75, 90, 105]
SCENES = {'scene_13': ('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13', 462),
          'scene_14': ('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14', 659)}
WINDOW_STARTS = [0, 50, 100, 150, 200, 250, 300, 350]

SOURCE = RUN / 'vmem'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'extern/CUT3R'), str(SOURCE / 'extern/CUT3R/src')]
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
import torch
from omegaconf import OmegaConf
import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip
huggingface_hub.hf_hub_download = lambda repo_id, filename, *a, **k: str(WEIGHTS / filename)
import modeling.pipeline as PM
PM.hf_hub_download = huggingface_hub.hf_hub_download
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
from modeling.pipeline import VMemPipeline, encode_vae_image, encode_image, tensor_to_pil
from PIL import Image

# ---- the worker's isolation routine, identical to the one job 595599 gated ---
MUTABLE_LIST_FIELDS = ('latents', 'encoder_embeddings', 'c2ws', 'Ks', 'pil_frames',
                       'surfels', 'surfel_Ks', 'surfel_depths', 'rgb_vae_latents',
                       'rgb_encoder_embeddings', 'poses', 'focal_lengths',
                       'all_pil_frames')

def isolate_arm_state(pipe):
    pipe.reset()
    for name in MUTABLE_LIST_FIELDS:
        if hasattr(pipe, name):
            setattr(pipe, name, [])
    if hasattr(pipe, 'surfel_to_timestep'):
        pipe.surfel_to_timestep = {}
    pipe.global_step = 0
    if hasattr(pipe, 'initial_threshold'):
        delattr(pipe, 'initial_threshold')

device = 'cuda'
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
pipe = VMemPipeline(cfg, torch.device(device))

def load_rgb(seq, fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f'frame-{fid:06d}.color.png').read_bytes())).convert('RGB'))
    t = torch.from_numpy(a.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]

def load_pose(seq, fid):
    return np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()),
                      dtype=np.float32).reshape(4, 4)

def build_bank(seq, bank_ids, K0):
    """Reproduce the sealed run's bank construction, including the five-frame
    priming state in which the pinned source assigns initial_threshold."""
    def _append(fid):
        img = load_rgb(seq, fid).unsqueeze(0).to(device, pipe.dtype)
        with torch.inference_mode():
            pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
            pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
        pipe.c2ws.append(load_pose(seq, fid)); pipe.Ks.append(K0)
        pipe.pil_frames.append(tensor_to_pil(img))
    pipe.initialize(load_rgb(seq, bank_ids[0]).unsqueeze(0).to(device, pipe.dtype),
                    load_pose(seq, bank_ids[0]), K0)
    for fid in bank_ids[1:5]:
        _append(fid)
    assert len(pipe.pil_frames) == 5, 'priming state must hold exactly five frames'
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
    prime_q = torch.tensor(np.stack([load_pose(seq, bank_ids[4])]), device=device, dtype=torch.float32)
    pipe.get_context_info(prime_q)          # native threshold assignment
    primed = float(getattr(pipe, 'initial_threshold', float('nan')))
    for fid in bank_ids[5:]:
        _append(fid)
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
    return primed

def select(seq, bank_ids, qc2w, flag):
    ctx = pipe.get_context_info(qc2w, use_non_maximum_suppression=flag)
    raw = [int(i) for i in ctx['context_time_indices'].detach().cpu().numpy().ravel()]
    got = [bank_ids[i] for i in raw]
    padded = (got * 4)[:4]                       # exactly what S111 feeds the consumer
    return {'threshold': float(getattr(pipe, 'initial_threshold', float('nan'))),
            'raw_indices': raw, 'retrieved_frame_ids': got, 'padded_context_ids': padded,
            'slot0': padded[0], 'unique_context_frames': len(set(padded)),
            'multiplicity': {str(f): padded.count(f) for f in sorted(set(padded))},
            'context_c2ws': [load_pose(seq, f).tolist() for f in padded]}

def regime(clean, leaked):
    if clean['padded_context_ids'] == leaked['padded_context_ids']:
        return 'NULL'
    if sorted(clean['padded_context_ids']) == sorted(leaked['padded_context_ids']):
        return 'PERMUTATION'
    return 'CONTENT'

OUT.mkdir(parents=True, exist_ok=True)
windows, errors, t0 = [], [], time.time()
for scene, (rel, nframes) in SCENES.items():
    root = DATA / rel; seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()),
                    dtype=np.float32).reshape(3, 3)
    for start in WINDOW_STARTS:
        if start + max(TARGET_OFFSETS) >= nframes:
            continue
        targets = [start + o for o in TARGET_OFFSETS]
        qc2w = torch.tensor(np.stack([load_pose(seq, f) for f in targets]),
                            device=device, dtype=torch.float32)
        bank_ids = [start + i for i in range(0, BANK_SPAN, BANK_STEP)]
        rec = {'scene': scene, 'window_start': start, 'bank_frame_ids': bank_ids,
               'target_frame_ids': targets}
        try:
            # build 1: clean NMS-on FIRST, so no preceding call can have written
            # the threshold; then reproduce the sealed off->on order in place.
            isolate_arm_state(pipe)
            rec['primed_threshold'] = build_bank(seq, bank_ids, K0)
            clean = select(seq, bank_ids, qc2w, True)
            recency = select(seq, bank_ids, qc2w, False)
            leaked_same_build = select(seq, bank_ids, qc2w, True)

            # build 2: independent rebuild running only the sealed off->on order,
            # to check that measuring clean first did not perturb the leaked arm.
            isolate_arm_state(pipe)
            build_bank(seq, bank_ids, K0)
            select(seq, bank_ids, qc2w, False)
            leaked_fresh = select(seq, bank_ids, qc2w, True)

            rec.update({
                'clean_nms_on': clean,
                'recency_nms_off': recency,
                'leaked_nms_on': leaked_fresh,
                'single_build_shortcut_agrees': (
                    leaked_same_build['padded_context_ids'] == leaked_fresh['padded_context_ids']
                    and leaked_same_build['threshold'] == leaked_fresh['threshold']),
                'leaked_nms_on_same_build': leaked_same_build,
                'regime': regime(clean, leaked_fresh),
                'slot0_invariant_to_leak': clean['slot0'] == leaked_fresh['slot0'],
                'clean_equals_recency': clean['padded_context_ids'] == recency['padded_context_ids'],
                'leaked_equals_recency': leaked_fresh['padded_context_ids'] == recency['padded_context_ids'],
                'status': 'OK'})
        except Exception as exc:
            rec.update({'status': 'ERROR', 'error': f'{type(exc).__name__}: {exc}'})
            errors.append(f'{scene} w{start}: {rec["error"]}')
        windows.append(rec)
        print(f'[{scene} w{start:03d}] {rec.get("regime", rec["status"])} '
              f'clean={rec.get("clean_nms_on", {}).get("padded_context_ids")} '
              f'leaked={rec.get("leaked_nms_on", {}).get("padded_context_ids")} '
              f'recency={rec.get("recency_nms_off", {}).get("padded_context_ids")}', flush=True)

ok = [w for w in windows if w['status'] == 'OK']
census = {r: sum(1 for w in ok if w['regime'] == r) for r in ('NULL', 'PERMUTATION', 'CONTENT')}
report = {
    'schema': 'leak-regime-census-v1',
    'zero_diffusion': True,
    'reads_ground_truth': False,
    'panel': {'scenes': list(SCENES), 'window_starts': WINDOW_STARTS,
              'bank_step': BANK_STEP, 'bank_span': BANK_SPAN,
              'target_offsets': TARGET_OFFSETS},
    'gated_by': 'job 595599 arm-state-order-invariance-v1 PASS (11/11)',
    'windows_attempted': len(windows), 'windows_ok': len(ok),
    'regime_census': census,
    'slot0_invariant_in_all_ok_windows': all(w['slot0_invariant_to_leak'] for w in ok),
    'single_build_shortcut_agrees_everywhere': all(w['single_build_shortcut_agrees'] for w in ok),
    'errors': errors,
    'windows': windows,
    'new_method_validated': False,
    'novelty_authorization': 'NONE',
    'elapsed_s': round(time.time() - t0, 1),
}
p = OUT / 'LEAK_REGIME_CENSUS.json'
p.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'regime_census': census, 'windows_ok': len(ok),
                  'slot0_invariant': report['slot0_invariant_in_all_ok_windows'],
                  'shortcut_agrees': report['single_build_shortcut_agrees_everywhere'],
                  'errors': errors}, indent=2))
print(f'wrote {p}')
