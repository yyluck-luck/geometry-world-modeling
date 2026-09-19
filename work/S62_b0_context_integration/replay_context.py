"""One saved B0 context call, original renderer then S61; no model or RGB."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import ast
import hashlib
import json
import math
import struct
import sys
import time
import traceback

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHIVE = ROOT / 'results/S40_declared_variant_generation/archive'
PIPELINE = 'work/S20_environment/isolated_vmem_source/modeling/pipeline.py'
UTIL = 'work/S20_environment/isolated_vmem_source/utils/util.py'
ADAPTER = 'work/S61_unit_consistent_retrieval/unit_consistent_renderer.py'
PINS = {
    PIPELINE: '680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255',
    UTIL: '30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e',
    ADAPTER: 'a90410b517b20bfa137cdd00a0bbc3b73c1489ebb8a8d0ab672cb06e6387de6c',
    'work/S61_unit_consistent_retrieval/AUTHOR_FINAL_DELIVERY.json': '111715a4d98dfaf9ed48e75a2a4073b68f47c129c7f408102c612d1bbafe4a07',
    'work/S20_environment/isolated_vmem_source/configs/inference/inference.yaml': '8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3',
    'work/S35_generation_integration/runtime_factory.py': 'a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0',
    'work/S35_generation_integration/integrate_original.py': 'adf819e1cda3de4f830d2c3e5776664591607a0109d50f59cdc1addeb684b0ec',
    'work/S40_declared_variant_generation/review_attachment_01/manifest.json': '9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe',
    'results/S40_declared_variant_generation/archive/events.jsonl': 'bca5c9148a81ba6a070cb4d10c67db384bf1d96f06a0233f746b117a3228a7b1',
    'results/S40_declared_variant_generation/archive/manifest.json': '4e2acb3448589710aedcf6945d2d278bfa1b6d194b94adaad0d9b371697e153b',
}
METHODS = ('render_surfels_to_image', 'get_frame_distribution',
           'process_retrieved_spatial_information', 'geodesic_distance',
           'get_transformed_c2ws', 'get_context_info')
CACHE_OUTPUTS = {'context_c2ws': 'c2ws', 'context_latents': 'latents',
                 'context_encoder_embeddings': 'encoder_embeddings', 'context_Ks': 'Ks'}
EXPECTED_IDS = [0, 2, 4, 1]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def field(node, name):
    require(node['kind'] == 'dict', 'Expected encoded dictionary')
    values = [x['value'] for x in node['items'] if x['key'].get('value') == name]
    require(len(values) == 1, 'Missing/duplicate field: ' + str(name))
    return values[0]


class Decoder:
    """Decode only the explicit numeric subtrees selected by load_inputs."""
    def __init__(self, readlog):
        self.readlog, self.raw, self.reads = readlog, {}, []

    def decode(self, node, label):
        kind = node['kind']
        if kind == 'scalar':
            return node['value']
        if kind == 'python_float64':
            return struct.unpack('<d', bytes.fromhex(node['little_endian_hex']))[0]
        if kind in ('list', 'tuple'):
            values = [self.decode(x, f'{label}[{i}]') for i, x in enumerate(node['items'])]
            return tuple(values) if kind == 'tuple' else values
        if kind == 'dict':
            result = {}
            for x in node['items']:
                key = self.decode(x['key'], label + '.key')
                require(key not in ('surfel_depths', 'pil_frames', 'color'), 'Excluded branch')
                result[key] = self.decode(x['value'], f'{label}.{key}')
            return result
        require(kind == 'tensor', 'Not an allowed numeric descriptor: ' + kind)
        require(node['dtype'] in ('float32', 'float64', 'int32', 'int64'), 'Unexpected dtype')
        require(node['byteorder'] == 'little' and node['order'] == 'C', 'Unexpected byte layout')
        require(node['blob'] == 'tensors/' + node['sha256'] + '.bin', 'Descriptor path mismatch')
        dtype = np.dtype(node['dtype']).newbyteorder('<')
        require(math.prod(node['shape']) * dtype.itemsize == node['nbytes'], 'Descriptor size mismatch')
        blob = node['blob']
        if blob not in self.raw:
            raw = (ARCHIVE / blob).read_bytes()
            read = dict(blob=blob, first_use=label, nbytes=len(raw), dtype=node['dtype'],
                        shape=node['shape'], expected_bytes_sha256=node['bytes_sha256'],
                        actual_bytes_sha256=sha(raw))
            read['verified'] = len(raw) == node['nbytes'] and sha(raw) == node['bytes_sha256']
            self.reads.append(read)
            self.readlog.write(json.dumps(read, ensure_ascii=False) + '\n')
            self.readlog.flush()
            require(read['verified'], 'Numeric blob SHA/size mismatch: ' + blob)
            self.raw[blob] = raw
        raw = self.raw[blob]
        require(sha(raw) == node['bytes_sha256'] and len(raw) == node['nbytes'], 'Reused blob mismatch')
        array = np.frombuffer(raw, dtype=dtype).reshape(node['shape']).copy()
        require(np.isfinite(array).all(), 'Nonfinite saved numeric input: ' + label)
        return array


def load_inputs(decoder):
    events = [json.loads(line) for line in (ARCHIVE / 'events.jsonl').read_text().splitlines()]
    names = {56: 'context_input', 58: 'render_input', 60: 'render_output',
             62: 'retrieval_output', 64: 'nms_threshold', 66: 'nms_selection',
             68: 'context_output', 70: 'batch_input'}
    trees = {}
    for seq, name in names.items():
        found = [e for e in events if e['seq'] == seq]
        require(len(found) == 1 and found[0]['payload']['name'] == name, 'Wrong capture')
        trees[seq] = found[0]['payload']['tree']
    d = decoder.decode
    mapped = field(trees[58], 'map')
    stored = field(mapped, 'surfels')
    require(stored['kind'] == 'list' and len(stored['items']) == 567, 'Expected 567 B0 surfels')
    surfels = [SimpleNamespace(**{key: d(field(s, key), f'seq58.surfels[{i}].{key}')
               for key in ('position', 'normal', 'radius', 'source_ids')})
               for i, s in enumerate(stored['items'])]
    cache_tree = field(trees[68], 'cache')
    require(len(field(cache_tree, 'pil_frames')['items']) == 5, 'Expected five history entries')
    cache = {key: d(field(cache_tree, key), 'seq68.cache.' + key)
             for key in ('c2ws', 'Ks', 'latents', 'encoder_embeddings', 'surfel_Ks')}
    require(all(len(values) == 5 for values in cache.values()), 'Cache history lengths differ')
    target = d(field(trees[56], 'args')['items'][0], 'seq56.target_c2ws')
    require(target.shape == (4, 4, 4) and target.dtype == np.float32, 'Wrong target poses')
    require(field(trees[68], 'context_info') == field(trees[70], 'context_info'), 'Context capture disagreement')
    expected = {
        'render_args': d(field(trees[58], 'args_after_surfels'), 'seq58.render_args'),
        'render_kwargs': d(field(trees[58], 'kwargs'), 'seq58.render_kwargs'),
        'maps': d(field(trees[60], 'result'), 'seq60.maps'),
        'retrieval': d(field(trees[62], 'result'), 'seq62.retrieval'),
        'context': d(field(trees[68], 'context_info'), 'seq68.context_info'),
        'nms': d(trees[66], 'seq66.nms'),
        'threshold': d(field(trees[64], 'initial_threshold'), 'seq64.initial_threshold'),
    }
    require(expected['nms']['selected_indices'] == EXPECTED_IDS, 'Wrong original IDs')
    require(expected['nms']['use_non_maximum_suppression'] is True, 'Wrong original NMS mode')
    # Read render-time focal cache rather than substituting a saved already-scaled focal.
    render_focals = d(field(mapped, 'surfel_Ks'), 'seq58.surfel_Ks')
    require(fingerprint(render_focals) == fingerprint(cache['surfel_Ks']), 'Focal caches changed')
    inputs = dict(cache=cache, surfels=surfels, target=target, surfel_Ks=render_focals,
                  surfel_to_timestep=d(field(mapped, 'surfel_to_timestep'), 'seq58.surfel_to_timestep'))
    return inputs, expected


def fingerprint(value):
    h = hashlib.sha256()
    def visit(x):
        if isinstance(x, np.ndarray):
            h.update(repr((x.dtype.str, x.shape)).encode()); h.update(x.tobytes())
        elif isinstance(x, SimpleNamespace):
            visit(vars(x))
        elif isinstance(x, dict):
            h.update(b'dict')
            for key, item in x.items():
                visit(key); visit(item)
        elif isinstance(x, (list, tuple)):
            h.update(type(x).__name__.encode())
            for item in x:
                visit(item)
        else:
            h.update(repr((type(x).__name__, x)).encode())
    visit(value)
    return h.hexdigest()


def original_numeric_class(sources):
    source_tree = ast.parse(sources[PIPELINE])
    methods = [f for c in source_tree.body if isinstance(c, ast.ClassDef)
               for f in c.body if isinstance(f, ast.FunctionDef) and f.name in METHODS]
    require(len(methods) == len(METHODS) and all(not f.decorator_list for f in methods), 'AST methods differ')
    average = [f for f in ast.parse(sources[UTIL]).body
               if isinstance(f, ast.FunctionDef) and f.name == 'average_camera_pose']
    require(len(average) == 1 and not average[0].decorator_list, 'AST average missing')
    namespace = dict(np=np, torch=torch, math=math, deepcopy=deepcopy)
    exec(compile(ast.Module(body=average, type_ignores=[]), UTIL + '[one-function]', 'exec'), namespace)
    exec(compile(ast.Module(body=methods, type_ignores=[]), PIPELINE + '[six-methods]', 'exec'), namespace)
    return type('OriginalNumericContext', (), {name: namespace[name] for name in METHODS})


def exact(actual, expected):
    require(actual.shape == expected.shape and actual.dtype == expected.dtype, 'Shape/dtype mismatch')
    np.testing.assert_array_equal(actual, expected)


def run_arm(label, cls, inputs, golden, out, result, adapter=None):
    before = fingerprint(inputs)
    scratch = deepcopy(inputs)
    scratch_before = fingerprint(scratch)
    kernel = cls()
    kernel.device, kernel.dtype = torch.device('cpu'), torch.float32
    kernel.config = SimpleNamespace(model=SimpleNamespace(context_num_frames=4, translation_distance_weight=0.1),
                                    surfel=SimpleNamespace(width=512, height=288),
                                    inference=SimpleNamespace(visualize=False))
    kernel.use_non_maximum_suppression = True
    kernel.pil_frames = [None] * 5  # Only len() is consumed; never load image bodies.
    for key, value in scratch['cache'].items():
        setattr(kernel, key, value)
    for key in ('surfels', 'surfel_to_timestep', 'surfel_Ks'):
        setattr(kernel, key, scratch[key])
    observed = {}
    result.update(name=label, status='RUNNING', renderer_calls=0, retrieval_calls=0)

    def original_renderer(surfels, pose, focal, **kwargs):
        result['renderer_calls'] += 1
        require(result['renderer_calls'] == 1, 'More than one renderer call')
        return cls.render_surfels_to_image(kernel, surfels, pose, focal, **kwargs)

    def render(surfels, pose, focal, **kwargs):
        # The same unmodified context function must construct the archived camera input.
        exact(pose, golden['render_args'][0])
        for actual, expected in zip(focal, golden['render_args'][1], strict=True):
            exact(np.asarray(actual), expected)
        require(kwargs == golden['render_kwargs'], 'Original rendering settings differ')
        if adapter is None:
            maps = original_renderer(surfels, pose, focal, **kwargs)
        else:
            maps, result['unit_receipt'] = adapter(original_renderer, surfels, pose, focal, **kwargs)
        observed['maps'] = maps
        with (out / (label + '_maps.npz')).open('xb') as handle:
            np.savez_compressed(handle, **maps)
        return maps

    def retrieve(maps):
        result['retrieval_calls'] += 1
        require(result['retrieval_calls'] == 1, 'More than one retrieval call')
        weights, counts = cls.process_retrieved_spatial_information(kernel, maps)
        result['weights'] = [[int(i), float(w)] for i, w in weights]
        result['frame_count'] = [[int(i), int(n)] for i, n in counts]
        return weights, counts

    kernel.render_surfels_to_image = render
    kernel.process_retrieved_spatial_information = retrieve
    try:
        context = kernel.get_context_info(torch.from_numpy(scratch['target']))
        context = {key: value.detach().cpu().numpy() for key, value in context.items()}
        with (out / (label + '_context.npz')).open('xb') as handle:
            np.savez_compressed(handle, **context)
        ids = context['context_time_indices']
        result['selected_ids'] = ids.tolist()
        require(ids.dtype == np.int64 and ids.shape == (4,) and ((ids >= 0) & (ids < 5)).all(), 'Invalid context IDs/count')
        require(result['renderer_calls'] == result['retrieval_calls'] == 1, 'Expected one call per stage')
        result['cache_slots_exact'] = {}
        for output_key, cache_key in CACHE_OUTPUTS.items():
            reference = np.stack([inputs['cache'][cache_key][int(i)] for i in ids]).astype(np.float32)
            exact(context[output_key], reference)
            result['cache_slots_exact'][output_key] = True
        result['initial_threshold'] = float(kernel.initial_threshold)
        require(result['initial_threshold'] == golden['threshold'], 'Original NMS initial threshold differs')
        if adapter is None:
            require(ids.tolist() == EXPECTED_IDS, 'Original context ID order mismatch')
            result['maps_max_absolute_difference'] = {}
            require(set(observed['maps']) == set(golden['maps']), 'Map keys differ')
            for key, reference in golden['maps'].items():
                actual = observed['maps'][key]
                require(actual.shape == reference.shape and actual.dtype == reference.dtype, 'Map layout differs')
                if key == 'surfel_index_map':
                    exact(actual, reference)
                else:
                    np.testing.assert_allclose(actual, reference, rtol=1e-6, atol=1e-6)
                result['maps_max_absolute_difference'][key] = float(np.max(np.abs(actual.astype(float)-reference.astype(float))))
            np.testing.assert_allclose(result['weights'], golden['retrieval'][0], rtol=0, atol=1e-6)
            require(result['frame_count'] == [list(x) for x in golden['retrieval'][1]], 'Original quota differs')
            require(set(context) == set(golden['context']), 'Context keys differ')
            for key, reference in golden['context'].items():
                exact(context[key], reference)
            result['archived_context_exact'] = True
        result['occupied_index_pixels'] = int((observed['maps']['surfel_index_map'] >= 0).sum())
        result['status'] = 'PASS'
    finally:
        result['original_inputs_sha256_before'] = before
        result['original_inputs_sha256_after'] = fingerprint(inputs)
        result['scratch_inputs_sha256_before'] = scratch_before
        result['scratch_inputs_sha256_after'] = fingerprint(scratch)
        require(result['original_inputs_sha256_after'] == before and
                result['scratch_inputs_sha256_after'] == scratch_before, 'Input/cache mutation')


def main():
    out = HERE / 'execution_01'
    out.mkdir(exist_ok=False)
    started, begin = datetime.now(timezone.utc).isoformat(), time.monotonic()
    result = dict(status='RUNNING', started_utc=started, source_sha256=sha(Path(__file__).read_bytes()),
                  pinned_sources=PINS, conditions=[], new_model_calls=0, RGB_reads=0,
                  surfel_depth_payload_reads=0, new_c2_generation=False, new_method_validated=False,
                  scope='One saved B0 second action; stops at get_context_info return')
    decoder = None
    exit_code = 1
    try:
        require(sys.byteorder == 'little', 'Expected little-endian runtime')
        require(torch.__version__.split('+')[0] == '2.7.0' and np.__version__ == '1.26.4', 'Frozen numeric base required')
        torch.set_num_threads(8)
        result['runtime'] = dict(python=sys.version, numpy=np.__version__, torch=torch.__version__, threads=torch.get_num_threads())
        sources = {path: (ROOT / path).read_bytes() for path in PINS}
        for path, data in sources.items():
            require(sha(data) == PINS[path], 'Source/archive identity mismatch: ' + path)
        with (out / 'readlist.jsonl').open('x') as readlog:
            decoder = Decoder(readlog)
            inputs, golden = load_inputs(decoder)
        cls = original_numeric_class(sources)
        original_result = {}
        result['conditions'].append(original_result)
        run_arm('original', cls, inputs, golden, out, original_result)
        # No adapter path starts if the original archive regression failed.
        adapter_namespace = {'__name__': 's62_pinned_s61_adapter'}
        exec(compile(sources[ADAPTER], ADAPTER, 'exec'), adapter_namespace)
        adapted_result = {}
        result['conditions'].append(adapted_result)
        run_arm('canonical_units', cls, inputs, golden, out, adapted_result,
                adapter_namespace['render_in_canonical_units'])
        result['status'], exit_code = 'PASS_B0_SAVED_CONTEXT_INTEGRATION', 0
    except Exception:
        result['status'] = 'FAIL_B0_SAVED_CONTEXT_INTEGRATION'
        result['error'] = traceback.format_exc()
        if result['conditions']:
            result['conditions'][-1]['status'] = 'FAIL'
    finally:
        result.update(ended_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-begin)
        result['numeric_unique_blob_count'] = len(decoder.reads) if decoder else 0
        result['numeric_unique_bytes_read'] = sum(x['nbytes'] for x in decoder.reads) if decoder else 0
        result['artifacts_sha256'] = {p.name: sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
        with (out / 'receipt.json').open('x') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n')
        for path in out.iterdir():
            if path.is_file():
                path.chmod(0o444)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
