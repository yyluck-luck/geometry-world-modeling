#!/usr/bin/env python3
"""Generate source-only, complete CUT3R+KPS candidates; never read target data.

Manifest: candidates [{candidate_id, order}], windows [{window_id, scene,
scene_rel, source_refs, target_refs}]. References are seq-XX/XXXXXX. Each order
permutes the same four source frames. Outputs are restored to source_refs order.
The protocol must be frozen before this runner is invoked with its SHA-256.
"""
import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import random
import re
import resource
import socket
import sys
import tempfile
import time
import traceback
import uuid

import numpy as np

SCHEMA = "w1-joint-geometry-candidate-v1"
SEED = 0
GRID = (384, 512)
SAFE_ID = re.compile(r"[A-Za-z0-9_.-]+\Z")
REF = re.compile(r"seq-[0-9]+/[0-9]{6}\Z")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_manifest(manifest):
    candidates, windows = manifest["candidates"], manifest["windows"]
    require(isinstance(candidates, list) and candidates, "Empty candidate list")
    require(isinstance(windows, list) and windows, "Empty window list")
    for candidate in candidates:
        require(bool(SAFE_ID.fullmatch(candidate["candidate_id"])), "Unsafe candidate ID")
        order = candidate["order"]
        require(isinstance(order, list) and all(type(i) is int for i in order)
                and sorted(order) == list(range(4)), "Candidate order must permute 0,1,2,3")
    require(len({c["candidate_id"] for c in candidates}) == len(candidates), "Duplicate candidate IDs")
    require(len({tuple(c["order"]) for c in candidates}) == len(candidates), "Duplicate candidate orders")
    for window in windows:
        require(bool(SAFE_ID.fullmatch(window["window_id"])), "Unsafe window ID")
        require(isinstance(window["scene"], str) and window["scene"], "Missing scene")
        rel = PurePosixPath(window["scene_rel"])
        require(not rel.is_absolute() and ".." not in rel.parts and rel.parts, "Unsafe scene_rel")
        sources, targets = window["source_refs"], window["target_refs"]
        require(isinstance(sources, list) and len(sources) == 4 and len(set(sources)) == 4,
                "Exactly four distinct source_refs are required")
        require(isinstance(targets, list) and targets and len(set(targets)) == len(targets),
                "Distinct target_refs metadata is required")
        require(all(isinstance(r, str) and REF.fullmatch(r) for r in sources + targets), "Invalid frame reference")
        require(not set(sources).intersection(targets), "Source and target identities overlap")
    require(len({w["window_id"] for w in windows}) == len(windows), "Duplicate window IDs")
    return candidates, windows


def contained_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), "Input path escapes the data root")
    return path


def load_sources(data_root, window):
    """Read this explicit allowlist only: source color, source pose, scene K."""
    from PIL import Image
    root = Path(data_root).resolve()
    scene = contained_path(root, window["scene_rel"])
    fingerprints = {}

    def read(path):
        require(path.is_relative_to(root), "Input path escapes the data root")
        blob = path.read_bytes()
        fingerprints[path.relative_to(root).as_posix()] = {"sha256": sha_bytes(blob), "bytes": len(blob)}
        return blob

    kp = contained_path(root, scene.relative_to(root) / "camera-intrinsics.txt")
    K = np.loadtxt(io.BytesIO(read(kp)), dtype=np.float64).reshape(3, 3)
    require(np.isfinite(K).all() and K[0, 0] > 0 and K[1, 1] > 0,
            "Nonfinite or nonpositive intrinsics")
    require(np.allclose(K[2], [0, 0, 1]), "Invalid intrinsics last row")
    rgbs, poses = [], []
    for ref in window["source_refs"]:
        sequence, frame = ref.split("/")
        base = scene.relative_to(root) / sequence / f"frame-{frame}"
        color_path = contained_path(root, str(base) + ".color.png")
        pose_path = contained_path(root, str(base) + ".pose.txt")
        with Image.open(io.BytesIO(read(color_path))) as image:
            rgb = np.asarray(image.convert("RGB")).copy()
        require(rgb.shape == (480, 640, 3), "Source RGB must have native shape 480x640x3")
        pose = np.loadtxt(io.BytesIO(read(pose_path)), dtype=np.float32).reshape(4, 4)
        rotation = pose[:3, :3].astype(np.float64)
        require(np.isfinite(pose).all() and np.allclose(pose[3], [0, 0, 0, 1], atol=1e-6), "Invalid source pose")
        require(np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-5)
                and np.isclose(np.linalg.det(rotation), 1, atol=1e-5), "Nonrigid source pose")
        rgbs.append(rgb)
        poses.append(pose)
    return rgbs, np.stack(poses), K, fingerprints


