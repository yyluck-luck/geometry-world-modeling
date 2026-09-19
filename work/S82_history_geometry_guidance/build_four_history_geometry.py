#!/usr/bin/env python3
"""S82: one supervised four-history raw CUT3R attempt; no alignment or rendering.

Official image/model loaders are reused without I/O adapters. Run without
arguments AFTER root's source review. Existing output
directories are never reused. Scientific quality is outside this stage's PASS.
"""
import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.metadata as metadata
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "FOUR_HISTORY_CONTRACT.json"
OUT = HERE / "execution_geometry_01"
sys.dont_write_bytecode = True


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, obj, initial=False):
    text = json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if initial:
        with path.open("x") as f:
            f.write(text)
    else:
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(text)
        temporary.replace(path)


def read_contract(expected=None):
    raw = CONTRACT.read_bytes()
    contract = json.loads(raw)
    if expected is not None:
        assert digest(raw) == expected, "contract changed after dispatch"
    assert digest(Path(__file__).read_bytes()) == contract["runner_sha256"]
    assert Path(contract["output_directory"]) == OUT
    assert [x["history_id"] for x in contract["history_rgb"]] == [12, 13, 18, 19]
    assert contract["generation_slot_order"] == [19, 18, 13, 12]
    return contract, digest(raw)


def tensor_record(array):
    return dict(shape=list(array.shape), dtype=str(array.dtype),
                body_bytes=array.nbytes, body_sha256=digest(array.tobytes(order="C")))


