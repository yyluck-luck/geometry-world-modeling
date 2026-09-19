"""S83 real geometry class on tiny artificial inputs; no real arrays or MST."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
OUT = HERE / "INTERFACE_SYNTHETIC_01.json"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    timer = time.monotonic()
    r = dict(started_utc=utc(), status="RUNNING", dtype="float32", device="cpu",
             runner_sha256=sha(HERE / "run_fixed_geometry.py"),
             contract_sha256=sha(HERE / "CONTRACT.json"), checker_sha256=sha(Path(__file__)),
             artificial_image_shape=[4, 3, 2, 3], real_scientific_array_reads=0,
             learned_model_calls=0, real_optimizer_runs=0, artificial_scene_instances=0,
             artificial_adam_steps=0, MST_calls=0, clean_calls=0)
    with OUT.open("x") as f:
        json.dump(r, f)

    def guard(event, args):
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(args[0]))
            if p.suffix.lower() in {".npz", ".npy", ".png", ".jpg", ".pth", ".safetensors"}:
                raise RuntimeError("No scientific input bodies in synthetic precheck: " + str(p))
        if event in {"socket.connect", "socket.getaddrinfo"}:
            raise RuntimeError("No network")

    try:
        sys.dont_write_bytecode = True
        sys.addaudithook(guard)
        spec = importlib.util.spec_from_file_location("s83_source_under_test", HERE / "run_fixed_geometry.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        c = json.loads((HERE / "CONTRACT.json").read_text())
        ctx = m.setup(c)
        T = ctx["torch"]
        T.set_num_threads(1)
        T.manual_seed(83)
        ctx["cv2"].setNumThreads(1)
        images = T.zeros((4, 3, 2, 3), dtype=T.float32)
        P = T.eye(4).repeat(4, 1, 1)
        P[:, 0, 3] = T.tensor([0., .1, .2, .3])
        K = T.tensor([[2., 0., 1.1], [0., 2., .6], [0., 0., 1.]]).repeat(4, 1, 1)
        v, u = T.meshgrid(T.arange(2.), T.arange(3.), indexing="ij")
        self_pts = T.stack(((u - 1.1) * .8, (v - .6) * .8, T.full_like(u, 1.6)), dim=-1)[None]
        heads = []
        for i in range(4):
            heads.append(dict(pts3d_in_self_view=self_pts.clone(),
                pts3d_in_other_view=self_pts + T.tensor([i * .1, 0., 0.]),
                conf_self=T.full((1, 2, 3), 3.5), conf=T.full((1, 2, 3), 3.5),
                camera_pose=T.tensor([[0., 0., 0., 1., 0., 0., 0.]]), rgb=T.zeros((1, 2, 3, 3))))
        scene = m.assemble_scene(ctx, images, heads, P, K, c["scene_options"])
        r["artificial_scene_instances"] = 1
        frozen = m.fixed_parameters(scene)
        r["preset_readback"] = m.check_fixed(ctx, scene, frozen, P, K, c["tolerances"])
        r["edges"] = scene.edges
        r["get_depthmaps_raw_shape"] = list(scene.get_depthmaps(True).shape)
        r["get_pts3d_shapes"] = [list(x.shape) for x in scene.get_pts3d()]
        assert T.equal(scene._stacked_pred_i[0], self_pts[0].reshape(-1, 3))
        assert T.equal(scene._stacked_pred_j[2], heads[3]["pts3d_in_other_view"][0].reshape(-1, 3))
        before = [p.detach().clone() for p in scene.im_depthmaps]
        optimizer = T.optim.Adam([p for p in scene.parameters() if p.requires_grad], lr=.01, betas=(.9, .9))
        loss, lr = ctx["base"].global_alignment_iter(scene, 0, 100, .01, 1e-6, optimizer, "linear")
        r["artificial_adam_steps"] = 1
        r["loss_before_one_step"], r["lr"] = loss, lr
        r["registered_depth_gradients"] = [dict(is_none=p.grad is None,
            finite=False if p.grad is None else bool(T.isfinite(p.grad).all()),
            norm=None if p.grad is None else float(p.grad.double().norm())) for p in scene.im_depthmaps]
        r["registered_depth_changed"] = [not T.equal(p.detach(), q) for p, q in zip(scene.im_depthmaps, before)]
        r["post_step_readback"] = m.check_fixed(ctx, scene, frozen, P, K, c["tolerances"])
        assert all(not x["is_none"] and x["finite"] for x in r["registered_depth_gradients"])
        assert all(r["registered_depth_changed"])
        r.update(status="PASS_TINY_ARTIFICIAL_INTERFACE", actual_torch_threads=T.get_num_threads(),
                 boundary="One 4x2x3 artificial scene step only. Real caches, real P/K, MST/PnP,100steps,clean and geometric accuracy not tested.")
    except BaseException:
        r.update(status="FAILED", traceback=traceback.format_exc())
        raise
    finally:
        r.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - timer)
        OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + "\n")
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
