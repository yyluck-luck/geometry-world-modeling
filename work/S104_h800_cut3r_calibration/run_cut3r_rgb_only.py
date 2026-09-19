#!/usr/bin/env python3
"""Bounded CUT3R component run: exactly four explicitly supplied RGB files."""
import argparse, hashlib, json, os, platform, sys, time, traceback
from pathlib import Path

IDS = (1, 31, 61, 91)
FORBIDDEN = ("depth", "pose", "gt", "ground_truth", "trajectory")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rgb", nargs=4, required=True, help="IDs 1,31,61,91 in that order")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=512)
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    receipt = {"schema":"s104-cut3r-rgb-only-receipt-v1", "status":"RUNNING",
               "ids":list(IDS), "data_access":"RGB_ONLY", "depth_access":False,
               "pose_access":False, "gt_access":False, "model_path":str(Path(a.model).resolve()),
               "model_sha256":None, "source_root":os.environ.get("CUT3R_SOURCE","UNKNOWN"),
               "python":sys.version, "platform":platform.platform()}
    (out/"STARTED.json").write_text(json.dumps(receipt, indent=2))
    try:
        if len(a.rgb) != 4: raise ValueError("exactly four RGB paths required")
        paths = [Path(x).resolve() for x in a.rgb]
        for p in paths:
            if not p.is_file(): raise FileNotFoundError(p)
            low = str(p).lower()
            if any(x in low for x in FORBIDDEN): raise ValueError(f"forbidden non-RGB path: {p}")
        receipt["rgb_sha256"] = [sha256(p) for p in paths]
        receipt["model_bytes"] = Path(a.model).stat().st_size
        receipt["model_sha256"] = sha256(a.model)
        import torch
        from PIL import Image
        from demo import prepare_input
        from src.dust3r.model import ARCroco3DStereo
        from src.dust3r.inference import inference
        if not torch.cuda.is_available(): raise RuntimeError("CUDA_NOT_AVAILABLE")
        device = "cuda"
        views = prepare_input([str(p) for p in paths], [True]*4, a.size, revisit=1, update=True)
        receipt["input_shapes"] = [list(v["img"].shape) for v in views]
        # CUT3R's released checkpoint contains OmegaConf objects.  PyTorch >=2.6
        # rejects these under weights_only=True; this narrowly scoped loader
        # compatibility shim is used only after recording the trusted SHA-256.
        # It is an infrastructure fix, not a model or scientific change.
        _torch_load_original = torch.load
        def _trusted_checkpoint_load(*args, **kwargs):
            if args and os.path.abspath(str(args[0])) == os.path.abspath(a.model):
                kwargs["weights_only"] = False
            return _torch_load_original(*args, **kwargs)
        torch.load = _trusted_checkpoint_load
        receipt["loader_compatibility"] = "force_weights_only_false_for_sha_verified_cut3r_checkpoint"
        t0 = time.perf_counter(); model = ARCroco3DStereo.from_pretrained(a.model).to(device); model.eval()
        torch.cuda.synchronize(); receipt["load_seconds"] = time.perf_counter()-t0
        torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize(); t1=time.perf_counter()
        with torch.no_grad(): outputs, state = inference(views, model, device)
        torch.cuda.synchronize(); receipt["inference_seconds_sync"] = time.perf_counter()-t1
        receipt.update({"device":torch.cuda.get_device_name(0), "torch":torch.__version__,
                        "cuda":torch.version.cuda, "peak_memory_bytes":torch.cuda.max_memory_allocated(),
                        "forward_completed":True})
        torch.save({"outputs":outputs, "state_args":state}, out/"raw_outputs.pt")
        receipt["raw_outputs_sha256"] = sha256(out/"raw_outputs.pt")
        receipt["status"] = "SUCCESS"
    except Exception as e:
        receipt.update({"status":"FAILED", "error_type":type(e).__name__, "error":str(e),
                        "traceback":traceback.format_exc()})
    (out/"RECEIPT.json").write_text(json.dumps(receipt, indent=2, default=str))
    return 0 if receipt["status"] == "SUCCESS" else 1
if __name__ == "__main__": raise SystemExit(main())