def config_json(value):
    """Keep explicit +/-inf configuration sentinels valid in strict JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_float": repr(value)}
    if isinstance(value, dict):
        return {k: config_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [config_json(v) for v in value]
    return value


def worker(expected_contract_sha):
    c, contract_sha = read_contract(expected_contract_sha)
    assert OUT.is_dir(), "only the one-shot supervisor creates the output directory"
    started = time.monotonic()
    r = dict(schema="S82-raw-four-history-receipt-v1", started_utc=utc(),
             status="RUNNING", contract_sha256=contract_sha,
             runner_sha256=c["runner_sha256"], scientific_input_reads=[],
             scientific_input_open_events=[], prohibited_open_attempts=[],
             source_files_verified=[], model_loads=0, recurrent_calls=0,
             downstream_head_calls=0, frames_completed=0, image_decodes=0,
             optimizer_calls=0, render_calls=0, generation_calls=0,
             loaded_previous_state=False, target_or_depth_inputs=False,
             new_method_validated=False, artifacts=[], output_heads=[])
    write_json(OUT / "RECEIPT.json", r, initial=True)

    def flush():
        r["elapsed_seconds"] = time.monotonic() - started
        # This frozen runtime is macOS: ru_maxrss is bytes, not Linux KiB.
        r["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        write_json(OUT / "RECEIPT.json", r)

    input_specs = {str(Path(x["path"]).resolve()): x
                   for x in c["history_rgb"] + [c["checkpoint"]]}
    open_counts = dict.fromkeys(input_specs, 0)
    scientific_suffixes = {".png", ".jpg", ".jpeg", ".exr", ".npz", ".npy",
                           ".pth", ".pt", ".safetensors", ".ckpt"}

    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "urllib.Request"}:
            raise RuntimeError("network access forbidden in S82")
        if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        p = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1], args[2]
        writing = ((isinstance(mode, str) and any(x in mode for x in "wax+"))
                   or (isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR))))
        if p.is_relative_to(OUT):
            return  # output writes and own-artifact hashes are separately recorded
        if str(p) in input_specs:
            if writing or open_counts[str(p)] >= input_specs[str(p)]["maximum_file_read_opens"]:
                r["prohibited_open_attempts"].append(dict(path=str(p), mode=str(mode)))
                raise RuntimeError("scientific input read limit or write violation: " + str(p))
            open_counts[str(p)] += 1
            r["scientific_input_open_events"].append(dict(path=str(p), utc=utc(), mode=str(mode)))
        elif p.suffix.lower() in scientific_suffixes:
            r["prohibited_open_attempts"].append(dict(path=str(p), mode=str(mode)))
            raise RuntimeError("unlisted scientific file access: " + str(p))

    def hash_rgb(spec):
        p = Path(spec["path"])
        before = p.stat()
        assert before.st_size == spec["size_bytes"], str(p)
        if "mtime_ns" in spec:
            assert before.st_mtime_ns == spec["mtime_ns"], str(p)
        t = time.perf_counter()
        raw = p.read_bytes()  # identity pass; original PIL loader later decodes it
        after = p.stat()
        entry = dict(path=str(p), size_bytes=len(raw), sha256=digest(raw),
                     read_seconds=time.perf_counter() - t,
                     before_size_mtime=[before.st_size, before.st_mtime_ns],
                     after_size_mtime=[after.st_size, after.st_mtime_ns])
        r["scientific_input_reads"].append(entry)
        flush()
        assert entry["sha256"] == spec["sha256"], str(p)
        assert entry["before_size_mtime"] == entry["after_size_mtime"], str(p)

    def save_npz(name, **arrays):
        path = OUT / name
        with path.open("xb") as f:
            np.savez_compressed(f, **arrays)
        record = dict(path=str(path), size_bytes=path.stat().st_size,
                      sha256=digest(path.read_bytes()),
                      tensors={k: tensor_record(v) for k, v in arrays.items()})
        r["artifacts"].append(record)
        return record

    hook_handle = None
    try:
        assert sys.platform == c["runtime"]["platform"] == "darwin"
        assert list(sys.version_info[:3]) == c["runtime"]["python_version"]
        assert sys.executable == c["runtime"]["python_executable"]
        sys.path[:0] = c["runtime"]["prepend_sys_path"]
        os.environ.update(c["runtime"]["environment"])
        sys.addaudithook(audit)
        for item in c["source_files"]:
            assert digest(Path(item["path"]).read_bytes()) == item["sha256"], item["path"]
            r["source_files_verified"].append(item)
        actual_versions = {}
        for name, spec in c["runtime"]["distributions"].items():
            dist = metadata.distribution(name)
            actual = dict(version=dist.version, root=str(dist.locate_file("")))
            assert actual == spec, (name, actual, spec)
            actual_versions[name] = actual
        r["versions"] = actual_versions
        flush()

        import numpy as np
        import torch
        import cv2
        from typing import Any
        from collections import defaultdict
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata, Metadata
        from omegaconf.nodes import AnyNode
        import dust3r.model as model_module
        from dust3r.utils.image import load_images_for_eval
        from dust3r.utils.camera import pose_encoding_to_camera
        from dust3r.inference import inference_recurrent
        from models.pos_embed import RoPE2D
        import cut3r_rope_compat

        torch.set_num_threads(c["inference"]["torch_threads"])
        cv2.setNumThreads(c["inference"]["opencv_threads"])
        torch.manual_seed(c["inference"]["seed"])
        np.random.seed(c["inference"]["seed"])
        cut3r_rope_compat.install(RoPE2D)
        r["imported_source_paths"] = dict(model=model_module.__file__,
            image_loader=load_images_for_eval.__code__.co_filename,
            inference=inference_recurrent.__wrapped__.__code__.co_filename,
            pose_decoder=pose_encoding_to_camera.__code__.co_filename,
            rope=RoPE2D.__module__)
        assert str(Path(model_module.__file__).resolve()) == c["model_module_path"]

        for item in c["history_rgb"]:
            hash_rgb(item)
        tree = ast.parse(Path(c["prepare_input_source"]).read_text())
        definitions = [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef) and x.name == "prepare_input"]
        assert len(definitions) == 1
        ns = dict(torch=torch, np=np, load_images=load_images_for_eval, deepcopy=copy.deepcopy)
        exec(compile(ast.Module(body=definitions, type_ignores=[]), c["prepare_input_source"], "exec"), ns)
        views = ns["prepare_input"]([x["path"] for x in c["history_rgb"]], [True] * 4,
                                    size=512, crop=True, revisit=1, update=True)
        assert len(views) == 4
        r["image_decodes"] = len(views)
        for i, view in enumerate(views):
            assert list(view["img"].shape) == [1, 3, 384, 512]
            assert view["img"].dtype == torch.float32 and view["img"].device.type == "cpu"
            assert view["idx"] == i and view["instance"] == str(i)
            assert bool(view["img_mask"]) and bool(view["update"])
            assert not bool(view["ray_mask"]) and not bool(view["reset"])
            assert torch.isnan(view["ray_map"]).all()
            assert torch.equal(view["camera_pose"], torch.eye(4).unsqueeze(0))
            assert np.array_equal(view["true_shape"].numpy(), [[384, 512]])
            assert torch.isfinite(view["img"]).all()
        normalized_images = np.concatenate([v["img"].numpy() for v in views])
        save_npz("PREPROCESSED_INPUTS.npz", history_ids=np.array([12, 13, 18, 19], np.int64),
            images_normalized=normalized_images,
            rgb01_reconstructed_from_normalized=(normalized_images.transpose(0, 2, 3, 1) + 1.) / 2.,
            K_native_approx=np.array(c["coordinates"]["K_native_approx"], np.float64),
            K_512_approx=np.array(c["coordinates"]["K_512_approx"], np.float64),
            native_to_512=np.array(c["coordinates"]["native_to_512"], np.float64),
            grid512_to_grid576=np.array(c["coordinates"]["grid512_to_grid576"], np.float64))
        r["preprocessing"] = dict(declared_original_wh=[[640, 480]] * 4,
                                  original_size_basis="S68/S69 receipts plus current exact RGB SHA identity",
                                  processed_wh=[[512, 384]] * 4,
                                  image_paths_in_decode_order=[x["path"] for x in c["history_rgb"]],
                                  K_is_nominal_metadata_not_model_input=True)
        del normalized_images
        flush()

        cp = Path(c["checkpoint"]["path"])
        cp_before = cp.stat()
        assert [cp_before.st_size, cp_before.st_mtime_ns] == [c["checkpoint"]["size_bytes"], c["checkpoint"]["mtime_ns"]]
        r["checkpoint_identity"] = dict(path=str(cp), inherited_sha256=c["checkpoint"]["sha256"],
            current_sha256_recomputed=False, sha_source=c["checkpoint"]["sha_source"],
            size_bytes=cp_before.st_size, mtime_ns=cp_before.st_mtime_ns,
            read_accounting="audit file-open events; no claim of kernel-level byte counts")
        allowed = [DictConfig, ContainerMetadata, Any, dict, defaultdict, AnyNode, Metadata]
        unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(cp)
        assert set(unsafe) <= {f"{x.__module__}.{x.__qualname__}" for x in allowed}
        r["checkpoint_unsafe_globals"] = unsafe
        load_start = time.perf_counter()
        r["model_loads"] += 1
        with (OUT / "CHECKPOINT_LOAD.txt").open("x") as log:
            with contextlib.redirect_stdout(log), torch.serialization.safe_globals(allowed):
                model = model_module.ARCroco3DStereo.from_pretrained(str(cp)).float().to("cpu").eval()
        cp_after = cp.stat()
        assert [cp_before.st_size, cp_before.st_mtime_ns] == [cp_after.st_size, cp_after.st_mtime_ns]
        assert "All keys matched successfully" in (OUT / "CHECKPOINT_LOAD.txt").read_text()
        assert model.config.head_type == "dpt"
        assert not model.training
        assert all(not m.training for m in model.modules())
        assert all(p.dtype == torch.float32 and p.device.type == "cpu" for p in model.parameters())
        r.update(model_load_seconds=time.perf_counter() - load_start,
                 parameters=sum(p.numel() for p in model.parameters()), model_training=False,
                 full_model_config=config_json(model.config.to_dict()), weights_only=True,
                 torch_threads=torch.get_num_threads(),
                 opencv_threads=cv2.getNumThreads(),
                 precision_scope="CPU float32 parameters/inputs, official internals plus frozen signed RoPE")
        flush()
        poses = []
        forward_started = time.perf_counter()

        def save_head(module, inputs, result):
            i = r["downstream_head_calls"]
            r["downstream_head_calls"] += 1
            assert i < 4 and set(result) == set(c["output_schema"]["raw_head_keys"])
            assert all(torch.is_tensor(value) for value in result.values())
            arrays = {k: v.detach().cpu().numpy().copy() for k, v in result.items()}
            hid = c["history_rgb"][i]["history_id"]
            artifact = save_npz(f"head_{i:02d}_history_{hid}.npz", **arrays)
            entry = dict(inference_row=i, history_id=hid, artifact=artifact,
                         finite={k: bool(np.isfinite(a).all()) for k, a in arrays.items()})
            r["output_heads"].append(entry)
            flush()  # preserve the actual complete raw head before validation fails
            for key, shape in c["output_schema"]["head_shapes"].items():
                assert list(arrays[key].shape) == shape, (key, arrays[key].shape)
                assert arrays[key].dtype == np.float32, (key, arrays[key].dtype)
            assert all(entry["finite"].values()), "non-finite raw head retained"
            camera = pose_encoding_to_camera(result["camera_pose"].clone()).detach().cpu().numpy()
            assert camera.shape == (1, 4, 4) and camera.dtype == np.float32 and np.isfinite(camera).all()
            poses.append(camera[0].copy())
            entry["official_decoded_predicted_c2w"] = camera[0].tolist()
            r["frames_completed"] = len(poses)
            r["last_frame_utc"] = utc()
            flush()

        hook_handle = model.downstream_head.register_forward_hook(save_head)
        r["recurrent_calls"] += 1
        flush()
        outputs, unused_state = inference_recurrent(views, model, "cpu", verbose=False)
        hook_handle.remove()
        hook_handle = None
        r["forward_with_archival_seconds"] = time.perf_counter() - forward_started
        assert r["recurrent_calls"] == 1 and r["model_loads"] == 1
        assert len(outputs["pred"]) == len(poses) == r["downstream_head_calls"] == 4
        assert all(count == input_specs[path]["expected_file_read_opens"] for path, count in open_counts.items())
        assert not r["prohibited_open_attempts"]
        save_npz("PREDICTED_CAMERAS.npz", history_ids=np.array([12, 13, 18, 19], np.int64),
                 predicted_c2w=np.stack(poses))
        del unused_state
        r.update(status="RAW_FOUR_HISTORY_COMPLETE", completed_utc=utc(),
                 input_open_counts=open_counts, fresh_recurrent_state=True,
                 scientific_claim="Raw predictions from four fixed histories only; no metric alignment or scientific success claim")
    except BaseException:
        r.update(status="FAILED", completed_utc=utc(), traceback=traceback.format_exc(),
                 input_open_counts=open_counts)
        raise
    finally:
        if hook_handle is not None:
            hook_handle.remove()
        flush()


def supervise():
    c, contract_sha = read_contract()
    import psutil
    OUT.mkdir(exist_ok=False)  # no automatic rerun or overwrite, including failures
    s = dict(schema="S82-four-history-supervision-v1", status="RUNNING", started_utc=utc(),
             contract_sha256=contract_sha, peak_process_tree_rss_bytes=0,
             limits=c["resources"], attempts=1)
    write_json(OUT / "SUPERVISION.json", s, initial=True)
    command = [sys.executable, "-I", str(Path(__file__).resolve()), "--worker", contract_sha]
    s["command"] = command
    env = dict(os.environ, **c["runtime"]["environment"])
    start = time.monotonic()
    process = None
    try:
        with (OUT / "STDOUT.txt").open("x") as stdout, (OUT / "STDERR.txt").open("x") as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env, start_new_session=True)
            s["pid"] = process.pid
            while process.poll() is None:
                try:
                    tree = [psutil.Process(process.pid)]
                    tree += tree[0].children(recursive=True)
                    rss = sum(p.memory_info().rss for p in tree)
                    s["peak_process_tree_rss_bytes"] = max(s["peak_process_tree_rss_bytes"], rss)
                except psutil.NoSuchProcess:
                    pass
                elapsed = time.monotonic() - start
                if elapsed > c["resources"]["wall_seconds"] or s["peak_process_tree_rss_bytes"] > c["resources"]["rss_bytes"]:
                    s["failure"] = "wall_or_sampled_RSS_limit"
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    break
                write_json(OUT / "SUPERVISION.json", s)
                time.sleep(c["resources"]["rss_poll_seconds"])
            s["returncode"] = process.wait()
        receipt_path = OUT / "RECEIPT.json"
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        s["worker_status"] = None if receipt is None else receipt["status"]
        if time.monotonic() - start > c["resources"]["wall_seconds"]:
            s["failure"] = "elapsed_wall_limit_at_exit"
        if receipt is not None and receipt.get("peak_self_rss_bytes", 0) > c["resources"]["rss_bytes"]:
            s["failure"] = "worker_ru_maxrss_exceeded_limit"
        success = s["returncode"] == 0 and "failure" not in s and s["worker_status"] == "RAW_FOUR_HISTORY_COMPLETE"
        s["status"] = "COMPLETE" if success else "FAILED"
        if not success and receipt is not None and receipt["status"] == "RUNNING":
            receipt.update(status="FAILED_TERMINATED", termination_by_supervisor=True, completed_utc=utc())
            write_json(receipt_path, receipt)
    except BaseException:
        s.update(status="FAILED", traceback=traceback.format_exc())
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise
    finally:
        s.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - start)
        write_json(OUT / "SUPERVISION.json", s)
    print(json.dumps(s, ensure_ascii=False))
    return 0 if s["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
    else:
        raise SystemExit(supervise())
