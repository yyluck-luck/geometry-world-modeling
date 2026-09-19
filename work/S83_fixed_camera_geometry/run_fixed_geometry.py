"""S83 one-shot saved-head geometry diagnostic. Real execution is root-only.

No backbone/renderer is created. Root supplies the external 300s/8GiB process
supervisor; this runner also checks its own time/RSS and retains partial output.
"""
import ast
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata as metadata
import io
import json
import math
import os
from pathlib import Path
import random
import resource
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "CONTRACT.json"
OUT = HERE / "execution_01"
sys.dont_write_bytecode = True


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    tmp.replace(path)


def setup(c):
    """Only imports the original S26 dependency/source route and local adapter."""
    sys.path[:0] = c["runtime"]["sys_path"]
    for p, expected in c["source_sha256"].items():
        assert sha(Path(p).read_bytes()) == expected, p
    actual_versions = {}
    for name, expected in c["runtime"]["distributions"].items():
        d = metadata.distribution(name)
        actual_versions[name] = dict(version=d.version, root=str(d.locate_file("")))
        assert actual_versions[name] == expected, (name, actual_versions[name], expected)
    import numpy as np
    import torch
    import cv2
    import cloud_opt.dust3r_opt.optimizer as original
    import cloud_opt.dust3r_opt.base_opt as base
    import cloud_opt.dust3r_opt.init_im_poses as init
    from gradient_preserving_optimizer import with_gradient_preserving_depths
    assert str(Path(original.__file__).resolve()) == c["optimizer_source"]
    functions = ast.parse(Path(c["wrapper_source"]).read_text())
    selected = [n for n in functions.body if isinstance(n, ast.FunctionDef) and n.name in {"listify", "collate_with_cat"}]
    assert len(selected) == 2
    ns = dict(np=np, torch=torch)
    exec(compile(ast.Module(body=selected, type_ignores=[]), c["wrapper_source"], "exec"), ns)
    return dict(np=np, torch=torch, cv2=cv2, base=base, init=init,
                Scene=with_gradient_preserving_depths(original.PointCloudOptimizer),
                collate=ns["collate_with_cat"], versions=actual_versions)


def assemble_scene(ctx, images, heads, poses, K, options):
    T = ctx["torch"]
    n, _, height, width = images.shape
    assert n == len(heads) == 4 and poses.shape == (4, 4, 4) and K.shape == (4, 3, 3)
    views = [dict(idx=i, img=images[i:i+1], true_shape=T.tensor([[height, width]], dtype=T.int32)) for i in range(n)]
    cat = ctx["collate"]
    output = dict(view1=cat([views[0]] * 3), view2=cat(views[1:]),
                  pred1=cat([heads[0]] * 3), pred2=cat(heads[1:]))
    scene = ctx["Scene"](output["view1"], output["view2"], output["pred1"], output["pred2"], **options).to("cpu")
    assert scene.edges == [(0, 1), (0, 2), (0, 3)]
    assert T.equal(K[:, 0, 0], K[:, 1, 1])
    scene.preset_pose(poses)
    scene.preset_focal(K[:, 0, 0].tolist())
    scene.preset_principal_point(K[:, :2, 2].numpy())
    assert not scene.im_poses.requires_grad and not scene.im_focals.requires_grad and not scene.im_pp.requires_grad
    assert not scene.norm_pw_scale and not scene.pw_adaptors.requires_grad
    assert all(p.requires_grad and p.is_leaf for p in scene.im_depthmaps)
    return scene


def fixed_parameters(scene):
    return {n: p.detach().clone() for n, p in scene.named_parameters()
            if not p.requires_grad and not n.startswith("im_conf.")}


def check_fixed(ctx, scene, initial, poses, K, tolerances):
    T = ctx["torch"]
    current = fixed_parameters(scene)
    assert set(current) == set(initial)
    assert all(T.equal(current[n], initial[n]) for n in initial), "frozen parameter changed"
    assert not scene.im_poses.requires_grad and not scene.im_focals.requires_grad and not scene.im_pp.requires_grad
    assert not scene.norm_pw_scale and not scene.pw_adaptors.requires_grad
    p_error = float((scene.get_im_poses() - poses).abs().max())
    k_error = float((scene.get_intrinsics() - K).abs().max())
    assert p_error <= tolerances["P_absolute"] and k_error <= tolerances["K_absolute_px"]
    return dict(P_max_abs=p_error, K_max_abs_px=k_error, encoded_frozen_exact=True)


