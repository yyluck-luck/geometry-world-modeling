"""S35 original-loop observation wiring; import is standard-library only.

Preparation, not generation evidence. run_original calls the root-owned resource
validator before *any* factory. Real model construction/inputs/budgets belong to
the root factory and execution contract. No weights, downloads, or algorithms
are implemented here. Existing S20 source and TraceWriter remain unchanged.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
import hashlib
import inspect
import json
from pathlib import Path
from types import FunctionType, MethodType
from collections.abc import Mapping

BINDING = '_S35_GENERATION_OBSERVER'
BATCH = '_s35_observed_batch'
MISSING = object()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _statement(code):
    return ast.parse(code).body[0]


def _observer_call(node):
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id in (BINDING, BATCH))


class _StripObservation(ast.NodeTransformer):
    """Erase exactly our observation additions to check original AST equality."""
    def visit_With(self, node):
        if (len(node.items) == 1 and isinstance(node.items[0].context_expr, ast.Call)
                and ast.unparse(node.items[0].context_expr.func) == BINDING + '.batch'):
            return [self.visit(v) for v in node.body if not _observer_call(v)]
        return self.generic_visit(node)

    def visit_Expr(self, node):
        return None if _observer_call(node) else self.generic_visit(node)

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if ast.unparse(node.func) == BATCH + '.sample':
            require(node.args and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == 'do_sample', 'Unexpected sampler derivation')
            node.func, node.args = node.args[0], node.args[1:]
        return node


def derive_observed_methods(pipeline_source):
    """Read/parse fixed source only; do not import VMem or instantiate anything.

    Returns two AST functions and a round-trip proof. The generated code still
    resolves mathematical globals in the actual original pipeline module.
    """
    source = Path(pipeline_source).read_text()
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'VMemPipeline']
    require(len(classes) == 1, 'Original VMemPipeline class must be unique')
    names = ('_generate_frames_for_trajectory', 'get_context_info')
    originals = {}
    for name in names:
        found = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == name]
        require(len(found) == 1, 'Original method must be unique: ' + name)
        originals[name] = found[0]
    require(not any(isinstance(n, ast.Name) and n.id in (BINDING, BATCH)
                    for f in originals.values() for n in ast.walk(f)), 'Observer name collision')
    methods = {name: deepcopy(node) for name, node in originals.items()}
    loop_method = methods[names[0]]
    loops = [n for n in loop_method.body if isinstance(n, ast.For)
             and ast.unparse(n.iter) == 'range(generation_steps)']
    require(len(loops) == 1, 'Expected one original generation loop')
    loop = loops[0]
    context_at = [i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'context_info' for t in n.targets)]
    require(len(context_at) == 1, 'Expected one original context assignment')
    start = context_at[0] + 1
    tail = loop.body[start:]
    samples = cache_commits = map_commits = 0
    new_tail = []
    for node in tail:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == 'do_sample':
            node.value = ast.Call(func=ast.Attribute(value=ast.Name(id=BATCH, ctx=ast.Load()), attr='sample', ctx=ast.Load()),
                                  args=[ast.Name(id='do_sample', ctx=ast.Load())] + node.value.args,
                                  keywords=node.value.keywords)
            samples += 1
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and ast.unparse(node.value.func) == 'self.construct_and_store_scene'):
            new_tail.append(_statement(BATCH + '.commit_cache(target_encoder_embeddings=target_encoder_embeddings)'))
            cache_commits += 1
            new_tail.append(node)
            new_tail.append(_statement(BATCH + '.commit_map()'))
            map_commits += 1
        else:
            new_tail.append(node)
    require((samples, cache_commits, map_commits) == (1, 1, 1), 'Unexpected original sample/cache/map anchors')
    with_node = _statement('with ' + BINDING + '.batch(self, context_info, target_c2ws, target_Ks, padding_size=padding_size) as ' + BATCH + ':\n    pass')
    with_node.body = new_tail
    loop.body[start:] = [with_node]

    # Observe actual NMS locals; do not rerun geodesic distances, renderer or NMS.
    class ContextObserver(ast.NodeTransformer):
        def __init__(self):
            self.thresholds, self.selections = 0, 0

        def visit_Assign(self, node):
            if any(isinstance(t, ast.Attribute) and ast.unparse(t) == 'self.initial_threshold' for t in node.targets):
                self.thresholds += 1
                return [node, _statement(BINDING + ".capture_locals('nms_threshold', locals(), ('is_second_step','pairwise_distances','percentile_idx','use_non_maximum_suppression'))")]
            if (any(isinstance(t, ast.Name) and t.id == 'context_time_indices' for t in node.targets)
                    and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == 'torch.from_numpy'):
                self.selections += 1
                return [_statement(BINDING + ".capture_locals('nms_selection', locals(), ('candidates','distances','sorted_indices','sorted_frames','selected_indices','current_threshold','max_frames','is_second_step','use_non_maximum_suppression'))"), node]
            return node

    context_observer = ContextObserver()
    methods[names[1]] = context_observer.visit(methods[names[1]])
    require((context_observer.thresholds, context_observer.selections) == (3, 1), 'NMS source anchors changed')
    proof = {}
    for name, observed in methods.items():
        ast.fix_missing_locations(observed)
        stripped = _StripObservation().visit(deepcopy(observed))
        require(_dump(stripped) == _dump(originals[name]), 'Original AST changed after erasing observations: ' + name)
        # compile syntax only; no function body or module imports executed here.
        compile(ast.Module(body=[observed], type_ignores=[]), str(pipeline_source), 'exec')
        proof[name] = {'original_ast_sha256': hashlib.sha256(_dump(originals[name]).encode()).hexdigest(),
                       'observed_ast_sha256': hashlib.sha256(_dump(observed).encode()).hexdigest(),
                       'erase_observers_recovers_original_ast': True}
    return methods, proof


def _rng_values():
    """Read existing CPU states; no draws, seeding, or device initialization."""
    import random
    import numpy as np
    import torch
    return {'python': random.getstate(), 'numpy_legacy': np.random.get_state(),
            'torch_cpu': torch.get_rng_state()}


def _cache_tree(pipeline):
    return {name: getattr(pipeline, name) for name in
            ('pil_frames', 'latents', 'encoder_embeddings', 'c2ws', 'Ks', 'surfel_depths', 'surfel_Ks')}


def _map_tree(pipeline):
    return {'surfels': [{'position': s.position, 'normal': s.normal, 'radius': s.radius,
                         'color': s.color, 'source_ids': list(pipeline.surfel_to_timestep[i])}
                        for i, s in enumerate(pipeline.surfels)],
            'surfel_to_timestep': pipeline.surfel_to_timestep,
            'surfel_depths': pipeline.surfel_depths, 'surfel_Ks': pipeline.surfel_Ks}


def _shape_tree(value):
    """Counter diagnostics only, not activation retention or numerical scoring."""
    if hasattr(value, 'shape') and hasattr(value, 'dtype'):
        return {'shape': list(value.shape), 'dtype': str(value.dtype)}
    if isinstance(value, Mapping):
        return {str(k): _shape_tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_shape_tree(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return {'type': type(value).__module__ + '.' + type(value).__qualname__}


class _BatchObservation:
    def __init__(self, owner, event):
        self.owner, self.event = owner, event

    def sample(self, original, *args, **kwargs):
        owner = self.owner
        owner.require_source(original, 'do_sample')
        bound = inspect.signature(original).bind(*args, **kwargs)
        bound.apply_defaults()
        sampler = bound.arguments['sampler']

        def archive_sampler(denoiser, noise, *sa, **sk):
            require(not sa, 'Unexpected sampler positional layout')
            owner.count('sampler_call')
            # Original prepare_sampling_loop mutates noise in-place: save NOW.
            owner.capture('sampler_input', {'noise': noise, 'inputs': {k: sk[k] for k in
                          ('scale', 'cond', 'uc', 'c2w', 'K', 'input_frame_mask')}, 'rng': _rng_values()})
            output = sampler(denoiser, noise, *sa, **sk)
            owner.capture('sampler_output', {'output': output, 'rng': _rng_values()})
            return output

        bound.arguments['sampler'] = archive_sampler
        owner.count('do_sample')
        result = self.event.sample(original, *bound.args, **bound.kwargs)
        owner.capture('sample_output', {'samples': result[0], 'samples_z': result[1]})
        return result

    def commit_cache(self, *, target_encoder_embeddings):
        self.event.commit_cache(target_encoder_embeddings=target_encoder_embeddings)
        self.owner.capture('cache_commit', {'cache': _cache_tree(self.owner.pipeline),
                           'target_encoder_embeddings': target_encoder_embeddings,
                           'retained_ids': self.event.retained_ids,
                           'selected_context_ids': self.event.ids,
                           'padding_size': self.event.ntarget - self.event.nkeep})

    def commit_map(self):
        self.event.commit_map()
        self.owner.capture('map_commit', {'map': _map_tree(self.owner.pipeline),
                           'cache': _cache_tree(self.owner.pipeline)})


class OriginalLoopObservers:
    """Single original pipeline in one process; every patch restores on exit.

    The module is deliberately opt-in. Synthetic execution may use this same
    wiring only under an independently approved synthetic contract/trace.
    """
    def __init__(self, pipeline, *, navigator, pipeline_module, trace, archive, source_manifest):
        self.pipeline, self.navigator, self.module = pipeline, navigator, pipeline_module
        self.trace, self.archive, self.manifest = trace, archive, source_manifest
        self.undo, self.counts = [], {}
        self.operation_index, self.operation_name, self.batch_index = 0, 'not_started', 0
        self.active_batch_id, self.failed_batch = None, False
        self.last_context, self.last_context_ids = None, None
        self.completed_batches = []

    def count(self, name):
        self.counts[name] = self.counts.get(name, 0) + 1

    def metadata(self):
        return {'operation_index': self.operation_index, 'operation_name': self.operation_name,
                'batch_id': self.active_batch_id}

    def capture(self, name, payload):
        # Archive owns synchronous raw-copy serialization; no arbitrary objects.
        return self.archive.capture(name, {'metadata': self.metadata(), **payload})

    def capture_locals(self, name, namespace, keys):
        payload = {key: namespace[key] for key in keys if key in namespace}
        payload['observed_keys'] = [key for key in keys if key in namespace]
        if hasattr(self.pipeline, 'initial_threshold'):
            payload['initial_threshold'] = self.pipeline.initial_threshold
        self.capture(name, payload)

    def require_source(self, function, label):
        raw = inspect.unwrap(function)
        filename = inspect.getsourcefile(raw)
        require(filename is not None, 'Unbound original callable: ' + label)
        path = str(Path(filename).resolve())
        expected = self.manifest['identities'].get(path)
        require(expected is not None and file_sha(path) == expected, 'Original callable source changed: ' + label)

    def _patch(self, obj, name, value):
        old = obj.__dict__.get(name, MISSING)
        self.undo.append((obj, name, old))
        setattr(obj, name, value)

    def restore(self):
        errors = []
        for obj, name, old in reversed(self.undo):
            try:
                if old is MISSING:
                    delattr(obj, name)
                else:
                    setattr(obj, name, old)
            except BaseException as error:
                errors.append(type(error).__name__ + ': ' + str(error))
        self.undo.clear()
        require(not errors, 'Hook restoration failed: ' + '; '.join(errors))

    def _wrap_method(self, obj, name, label, *, before=None, after=None):
        original = getattr(obj, name)
        self.require_source(original, label)

        @wraps(original)
        def observed(*args, **kwargs):
            self.count(label)
            if before is not None:
                before(args, kwargs)
            result = original(*args, **kwargs)
            if after is not None:
                after(args, kwargs, result)
            return result
        self._patch(obj, name, observed)

    def _counter_method(self, obj, name, label):
        def before(args, kwargs):
            self.trace.observe('actual_call', values={'label': label, 'ordinal': self.counts[label],
                               'inputs': _shape_tree([args, kwargs]), **self.metadata()}, batch_id=self.active_batch_id)
        self._wrap_method(obj, name, label, before=before)

    def __enter__(self):
        try:
            require(self.module.__dict__.get(BINDING, MISSING) is MISSING, 'Another observer is installed')
            require(self.navigator.pipeline is self.pipeline, 'Navigator does not own this pipeline')
            source_path = Path(self.manifest['pipeline_source']).resolve()
            require(Path(self.module.__file__).resolve() == source_path, 'Wrong pipeline module namespace')
            require(self.trace.evidence_kind == self.archive.evidence_kind, 'Archive/trace evidence kinds disagree')
            for path, expected in self.manifest['identities'].items():
                require(file_sha(path) == expected, 'Observation source changed: ' + path)
            methods, self.derivation = derive_observed_methods(source_path)
            self._patch(self.module, BINDING, self)
            # Functions use the original live module dict, including its aliases.
            for name, node in methods.items():
                original = getattr(self.pipeline, name)
                self.require_source(original, name)
                namespace = dict(original.__func__.__globals__)
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(source_path), 'exec'), namespace)
                generated = namespace[name]
                derived = FunctionType(generated.__code__, original.__func__.__globals__, name,
                                       original.__func__.__defaults__, original.__func__.__closure__)
                derived.__kwdefaults__ = original.__func__.__kwdefaults__
                self._patch(self.pipeline, name, MethodType(derived, self.pipeline))

            def initialized(args, kwargs, result):
                self.capture('initial_output', {'return_pil': result, 'cache': _cache_tree(self.pipeline)})
            self._wrap_method(self.pipeline, 'initialize', 'pipeline_initialize',
                before=lambda a, k: self.capture('initial_input', {'args': a, 'kwargs': k}), after=initialized)
            def context_returned(args, kwargs, result):
                self.last_context = result
                raw_ids = result['context_time_indices']
                self.last_context_ids = raw_ids.detach().cpu().tolist() if hasattr(raw_ids, 'detach') else list(raw_ids)
                self.capture('context_output', {'context_info': result, 'cache': _cache_tree(self.pipeline),
                             'initial_threshold': getattr(self.pipeline, 'initial_threshold', None)})
            self._wrap_method(self.pipeline, 'get_context_info', 'get_context_info',
                before=lambda a, k: self.capture('context_input', {'args': a, 'kwargs': k}), after=context_returned)
            self._wrap_method(self.pipeline, 'get_translation_scaling_factor', 'translation_scaling',
                before=lambda a, k: self.capture('translation_input', {'args': a, 'kwargs': k}),
                after=lambda a, k, r: self.capture('translation_output', {'result': r}))
            self._wrap_method(self.pipeline, 'get_cond', 'get_cond',
                before=lambda a, k: self.capture('condition_input', {'args': a, 'kwargs': k}),
                after=lambda a, k, r: self.capture('condition_output', {'result': r}))
            for method, label in (('render_surfels_to_image', 'render'), ('process_retrieved_spatial_information', 'retrieval')):
                # Render input contains Surfel objects: explicitly export fields.
                before = (lambda a, k: self.capture('render_input', {'map': _map_tree(self.pipeline),
                          'args_after_surfels': a[1:], 'kwargs': k})) if label == 'render' else None
                self._wrap_method(self.pipeline, method, label, before=before,
                    after=lambda a, k, r, label=label: self.capture(label + '_output', {'result': r}))
            self._counter_method(self.pipeline, 'construct_and_store_scene', 'construct_scene')
            for name in ('encode_image', 'encode_vae_image'):
                # These are pipeline-module aliases, not utils-only patches.
                self._wrap_method(self.module, name, name,
                    before=lambda a, k, name=name: self.capture(name + '_input', {'image': a[0], 'device': a[2], 'dtype': a[3]}),
                    after=lambda a, k, r, name=name: self.capture(name + '_output', {'result': r}))
            self._wrap_method(self.module, 'run_inference_from_pil', 'geometry',
                before=lambda a, k: self.capture('geometry_input', {'input_images': a[0], 'kwargs': k}),
                after=lambda a, k, r: self.capture('geometry_output', {'scene': r}))
            for obj, name, label in ((self.pipeline.model_wrapper, 'forward', 'main_model_forward'),
                    (self.pipeline.vae, 'encode', 'vae_encode'), (self.pipeline.vae, 'decode', 'vae_decode'),
                    (self.pipeline.image_encoder, 'forward', 'clip_forward'),
                    (self.pipeline.sampler[0], 'sampler_step', 'euler_step')):
                self._counter_method(obj, name, label)
            self.trace.observe('integration_installed', values={'derivation': self.derivation,
                               'claim': 'installed observers only, not generation success'})
            return self
        except BaseException as error:
            try:
                self.restore()
            except BaseException as cleanup_error:
                error.add_note('S35 install cleanup: ' + str(cleanup_error))
            raise

    def __exit__(self, exc_type, exc, tb):
        try:
            self.restore()
        except BaseException as cleanup_error:
            if exc is None:
                raise
            exc.add_note('S35 exit cleanup: ' + str(cleanup_error))
        return False

    @contextmanager
    def batch(self, pipeline, context_info, target_c2ws, target_Ks, *, padding_size):
        require(pipeline is self.pipeline and context_info is self.last_context, 'Batch does not follow actual original context return')
        require(self.active_batch_id is None, 'Overlapping original batches')
        self.batch_index += 1
        bid = 'batch_' + str(self.batch_index)
        self.active_batch_id = bid
        try:
            with self.trace.batch(bid, pipeline, context_info, target_c2ws, target_Ks, padding_size=padding_size) as event:
                self.capture('batch_input', {'context_info': context_info, 'target_c2ws': target_c2ws,
                             'target_Ks': target_Ks, 'padding_size': padding_size, 'map': _map_tree(pipeline)})
                yield _BatchObservation(self, event)
            self.completed_batches.append({'batch_id': bid, 'selected_context_ids': list(event.ids),
                                           'retained_ids': list(event.retained_ids)})
        except BaseException:
            # S20 event context records a failure; creation failure has no batch.
            self.failed_batch = bid in self.trace.batch_ids
            raise
        finally:
            self.active_batch_id = None

    def invoke(self, name, *args):
        require(name in ('initialize', 'turn_left', 'turn_right'), 'Only the frozen original operations are exposed')
        self.operation_name = name
        self.capture('navigator_begin', {'name': name, 'args': args,
                     'current_pose': self.navigator.current_pose, 'current_K': self.navigator.current_K})
        original = getattr(self.navigator, name)
        self.require_source(original, 'Navigator.' + name)
        self.count('navigator_' + name)
        result = original(*args)
        self.capture('navigator_return', {'name': name, 'return': result,
                     'current_pose': self.navigator.current_pose, 'current_K': self.navigator.current_K,
                     'pose_history': self.navigator.pose_history,
                     'canonical_cache': _cache_tree(self.pipeline), 'counts': dict(self.counts)})
        self.operation_index += 1
        return result


def install_observers(pipeline, *, navigator, pipeline_module, trace, archive, source_manifest):
    return OriginalLoopObservers(pipeline, navigator=navigator, pipeline_module=pipeline_module,
                                 trace=trace, archive=archive, source_manifest=source_manifest)


def run_original(create_runtime, *, resource_gate, check_resource_gate, create_trace,
                 create_archive, source_manifest, evidence_kind='recorded_execution'):
    """Root-owned gate/factories; all three factories receive validated_gate.

    Required runtime keys: pipeline,navigator,pipeline_module,image,initial_pose,
    initial_K. No callback runs before check_resource_gate. The root owns final
    archive.finalize, trace verification, budgets and success decision. On any
    failure we preserve the original exception and close recorded prefixes.
    """
    require(evidence_kind in ('recorded_execution', 'synthetic_test'), 'Explicit evidence kind required')
    checked = check_resource_gate(resource_gate)  # MUST precede every factory.
    require(isinstance(checked, Mapping), 'Resource validator did not return a verified gate')
    require(checked.get('evidence_kind') == evidence_kind, 'Gate/evidence kind mismatch')
    trace = archive = observer = None
    phase = 'trace_factory'
    try:
        trace = create_trace(checked)
        require(trace.evidence_kind == evidence_kind, 'Trace factory returned another evidence kind')
        phase = 'archive_factory'
        archive = create_archive(checked)
        require(archive.evidence_kind == evidence_kind, 'Archive factory returned another evidence kind')
        phase = 'runtime_factory'
        runtime = create_runtime(checked)
        required = {'pipeline','navigator','pipeline_module','image','initial_pose','initial_K'}
        require(isinstance(runtime, Mapping) and required <= set(runtime), 'Incomplete original runtime')
        phase = 'install_observers'
        import torch  # Deferred until the real resource gate/runtime completed.
        require(not torch.is_inference_mode_enabled(), 'Outer inference_mode would disable original GA gradients')
        with torch.no_grad(), install_observers(runtime['pipeline'], navigator=runtime['navigator'],
                pipeline_module=runtime['pipeline_module'], trace=trace, archive=archive,
                source_manifest=source_manifest) as observer:
            require(len(runtime['pipeline'].pil_frames) == 0, 'Original runtime must be fresh and uninitialized')
            phase = 'initialize'
            initial = observer.invoke('initialize', runtime['image'], runtime['initial_pose'], runtime['initial_K'])
            require(len(runtime['pipeline'].pil_frames) == 1, 'Initialize did not retain exactly ID0')
            phase = 'turn_left'
            left = observer.invoke('turn_left', 5)
            require(len(runtime['pipeline'].pil_frames) == 5, 'First original turn did not retain history5')
            phase = 'turn_right'
            right = observer.invoke('turn_right', 5)
            require(len(runtime['pipeline'].pil_frames) == 9, 'Second original turn did not retain history9')
            require(len(observer.completed_batches) == 2, 'Original route did not complete exactly two batches')
            require(any(i > 0 for i in observer.completed_batches[1]['selected_context_ids']),
                    'Second batch did not consume an actual generated cache ID')
            summary = {'counts': dict(observer.counts), 'batches': observer.completed_batches,
                       'evidence_kind': evidence_kind, 'status': 'OBSERVED_ROUTE_RETURNED_NOT_QUALITY_VERIFIED'}
            archive.capture('integration_return', summary)
        trace.close()
        return {'runtime': runtime, 'initial_return': initial, 'left_return': left,
                'right_return': right, 'observation_summary': summary,
                'trace': trace, 'archive': archive}
    except BaseException as error:
        # A recording error must not silently disable observation and continue.
        # Secondary cleanup faults annotate, never replace, the original error.
        for action in (
            lambda: trace.failed_operation(phase, error) if trace is not None and trace.active is None
                       and not (observer is not None and observer.failed_batch) else None,
            lambda: archive.fail(error, phase=phase) if archive is not None else None,
            lambda: trace.close() if trace is not None and not trace.closed and trace.active is None else None,
        ):
            try:
                action()
            except BaseException as cleanup_error:
                error.add_note('S35 cleanup: ' + type(cleanup_error).__name__ + ': ' + str(cleanup_error))
        raise


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Source-only S35 derivation report; never creates runtime')
    parser.add_argument('--pipeline-source', type=Path, required=True)
    args = parser.parse_args()
    _, proof = derive_observed_methods(args.pipeline_source)
    print(json.dumps({'status': 'SOURCE_AST_ROUNDTRIP_ONLY', 'proof': proof,
                      'scientific_execution': False}, indent=2))


if __name__ == '__main__':
    main()