def rgb576(rgb, torch):
    """Exactly geometry_b2.rgb576: native RGB -> area resize -> square crop."""
    from PIL import Image
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float() / 255.
    t = torch.nn.functional.interpolate(t.unsqueeze(0), (576, 768), mode="area")[:, :, :, 96:672][0]
    return Image.fromarray(np.clip(t.permute(1, 2, 0).numpy() * 255, 0, 255).astype(np.uint8))


def collect_code(source, kps_source):
    cut3r = Path(source) / "extern/CUT3R"
    require((cut3r / "surfel_inference.py").is_file(), "--vmem-source must contain extern/CUT3R")
    paths = sorted(p for p in cut3r.rglob("*") if p.is_file()
                   and p.suffix in {".py", ".so", ".json", ".yaml", ".yml"}
                   and not {".git", "__pycache__"}.intersection(p.parts))
    hashes = {"CUT3R/" + p.relative_to(cut3r).as_posix(): sha_file(p) for p in paths}
    hashes["generate_candidates.py"] = sha_file(__file__)
    hashes["kps.py"] = sha_file(kps_source)
    return hashes


@contextlib.contextmanager
def trusted_checkpoint_load(torch, checkpoint):
    original = torch.load

    def scoped(path, *args, **kwargs):
        if isinstance(path, (str, os.PathLike)) and Path(path).resolve() == checkpoint.resolve():
            kwargs["weights_only"] = False
        return original(path, *args, **kwargs)

    torch.load = scoped
    try:
        yield
    finally:
        torch.load = original


def prepare_runtime(args, checkpoint, kps_source):
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True
    cut3r = Path(args.vmem_source).resolve() / "extern/CUT3R"
    sys.path[:0] = [str(cut3r), str(cut3r / "src")]
    import torch
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    from add_ckpt_path import add_path_to_dust3r
    add_path_to_dust3r(str(checkpoint))
    from src.dust3r.model import ARCroco3DStereo
    import surfel_inference as SI
    from cloud_opt.dust3r_opt import init_im_poses as IIP
    spec = importlib.util.spec_from_file_location("w1_pinned_kps", kps_source)
    kps = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kps)
    # croco.py enables TF32 at import. Override only after all model imports.
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.set_float32_matmul_precision("highest")
    if args.device == "cuda":
        require(torch.cuda.is_available(), "CUDA requested but unavailable; CPU fallback is forbidden")
    log = []
    method = kps.install(IIP, log=log, seed=SEED, known_K=None)

    def guarded_kps(self, **kwargs):
        nkp, _, _ = IIP.get_known_poses(self)
        require(int(nkp) == self.n_imgs and all(i == 0 for i, _ in self.edges),
                "KPS cannot run; original MST fallback is forbidden")
        return method(self, **kwargs)

    IIP.init_minimum_spanning_tree = guarded_kps
    reseed(torch)
    with trusted_checkpoint_load(torch, checkpoint):
        model = ARCroco3DStereo.from_pretrained(str(checkpoint)).to(args.device, dtype=torch.float32).eval()
    versions = {}
    from importlib.metadata import version, PackageNotFoundError
    for package in ("torch", "torchvision", "numpy", "scipy", "pillow", "transformers", "roma", "einops", "opencv-python-headless"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    environment = {"python": platform.python_version(), "platform": platform.platform(), "packages": versions,
                   "device": args.device, "device_name": torch.cuda.get_device_name() if args.device == "cuda" else platform.machine(),
                   "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(), "dtype": "float32",
                   "tf32_matmul": bool(torch.backends.cuda.matmul.allow_tf32),
                   "tf32_cudnn": bool(torch.backends.cudnn.allow_tf32),
                   "float32_matmul_precision": torch.get_float32_matmul_precision(),
                   "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
                   "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                   "threads": args.threads, "interop_threads": 1, "seed": SEED,
                   "niter": 0, "lr": 0.01, "size": 512, "known_K": False}
    return torch, SI, model, log, environment


def reseed(torch):
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)


