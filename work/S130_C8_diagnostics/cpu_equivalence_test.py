#!/usr/bin/env python3
"""CPU gate for C8 RS equivalence. Requires the existing VMem runtime and a real S107 pose receipt.

The script intentionally fails closed when torch, the pinned source, or the real pose receipt is absent.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
try:
    import torch
except Exception as exc:
    print(f"[BLOCKED] torch import failed: {type(exc).__name__}: {exc}")
    print("[BLOCKED] No CPU equivalence claim was made; run this exact script in the recorded VMem runtime.")
    raise SystemExit(2)

pose_path = os.environ.get("C8_S107_POSES")
if not pose_path or not Path(pose_path).exists():
    print("[BLOCKED] C8_S107_POSES is missing or does not point to a real S107 pose receipt.")
    print("[BLOCKED] Refusing synthetic poses; no equivalence claim was made.")
    raise SystemExit(2)

run_root = Path(os.environ.get("C8_RUN_ROOT", "/home/yliutz/gwm_source_transport_20260915"))
sys.path[:0] = [str(run_root / "vmem"), str(run_root / "vmem/extern/CUT3R"), str(run_root / "vmem/extern/CUT3R/src")]
from omegaconf import OmegaConf
from modeling.pipeline import VMemPipeline
from factorized_conditioning import build_conditioning, multiset_permutation

payload = json.loads(Path(pose_path).read_text())
poses = torch.tensor(payload["poses"], dtype=torch.float32)
if poses.shape != (8, 4, 4):
    raise RuntimeError(f"expected 8 real context+target poses, got {tuple(poses.shape)}")
config = OmegaConf.load(str(run_root / "vmem/configs/inference/inference.yaml"))
carrier = object.__new__(VMemPipeline)
carrier.camera_scale = float(config.model.camera_scale); carrier.device = torch.device("cpu"); carrier.dtype = torch.float32; carrier.config = config
latents = torch.randn(4, 4, 8, 8)
emb = torch.randn(4, 16)
Ks = torch.eye(3).repeat(8, 1, 1)
mask = torch.tensor([True] * 4 + [False] * 4)
a = [int(x) for x in payload["order_a"]]
b = [int(x) for x in payload["order_b"]]
perm = multiset_permutation(a, b)
# `perm[j]` gives the A index of B slot j.  To reorder B back into A slot
# order, take the inverse mapping.
invperm = [perm.index(i) for i in range(4)]
ref = poses[0].clone()

def reorder(x):
    # context slots are permuted; target slots remain fixed.
    return torch.cat([x[invperm], x[4:]], dim=0)

out_a = {}; out_b = {}
for convention in ("N", "R", "S", "RS"):
    out_a[convention] = build_conditioning(carrier, latents, poses, Ks, emb, mask, convention, ref)
    out_b[convention] = build_conditioning(carrier, latents[perm], poses[perm + [4,5,6,7]], Ks[perm + [4,5,6,7]], emb[perm], mask, convention, ref)
    maxdiff = 0.0
    for key in ("concat", "dense_vector", "replace", "crossattn"):
        xa = out_a[convention]["c"][key]
        xb = reorder(out_b[convention]["c"][key])
        maxdiff = max(maxdiff, float((xa - xb).abs().max()))
    print(f"[{convention}] permuted_condition_max_abs_diff={maxdiff:.9g}")
    if convention == "RS" and maxdiff > 1e-6:
        raise SystemExit("RS equivalence failed")
    if convention == "N" and maxdiff <= 1e-6:
        raise SystemExit("N unexpectedly invariant")
print("[PASS] RS is exactly a slot permutation; N is not invariant.")
