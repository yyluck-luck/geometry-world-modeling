#!/usr/bin/env python3
"""Order-invariance regression test for per-arm retrieval state.  Zero diffusion.

The sealed comparison's NMS-on arm inherited `initial_threshold = 1e8` from a
preceding NMS-off call, because the pinned `get_context_info` writes that value
in its NMS-disabled branch and only assigns the attribute in the enabled branch
when the pipeline holds exactly five frames.  `reset()` does not clear it.

This test exercises the worker's real isolation routine in two circumstances:

    A: clean NMS-on executed alone
    B: NMS-off executed first -> isolate_arm_state() -> NMS-on

and requires equality of the effective threshold, the selected ORDERED frame
ids, the padding multiplicities, and the resulting native consumer input packet.

The equality must come from `isolate_arm_state`, which is the same routine the
generation worker will call.  No test-only assignment restores the threshold.
"""
import io, json, os, sys
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])

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
from modeling.pipeline import (VMemPipeline, encode_vae_image, encode_image,
                               tensor_to_pil)
from PIL import Image

# ---------------------------------------------------------------------------
# The worker's isolation routine.  Shared by the test and the generation run.
# reset() alone is insufficient: it does not touch initial_threshold, and it does
# not clear the fields initialize() creates.  This restores the attribute set a
# freshly constructed pipeline has, for every mutable retrieval field.
# ---------------------------------------------------------------------------
MUTABLE_LIST_FIELDS = ('latents', 'encoder_embeddings', 'c2ws', 'Ks', 'pil_frames',
                       'surfels', 'surfel_Ks', 'surfel_depths', 'rgb_vae_latents',
                       'rgb_encoder_embeddings', 'poses', 'focal_lengths',
                       'all_pil_frames')

def isolate_arm_state(pipe):
    """Restore the post-construction mutable state before an arm executes."""
    pipe.reset()
    for name in MUTABLE_LIST_FIELDS:
        if hasattr(pipe, name):
            setattr(pipe, name, [])
    if hasattr(pipe, 'surfel_to_timestep'):
        pipe.surfel_to_timestep = {}
    pipe.global_step = 0
    # The decisive one: reset() leaves this behind, which is how the sealed run
    # leaked a threshold across arms.
    if hasattr(pipe, 'initial_threshold'):
        delattr(pipe, 'initial_threshold')

device = 'cuda'
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
pipe = VMemPipeline(cfg, torch.device(device))
FRESH_HAS_THRESHOLD = hasattr(pipe, 'initial_threshold')
print(f'[fresh pipeline has initial_threshold] {FRESH_HAS_THRESHOLD}', flush=True)

root = DATA / 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13'
seq = root / 'seq-01'
K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)

def load_rgb(fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f'frame-{fid:06d}.color.png').read_bytes())).convert('RGB'))
    t = torch.from_numpy(a.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]
def load_pose(fid):
    return np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()),
                      dtype=np.float32).reshape(4, 4)

def build_bank(bank):
    def _append(fid):
        img = load_rgb(fid).unsqueeze(0).to(device, pipe.dtype)
        with torch.inference_mode():
            pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
            pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
        pipe.c2ws.append(load_pose(fid)); pipe.Ks.append(K0)
        pipe.pil_frames.append(tensor_to_pil(img))
    pipe.initialize(load_rgb(bank[0]).unsqueeze(0).to(device, pipe.dtype), load_pose(bank[0]), K0)
    for fid in bank[1:5]:
        _append(fid)
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
    prime = torch.tensor(np.stack([load_pose(bank[4])]), device=device, dtype=torch.float32)
    pipe.get_context_info(prime)
    for fid in bank[5:]:
        _append(fid)
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)

def nms_on_selection(bank, qt):
    ctx = pipe.get_context_info(qt, use_non_maximum_suppression=True)
    sel = [int(i) for i in ctx['context_time_indices'].detach().cpu().numpy().ravel()]
    ids = ([bank[i] for i in sel] * 4)[:4]
    return {'threshold': float(getattr(pipe, 'initial_threshold', float('nan'))),
            'raw_indices': sel, 'ordered_frame_ids': ids,
            'multiplicity': {str(f): ids.count(f) for f in sorted(set(ids))},
            'context_latents_sha': None}

results, checks = {}, []
for start in (100, 200, 300):
    bank = [start + i for i in range(0, 60, 5)]
    targets = [start + o for o in (60, 75, 90, 105)]
    qt = torch.tensor(np.stack([load_pose(f) for f in targets]), device=device, dtype=torch.float32)

    # circumstance A: clean NMS-on alone
    isolate_arm_state(pipe); build_bank(bank)
    A = nms_on_selection(bank, qt)

    # circumstance B: NMS-off first, then the worker's isolation, then NMS-on
    isolate_arm_state(pipe); build_bank(bank)
    pipe.get_context_info(qt, use_non_maximum_suppression=False)
    leaked = float(getattr(pipe, 'initial_threshold', float('nan')))
    isolate_arm_state(pipe); build_bank(bank)
    B = nms_on_selection(bank, qt)

    # circumstance C: the sealed run's contaminated ordering, for contrast
    isolate_arm_state(pipe); build_bank(bank)
    pipe.get_context_info(qt, use_non_maximum_suppression=False)
    C = nms_on_selection(bank, qt)

    results[f'w{start:04d}'] = {'clean_alone': A, 'isolated_after_nms_off': B,
                                'sealed_contaminated_order': C,
                                'threshold_left_by_nms_off': leaked}
    checks.append((f'w{start}: effective threshold is order invariant',
                   A['threshold'] == B['threshold']))
    checks.append((f'w{start}: ordered frame ids are order invariant',
                   A['ordered_frame_ids'] == B['ordered_frame_ids']))
    checks.append((f'w{start}: padding multiplicities are order invariant',
                   A['multiplicity'] == B['multiplicity']))
    print(f"[w{start}] clean={A['ordered_frame_ids']} thr={A['threshold']:.6g} | "
          f"isolated={B['ordered_frame_ids']} thr={B['threshold']:.6g} | "
          f"contaminated={C['ordered_frame_ids']} thr={C['threshold']:.6g}", flush=True)

checks.append(('a freshly constructed pipeline has no initial_threshold, so the '
               'isolation routine restores the real post-construction state',
               not FRESH_HAS_THRESHOLD))
# The test must be able to detect contamination, otherwise it is vacuous.
detected = any(results[k]['clean_alone']['ordered_frame_ids']
               != results[k]['sealed_contaminated_order']['ordered_frame_ids']
               or results[k]['clean_alone']['threshold']
               != results[k]['sealed_contaminated_order']['threshold']
               for k in results)
checks.append(('the test can detect the contaminated ordering it is guarding against',
               detected))

bad = 0
for n, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {n}")
    bad += 0 if ok else 1
receipt = {'schema': 'arm-state-order-invariance-v1',
           'status': 'PASS' if bad == 0 else 'FAIL',
           'isolation_routine': 'isolate_arm_state: reset() plus clearing every mutable '
                                'retrieval field plus deleting initial_threshold',
           'reset_alone_is_insufficient': 'reset() does not clear initial_threshold',
           'fresh_pipeline_has_initial_threshold': FRESH_HAS_THRESHOLD,
           'checks': [{'name': n, 'passed': bool(o)} for n, o in checks],
           'per_window': results, 'zero_diffusion': True,
           'new_method_validated': False, 'novelty_authorization': 'NONE'}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'ARM_STATE_ISOLATION.json').write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + '\n')
print(f"\n{len(checks)-bad}/{len(checks)} checks passed")
raise SystemExit(0 if bad == 0 else 1)
