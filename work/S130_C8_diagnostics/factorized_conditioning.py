"""Thin, source-preserving conditioning wrapper for C8 Experiment 1.

The module imports the pinned VMem pipeline only at call time. It implements N/R/S/RS
by controlling the ray reference and/or translation scale passed into get_cond; no
pinned source file is edited. It is intended to run in the existing remote runtime.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import torch

@dataclass(frozen=True)
class Convention:
    name: str
    fixed_reference: bool
    fixed_scale: bool

CONVENTIONS = {
    "N": Convention("N", False, False),
    "R": Convention("R", True, False),
    "S": Convention("S", False, True),
    "RS": Convention("RS", True, True),
}

def _center_like_native(pipeline, raw_all: torch.Tensor):
    """Copy pipeline.py:1098-1107 without changing the input tensor."""
    c2ws = raw_all.clone()
    ref = c2ws
    dist = torch.norm(ref[:, :3, 3] - ref[:, :3, 3].median(0, keepdim=True).values, dim=-1)
    valid = dist <= torch.clamp(torch.quantile(dist, 0.97) * 10, max=1e6)
    offset = ref[valid, :3, 3].mean(0, keepdim=True)
    c2ws[:, :3, 3] -= offset
    return c2ws, offset

def _native_scale(pipeline, centered: torch.Tensor):
    d = torch.norm(centered[:, :3, 3], dim=-1)
    return pipeline.camera_scale if torch.isclose(d[0], torch.zeros(1, device=pipeline.device, dtype=pipeline.dtype), atol=1e-5).any() else pipeline.camera_scale / d[0] + 0.01

def _w2c_reference(ref_raw: torch.Tensor, center_offset: torch.Tensor, scale: torch.Tensor):
    """Express a physical reference in the exact frame used by get_cond."""
    # centered_all and ref_raw share the same native centering offset.
    ref = ref_raw.clone()
    ref[:3, 3] -= center_offset[0]
    ref[:, [1, 2]] *= -1
    w2c = torch.linalg.inv(ref)
    w2c[:3, 3] *= scale
    return w2c.unsqueeze(0)

def build_conditioning(pipeline, context_latents, raw_all, all_Ks, encoder_embeddings, input_masks,
                       convention: str, reference_physical: Optional[torch.Tensor] = None):
    """Return the real VMem condition dictionary under one preregistered convention."""
    c = CONVENTIONS[convention]
    centered, center_offset = _center_like_native(pipeline, raw_all)
    native_scale = _native_scale(pipeline, centered)
    fixed_scale = native_scale
    if c.fixed_scale:
        if reference_physical is None:
            raise ValueError("S/RS require the physical reference pose from order A slot 0")
        # The scale is defined from the fixed physical reference after the same centering.
        ref_centered = reference_physical.clone()
        ref_centered[:3, 3] -= center_offset[0]
        rd = torch.norm(ref_centered[:3, 3])
        fixed_scale = pipeline.camera_scale if torch.isclose(rd, torch.zeros(1, device=rd.device, dtype=rd.dtype), atol=1e-5).any() else pipeline.camera_scale / rd + 0.01
    ref_w2c = None
    if c.fixed_reference:
        if reference_physical is None:
            raise ValueError("R/RS require the physical reference pose from order A slot 0")
        ref_w2c = _w2c_reference(reference_physical, center_offset, fixed_scale)
    # get_cond mutates its all_c2ws argument, so pass a fresh clone.
    module = __import__(pipeline.__class__.__module__, fromlist=["get_plucker_coordinates"])
    original = module.get_plucker_coordinates
    used = {"count": 0}
    def patched(extrinsics_src, extrinsics, intrinsics, target_size, **kwargs):
        if ref_w2c is not None:
            used["count"] += 1
            extrinsics_src = ref_w2c
        return original(extrinsics_src, extrinsics, intrinsics, target_size, **kwargs)
    module.get_plucker_coordinates = patched
    try:
        result = pipeline.get_cond(context_latents.clone(), centered.clone(), all_Ks.clone(), fixed_scale,
                                   encoder_embeddings.clone(), input_masks.clone())
    finally:
        module.get_plucker_coordinates = original
    result["c8_convention"] = convention
    result["c8_reference_override_calls"] = used["count"]
    return result

def multiset_permutation(order_a, order_b):
    """Return A indices in B order, consuming duplicate IDs once."""
    unused = list(range(len(order_a))); out = []
    for value in order_b:
        hits = [i for i in unused if order_a[i] == value]
        if not hits:
            raise ValueError(f"orders are not the same multiset: {order_a} vs {order_b}")
        out.append(hits[0]); unused.remove(hits[0])
    return out
