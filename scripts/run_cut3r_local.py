#!/usr/bin/env python3
"""Run pinned official CUT3R on explicit images, recording raw numeric outputs.

The input-view schema follows CUT3R/demo.py (CC BY-NC-SA 4.0).
This runs independent CUT3R, not VMem cleaning, memory retrieval, or video generation.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import contextlib
from datetime import datetime, timezone
from functools import partial
import hashlib
import io
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            digest.update(block)
    return digest.hexdigest()


def configuration_json(value):
    """Serialize configuration callables by stable names, never memory addresses."""
    if isinstance(value, dict):
        result = {}
        for key,item in value.items():
            if not isinstance(key, (str,int)):
                raise TypeError(f"Configuration has an unsupported dictionary key: {type(key)}")
            normalized_key = str(key)
            if normalized_key in result:
                raise ValueError(f"Configuration key collision after JSON normalization: {normalized_key}")
            result[normalized_key] = configuration_json(item)
        return result
    if isinstance(value, (tuple,list)):
        return [configuration_json(item) for item in value]
    if isinstance(value, partial):
        return {"partial":f"{value.func.__module__}.{value.func.__qualname__}",
                "args":configuration_json(value.args), "keywords":configuration_json(value.keywords)}
    if isinstance(value, type):
        return {"class":f"{value.__module__}.{value.__qualname__}"}
    if isinstance(value, float) and not math.isfinite(value):
        return {"numeric_literal":repr(value)}
    if value is None or isinstance(value, (str,int,float,bool)):
        return value
    raise TypeError(f"Configuration has an unsupported type: {type(value)}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True, type=Path)
    p.add_argument("--checkpoint", required=True, type=Path)
    p.add_argument("--images", nargs="+", required=True, type=Path)
    p.add_argument("--device", choices=("cpu", "mps"), required=True)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--input-source", required=True)
    p.add_argument("--compare", type=Path, help="CPU run directory using identical code, weights and input order")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--signed-rope-check", type=Path,
                   help="Passed compatibility report for the explicit signed-position RoPE adapter")
    args = p.parse_args()
    if args.output.exists():
        p.error("Output directory already exists; choose a new name to preserve earlier runs.")
    args.output.mkdir(parents=True)
    report = {"started_utc": now(), "evidence_level": "independent_pretrained_geometry_inference",
              "device": args.device, "dtype": "float32", "resolution_model": "224_linear_intermediate",
              "vmem_complete_pipeline": False, "video_generated": False, "accuracy_evaluated": False,
              "input_source": args.input_source, "seed": 0, "cpu_threads": args.threads}
    report["runner_sha256"] = sha(Path(__file__))
    shutil.copy2(Path(__file__),args.output/"runner_snapshot.py")
    report["python_executable"] = sys.executable
    def save_report():
        (args.output / "run_metadata.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    def phase(name):
        report["phase"] = name
        report["updated_utc"] = now()
        save_report()
        print(json.dumps({"utc": now(), "phase": name}), flush=True)
    try:
        import numpy as np
        import torch
        if args.device == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS requested but unavailable")
        torch.set_num_threads(args.threads)
        torch.manual_seed(0)
        np.random.seed(0)
        repo = args.repo.resolve()
        git = "/usr/bin/git" if sys.platform == "darwin" else "git"
        report.update(repo=str(repo), commit=subprocess.check_output([git,"-C",str(repo),"rev-parse","HEAD"],text=True).strip(),
                      tracked_changes=subprocess.check_output([git,"-C",str(repo),"status","--porcelain","--untracked-files=no"],text=True).strip(),
                      torch_version=torch.__version__, numpy_version=np.__version__, python=sys.version)
        report["versions"] = {name:version(name) for name in (
            "torch", "torchvision", "numpy", "scipy", "pillow", "transformers",
            "accelerate", "einops", "roma", "opencv-python-headless", "huggingface-hub", "omegaconf",
        )}
        report["mps_environment"] = {key:os.environ.get(key) for key in (
            "PYTORCH_ENABLE_MPS_FALLBACK", "PYTORCH_MPS_HIGH_WATERMARK_RATIO",
            "PYTORCH_MPS_PREFER_METAL", "PYTORCH_MPS_FAST_MATH",
        )}
        report["available_backends"] = {"cuda":torch.cuda.is_available(), "mps":torch.backends.mps.is_available()}
        report["serialization_environment"] = {key:os.environ.get(key) for key in (
            "TORCH_FORCE_WEIGHTS_ONLY_LOAD", "TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD",
        )}
        if str(os.environ.get("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "")).lower() in ("1", "y", "yes", "true"):
            raise RuntimeError("This runner requires weights-only checkpoint deserialization")
        if report["tracked_changes"]:
            raise RuntimeError("Official checkout has tracked modifications; record a patch before running")
        phase("verify_inputs_and_checkpoint")
        if not args.checkpoint.is_file():
            raise FileNotFoundError(args.checkpoint)
        report["checkpoint"] = {"path":str(args.checkpoint.resolve()), "bytes":args.checkpoint.stat().st_size, "sha256":sha(args.checkpoint)}
        download_manifest = args.checkpoint.parent / "download_manifest.json"
        if not download_manifest.exists():
            raise RuntimeError("Checkpoint download manifest is missing")
        expected = json.loads(download_manifest.read_text())
        if expected.get("sha256") != report["checkpoint"]["sha256"]:
            raise RuntimeError("Checkpoint hash does not match download manifest")
        if expected.get("status") != "verified_download" or expected.get("actual_size") != report["checkpoint"]["bytes"]:
            raise RuntimeError("Checkpoint download was not completely verified")
        report["images"] = [{"path":str(path.resolve()), "sha256":sha(path)} for path in args.images]
        sys.path.insert(0, str(repo / "src"))
        sys.path.insert(1, str(repo / "src" / "croco"))
        from dust3r.utils.image import load_images
        from dust3r.model import ARCroco3DStereo
        from dust3r.inference import inference
        from dust3r.utils.camera import pose_encoding_to_camera
        from models.pos_embed import RoPE2D
        report["loaded_modules"] = {name:sys.modules[name].__file__ for name in (
            "dust3r.model", "dust3r.inference", "dust3r.utils.image", "models.pos_embed",
        )}
        report["rope_class_module"] = RoPE2D.__module__
        report["upstream_source_files_unmodified"] = not bool(report["tracked_changes"])
        report["upstream_execution_unmodified"] = False
        report["runtime_compatibility"] = {"signed_rope_adapter":False,"blocking_input_staging":True}
        if args.signed_rope_check:
            import cut3r_rope_compat
            check = json.loads(args.signed_rope_check.read_text())
            adapter_path = Path(cut3r_rope_compat.__file__).resolve()
            if check.get("ok") is not True or check.get("adapter_sha256") != sha(adapter_path) or check.get("commit") != report["commit"]:
                raise RuntimeError("Signed RoPE compatibility check is missing, failed, or for different code")
            cut3r_rope_compat.install(RoPE2D)
            report["runtime_compatibility"] = {
                "signed_rope_adapter":True,"blocking_input_staging":True,"adapter_path":str(adapter_path),
                "adapter_sha256":sha(adapter_path),"validation_path":str(args.signed_rope_check.resolve()),
                "validation_sha256":sha(args.signed_rope_check),
                "reason":"Official pose tokens have positions (-1,-1); PyTorch fallback embedding rejects negative indices",
                "semantics":"Signed angle from official CUDA source; verified against nonnegative original fallback and CPU/MPS formula checks",
            }
        phase("prepare_images")
        images = load_images([str(path.resolve()) for path in args.images], size=224)
        views = []
        for i, image in enumerate(images):
            img = image["img"].float()
            views.append({"img": img, "ray_map": torch.full((img.shape[0],6,*img.shape[-2:]), torch.nan),
                          "true_shape":torch.from_numpy(image["true_shape"]), "idx":i, "instance":str(i),
                          "camera_pose":torch.eye(4,dtype=torch.float32).unsqueeze(0),
                          "img_mask":torch.tensor([True]), "ray_mask":torch.tensor([False]),
                          "update":torch.tensor([True]), "reset":torch.tensor([False])})
        report["input_tensor_shapes"] = [list(v["img"].shape) for v in views]
        report["views"] = len(views)
        phase("load_pretrained_model")
        # Official checkpoints carry OmegaConf settings. Keep PyTorch 2.7's
        # weights-only loader, allowing just these inspected configuration types.
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata, Metadata
        from omegaconf.nodes import AnyNode
        allowed_globals = [DictConfig, ContainerMetadata, Any, dict, defaultdict, AnyNode, Metadata]
        allowed_names = {f"{value.__module__}.{value.__qualname__}" for value in allowed_globals}
        unsafe_globals = sorted(torch.serialization.get_unsafe_globals_in_checkpoint(args.checkpoint))
        if set(unsafe_globals)-allowed_names:
            raise RuntimeError(f"Unexpected checkpoint classes: {set(unsafe_globals)-allowed_names}")
        report["checkpoint_serialization"] = {"weights_only":True, "inspected_extra_globals":unsafe_globals,
            "scoped_allowed_globals":sorted(allowed_names), "upstream_source_modified":False}
        started = time.perf_counter()
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log), torch.serialization.safe_globals(allowed_globals):
                model = ARCroco3DStereo.from_pretrained(str(args.checkpoint.resolve())).float()
        finally:
            (args.output / "checkpoint_load.txt").write_text(log.getvalue())
        load_text = log.getvalue()
        (args.output / "checkpoint_load.txt").write_text(load_text)
        print(load_text, flush=True)
        report["checkpoint_all_keys_matched"] = "All keys matched successfully" in load_text
        if not report["checkpoint_all_keys_matched"]:
            raise RuntimeError("Official loader did not report all checkpoint keys matched; inspect checkpoint_load.txt")
        # CroCoNet replaces self.config with its backbone config; head_type is
        # retained on the concrete model, not on that backbone-only config.
        report["model_config"] = {
            "retained_backbone_config":configuration_json(model.config.to_dict()),
            "runtime_attributes":configuration_json({key:getattr(model,key) for key in (
                "head_type", "output_mode", "state_size", "state_pe", "pose_head_flag",
                "depth_mode", "conf_mode", "pose_mode",
            )}),
            "downstream_head_class":f"{type(model.downstream_head).__module__}.{type(model.downstream_head).__qualname__}",
        }
        report["actual_head_type"] = getattr(model, "head_type", None)
        report["actual_patch_image_size"] = list(model.patch_embed.img_size)
        if report["actual_head_type"] != "linear" or report["actual_patch_image_size"] != [224,224]:
            raise RuntimeError("Loaded architecture does not match the intended 224 linear checkpoint")
        model = model.to(args.device).eval()
        if args.device == "mps": torch.mps.synchronize()
        report["load_seconds"] = time.perf_counter() - started
        report["parameters"] = sum(parameter.numel() for parameter in model.parameters())
        phase("stage_inputs_with_blocking_transfers")
        staging_started=time.perf_counter()
        # Official inference replaces host tensor references while requesting
        # asynchronous copies. On this MPS stack that corrupted boolean masks.
        # Pre-stage all eligible inputs synchronously; the official same-device
        # .to calls then need no transfer. Preserve and verify values, including NaNs.
        ignore_keys={"depthmap","dataset","label","instance","idx","true_shape","rng"}
        staged_checks=[]
        for i,view in enumerate(views):
            for key,value in list(view.items()):
                if key in ignore_keys or not torch.is_tensor(value):continue
                expected_value=value.detach().cpu().numpy().copy()
                view[key]=value.to(args.device,non_blocking=False)
                actual_value=view[key].detach().cpu().numpy()
                same=bool(np.array_equal(expected_value,actual_value,equal_nan=True))
                staged_checks.append({"view":i,"field":key,"values_preserved":same})
                if not same:raise RuntimeError(f"Input staging corrupted view {i}, field {key}")
        report["input_device_staging"]={"mode":"blocking_before_official_inference",
                                        "checks":staged_checks,"all_values_preserved":True}
        report["input_staging_seconds"]=time.perf_counter()-staging_started
        phase("inference")
        started = time.perf_counter()
        with torch.inference_mode():
            outputs, _ = inference(views, model, args.device)
        if args.device == "mps": torch.mps.synchronize()
        report["inference_seconds"] = time.perf_counter() - started
        phase("save_predictions")
        arrays = {}
        statistics = {}
        for i, prediction in enumerate(outputs["pred"]):
            for key, value in prediction.items():
                if not torch.is_tensor(value): continue
                name = f"frame{i}_{key}"
                arrays[name] = value.detach().cpu().numpy()
            arrays[f"frame{i}_camera_c2w"] = pose_encoding_to_camera(prediction["camera_pose"].detach().cpu()).numpy()
        for key, array in arrays.items():
            finite = np.isfinite(array)
            valid = array[finite]
            statistics[key] = {"shape":list(array.shape), "dtype":str(array.dtype), "all_finite":bool(finite.all()),
                               "finite_fraction":float(finite.mean()), "min":float(valid.min()) if valid.size else None,
                               "max":float(valid.max()) if valid.size else None}
        np.savez_compressed(args.output / "predictions.npz", **arrays)
        report["outputs"] = statistics
        report["all_outputs_finite"] = all(item["all_finite"] for item in statistics.values())
        report["required_outputs_present"] = all(
            f"frame{i}_{key}" in arrays for i in range(len(views))
            for key in ("pts3d_in_self_view", "pts3d_in_other_view", "conf_self", "conf", "camera_pose", "camera_c2w")
        )
        report["predictions_sha256"] = sha(args.output / "predictions.npz")
        report["peak_process_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system()=="Darwin" else 1024)
        report["inference_ok"] = report["all_outputs_finite"] and report["required_outputs_present"]
        if args.compare:
            reference_meta = json.loads((args.compare / "run_metadata.json").read_text())
            if reference_meta.get("device") != "cpu" or reference_meta.get("ok") is not True:
                raise RuntimeError("Reference must be a successful CPU run")
            if sha(args.compare / "predictions.npz") != reference_meta.get("predictions_sha256"):
                raise RuntimeError("Reference predictions hash mismatch")
            for key in ("commit", "images", "input_tensor_shapes", "resolution_model", "runner_sha256", "versions", "dtype", "seed", "cpu_threads", "model_config", "rope_class_module", "checkpoint_serialization", "runtime_compatibility", "input_device_staging"):
                if report[key] != reference_meta[key]:
                    raise RuntimeError(f"Comparison mismatch for {key}")
            if report["checkpoint"]["sha256"] != reference_meta["checkpoint"]["sha256"]:
                raise RuntimeError("Comparison checkpoint mismatch")
            reference = np.load(args.compare / "predictions.npz", allow_pickle=False)
            comparison = {"reference":str(args.compare.resolve()), "atol":1e-3, "rtol":1e-3, "per_array":{}}
            if set(reference.files) != set(arrays): raise RuntimeError("Comparison output keys differ")
            for key, array in arrays.items():
                other = reference[key]
                if array.shape != other.shape or array.dtype != other.dtype:
                    raise RuntimeError(f"Comparison shape/dtype mismatch for {key}")
                difference = np.abs(array.astype(np.float64)-other.astype(np.float64))
                comparison["per_array"][key] = {"max_absolute_difference":float(difference.max()),
                    "mean_absolute_difference":float(difference.mean()),
                    "allclose":bool(np.allclose(array,other,atol=1e-3,rtol=1e-3))}
            comparison["all_arrays_close"] = all(v["allclose"] for v in comparison["per_array"].values())
            (args.output / "cpu_comparison.json").write_text(json.dumps(comparison,indent=2)+"\n")
            report["cpu_comparison_all_arrays_close"] = comparison["all_arrays_close"]
        report["ok"] = report["inference_ok"] and report.get("cpu_comparison_all_arrays_close",True)
        report["phase"] = "complete"
    except Exception:
        report["ok"] = False
        report["error"] = traceback.format_exc()
        print(report["error"], flush=True)
    report["completed_utc"] = now()
    save_report()
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
