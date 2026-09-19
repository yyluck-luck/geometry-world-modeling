"""One failed C2 context call: exact original failure, then S61 real-cache return."""
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
ARCHIVE = ROOT / 'results/S47B_C2_confirmation_generation_v9/archive'
PIPELINE = 'work/S20_environment/isolated_vmem_source/modeling/pipeline.py'
UTIL = 'work/S20_environment/isolated_vmem_source/utils/util.py'
ADAPTER = 'work/S61_unit_consistent_retrieval/unit_consistent_renderer.py'
PINS = {
    'work/S62_b0_context_integration/replay_context.py': 'aced1cd73277433ab5573d2a01d91392c1c0d2d7b5c86881c1c6dc1102fcf876',
    PIPELINE: '680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255',
    UTIL: '30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e',
    ADAPTER: 'a90410b517b20bfa137cdd00a0bbc3b73c1489ebb8a8d0ab672cb06e6387de6c',
    'work/S61_unit_consistent_retrieval/AUTHOR_FINAL_DELIVERY.json': '111715a4d98dfaf9ed48e75a2a4073b68f47c129c7f408102c612d1bbafe4a07',
    'work/S20_environment/isolated_vmem_source/configs/inference/inference.yaml': '8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3',
    'work/S35_generation_integration/runtime_factory.py': 'a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0',
    'work/S35_generation_integration/integrate_original.py': 'adf819e1cda3de4f830d2c3e5776664591607a0109d50f59cdc1addeb684b0ec',
    'work/S47B_c2_confirmation_generation_v9/review_attachment_01/manifest.json': 'caa6d7c04d7784e731165e05c07ff4e358322d14c8e76f08c2337b7f4dc641ac',
    'results/S47B_C2_confirmation_generation_v9/archive/events.jsonl': 'b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7',
    'results/S47B_C2_confirmation_generation_v9/archive/manifest.json': '7cfd56b59924fb3c603a3eb54c34f387db8439c72fc4a6fe08e3097dcf659b4c',
}
METHODS = ('render_surfels_to_image', 'get_frame_distribution',
           'process_retrieved_spatial_information', 'geodesic_distance',
           'get_transformed_c2ws', 'get_context_info')
CACHE_OUTPUTS = {'context_c2ws': 'c2ws', 'context_latents': 'latents',
                 'context_encoder_embeddings': 'encoder_embeddings', 'context_Ks': 'Ks'}

# Reference already exposed in S61; not an unseen oracle. Loaded only at runtime.
REFERENCE_MAPS = 'work/S61_unit_consistent_retrieval/execution_01/recorded_length_unit.npz'
REFERENCE_SHA = '1b2fefa8c44eeca818f4aab979b95b176fee4875df1e6c3538615477b8b23bfe'
EXPECTED_ERROR_LINE = 711
EXPECTED_ERROR_STATEMENT = 'selected_indices.append(sorted_frames[0])'


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
    def __init__(self, archive, readlog):
        self.archive = archive
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
            raw = (self.archive / blob).read_bytes()
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


