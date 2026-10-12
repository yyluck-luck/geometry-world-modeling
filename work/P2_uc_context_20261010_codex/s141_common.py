#!/usr/bin/env python3
"""S141 shared code: VMem model pieces (weights patched to local files as gen_s140.py), LoRA, the variant-B warp input
branch, image/pose loading identical to gen_s140.py, and conditioning built exactly as gen_s140.sample().

Env: RUN_ROOT (contains vmem/), WEIGHTS (vmem_weights.pth, VAE, open_clip, cut3r).
"""
import io, math, os, sys
from pathlib import Path
import numpy as np

RUN = Path(os.environ['RUN_ROOT']); WEIGHTS = Path(os.environ['WEIGHTS']); SOURCE = RUN / 'vmem'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'extern/CUT3R'), str(SOURCE / 'extern/CUT3R/src')]
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
import torch
import torch.nn as nn
import torch.nn.functional as F
from omegaconf import OmegaConf
import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip
huggingface_hub.hf_hub_download = lambda repo_id, filename, *a, **k: str(WEIGHTS / filename)
import modeling.pipeline as _pm
_pm.hf_hub_download = huggingface_hub.hf_hub_download
_ov = AutoencoderKL.from_pretrained
AutoencoderKL.from_pretrained = lambda repo, *a, **k: _ov(
    str(WEIGHTS), local_files_only=True, force_download=False, low_cpu_mem_usage=False, use_safetensors=True)
_oc = open_clip.create_model_and_transforms
open_clip.create_model_and_transforms = lambda name, *a, **k: _oc(name, pretrained=str(WEIGHTS / 'open_clip_model.safetensors'))
_ol = torch.load
def _vl(path, *a, **k):
    if str(path) in {str(WEIGHTS / 'vmem_weights.pth'), str(WEIGHTS / 'cut3r_512_dpt_4_64.pth')}:
        k['weights_only'] = False
    return _ol(path, *a, **k)
torch.load = _vl

from modeling.network import VMemModel, VMemModelParams, VMemWrapper
from modeling.modules.layers import timestep_embedding
from modeling.modules.transformer import Attention
from modeling.modules.autoencoder import AutoEncoder
from modeling.modules.conditioner import CLIPConditioner
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser
from modeling.pipeline import VMemPipeline
from PIL import Image

CFG = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
K7 = np.array([[585.0, 0, 320.0], [0, 585.0, 240.0], [0, 0, 1]], np.float32)   # 7-Scenes nominal RGB intrinsics
TRAIN_SCENES = ['fire', 'heads', 'office', 'pumpkin', 'redkitchen', 'stairs']  # chess is the held-out evaluation scene


# ---------------- data (identical transforms to gen_s140.py) ----------------
def model_grid_K(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k


def load_rgb_path(p):
    arr = np.asarray(Image.open(io.BytesIO(Path(p).read_bytes())).convert('RGB'))
    t = torch.from_numpy(arr.transpose(2, 0, 1).copy()).float() / 255.
    t = F.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2. - 1.)[0]


def load_pose_path(p):
    return np.loadtxt(io.StringIO(Path(p).read_text()), dtype=np.float32).reshape(4, 4)


def to_gl(c2w):  # gen_s140.convert(..., 'gl') on a (N,4,4) tensor
    out = c2w.clone(); out[:, :, [1, 2]] *= -1
    return out


# ---------------- model ----------------
def load_base_model(device='cuda'):
    model = VMemModel(VMemModelParams())
    sd = torch.load(str(WEIGHTS / 'vmem_weights.pth'), map_location='cpu')
    sd = {k.replace('module.', '') if 'module.' in k else k: v for k, v in sd.items()}
    model.load_state_dict(sd, strict=True)
    return model.to(device)


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r: int, alpha: float):
        super().__init__()
        self.base = base
        self.base.requires_grad_(False)
        self.down = nn.Linear(base.in_features, r, bias=False)
        self.up = nn.Linear(r, base.out_features, bias=False)
        nn.init.kaiming_uniform_(self.down.weight, a=math.sqrt(5))
        nn.init.zeros_(self.up.weight)                       # step 0: exactly the base layer
        self.scale = alpha / r

    def forward(self, x):
        return self.base(x) + self.up(self.down(x)) * self.scale