def restore_geometry(result, order):
    """Permutation is input-position -> canonical-source-position."""
    arrays = {}
    for key, output, shape in (("depths", "depths", GRID), ("confidences", "confidences", GRID),
                               ("point_clouds", "point_clouds", (*GRID, 3))):
        require(key in result and len(result[key]) == 4, f"Missing complete {key}")
        canonical = [None] * 4
        for position, value in enumerate(result[key]):
            if hasattr(value, "detach"):
                value = value.detach().float().cpu().numpy()
            value = np.asarray(value, dtype=np.float32)
            require(value.shape == (1, *shape), f"Unexpected {key} shape {value.shape}")
            value = value[0]
            canonical[order[position]] = value
        arrays[output] = np.stack(canonical)
    require((np.isfinite(arrays["depths"]) & (arrays["depths"] > 0)).any(),
            "All candidate depths are invalid")
    return arrays


def atomic_publish(path, writer):
    """No-clobber atomic publication; interrupted temporaries never look final."""
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            writer(fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.link(temp, path)  # Atomic and fails if final path already exists.
    finally:
        Path(temp).unlink(missing_ok=True)


def publish_json(path, value):
    def safe(obj):
        if isinstance(obj, dict):
            return {key: safe(item) for key, item in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [safe(item) for item in obj]
        if isinstance(obj, (float, np.floating)):
            return float(obj) if np.isfinite(obj) else None
        if isinstance(obj, np.integer):
            return int(obj)
        return obj
    content = json.dumps(safe(value), indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    atomic_publish(path, lambda fh: fh.write(content))


def existing_matches(npz_path, receipt_path, fingerprint):
    if not npz_path.exists() and not receipt_path.exists():
        return False
    require(npz_path.is_file() and receipt_path.is_file(), "Incomplete previous output; refusing overwrite")
    receipt = json.loads(receipt_path.read_text())
    require(receipt.get("status") == "OK" and receipt.get("fingerprint") == fingerprint,
            "Existing output fingerprints differ; choose a fresh output directory")
    require(sha_file(npz_path) == receipt.get("candidate_sha256"), "Existing candidate checksum mismatch")
    return True


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "data-root", "vmem-source", "weights", "out", "protocol-sha"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--kps-source", default=str(Path(__file__).with_name("kps.py")))
    p.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--shard", default="0/1", help="Window shard i/n; candidate filtering is independent")
    p.add_argument("--candidate-ids", default="", help="Comma-separated manifest candidate IDs; empty means all")
    args = p.parse_args(argv)
    require(bool(re.fullmatch(r"[0-9a-fA-F]{64}", args.protocol_sha)), "--protocol-sha must be a SHA-256 hex digest")
    args.protocol_sha = args.protocol_sha.lower()
    require(args.threads > 0, "--threads must be positive")
    try:
        args.shard_index, args.shard_count = map(int, args.shard.split("/"))
    except ValueError as error:
        raise ValueError("--shard must have form i/n") from error
    require(0 <= args.shard_index < args.shard_count, "Invalid window shard")
    return args


def main(argv=None):
    args = parse_args(argv)
    manifest_bytes = Path(args.manifest).read_bytes()
    candidates, windows = validate_manifest(json.loads(manifest_bytes))
    if args.candidate_ids:
        ids = args.candidate_ids.split(",")
        require(len(ids) == len(set(ids)) and set(ids) <= {c["candidate_id"] for c in candidates}, "Unknown/duplicate --candidate-ids")
        candidates = [c for c in candidates if c["candidate_id"] in ids]
    windows = [w for index, w in enumerate(windows) if index % args.shard_count == args.shard_index]
    require(windows, "Shard has no windows")
    checkpoint = Path(args.weights).resolve()
    if checkpoint.is_dir():
        checkpoint = checkpoint / "cut3r_512_dpt_4_64.pth"
    require(checkpoint.is_file(), "CUT3R checkpoint is missing")
    kps_source = Path(args.kps_source).resolve()
    require(kps_source.is_file(), "Pinned KPS source is missing")
    code = collect_code(args.vmem_source, kps_source)
    weight_sha = sha_file(checkpoint)
    torch, SI, model, kps_log, environment = prepare_runtime(args, checkpoint, kps_source)
    common = {"schema": SCHEMA, "protocol_sha256": args.protocol_sha,
              "manifest_sha256": sha_bytes(manifest_bytes), "code_hashes": code,
              "weight_sha256": weight_sha, "environment": environment}
    output_dir = Path(args.out).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for window in windows:
        rgbs, poses, K, source_hashes = load_sources(args.data_root, window)
        pils = [rgb576(rgb, torch) for rgb in rgbs]
        for candidate in candidates:
            basename = f"{window['window_id']}__{candidate['candidate_id']}"
            npz_path, receipt_path = output_dir / (basename + ".npz"), output_dir / (basename + ".json")
            identity = {**common, "window": window, "candidate": candidate, "source_files": source_hashes}
            fingerprint = sha_bytes(canonical_bytes(identity))
            if existing_matches(npz_path, receipt_path, fingerprint):
                print(f"[skip] {basename} verified", flush=True)
                continue
            lock = output_dir / (basename + ".lock")
            lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(lock_fd)
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            t0 = time.perf_counter()
            try:
                # Recheck under our per-candidate lock.
                require(not npz_path.exists() and not receipt_path.exists(), "Concurrent output publication")
                reseed(torch)
                kps_log.clear()
                if args.device == "cuda":
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats()
                order = candidate["order"]
                with torch.no_grad():
                    result = SI.run_inference_from_pil([pils[i] for i in order], model,
                        poses=poses[order].copy(), depths=None, lr=0.01, niter=0,
                        device=args.device, size=512, visualize=False, save_flag=False)
                require(len(kps_log) == 1 and kps_log[0].get("kps") == "OK", "KPS did not complete successfully")
                calibration = kps_log[0]
                require(np.isfinite(calibration["sigma"]) and calibration["sigma"] > 0
                        and np.isfinite(calibration["median_reproj_px"]), "Invalid KPS calibration")
                require(all(f is not None and np.isfinite(f) and f > 0 for f in calibration["focals"]), "Invalid KPS focal")
                arrays = restore_geometry(result, order)
                arrays.update(poses=poses, K=K, source_refs=np.array(window["source_refs"], dtype="U"),
                              candidate_order=np.array(order, dtype=np.int64))
                if args.device == "cuda":
                    torch.cuda.synchronize()
                elapsed = time.perf_counter() - t0
                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                memory = {"process_peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
                          "rss_scope": "process lifetime high-water mark",
                          "cuda_peak_allocated_bytes": int(torch.cuda.max_memory_allocated()) if args.device == "cuda" else None,
                          "cuda_peak_reserved_bytes": int(torch.cuda.max_memory_reserved()) if args.device == "cuda" else None}
                atomic_publish(npz_path, lambda fh: np.savez_compressed(fh, **arrays))
                receipt = {**identity, "status": "OK", "fingerprint": fingerprint, "kps": list(kps_log),
                           "candidate_sha256": sha_file(npz_path), "candidate_file": npz_path.name,
                           "started_utc": started, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "runtime_seconds": elapsed, "peak_memory": memory,
                           "hostname": socket.gethostname(), "checkpoint_path": str(checkpoint),
                           "vmem_source": str(Path(args.vmem_source).resolve()), "kps_source": str(kps_source),
                           "arrays": {key: {"shape": list(value.shape), "dtype": str(value.dtype)} for key, value in arrays.items()},
                           "invalid_predictions": {
                               "depth_nonfinite_per_source": np.sum(~np.isfinite(arrays["depths"]), axis=(1, 2)).tolist(),
                               "depth_nonpositive_per_source": np.sum(np.isfinite(arrays["depths"]) & (arrays["depths"] <= 0), axis=(1, 2)).tolist(),
                               "confidence_nonfinite_per_source": np.sum(~np.isfinite(arrays["confidences"]), axis=(1, 2)).tolist(),
                               "point_cloud_nonfinite_values_per_source": np.sum(~np.isfinite(arrays["point_clouds"]), axis=(1, 2, 3)).tolist()},
                           "target_data_read": False, "errors": []}
                publish_json(receipt_path, receipt)
                del result, arrays
                print(f"[ok] {basename} seconds={elapsed:.3f} sigma={calibration['sigma']:.8g}", flush=True)
            except Exception as error:
                failures += 1
                failure = {**identity, "status": "ERROR", "fingerprint": fingerprint, "kps": list(kps_log),
                           "started_utc": started, "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "runtime_seconds": time.perf_counter() - t0,
                           "errors": [{"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}]}
                # Never replace a failed or successful receipt from a previous attempt.
                publish_json(output_dir / (basename + ".error." + uuid.uuid4().hex + ".json"), failure)
                print(f"[error] {basename}: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
                if args.device == "cuda":
                    torch.cuda.empty_cache()
            finally:
                lock.unlink()
    print(json.dumps({"status": "OK" if not failures else "PARTIAL_FAILURE", "failed_candidates": failures}), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
