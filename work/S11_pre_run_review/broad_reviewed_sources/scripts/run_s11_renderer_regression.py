#!/usr/bin/env python3
"""Frozen correctness-only extension on previously saved S7/S8 map variants.

Reuses S10 evidence for 24 conditions and executes the candidate exactly once
for each of the other 168. No performance timings, images, GT or model loading.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import signal
import sys
import time
import traceback
from types import MethodType
import zipfile

sys.dont_write_bytecode = True
import profile_s9_components as s9
import run_s10_renderer_comparison as s10

ROOT = Path(__file__).resolve().parents[1]
S10_FREEZE_SHA = 'db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204'
CANDIDATE_SHA = '3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521'
RUNS = {'S7': ROOT/'results/S7_event_replay', 'S8': ROOT/'results/S8_event_replay_v2'}
S10_RESULT = ROOT/'results/S10_renderer_comparison'
SOURCE_NAMES = (*s10.SOURCE_NAMES, 'scripts/run_s11_renderer_regression.py')
CONTRACT = dict(schema='s11-renderer-regression-v1', stages=['S7','S8'], blocks=[0,1,2],
    strides=[8,12], arms=['A0P0','A0P1','A1P0','A1P1'], queries=[20,21,22,23],
    width=160, history_count=20, context_count=4, full_conditions=192,
    inherited_conditions=24, new_candidate_invocations=168, new_candidate_maps=42,
    inherited_rule='stride8_A0P0_all_24_from_S10_correctness_candidate',
    order='stage_then_block_then_stride_then_arm_then_query',
    device='cpu', torch_threads=8, torch_interop_threads=8,
    versions=dict(python='3.12.14',numpy='2.3.5',torch='2.7.0',scipy='1.16.2'),
    wall_budget_seconds=600, peak_rss_budget_bytes=16*1024**3, resource_limit='soft',
    exact_C_bytes_gate=True, exact_complete_trace_gate=True, warmup_calls=0,
    performance_timing=False, original_renderer_calls=0, raw_pixels_allowed=False,
    gt_allowed=False, model_loading_allowed=False)
require, read, save, sha, utc = s9.require, s9.read, s9.save, s9.sha, s9.utc


def schedule():
    """Only enumerate conditions; no file, array, renderer or clock access."""
    result = []
    for stage in CONTRACT['stages']:
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                for arm in CONTRACT['arms']:
                    for query in CONTRACT['queries']:
                        inherited = stride == 8 and arm == 'A0P0'
                        result.append(dict(condition_index=len(result),stage=stage,block=block,
                            stride=stride,arm=arm,query=query,
                            label=f'{stage}_block{block}_stride{stride}_{arm}_query{query}',
                            evidence='inherited_S10' if inherited else 'new_candidate'))
    return result


def expected_inputs():
    """Exact original 316-file domain, including the 24 inherited references."""
    result = []
    for stage in CONTRACT['stages']:
        run = RUNS[stage]
        result += [run/'run_metadata.json',run/'records.json']
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                base = run/f'block{block}_stride{stride}'
                result += [base/'predicted_poses.npz',base/'prediction_only_selection.json']
                for arm in CONTRACT['arms']:
                    result += [base/f'{arm}.npz',base/f'{arm}_sources.json']
                    result += [base/f'query{q}_{arm}_render.npz' for q in CONTRACT['queries']]
    return result


def expected_s10_evidence():
    """Bind every previously completed call, without rerunning any of them."""
    result = [S10_RESULT/name for name in ('run_metadata.json','invocations.jsonl','schedule.json',
        'call_artifact_manifest.json','renderer_transformation.json','comparison_source.zip',
        'sealed_comparison_inputs.zip','summary.json')]
    for pair in s10.schedule():
        for method in pair['methods']:
            base = S10_RESULT/'calls'/pair['phase']/f"round{pair['round']}"/pair['label']/method
            result += [base/'render.npz',base/'trace.json']
    result += [ROOT/'results/S10_renderer_comparison_independent_review/verification.json',
               ROOT/'results/S10_renderer_comparison_audit_v2/verification.json']
    return result


def hashes(paths):
    require(all(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT) for p in paths),
            'Missing, symlinked or escaping input file')
    result = {str(p.relative_to(ROOT)):sha(p) for p in paths}
    require(len(result) == len(paths), 'Duplicate input paths')
    return result


def archive_files(path, items):
    """Archive and verify every member while all source paths remain read-only."""
    identities = {name:sha(source) for name,source in items.items()}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,source in items.items():
            z.write(source,name)
    with zipfile.ZipFile(path) as z:
        require(len(z.namelist()) == len(set(z.namelist())) and set(z.namelist()) == set(items),
                'Archive member domain changed')
        require(z.testzip() is None, 'Archive CRC failure')
        for name in items:
            require(hashlib.sha256(z.read(name)).hexdigest() == identities[name] == sha(items[name]),
                    'Archive or source bytes changed: '+name)
    return sha(path)


def validate_s10_history(prior, evidence_sha):
    meta = read(S10_RESULT/'run_metadata.json')
    require(meta['status'] == 'completed' and meta['phase'] == 'complete' and
            meta['completed_invocations'] == meta['exact_output_regressions_passed'] == 336,
            'S10 must be completely successful')
    require(meta['freeze_sha256'] == S10_FREEZE_SHA and meta['protocol_sha256'] == prior['protocol_sha256'] and
            meta['execution_source_sha256'] == prior['execution_source_sha256'] and
            meta['input_sha256'] == prior['input_sha256'], 'S10 predecessor identity differs')
    for filename,field in (('comparison_source.zip','source_archive_sha256'),
        ('sealed_comparison_inputs.zip','input_archive_sha256'),
        ('renderer_transformation.json','renderer_transformation_sha256'),
        ('call_artifact_manifest.json','call_artifact_manifest_sha256')):
        require(sha(S10_RESULT/filename) == meta[field], 'S10 archive/manifest identity changed')
    require(read(ROOT/'results/S10_renderer_comparison_independent_review/verification.json')['status'] == 'PASS',
            'S10 different-author review must pass')
    require(read(ROOT/'results/S10_renderer_comparison_audit_v2/verification.json')['status'] == 'passed',
            'S10 different-script audit must pass')
    planned = s10.schedule()
    require(read(S10_RESULT/'schedule.json') == json.loads(json.dumps(planned)), 'S10 saved schedule differs')
    rows = [json.loads(line) for line in (S10_RESULT/'invocations.jsonl').read_text().splitlines()]
    require(len(rows) == 336, 'S10 must retain all 336 invocation records')
    manifest = read(S10_RESULT/'call_artifact_manifest.json')
    inventory = {x['path']:x for x in manifest}
    actual_paths = {str(p.relative_to(S10_RESULT)) for p in (S10_RESULT/'calls').rglob('*') if p.is_file()}
    require(len(manifest) == len(inventory) == 672 and set(inventory) == actual_paths,
            'S10 actual calls directory has missing/extra files')
    chosen = {}
    for ordinal,row in enumerate(rows):
        index,position = divmod(ordinal,2); pair = planned[index]
        require(row['pair_index'] == index and row['position_in_pair'] == position and
                row['method'] == pair['methods'][position] and row['exact_regression_passed'] is True,
                'S10 invocation position/status differs')
        for key in ('phase','round','query_index','stage','block','query','label'):
            require(row[key] == pair[key], 'S10 invocation schedule mismatch: '+key)
        base = f"calls/{row['phase']}/round{row['round']}/{row['label']}/{row['method']}/"
        for kind,suffix in (('render','render.npz'),('trace','trace.json')):
            relative = base+suffix; path = S10_RESULT/relative
            require(row[kind+'_path'] == relative and relative in inventory,
                    'S10 invocation result path differs')
            require(row[kind+'_sha256'] == inventory[relative]['sha256'] ==
                    evidence_sha[str(path.relative_to(ROOT))] and
                    inventory[relative]['bytes'] == path.stat().st_size, 'S10 result SHA/size differs')
        if row['phase'] == 'correctness' and row['method'] == 'candidate':
            chosen[(row['stage'],row['block'],row['query'])] = row
    require(len(chosen) == 24, 'Exactly 24 S10 initial candidate conditions are inherited')
    return chosen


def load_references(inputs, np):
    """Read the sealed variant references; do not initialize or execute renderers."""
    refs, cases = {}, {}
    for stage,run in RUNS.items():
        meta = read(run/'run_metadata.json')
        require(meta['status'] == 'completed' and meta['phase'] == 'complete', 'Prior replay incomplete')
        for name in s9.SOURCE_NAMES:
            if name.startswith('src/'):
                require(sha(ROOT/name) == meta['source_sha256'][name], 'Historical source changed')
        records = read(run/'records.json')
        indexed = {(r['block'],r['stride'],r['frame']):r for r in records}
        require(len(indexed) == len(records), 'Duplicate original records')
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                base = run/f'block{block}_stride{stride}'
                seals = [x for x in meta['cases'] if x['block'] == block and x['stride'] == stride]
                require(len(seals) == 1 and seals[0]['directory'] == base.name, 'Prior case domain differs')
                for path in inputs:
                    if path.parent == base:
                        require(sha(path) == seals[0]['sealed_files'][path.name], 'Prior case seal differs')
                selection = read(base/'prediction_only_selection.json')
                require(selection['block'] == block and selection['stride'] == stride and selection['width'] == 160 and
                        [q['frame'] for q in selection['queries']] == [20,21,22,23] and
                        set(selection['maps']) == set(CONTRACT['arms']), 'Prior case configuration differs')
                cases[(stage,block,stride)] = dict(base=base,selection=selection)
                for item in selection['queries']:
                    require(set(item['maps']) == set(CONTRACT['arms']), 'Prior query arm domain differs')
                    query = item['frame']
                    for arm in CONTRACT['arms']:
                        expected = item['maps'][arm]
                        require(expected['official_trace']['selected'] ==
                            indexed[(block,stride,query)]['readouts'][arm]['official']['selected'],
                            'Selection/records ordered IDs differ')
                        with np.load(base/f'query{query}_{arm}_render.npz',allow_pickle=False) as z:
                            render = {k:z[k] for k in z.files}
                        require(set(render) == {'depth','surfel_index_map','cos_value_map'} and
                            all(a.shape == (160,160) and np.isfinite(a).all() for a in render.values()),
                            'Invalid saved reference buffer')
                        refs[(stage,block,stride,arm,query)] = dict(expected=expected,render=render)
    require(len(refs) == 192 and len(cases) == 12, 'Expected 192 reference conditions and 12 saved cases')
    return refs,cases


def exact_buffers(actual, expected, np):
    require(set(actual) == set(expected), 'Rendered array keys differ')
    for name,value in expected.items():
        a = actual[name]
        require(a.dtype == value.dtype and a.shape == value.shape and
                a.tobytes(order='C') == value.tobytes(order='C'), 'Rendered C bytes differ: '+name)


def bind_inherited(chosen, references, np, output):
    result = []
    for condition in schedule():
        if condition['evidence'] != 'inherited_S10':
            continue
        stage,block,query = condition['stage'],condition['block'],condition['query']
        row = chosen[(stage,block,query)]; reference = references[(stage,block,8,'A0P0',query)]
        with np.load(S10_RESULT/row['render_path'],allow_pickle=False) as z:
            arrays = {k:z[k] for k in z.files}
        trace = read(S10_RESULT/row['trace_path'])
        exact_buffers(arrays,reference['render'],np)
        expected = reference['expected']
        require(trace['status'] == 'passed' and trace['official_trace'] == expected['official_trace'] and
                trace['official_decision'] == expected['readouts']['official'] and
                trace['returned_ordered_ids'] == expected['official_trace']['selected'] and
                trace['observed_weights'] == expected['official_trace']['weights'] and
                trace['observed_counts'] == expected['official_trace']['candidate_counts'],
                'Inherited S10 output/complete trace differs from original reference')
        require(trace['render_arrays'] == {k:s10.array_identity(a,np) for k,a in arrays.items()},
                'Inherited trace array identities differ')
        result.append(dict(**condition,status='passed',new_renderer_call=False,
            prior_pair_index=row['pair_index'],prior_method='candidate',prior_phase='correctness',
            render_path=str((S10_RESULT/row['render_path']).relative_to(ROOT)),render_sha256=row['render_sha256'],
            trace_path=str((S10_RESULT/row['trace_path']).relative_to(ROOT)),trace_sha256=row['trace_sha256']))
    require(len(result) == 24, 'Inherited coverage incomplete')
    save(output/'inherited_coverage.json',result)
    return result


def load_new_cases(references, saved_cases, np, torch, modules):
    """New S11 loader: same S9 construction, widened arm/stride domain only."""
    bridge,events,retrieval = (modules[n] for n in ('s6_memory_bridge','s7_event_replay','rgbd_retrieval'))
    Memory,Surfel = modules['rgbd_memory'].Memory,modules['vmem_memory_kernel'].Surfel
    kernels,poses_by_case = {},{}
    result = []
    for condition in schedule():
        if condition['evidence'] == 'inherited_S10':
            continue
        stage,block,stride,arm,query = (condition[k] for k in ('stage','block','stride','arm','query'))
        key = (stage,block,stride); map_key = (*key,arm)
        source = saved_cases[key]; base,selection = source['base'],source['selection']
        if key not in poses_by_case:
            with np.load(base/'predicted_poses.npz',allow_pickle=False) as z:
                require(z.files == ['poses'], 'Pose archive schema differs')
                poses = z['poses']
            require(poses.shape == (24,4,4) and np.isfinite(poses).all(), 'Invalid saved poses')
            poses_by_case[key] = poses
        poses = poses_by_case[key]
        if map_key not in kernels:
            with np.load(base/f'{arm}.npz',allow_pickle=False) as z:
                values = {k:z[k] for k in z.files}
            require(set(values) == {'points','normals','radii','colors','counts'}, 'Map schema differs')
            count = len(values['points'])
            require(values['points'].shape == values['normals'].shape == values['colors'].shape == (count,3) and
                values['radii'].shape == values['counts'].shape == (count,) and
                all(np.isfinite(v).all() for v in values.values()), 'Invalid saved map arrays')
            mapping = {int(k):v for k,v in read(base/f'{arm}_sources.json').items()}
            require(set(mapping) == set(range(count)) and all(isinstance(v,list) and v and
                all(type(i) is int and 0 <= i < 20 for i in v) for v in mapping.values()), 'Invalid saved source domain')
            memory = Memory(surfels=[Surfel(p.copy(),n.copy(),float(r),c.copy()) for p,n,r,c in
                zip(values['points'],values['normals'],values['radii'],values['colors'])],
                counts=values['counts'].tolist(),mapping=mapping)
            for name,array in events.arrays(memory).items():
                require(array.dtype == values[name].dtype and array.shape == values[name].shape and
                    array.tobytes(order='C') == values[name].tobytes(order='C'), 'Loading altered map bytes: '+name)
            require(bridge.memory_digest(memory) == selection['maps'][arm]['digest'], 'Map memory digest differs')
            kernel = bridge.make_selector(memory,poses[:20],width=160)
            kernels[map_key] = (kernel,memory,count)
        kernel,memory,count = kernels[map_key]
        reference = references[(stage,block,stride,arm,query)]
        require(kernel.initial_threshold == reference['expected']['official_trace']['nms_initial_threshold'],
                'Original NMS initialization differs')
        result.append(dict(**condition,kernel=kernel,memory=memory,
            memory_digest=selection['maps'][arm]['digest'],pose=poses[query].copy(),
            target=torch.tensor(retrieval.optical_to_vmem(poses[query])[None],dtype=torch.float64),
            expected=reference['expected'],render=reference['render'],map_points=count))
    require(len(result) == 168 and len(kernels) == 42 and len({id(c['kernel']) for c in result}) == 42,
            'New candidate domain must be exactly 168 calls on 42 maps')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('protocol','freeze','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    raw = args.output.absolute()
    require(not raw.exists() and not raw.is_symlink(), 'Fresh output required; preserve failed directories')
    output = raw.resolve()
    require(not any(output.is_relative_to(ROOT/name) for name in ('src','scripts','docs','data','vendor')),
            'Output overlaps protected material')
    require(not any(output.is_relative_to(p) for p in (*RUNS.values(),S10_RESULT,
        ROOT/'results/S9_component_profile',ROOT/'results/S10_renderer_comparison_audit_v2',
        ROOT/'results/S10_renderer_comparison_independent_review')), 'Output overlaps prior evidence')
    output.mkdir(parents=True,exist_ok=False)
    started = time.monotonic()  # Total soft budget only; never a per-call performance timer.
    report = dict(status='running',phase='preflight',started_utc=utc(),output=str(output),contract=CONTRACT,
        limitations=[
            'Correctness-only extension on already seen map variants, not unseen-scene or independent-query evidence.',
            '192 conditions concern the same 24 related queries from two scenes; S7 includes development data.',
            '24 initial S10 candidate outputs are inherited; only the other 168 candidate calls execute now.',
            'No original renderer, performance comparison, warmup, PNG, GT, model or video is executed.',
            'The existing CPU environment and dummy context arrays are reused; 600s/16GiB guards are soft.',
            'Only the frozen renderer binding changes; loading and diagnostics reuse unchanged S9/S10 helpers.'])
    save(output/'run_metadata.json',report)
    rows = []
    def budget():
        require(time.monotonic()-started <= 600, '600-second total soft budget exceeded')
        require(s9.peak_rss_bytes() <= 16*1024**3, '16-GiB soft peak-RSS budget exceeded')
    def alarm(signum,frame):
        raise TimeoutError('600-second soft wall alarm; partial evidence remains')
    previous = signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,600)
    try:
        protocol,freeze_path = args.protocol.resolve(strict=True),args.freeze.resolve(strict=True)
        prior_path = ROOT/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json'
        require(sha(prior_path) == S10_FREEZE_SHA, 'S10 predecessor freeze changed')
        prior,freeze = read(prior_path),read(freeze_path)
        require(freeze.get('schema') == 's11-renderer-regression-freeze-v1' and
                freeze.get('status') == 'approved_for_execution', 'Root-approved S11 execution freeze required')
        frozen_time = datetime.fromisoformat(freeze['frozen_utc'])
        require(frozen_time.tzinfo is not None and frozen_time <= datetime.fromisoformat(report['started_utc']),
                'S11 freeze must predate execution')
        require(freeze['s10_freeze_sha256'] == S10_FREEZE_SHA and sha(protocol) == freeze['protocol_sha256'],
                'Frozen protocol/predecessor identity mismatch')
        match = re.findall(r'```s11-regression-json\s*\n(.*?)\n```',protocol.read_text(),re.S)
        require(len(match) == 1 and json.loads(match[0]) == CONTRACT, 'Protocol machine contract mismatch')
        require(set(freeze['execution_source_sha256']) == set(SOURCE_NAMES), 'Execution source domain differs')
        source_paths = [ROOT/name for name in SOURCE_NAMES]
        source_sha = hashes(source_paths)
        require(source_sha == freeze['execution_source_sha256'], 'Frozen execution source changed')
        require(all(source_sha[name] == prior['execution_source_sha256'][name] for name in s10.SOURCE_NAMES) and
                source_sha['src/s10_vectorized_renderer.py'] == CANDIDATE_SHA, 'Any S10 source/candidate change is forbidden')
        inputs,evidence = expected_inputs(),expected_s10_evidence()
        input_sha,evidence_sha = hashes(inputs),hashes(evidence)
        require(len(input_sha) == 316 and input_sha == freeze['input_sha256'], 'S11 input identity/domain differs')
        require(len(evidence_sha) == 682 and evidence_sha == freeze['s10_evidence_sha256'], 'S10 evidence identity/domain differs')
        require(all(input_sha[name] == digest for name,digest in prior['input_sha256'].items()),
                'Previously profiled 52 inputs changed')
        review_sha = freeze.get('review_evidence_sha256',{})
        require(isinstance(review_sha,dict) and review_sha, 'Pre-run review evidence must be sealed')
        review_paths = [ROOT/name for name in review_sha]
        require(hashes(review_paths) == review_sha, 'Pre-run review evidence changed')
        controls = {protocol:sha(protocol),freeze_path:sha(freeze_path),prior_path:sha(prior_path)}
        chosen = validate_s10_history(prior,evidence_sha)
        report.update(protocol_sha256=sha(protocol),freeze_sha256=sha(freeze_path),
            s10_freeze_sha256=S10_FREEZE_SHA,execution_source_sha256=source_sha,
            input_sha256=input_sha,s10_evidence_sha256=evidence_sha,review_evidence_sha256=review_sha,
            inputs_sealed_utc=utc(),planned_conditions=192,new_planned_invocations=168,inherited_planned_conditions=24)
        save(output/'run_metadata.json',report)
        archive_source = {str(p.relative_to(ROOT)):p for p in source_paths}
        archive_source.update({'frozen_protocol.md':protocol,'execution_freeze.json':freeze_path,
                               'S10_execution_freeze.json':prior_path})
        report['source_archive_sha256'] = archive_files(output/'regression_source.zip',archive_source)
        report['input_archive_sha256'] = archive_files(output/'sealed_regression_inputs.zip',
            {str(p.relative_to(ROOT)):p for p in inputs})
        report['s10_evidence_archive_sha256'] = archive_files(output/'inherited_S10_evidence.zip',
            {str(p.relative_to(ROOT)):p for p in evidence})
        report['review_evidence_archive_sha256'] = archive_files(output/'sealed_review_evidence.zip',
            {str(p.relative_to(ROOT)):p for p in review_paths})
        save(output/'schedule.json',schedule()); save(output/'run_metadata.json',report)
        sys.dont_write_bytecode = True; sys.pycache_prefix = str(output/'unused_pycache')
        s9.install_io_guard([*inputs,*evidence,*review_paths],output)
        for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
            os.environ[key] = '8'
        os.environ['OMP_DYNAMIC'] = os.environ['MKL_DYNAMIC'] = 'FALSE'
        require('numpy' not in sys.modules and 'torch' not in sys.modules, 'Set threads before numerical imports')
        import numpy as np
        import torch
        torch.set_num_threads(8); torch.set_num_interop_threads(8)
        versions = dict(python=sys.version.split()[0],**{n:version(n) for n in ('numpy','torch','scipy')})
        require(versions == CONTRACT['versions'] and torch.get_num_threads() == torch.get_num_interop_threads() == 8 and
                torch.get_default_dtype() == torch.float32, 'Frozen numerical/thread environment differs')
        report['environment'] = dict(versions=versions,python_executable=sys.executable,
            platform=dict(system=platform.system(),release=platform.release(),machine=platform.machine()),
            torch_threads=8,torch_interop_threads=8,torch_default_dtype=str(torch.get_default_dtype()),
            native_thread_environment={k:v for k,v in os.environ.items() if k.endswith('_NUM_THREADS') or
                k in ('VECLIB_MAXIMUM_THREADS','OMP_DYNAMIC','MKL_DYNAMIC')})
        references,saved_cases = load_references(inputs,np)
        inherited = bind_inherited(chosen,references,np,output)
        report.update(inherited_24_verified_utc=utc(),phase='initialize_new_cases')
        save(output/'run_metadata.json',report)
        sys.path.insert(0,str(ROOT/'src'))
        module_names = ('s6_memory_bridge','s7_event_replay','rgbd_memory','rgbd_retrieval',
                        'retrieval_diagnostic','vmem_memory_kernel','vmem_retrieval_kernel')
        modules = {name:importlib.import_module(name) for name in module_names}
        candidate_module = importlib.import_module('s10_vectorized_renderer')
        for name,module in {**modules,'s10_vectorized_renderer':candidate_module}.items():
            require(Path(module.__file__).resolve() == ROOT/'src'/f'{name}.py', 'Unexpected imported source location')
        candidate = candidate_module.renderer_function()
        transform = candidate.s10_transformation
        require(transform['helper_source_sha256'] == CANDIDATE_SHA and
                transform['original_source_sha256'] == source_sha['src/vmem_retrieval_kernel.py'] and
                transform['numpy'] == '2.3.5' and transform['replaced_nested_pixel_loops'] == 1 and
                transform['restored_full_method_ast_identical'] is True, 'Frozen candidate transformation differs')
        require(transform == read(S10_RESULT/'renderer_transformation.json'), 'S10 transformation record differs')
        save(output/'renderer_transformation.json',transform)
        cases = load_new_cases(references,saved_cases,np,torch,modules)
        wrapped = s10.observed_renderer(candidate); bound = set(); identities = {}
        for case in cases:
            kernel = case['kernel']
            require(kernel.get_context_info.__func__ is modules['vmem_retrieval_kernel'].RetrievalKernel.get_context_info,
                    'Full get_context_info must remain unchanged and uninstrumented')
            if id(kernel) not in bound:
                kernel.render_surfels_to_image = MethodType(wrapped,kernel); bound.add(id(kernel))
            identities[case['label']] = s10.state_identity(case,np,modules['s6_memory_bridge'])
        require(len(bound) == 42, 'Unexpected initialized candidate map count')
        save(output/'initial_state_identities.json',identities)
        report.update(initialization_completed_utc=utc(),phase='candidate_correctness',
            raw_pixels_decoded=False,gt_loaded=False,model_loaded=False,performance_measured=False,
            original_renderer_calls=0,new_candidate_calls_started=0)
        save(output/'run_metadata.json',report)
        with (output/'invocations.jsonl').open('x') as stream:
            for invocation,case in enumerate(cases):
                budget(); folder = output/'calls'/case['label']; folder.mkdir(parents=True,exist_ok=False)
                row = {k:case[k] for k in ('condition_index','stage','block','stride','arm','query','label','evidence')}
                row.update(invocation_index=invocation,method='candidate',status='unverified')
                kernel = case['kernel']; kernel.last_render = None
                report['new_candidate_calls_started'] = invocation+1
                save(output/'run_metadata.json',report)
                try:
                    # No per-call clock: this is only a correctness invocation.
                    result = kernel.get_context_info(case['target'])
                    np.savez_compressed(folder/'render.npz',**kernel.last_render)
                    trace = dict(status='unverified',returned_ordered_ids=result['context_time_indices'].detach().cpu().tolist(),
                        observed_weights=[[int(k),float(v)] for k,v in kernel.last_weights],
                        observed_counts=[[int(k),int(v)] for k,v in kernel.last_counts],
                        render_arrays={k:s10.array_identity(v,np) for k,v in kernel.last_render.items()})
                    save(folder/'trace.json',trace)
                    actual = s9.validate_output(case,result,np,modules,folder,'s11')
                    exact_buffers(kernel.last_render,case['render'],np)
                    after = s10.state_identity(case,np,modules['s6_memory_bridge'])
                    require(after == identities[case['label']], 'Candidate mutated frozen case state')
                    trace.update(status='passed',**actual,state_after=after,
                        state_before_sha256=hashlib.sha256(json.dumps(identities[case['label']],sort_keys=True).encode()).hexdigest())
                    save(folder/'trace.json',trace); row['status'] = 'passed'
                except Exception:
                    row.update(status='failed',traceback=traceback.format_exc())
                    # Preserve a renderer return even when a later selector operation failed.
                    if kernel.last_render is not None and not (folder/'render.npz').exists():
                        np.savez_compressed(folder/'render.npz',**kernel.last_render)
                    save(folder/'failure.json',row)
                for kind in ('render','trace'):
                    path = folder/('render.npz' if kind == 'render' else 'trace.json')
                    if path.exists():
                        row[kind+'_path'] = str(path.relative_to(output)); row[kind+'_sha256'] = sha(path)
                rows.append(row); stream.write(json.dumps(row,allow_nan=False)+'\n'); stream.flush()
                require(row['status'] == 'passed', 'Candidate correctness failure; actual/partial evidence retained')
                budget()
        require(len(rows) == 168 and all(r['status'] == 'passed' for r in rows), '168-call regression incomplete')
        for case in cases:
            require(s10.state_identity(case,np,modules['s6_memory_bridge']) == identities[case['label']],
                    'Final in-memory input state changed')
        require(hashes(source_paths) == source_sha and hashes(inputs) == input_sha and
                hashes(evidence) == evidence_sha and hashes(review_paths) == review_sha,
                'Original source, input or inherited evidence changed')
        require(all(sha(path) == digest for path,digest in controls.items()), 'Protocol/freeze changed')
        coverage = sorted([*inherited,*rows],key=lambda x:x['condition_index'])
        require([r['condition_index'] for r in coverage] == list(range(192)), 'Full coverage has gaps/duplicates')
        save(output/'coverage.json',coverage)
        manifest = [dict(path=str(p.relative_to(output)),bytes=p.stat().st_size,sha256=sha(p))
                    for p in sorted((output/'calls').rglob('*')) if p.is_file()]
        require(len(manifest) == 336 and sum(p['path'].endswith('/render.npz') for p in manifest) == 168 and
                sum(p['path'].endswith('/trace.json') for p in manifest) == 168, 'Actual call evidence incomplete')
        save(output/'call_artifact_manifest.json',manifest)
        save(output/'summary.json',dict(status='passed',full_conditions=192,new_candidate_invocations=168,
            inherited_conditions=24,distinct_seen_queries=24,physical_scenes=2,original_map_variants=48,
            new_candidate_maps=42,all_exact_output_checks_passed=True,performance_measured=False,
            limitations=report['limitations']))
        budget()
        report.update(status='completed',phase='complete',completed_new_invocations=168,
            inherited_conditions=24,covered_conditions=192,distinct_seen_queries=24,new_candidate_maps=42,
            source_inputs_inherited_evidence_unchanged=True,in_memory_inputs_unchanged=True,
            all_actual_arrays_and_complete_traces_saved=True,
            call_artifact_manifest_sha256=sha(output/'call_artifact_manifest.json'),
            coverage_sha256=sha(output/'coverage.json'),summary_sha256=sha(output/'summary.json'),
            renderer_transformation_sha256=sha(output/'renderer_transformation.json'),
            initial_state_identities_sha256=sha(output/'initial_state_identities.json'))
    except Exception:
        report.update(status='failed',traceback=traceback.format_exc(),
            completed_new_invocations=sum(r['status'] == 'passed' for r in rows),
            partial_results_establish_full_coverage=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0); signal.signal(signal.SIGALRM,previous)
        report.update(completed_utc=utc(),wall_elapsed_for_budget_seconds=time.monotonic()-started,
                      process_peak_rss_bytes=s9.peak_rss_bytes())
        save(output/'run_metadata.json',report)
    print(json.dumps({k:report.get(k) for k in ('status','phase','output','completed_utc',
        'completed_new_invocations','inherited_conditions','covered_conditions')},ensure_ascii=False))
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
