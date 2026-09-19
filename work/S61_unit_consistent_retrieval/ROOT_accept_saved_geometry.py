"""Finite acceptance of a reviewed new adapter on previously exposed C2 geometry."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
import argparse
import ast
import hashlib
import importlib.util
import json
import math
import sys
import time
import numpy as np
import torch

D = Path(__file__).resolve().parent
R = D.parents[1]
A = R / 'results/S47B_C2_confirmation_generation_v9/archive'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_source(name, path, expected):
    assert sha(path) == expected
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def field(node, key):
    assert node['kind'] == 'dict'
    found = [v['value'] for v in node['items'] if v['key']['value'] == key]
    assert len(found) == 1
    return found[0]

def input_identity(surfels, cam, focal, kwargs):
    h = hashlib.sha256()
    for value in [cam, *focal, *[x for s in surfels for x in (s.position, s.normal, s.radius)]]:
        a = np.asarray(value)
        h.update(str(a.shape).encode())
        h.update(a.dtype.str.encode())
        h.update(a.tobytes())
    h.update(json.dumps(kwargs, sort_keys=True).encode())
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--adapter', required=True)
    ap.add_argument('--sha256', required=True)
    args = ap.parse_args()
    adapter_path = Path(args.adapter).resolve()
    assert adapter_path.parent == D.resolve()
    out = D / 'execution_01'
    out.mkdir(exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    adapter = load_source('s61_accepted_adapter', adapter_path, args.sha256)
    old = load_source('s60_numeric_decoder', R/'work/S60_renderer_unit_replay/replay.py',
                      '4f58467755346fe126cf5a351b25d66359c143e6e7bae9188245a44b08175dfb')
    assert sha(A/'events.jsonl') == old.EVENTS_SHA
    events = [json.loads(x) for x in (A/'events.jsonl').read_text().splitlines()]
    event = next(x for x in events if x['seq'] == 58)
    assert event['payload']['name'] == 'render_input'
    tree = event['payload']['tree']
    mapped = field(tree, 'map')
    # Select only the permitted geometry, leaving depth maps and image branches undecoded.
    stored = old.decode(field(mapped, 'surfels'))
    ids = old.decode(field(mapped, 'surfel_to_timestep'))
    pose, focal = old.decode(field(tree, 'args_after_surfels'))
    kwargs = old.decode(field(tree, 'kwargs'))
    assert len(stored) == 515
    src = old.P.read_bytes()
    assert hashlib.sha256(src).hexdigest() == old.SOURCE_SHA
    names = ('render_surfels_to_image', 'get_frame_distribution', 'process_retrieved_spatial_information')
    selected = [f for c in ast.parse(src).body if isinstance(c, ast.ClassDef)
                for f in c.body if isinstance(f, ast.FunctionDef) and f.name in names]
    assert len(selected) == 3 and all(not f.decorator_list for f in selected)
    namespace = {'np': np, 'torch': torch, 'math': math}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(old.P)+'[numeric-only]', 'exec'), namespace)
    kernel = type('PinnedOriginalNumericMethods', (), {n: namespace[n] for n in names})()
    kernel.config = SimpleNamespace(model=SimpleNamespace(context_num_frames=4))
    kernel.surfel_to_timestep = ids
    golden_npz = R/'work/S60_renderer_unit_replay/execution_01/median_depth_unit_numeric_maps.npz'
    golden_receipt = R/'work/S60_renderer_unit_replay/execution_01/receipt.json'
    assert sha(golden_npz) == '1b2fefa8c44eeca818f4aab979b95b176fee4875df1e6c3538615477b8b23bfe'
    assert sha(golden_receipt) == '8c5353945322be90093db0bbbcb2992e898a7dbc91e5e8e009d16b92c269b9f0'
    with np.load(golden_npz, allow_pickle=False) as z:
        golden = {k: z[k].copy() for k in z.files}
    expected_retrieval = json.loads(golden_receipt.read_text())['conditions'][1]
    conditions = []
    for label, factor in [('recorded_length_unit', 1.0), ('small_length_unit', 1e-6), ('large_length_unit', 1e6)]:
        ss = [SimpleNamespace(position=s['position'].astype(np.float64)*factor,
                              radius=float(s['radius'])*factor, normal=s['normal'].copy(),
                              source_ids=list(s['source_ids'])) for s in stored]
        cam = pose.copy()
        cam[:3, 3] *= factor
        before = input_identity(ss, cam, focal, kwargs)
        calls = []
        def original_renderer_once(new_surfels, new_cam, new_focal, **new_kwargs):
            points = np.asarray([s.position for s in new_surfels])
            local = (np.linalg.inv(new_cam[:3, :3]) @ (points-new_cam[:3, 3]).T).T
            median = float(np.median(local[local[:, 2] > 0, 2]))
            np.testing.assert_allclose(median, 1.0, rtol=1e-12, atol=1e-12)
            assert new_kwargs == kwargs
            np.testing.assert_array_equal(np.asarray(new_focal), np.asarray(focal))
            calls.append({'positive_camera_depth_median': median, 'surfels': len(new_surfels)})
            return kernel.render_surfels_to_image(new_surfels, new_cam, new_focal, **new_kwargs)
        clock = time.monotonic()
        maps, receipt = adapter.render_in_canonical_units(original_renderer_once, ss, cam, focal, **kwargs)
        assert len(calls) == 1
        assert input_identity(ss, cam, focal, kwargs) == before
        assert set(maps) == set(golden)
        errors = {}
        for key in golden:
            assert maps[key].shape == (288, 512) and np.isfinite(maps[key]).all()
            if key == 'surfel_index_map':
                np.testing.assert_array_equal(maps[key], golden[key])
            else:
                np.testing.assert_allclose(maps[key], golden[key], atol=1e-6, rtol=1e-6)
            errors[key] = float(np.max(np.abs(maps[key].astype(float)-golden[key].astype(float))))
        weights, count = kernel.process_retrieved_spatial_information(maps)
        assert [list(x) for x in count] == expected_retrieval['frame_count']
        np.testing.assert_allclose(weights, expected_retrieval['timestep_weights'], atol=1e-6, rtol=0)
        np.savez_compressed(out/(label+'.npz'), **maps)
        conditions.append({'name': label, 'input_length_factor': factor, 'renderer_calls': calls,
                           'inputs_unchanged': True, 'elapsed_seconds': time.monotonic()-clock,
                           'maps_max_abs_difference': errors, 'occupied_index_pixels': int((maps['surfel_index_map']>=0).sum()),
                           'frame_count': count, 'weights': weights, 'adapter_receipt': receipt})
    result = {'status': 'PASS_SAVED_GEOMETRY_COMPONENT_ACCEPTANCE', 'started_utc': started,
              'ended_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.monotonic()-begin,
              'source_sha256': sha(__file__), 'adapter_path': str(adapter_path), 'adapter_sha256': args.sha256,
              'conditions': conditions, 'numeric_blob_reads': old.READS,
              'new_model_calls': 0, 'rgb_reads': 0, 'independent_scenes': 1,
              'full_pipeline_installed': False, 'new_c2_generation': False, 'new_method_validated': False}
    (out/'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    for p in out.iterdir():
        p.chmod(0o444)
    print(json.dumps({k:v for k,v in result.items() if k!='numeric_blob_reads'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
