#!/usr/bin/env python3
"""S105 development probe: does VMem's geometric retrieval actually run, and
what does it select when the bank is larger than k?

Scope: development feasibility only.  Precedent is the S104 CUT3R component
inference (job 586719): a component-level smoke, not a scored experiment.

It does NOT score, does NOT open any future RGB or depth, and cannot: the stage
contains bank frames 0..55 and target POSES only.  No generation is performed.

The question it answers is narrow and factual: given 12 candidate history frames
and four target cameras, which four frames does VMem's surfel retrieval choose,
and do they match the hardcoded 0/15/30/45 used by the selector-free baseline?
"""
import datetime as dt, hashlib, io, json, os, socket, sys, time
from pathlib import Path

STAGE = Path(os.environ["BANK_STAGE"])
OUT = Path(os.environ["PROBE_OUT"])
RUN = Path(os.environ.get("RUN_ROOT", "/home/yliutz/gwm_source_transport_20260915"))
WEIGHTS = Path("/home/yliutz/gwm_weights_20260915")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

stages = []
def mark(name, **kw):
    stages.append(dict(stage=name, at=dt.datetime.now(dt.timezone.utc).isoformat(), **kw))
    print(f"[{name}] {kw}", flush=True)

SOURCE = RUN / "vmem"
sys.path[:0] = [str(SOURCE), str(SOURCE / "extern/CUT3R"), str(SOURCE / "extern/CUT3R/src")]
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")

import numpy as np, torch
from omegaconf import OmegaConf
mark("imports_ok", torch=torch.__version__, cuda=torch.cuda.is_available())

# Redirect every hub download to the locally hash-verified weight files.
import huggingface_hub
_TABLE = {("liguang0115/vmem", "vmem_weights.pth"): WEIGHTS / "vmem_weights.pth",
          ("liguang0115/cut3r", "cut3r_512_dpt_4_64.pth"): WEIGHTS / "cut3r_512_dpt_4_64.pth"}
def _local_hub(repo_id=None, filename=None, **kw):
    key = (repo_id, filename)
    if key not in _TABLE:
        raise RuntimeError(f"unexpected hub request: {key}")
    return str(_TABLE[key])
huggingface_hub.hf_hub_download = _local_hub
import modeling.pipeline as pipeline_mod
pipeline_mod.hf_hub_download = _local_hub

from diffusers.models import AutoencoderKL
_orig_vae = AutoencoderKL.from_pretrained
AutoencoderKL.from_pretrained = lambda *a, **k: _orig_vae(str(WEIGHTS), torch_dtype=k.get("torch_dtype"))
import open_clip
_orig_clip = open_clip.create_model_and_transforms
open_clip.create_model_and_transforms = lambda name, *a, **k: _orig_clip(
    name, pretrained=str(WEIGHTS / "open_clip_model.safetensors"))
_orig_load = torch.load
def _load(f, *a, **k):
    if str(f) in {str(_TABLE[k2]) for k2 in _TABLE}: k["weights_only"] = False
    return _orig_load(f, *a, **k)
torch.load = _load
mark("hub_redirected")

manifest = json.loads((STAGE / "BANK_MANIFEST.json").read_text())
bank_ids = manifest["bank_frame_ids"]; target_ids = manifest["target_frame_ids"]
assert manifest["future_rgb_staged"] is False and max(bank_ids) < min(target_ids)
mark("stage_loaded", bank=len(bank_ids), targets=target_ids)

cfg = OmegaConf.load(str(SOURCE / "configs/inference/inference.yaml"))
from modeling.pipeline import VMemPipeline
t0 = time.time()
pipe = VMemPipeline(cfg, torch.device("cuda"))     # <-- the real __init__
mark("pipeline_constructed", seconds=round(time.time() - t0, 2),
     has_surfel_model=hasattr(pipe, "surfel_model"),
     has_global_aligner=hasattr(pipe, "GlobalAlignerMode"))

from PIL import Image
def load_rgb(fid):
    p = STAGE / "bank" / f"frame-{fid:06d}.color.png"
    arr = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert("RGB"))
    t = torch.from_numpy(arr.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode="area")[:, :, :, 96:672]
    return (t * 2. - 1.).to("cuda", pipe.dtype)