def load_inputs(decoder):
    events = [json.loads(x) for x in (ARCHIVE / 'events.jsonl').read_text().splitlines()]
    names = {50: 'map_commit', 56: 'context_input', 58: 'render_input',
             60: 'render_output', 62: 'retrieval_output', 64: 'nms_threshold'}
    trees = {}
    for seq, name in names.items():
        matches = [e for e in events if e['seq'] == seq]
        require(len(matches) == 1 and matches[0]['payload']['name'] == name, 'Wrong C2 capture')
        trees[seq] = matches[0]['payload']['tree']
    failure = next(e for e in events if e['seq'] == 65)
    require(failure['event'] == 'caller_failure' and failure['payload'] == {
        'exception_type': 'IndexError', 'message': 'list index out of range', 'phase': 'turn_right'},
        'Wrong archived C2 failure metadata')
    d = decoder.decode
    cache_tree = field(trees[50], 'cache')
    require(len(field(cache_tree, 'pil_frames')['items']) == 5, 'Expected five C2 history entries')
    cache = {key: d(field(cache_tree, key), 'seq50.cache.' + key)
             for key in ('c2ws', 'Ks', 'latents', 'encoder_embeddings', 'surfel_Ks')}
    layouts = {'c2ws': (4, 4), 'Ks': (3, 3), 'latents': (4, 72, 72),
               'encoder_embeddings': (1024,), 'surfel_Ks': (1,)}
    for key, values in cache.items():
        require(len(values) == 5, 'Wrong cache history length')
        for i, array in enumerate(values):
            dtype = np.float64 if key == 'c2ws' and i == 0 else np.float32
            require(array.shape == layouts[key] and array.dtype == dtype, 'Wrong saved cache layout')
    target, nms_argument = d(field(trees[56], 'args'), 'seq56.args')
    require(nms_argument is None and d(field(trees[56], 'kwargs'), 'seq56.kwargs') == {}, 'Wrong context arguments')
    require(target.shape == (4, 4, 4) and target.dtype == np.float32, 'Wrong target layout')
    mapped = field(trees[58], 'map')
    require(field(mapped, 'surfel_Ks') == field(cache_tree, 'surfel_Ks'), 'Focal cache descriptors changed')
    stored = field(mapped, 'surfels')
    require(stored['kind'] == 'list' and len(stored['items']) == 515, 'Expected 515 C2 surfels')
    surfels = [SimpleNamespace(**{key: d(field(s, key), f'seq58.surfels[{i}].{key}')
               for key in ('position', 'normal', 'radius', 'source_ids')})
               for i, s in enumerate(stored['items'])]
    for surfel in surfels:
        require(surfel.position.shape == surfel.normal.shape == (3,) and
                surfel.position.dtype == surfel.normal.dtype == np.float32 and
                surfel.radius.shape == () and surfel.radius.dtype == np.float64 and
                surfel.radius >= 0, 'Wrong surfel geometry layout')
    mapping = d(field(mapped, 'surfel_to_timestep'), 'seq58.surfel_to_timestep')
    require(set(mapping) == set(range(515)), 'Incomplete surfel ID mapping')
    require(all(type(i) is int and 0 <= i < 5 for ids in mapping.values() for i in ids), 'Illegal source ID')
    expected = dict(render_args=d(field(trees[58], 'args_after_surfels'), 'seq58.render_args'),
                    render_kwargs=d(field(trees[58], 'kwargs'), 'seq58.render_kwargs'),
                    maps=d(field(trees[60], 'result'), 'seq60.maps'),
                    retrieval=d(field(trees[62], 'result'), 'seq62.retrieval'),
                    nms=d(trees[64], 'seq64.nms'), failure_metadata=failure['payload'])
    require(expected['retrieval'] == ([], []), 'Archived retrieval was not empty')
    require(expected['nms']['is_second_step'] is True and
            expected['nms']['use_non_maximum_suppression'] is True, 'Wrong archived NMS mode')
    require(len(decoder.reads) == 1496 and sum(x['nbytes'] for x in decoder.reads) == 1631256,
            'Actual numeric read scope differs from frozen metadata inventory')
    return dict(cache=cache, surfels=surfels, target=target, surfel_to_timestep=mapping), expected


def check_maps(maps):
    layouts = {'depth': np.float32, 'surfel_index_map': np.int32, 'cos_value_map': np.float32}
    require(set(maps) == set(layouts), 'Wrong map keys')
    for key, dtype in layouts.items():
        require(isinstance(maps[key], np.ndarray) and maps[key].shape == (288, 512) and
                maps[key].dtype == dtype and np.isfinite(maps[key]).all(), 'Invalid map layout/finite: ' + key)
    index, depth, cosine = maps['surfel_index_map'], maps['depth'], maps['cos_value_map']
    require(((index >= -1) & (index < 515)).all(), 'Surfel index outside [-1,514]')
    occupied = index >= 0
    require((depth >= 0).all() and (depth[occupied] > 0).all() and
            (depth[~occupied] == 0).all() and (cosine[~occupied] == 0).all(), 'Invalid foreground/background maps')
    require((np.abs(cosine) <= 1 + 1e-6).all(), 'Cosine outside numerical unit range')
    return dict(occupied_index_pixels=int(occupied.sum()), visible_surfel_count=int(np.unique(index[occupied]).size),
                depth_min=float(depth.min()), depth_max=float(depth.max()),
                cosine_min=float(cosine.min()), cosine_max=float(cosine.max()))


