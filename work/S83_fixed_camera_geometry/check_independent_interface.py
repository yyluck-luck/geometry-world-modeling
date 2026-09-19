"""Independent tiny artificial interface check; never calls runner.main."""
from pathlib import Path
import sys, os, json, hashlib, importlib.util, time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def guard(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "urllib.Request"}:
        raise RuntimeError("No network in independent synthetic review")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        p = Path(os.fsdecode(args[0]))
        if p.suffix.lower() in {".npz", ".npy", ".png", ".jpg", ".pth", ".pt", ".safetensors", ".exr"}:
            raise RuntimeError("No scientific arrays or images in independent synthetic review: " + str(p))

def main():
    sys.addaudithook(guard)
    start = time.monotonic()
    report = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                  runner_sha256=sha(HERE / "run_fixed_geometry.py"),
                  contract_sha256=sha(HERE / "CONTRACT.json"),
                  reviewer_sha256=sha(Path(__file__)), real_array_reads=0,
                  real_model_loads=0, real_optimizer_calls=0, mst_calls=0, clean_calls=0)
    c = json.loads((HERE / "CONTRACT.json").read_text())
    assert report["runner_sha256"] == c["runner_sha256"]
    spec = importlib.util.spec_from_file_location("s83_reviewed_runner", HERE / "run_fixed_geometry.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ctx = m.setup(c)
    T = ctx["torch"]
    T.set_num_threads(1); T.manual_seed(831)
    h, w = 3, 4
    images = T.zeros(4, 3, h, w)
    P = T.eye(4).repeat(4, 1, 1)
    for i in range(4):
        angle = T.tensor(.17 * (i + 1))
        cs, sn = T.cos(angle), T.sin(angle)
        P[i, :3, :3] = T.tensor([[cs, -sn, 0.], [sn, cs, 0.], [0., 0., 1.]])
        P[i, :3, 3] = T.tensor([.12 * i, -.07 * i, .03 * i])
    K = T.tensor([[3., 0., 1.17], [0., 3., .81], [0., 0., 1.]]).repeat(4, 1, 1)
    y, x = T.meshgrid(T.arange(h), T.arange(w), indexing="ij")
    base = T.stack(((x - 1.17) / 3, (y - .81) / 3, T.ones(h, w)), -1)
    heads = []
    for i in range(4):
        local = base * (1.1 + .2 * i)
        other = local + T.tensor([.3 * i, .1 * i, .2])
        heads.append(dict(pts3d_in_self_view=local[None], pts3d_in_other_view=other[None],
                          conf_self=T.full((1,h,w), 4. + i), conf=T.full((1,h,w), 7. + i),
                          rgb=T.zeros(1,h,w,3), camera_pose=T.tensor([[0.,0.,0.,1.,0.,0.,0.]])))
    scene = m.assemble_scene(ctx, images, heads, P, K, c["scene_options"])
    fixed = m.fixed_parameters(scene)
    report["preset_readback"] = m.check_fixed(ctx, scene, fixed, P, K, c["tolerances"])
    for j in range(3):
        assert T.equal(scene._stacked_pred_i[j], heads[0]["pts3d_in_self_view"].reshape(-1,3))
        assert T.equal(scene._stacked_pred_j[j], heads[j+1]["pts3d_in_other_view"].reshape(-1,3))
        T.testing.assert_close(scene._weight_i[j], T.log(heads[0]["conf_self"]).reshape(-1))
        T.testing.assert_close(scene._weight_j[j], T.log(heads[j+1]["conf"]).reshape(-1))
    direct = T.stack(scene.get_depthmaps()).sum()
    gradients = T.autograd.grad(direct, tuple(scene.im_depthmaps))
    for g, leaf in zip(gradients, scene.im_depthmaps):
        T.testing.assert_close(g, leaf.exp())
    before = [p.detach().clone() for p in scene.im_depthmaps]
    ids = [id(p) for p in scene.im_depthmaps]
    optimizer = T.optim.Adam([p for p in scene.parameters() if p.requires_grad], lr=.01, betas=(.9,.9))
    loss, lr = ctx["base"].global_alignment_iter(scene, 0, 100, .01, 1e-6, optimizer, "linear")
    assert ids == [id(p) for p in scene.im_depthmaps]
    finite = [bool(p.grad is not None and T.isfinite(p.grad).all()) for p in scene.im_depthmaps]
    changed = [not T.equal(a, b) for a,b in zip(before, scene.im_depthmaps)]
    assert all(finite) and all(changed)
    report.update(status="PASS_SYNTHETIC_INTERFACE_ONLY", synthetic_image_shape=list(images.shape),
                  artificial_original_adam_steps=1, depth_gradient_finite=finite, depth_parameters_changed=changed,
                  self0_crossj_and_log_confidence_mapping=True, exp_derivative_to_registered_leaf=True,
                  nonidentity_rotation_and_offcenter_principal_point=True,
                  after_step_readback=m.check_fixed(ctx, scene, fixed, P, K, c["tolerances"]),
                  loss_before_artificial_step=loss, learning_rate=lr,
                  elapsed_seconds=time.monotonic()-start, completed_utc=datetime.now(timezone.utc).isoformat(),
                  scope="Artificial 4x3x4 only; actual original class and one original iteration. No MST/clean/real data or 100-step claim.")
    output = HERE / "INDEPENDENT_INTERFACE_SYNTHETIC.json"
    with output.open("x") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(report))

if __name__ == "__main__":
    main()