def load_pose(fid, sub):
    p = STAGE / sub / f"frame-{fid:06d}.pose.txt"
    return np.loadtxt(io.StringIO(p.read_text()), dtype=np.float32).reshape(4, 4)

K = np.loadtxt(io.StringIO((STAGE / "camera-intrinsics.txt").read_text()), dtype=np.float32).reshape(3, 3)

# Build the bank from real observations.  initialize() seeds the state with the
# first frame; the remaining frames are appended in the same fields it creates.
from modeling.pipeline import encode_vae_image, encode_image, tensor_to_pil
pipe.initialize(load_rgb(bank_ids[0]), load_pose(bank_ids[0], "bank"), K)
for fid in bank_ids[1:]:
    img = load_rgb(fid)
    with torch.inference_mode():
        pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
        pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
    pipe.c2ws.append(load_pose(fid, "bank")); pipe.Ks.append(K)
    pipe.pil_frames.append(tensor_to_pil(img))
mark("bank_built", frames=len(pipe.c2ws), latents=len(pipe.latents))

t1 = time.time()
pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                               niter=cfg.surfel.niter, lr=cfg.surfel.lr, device="cuda")
mark("scene_constructed", seconds=round(time.time() - t1, 2),
     surfel_count=int(len(pipe.surfels)) if hasattr(pipe, "surfels") else None)

# average_camera_pose indexes with [:, :3, :3], so a stacked tensor is required;
# job 594690 failed because a list of arrays was passed instead.
target_c2ws = torch.from_numpy(np.stack([load_pose(f, "query") for f in target_ids])).to("cuda")
# Upstream fragility found in job 594691: get_context_info assigns
# self.initial_threshold only inside "if use_non_maximum_suppression: if
# is_second_step:", where is_second_step means len(self.pil_frames) == 5.  With
# NMS enabled and any other frame count the attribute is missing and the call
# raises AttributeError.  The normal app flow hides this because initialize()
# leaves one frame and the first generation step adds four.  Both arms are run
# rather than patching upstream: arm A disables NMS through the documented
# parameter; arm B reproduces the five-frame state the code expects.
# Instrument the visibility step so the receipt reports a measurement rather
# than an inference.  Job 594696 returned two duplicate slots, which is only
# consistent with max_frames = min(k, len(candidates), ...) == 1, i.e. exactly
# one bank frame visible from the targets.  Capture that directly.
VISIBILITY = {}
_orig_prsi = pipe.process_retrieved_spatial_information
def _traced_prsi(retrieved_spatial_information):
    out = _orig_prsi(retrieved_spatial_information)
    try:
        counts = out[1]
        VISIBILITY["frame_count_raw"] = {str(k): int(v) for k, v in dict(counts).items()} \
            if hasattr(counts, "items") else str(counts)
        VISIBILITY["n_visible_frames"] = len(counts) if hasattr(counts, "__len__") else None
    except Exception as exc:
        VISIBILITY["trace_error"] = f"{type(exc).__name__}: {exc}"
    return out
pipe.process_retrieved_spatial_information = _traced_prsi

arms = {}

t2 = time.time()
ctx_nonms = pipe.get_context_info(target_c2ws, use_non_maximum_suppression=False)
arms["A_nms_off"] = {"seconds": round(time.time() - t2, 2), "ctx": ctx_nonms}
mark("retrieval_arm_A_done", seconds=arms["A_nms_off"]["seconds"])

ctx = ctx_nonms  # default for the extraction below

def extract_indices(obj):
    if isinstance(obj, dict):
        for key in ("context_time_indices", "context_indices", "indices",
                    "selected_indices", "context_frame_indices"):
            if key in obj: return list(obj[key])
        for v in obj.values():
            r = extract_indices(v)
            if r: return r
    if isinstance(obj, (list, tuple)) and obj and all(isinstance(x, int) for x in obj):
        return list(obj)
    return None

