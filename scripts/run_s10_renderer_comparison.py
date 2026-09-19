#!/usr/bin/env python3
"""Frozen paired comparison of original/candidate CPU renderers on seen inputs.

No raw images, GT, model weights, new sampling, or candidate development. A new
root-approved freeze is mandatory. All rendering and timing is behind that gate.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import signal
import statistics
import sys
import time
import traceback
from types import MethodType
import zipfile

import profile_s9_components as s9

ROOT = Path(__file__).resolve().parents[1]
S9_FREEZE_SHA = '8e9c0a84cea827cf11d01f793e21ce46a9c2ce579206cc6678d3d006805fa9cd'
SOURCE_NAMES = (*s9.SOURCE_NAMES, 'scripts/run_s10_renderer_comparison.py',
                'src/s10_vectorized_renderer.py')
CONTRACT = dict(schema='s10-renderer-comparison-v1', stages=['S7', 'S8'],
    blocks=[0, 1, 2], queries=[20, 21, 22, 23], stride=8, arm='A0P0', width=160,
    history_count=20, context_count=4, correctness_rounds=1, warmup_rounds=1,
    measured_rounds=5, methods=['original', 'candidate'],
    query_order='stage_then_block_then_query',
    pair_order='AB_if_query_index_plus_round_index_is_even_else_BA',
    device='cpu', torch_threads=8, torch_interop_threads=8,
    versions=dict(python='3.12.14', numpy='2.3.5', torch='2.7.0', scipy='1.16.2'),
    wall_budget_seconds=600, peak_rss_budget_bytes=16*1024**3, resource_limit='soft',
    exact_output_gate=True, raw_pixels_allowed=False, gt_allowed=False,
    model_loading_allowed=False, saved_render_for_every_completed_call=True)
require, read, save, sha, utc = s9.require, s9.read, s9.save, s9.sha, s9.utc


def pair_order(query_index, round_index):
    return ('original', 'candidate') if (query_index+round_index) % 2 == 0 else ('candidate', 'original')


def schedule():
    """Pure fixed schedule; no file/array reads or timing."""
    queries = [(stage, b, q) for stage in CONTRACT['stages']
               for b in CONTRACT['blocks'] for q in CONTRACT['queries']]
    result = []
    for phase, rounds in (('correctness', 1), ('warmup', 1), ('measured', 5)):
        for repeat in range(rounds):
            for index, (stage, block, query) in enumerate(queries):
                result.append(dict(phase=phase, round=repeat, query_index=index,
                    stage=stage, block=block, query=query,
                    label=f'{stage}_block{block}_query{query}',
                    methods=pair_order(index, repeat)))
    return result


def observed_renderer(function):
    """Identical return-value observer wrapper for both bound renderer functions."""
    def render(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        self.last_render = result
        return result
    return render


def array_identity(value, np):
    array = np.asarray(value)
    return dict(shape=list(array.shape), dtype=str(array.dtype),
                sha256=hashlib.sha256(array.tobytes(order='C')).hexdigest())


def state_identity(case, np, bridge):
    kernel = case['kernel']
    return dict(memory_digest=bridge.memory_digest(case['memory']),
        c2ws=[array_identity(a, np) for a in kernel.c2ws],
        Ks=[array_identity(a, np) for a in kernel.Ks],
        latents=[array_identity(a, np) for a in kernel.latents],
        encoder_embeddings=[array_identity(a, np) for a in kernel.encoder_embeddings],
        surfel_Ks=[float(a) for a in kernel.surfel_Ks], initial_threshold=float(kernel.initial_threshold),
        target=array_identity(case['target'].detach().cpu().numpy(), np),
        optical_query=array_identity(case['pose'], np))


def summarize(rows):
    measured = [r for r in rows if r['phase'] == 'measured']
    require(len(measured) == 240 and all(r['exact_regression_passed'] for r in measured),
            'Only the full passing measured schedule can be summarized')
    grouped = {}
    for row in measured:
        key = (row['round'], row['query_index'])
        require(row['method'] not in grouped.setdefault(key, {}), 'Duplicate paired measurement')
        grouped[key][row['method']] = row
    require(len(grouped) == 120 and all(set(v) == {'original', 'candidate'} for v in grouped.values()),
            'Missing paired measurements')
    pairs = []
    for (repeat, index), arms in grouped.items():
        a, b = arms['original'], arms['candidate']
        require(a['pair_order'] == b['pair_order'], 'Pair order mismatch')
        pairs.append(dict(round=repeat, query_index=index, label=a['label'], stage=a['stage'],
            pair_order=a['pair_order'], original_ns=a['elapsed_ns'], candidate_ns=b['elapsed_ns'],
            original_over_candidate=a['elapsed_ns']/b['elapsed_ns']))
    def group(values):
        a = [r['original_ns'] for r in values]; b = [r['candidate_ns'] for r in values]
        return dict(pairs=len(values), distinct_queries=len({r['label'] for r in values}),
            original=dict(total_ns=sum(a), mean_ms=statistics.mean(a)/1e6,
                          median_ms=statistics.median(a)/1e6, min_ms=min(a)/1e6, max_ms=max(a)/1e6),
            candidate=dict(total_ns=sum(b), mean_ms=statistics.mean(b)/1e6,
                           median_ms=statistics.median(b)/1e6, min_ms=min(b)/1e6, max_ms=max(b)/1e6),
            ratio_of_total_times=sum(a)/sum(b),
            median_paired_ratio=statistics.median(r['original_over_candidate'] for r in values),
            AB_pairs=sum(r['pair_order'] == 'AB' for r in values),
            BA_pairs=sum(r['pair_order'] == 'BA' for r in values))
    groups = {'all':group(pairs)}
    groups.update({stage:group([p for p in pairs if p['stage'] == stage]) for stage in ('S7', 'S8')})
    groups.update({order:group([p for p in pairs if p['pair_order'] == order]) for order in ('AB', 'BA')})
    per_query = []
    for index in range(24):
        values = [p for p in pairs if p['query_index'] == index]
        a = statistics.median(p['original_ns'] for p in values)
        b = statistics.median(p['candidate_ns'] for p in values)
        per_query.append(dict(query_index=index, label=values[0]['label'], repeats=len(values),
            original_median_ms=a/1e6, candidate_median_ms=b/1e6, ratio_of_medians=a/b,
            AB_pairs=sum(p['pair_order'] == 'AB' for p in values),
            BA_pairs=sum(p['pair_order'] == 'BA' for p in values)))
    return dict(primary_estimator='ratio of summed original/candidate integer nanoseconds over 120 measured pairs',
        groups=groups, per_query=per_query, pairs=pairs,
        limitations='Descriptive paired software measurements on 24 seen queries; no independent-replicate significance test.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('s7', 's8', 's9-freeze', 'protocol', 'freeze', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    requested = args.output.absolute()
    require(not requested.exists() and not requested.is_symlink(), 'Output already exists; failures must remain')
    output = requested.resolve()
    require(not output.exists(), 'Resolved output already exists')
    for name in ('src', 'scripts', 'docs', 'data', 'vendor'):
        require(not output.is_relative_to(ROOT/name), 'Output overlaps protected project material')
    runs = dict(S7=args.s7.resolve(strict=True), S8=args.s8.resolve(strict=True))
    require(runs == dict(S7=ROOT/'results/S7_event_replay', S8=ROOT/'results/S8_event_replay_v2'),
            'Only the exact S9 source runs are eligible')
    require(not any(output.is_relative_to(p) for p in (*runs.values(), ROOT/'results/S9_component_profile')),
            'Output overlaps a prior experiment')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = dict(status='running', phase='preflight', started_utc=utc(), output=str(output),
        contract=CONTRACT, limitations=[
            'Ordinary component engineering comparison, not an independently novel method or full VMem speed measurement.',
            'S9 measured results informed this design. These 24 queries, two scenes, six maps are already seen; S7 includes development data.',
            'Five repetitions per query are dependent observations, not 120 independent queries or unseen validation.',
            'Only renderer binding changes. Full get_context_info is uninstrumented; both arms retain the same observer wrapper.',
            'Existing CPU environment and small dummy context arrays are reused; no model, GT, raw RGB/depth, or video execution.',
            '600-second alarm and 16-GiB peak-RSS checks are soft guards; other machine processes are not controlled.',
            'Five odd rounds give each query 2/3 or 3/2 AB/BA, while all measured pairs balance 60/60.'])
    save(output/'run_metadata.json', report)
    rows = []
    def budget():
        require(time.monotonic()-started <= 600, 'Ten-minute total budget exceeded')
        require(s9.peak_rss_bytes() <= 16*1024**3, '16-GiB soft peak-RSS budget exceeded')
    def alarm(signum, frame):
        raise TimeoutError('Ten-minute wall alarm; partial results remain')
    previous = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 600)
    try:
        protocol, freeze_path = args.protocol.resolve(strict=True), args.freeze.resolve(strict=True)
        prior_path = args.s9_freeze.resolve(strict=True)
        require(prior_path == ROOT/'docs/S9_COMPONENT_PROFILE_EXECUTION_FREEZE.json' and
                sha(prior_path) == S9_FREEZE_SHA, 'S9 historical freeze changed')
        prior, freeze = read(prior_path), read(freeze_path)
        require(freeze.get('schema') == 's10-renderer-comparison-freeze-v1' and
                freeze.get('status') == 'approved_for_execution', 'Root-approved execution freeze required')
        frozen_time = datetime.fromisoformat(freeze['frozen_utc'])
        require(frozen_time.tzinfo is not None and frozen_time <= datetime.fromisoformat(report['started_utc']),
                'Freeze must predate the new execution')
        require(freeze['s9_freeze_sha256'] == S9_FREEZE_SHA and sha(protocol) == freeze['protocol_sha256'],
                'Frozen protocol/prior-freeze identity mismatch')
        control_sha = {protocol:sha(protocol), freeze_path:sha(freeze_path), prior_path:sha(prior_path)}
        match = re.findall(r'```s10-comparison-json\s*\n(.*?)\n```', protocol.read_text(), re.S)
        require(len(match) == 1 and json.loads(match[0]) == CONTRACT, 'Protocol machine contract mismatch')
        require(set(freeze['execution_source_sha256']) == set(SOURCE_NAMES), 'Execution source domain mismatch')
        sources = {ROOT/name:digest for name,digest in freeze['execution_source_sha256'].items()}
        for path, digest in sources.items():
            require(sha(path) == digest, 'Frozen source changed: '+str(path))
        require(all(freeze['execution_source_sha256'][name] == prior['execution_source_sha256'][name]
                    for name in s9.SOURCE_NAMES), 'An unchanged S9 helper/source was modified')
        inputs = s9.expected_inputs(runs)
        input_sha = {str(p.relative_to(ROOT)):sha(p) for p in inputs}
        require(len(inputs) == len(input_sha) == 52 and input_sha == prior['input_sha256'] == freeze['input_sha256'],
                'S10 must use precisely the same 52 frozen S9 input files')
        report.update(protocol_sha256=sha(protocol), freeze_sha256=sha(freeze_path),
            s9_freeze_sha256=S9_FREEZE_SHA, input_sha256=input_sha,
            execution_source_sha256=freeze['execution_source_sha256'], inputs_sealed_utc=utc())
        with zipfile.ZipFile(output/'comparison_source.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sources:
                archive.write(path, str(path.relative_to(ROOT)))
            archive.write(protocol, 'frozen_protocol.md'); archive.write(freeze_path, 'execution_freeze.json')
            archive.write(prior_path, 'S9_execution_freeze.json')
        with zipfile.ZipFile(output/'sealed_comparison_inputs.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in inputs:
                archive.write(path, str(path.relative_to(ROOT)))
        sys.dont_write_bytecode = True
        sys.pycache_prefix = str(output/'unused_pycache')
        s9.install_io_guard(inputs, output)
        for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                    'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[key] = '8'
        os.environ['OMP_DYNAMIC'] = os.environ['MKL_DYNAMIC'] = 'FALSE'
        require('numpy' not in sys.modules and 'torch' not in sys.modules,
                'Numerical modules must be imported only after fixed thread settings')
        import numpy as np
        import torch
        torch.set_num_threads(8); torch.set_num_interop_threads(8)
        versions = dict(python=sys.version.split()[0], **{n:version(n) for n in ('numpy','torch','scipy')})
        require(versions == CONTRACT['versions'], 'Frozen package versions changed')
        require(torch.get_num_threads() == torch.get_num_interop_threads() == 8 and
                torch.get_default_dtype() == torch.float32, 'Torch threads/default sorting dtype changed')
        sys.path.insert(0, str(ROOT/'src'))
        names = ['s6_memory_bridge', 's7_event_replay', 'rgbd_memory', 'rgbd_retrieval',
                 'retrieval_diagnostic', 'vmem_memory_kernel', 'vmem_retrieval_kernel']
        modules = {n:importlib.import_module(n) for n in names}
        candidate_module = importlib.import_module('s10_vectorized_renderer')
        for name, module in {**modules, 's10_vectorized_renderer':candidate_module}.items():
            require(Path(module.__file__).resolve() == ROOT/'src'/f'{name}.py', 'Unexpected imported source location')
        original_function = modules['vmem_retrieval_kernel'].RetrievalKernel.render_surfels_to_image
        candidate_function = candidate_module.renderer_function()
        require(callable(candidate_function), 'Candidate factory must return an unbound renderer function')
        transformation = candidate_function.s10_transformation
        require(transformation['original_source_sha256'] == freeze['execution_source_sha256']['src/vmem_retrieval_kernel.py'] and
                transformation['helper_source_sha256'] == freeze['execution_source_sha256']['src/s10_vectorized_renderer.py'] and
                transformation['numpy'] == CONTRACT['versions']['numpy'] and
                transformation['replaced_nested_pixel_loops'] == 1 and
                transformation['restored_full_method_ast_identical'] is True,
                'Candidate transformation identity/scope differs from the reviewed version')
        save(output/'renderer_transformation.json', transformation)
        cases = s9.load_cases(runs, np, torch, modules, inputs)
        arms = dict(original=cases, candidate=copy.deepcopy(cases))
        identities = {}
        for method, collection in arms.items():
            wrapped = observed_renderer(original_function if method == 'original' else candidate_function)
            kernels = set()
            for case in collection:
                kernel = case['kernel']
                require(kernel.get_context_info.__func__ is modules['vmem_retrieval_kernel'].RetrievalKernel.get_context_info,
                        'Full context method must be the unchanged, uninstrumented original')
                if id(kernel) not in kernels:
                    kernel.render_surfels_to_image = MethodType(wrapped, kernel); kernels.add(id(kernel))
                identities[(method, case['label'])] = state_identity(case, np, modules['s6_memory_bridge'])
            require(len(kernels) == 6, 'Each arm must have exactly six independent block kernels')
        require(not ({id(c['kernel']) for c in arms['original']} & {id(c['kernel']) for c in arms['candidate']}),
                'Original and candidate must not share mutable kernels')
        require(all(identities[('original', c['label'])] == identities[('candidate', c['label'])] for c in cases),
                'Arms did not initialize to identical inputs/state')
        planned = schedule()
        save(output/'schedule.json', planned)
        report.update(environment=dict(versions=versions, python_executable=sys.executable,
            platform=dict(system=platform.system(), release=platform.release(), machine=platform.machine()),
            logical_cpus=os.cpu_count(), torch_threads=torch.get_num_threads(),
            torch_interop_threads=torch.get_num_interop_threads(), torch_default_dtype=str(torch.get_default_dtype()),
            native_thread_environment={k:v for k,v in os.environ.items() if k.endswith('_NUM_THREADS') or
                k in ('VECLIB_MAXIMUM_THREADS','OMP_DYNAMIC','MKL_DYNAMIC')}),
            initialization_completed_utc=utc(), initialization_elapsed_seconds=time.monotonic()-started,
            query_order=[c['label'] for c in cases], raw_pixels_decoded=False, gt_loaded=False, model_loaded=False)
        save(output/'run_metadata.json', report)
        with (output/'invocations.jsonl').open('x') as stream:
            for pair_index, pair in enumerate(planned):
                budget()
                if report['phase'] != pair['phase']:
                    if pair['phase'] == 'warmup':
                        require(len(rows) == 48 and all(r['exact_regression_passed'] for r in rows),
                                'All correctness calls must pass before warmup')
                        report['all_initial_correctness_passed_utc'] = utc()
                    if pair['phase'] == 'measured':
                        require(len(rows) == 96 and all(r['exact_regression_passed'] for r in rows),
                                'Full correctness and warmup must pass before measurement')
                        report['measurement_started_utc'] = utc()
                    report['phase'] = pair['phase']; save(output/'run_metadata.json', report)
                completed, pair_errors = [], []
                # Both calls finish before any output validation/hash/serialization.
                # Allocation outside get_context_info is excluded equally in both arms.
                for position, method in enumerate(pair['methods']):
                    case = arms[method][pair['query_index']]; kernel = case['kernel']
                    try:
                        if pair['phase'] == 'correctness':
                            result = kernel.get_context_info(case['target']); elapsed = None
                        else:
                            before = time.perf_counter_ns()
                            result = kernel.get_context_info(case['target'])
                            elapsed = time.perf_counter_ns()-before
                            require(elapsed > 0, 'Nonpositive measured duration')
                        completed.append((position, method, case, result, elapsed))
                    except Exception:
                        pair_errors.append(dict(method=method, operation='get_context_info', traceback=traceback.format_exc()))
                        break
                # Save every completed call's actual arrays before a regression can fail.
                payloads = []
                for position, method, case, result, elapsed in completed:
                    folder = output/'calls'/pair['phase']/f"round{pair['round']}"/pair['label']/method
                    folder.mkdir(parents=True, exist_ok=False)
                    np.savez_compressed(folder/'render.npz', **case['kernel'].last_render)
                    row = dict(pair_index=pair_index, phase=pair['phase'], round=pair['round'],
                        query_index=pair['query_index'], stage=pair['stage'], block=pair['block'], query=pair['query'],
                        label=pair['label'], method=method, position_in_pair=position,
                        pair_order='AB' if pair['methods'][0] == 'original' else 'BA', elapsed_ns=elapsed,
                        exact_regression_passed=False, render_path=str((folder/'render.npz').relative_to(output)),
                        trace_path=str((folder/'trace.json').relative_to(output)))
                    trace = dict(status='unverified', returned_ordered_ids=result['context_time_indices'].detach().cpu().tolist(),
                        observed_weights=[[int(k),float(v)] for k,v in case['kernel'].last_weights],
                        observed_counts=[[int(k),int(v)] for k,v in case['kernel'].last_counts],
                        render_arrays={k:array_identity(v,np) for k,v in case['kernel'].last_render.items()})
                    save(folder/'trace.json', trace)
                    payloads.append((case, result, folder, row, trace))
                for case, result, folder, row, trace in payloads:
                    try:
                        actual = s9.validate_output(case, result, np, modules, folder, 's10')
                        for name, expected_buffer in case['render'].items():
                            require(case['kernel'].last_render[name].tobytes(order='C') ==
                                    expected_buffer.tobytes(order='C'),
                                    'Rendered bytes differ, including signed zero: '+name)
                        require(state_identity(case,np,modules['s6_memory_bridge']) == identities[(row['method'],case['label'])],
                                'Renderer/retrieval mutated frozen case state')
                        trace.update(status='passed', **actual)
                        row['exact_regression_passed'] = True
                    except Exception:
                        trace.update(status='failed', traceback=traceback.format_exc())
                        pair_errors.append(dict(method=row['method'], operation='regression', traceback=trace['traceback']))
                    save(folder/'trace.json', trace)
                    row.update(render_sha256=sha(folder/'render.npz'), trace_sha256=sha(folder/'trace.json'))
                    rows.append(row); stream.write(json.dumps(row, allow_nan=False)+'\n'); stream.flush()
                if pair_errors:
                    save(output/f'failed_pair_{pair_index}.json', pair_errors)
                    raise ValueError('Paired call/regression failed; all completed-call arrays and partial traces retained')
                budget()
        require(len(rows) == 336 and all(r['exact_regression_passed'] for r in rows), 'Fixed 336-call schedule incomplete')
        require(sum(r['phase'] == 'correctness' for r in rows) == 48 and
                sum(r['phase'] == 'warmup' for r in rows) == 48 and
                sum(r['phase'] == 'measured' for r in rows) == 240, 'Phase invocation counts differ')
        for path, digest in sources.items():
            require(sha(path) == digest, 'Source changed during comparison')
        for path, digest in control_sha.items():
            require(sha(path) == digest, 'Protocol/execution freeze changed during comparison')
        require({str(p.relative_to(ROOT)):sha(p) for p in inputs} == input_sha, 'Original input bytes changed')
        for method, collection in arms.items():
            for case in collection:
                require(state_identity(case,np,modules['s6_memory_bridge']) == identities[(method,case['label'])],
                        'Final immutable input state differs')
        budget()
        save(output/'summary.json', summarize(rows))
        manifest = []
        for path in sorted((output/'calls').rglob('*')):
            if path.is_file():
                manifest.append(dict(path=str(path.relative_to(output)), bytes=path.stat().st_size, sha256=sha(path)))
        save(output/'call_artifact_manifest.json', manifest)
        require(sum(p['path'].endswith('/render.npz') for p in manifest) == 336 and
                sum(p['path'].endswith('/trace.json') for p in manifest) == 336,
                'Per-invocation evidence inventory incomplete')
        budget()
        report.update(status='completed', phase='complete', completed_invocations=336,
            correctness_invocations=48, warmup_invocations=48, measured_invocations=240, measured_pairs=120,
            distinct_seen_queries=24, maps_per_method=6, exact_output_regressions_passed=336,
            original_sources_unchanged=True, original_inputs_unchanged=True, in_memory_inputs_unchanged=True,
            all_call_render_arrays_saved=True, all_call_complete_traces_saved=True,
            source_archive_sha256=sha(output/'comparison_source.zip'),
            input_archive_sha256=sha(output/'sealed_comparison_inputs.zip'),
            renderer_transformation_sha256=sha(output/'renderer_transformation.json'),
            call_artifact_manifest_sha256=sha(output/'call_artifact_manifest.json'))
    except Exception:
        report.update(status='failed', traceback=traceback.format_exc(), completed_invocations=len(rows),
                      partial_measurements_valid_for_speed_claim=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)
        report.update(completed_utc=utc(), total_elapsed_seconds=time.monotonic()-started,
                      process_peak_rss_bytes=s9.peak_rss_bytes())
        save(output/'run_metadata.json', report)
    print(json.dumps({k:report.get(k) for k in ('status','phase','output','completed_utc',
        'completed_invocations','total_elapsed_seconds','process_peak_rss_bytes')}, ensure_ascii=False))
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
