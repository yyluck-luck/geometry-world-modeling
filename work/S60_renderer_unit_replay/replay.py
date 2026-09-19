"""Two post-failure numeric-only replays of three unchanged VMem methods."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import ast
import hashlib
import json
import math
import time
import numpy as np
import torch

R = Path(__file__).resolve().parents[2]
D = Path(__file__).resolve().parent
A = R / 'results/S47B_C2_confirmation_generation_v9/archive'
P = R / 'work/S20_environment/isolated_vmem_source/modeling/pipeline.py'
SOURCE_SHA = '680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255'
EVENTS_SHA = 'b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7'
READS = {}

def digest(b):
    return hashlib.sha256(b).hexdigest()

def decode(node):
    kind = node['kind']
    if kind == 'scalar':
        return node['value']
    if kind == 'dict':
        return {decode(x['key']): decode(x['value']) for x in node['items']}
    if kind in ('list', 'tuple'):
        values = [decode(x) for x in node['items']]
        return tuple(values) if kind == 'tuple' else values
    if kind != 'tensor':
        raise ValueError('Only the specified numeric trees are permitted: ' + kind)
    p = (A / node['blob']).resolve()
    assert p.parent == (A / 'tensors').resolve() and p.suffix == '.bin'
    assert node['dtype'] in ('float32', 'float64', 'int32', 'int64')
    b = p.read_bytes()
    assert len(b) == node['nbytes'] and digest(b) == node['bytes_sha256']
    READS[str(p.relative_to(R))] = {'sha256': digest(b), 'bytes': len(b)}
    dt = np.dtype(node['dtype']).newbyteorder('<')
    return np.frombuffer(b, dtype=dt).reshape(node['shape']).copy()

def project(surfels, pose, focals, pp):
    xyz = np.asarray([s.position for s in surfels], dtype=np.float64)
    local = np.linalg.solve(pose[:3, :3], (xyz - pose[:3, 3]).T).T
    uv = local[:, :2] / local[:, 2:3]
    uv = uv * np.asarray(focals).reshape(2) + np.asarray(pp)
    return local, uv

def main():
    out = D / 'execution_01'
    out.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    clock = time.monotonic()
    src = P.read_bytes()
    assert digest(src) == SOURCE_SHA
    event_bytes = (A / 'events.jsonl').read_bytes()
    assert digest(event_bytes) == EVENTS_SHA
    events = [json.loads(x) for x in event_bytes.splitlines() if x]
    by_seq = {x['seq']: x for x in events}
    for seq, name in [(58, 'render_input'), (60, 'render_output'), (62, 'retrieval_output')]:
        assert by_seq[seq]['payload']['name'] == name
    data = decode(by_seq[58]['payload']['tree'])
    old_render = decode(by_seq[60]['payload']['tree'])['result']
    old_retrieval = decode(by_seq[62]['payload']['tree'])['result']
    assert data['metadata']['operation_name'] == 'turn_right'
    surfels = [SimpleNamespace(**s) for s in data['map']['surfels']]
    assert len(surfels) == 515
    pose, focal = data['args_after_surfels']
    kwargs = data['kwargs']
    assert kwargs['image_width'] == 512 and kwargs['image_height'] == 288
    names = ('render_surfels_to_image', 'get_frame_distribution', 'process_retrieved_spatial_information')
    tree = ast.parse(src)
    selected = [x for cls in tree.body if isinstance(cls, ast.ClassDef)
                for x in cls.body if isinstance(x, ast.FunctionDef) and x.name in names]
    assert len(selected) == 3 and all(not f.decorator_list for f in selected)
    # Compile only these existing numeric methods. Never import the pipeline or instantiate models.
    ns = {'np': np, 'torch': torch, 'math': math}
    method_tree = ast.Module(body=selected, type_ignores=[])
    exec(compile(method_tree, str(P) + '[numeric-only]', 'exec'), ns)
    kernel = type('OriginalNumericMethods', (), {n: ns[n] for n in names})()
    kernel.config = SimpleNamespace(model=SimpleNamespace(context_num_frames=4))
    kernel.surfel_to_timestep = data['map']['surfel_to_timestep']
    local, uv = project(surfels, pose, focal, kwargs['principal_points'])
    positive = local[:, 2][np.isfinite(local[:, 2]) & (local[:, 2] > 0)]
    assert len(positive) == len(surfels)
    # Predetermined dimensionless convention: median positive camera depth equals one.
    unit_scale = 1.0 / float(np.median(positive))
    conditions = []
    for label, scale in [('recorded_units', 1.0), ('median_depth_unit', unit_scale)]:
        ss = [SimpleNamespace(position=s.position.astype(np.float64) * scale,
                              normal=s.normal.copy(), radius=float(s.radius) * scale)
              for s in surfels] if label != 'recorded_units' else surfels
        cam = pose.copy()
        cam[:3, 3] *= scale
        transformed_local, transformed_uv = project(ss, cam, focal, kwargs['principal_points'])
        np.testing.assert_allclose(transformed_uv, uv, rtol=1e-12, atol=1e-9)
        begin = time.monotonic()
        result = kernel.render_surfels_to_image(ss, cam, focal, **kwargs)
        retrieval = kernel.process_retrieved_spatial_information(result)
        seconds = time.monotonic() - begin
        if label == 'recorded_units':
            for key in old_render:
                assert np.array_equal(result[key], old_render[key]), key
            assert retrieval == old_retrieval
        assert all(np.isfinite(v).all() for v in result.values())
        np.savez_compressed(out / (label + '_numeric_maps.npz'), **result)
        conditions.append({'condition': label, 'length_scale': scale,
                           'elapsed_seconds': seconds,
                           'camera_z_min': float(transformed_local[:, 2].min()),
                           'camera_z_max': float(transformed_local[:, 2].max()),
                           'max_projection_difference_px': float(np.max(np.abs(transformed_uv - uv))),
                           'occupied_index_pixels': int((result['surfel_index_map'] >= 0).sum()),
                           'distinct_rasterized_surfels': int(len(np.unique(result['surfel_index_map'][result['surfel_index_map'] >= 0]))),
                           'timestep_weights': retrieval[0], 'frame_count': retrieval[1],
                           'original_numeric_arrays_exact_match': label == 'recorded_units'})
    receipt = {'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
               'elapsed_seconds': time.monotonic() - clock, 'source_sha256': SOURCE_SHA,
               'script_sha256': digest(Path(__file__).read_bytes()), 'archive_events_sha256': EVENTS_SHA,
               'compiled_unchanged_functions': list(names), 'read_numeric_blobs': READS,
               'conditions': conditions, 'new_model_calls': 0, 'rgb_image_reads': 0,
               'second_generation_batch_run': False, 'c2_complete': False,
               'post_exposure_diagnostic': True, 'new_method_validated': False,
               'interpretation_limit': 'Changes to numeric length units preserve geometric projection but fixed dimensional constants remain unchanged. This tests unit dependence, not physical calibration, an implemented production repair, original-baseline completion or video-quality gain.'}
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    for p in out.iterdir():
        p.chmod(0o444)
    print(json.dumps({'status': 'NUMERIC_ONLY_REPLAY_COMPLETED', 'conditions': conditions,
                      'elapsed_seconds': receipt['elapsed_seconds']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
