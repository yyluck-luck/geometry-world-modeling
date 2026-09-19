#!/usr/bin/env python3
"""Crossed context x ray-reference intervention on the existing comparison windows.

Motivation, from an external adversarial review (2026-09-18).  The native
memory-versus-recency contrast changes two things at once:

    retrieval policy -> { selected ordered context , ray-coordinate reference }

because get_cond calls get_plucker_coordinates(extrinsics_src=all_w2cs[:1], ...),
so the first context frame defines the reference frame for every ray.  The
observed native difference therefore cannot be attributed to the visual evidence
alone.

Design.  For each window freeze the two contexts the policies actually select:
    C_R : recency's ordered context          g_R : reference induced by C_R[0]
    C_M : native memory's ordered context    g_M : reference induced by C_M[0]
and evaluate all four cells

    a = Y(C_R, g_R)   native recency        b = Y(C_R, g_M)
    c = Y(C_M, g_R)                         d = Y(C_M, g_M)   native memory

giving the exact identity
    Delta_native   = d - a
    Delta_context  = ((c - a) + (d - b)) / 2
    Delta_reference= ((b - a) + (d - c)) / 2
    Delta_native   = Delta_context + Delta_reference
and the interaction I = (d - b) - (c - a).

Off-diagonal cells are NOT produced by permuting context frames.  Each row keeps
its images, order, multiplicities and physical camera-image association fixed;
only the numerical reference used to express the ray conditioning is changed, via
an input-conditioning override of extrinsics_src.  No model or weight is changed.

DECLARED LIMITATION.  get_translation_scaling_factor derives the translation
scale from the first camera's distance to the centroid, so the scale is also
coupled to slot 0.  This experiment overrides only the ray-origin reference; the
scale stays with the context.  Delta_reference therefore isolates the ray-origin
frame, and any scale component remains inside Delta_context.  The algebraic
identity still holds exactly because it is a decomposition of the four measured
cells.

DEVELOPMENT scope.  Same windows, same frozen RGB metric, same weights.
"""
import datetime as dt, hashlib, io, json, os, random, socket, sys, time
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
SEEDS = [int(x) for x in os.environ.get('SEEDS', '42,7,13,29').split(',')]
NULL_CONTROL_ONLY = os.environ.get('NULL_CONTROL_ONLY', '0') == '1'
# When set, the override is never installed and the pipeline's own
# all_w2cs[:1] is used.  Comparing this against the null override (which
# supplies the native slot-0 pose explicitly) is the self-contained
# correctness control: the two must agree byte for byte.
OVERRIDE_DISABLED = os.environ.get('OVERRIDE_DISABLED', '0') == '1'

SCENES = {'scene_13': ('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13', 462),
          'scene_14': ('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14', 659)}
# The sealed comparison for this contrast has memory artefacts at starts
# 50..350 only; start 0 terminated with a retrieval failure in the original
# run, so no sealed memory endpoint exists there.  Using the original
# paired population for this contrast rather than a differently chosen set.
WINDOW_STARTS = [50, 100, 150, 200, 250, 300, 350]
TARGET_OFFSETS = [60, 75, 90, 105]
BANK_STEP, BANK_SPAN = 5, 60
# The earlier negative result compared native memory against this fixed
# spread context, so C_R must be the same arm for the decomposition to
# explain that result rather than a different comparison.
BASELINE_OFFSETS = [0, 15, 30, 45]

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

from modeling.network import VMemModel, VMemModelParams, VMemWrapper
from modeling.modules.autoencoder import AutoEncoder
from modeling.modules.conditioner import CLIPConditioner
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser, create_samplers
from modeling.pipeline import VMemPipeline, encode_vae_image, encode_image, tensor_to_pil
from utils import do_sample

# ---- input-conditioning override of the ray reference -----------------------
_REF_OVERRIDE = {"w2c": None, "used": 0}
_orig_plucker = PM.get_plucker_coordinates
def _plucker_with_reference_override(extrinsics_src, extrinsics, intrinsics, target_size, **kw):
    if _REF_OVERRIDE["w2c"] is not None:
        extrinsics_src = _REF_OVERRIDE["w2c"]
        _REF_OVERRIDE["used"] += 1
    return _orig_plucker(extrinsics_src=extrinsics_src, extrinsics=extrinsics,
                         intrinsics=intrinsics, target_size=target_size, **kw)
PM.get_plucker_coordinates = _plucker_with_reference_override

device, dtype = 'cuda', torch.float32
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
torch.set_num_threads(8); torch.set_num_interop_threads(1)
STEPS = int(cfg.model.inference_num_steps); CFG = float(cfg.model.cfg)
CFG_MIN = float(cfg.model.cfg_min); GUIDER = int(cfg.model.guider_types)

pipe = VMemPipeline(cfg, torch.device(device))
model, ae, clip = pipe.model_wrapper, pipe.vae, pipe.image_encoder
print('[pipeline_ready]', flush=True)

from PIL import Image
def gridK(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k
def load_rgb(seq, fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f'frame-{fid:06d}.color.png').read_bytes())).convert('RGB'))
    t = torch.from_numpy(a.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]