def main():
    raw_contract = CONTRACT.read_bytes()
    c = json.loads(raw_contract)
    assert sha(Path(__file__).read_bytes()) == c["runner_sha256"]
    assert Path(c["output_directory"]) == OUT
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    r = dict(schema="S83-fixed-camera-geometry-v1", status="RUNNING", started_utc=utc(),
             contract_sha256=sha(raw_contract), runner_sha256=c["runner_sha256"], reads=[],
             artifacts=[], iterations_completed=0, initializer_calls=0, pnp_calls=[],
             clean_calls=0, model_loads=0, model_forwards=0, new_RGB_decodes=0,
             sensor_depth_reads=0, renders=0, generation_calls=0, new_method_validated=False)

    def flush():
        r["elapsed_seconds"] = time.monotonic() - started
        r["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        dump(OUT / "RECEIPT.json", r)

    def limit():
        flush()
        assert r["elapsed_seconds"] <= c["resources"]["wall_seconds"], "wall limit"
        assert r["peak_self_rss_bytes"] <= c["resources"]["rss_bytes"], "self RSS limit"

    def timeout(signum, frame):
        raise TimeoutError("S83 alarm expired; retain partial artifacts")

    allowed_inputs = {p["path"] for p in c["inputs"]}
    opened = []

    def guard(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "urllib.Request"}:
            raise RuntimeError("network forbidden")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(args[0])).resolve()
            if p.is_relative_to(OUT):
                return
            if p.suffix.lower() in {".npz", ".npy", ".png", ".jpg", ".pth", ".pt", ".safetensors", ".exr"}:
                assert str(p) in allowed_inputs, "unlisted scientific input: " + str(p)
                assert str(p) not in opened, "scientific input already read"
                mode, flags = args[1], args[2]
                assert not (isinstance(mode, str) and any(x in mode for x in "wax+"))
                assert not (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR))
                opened.append(str(p))

    def load_input(spec):
        p = Path(spec["path"])
        raw = p.read_bytes()
        r["reads"].append(dict(path=str(p), bytes=len(raw), sha256=sha(raw), role=spec["role"]))
        flush()
        assert sha(raw) == spec["sha256"] and len(raw) == spec["size_bytes"]
        with np.load(io.BytesIO(raw), allow_pickle=False) as z:
            assert set(z.files) == set(spec["tensors"])
            arrays = {key: z[key].copy() for key in z.files}
        for key, a in arrays.items():
            meta = spec["tensors"][key]
            assert list(a.shape) == meta["shape"] and str(a.dtype) == meta["dtype"]
            assert sha(a.tobytes(order="C")) == meta["body_sha256"]
            assert np.isfinite(a).all(), (spec["role"], key)
        return arrays

    def array(value):
        return value.detach().cpu().numpy().copy() if T.is_tensor(value) else np.array(value, copy=True)

    def save(name, arrays):
        values = {k: array(v) for k, v in arrays.items()}
        path = OUT / name
        with path.open("xb") as f:
            np.savez_compressed(f, **values)
        r["artifacts"].append(dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path.read_bytes()),
            tensors={k: dict(shape=list(a.shape), dtype=str(a.dtype), body_sha256=sha(a.tobytes(order="C")),
                            finite=bool(np.isfinite(a).all())) for k, a in values.items()}))
        flush()
        assert all(np.isfinite(a).all() for a in values.values()), "nonfinite artifact retained: " + name

    def snapshot(name):
        with T.no_grad():
            save(name, dict(depth=T.stack(scene.get_depthmaps()), world_points=T.stack(scene.get_pts3d()),
                log_depth=T.stack(list(scene.im_depthmaps)), confidence=T.stack(list(scene.im_conf)),
                c2w=scene.get_im_poses(), K=scene.get_intrinsics(), pw_poses=scene.pw_poses,
                pw_adaptors=scene.pw_adaptors, colors=np.array(scene.imgs),
                history_ids=np.array(c["history_ids"], np.int64)))

    def summary(value):
        if value is None:
            return dict(is_none=True)
        a = value.detach()
        maximum, norm = float(a.abs().max()), float(a.double().norm())
        return dict(is_none=False, finite=bool(T.isfinite(a).all()), shape=list(a.shape), dtype=str(a.dtype),
                    max_abs=maximum if math.isfinite(maximum) else repr(maximum),
                    l2=norm if math.isfinite(norm) else repr(norm),
                    nonzero=int(T.count_nonzero(a)), body_sha256=sha(array(a).tobytes()))

    def checked_loss(value, label):
        value = float(value)
        r[label] = value if math.isfinite(value) else {"nonfinite": repr(value)}
        assert math.isfinite(value), label + " is nonfinite"
        return value

    original_pnp = None
    try:
        assert sys.platform == "darwin" and sys.executable == c["runtime"]["python"]
        os.environ.update(c["runtime"]["environment"])
        sys.addaudithook(guard)
        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(c["resources"]["wall_seconds"])
        ctx = setup(c)
        np, T, cv2 = ctx["np"], ctx["torch"], ctx["cv2"]
        assert T.is_grad_enabled() and not T.is_inference_mode_enabled()
        assert not T.is_autocast_enabled("cpu") and not T.is_autocast_enabled("cuda")
        T.set_num_threads(c["optimization"]["torch_threads"])
        cv2.setNumThreads(1)
        T.manual_seed(82); np.random.seed(82); random.seed(82); cv2.setRNGSeed(82)
        r["versions"] = ctx["versions"]
        r["source_paths"] = dict(base=ctx["base"].__file__, initializer=ctx["init"].__file__)
        loaded = {spec["role"]: load_input(spec) for spec in c["inputs"]}
        pre = loaded["preprocessed"]
        assert pre["history_ids"].tolist() == c["history_ids"] == [12, 13, 18, 19]
        assert np.array_equal(pre["K_512_approx"], np.array(c["K_512_nominal"], np.float64))
        images = T.from_numpy(pre["images_normalized"])
        heads = [{k: T.from_numpy(a) for k, a in loaded[f"head_{i}"].items()} for i in range(4)]
        for head in heads:
            assert bool((head["conf"] > 0).all() and (head["conf_self"] > 0).all())
        camera = loaded["camera_archive"]
        all_ids = camera["ids"].tolist()
        assert len(set(all_ids)) == len(all_ids)
        rows = [all_ids.index(i) for i in c["history_ids"]]
        poses = T.from_numpy(camera["c2ws"][rows].astype(np.float32))
        K = T.from_numpy(np.repeat(pre["K_512_approx"][None], 4, axis=0).astype(np.float32))
        r["camera_archive_selection"] = dict(archive_ids=all_ids, selected_rows=rows,
            consumed_ids=c["history_ids"], other_camera_rows_used_in_computation=False)
        save("GIVEN_P_K.npz", dict(c2w_input_float64=camera["c2ws"][rows], c2w_input_fp32=poses,
                                   K_input_fp32=K, history_ids=pre["history_ids"]))
        scene = assemble_scene(ctx, images, heads, poses, K, c["scene_options"])
        fixed = fixed_parameters(scene)
        r["preset_readback"] = check_fixed(ctx, scene, fixed, poses, K, c["tolerances"])
        r["actual_fields"] = dict(edges=scene.edges, imshapes=scene.imshapes, min_conf_thr=scene.min_conf_thr,
            norm_pw_scale=scene.norm_pw_scale, base_scale=scene.base_scale, pw_break=scene.pw_break,
            focal_break=scene.focal_break, parameter_flags={n: p.requires_grad for n, p in scene.named_parameters()})
        save("FROZEN_PARAMETERS.npz", fixed)
        save("CONSUMED_OBSERVATIONS.npz", dict(pred_i=scene._stacked_pred_i, pred_j=scene._stacked_pred_j,
            weight_i=scene._weight_i, weight_j=scene._weight_j, edge_i=scene._ei, edge_j=scene._ej))
        original_pnp = ctx["init"].fast_pnp

        def observed_pnp(*args, **kwargs):
            answer = original_pnp(*args, **kwargs)
            r["pnp_calls"].append(dict(success=answer is not None, niter_PnP=kwargs.get("niter_PnP"),
                estimated_focal=None if answer is None else float(answer[0])))
            flush()
            return answer

        ctx["init"].fast_pnp = observed_pnp
        r["initializer_calls"] += 1
        limit()
        ctx["init"].init_minimum_spanning_tree(scene, niter_PnP=10)
        ctx["init"].fast_pnp = original_pnp
        original_pnp = None
        r["after_MST_readback"] = check_fixed(ctx, scene, fixed, poses, K, c["tolerances"])
        snapshot("INITIALIZED_STATE.npz")
        with T.no_grad():
            checked_loss(scene(), "initial_loss")
        registered_ids = [id(p) for p in scene.im_depthmaps]
        initial_depth_parameters = [p.detach().clone() for p in scene.im_depthmaps]
        optimizer = T.optim.Adam([p for p in scene.parameters() if p.requires_grad], lr=.01, betas=(.9, .9))
        r["adam_parameter_names"] = [n for n, p in scene.named_parameters() if p.requires_grad]
        with (OUT / "STEPS.jsonl").open("x", buffering=1) as log:
            for n in range(100):
                limit()
                before = [p.detach().clone() for p in scene.im_depthmaps]
                loss, lr = ctx["base"].global_alignment_iter(scene, n, 100, .01, 1e-6, optimizer, "linear")
                entry = dict(step=n, loss_before_step=loss if math.isfinite(loss) else {"nonfinite": repr(loss)}, lr=lr,
                    registered_leaf_ids_unchanged=registered_ids == [id(p) for p in scene.im_depthmaps],
                    depth_gradients=[summary(p.grad) for p in scene.im_depthmaps],
                    depth_deltas=[summary(p.detach() - old) for p, old in zip(scene.im_depthmaps, before)])
                log.write(json.dumps(entry, allow_nan=False) + "\n")
                assert np.isfinite(loss) and entry["registered_leaf_ids_unchanged"]
                assert all(not x["is_none"] and x["finite"] for x in entry["depth_gradients"])
                assert all(x["finite"] for x in entry["depth_deltas"])
                check_fixed(ctx, scene, fixed, poses, K, c["tolerances"])
                r["iterations_completed"] = n + 1
                r["last_pre_step_loss"] = loss
                flush()
        with T.no_grad():
            checked_loss(scene(), "final_loss_after_100_updates")
        r["total_registered_depth_deltas"] = [summary(p.detach() - old) for p, old in zip(scene.im_depthmaps, initial_depth_parameters)]
        r["final_readback"] = check_fixed(ctx, scene, fixed, poses, K, c["tolerances"])
        snapshot("FINAL_BEFORE_CLEAN.npz")
        depth_before_clean = T.stack(scene.get_depthmaps()).detach().clone()
        scene.clean_pointcloud(tol=.001, bad_conf=0)
        r["clean_calls"] += 1
        assert T.equal(T.stack(scene.get_depthmaps()).detach(), depth_before_clean)
        r["after_clean_readback"] = check_fixed(ctx, scene, fixed, poses, K, c["tolerances"])
        snapshot("FINAL_AFTER_CLEAN.npz")
        r["step_log_sha256"] = sha((OUT / "STEPS.jsonl").read_bytes())
        assert set(opened) == allowed_inputs and len(opened) == 6
        limit()
        r.update(status="COMPLETED_FIXED_BUDGET_DIAGNOSTIC", completed_utc=utc(),
                 scientific_scope="Fixed historical RGB prediction observer fit with known approximate P/K; no physical geometry truth or generation claim")
    except BaseException:
        r.update(status="FAILED", completed_utc=utc(), traceback=traceback.format_exc())
        raise
    finally:
        if original_pnp is not None:
            ctx["init"].fast_pnp = original_pnp
        signal.alarm(0)
        r["actual_scientific_file_open_order"] = opened
        flush()


if __name__ == "__main__":
    main()
