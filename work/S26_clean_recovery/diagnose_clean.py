"""Saved common_old diagnostic only: no model, GA or sensor GT access."""
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

import numpy as np
import torch

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
DATA = ROOT / 'results/S26_consumer_baseline/common_old'
EMBEDDED = ROOT / 'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def extract(path, names, namespace):
    tree = ast.parse(Path(path).read_text())
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(body) == len(names)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), namespace)


def project(points, inverse, intrinsics, arithmetic):
    if arithmetic == 'torch_matmul':
        p = torch.from_numpy(points)
        mat = torch.from_numpy(inverse)
        cam = (p @ mat.T[:3, :] + mat.T[3:4, :])[..., :3]
        homogeneous = cam @ torch.from_numpy(intrinsics).T
        xy = (homogeneous / homogeneous[..., 2:3])[..., :2]
        return xy.numpy().copy(), cam[..., 2].numpy().copy()
    if arithmetic == 'numpy_matmul':
        cam = (points @ inverse.T[:3, :] + inverse.T[3:4, :])[..., :3]
        homogeneous = cam @ intrinsics.T
        return (homogeneous / homogeneous[..., 2:3])[..., :2], cam[..., 2]
    assert arithmetic == 'numpy_component'
    cam = np.stack([((points[..., 0] * inverse[k, 0] + points[..., 1] * inverse[k, 1])
                     + points[..., 2] * inverse[k, 2]) + inverse[k, 3] for k in range(3)], -1)
    z = cam[..., 2]
    xy = np.stack(((intrinsics[0, 0] * cam[..., 0] + intrinsics[0, 2] * z) / z,
                   (intrinsics[1, 1] * cam[..., 1] + intrinsics[1, 2] * z) / z), -1)
    return xy, z


def trajectory(conf, depth, projections):
    result, traces = conf.copy(), []
    h, w = depth.shape[-2:]
    for i, j, xy, z in projections:
        assert np.isfinite(xy).all() and np.isfinite(z).all()
        uv = np.rint(xy).astype(np.int64)
        u, v = uv[..., 0], uv[..., 1]
        valid = (z > 0) & (u >= 0) & (u < w) & (v >= 0) & (v < h)
        rr, cc = v.clip(0, h - 1), u.clip(0, w - 1)
        threshold = np.float32(.999) * depth[j, rr, cc]
        target_conf = result[j, rr, cc]
        front = z < threshold
        weaker = result[i] < target_conf
        bad = valid & front & weaker
        before = result[i].copy()
        result[i][bad] = np.minimum(result[i][bad], np.float32(0))
        traces.append(dict(source=i, target=j, xy=xy, z=z, uv=uv,
                           valid=valid, front=front & valid, weaker=weaker & valid, bad=bad,
                           depth_margin=z-threshold, confidence_margin=before-target_conf,
                           before=before, after=result[i].copy()))
    return result, traces