def load_pose(seq, fid):
    return np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()),
                      dtype=np.float32).reshape(4, 4)

def generate(seq, K0, ctx_ids, target_ids, seed, reference_c2w_raw):
    """One cell.  reference_c2w_raw is the RAW (un-centred) c2w whose inverse becomes
    extrinsics_src.  Passing ctx's own first pose reproduces native behaviour."""
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    imgs = torch.stack([load_rgb(seq, f) for f in ctx_ids]).to(device, dtype)
    Ks = torch.stack([gridK(K0) for _ in ctx_ids]).to(device)
    c2ws = torch.tensor(np.stack([load_pose(seq, f) for f in ctx_ids]), device=device, dtype=torch.float32)
    qc2w = torch.tensor(np.stack([load_pose(seq, f) for f in target_ids]), device=device, dtype=torch.float32)
    carrier = object.__new__(VMemPipeline)
    carrier.camera_scale = 2.0; carrier.device = torch.device(device)
    carrier.dtype = torch.float32; carrier.config = cfg
    with torch.inference_mode():
        lat = encode_vae_image(imgs, ae, device, dtype)
        emb = encode_image(imgs, clip, device, dtype)
        raw_all = torch.cat([c2ws, qc2w], 0)
        raw_before = raw_all.clone()
        scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, raw_all.clone())
        # Recover the centring offset this cell applied, then express the
        # designated reference pose in the same centred frame.
        # The reference must reach the call site through the SAME chain get_cond
        # applies, not merely the centring step.  get_cond performs, in order:
        #     all_c2ws[:, :, [1, 2]] *= -1        (R -> R diag(1,-1,-1))
        #     all_w2cs = inv(all_c2ws)
        #     all_w2cs[:, :3, 3] *= translation_scaling_factor
        # An external reference that skipped the flip, the inversion or the scale
        # would not be the same quantity the pipeline passes as extrinsics_src.
        # The physical reference CAMERA is moved into this cell's frame; a matrix
        # already normalised inside the other cell is never copied across, which
        # would import that cell's centre and scale.
        offset = (raw_before[:, :3, 3] - all_c2w[:, :3, 3]).mean(0)
        ref = torch.tensor(reference_c2w_raw, device=device, dtype=torch.float32).clone()
        ref[:3, 3] -= offset
        ref[:, [1, 2]] *= -1
        ref_w2c = torch.linalg.inv(ref)
        ref_w2c[:3, 3] *= scale
        _REF_OVERRIDE["w2c"] = None if OVERRIDE_DISABLED else ref_w2c.unsqueeze(0)
        _REF_OVERRIDE["used"] = 0
        qK = gridK(K0).to(device)
        all_K = torch.cat([Ks, qK.unsqueeze(0).repeat(len(target_ids), 1, 1)], 0)
        mask = torch.tensor([True] * 4 + [False] * 4, device=device)
        cond = VMemPipeline.get_cond(carrier, lat, all_c2w, all_K, scale, emb, mask)
        used = _REF_OVERRIDE["used"]; _REF_OVERRIDE["w2c"] = None
        den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)
        smp = create_samplers(guider_types=GUIDER, discretization=DDPMDiscretization(),
                              num_frames=8, num_steps=STEPS, cfg_min=CFG_MIN, device=device)[0]
        outs = do_sample(model, ae, den, smp, cond['c'], cond['uc'], cond['all_c2ws'],
                         cond['all_Ks'], cond['input_masks'], H=576, W=576, C=4, F=8, T=8,
                         cfg=CFG, decoding_t=1, verbose=False, global_pbar=None,
                         return_latents=True, device=device)
    expected = 0 if OVERRIDE_DISABLED else 1
    require(used == expected, f"reference override applied {used} times, expected {expected}")
    return outs[0][4:].detach().float().cpu().numpy()

