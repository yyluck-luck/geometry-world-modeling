#!/usr/bin/env python3
"""Does the shipped (NMS-disabled) retrieval read `initial_threshold`?  Zero diffusion.

This is the load-bearing premise for salvaging the sealed S111 comparison.  The
`initial_threshold` leak is known to have contaminated the NMS-ENABLED arm.  If the
NMS-DISABLED arm is provably independent of that attribute, then the sealed
`memory_nms_off` and `static` arms are uncontaminated and their paired contrast stands
without re-running anything.

Code reading says the disabled branch assigns `self.initial_threshold = 1e8` and then
reads it into `current_threshold`, but the only consumer of `current_threshold` is a
`while` loop guarded by `and use_non_maximum_suppression`, which is False.  Reading code
is not measurement.  This test forces the attribute to adversarial values before the
disabled call and requires the selection to be unchanged.

Values tested: the natively primed percentile, 1e8 (the leaked value), 1e-9 (below the
loop's 1e-5 floor), and 0.0.  A deleted attribute is also probed, because the read happens
unconditionally and would raise.
"""
import io, json, os, sys
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])

BANK_STEP = 5; BANK_SPAN = 60
TARGET_OFFSETS = [60, 75, 90, 105]
SCENES = {'scene_13': ('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13', 462),
          'scene_14': ('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14', 659)}
WINDOW_STARTS = [100, 200, 300]

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

MUTABLE_LIST_FIELDS = ('latents', 'encoder_embeddings', 'c2ws', 'Ks', 'pil_frames',
                       'surfels', 'surfel_Ks', 'surfel_depths', 'rgb_vae_latents',
                       'rgb_encoder_embeddings', 'poses', 'focal_lengths', 'all_pil_frames')

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
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
    pipe.get_context_info(torch.tensor(np.stack([load_pose(seq, bank_ids[4])]),
                                       device=device, dtype=torch.float32))
    primed = float(getattr(pipe, 'initial_threshold', float('nan')))
    for fid in bank_ids[5:]:
        _append(fid)
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
    return primed

def sel_off(bank_ids, qc2w):
    ctx = pipe.get_context_info(qc2w, use_non_maximum_suppression=False)
    raw = [int(i) for i in ctx['context_time_indices'].detach().cpu().numpy().ravel()]
    return ([bank_ids[i] for i in raw] * 4)[:4]

OUT.mkdir(parents=True, exist_ok=True)
rows, checks = [], []
for scene, (rel, nframes) in SCENES.items():
    root = DATA / rel; seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
    for start in WINDOW_STARTS:
        if start + max(TARGET_OFFSETS) >= nframes:
            continue
        qc2w = torch.tensor(np.stack([load_pose(seq, start + o) for o in TARGET_OFFSETS]),
                            device=device, dtype=torch.float32)
        bank_ids = [start + i for i in range(0, BANK_SPAN, BANK_STEP)]
        isolate_arm_state(pipe)
        primed = build_bank(seq, bank_ids, K0)

        out = {}
        out['primed'] = sel_off(bank_ids, qc2w)
        for name, val in (('leaked_1e8', 1e8), ('below_floor_1e-9', 1e-9), ('zero', 0.0),
                          ('reprimed_value', primed)):
            pipe.initial_threshold = val
            out[name] = sel_off(bank_ids, qc2w)

        # the attribute is read unconditionally, so removing it must raise
        delattr(pipe, 'initial_threshold')
        try:
            sel_off(bank_ids, qc2w)
            deleted = 'NO_ERROR'
        except Exception as exc:
            deleted = type(exc).__name__
        pipe.initial_threshold = primed

        same = all(out[k] == out['primed'] for k in out)
        rows.append({'scene': scene, 'window_start': start, 'primed_threshold': primed,
                     'selections': out, 'invariant': same, 'deleted_attribute_raises': deleted})
        checks.append((f'{scene} w{start}: NMS-disabled selection is invariant to initial_threshold', same))
        print(f'[{scene} w{start:03d}] invariant={same} primed={out["primed"]} '
              f'leaked={out["leaked_1e8"]} zero={out["zero"]} deleted->{deleted}', flush=True)

allpass = all(ok for _, ok in checks)
report = {'schema': 'nms-off-threshold-independence-v1', 'zero_diffusion': True,
          'reads_ground_truth': False,
          'question': 'is the shipped NMS-disabled retrieval independent of initial_threshold?',
          'consequence_if_pass': ('the sealed S111 memory_nms_off arm could not have been '
                                  'contaminated by the cross-arm threshold leak, and the '
                                  'static arm never calls get_context_info at all'),
          'rows': rows, 'checks': [{'name': n, 'pass': ok} for n, ok in checks],
          'status': 'PASS' if allpass else 'FAIL',
          'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'NMS_OFF_THRESHOLD_INDEPENDENCE.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
for n, ok in checks:
    print(('[PASS] ' if ok else '[FAIL] ') + n)
print(f"\n{sum(1 for _, ok in checks if ok)}/{len(checks)} checks passed -> {report['status']}")
