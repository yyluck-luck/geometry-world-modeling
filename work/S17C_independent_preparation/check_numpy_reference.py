#!/usr/bin/env python3
"""Bounded artificial checks of the independent path against source functions."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    began = datetime.now(timezone.utc).isoformat()
    torch.set_num_threads(1)
    mathfile = Path(__file__).with_name('numerical_reference.py')
    spec = importlib.util.spec_from_file_location('independent_math', mathfile)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    ns = dict(np=np, torch=torch)
    ids = []
    for relative, name in [('src/dust3r/utils/geometry.py', 'geotrf'),
                            ('cloud_opt/dust3r_opt/base_opt.py', 'clean_pointcloud')]:
        p = a.source / relative
        node = next(n for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(p), 'exec'), ns)
        ids.append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    checks = []
    def check(name, value):
        assert value, name
        checks.append(dict(name=name, passed=True))
    depth = np.array([[[1,1,3],[2,2,1]], [[2,2,2],[2,1,2]]], dtype=np.float32)
    conf = np.array([[[2,5,6],[7,9,4]], [[8,3,10],[7,6,1]]], dtype=np.float32)
    rot = np.array([[[0,-1,0],[1,0,0],[0,0,1]]] * 2, dtype=np.float32)
    trans = np.array([[1,2,3]] * 2, dtype=np.float32)
    focal = np.array([[2.]] * 2, dtype=np.float32)
    pp = np.array([[1.5,1.]] * 2, dtype=np.float32)
    world = ref.reconstruct_world(depth, focal, pp, rot, trans).astype(np.float32)
    k = np.array([[[2,0,1.5],[0,2,1],[0,0,1]]] * 2, dtype=np.float32)
    cam = np.linalg.inv(ref.camera_matrices(rot, trans).astype(np.float32))
    got_source = np.stack([x.numpy() for x in ns['clean_pointcloud'](
        list(torch.from_numpy(conf)), torch.from_numpy(k), torch.from_numpy(cam),
        list(torch.from_numpy(depth)), list(torch.from_numpy(world)))])
    got_numpy, visits, margins = ref.clean_reference(conf, depth, world, focal, pp, rot, trans)
    expected = np.array([[[0,5,6],[7,9,4]], [[8,3,10],[7,0,1]]], dtype=np.float32)
    check('nonidentity_cameras_hand_expected_clean', np.array_equal(got_source, expected))
    check('independent_fp32_clean_matches_original_on_artificial_fixture', np.array_equal(got_numpy, got_source))
    check('all_projection_margins_retained', len(margins) == 12 and sum(v['actually_changed'] for v in visits) == 2)
    test_world = np.array([[[[3.,4.,0.]]], [[[0.,0.,12.]]]])
    objective = ref.pair_objective(test_world, np.zeros((1,1,3)), np.zeros((1,1,3)),
                                   np.array([[np.e]]), np.array([[np.e**2]]), np.eye(4), np.ones(3))
    check('euclidean_logweighted_two_endpoint_objective_not_manhattan', abs(objective - 29.) < 1e-12)
    check('iteration_schedule_400_no_final_step_at_minimum', len(ref.expected_learning_rates()) == 400 and
          abs(ref.expected_learning_rates()[-1] - .0000259975) < 1e-17)
    receipt = dict(schema='s17c-independent-numpy-artificial-v1', status='PASS_ARTIFICIAL_ONLY',
                   started_utc=began, completed_utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                   source_identities=ids, numerical_reference_sha256=hashlib.sha256(mathfile.read_bytes()).hexdigest(),
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   real_image_reads=0, weights_read=0, gt_read=0, model_calls=0, optimizer_runs=0)
    (a.output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'], output=str(a.output/'receipt.json'))))

if __name__ == '__main__':
    main()