def run_arm(label, cls, inputs, expected, out, result, adapter=None):
    before, scratch = fingerprint(inputs), deepcopy(inputs)
    scratch_before = fingerprint(scratch)
    kernel = cls()
    kernel.device, kernel.dtype = torch.device('cpu'), torch.float32
    kernel.config = SimpleNamespace(model=SimpleNamespace(context_num_frames=4, translation_distance_weight=0.1),
                                    surfel=SimpleNamespace(width=512, height=288),
                                    inference=SimpleNamespace(visualize=False))
    kernel.use_non_maximum_suppression = True
    kernel.pil_frames = [None] * 5  # Original context reads only its length.
    for key, value in scratch['cache'].items():
        setattr(kernel, key, value)
    kernel.surfels, kernel.surfel_to_timestep = scratch['surfels'], scratch['surfel_to_timestep']
    observed = {}
    result.update(name=label, status='RUNNING', renderer_calls=0, retrieval_calls=0)

    def original_renderer(surfels, pose, focal, **kwargs):
        result['renderer_calls'] += 1
        require(result['renderer_calls'] == 1, 'Expected at most one original renderer call')
        return cls.render_surfels_to_image(kernel, surfels, pose, focal, **kwargs)

    def render(surfels, pose, focal, **kwargs):
        exact(pose, expected['render_args'][0])
        for actual, reference in zip(focal, expected['render_args'][1], strict=True):
            exact(np.asarray(actual), reference)
        require(kwargs == expected['render_kwargs'], 'Original query kwargs differ')
        if adapter is None:
            maps = original_renderer(surfels, pose, focal, **kwargs)
        else:
            maps, result['unit_receipt'] = adapter(original_renderer, surfels, pose, focal, **kwargs)
        observed['maps'] = maps
        with (out / (label + '_maps.npz')).open('xb') as handle:
            np.savez_compressed(handle, **maps)
        result['maps'] = check_maps(maps)
        if adapter is None:
            for key, reference in expected['maps'].items():
                exact(maps[key], reference)
            require(result['maps']['occupied_index_pixels'] == 0, 'Original map is not empty')
            result['archived_maps_exact'] = True
        return maps

    def retrieve(maps):
        result['retrieval_calls'] += 1
        require(result['retrieval_calls'] == 1, 'Expected at most one original retrieval call')
        weights, counts = cls.process_retrieved_spatial_information(kernel, maps)
        result['weights'] = [[int(i), float(w)] for i, w in weights]
        result['frame_count'] = [[int(i), int(n)] for i, n in counts]
        if adapter is None:
            require((weights, counts) == expected['retrieval'], 'Original empty retrieval differs')
        return weights, counts

    kernel.render_surfels_to_image, kernel.process_retrieved_spatial_information = render, retrieve
    try:
        try:
            context = kernel.get_context_info(torch.from_numpy(scratch['target']), None)
        except IndexError as error:
            # Only this arm can consume the known failure. An adapter IndexError propagates.
            if adapter is not None:
                raise
            result['observed_exception'] = dict(type=type(error).__name__, message=str(error),
                                                traceback=traceback.format_exc())
            tb = error.__traceback__
            while tb.tb_next is not None:
                tb = tb.tb_next
            locals_ = tb.tb_frame.f_locals
            require(type(error) is IndexError and str(error) == expected['failure_metadata']['message'] and
                    tb.tb_frame.f_code is cls.get_context_info.__code__ and
                    tb.tb_frame.f_code.co_filename == PIPELINE + '[six-methods]' and
                    tb.tb_lineno == EXPECTED_ERROR_LINE, 'Unexpected exception location/type/message')
            require(locals_['sorted_frames'] == locals_['candidates'] == locals_['frame_count'] == [] and
                    locals_['max_frames'] == 0, 'Failure was not the original empty selection')
            for key in ('pairwise_distances', 'percentile_idx', 'is_second_step', 'use_non_maximum_suppression'):
                require(locals_[key] == expected['nms'][key], 'Original NMS locals differ: ' + key)
            result['expected_exception_match'] = dict(function='get_context_info', line=tb.tb_lineno,
                filename=tb.tb_frame.f_code.co_filename, statement=EXPECTED_ERROR_STATEMENT,
                sorted_frames=[], candidates=[], frame_count=[], max_frames=0,
                pairwise_distances=locals_['pairwise_distances'], percentile_idx=locals_['percentile_idx'])
            result['context_returned'] = False
        else:
            require(adapter is not None, 'Original unexpectedly returned a successful context')
            context = {key: value.detach().cpu().numpy() for key, value in context.items()}
            with (out / (label + '_context.npz')).open('xb') as handle:
                np.savez_compressed(handle, **context)
            require(set(context) == set(CACHE_OUTPUTS) | {'context_time_indices'}, 'Wrong context keys')
            ids = context['context_time_indices']
            require(ids.dtype == np.int64 and ids.shape == (4,) and ((ids >= 0) & (ids < 5)).all() and
                    np.unique(ids).size == 4, 'Expected four unique legal context IDs')
            result['selected_ids'], result['cache_slots_exact'] = ids.tolist(), {}
            for output_key, cache_key in CACHE_OUTPUTS.items():
                reference = np.stack([inputs['cache'][cache_key][int(i)] for i in ids]).astype(np.float32)
                require(np.isfinite(context[output_key]).all(), 'Nonfinite returned context')
                exact(context[output_key], reference)
                result['cache_slots_exact'][output_key] = True
            # This already-seen numeric reference is not a C2 successful-context oracle.
            reference_bytes = (ROOT / REFERENCE_MAPS).read_bytes()
            result['seen_reference_read'] = dict(path=REFERENCE_MAPS, expected_sha256=REFERENCE_SHA,
                                                actual_sha256=sha(reference_bytes), nbytes=len(reference_bytes))
            require(sha(reference_bytes) == REFERENCE_SHA, 'S61 reference SHA mismatch')
            from io import BytesIO
            with np.load(BytesIO(reference_bytes), allow_pickle=False) as archive:
                reference_maps = {key: archive[key].copy() for key in archive.files}
            check_maps(reference_maps)
            result['seen_reference_maps_max_abs_difference'] = {}
            for key, reference in reference_maps.items():
                actual = observed['maps'][key]
                if key == 'surfel_index_map':
                    exact(actual, reference)
                else:
                    np.testing.assert_allclose(actual, reference, rtol=1e-6, atol=1e-6)
                result['seen_reference_maps_max_abs_difference'][key] = float(np.max(np.abs(actual.astype(float)-reference.astype(float))))
            result['context_returned'] = True
        require(result['renderer_calls'] == result['retrieval_calls'] == 1, 'Expected one call per stage')
        result['initial_threshold'] = float(kernel.initial_threshold)
        require(result['initial_threshold'] == expected['nms']['initial_threshold'], 'NMS threshold differs')
        result['status'] = 'PASS_EXPECTED_ORIGINAL_FAILURE' if adapter is None else 'PASS_REPAIRED_CONTEXT'
    except Exception:
        result['status'], result['error'] = 'FAIL', traceback.format_exc()
        raise
    finally:
        result['original_inputs_sha256_before'] = before
        result['original_inputs_sha256_after'] = fingerprint(inputs)
        result['scratch_inputs_sha256_before'] = scratch_before
        result['scratch_inputs_sha256_after'] = fingerprint(scratch)
        # Include attached attributes, so replacement of a cache attribute is also detected.
        attached = dict(cache={key: getattr(kernel, key) for key in scratch['cache']},
                        surfels=kernel.surfels, target=scratch['target'],
                        surfel_to_timestep=kernel.surfel_to_timestep)
        result['attached_inputs_sha256_after'] = fingerprint(attached)
        require(result['original_inputs_sha256_after'] == before and
                result['scratch_inputs_sha256_after'] == scratch_before and
                result['attached_inputs_sha256_after'] == scratch_before, 'Input/cache mutation')