def main():
    started, start = datetime.now(timezone.utc).isoformat(), time.monotonic()
    assert not (HERE / 'diagnostic_receipt.json').exists()
    torch.set_num_threads(8)
    assert np.__version__ == '1.26.4' and torch.__version__ == '2.7.0'
    seal = json.loads((HERE / 'pre_read_seal.json').read_bytes())
    for p, h in seal['identities'].items():
        assert sha(p) == h, p
    with np.load(DATA / 'output.npz', allow_pickle=False) as z:
        a = {k: z[k].copy() for k in z.files}
    with np.load(DATA / 'preclean_conf.npz', allow_pickle=False) as z:
        conf = z['conf'].copy()
    assert a['depth'].shape == conf.shape == (4, 384, 512)
    assert all(x.dtype == np.float32 and np.isfinite(x).all() for x in a.values())
    assert np.isfinite(conf).all() and (conf > 0).all()
    old = module(ROOT / 'work/S17C_independent_preparation/numerical_reference.py', 'old_reference')
    revised = module(HERE / 'clean_reference_torch_fp32.py', 'revised_reference')
    args = (conf, a['depth'], a['point_cloud'], a['focal'], a['pp'], a['c2w'][:, :3, :3], a['c2w'][:, :3, 3])
    old_output, old_visits, old_margins = old.clean_reference(*args)
    mismatch = old_output != a['conf']
    with np.load(DATA / 'clean_mismatch_diagnostics.npz', allow_pickle=False) as z:
        assert np.array_equal(mismatch, z['mismatch'])
        assert set(z.files) == set(old_margins) | {'mismatch'}
        for key, value in old_margins.items():
            assert np.array_equal(value, z[key], equal_nan=True), key
    del old_margins
    K = np.zeros((4, 3, 3), dtype=np.float32)
    K[:, 0, 0] = K[:, 1, 1] = a['focal'].reshape(4)
    K[:, :2, 2], K[:, 2, 2] = a['pp'], 1
    inverses = {
        'torch_batched': torch.linalg.inv(torch.from_numpy(a['c2w'])).numpy().copy(),
        'numpy_each': np.stack([np.linalg.inv(c) for c in a['c2w']]),
        'numpy_float64_cast32': np.linalg.inv(a['c2w'].astype(np.float64)).astype(np.float32),
    }
    namespace = {'torch': torch, 'np': np}
    extract(EMBEDDED / 'src/dust3r/utils/geometry.py', ('geotrf', 'inv'), namespace)
    extract(EMBEDDED / 'cloud_opt/dust3r_opt/base_opt.py', ('clean_pointcloud',), namespace)
    real_source = namespace['clean_pointcloud'](
        [torch.from_numpy(x) for x in conf], torch.from_numpy(K), torch.from_numpy(inverses['torch_batched']),
        [torch.from_numpy(x) for x in a['depth']], [torch.from_numpy(x) for x in a['point_cloud']])
    source_output = torch.stack(real_source).numpy().copy()
    assert np.array_equal(source_output, a['conf']), 'Exact original clean replay must reproduce saved producer'
    new_output, new_visits, new_margins = revised.clean_reference(*args)
    assert np.array_equal(new_output, a['conf']), 'Independent same-contract reference differs'
    del new_margins
    np.savez_compressed(HERE / 'independent_clean_outputs.npz', saved=a['conf'], old_numpy=old_output,
                        original_torch_replay=source_output, revised_torch_reference=new_output)
    variants = [('torch_batched', 'torch_matmul'), ('numpy_each', 'numpy_component'),
                ('numpy_each', 'torch_matmul'), ('torch_batched', 'numpy_component'),
                ('numpy_each', 'numpy_matmul'), ('torch_batched', 'numpy_matmul'),
                ('numpy_float64_cast32', 'torch_matmul')]
    summaries, pair_rows, masks, outputs = {}, [], {}, {}
    baseline_trace, old_trace = None, None
    for inverse_name, arithmetic in variants:
        name = inverse_name + '__' + arithmetic
        projections = [(i, j, *project(a['point_cloud'][i], inverses[inverse_name][j], K[j], arithmetic))
                       for i in range(4) for j in range(4) if i != j]
        output, traces = trajectory(conf, a['depth'], projections)
        outputs[name] = output
        if baseline_trace is None:
            baseline_trace = traces
            assert np.array_equal(output, source_output)
        if inverse_name == 'numpy_each' and arithmetic == 'numpy_component':
            old_trace = traces
            assert np.array_equal(output, old_output)
        summaries[name] = {'final_mismatch_pixels': int((output != a['conf']).sum()),
                           'by_frame': (output != a['conf']).reshape(4, -1).sum(axis=1).tolist()}
        masks[name] = np.stack([t['bad'] for t in traces])
        for t, b in zip(traces, baseline_trace):
            pair_rows.append({'variant': name, 'source': t['source'], 'target': t['target'],
                              'grid_pixels': 384*512,
                              'max_abs_xy_difference_px': float(np.abs(t['xy'] - b['xy']).max()),
                              'max_abs_z_difference_m': float(np.abs(t['z'] - b['z']).max()),
                              'uv_different_pixels': int(np.any(t['uv'] != b['uv'], axis=-1).sum()),
                              'valid_different_pixels': int((t['valid'] != b['valid']).sum()),
                              'front_different_pixels': int((t['front'] != b['front']).sum()),
                              'weaker_different_pixels': int((t['weaker'] != b['weaker']).sum()),
                              'bad_different_pixels': int((t['bad'] != b['bad']).sum()),
                              'after_different_pixels': int((t['after'] != b['after']).sum())})
    np.savez_compressed(HERE / 'all_12_pair_bad_masks.npz', **masks)
    with (HERE / 'all_pair_comparison.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(pair_rows[0])); writer.writeheader(); writer.writerows(pair_rows)
    details, pixels = [], []
    for i, y, x in np.argwhere(mismatch):
        i, y, x = int(i), int(y), int(x)
        row = {'frame': i, 'row': y, 'column': x, 'saved_conf': float(a['conf'][i, y, x]),
               'old_numpy_conf': float(old_output[i, y, x]), 'revised_conf': float(new_output[i, y, x])}
        row.update({name: float(value[i, y, x]) for name, value in outputs.items()})
        pixels.append(row)
        for b, t in zip(baseline_trace, old_trace):
            if b['source'] != i:
                continue
            detail = {'frame': i, 'row': y, 'column': x, 'target': b['target']}
            for label, trace in [('source_contract', b), ('old_numpy', t)]:
                detail[label] = {k: trace[k][y, x].tolist() for k in
                                 ('xy', 'z', 'uv', 'valid', 'front', 'weaker', 'bad', 'depth_margin',
                                  'confidence_margin', 'before', 'after')}
            details.append(detail)
    with (HERE / 'all_mismatch_pixels.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(pixels[0])); writer.writeheader(); writer.writerows(pixels)
    write(HERE / 'all_mismatch_pair_traces.json', details)
    trace = [json.loads(line) for line in (DATA / 'optimization_trace.jsonl').read_text().splitlines()]
    assert len(trace) == 400 and [r['iteration'] for r in trace] == list(range(400))
    assert all(math.isfinite(r['loss_before_step']) and math.isfinite(r['lr']) for r in trace)
    lr_error = max(abs(row['lr'] - (.01 + (1e-6 - .01) * i/400)) for i, row in enumerate(trace))
    assert lr_error < 1e-15
    inverse_report = {name: {'max_abs_difference_from_torch': float(np.abs(value - inverses['torch_batched']).max()),
                            'unequal_elements_from_torch': int((value != inverses['torch_batched']).sum()),
                            'values': value.tolist()} for name, value in inverses.items()}
    for p, h in seal['identities'].items():
        assert sha(p) == h, p
    record = {'status': 'PASS_SAVED_OUTPUT_DIAGNOSIS', 'started_utc': started,
              'completed_utc': datetime.now(timezone.utc).isoformat(), 'wall_seconds': time.monotonic()-start,
              'torch_threads': torch.get_num_threads(), 'numpy_version': np.__version__, 'torch_version': torch.__version__,
              'original_run_status_preserved': 'FAILED', 'sensor_GT_bytes_read': 0, 'model_runs': 0, 'GA_runs': 0,
              'source_clean_only_replays': 1, 'revised_reference_only_replays': 1, 'projection_variants': len(variants),
              'all_cross_view_pairs_per_variant': 12, 'pixels_per_pair': 384*512,
              'all_saved_mismatch_diagnostics_reproduced': True, 'old_numpy_final_mismatch_pixels': int(mismatch.sum()),
              'old_numpy_mismatch_pixels_by_frame': mismatch.reshape(4, -1).sum(axis=1).tolist(),
              'original_source_replay_mismatch_pixels': int((source_output != a['conf']).sum()),
              'revised_reference_mismatch_pixels': int((new_output != a['conf']).sum()),
              'variant_results': summaries, 'inverse_comparison': inverse_report,
              'trace': {'rows': 400, 'indices_exact_0_to_399': True, 'finite_loss_and_lr': True,
                        'linear_schedule_max_abs_error': lr_error, 'first_utc': trace[0]['utc'], 'last_utc': trace[-1]['utc'],
                        'actual_adam_step_evidence': 'Frozen runner passed explicit observer.steps==observer.adam_steps==400 before reaching the recorded clean-reference exception; trace alone is not an Adam-step counter.'},
              'input_identities_before_after': seal['identities'], 'inputs_unchanged': True,
              'new_control_identities': {str(p):sha(p) for p in (Path(__file__), HERE/'clean_reference_torch_fp32.py', HERE/'pre_read_seal.json')},
              'outputs': {p.name:sha(p) for p in HERE.iterdir() if p.suffix in ('.csv','.npz') or p.name=='all_mismatch_pair_traces.json'},
              'claim_limit': 'This post-failure saved-output diagnostic does not retrospectively pass S26 or prove method benefit. Shared numerical primitives are disclosed; no tolerances were relaxed.'}
    write(HERE / 'diagnostic_receipt.json', record)
    print(json.dumps({k:record[k] for k in ('status','wall_seconds','old_numpy_final_mismatch_pixels',
          'original_source_replay_mismatch_pixels','revised_reference_mismatch_pixels','variant_results','trace')}, indent=2))


if __name__ == '__main__':
    main()