class WarpInConv(nn.Module):
    """input_blocks[0][0] for variant B: base 11-channel conv + zero-initialised conv on [warp latent(4), coverage(1)]."""
    def __init__(self, base: nn.Conv2d, extra: int = 5):
        super().__init__()
        self.base = base; self.n = base.in_channels
        self.warp = nn.Conv2d(extra, base.out_channels, 3, padding=1)
        nn.init.zeros_(self.warp.weight); nn.init.zeros_(self.warp.bias)

    def forward(self, x):
        return self.base(x[:, :self.n]) + self.warp(x[:, self.n:])


def add_adapters(model, r=16, alpha=16.0, warp=False):
    model.requires_grad_(False)
    n = 0
    for mod in list(model.modules()):
        if isinstance(mod, Attention):
            mod.to_q = LoRALinear(mod.to_q, r, alpha); mod.to_k = LoRALinear(mod.to_k, r, alpha)
            mod.to_v = LoRALinear(mod.to_v, r, alpha); mod.to_out[0] = LoRALinear(mod.to_out[0], r, alpha)
            n += 1
    if warp:
        model.input_blocks[0][0] = WarpInConv(model.input_blocks[0][0])
    dev = next(model.parameters()).device
    model.to(dev)
    trainable = [p for p in model.parameters() if p.requires_grad]
    return n, trainable


def adapter_state(model):
    return {k: v.detach().cpu() for k, v in model.state_dict().items() if ('.down.' in k or '.up.' in k or '.warp.' in k)}


def ckpt_forward(self, x, t, y, dense_y, num_frames=None):
    """VMemModel.forward with activation checkpointing per block (numerically the same function)."""
    from torch.utils.checkpoint import checkpoint
    num_frames = num_frames or self.params.num_frames
    t_emb = self.time_embed(timestep_embedding(t, self.model_channels))
    run = lambda m, h: checkpoint(m, h, t_emb, y, dense_y, num_frames, use_reentrant=False)
    hs = []; h = x
    for m in self.input_blocks:
        h = run(m, h); hs.append(h)
    h = run(self.middle_block, h)
    for m in self.output_blocks:
        h = run(m, torch.cat([h, hs.pop()], dim=1))
    h = h.type(x.dtype)
    return self.out(h)


# ---------------- conditioning (gen_s140.sample() up to get_cond) ----------------
def build_cond(lat, emb, c2ws, Ks, qc2w, qK, device='cuda'):
    carrier = object.__new__(VMemPipeline)
    carrier.camera_scale = 2.0; carrier.device = torch.device(device)
    carrier.dtype = torch.float32; carrier.config = CFG
    raw_all = torch.cat([c2ws, qc2w], 0)
    scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, raw_all.clone())
    all_K = torch.cat([Ks, qK.unsqueeze(0).repeat(qc2w.shape[0], 1, 1)], 0)
    mask = torch.tensor([True] * lat.shape[0] + [False] * qc2w.shape[0], device=device)
    return VMemPipeline.get_cond(carrier, lat, all_c2w, all_K, scale, emb, mask)


def extend_concat(cond_dict, warp5):
    """Append [warp latent, coverage] (targets) / zeros (contexts) to the concat channels of a c or uc dict."""
    d = dict(cond_dict)
    nctx = d['concat'].shape[0] - warp5.shape[0]
    extra = torch.cat([torch.zeros((nctx, *warp5.shape[1:]), device=warp5.device, dtype=d['concat'].dtype),
                       warp5.to(d['concat'].dtype)], 0)
    d['concat'] = torch.cat([d['concat'], extra], 1)
    return d
