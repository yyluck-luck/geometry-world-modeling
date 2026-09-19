#!/usr/bin/env python3
"""Check official CUT3R imports and RoPE backends without loading any weights.

This is an environment/component check, not a model prediction or quality test.
Run inside .venv-cut3r, with an independently pinned official CUT3R checkout.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def git_text(repo, *args):
    git = "/usr/bin/git" if sys.platform == "darwin" else "git"
    return subprocess.check_output(
        [git, "-C", str(repo), *args], text=True
    ).strip()


def package_versions():
    result = {}
    for name in (
        "torch", "torchvision", "numpy", "scipy", "pillow", "transformers",
        "accelerate", "einops", "roma", "opencv-python-headless", "tqdm",
        "huggingface-hub", "safetensors", "tokenizers", "omegaconf",
    ):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.output.exists():
        parser.error("Output exists; choose a new filename to preserve prior checks.")

    report = {
        "started_utc": utc_now(),
        "evidence_level": "untrained_component_and_import_check",
        "checkpoint_loaded": False,
        "model_instantiated": False,
        "images_processed": 0,
        "repo": str(repo),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "versions": package_versions(),
        "seed": 0,
        "tolerances": {"absolute": 1e-5, "relative": 1e-4},
    }
    try:
        report["commit"] = git_text(repo, "rev-parse", "HEAD")
        report["tracked_changes"] = git_text(
            repo, "status", "--porcelain", "--untracked-files=no"
        )
        report["source_sha256"] = {
            name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
            for name in (
                "LICENSE", "src/dust3r/model.py",
                "src/croco/models/pos_embed.py",
            )
        }
        sys.path.insert(0, str(repo / "src"))
        sys.path.insert(1, str(repo / "src" / "croco"))
        import torch

        report["cuda_available"] = torch.cuda.is_available()
        report["mps_built"] = torch.backends.mps.is_built()
        report["mps_available"] = torch.backends.mps.is_available()

        # Importing the class does not instantiate a model or load a checkpoint.
        try:
            module = importlib.import_module("dust3r.model")
            report["model_import"] = {
                "ok": hasattr(module, "ARCroco3DStereo"),
                "class": "dust3r.model.ARCroco3DStereo",
                "source": module.__file__,
            }
        except Exception:
            report["model_import"] = {"ok": False, "error": traceback.format_exc()}

        pos_embed = importlib.import_module("models.pos_embed")
        rope_class = pos_embed.RoPE2D
        report["rope_implementation"] = {
            "class_module": rope_class.__module__,
            "source": pos_embed.__file__,
            "pytorch_fallback": rope_class.__module__ == "models.pos_embed",
        }
        generator = torch.Generator(device="cpu").manual_seed(0)
        tokens = torch.randn((2, 4, 16, 32), generator=generator, dtype=torch.float32)
        yy, xx = torch.meshgrid(torch.arange(4), torch.arange(4), indexing="ij")
        positions = torch.stack((yy.flatten(), xx.flatten()), dim=-1)
        positions = positions.unsqueeze(0).repeat(2, 1, 1)
        atol, rtol = 1e-5, 1e-4

        with torch.inference_mode():
            cpu_rope = rope_class(freq=100.0)
            cpu_output = cpu_rope(tokens, positions)
            zero_output = cpu_rope(tokens, torch.zeros_like(positions))
            finite = bool(torch.isfinite(cpu_output).all())
            identity_ok = bool(torch.equal(zero_output, tokens))
            norm_ok = bool(torch.allclose(
                torch.linalg.vector_norm(tokens, dim=-1),
                torch.linalg.vector_norm(cpu_output, dim=-1), atol=atol, rtol=rtol,
            ))
            report["cpu_rope"] = {
                "ok": finite and identity_ok and norm_ok,
                "shape": list(cpu_output.shape),
                "dtype": str(cpu_output.dtype),
                "all_finite": finite,
                "zero_position_identity_exact": identity_ok,
                "vector_norm_preserved_within_tolerance": norm_ok,
                "max_zero_position_absolute_error": float((zero_output-tokens).abs().max()),
            }

            if report["mps_available"]:
                try:
                    mps_rope = rope_class(freq=100.0).to("mps")
                    mps_output = mps_rope(tokens.to("mps"), positions.to("mps"))
                    torch.mps.synchronize()
                    mps_on_cpu = mps_output.cpu()
                    finite = bool(torch.isfinite(mps_on_cpu).all())
                    close = bool(torch.allclose(cpu_output, mps_on_cpu, atol=atol, rtol=rtol))
                    report["mps_rope"] = {
                        "ok": finite and close,
                        "all_finite": finite,
                        "matches_cpu_within_tolerance": close,
                        "max_absolute_error_vs_cpu": float((mps_on_cpu-cpu_output).abs().max()),
                    }
                except Exception:
                    report["mps_rope"] = {"ok": False, "error": traceback.format_exc()}
            else:
                report["mps_rope"] = {"ok": None, "skipped": "MPS unavailable"}

        report["ok"] = (
            report["model_import"]["ok"]
            and report["rope_implementation"]["pytorch_fallback"]
            and report["cpu_rope"]["ok"]
            and report["mps_rope"]["ok"] is not False
        )
    except Exception:
        report["ok"] = False
        report["error"] = traceback.format_exc()
    report["completed_utc"] = utc_now()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