def summarize(obj):
    idx = extract_indices(obj)
    sel = [bank_ids[i] for i in idx] if idx and max(idx) < len(bank_ids) else None
    return {"raw_indices": idx, "frame_ids": sel,
            "keys": sorted(obj.keys()) if isinstance(obj, dict) else None}

summary = {"A_nms_off": summarize(ctx_nonms)}

# Arm B: rebuild the bank incrementally so the pipeline passes through the
# five-frame state that populates self.initial_threshold, then extend to full
# size and query again with NMS enabled.
try:
    pipe_b_ok = False
    pipe = VMemPipeline(cfg, torch.device("cuda"))
    pipe.initialize(load_rgb(bank_ids[0]), load_pose(bank_ids[0], "bank"), K)
    for fid in bank_ids[1:5]:
        img = load_rgb(fid)
        with torch.inference_mode():
            pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
            pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
        pipe.c2ws.append(load_pose(fid, "bank")); pipe.Ks.append(K)
        pipe.pil_frames.append(tensor_to_pil(img))
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device="cuda")
    _ = pipe.get_context_info(target_c2ws)      # five-frame state sets the threshold
    mark("arm_B_threshold_primed", value=float(getattr(pipe, "initial_threshold", float("nan"))))
    for fid in bank_ids[5:]:
        img = load_rgb(fid)
        with torch.inference_mode():
            pipe.latents.append(encode_vae_image(img, pipe.vae, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
            pipe.encoder_embeddings.append(encode_image(img, pipe.image_encoder, pipe.device, pipe.dtype).detach().cpu().numpy()[0])
        pipe.c2ws.append(load_pose(fid, "bank")); pipe.Ks.append(K)
        pipe.pil_frames.append(tensor_to_pil(img))
    pipe.construct_and_store_scene(pipe.pil_frames, list(range(len(pipe.pil_frames))),
                                   niter=cfg.surfel.niter, lr=cfg.surfel.lr, device="cuda")
    ctx_nms = pipe.get_context_info(target_c2ws)
    summary["B_nms_on"] = summarize(ctx_nms)
    pipe_b_ok = True
    mark("retrieval_arm_B_done", frames=len(pipe.c2ws))
except Exception as exc:
    summary["B_nms_on"] = {"failed": f"{type(exc).__name__}: {exc}"}
    mark("retrieval_arm_B_failed", error=str(exc)[:200])

idx = summary["A_nms_off"]["raw_indices"]
selected = summary["A_nms_off"]["frame_ids"]
hardcoded = [0, 15, 30, 45]
receipt = {
    "schema": "s105-retrieval-feasibility-probe-v1",
    "status": "RETRIEVAL_PATH_EXECUTED",
    "scope": "development feasibility smoke; no scoring, no generation, no future outcome access",
    "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "hostname": socket.gethostname(), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "bank_frame_ids": bank_ids, "bank_size": len(bank_ids),
    "target_frame_ids": target_ids, "selection_k": cfg.model.context_num_frames,
    "retrieved_raw_indices": idx,
    "retrieved_frame_ids": selected,
    "selector_free_baseline_used": hardcoded,
    "retrieval_matches_hardcoded_baseline": (sorted(selected) == sorted(hardcoded)) if selected else None,
    "context_keys": sorted(ctx.keys()) if isinstance(ctx, dict) else None,
    "arms": summary,
    "visibility_measurement": VISIBILITY,
    "bank_frame_for_index_11": 55,
    "upstream_fragility": ("get_context_info assigns self.initial_threshold only when "
                           "use_non_maximum_suppression is true AND len(pil_frames)==5; "
                           "any other state raises AttributeError (observed in job 594691)"),
    "stages": stages,
    "future_rgb_opened": False, "future_depth_opened": False,
    "scored": False, "generation_performed": False,
    "scientific_result": False, "new_method_validated": False, "novelty_authorization": "NONE",
    "claim_boundary": ("Establishes only that the retrieval path executes and what it "
                       "selects for this bank and these targets. No quality, geometry, "
                       "memory-benefit or method claim follows."),
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "RETRIEVAL_PROBE_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n")
print(json.dumps(receipt, indent=2, sort_keys=True, default=str))