OUT.mkdir(parents=True, exist_ok=True)
index, t0 = [], time.time()
for scene, (rel, nframes) in SCENES.items():
    root = DATA / rel; seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
    for start in WINDOW_STARTS:
        if start + max(TARGET_OFFSETS) >= nframes: continue
        targets = [start + o for o in TARGET_OFFSETS]
        baseline = [start + o for o in BASELINE_OFFSETS]
        bank = [start + i for i in range(0, BANK_SPAN, BANK_STEP)]

        # Native memory context, NMS on (the pinned inference.yaml value).
        # This reproduces the ORIGINAL sealed comparison's derivation step for
        # step.  The earlier crossover draft deviated in three ways and produced
        # different memory contexts, so its cells could not decompose the sealed
        # result: it primed the NMS threshold with TARGET poses instead of a bank
        # pose, it built the scene once instead of twice, and it padded a short
        # retrieval by repeating the last element instead of cycling.
        memory, mem_err = None, None
        try:
            def _append(fid):
                img = load_rgb(seq, fid).unsqueeze(0).to(device, pipe.dtype)
                with torch.inference_mode():
                    pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
                    pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
                pipe.c2ws.append(load_pose(seq, fid)); pipe.Ks.append(K0)
                pipe.pil_frames.append(tensor_to_pil(img))

            pipe.initialize(load_rgb(seq, bank[0]).unsqueeze(0).to(device, pipe.dtype),
                            load_pose(seq, bank[0]), K0)
            for fid in bank[1:5]:
                _append(fid)
            require(len(pipe.pil_frames) == 5, 'priming state must hold exactly five frames')
            pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                           niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
            prime_q = torch.tensor(np.stack([load_pose(seq, bank[4])]),
                                   device=device, dtype=torch.float32)
            pipe.get_context_info(prime_q)          # natural threshold assignment
            for fid in bank[5:]:
                _append(fid)
            pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                           niter=cfg.surfel.niter, lr=cfg.surfel.lr, device=device)
            qc2w = torch.tensor(np.stack([load_pose(seq, f) for f in targets]),
                                device=device, dtype=torch.float32)
            # The sealed original iterated ('nms_off', False) then ('nms_on', True).
            # That ordering is load-bearing: with NMS disabled get_context_info
            # executes `self.initial_threshold = 1e8`, and the following NMS-on
            # call does not reassign the attribute unless the pipeline happens to
            # hold exactly five frames, so it INHERITS 1e8 from the preceding
            # call.  Calling NMS-on alone uses the naturally primed threshold and
            # yields a different selection.  The original NMS-on arm therefore ran
            # under a threshold leaked across arms; that is a property of the
            # sealed run being decomposed, reproduced here rather than corrected.
            _ = pipe.get_context_info(qc2w, use_non_maximum_suppression=False)
            leaked_threshold = float(getattr(pipe, 'initial_threshold', float('nan')))
            ctx = pipe.get_context_info(qc2w, use_non_maximum_suppression=True)
            sel = [int(i) for i in ctx['context_time_indices'].detach().cpu().numpy().ravel()]
            memory = ([bank[i] for i in sel] * 4)[:4]
        except Exception as exc:
            mem_err = f'{type(exc).__name__}: {exc}'
        if memory is None:
            index.append({'scene': scene, 'window_start': start, 'terminal_failure': mem_err,
                          'cells_completed': 0})
            print(f'[terminal_failure] {scene} w{start}: {mem_err}', flush=True)
            continue

        gR = load_pose(seq, baseline[0]); gM = load_pose(seq, memory[0])
        cells = {'a_CR_gR': (baseline, gR), 'b_CR_gM': (baseline, gM),
                 'c_CM_gR': (memory, gR), 'd_CM_gM': (memory, gM)}
        if NULL_CONTROL_ONLY:
            cells = {'a_CR_gR': (baseline, gR), 'd_CM_gM': (memory, gM)}
        for seed in SEEDS:
            for name, (ctx_ids, ref) in cells.items():
                arr = generate(seq, K0, ctx_ids, targets, seed, ref)
                tag = f'{scene}__w{start:04d}__{name}__s{seed}'
                f = OUT / f'{tag}.npy'; np.save(f, arr, allow_pickle=False)
                index.append({'tag': tag, 'scene': scene, 'window_start': start, 'cell': name,
                              'seed': seed, 'context_frame_ids': ctx_ids,
                              'reference_frame_id': baseline[0] if ref is gR else memory[0],
                              'target_frame_ids': targets, 'baseline_context': baseline,
                              'memory_context': memory,
                              'inherited_nms_threshold': leaked_threshold,
                              'output': {'path': str(f), 'bytes': f.stat().st_size,
                                         'sha256': sha_file(f)}})
                print(f'[cell] {tag} ctx={ctx_ids} ref={index[-1]["reference_frame_id"]}', flush=True)

receipt = {'schema': 'context-reference-crossover-v1',
           'status': 'CELLS_COMPLETE_UNSCORED',
           'scope': 'development; same windows as the earlier memory-versus-recency comparison',
           'null_control_only': NULL_CONTROL_ONLY,
           'override_disabled': OVERRIDE_DISABLED,
           'intervention': ('input-conditioning override of get_plucker_coordinates '
                            'extrinsics_src; context images, order and multiplicity unchanged'),
           'decomposition_labels': {
               'row_quantity': 'context PACKAGE = selected ordered context together with its native translation scale',
               'delta_context_package': 'NOT a pure visual-content effect; the native scale travels with the row',
               'delta_reference': 'effect of changing the reference camera pose at each row native scale',
               'identity_is_algebraic': 'the four-number identity holds for any four numbers and is not by itself a causal decomposition'},
           'declared_limitation': ('translation scale is derived from the first context camera and '
                                   'is NOT overridden; Delta_reference isolates the ray-origin '
                                   'frame only and any scale component stays inside Delta_context'),
           'recorded_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'hostname': socket.gethostname(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
           'seeds': SEEDS, 'nms': 'on (pinned inference.yaml value)',
           'total_runs': len([r for r in index if 'tag' in r]),
           'elapsed_seconds': round(time.time() - t0, 1), 'runs': index,
           'scored': False, 'scientific_result': False,
           'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'CROSSOVER_RECEIPT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'runs'}, indent=2, sort_keys=True))
