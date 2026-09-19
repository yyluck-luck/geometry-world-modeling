#!/usr/bin/env python3
"""Tiny artificial source-function checks. No model/checkpoint/image/data reads."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    torch.set_num_threads(1)
    ns = {'np': np, 'torch': torch}
    identities = []
    selections = [
        ('src/dust3r/utils/geometry.py', ['geotrf']),
        ('src/dust3r/utils/image.py', ['rgb']),
        ('cloud_opt/dust3r_opt/commons.py', ['linear_schedule']),
        ('cloud_opt/dust3r_opt/optimizer.py', ['_fast_depthmap_to_pts3d']),
        ('cloud_opt/dust3r_opt/base_opt.py', ['clean_pointcloud']),
    ]
    for relative, names in selections:
        path = args.source / relative
        tree = ast.parse(path.read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        assert {n.name for n in nodes} == set(names)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
        identities.append({'path': str(path), 'sha256': sha(path), 'functions': names})
    checks = []

    def check(name, predicate, **evidence):
        assert bool(predicate), name
        checks.append({'name': name, 'pass': True, **evidence})

    # Camera z is not Euclidean range. Output world point uses c2w, no y/z flip.
    vv, uu = np.meshgrid(np.arange(2), np.arange(3), indexing='ij')
    grid = np.stack([uu, vv], axis=-1).reshape(1, -1, 2).astype(np.float64)
    z = np.array([[[1., 2., 3.], [2., 3., 4.]]])
    pp = np.array([[1.5, 1.]])
    f = np.array([[2.]])
    expected_camera = np.stack([(uu - 1.5) * z[0] / 2,
                                (vv - 1.) * z[0] / 2, z[0]], axis=-1)
    actual_camera = ns['_fast_depthmap_to_pts3d'](
        torch.from_numpy(z), torch.from_numpy(grid), torch.from_numpy(f), torch.from_numpy(pp))
    check('camera_z_backprojection', np.array_equal(actual_camera.numpy().reshape(2, 3, 3), expected_camera))
    c2w = np.array([[0., -1., 0., 1.], [1., 0., 0., 2.], [0., 0., 1., 3.], [0., 0., 0., 1.]])
    expected_world = expected_camera @ c2w[:3, :3].T + c2w[:3, 3]
    actual_world = ns['geotrf'](torch.from_numpy(c2w), actual_camera.reshape(2, 3, 3))
    check('world_c2w_rotation_translation', np.array_equal(actual_world.numpy(), expected_world))
    actual_back = ns['geotrf'](torch.from_numpy(np.linalg.inv(c2w)), actual_world)
    check('inverse_c2w_recovers_camera_z', np.array_equal(actual_back.numpy(), expected_camera))

    # Original cleaner on a hand-enumerated two-view same-camera fixture.
    depths = [torch.tensor([[1., 1., 3.], [2., 2., 1.]], dtype=torch.float64),
              torch.tensor([[2., 2., 2.], [2., 1., 2.]], dtype=torch.float64)]
    confs = [torch.tensor([[2., 5., 6.], [7., 9., 4.]], dtype=torch.float64),
             torch.tensor([[8., 3., 10.], [7., 6., 1.]], dtype=torch.float64)]
    original_conf = [c.clone() for c in confs]
    points = [torch.stack([torch.from_numpy(uu) * d, torch.from_numpy(vv) * d, d], dim=-1) for d in depths]
    orig_points = [p.clone() for p in points]
    orig_depths = [d.clone() for d in depths]
    actual_clean = ns['clean_pointcloud'](confs, [torch.eye(3, dtype=torch.float64)] * 2,
                                        [torch.eye(4, dtype=torch.float64)] * 2, depths, points)
    expected_clean = [np.array([[0., 5., 6.], [7., 9., 4.]]), np.array([[8., 3., 10.], [7., 0., 1.]])]
    check('clean_strict_depth_and_lower_confidence', all(np.array_equal(a.numpy(), b) for a, b in zip(actual_clean, expected_clean)),
          expected=[x.tolist() for x in expected_clean])
    check('clean_function_returns_new_confs_without_geometry_change',
          all(torch.equal(a, b) for a, b in zip(points, orig_points)) and
          all(torch.equal(a, b) for a, b in zip(depths, orig_depths)) and
          all(torch.equal(a, b) for a, b in zip(confs, original_conf)))

    # Half-pixel source projects to x=.5. Torch rounds to even 0, not floor(x+.5)=1.
    half_confs = [torch.tensor([[2., 2.]], dtype=torch.float64), torch.tensor([[9., 1.]], dtype=torch.float64)]
    half_depths = [torch.tensor([[1., 1.]], dtype=torch.float64), torch.tensor([[2., 2.]], dtype=torch.float64)]
    half_points = [torch.tensor([[[.5, 0., 1.], [99., 0., 1.]]], dtype=torch.float64),
                   torch.tensor([[[0., 0., 2.], [2., 0., 2.]]], dtype=torch.float64)]
    half_clean = ns['clean_pointcloud'](half_confs, [torch.eye(3, dtype=torch.float64)] * 2,
                                       [torch.eye(4, dtype=torch.float64)] * 2, half_depths, half_points)
    check('clean_round_ties_even_and_outside_kept', half_clean[0].tolist() == [[0., 2.]])

    # Scene colors come from normalized input, not predicted rgb.
    normalized = torch.tensor([[[-1., 1.]], [[0., -1.]], [[1., 0.]]])
    color = ns['rgb'](normalized)
    check('input_color_denormalization_rgb_not_bgr', np.array_equal(color, [[[0., .5, 1.], [1., 0., .5]]]))
    lrs = [ns['linear_schedule'](i / 400, .01, 1e-6) for i in range(400)]
    check('400_step_schedule_pre_step_endpoint', lrs[0] == .01 and abs(lrs[-1] - .0000259975) < 1e-17,
          first=lrs[0], last=lrs[-1], configured_minimum=1e-6)
    # Integer geometry only: no PIL images constructed or opened.
    resized = tuple(round(d * 512 / 640) for d in (640, 480))
    cx, cy = resized[0] // 2, resized[1] // 2
    halfw, halfh = ((2 * cx) // 16) * 8, ((2 * cy) // 16) * 8
    check('native640x480_crop_keeps384x512', resized == (512, 384) and
          (cx-halfw, cy-halfh, cx+halfw, cy+halfh) == (0, 0, 512, 384))
    ended = datetime.now(timezone.utc).isoformat()
    receipt = {'schema': 's17c-independent-artificial-interface-v1', 'status': 'PASS_ARTIFICIAL_ONLY',
               'started_utc': started, 'completed_utc': ended, 'script_sha256': sha(Path(__file__)),
               'numpy': np.__version__, 'torch': torch.__version__, 'source_identities': identities,
               'checks': checks, 'real_images_read': 0, 'checkpoint_reads': 0, 'gt_reads': 0,
               'model_calls': 0, 'global_optimizer_runs': 0,
               'scope': 'AST-extracted pure source functions on tiny invented arrays; not inference or real optimization validation.'}
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'output': str(args.output / 'receipt.json'), 'checks': len(checks)}))


if __name__ == '__main__':
    main()
