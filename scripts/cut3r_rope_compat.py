#!/usr/bin/env python3
"""Signed-position compatibility for official CUT3R's PyTorch RoPE fallback.

Adapted from CUT3R/CroCo positional embedding code, CC BY-NC-SA 4.0,
Copyright (C) 2022-present Naver Corporation. All rights reserved.
Pinned upstream: CUT3R/CUT3R commit 8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf.
This implements the signed-angle formula in the official CUDA kernel; it is a
runtime compatibility change, not an architectural or research contribution.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback


def signed_forward(self, tokens, positions):
    import torch
    if self.F0 != 1.0:
        raise ValueError("This compatibility adapter is validated only for F0=1")
    if tokens.size(3) % 4 or positions.ndim != 3 or positions.shape[-1] != 2:
        raise ValueError("Expected BxHeadsxTokensxD (D divisible by 4) and BxTokensx2 positions")
    half_dimension = tokens.size(3) // 2
    cos, sin = self.get_cos_sin(
        half_dimension, int(positions.abs().max())+1, tokens.device, tokens.dtype
    )

    def rotate_axis(values, axis_positions):
        indices = axis_positions.abs()
        axis_cos = torch.nn.functional.embedding(indices, cos)[:, None, :, :]
        axis_sin = torch.nn.functional.embedding(indices, sin)[:, None, :, :]
        axis_sin = axis_sin * axis_positions.sign()[:, None, :, None]
        return values * axis_cos + self.rotate_half(values) * axis_sin

    y, x = tokens.chunk(2, dim=-1)
    return torch.cat((rotate_axis(y, positions[:, :, 0]),
                      rotate_axis(x, positions[:, :, 1])), dim=-1)


def install(rope_class):
    if rope_class.__module__ != "models.pos_embed":
        raise ValueError("Adapter applies only to the official pure PyTorch fallback")
    if rope_class.forward is signed_forward:
        return
    rope_class.forward = signed_forward


def check_main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args = p.parse_args()
    if args.output.exists(): p.error("Refusing to overwrite earlier validation")
    report = {"started_utc":datetime.now(timezone.utc).isoformat(),
              "evidence_level":"signed_rope_formula_and_backend_check",
              "checkpoint_loaded":False,"images_processed":0,"model_instantiated":False,
              "atol":1e-5,"rtol":1e-4,"seed":0,"base":100.0,"F0":1.0,
              "adapter_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        import numpy as np
        import torch
        repo=args.repo.resolve()
        git="/usr/bin/git" if sys.platform=="darwin" else "git"
        report["commit"]=subprocess.check_output([git,"-C",str(repo),"rev-parse","HEAD"],text=True).strip()
        report["cuda_kernel_sha256"]=hashlib.sha256((repo/"src/croco/models/curope/kernels.cu").read_bytes()).hexdigest()
        report["torch_version"]=torch.__version__
        sys.path.insert(0,str(repo/"src/croco"))
        from models.pos_embed import RoPE2D
        generator=torch.Generator(device="cpu").manual_seed(0)
        tokens=torch.randn((2,4,17,64),generator=generator,dtype=torch.float32)
        positions=torch.randint(-8,15,(2,17,2),generator=generator)
        positions[:,0,:]=-1
        positions[:,1,:]=0
        positions[:,2,:]=14
        positions[:,3,:]=torch.tensor([-19,2])
        positions[:,4,:]=torch.tensor([2,-19])
        original=RoPE2D(freq=100.0)
        with torch.inference_mode():
            original_nonnegative=original(tokens,positions.abs())
            original_nonnegative_mps=None
            if torch.backends.mps.is_available():
                original_nonnegative_mps=RoPE2D(freq=100.0).to("mps")(tokens.to("mps"),positions.abs().to("mps")).cpu()
            try:
                original(tokens,positions)
            except IndexError:
                report["original_negative_positions_raise_indexerror"]=True
            else:
                raise AssertionError("Expected original negative-position failure was not reproduced")

        # Independent scalar rotation layout from kernels.cu: Q=D_full/4;
        # theta=position/base**(j/Q), then (u*c-v*s,v*c+u*s).
        a=tokens.numpy().astype(np.float64)
        pos=positions.numpy()
        reference=np.empty_like(a)
        quarter=a.shape[-1]//4
        for axis in (0,1):
            for j in range(quarter):
                theta=pos[:,:,axis]/(100.0**(j/quarter))
                c=np.cos(theta)[:,None,:];s=np.sin(theta)[:,None,:]
                ui=axis*2*quarter+j;vi=ui+quarter
                reference[...,ui]=a[...,ui]*c-a[...,vi]*s
                reference[...,vi]=a[...,vi]*c+a[...,ui]*s
        install(RoPE2D)
        with torch.inference_mode():
            adapted=RoPE2D(freq=100.0)
            cpu=adapted(tokens,positions)
            positive=adapted(tokens,positions.abs())
            report["nonnegative_cpu_exact_match"]=bool(torch.equal(positive,original_nonnegative))
            report["cpu_all_finite"]=bool(torch.isfinite(cpu).all())
            report["cpu_matches_cuda_source_formula"]=bool(np.allclose(cpu.numpy(),reference,atol=1e-5,rtol=1e-4))
            report["cpu_max_absolute_error_vs_formula"]=float(np.abs(cpu.numpy()-reference).max())
            # Covers all-negative inputs, for which max(pos)+1 is not sufficient.
            negative=adapted(tokens,-positions.abs()-1)
            report["all_negative_case_finite"]=bool(torch.isfinite(negative).all())
            report["mps_available"]=torch.backends.mps.is_available()
            if report["mps_available"]:
                mps=RoPE2D(freq=100.0).to("mps")(tokens.to("mps"),positions.to("mps"))
                torch.mps.synchronize();mps=mps.cpu()
                report["mps_all_finite"]=bool(torch.isfinite(mps).all())
                report["mps_matches_cpu"]=bool(torch.allclose(mps,cpu,atol=1e-5,rtol=1e-4))
                report["mps_matches_cuda_source_formula"]=bool(np.allclose(mps.numpy(),reference,atol=1e-5,rtol=1e-4))
                report["mps_max_absolute_error_vs_cpu"]=float((mps-cpu).abs().max())
                nonnegative_mps=RoPE2D(freq=100.0).to("mps")(tokens.to("mps"),positions.abs().to("mps")).cpu()
                report["nonnegative_mps_exact_match"]=bool(torch.equal(nonnegative_mps,original_nonnegative_mps))
            else:
                raise RuntimeError("MPS unavailable for this local comparison protocol")
        flags=["nonnegative_cpu_exact_match","cpu_all_finite","cpu_matches_cuda_source_formula",
               "all_negative_case_finite","mps_all_finite","mps_matches_cpu","mps_matches_cuda_source_formula",
               "nonnegative_mps_exact_match"]
        report["ok"]=all(report[name] for name in flags)
    except Exception:
        report["ok"]=False;report["error"]=traceback.format_exc()
    report["completed_utc"]=datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if report["ok"] else 1


if __name__=="__main__":
    raise SystemExit(check_main())