def main():
    out = HERE / 'execution_01'
    out.mkdir(exist_ok=False)
    started, begin = datetime.now(timezone.utc).isoformat(), time.monotonic()
    result = dict(status='RUNNING', started_utc=started, source_sha256=sha(Path(__file__).read_bytes()),
                  pinned_sources=PINS, archive=str(ARCHIVE), conditions=[], new_model_calls=0, RGB_reads=0,
                  surfel_depth_payload_reads=0, new_c2_generation=False, new_method_validated=False,
                  scope='One saved C2 failure; original error then real-cache context return, no get_cond')
    decoder, exit_code = None, 1
    try:
        require(sys.byteorder == 'little', 'Expected little-endian runtime')
        require(torch.__version__.split('+')[0] == '2.7.0' and np.__version__ == '1.26.4', 'Frozen numeric base required')
        torch.set_num_threads(8)
        result['runtime'] = dict(python=sys.version, numpy=np.__version__, torch=torch.__version__, threads=torch.get_num_threads())
        sources = {path: (ROOT / path).read_bytes() for path in PINS}
        for path, data in sources.items():
            require(sha(data) == PINS[path], 'Source/archive identity mismatch: ' + path)
        require(sources[PIPELINE].decode().splitlines()[EXPECTED_ERROR_LINE-1].strip() == EXPECTED_ERROR_STATEMENT,
                'Pinned failure statement differs')
        with (out / 'readlist.jsonl').open('x') as readlog:
            decoder = Decoder(ARCHIVE, readlog)
            inputs, expected = load_inputs(decoder)
        cls = original_numeric_class(sources)
        original_result = {}
        result['conditions'].append(original_result)
        run_arm('original', cls, inputs, expected, out, original_result)
        # The repaired arm starts only after the precise original failure is reproduced.
        adapter_namespace = {'__name__': 's63_pinned_s61_adapter'}
        exec(compile(sources[ADAPTER], ADAPTER, 'exec'), adapter_namespace)
        adapted_result = {}
        result['conditions'].append(adapted_result)
        run_arm('canonical_units', cls, inputs, expected, out, adapted_result,
                adapter_namespace['render_in_canonical_units'])
        result['status'], exit_code = 'PASS_C2_SAVED_CONTEXT_INTEGRATION', 0
    except Exception:
        result['status'], result['error'] = 'FAIL_C2_SAVED_CONTEXT_INTEGRATION', traceback.format_exc()
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
