#!/usr/bin/env python3
"""Frozen, CPU-only profiling of 24 already-seen S7/S8 retrieval queries.

Requires a separately approved execution freeze. No model, RGB/depth PNG, GT,
new sampling, geometry update, or incremental retrieval algorithm is run.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import platform
import re
import resource
import signal
import sys
import textwrap
import time
import traceback
from types import MethodType
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = (
    'scripts/profile_s9_components.py', 'src/s6_memory_bridge.py',
    'src/s7_event_replay.py', 'src/rgbd_memory.py', 'src/rgbd_retrieval.py',
    'src/retrieval_diagnostic.py', 'src/vmem_memory_kernel.py',
    'src/vmem_retrieval_kernel.py', 'vendor/provenance.json', 'vendor/VMEM_LICENSE')
CONTRACT = dict(schema='s9-component-profile-v1', stages=['S7', 'S8'],
    blocks=[0, 1, 2], queries=[20, 21, 22, 23], stride=8, arm='A0P0', width=160,
    history_count=20, context_count=4, warmup_rounds=1, measured_rounds=5,
    order='stage_then_block_then_query', device='cpu', torch_threads=8,
    torch_interop_threads=8, wall_budget_seconds=300, peak_rss_budget_bytes=16*1024**3,
    resource_limit='soft', exact_output_gate=True, diagnostic_atol=1e-9,
    diagnostic_rtol=1e-10, raw_pixels_allowed=False, gt_allowed=False,
    model_loading_allowed=False)
PHASES = ('renderer_ns', 'votes_allocation_ns', 'sort_nms_ns')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                   allow_nan=False)+'\n')


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: '+key)
            result[key] = value
        return result
    def bad(value):
        raise ValueError('Nonfinite JSON: '+value)
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=bad)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expected_inputs(runs):
    """Path inventory only; no array/image decoding or profiling."""
    result = []
    for stage in CONTRACT['stages']:
        run = runs[stage]
        result.extend([run/'run_metadata.json', run/'records.json'])
        for block in CONTRACT['blocks']:
            case = run/f'block{block}_stride8'
            result.extend(case/name for name in ('A0P0.npz', 'A0P0_sources.json',
                'predicted_poses.npz', 'prediction_only_selection.json'))
            result.extend(case/f'query{q}_A0P0_render.npz' for q in CONTRACT['queries'])
    return result


def install_io_guard(inputs, output):
    """Guard this runner's data access; not an OS sandbox or clean environment."""
    allowed = {p.resolve(strict=True) for p in inputs}
    out = output.resolve(strict=True)
    def hook(event, args):
        if event.startswith('socket.') and event != 'socket.__new__':
            raise PermissionError('S9 profiling has no network access')
        if event == 'subprocess.Popen':
            raise PermissionError('S9 profiling launches no subprocess/model')
        if event != 'open' or not args or not isinstance(args[0], (str, bytes)):
            return
        p = Path(os.path.abspath(os.fsdecode(args[0])))
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        writing = ((isinstance(mode, str) and any(x in mode for x in 'wax+')) or
            (isinstance(flags, int) and flags &
             (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
        if writing:
            if not p.is_relative_to(out):
                raise PermissionError('Writes must stay in fresh S9 output: '+str(p))
            return
        if p.is_relative_to(out):
            return
        if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.pt', '.pth', '.safetensors'):
            raise PermissionError('Raw pixels/model weights prohibited: '+str(p))
        if p.is_relative_to(ROOT/'data') or (p.is_relative_to(ROOT/'results') and p not in allowed):
            raise PermissionError('Unlisted original data/results prohibited: '+str(p))
    sys.addaudithook(hook)


def instrument_context_method(kernel_module, output):
    """Add six clock reads around three original statement ranges; verify AST."""
    source = textwrap.dedent(inspect.getsource(kernel_module.RetrievalKernel.get_context_info))
    require('__s9_' not in source, 'Instrumentation namespace collision')
    original = ast.parse(source)
    tree = copy.deepcopy(original)
    method = tree.body[0]
    branches = [n for n in method.body if isinstance(n, ast.If) and n.orelse]
    require(len(branches) == 1, 'Original context branch changed')
    branch = branches[0]
    start = {'retrieved_info': 'renderer_ns', 'candidates': 'sort_nms_ns'}
    inserted = []
    instrumented = []
    counts = {name: 0 for name in PHASES}
    def marker(text):
        node = ast.parse(text).body[0]
        inserted.append(ast.dump(node, include_attributes=False))
        instrumented.append(node)
    for node in branch.orelse:
        target = ast.unparse(node.targets[0]) if isinstance(node, ast.Assign) else None
        if target in start:
            marker('__s9_begin = __s9_clock()')
        if target == '(_, frame_count)':
            marker('__s9_begin = __s9_clock()')
        instrumented.append(node)
        phase = {'retrieved_info': 'renderer_ns', '(_, frame_count)': 'votes_allocation_ns',
                 'context_time_indices': 'sort_nms_ns'}.get(target)
        if phase:
            marker(f'self.__s9_times[{phase!r}] = __s9_clock() - __s9_begin')
            counts[phase] += 1
    require(all(v == 1 for v in counts.values()), 'Phase boundaries did not match exactly once')
    branch.orelse = instrumented
    restored = copy.deepcopy(tree)
    restored_branch = [n for n in restored.body[0].body if isinstance(n, ast.If) and n.orelse][0]
    marker_dumps = set(inserted)
    restored_branch.orelse = [n for n in restored_branch.orelse
                            if ast.dump(n, include_attributes=False) not in marker_dumps]
    identical = ast.dump(restored, include_attributes=False) == ast.dump(original, include_attributes=False)
    require(identical, 'Original AST differs after removing timing markers')
    ast.fix_missing_locations(tree)
    adapted = ast.unparse(tree)+'\n'
    (output/'timed_get_context_info.py.txt').write_text(adapted)
    (output/'original_get_context_info.py.txt').write_text(source)
    namespace = dict(vars(kernel_module), __s9_clock=time.perf_counter_ns)
    exec(compile(tree, '<S9 timing-only context instrumentation>', 'exec'), namespace)
    return namespace['get_context_info'], dict(original_AST_preserved=True,
        inserted_statements=len(inserted), clock_reads=6, phase_boundaries=counts,
        original_text_sha256=hashlib.sha256(source.encode()).hexdigest(),
        instrumented_text_sha256=hashlib.sha256(adapted.encode()).hexdigest())


def peak_rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value*1024)


def load_cases(runs, np, torch, modules, inputs):
    bridge, events, retrieval = modules['s6_memory_bridge'], modules['s7_event_replay'], modules['rgbd_retrieval']
    Memory, Surfel = modules['rgbd_memory'].Memory, modules['vmem_memory_kernel'].Surfel
    cases = []
    for stage in CONTRACT['stages']:
        run = runs[stage]
        meta = read(run/'run_metadata.json')
        require(meta.get('status') == 'completed' and meta.get('phase') == 'complete',
                stage+' replay must be completed')
        for name in SOURCE_NAMES:
            if name.startswith('src/'):
                require(sha(ROOT/name) == meta['source_sha256'][name],
                        stage+' historical retrieval source changed: '+name)
        records = read(run/'records.json')
        refs = {(r['block'], r['stride'], r['frame']): r for r in records}
        require(len(refs) == len(records), 'Duplicate saved record')
        for block in CONTRACT['blocks']:
            folder = run/f'block{block}_stride8'
            entries = [x for x in meta['cases'] if x['block'] == block and x['stride'] == 8]
            require(len(entries) == 1 and entries[0]['directory'] == folder.name, 'Historical case domain mismatch')
            for p in inputs:
                if p.parent == folder:
                    require(sha(p) == entries[0]['sealed_files'][p.name], 'Historical case seal mismatch: '+str(p))
            choice = read(folder/'prediction_only_selection.json')
            require(choice['block'] == block and choice['stride'] == 8 and choice['width'] == 160,
                    'Historical case configuration mismatch')
            require([x['frame'] for x in choice['queries']] == CONTRACT['queries'], 'Saved query domain mismatch')
            with np.load(folder/'A0P0.npz', allow_pickle=False) as z:
                values = {k: z[k] for k in z.files}
            require(set(values) == {'points', 'normals', 'radii', 'colors', 'counts'}, 'Map schema mismatch')
            count = len(values['points'])
            require(values['points'].shape == values['normals'].shape == values['colors'].shape == (count, 3)
                    and values['radii'].shape == values['counts'].shape == (count,)
                    and all(np.isfinite(v).all() for v in values.values()), 'Invalid saved map arrays')
            mapping = {int(k): v for k, v in read(folder/'A0P0_sources.json').items()}
            memory = Memory(surfels=[Surfel(p.copy(), n.copy(), float(r), c.copy()) for p, n, r, c in
                zip(values['points'], values['normals'], values['radii'], values['colors'])],
                counts=values['counts'].tolist(), mapping=mapping)
            for key, array in events.arrays(memory).items():
                require(array.dtype == values[key].dtype and np.array_equal(array, values[key]),
                        'Loading altered map: '+key)
            require(bridge.memory_digest(memory) == choice['maps']['A0P0']['digest'], 'Loaded memory digest mismatch')
            with np.load(folder/'predicted_poses.npz', allow_pickle=False) as z:
                require(z.files == ['poses'], 'Saved pose schema mismatch')
                poses = z['poses']
            require(poses.shape == (24, 4, 4) and np.isfinite(poses).all(), 'Invalid predicted poses')
            kernel = bridge.make_selector(memory, poses[:20], width=160)
            for item in choice['queries']:
                q = item['frame']; label = f'{stage}_block{block}_query{q}'
                expected = item['maps']['A0P0']
                require(expected['official_trace']['selected'] == refs[(block, 8, q)]['readouts']['A0P0']['official']['selected'],
                        label+' saved selection/record mismatch')
                require(kernel.initial_threshold == expected['official_trace']['nms_initial_threshold'],
                        label+' NMS threshold mismatch')
                with np.load(folder/f'query{q}_A0P0_render.npz', allow_pickle=False) as z:
                    render = {k: z[k] for k in z.files}
                require(set(render) == {'depth', 'surfel_index_map', 'cos_value_map'} and
                        all(v.shape == (160, 160) and np.isfinite(v).all() for v in render.values()),
                        label+' invalid reference render')
                cases.append(dict(stage=stage, block=block, query=q, label=label, kernel=kernel,
                    memory=memory, memory_digest=choice['maps']['A0P0']['digest'], pose=poses[q].copy(),
                    target=torch.tensor(retrieval.optical_to_vmem(poses[q])[None], dtype=torch.float64),
                    expected=expected, render=render, map_points=count))
    require(len(cases) == 24, 'Expected exactly 24 previously seen queries')
    return cases


def validate_output(case, result, np, modules, output, round_name):
    kernel = case['kernel']
    for name, expected in case['render'].items():
        actual = kernel.last_render[name]
        if actual.shape != expected.shape or actual.dtype != expected.dtype or not np.array_equal(actual, expected):
            np.savez_compressed(output/f"FAILED_{round_name}_{case['label']}_render.npz", **kernel.last_render)
            raise ValueError(case['label']+' exact render regression failed: '+name)
    # Reuse unchanged diagnostic wrapper outside the timer without another render.
    # Its temporary getter returns this invocation's output, never a saved baseline.
    previous = kernel.get_context_info
    try:
        kernel.get_context_info = lambda *args, **kwargs: result
        official = modules['rgbd_retrieval'].select(kernel, case['pose'])
    finally:
        kernel.get_context_info = previous
    decision = modules['s7_event_replay'].decision_trace(kernel, case['pose'], kernel.last_counts, nms=True)
    actual = dict(official_trace=official, official_decision=decision)
    if official != case['expected']['official_trace'] or decision != case['expected']['readouts']['official']:
        save(output/f"FAILED_{round_name}_{case['label']}_decision.json", actual)
        raise ValueError(case['label']+' exact vote/count/full trace/ordered-ID regression failed')
    return actual


def summarize(rows):
    import statistics
    groups = {}
    for stage in ('all', 'S7', 'S8'):
        subset = [r for r in rows if not r['warmup'] and (stage == 'all' or r['stage'] == stage)]
        groups[stage] = dict(invocations=len(subset), distinct_queries=24 if stage == 'all' else 12)
        for phase in (*PHASES, 'total_ns', 'other_ns'):
            values = [r[phase]/1e6 for r in subset]
            groups[stage][phase.removesuffix('_ns')+'_ms'] = dict(
                mean=statistics.mean(values), median=statistics.median(values),
                min=min(values), max=max(values), total=sum(values))
        total = sum(r['total_ns'] for r in subset)
        groups[stage]['time_shares'] = {p.removesuffix('_ns'):sum(r[p] for r in subset)/total
                                       for p in (*PHASES, 'other_ns')}
    per_query = []
    for label in dict.fromkeys(r['label'] for r in rows):
        selected = [r for r in rows if not r['warmup'] and r['label'] == label]
        per_query.append(dict(label=label, repeats=len(selected),
            **{p.removesuffix('_ns')+'_median_ms':statistics.median(r[p] for r in selected)/1e6
               for p in (*PHASES, 'total_ns', 'other_ns')}))
    return dict(groups=groups, per_query=per_query,
        inference='Descriptive repeated-call software timings only; repeats are not independent samples.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('s7', 's8', 'protocol', 'freeze', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    requested_output = args.output.absolute()
    require(not requested_output.exists() and not requested_output.is_symlink(),
            'Requested output path already exists, including a dangling symlink')
    output = requested_output.resolve()
    require(not output.exists() and not output.is_symlink(), 'Output must be a fresh directory; failures remain')
    for protected in ('src', 'scripts', 'docs', 'data', 'vendor'):
        require(not output.is_relative_to(ROOT/protected), 'Output overlaps protected project files')
    runs = {'S7': args.s7.resolve(strict=True), 'S8': args.s8.resolve(strict=True)}
    require(runs == {'S7':ROOT/'results/S7_event_replay', 'S8':ROOT/'results/S8_event_replay_v2'},
            'Only the named completed S7/S8 runs are in scope')
    require(not any(output.is_relative_to(p) for p in runs.values()), 'Output overlaps an original run')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = dict(status='running', phase='preflight', started_utc=utc(), contract=CONTRACT,
                  checks=[], output=str(output), limitations=[
        '24 already-seen queries from two existing scenes, including S7 development block; software profiling only.',
        'Five repeated rounds do not create independent queries/scenes or a statistical speedup claim.',
        'CPU component kernel with dummy context arrays; not full VMem, generation, model inference or deployment time.',
        'Fresh renderer calls are executed; no RGB/depth PNG, GT trajectory or model weights are loaded.',
        'Instrumented wall times include timer/wrapper overhead; no overhead subtraction or uninstrumented speed claim.',
        'Python executes serially; Torch intra/inter-op threads fixed to 8. Existing local environment is reused.',
        '300-second wall alarm and 16-GiB peak-RSS checks are soft guards, not a hard OS memory sandbox.'])
    save(output/'run_metadata.json', report)
    rows = []
    original_sources = {}
    inputs = []
    def budget():
        require(time.monotonic()-started <= 300, 'Five-minute total execution budget exceeded')
        require(peak_rss_bytes() <= 16*1024**3, '16-GiB soft peak-RSS budget exceeded')
    def alarm(signum, frame):
        raise TimeoutError('Five-minute wall alarm; fresh partial result is preserved')
    previous_handler = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        protocol, freeze_path = args.protocol.resolve(strict=True), args.freeze.resolve(strict=True)
        freeze = read(freeze_path)
        require(freeze.get('schema') == 's9-component-profile-freeze-v1' and
                freeze.get('status') == 'approved_for_execution', 'Reviewed execution freeze is required')
        frozen_time = datetime.fromisoformat(freeze['frozen_utc'])
        require(frozen_time.tzinfo is not None and frozen_time <= datetime.fromisoformat(report['started_utc']),
                'Execution freeze must predate this run')
        require(sha(protocol) == freeze['protocol_sha256'], 'Protocol differs from freeze')
        match = re.findall(r'```s9-profile-json\s*\n(.*?)\n```', protocol.read_text(), re.S)
        require(len(match) == 1 and json.loads(match[0]) == CONTRACT, 'Protocol machine contract mismatch')
        require(set(freeze['execution_source_sha256']) == set(SOURCE_NAMES), 'Execution source inventory mismatch')
        original_sources = {ROOT/name:digest for name, digest in freeze['execution_source_sha256'].items()}
        for path, digest in original_sources.items():
            require(sha(path) == digest, 'Execution source changed: '+str(path))
        inputs = expected_inputs(runs)
        require(len(inputs) == len(set(inputs)) == 52, 'Fixed input inventory mismatch')
        input_sha = {str(p.relative_to(ROOT)):sha(p) for p in inputs}
        require(input_sha == freeze['input_sha256'], 'Input inventory/SHA differs from freeze')
        report.update(protocol_sha256=sha(protocol), freeze_sha256=sha(freeze_path),
            input_sha256=input_sha, execution_source_sha256=freeze['execution_source_sha256'],
            inputs_sealed_utc=utc())
        with zipfile.ZipFile(output/'profile_source.zip', 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for path in original_sources:
                z.write(path, str(path.relative_to(ROOT)))
            z.write(protocol, 'frozen_protocol.md'); z.write(freeze_path, 'execution_freeze.json')
        with zipfile.ZipFile(output/'sealed_profile_inputs.zip', 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for path in inputs:
                z.write(path, str(path.relative_to(ROOT)))
        sys.dont_write_bytecode = True
        sys.pycache_prefix = str(output/'unused_pycache')
        install_io_guard(inputs, output)
        for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                    'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[key] = '8'
        os.environ['OMP_DYNAMIC'] = os.environ['MKL_DYNAMIC'] = 'FALSE'
        import numpy as np
        import torch
        torch.set_num_threads(8); torch.set_num_interop_threads(8)
        require(torch.get_num_threads() == torch.get_num_interop_threads() == 8, 'Torch thread configuration failed')
        require(torch.get_default_dtype() == torch.float32, 'Original distance-sort default must be float32')
        sys.path.insert(0, str(ROOT/'src'))
        names = ['s6_memory_bridge', 's7_event_replay', 'rgbd_memory', 'rgbd_retrieval',
                 'retrieval_diagnostic', 'vmem_memory_kernel', 'vmem_retrieval_kernel']
        modules = {name:importlib.import_module(name) for name in names}
        for name, module in modules.items():
            require(Path(module.__file__).resolve() == ROOT/'src'/f'{name}.py', 'Unexpected module location')
        report['environment'] = dict(python=sys.version, python_executable=sys.executable,
            platform=dict(system=platform.system(), release=platform.release(), version=platform.version()),
            machine=platform.machine(), logical_cpus=os.cpu_count(),
            numpy=np.__version__, torch=torch.__version__, torch_threads=torch.get_num_threads(),
            torch_interop_threads=torch.get_num_interop_threads(), torch_default_dtype=str(torch.get_default_dtype()),
            native_thread_environment={k:v for k,v in os.environ.items() if k.endswith('_NUM_THREADS') or
                k in ('VECLIB_MAXIMUM_THREADS','OMP_DYNAMIC','MKL_DYNAMIC')})
        method, report['instrumentation'] = instrument_context_method(modules['vmem_retrieval_kernel'], output)
        cases = load_cases(runs, np, torch, modules, inputs)
        for case in cases:
            case['kernel'].get_context_info = MethodType(method, case['kernel'])
        report.update(initialization_completed_utc=utc(), initialization_elapsed_seconds=time.monotonic()-started,
            query_order=[c['label'] for c in cases], phase='warmup', data_arrays_decoded='saved map/pose/render NPZ only',
            raw_pixels_decoded=False, gt_loaded=False, model_loaded=False)
        save(output/'run_metadata.json', report)
        budget()
        with (output/'timings.jsonl').open('x') as stream:
            for repeat in range(6):
                round_name = 'warmup' if repeat == 0 else f'repeat{repeat}'
                report['phase'] = round_name
                save(output/'run_metadata.json', report)
                for case in cases:
                    budget()
                    kernel = case['kernel']; kernel.__s9_times = {}
                    before = time.perf_counter_ns()
                    result = kernel.get_context_info(case['target'])
                    total = time.perf_counter_ns()-before
                    phase = dict(kernel.__s9_times)
                    require(set(phase) == set(PHASES) and all(type(v) is int and v >= 0 for v in phase.values()),
                            'Missing phase timings')
                    other = total-sum(phase.values())
                    require(other >= 0, 'Phase timing sum exceeds total')
                    actual = validate_output(case, result, np, modules, output, round_name)
                    if repeat == 0:
                        save(output/(case['label']+'_regression.json'), actual)
                    row = dict(stage=case['stage'], block=case['block'], query=case['query'], label=case['label'],
                        round=repeat, warmup=repeat == 0, map_points=case['map_points'],
                        total_ns=total, other_ns=other, **phase, exact_regression_passed=True)
                    rows.append(row); stream.write(json.dumps(row, allow_nan=False)+'\n'); stream.flush()
                    budget()
        require(len(rows) == 144 and sum(not r['warmup'] for r in rows) == 120, 'Incomplete fixed schedule')
        for case in cases:
            require(modules['s6_memory_bridge'].memory_digest(case['memory']) == case['memory_digest'],
                    'Profiling mutated an in-memory map')
        for path, digest in original_sources.items():
            require(sha(path) == digest, 'Original source changed during profiling')
        require({str(p.relative_to(ROOT)):sha(p) for p in inputs} == input_sha, 'Original inputs changed')
        budget()
        save(output/'summary.json', summarize(rows))
        report.update(status='completed', phase='complete', exact_output_regressions_passed=144,
            distinct_previously_seen_queries=24, warmup_invocations=24, measured_invocations=120,
            original_sources_unchanged=True, original_inputs_unchanged=True,
            source_archive_sha256=sha(output/'profile_source.zip'),
            input_archive_sha256=sha(output/'sealed_profile_inputs.zip'))
    except Exception:
        report.update(status='failed', traceback=traceback.format_exc(),
                      completed_query_invocations=len(rows), partial_timings_valid_for_claims=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        report.update(completed_utc=utc(), total_elapsed_seconds=time.monotonic()-started,
                      process_peak_rss_bytes=peak_rss_bytes())
        save(output/'run_metadata.json', report)
    print(json.dumps({k:report.get(k) for k in ('status','phase','output','completed_utc',
        'total_elapsed_seconds','process_peak_rss_bytes')}, ensure_ascii=False))
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
