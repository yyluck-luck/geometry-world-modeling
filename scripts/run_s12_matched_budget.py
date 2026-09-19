#!/usr/bin/env python3
"""Frozen, exploratory pose14 comparison on already observed S7/S8 queries.

Only 24 new decision_trace calls. No renderer, model, raw RGB/depth or GT pose
loading. Saved support/valid fields are decoded after all new choices are sealed.
Imports of numerical dependencies occur only inside the frozen execution path.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import re
import resource
import signal
import sys
import time
import traceback
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUNS = {'S7': ROOT/'results/S7_event_replay', 'S8': ROOT/'results/S8_event_replay_v2'}
SOURCE_PINS = {
    'src/vmem_retrieval_kernel.py': '35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3',
    'src/s7_event_replay.py': '3f4028366d1cf1fdcca8744a0cb14690075b9b146bd71af88360afa74bc5e20d',
    'src/rgbd_retrieval.py': '6f5188f7f72b66e93af27ab5a368cd09fcea2166715f1bf4cd0545a686ec3cd6',
}
SOURCE_NAMES = (*SOURCE_PINS, 'scripts/run_s12_matched_budget.py')
CONTRACT = dict(
    schema='s12-matched-budget-v1', stages=['S7', 'S8'], blocks=[0, 1, 2],
    queries=[20, 21, 22, 23], strides=[8, 12], arms=['A0P0', 'A0P1', 'A1P0', 'A1P1'],
    readouts=['official', 'candidate_no_nms', 'all20_nms', 'all20_no_nms'],
    unique_queries=24, new_decision_trace_calls=24, old_decision_trace_calls=0,
    history_count=20, candidate_count=14, context_count=4, input_files=76,
    execution_sources=4, scoring_files=48, old_readout_scores=768,
    old_all20_upper_bounds=48, paired_map_conditions=192,
    main_arm='A0P0', main_stride=8, difference='geometry14_minus_pose14_percentage_points',
    reporting_strata=['S7_development_4', 'S7_test_8', 'S8_test_12'],
    selection_order='stage_then_block_then_query', translation_weight=0.1,
    distance_dtype='float64', sorting_dtype='float32', sort='torch_default_argsort_no_ties',
    candidate_counts='nearest14_set_then_frame_id_ascending_each_count1',
    initial_threshold='original_first5_10_pairs_sorted_index5',
    all_choices_sealed_before_scoring_decode=True, exact_old_score_gate=True,
    device='cpu', torch_threads=8, torch_interop_threads=8,
    versions=dict(python='3.12.14', numpy='2.3.5', torch='2.7.0', scipy='1.16.2'),
    wall_budget_seconds=600, peak_rss_budget_bytes=16*1024**3, resource_limit='soft',
    performance_timing=False, renderer_calls=0, model_calls=0,
    raw_pixels_allowed=False, gt_pose_values_allowed=False,
    scope='exploratory_matched_candidate_budget_on_24_seen_queries',
)


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for part in iter(lambda: handle.read(1024*1024), b''):
            digest.update(part)
    return digest.hexdigest()


def schedule():
    """Pure fixed query enumeration; does not construct any candidate set."""
    return [dict(stage=s, block=b, query=q,
                 split='development' if s == 'S7' and b == 0 else 'test',
                 label=f'{s}_block{b}_query{q}')
            for s in CONTRACT['stages'] for b in CONTRACT['blocks'] for q in CONTRACT['queries']]


def expected_inputs():
    paths = []
    for run in RUNS.values():
        paths += [run/'run_metadata.json', run/'records.json']
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                base = run/f'block{block}_stride{stride}'
                paths += [base/'predicted_poses.npz', base/'prediction_only_selection.json']
                paths += [base/f'query{q}_scoring.npz' for q in CONTRACT['queries']]
    return paths


def file_hashes(paths):
    values = {}
    for path in paths:
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT),
                f'Missing, symlinked or escaping source/input: {path}')
        name = str(path.relative_to(ROOT))
        require(name not in values, f'Duplicate file: {name}')
        values[name] = sha(path)
    return values


def archive(path, identities):
    """Copy original bytes, then verify every ZIP member and its CRC."""
    manifest = {}
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as package:
        for name, digest in identities.items():
            data = (ROOT/name).read_bytes()
            require(hashlib.sha256(data).hexdigest() == digest, f'Source changed during archive: {name}')
            package.writestr(name, data)
            manifest[name] = dict(sha256=digest, bytes=len(data))
    with zipfile.ZipFile(path) as package:
        require(package.testzip() is None, f'ZIP CRC failure: {path.name}')
        require(package.namelist() == list(identities), 'ZIP member domain/order differs')
        for name, item in manifest.items():
            data = package.read(name)
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                    f'ZIP member mismatch: {name}')
    save(path.with_suffix('.manifest.json'), manifest)
    return dict(path=path.name, sha256=sha(path), bytes=path.stat().st_size,
                members=len(manifest), manifest_sha256=sha(path.with_suffix('.manifest.json')))


def extract_functions():
    """Source-only AST extraction; no import/execute of the original modules."""
    requests = [
        ('src/vmem_retrieval_kernel.py', None, 'average_camera_pose'),
        ('src/vmem_retrieval_kernel.py', 'RetrievalKernel', 'geodesic_distance'),
        ('src/rgbd_retrieval.py', None, 'optical_to_vmem'),
        ('src/rgbd_retrieval.py', None, 'initial_nms_threshold'),
        ('src/s7_event_replay.py', None, 'decision_trace'),
    ]
    snippets, receipt = [], []
    for filename, classname, name in requests:
        text = (ROOT/filename).read_text()
        module = ast.parse(text)
        body = module.body
        if classname:
            classes = [node for node in body if isinstance(node, ast.ClassDef) and node.name == classname]
            require(len(classes) == 1, f'Missing original class: {classname}')
            body = classes[0].body
        functions = [node for node in body if isinstance(node, ast.FunctionDef) and node.name == name]
        require(len(functions) == 1, f'Missing original function: {name}')
        node = functions[0]
        require(not node.decorator_list, f'Unexpected decorator: {name}')
        original_span = ''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
        # Unparse the original node instead of dedenting its text: dedent would
        # alter whitespace inside the method's docstring. Verify the complete
        # function AST, including that literal, before compiling anything.
        snippet = ast.unparse(node)+'\n'
        original_ast = ast.dump(node, include_attributes=False)
        require(ast.dump(ast.parse(snippet).body[0], include_attributes=False) == original_ast,
                f'Unparsed original function AST differs: {name}')
        snippets.append(snippet.rstrip()+'\n')
        receipt.append(dict(path=filename, owner=classname, name=name, first_line=node.lineno,
                            last_line=node.end_lineno, source_sha256=sha(ROOT/filename),
                            original_span_sha256=hashlib.sha256(original_span.encode()).hexdigest(),
                            extracted_source_sha256=hashlib.sha256(snippet.encode()).hexdigest(),
                            original_ast_sha256=hashlib.sha256(original_ast.encode()).hexdigest()))
    combined = '\n'.join(snippets)
    assembled = ast.parse(combined)
    require(len(assembled.body) == 5 and all(isinstance(n, ast.FunctionDef) for n in assembled.body),
            'Extracted module may contain only the five functions')
    for node, item in zip(assembled.body, receipt):
        require(hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
                == item['original_ast_sha256'], f'Extracted AST changed: {node.name}')
    return combined, receipt


def array_identity(array):
    return dict(dtype=str(array.dtype), shape=list(array.shape),
                c_bytes_sha256=hashlib.sha256(array.tobytes(order='C')).hexdigest())


def check_budget(started):
    elapsed = time.monotonic()-started
    # ru_maxrss is bytes on macOS, KiB on Linux. This is an observed soft guard,
    # not an OS memory cap, environment sandbox, or performance measurement.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    require(elapsed <= CONTRACT['wall_budget_seconds'], 'Wall-clock soft budget exceeded')
    require(peak <= CONTRACT['peak_rss_budget_bytes'], 'Peak RSS soft budget exceeded')
    return int(peak)


def timeout_handler(signum, frame):
    raise TimeoutError('600-second process wall-clock budget exceeded')


def load_prediction_inputs(np, input_sha):
    """Only saved predicted poses and saved choices; no scoring field access."""
    cases, poses = {}, {}
    for stage, run in RUNS.items():
        metadata = read(run/'run_metadata.json')
        require(metadata['status'] == 'completed' and len(metadata['cases']) == 6,
                f'Original run incomplete: {stage}')
        for name, digest in SOURCE_PINS.items():
            require(metadata['source_sha256'][name] == digest, f'Original source differs: {stage}/{name}')
        seals = {(c['block'], c['stride']): c for c in metadata['cases']}
        require(len(seals) == 6, 'Original case domain duplicated')
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                base = run/f'block{block}_stride{stride}'
                seal = seals[block, stride]
                require(seal['directory'] == base.name, 'Old case directory mismatch')
                for filename in ('predicted_poses.npz', 'prediction_only_selection.json'):
                    require(input_sha[str((base/filename).relative_to(ROOT))] == seal['sealed_files'][filename],
                            f'Original selection seal differs: {stage}/{base.name}/{filename}')
                with np.load(base/'predicted_poses.npz', allow_pickle=False) as package:
                    require(package.files == ['poses'], 'Unexpected predicted-pose fields')
                    values = package['poses']
                require(values.shape == (24, 4, 4) and values.dtype == np.dtype('float64')
                        and np.isfinite(values).all(), 'Invalid predicted camera array')
                if stride == 8:
                    poses[stage, block] = values
                else:
                    require(array_identity(values) == array_identity(poses[stage, block]),
                            'Two strides do not have identical predicted poses')
                selection = read(base/'prediction_only_selection.json')
                split = 'development' if stage == 'S7' and block == 0 else 'test'
                require((selection['block'], selection['stride'], selection['split'], selection['width'])
                        == (block, stride, split, 160), 'Original selection identity mismatch')
                require([q['frame'] for q in selection['queries']] == CONTRACT['queries'], 'Query domain differs')
                cases[stage, block, stride] = selection
    for condition in schedule():
        stage, block, query = (condition[k] for k in ('stage', 'block', 'query'))
        reference = None
        for stride in CONTRACT['strides']:
            choices = cases[stage, block, stride]['queries'][query-20]['maps']
            require(set(choices) == set(CONTRACT['arms']), 'Map domain differs')
            for arm in CONTRACT['arms']:
                choice = choices[arm]
                reads = choice['readouts']
                require(set(reads) == set(CONTRACT['readouts']), 'Readout domain differs')
                full = reads['all20_nms']
                require(full['expanded_candidates'] == list(range(20)) and full['nms'] is True,
                        'Old all20 pool differs')
                if reference is None:
                    reference = full
                require(full == reference, 'Old all20 NMS varies with map or stride')
                for name in CONTRACT['readouts']:
                    ids = reads[name]['selected']
                    require(len(ids) == len(set(ids)) == 4 and all(type(i) is int and 0 <= i < 20 for i in ids),
                            'Old readout is not four distinct historical IDs')
                    require(reads[name]['initial_threshold'] == full['initial_threshold'], 'Old threshold differs')
                official = choice['official_trace']
                counts = official['candidate_counts']
                require([i for i, c in counts] == list(range(20)) and all(c in (0, 1) for i, c in counts)
                        and sum(c for i, c in counts) == 14, 'Original geometry pool is not fourteen unique IDs')
                expected = [i for i, c in counts if c]
                require(official['candidates'] == expected == reads['official']['expanded_candidates']
                        == reads['candidate_no_nms']['expanded_candidates'], 'Original geometry pool identities differ')
                require(official['selected'] == reads['official']['selected'], 'Old official ID trace differs')
                require(official['nms_initial_threshold'] == full['initial_threshold'], 'Old official threshold differs')
                for field in ('expanded_candidates', 'sorted_frames', 'distances_float32'):
                    require(reads['all20_no_nms'][field] == full[field], f'Old all20 field differs: {field}')
    return cases, poses


def make_selections(np, torch, output, cases, poses, compiled, started):
    """Run exactly the 24 new selectors. The saved support fields are unavailable here."""
    namespace = dict(np=np, torch=torch)
    exec(compile(compiled, str(output/'extracted_original_functions.py'), 'exec'), namespace)
    calls = 0
    phase = ''
    label = ''
    distance_log = (output/'distance_calls.jsonl').open('x')

    class PoseKernel:
        def __init__(self):
            self.c2ws = []
            self.initial_threshold = None

        def geodesic_distance(self, left, right, weight_translation=1):
            nonlocal calls
            require(left.dtype == right.dtype == torch.float64 and left.device.type == right.device.type == 'cpu'
                    and tuple(left.shape) == tuple(right.shape) == (4, 4), 'Distance argument dtype/device/shape differs')
            result = namespace['geodesic_distance'](self, left, right, weight_translation)
            value = float(result)
            require(math.isfinite(value), 'Non-finite geodesic distance')
            left_np, right_np = left.detach().cpu().numpy(), right.detach().cpu().numpy()
            item = dict(call_index=calls, label=label, phase=phase, weight_translation=weight_translation,
                        left=left_np.tolist(), right=right_np.tolist(), left_identity=array_identity(left_np),
                        right_identity=array_identity(right_np), result_float64=value)
            distance_log.write(json.dumps(item, allow_nan=False)+'\n')
            calls += 1
            return result

    namespace['ObservedKernel'] = PoseKernel
    selections, threshold_rows, artifact_paths = {}, [], []
    try:
        for stage in CONTRACT['stages']:
            for block in CONTRACT['blocks']:
                check_budget(started)
                optical = poses[stage, block]
                label, phase = f'{stage}_block{block}', 'initial_threshold_first5'
                begin = calls
                threshold = namespace['initial_nms_threshold'](optical[:20], .1)
                require(calls-begin == 10 and math.isfinite(threshold), 'Initial threshold call count differs')
                for stride in CONTRACT['strides']:
                    for query in cases[stage, block, stride]['queries']:
                        require(all(c['readouts']['all20_nms']['initial_threshold'] == threshold
                                    for c in query['maps'].values()), 'Recomputed initial threshold differs from original')
                threshold_rows.append(dict(stage=stage, block=block, initial_threshold=threshold,
                                           distance_call_range=[begin, calls]))
                kernel = PoseKernel()
                kernel.c2ws = [namespace['optical_to_vmem'](p) for p in optical[:20]]
                kernel.initial_threshold = threshold
                for query in CONTRACT['queries']:
                    label, phase = f'{stage}_block{block}_query{query}', 'all20_query_distance_identity_gate'
                    begin = calls
                    normalized = torch.tensor(namespace['average_camera_pose'](torch.tensor(
                        namespace['optical_to_vmem'](optical[query])[None], dtype=torch.float64)), dtype=torch.float64)
                    distances = [float(kernel.geodesic_distance(normalized, torch.tensor(kernel.c2ws[i],
                                 dtype=torch.float64), .1)) for i in range(20)]
                    distances32 = torch.tensor(distances, dtype=torch.float32)
                    array32 = distances32.numpy()
                    ranked = torch.argsort(distances32).tolist()
                    old = cases[stage, block, 8]['queries'][query-20]['maps']['A0P0']['readouts']['all20_nms']
                    require(np.isfinite(array32).all() and len(set(distances32.tolist())) == 20,
                            'FP32 full20 distance contains a tie or non-finite value')
                    require(distances32.tolist() == old['distances_float32']
                            and array32.tobytes(order='C') == np.asarray(old['distances_float32'], dtype=np.float32).tobytes(order='C')
                            and ranked == old['sorted_frames'], 'Original full20 query distance or complete order differs')
                    require(calls-begin == 20, 'Full20 distance gate did not make exactly 20 calls')
                    candidates_ranked = ranked[:14]
                    counts = [[i, 1] for i in sorted(candidates_ranked)]
                    require(len(counts) == len(set(candidates_ranked)) == 14, 'New candidate pool differs from fourteen')
                    phase = 'new_pose14_decision_trace'
                    nms_begin = calls
                    trace = namespace['decision_trace'](kernel, optical[query], counts, nms=True)
                    require(len(trace['selected']) == len(set(trace['selected'])) == 4
                            and set(trace['selected']).issubset(candidates_ranked), 'New selected IDs outside pose14 pool')
                    require(trace['expanded_adjacent_pose_ties'] == 0 and trace['initial_threshold'] == threshold,
                            'New pose14 sorting or threshold differs')
                    split = 'development' if stage == 'S7' and block == 0 else 'test'
                    result = dict(stage=stage, block=block, query=query, split=split, label=label,
                                  created_utc=utc(), predicted_pose_identity=array_identity(optical),
                                  full20_frame_order=list(range(20)), full20_distances_float64=distances,
                                  full20_distances_float32=distances32.tolist(), full20_sorted_frames=ranked,
                                  pose14_ranked_candidates=candidates_ranked, pose14_counts=counts,
                                  full20_distance_call_range=[begin, nms_begin],
                                  pose14_distance_call_range=[nms_begin, calls], trace=trace)
                    path = output/'selections'/f'{label}.json'
                    save(path, result)
                    artifact_paths.append(path)
                    selections[stage, block, query] = result
                    check_budget(started)
    finally:
        distance_log.close()
    require(len(selections) == 24, 'Incomplete new selection domain')
    save(output/'initial_thresholds.json', threshold_rows)
    artifact_paths += [output/'initial_thresholds.json', output/'distance_calls.jsonl']
    seal = dict(schema='s12-selection-seal-v1', sealed_utc=utc(), selection_count=24,
                new_decision_trace_calls=24, old_decision_trace_calls=0, distance_calls=calls,
                scoring_fields_decoded=0,
                files={str(p.relative_to(output)): sha(p) for p in artifact_paths})
    save(output/'selection_seal.json', seal)
    return selections, seal


def score_support(support, valid, ids):
    numerator = int((support[ids].any(axis=0) & valid).sum())
    denominator = int(valid.sum())
    return dict(selected=ids, supported_pixels=numerator, valid_pixels=denominator,
                support=numerator/denominator)


def score_after_seal(np, output, cases, selections, metadata, started):
    """Decode only old support/valid; reproduce all old scores before new scores."""
    cache, identities, old_rows, bounds = {}, [], [], []
    for stage in CONTRACT['stages']:
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                base = RUNS[stage]/f'block{block}_stride{stride}'
                for query in CONTRACT['queries']:
                    check_budget(started)
                    path = base/f'query{query}_scoring.npz'
                    with np.load(path, allow_pickle=False) as package:
                        require({'support', 'valid'}.issubset(package.files), 'Missing saved scoring fields')
                        if metadata['first_scoring_field_decode_utc'] is None:
                            metadata['first_scoring_field_decode_utc'] = utc()
                            save(output/'run_metadata.json', metadata)
                        support, valid = package['support'], package['valid']
                    require(support.dtype == valid.dtype == np.dtype('bool') and support.shape == (20, 112, 112)
                            and valid.shape == (112, 112) and bool(valid.any()), 'Invalid saved support/valid fields')
                    key = stage, block, query
                    pair_id = dict(support=array_identity(support), valid=array_identity(valid))
                    if stride == 8:
                        cache[key] = (support, valid)
                    else:
                        a, b = cache[key]
                        require(pair_id == dict(support=array_identity(a), valid=array_identity(b)),
                                'Scoring support/valid differs between strides')
                    identities.append(dict(stage=stage, block=block, stride=stride, query=query,
                                           path=str(path.relative_to(ROOT)), **pair_id))
    require(len(identities) == 48 and len(cache) == 24, 'Incomplete scoring-field domain')
    save(output/'scoring_array_identities.json', identities)
    old_lookup = {}
    for stage, run in RUNS.items():
        records = read(run/'records.json')
        require(len(records) == 24, 'Unexpected original record count')
        index = {(r['block'], r['stride'], r['frame']): r for r in records}
        require(len(index) == 24, 'Duplicate original record identity')
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                for query in CONTRACT['queries']:
                    support, valid = cache[stage, block, query]
                    original = index[block, stride, query]
                    expected_split = 'development' if stage == 'S7' and block == 0 else 'test'
                    require(original['split'] == expected_split, 'Old record split differs')
                    denominator = int(valid.sum())
                    upper = score_support(support, valid, list(range(20)))
                    require(upper['support'] == original['all20_support']
                            and denominator == original['valid_pixels'], 'Old all20 support or denominator differs')
                    if stage == 'S8':
                        require(upper['supported_pixels'] == original['all20_supported_pixels'], 'Old all20 integer count differs')
                    bounds.append(dict(stage=stage, block=block, stride=stride, query=query, **upper))
                    choice = cases[stage, block, stride]['queries'][query-20]['maps']
                    require(set(original['readouts']) == set(CONTRACT['arms']), 'Original score map domain differs')
                    for arm in CONTRACT['arms']:
                        require(set(original['readouts'][arm]) == set(CONTRACT['readouts']), 'Original score readout domain differs')
                        scores = {}
                        for name in CONTRACT['readouts']:
                            saved = original['readouts'][arm][name]
                            ids = choice[arm]['readouts'][name]['selected']
                            actual = score_support(support, valid, ids)
                            require(saved['selected'] == ids and saved['support'] == actual['support'],
                                    f'Old readout score mismatch: {stage}/{block}/{stride}/{query}/{arm}/{name}')
                            if stage == 'S8':
                                require(saved['supported_pixels'] == actual['supported_pixels'], 'Old supported integer count differs')
                            scores[name] = actual
                            old_rows.append(dict(stage=stage, block=block, stride=stride, query=query,
                                                 arm=arm, readout=name, **actual))
                        old_lookup[stage, block, stride, query, arm] = scores
    require(len(old_rows) == 768 and len(bounds) == 48, 'Incomplete old score reproduction')
    save(output/'old_scoring_reproduction.json', dict(completed_utc=utc(), exact_match=True,
         old_readout_count=768, all20_upper_bound_count=48, readouts=old_rows, all20_upper_bounds=bounds))
    # No new candidate set or score has been computed from support before here.
    new_scores = {key: score_support(*cache[key], value['trace']['selected']) for key, value in selections.items()}
    rows = []
    for condition in schedule():
        stage, block, query = (condition[k] for k in ('stage', 'block', 'query'))
        selected = selections[stage, block, query]
        new = new_scores[stage, block, query]
        pose_pool = selected['pose14_ranked_candidates']
        for stride in CONTRACT['strides']:
            choices = cases[stage, block, stride]['queries'][query-20]['maps']
            for arm in CONTRACT['arms']:
                old = old_lookup[stage, block, stride, query, arm]
                geometry_pool = choices[arm]['readouts']['official']['expanded_candidates']
                geometry = old['official']
                rows.append(dict(**condition, stride=stride, arm=arm,
                    main_comparison=(stride == 8 and arm == 'A0P0'), old_readouts=old, pose14=new,
                    geometry14_candidates=geometry_pool, pose14_ranked_candidates=pose_pool,
                    geometry14_minus_pose14_pp=100*(geometry['support']-new['support']),
                    candidate_intersection_ids=sorted(set(geometry_pool)&set(pose_pool)),
                    candidate_intersection_count=len(set(geometry_pool)&set(pose_pool)),
                    same_candidate_set=set(geometry_pool) == set(pose_pool),
                    selected_intersection_count=len(set(geometry['selected'])&set(new['selected'])),
                    selected_set_changed=set(geometry['selected']) != set(new['selected']),
                    selected_order_changed=geometry['selected'] != new['selected'],
                    pose14_same_order_as_all20_nms=new['selected'] == old['all20_nms']['selected']))
    require(len(rows) == 192, 'Incomplete paired map conditions')
    save(output/'records.json', rows)
    return rows


def summarize(rows):
    def group(subset, identity):
        require(bool(subset), 'Empty planned summary group')
        n = len(subset)
        return dict(**identity, n_queries=n,
            geometry14_mean_support=sum(r['old_readouts']['official']['support'] for r in subset)/n,
            pose14_mean_support=sum(r['pose14']['support'] for r in subset)/n,
            geometry14_minus_pose14_mean_pp=sum(r['geometry14_minus_pose14_pp'] for r in subset)/n,
            geometry_higher=sum(r['geometry14_minus_pose14_pp'] > 0 for r in subset),
            pose_higher=sum(r['geometry14_minus_pose14_pp'] < 0 for r in subset),
            equal=sum(r['geometry14_minus_pose14_pp'] == 0 for r in subset),
            selected_set_changed=sum(r['selected_set_changed'] for r in subset),
            selected_order_changed=sum(r['selected_order_changed'] for r in subset),
            candidate_set_equal=sum(r['same_candidate_set'] for r in subset),
            pose14_same_order_as_all20_nms=sum(r['pose14_same_order_as_all20_nms'] for r in subset),
            old_readout_mean_support={name: sum(r['old_readouts'][name]['support'] for r in subset)/n
                                      for name in CONTRACT['readouts']})
    strata, blocks = [], []
    for stage, split, expected in [('S7', 'development', 4), ('S7', 'test', 8), ('S8', 'test', 12)]:
        for stride in CONTRACT['strides']:
            for arm in CONTRACT['arms']:
                subset = [r for r in rows if (r['stage'], r['split'], r['stride'], r['arm']) == (stage, split, stride, arm)]
                require(len(subset) == expected, 'Planned stratum query count differs')
                strata.append(group(subset, dict(stage=stage, split=split, stride=stride, arm=arm,
                                                main_comparison=stride == 8 and arm == 'A0P0')))
    for stage in CONTRACT['stages']:
        for block in CONTRACT['blocks']:
            for stride in CONTRACT['strides']:
                for arm in CONTRACT['arms']:
                    subset = [r for r in rows if (r['stage'], r['block'], r['stride'], r['arm']) == (stage, block, stride, arm)]
                    require(len(subset) == 4, 'Planned block query count differs')
                    blocks.append(group(subset, dict(stage=stage, block=block, split=subset[0]['split'],
                        stride=stride, arm=arm, main_comparison=stride == 8 and arm == 'A0P0')))
    return dict(schema='s12-matched-budget-summary-v1', unique_seen_queries=24,
                related_map_conditions=192, difference=CONTRACT['difference'],
                strata=strata, blocks=blocks,
                scope='Exploratory saved-query support proxy; no cross-scene pooled claim, p-value, speed or video-quality claim.')


def execute(args):
    output = args.output.resolve()
    require(output == ROOT/'results/S12_matched_budget', 'This protocol permits only the fixed new S12 output directory')
    require(not args.output.exists() and not args.output.is_symlink(), 'Output already exists; previous failures must remain intact')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    metadata = dict(schema='s12-matched-budget-run-v1', status='running', started_utc=utc(),
        phase='validate_freeze_and_archive', contract=CONTRACT, selections_sealed_utc=None,
        first_scoring_field_decode_utc=None, original_selection_calls=0, renderer_calls=0,
        model_calls=0, raw_pixels_decoded=False, gt_pose_values_parsed=False,
        scope=CONTRACT['scope'], resource_limit='soft wall time and observed peak RSS; no OS isolation')
    save(output/'run_metadata.json', metadata)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, CONTRACT['wall_budget_seconds'])
    try:
        protocol, freeze_path = args.protocol.resolve(), args.freeze.resolve()
        require(protocol == ROOT/'docs/S12_MATCHED_BUDGET_PROTOCOL.md'
                and freeze_path.is_relative_to(ROOT/'docs'), 'Unexpected protocol/freeze location')
        freeze = read(freeze_path)
        require(freeze['schema'] == 's12-matched-budget-freeze-v1'
                and freeze['status'] == 'approved_for_execution', 'Execution freeze not approved')
        require(datetime.fromisoformat(freeze['frozen_utc']) < datetime.fromisoformat(metadata['started_utc']),
                'Execution freeze must precede new execution')
        source_sha = file_hashes([ROOT/name for name in SOURCE_NAMES])
        input_sha = file_hashes(expected_inputs())
        require(len(source_sha) == 4 and len(input_sha) == 76, 'Source/input domain count differs')
        require(all(source_sha[name] == value for name, value in SOURCE_PINS.items()), 'An original source was modified')
        require(source_sha == freeze['execution_source_sha256'] and input_sha == freeze['input_sha256'],
                'Execution source or saved input differs from freeze')
        require(sha(protocol) == freeze['protocol_sha256'], 'Protocol differs from execution freeze')
        matches = re.findall(r'```s12-matched-budget-json\s*\n(.*?)\n```', protocol.read_text(), re.S)
        require(len(matches) == 1 and json.loads(matches[0]) == CONTRACT, 'Machine protocol differs from runner contract')
        review_sha = freeze['review_evidence_sha256']
        require(bool(review_sha), 'Frozen independent review evidence is required')
        require(file_hashes([ROOT/name for name in review_sha]) == review_sha, 'Review evidence changed')
        fixed_sha = file_hashes([protocol, freeze_path])
        combined_sources = {**source_sha, **review_sha, **fixed_sha}
        require(len(combined_sources) == len(source_sha)+len(review_sha)+2, 'Source/review/freeze domains overlap')
        save(output/'input_sha256.json', input_sha)
        save(output/'execution_source_sha256.json', source_sha)
        save(output/'protocol_and_review_sha256.json', {**review_sha, **fixed_sha})
        metadata.update(protocol_sha256=sha(protocol), freeze_sha256=sha(freeze_path),
                        execution_source_sha256=source_sha, input_sha256=input_sha,
                        archives=dict(inputs=archive(output/'sealed_inputs.zip', input_sha),
                                      sources=archive(output/'execution_sources.zip', combined_sources)))
        source, extraction_receipt = extract_functions()
        (output/'extracted_original_functions.py').write_text(source)
        save(output/'extraction_identity.json', dict(functions=extraction_receipt,
             extracted_file_sha256=sha(output/'extracted_original_functions.py'),
             original_modules_imported=False, representation='ast.unparse original node; complete original AST equality including docstrings'))
        for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[variable] = '8'
        import numpy as np
        import torch
        actual_versions = dict(python=platform.python_version(), **{n: version(n) for n in ('numpy', 'torch', 'scipy')})
        require(actual_versions == CONTRACT['versions'], 'Pinned numerical dependency versions differ')
        torch.set_num_threads(8)
        torch.set_num_interop_threads(8)
        require(torch.get_num_threads() == torch.get_num_interop_threads() == 8, 'Torch thread settings differ')
        metadata['environment'] = dict(versions=actual_versions, platform=platform.platform(), device='cpu',
                                       torch_threads=8, torch_interop_threads=8,
                                       thread_environment={k: os.environ[k] for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                                           'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')})
        metadata['phase'] = 'prediction_only_new_selections'
        save(output/'run_metadata.json', metadata)
        cases, poses = load_prediction_inputs(np, input_sha)
        selections, seal = make_selections(np, torch, output, cases, poses, source, started)
        metadata.update(selections_sealed_utc=seal['sealed_utc'], selection_seal_sha256=sha(output/'selection_seal.json'),
                        new_decision_trace_calls=24, distance_calls=seal['distance_calls'], phase='saved_support_scoring')
        save(output/'run_metadata.json', metadata)
        rows = score_after_seal(np, output, cases, selections, metadata, started)
        save(output/'summary.json', summarize(rows))
        require(file_hashes(expected_inputs()) == input_sha, 'Saved input changed during execution')
        require(file_hashes([ROOT/name for name in combined_sources]) == combined_sources, 'Source/protocol/review changed during execution')
        require(all(sha(output/name) == digest for name, digest in seal['files'].items())
                and sha(output/'selection_seal.json') == metadata['selection_seal_sha256'], 'Sealed selections changed during scoring')
        require(datetime.fromisoformat(metadata['selections_sealed_utc'])
                < datetime.fromisoformat(metadata['first_scoring_field_decode_utc']), 'Scoring decode preceded selection sealing')
        save(output/'post_run_integrity.json', dict(verified_utc=utc(), input_files=76, execution_sources=4,
             all_input_and_source_hashes_unchanged=True, selections_unchanged=True,
             input_sha256=input_sha, combined_source_sha256=combined_sources))
        metadata.update(status='completed', phase='completed', completed_utc=utc(), checked_scoring_files=48,
            reproduced_old_readout_scores=768, reproduced_all20_upper_bounds=48, unique_queries=24,
            paired_map_conditions=192, peak_rss_bytes=check_budget(started),
            summary_sha256=sha(output/'summary.json'), records_sha256=sha(output/'records.json'))
        save(output/'run_metadata.json', metadata)
        print(json.dumps(dict(status='completed', output=str(output), unique_queries=24,
                              paired_map_conditions=192, summary_sha256=metadata['summary_sha256'])))
    except BaseException as error:
        metadata.update(status='failed', failed_utc=utc(), error_type=type(error).__name__, error=str(error))
        save(output/'run_metadata.json', metadata)
        (output/'failure_traceback.txt').write_text(traceback.format_exc())
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    execute(parser.parse_args())


if __name__ == '__main__':
    main()
