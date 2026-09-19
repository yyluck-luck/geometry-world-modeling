#!/usr/bin/env python3
"""Different-script S10 result audit; same author as the comparison runner.

Does not import the comparison runner, its validation/summary helpers, Torch,
or either renderer. A completed result gate precedes NumPy/NPZ access.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import textwrap
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_SHA = 'b78d2f079e61bab4c92b7704bbbd632b8daa051b4c68ca6e4526b761d116a1bc'
RUNNER_SHA = '00dbae5db3c7a09dca78a428951db2074103b54d8f2c23a4daea17b7e6a96554'
FREEZE_SHA = 'db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204'
S9_FREEZE_SHA = '8e9c0a84cea827cf11d01f793e21ce46a9c2ce579206cc6678d3d006805fa9cd'
OLD_SOURCES = ('scripts/profile_s9_components.py', 'src/s6_memory_bridge.py',
    'src/s7_event_replay.py', 'src/rgbd_memory.py', 'src/rgbd_retrieval.py',
    'src/retrieval_diagnostic.py', 'src/vmem_memory_kernel.py',
    'src/vmem_retrieval_kernel.py', 'vendor/provenance.json', 'vendor/VMEM_LICENSE')
SOURCES = (*OLD_SOURCES, 'scripts/run_s10_renderer_comparison.py', 'src/s10_vectorized_renderer.py')
RUNS = {'S7':'results/S7_event_replay', 'S8':'results/S8_event_replay_v2'}
BUFFER_NAMES = {'depth', 'surfel_index_map', 'cos_value_map'}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def json_value(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: '+key)
            result[key] = value
        return result
    def bad(value):
        raise ValueError('Nonfinite JSON token: '+value)
    return json.loads(text, object_pairs_hook=unique, parse_constant=bad)


def safe_relative(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or str(p) != name or any(c in name for c in ('\\', ':', '\0')):
        raise ValueError('Unsafe relative path: '+repr(name))
    return p


def below(root, name):
    safe_relative(name)
    path = root/name
    if path.is_symlink():
        raise ValueError('Input symlinks are not allowed: '+str(path))
    path = path.resolve(strict=True)
    if not path.is_relative_to(root.resolve(strict=True)) or not path.is_file():
        raise ValueError('Input escapes its root: '+str(path))
    return path


class Check:
    def __init__(self):
        self.items = []
    def __call__(self, name, value, kind='recomputed', detail=None):
        item = dict(name=name, passed=bool(value), kind=kind)
        if detail is not None:
            item['detail'] = detail
        self.items.append(item)
        if not value:
            raise AssertionError(name)
    def same(self, name, actual, expected, kind='recomputed'):
        if isinstance(expected, dict):
            self(name+'/object_keys', isinstance(actual, dict) and set(actual) == set(expected), kind)
            for key in expected:
                self.same(name+'/'+str(key), actual[key], expected[key], kind)
        elif isinstance(expected, list):
            self(name+'/list_length', isinstance(actual, list) and len(actual) == len(expected), kind)
            for index, value in enumerate(expected):
                self.same(name+'/'+str(index), actual[index], value, kind)
        else:
            self(name, type(actual) is type(expected) and actual == expected, kind,
                 None if actual == expected else dict(actual=actual, expected=expected))


class Reader:
    def __init__(self, check):
        self.check, self.seen = check, {}
    def bytes(self, path):
        path = Path(path).resolve(strict=True)
        data = path.read_bytes(); value = digest_bytes(data)
        if str(path) in self.seen:
            self.check('stable_read/'+str(path), self.seen[str(path)] == value, 'integrity')
        self.seen[str(path)] = value
        return data
    def json(self, path):
        return json_value(self.bytes(path).decode())
    def hash(self, path, expected=None):
        value = digest_bytes(self.bytes(path))
        if expected is not None:
            self.check('sha/'+str(path), value == expected, 'integrity')
        return value
    def finish(self):
        for path, value in list(self.seen.items()):
            self.check('unchanged_during_audit/'+path, digest_bytes(Path(path).read_bytes()) == value, 'integrity')


def expected_input_names():
    result = []
    for root in RUNS.values():
        result += [root+'/run_metadata.json', root+'/records.json']
        for block in range(3):
            base = root+f'/block{block}_stride8/'
            result += [base+name for name in ('A0P0.npz','A0P0_sources.json','predicted_poses.npz','prediction_only_selection.json')]
            result += [base+f'query{query}_A0P0_render.npz' for query in range(20,24)]
    return result


def planned_pairs():
    result = []
    for phase in ('correctness', 'warmup', 'measured'):
        for repeat in range(5 if phase == 'measured' else 1):
            for index in range(24):
                stage = 'S7' if index < 12 else 'S8'
                local = index % 12; block, query = local//4, 20+local%4
                ab = index % 2 == repeat % 2
                result.append(dict(phase=phase, round=repeat, query_index=index, stage=stage,
                    block=block, query=query, label=f'{stage}_block{block}_query{query}',
                    methods=['original','candidate'] if ab else ['candidate','original']))
    return result


def midpoint(values):
    values = sorted(values); k = len(values)//2
    return values[k] if len(values) % 2 else (values[k-1]+values[k])/2


def integer_mean(values):
    quotient, remainder = divmod(sum(values), len(values))
    return quotient if remainder == 0 else float(Fraction(sum(values), len(values)))


def recomputed_summary(rows):
    """Independent indexing and integer/rational arithmetic; no runner import."""
    table = {(r['round'],r['query_index'],r['method']):r for r in rows if r['phase'] == 'measured'}
    pairs = []
    for repeat in range(5):
        for index in range(24):
            a, b = table[(repeat,index,'original')], table[(repeat,index,'candidate')]
            pairs.append(dict(round=repeat, query_index=index, label=a['label'], stage=a['stage'],
                pair_order=a['pair_order'], original_ns=a['elapsed_ns'], candidate_ns=b['elapsed_ns'],
                original_over_candidate=a['elapsed_ns']/b['elapsed_ns']))
    def describe(values):
        aa, bb = [p['original_ns'] for p in values], [p['candidate_ns'] for p in values]
        result = dict(pairs=len(values), distinct_queries=len({p['query_index'] for p in values}))
        for name, times in (('original',aa), ('candidate',bb)):
            result[name] = dict(total_ns=sum(times), mean_ms=integer_mean(times)/1e6,
                median_ms=midpoint(times)/1e6, min_ms=min(times)/1e6, max_ms=max(times)/1e6)
        result.update(ratio_of_total_times=sum(aa)/sum(bb),
            median_paired_ratio=midpoint([p['original_over_candidate'] for p in values]),
            AB_pairs=sum(p['pair_order'] == 'AB' for p in values),
            BA_pairs=sum(p['pair_order'] == 'BA' for p in values))
        return result
    groups = {}
    for name in ('all','S7','S8','AB','BA'):
        values = [p for p in pairs if name == 'all' or p['stage'] == name or p['pair_order'] == name]
        groups[name] = describe(values)
    per_query = []
    for index in range(24):
        values = [p for p in pairs if p['query_index'] == index]
        a = midpoint([p['original_ns'] for p in values]); b = midpoint([p['candidate_ns'] for p in values])
        per_query.append(dict(query_index=index, label=values[0]['label'], repeats=len(values),
            original_median_ms=a/1e6, candidate_median_ms=b/1e6, ratio_of_medians=a/b,
            AB_pairs=sum(p['pair_order'] == 'AB' for p in values),
            BA_pairs=sum(p['pair_order'] == 'BA' for p in values)))
    return dict(primary_estimator='ratio of summed original/candidate integer nanoseconds over 120 measured pairs',
        groups=groups, per_query=per_query, pairs=pairs,
        limitations='Descriptive paired software measurements on 24 seen queries; no independent-replicate significance test.')


def validate_archive(path, expected, reader, check):
    """Hash/CRC every member, without extraction or executing stored sources."""
    reader.hash(path)
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        check(path.name+'/inventory', len(names) == len(set(names)) and set(names) == set(expected), 'integrity')
        check(path.name+'/CRC', z.testzip() is None, 'integrity')
        payloads = {}
        for info in z.infolist():
            safe_relative(info.filename)
            mode = info.external_attr >> 16
            check(path.name+'/regular/'+info.filename,
                  not info.is_dir() and stat.S_IFMT(mode) in (0,stat.S_IFREG), 'integrity')
            payload = z.read(info.filename)
            check(path.name+'/member_sha/'+info.filename, digest_bytes(payload) == expected[info.filename], 'integrity')
            payloads[info.filename] = payload
    return payloads


def verify_transformation(metadata, source_payloads, freeze, check):
    kernel_source = source_payloads['src/vmem_retrieval_kernel.py'].decode()
    kernel = ast.parse(kernel_source)
    cls = next(n for n in kernel.body if isinstance(n,ast.ClassDef) and n.name == 'RetrievalKernel')
    method = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name == 'render_surfels_to_image')
    # The factory uses inspect.getsource + dedent; retain the same source context
    # for docstring indentation before comparing every AST node.
    method_text = '\n'.join(kernel_source.splitlines()[method.lineno-1:method.end_lineno])+'\n'
    original = ast.parse(textwrap.dedent(method_text)).body[0]
    captured = ast.parse(textwrap.dedent(metadata['original_method'])).body[0]
    check('transform/original_method_AST', ast.dump(original,include_attributes=False) == ast.dump(captured,include_attributes=False), 'source_order')
    changed = ast.parse(metadata['transformed_method'])
    expected_loop = ast.parse('''for py_ in range(min_y, max_y + 1):
    for px_ in range(min_x, max_x + 1):
        if point_in_polygon_2d(px_, py_, valid_points):
            if avg_depth < z_buffer[py_, px_]:
                z_buffer[py_, px_] = avg_depth
                surfel_index_map[py_, px_] = idx
                cos_buffer[py_, px_] = cos_value
''').body[0]
    marker = ast.parse('_s10_raster_patch(valid_points, min_x, max_x, min_y, max_y, avg_depth, idx, cos_value, z_buffer, surfel_index_map, cos_buffer)').body[0]
    replaced = []
    class Undo(ast.NodeTransformer):
        def visit_Expr(self, node):
            if ast.dump(node,include_attributes=False) == ast.dump(marker,include_attributes=False):
                replaced.append(node)
                return copy.deepcopy(expected_loop)
            return self.generic_visit(node)
    restored = Undo().visit(copy.deepcopy(changed))
    check('transform/only_original_inner_loop', len(replaced) == 1 and len(restored.body) == 1 and
          ast.dump(restored.body[0],include_attributes=False) == ast.dump(original,include_attributes=False), 'source_order')
    check('transform/identity', metadata['original_source_sha256'] == freeze['execution_source_sha256']['src/vmem_retrieval_kernel.py'] and
          metadata['helper_source_sha256'] == freeze['execution_source_sha256']['src/s10_vectorized_renderer.py'] and
          metadata['numpy'] == '2.3.5' and metadata['replaced_nested_pixel_loops'] == 1 and
          metadata['restored_full_method_ast_identical'] is True, 'integrity')
    runner = ast.parse(source_payloads['scripts/run_s10_renderer_comparison.py'].decode())
    calls = [n for n in ast.walk(runner) if isinstance(n, ast.Call)]
    check('runner/no_S9_timing_instrumentation', not any(isinstance(n.func,ast.Attribute) and
          n.func.attr == 'instrument_context_method' for n in calls), 'source_order')
    check('runner/clock_boundary_count', sum(isinstance(n.func,ast.Attribute) and n.func.attr == 'perf_counter_ns' for n in calls) == 2, 'source_order')
    check('runner/validation_outside_timer', max(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and
          n.func.attr == 'perf_counter_ns') < min(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and
          n.func.attr == 'validate_output'), 'source_order')
    check('runner/explicit_render_C_bytes_gate', sum(isinstance(n.func,ast.Attribute) and n.func.attr == 'tobytes'
          for n in calls) >= 3, 'source_order')


def recompute_votes(buffers, sources, np):
    """Rebuild once per distinct reference buffer; every actual buffer equals it."""
    ids, cos, depth = (buffers[k].ravel(order='C') for k in ('surfel_index_map','cos_value_map','depth'))
    totals = {}
    for pixel in np.flatnonzero(ids >= 0):
        if cos[pixel] < 0:
            continue
        contribution = cos[pixel]/(1+depth[pixel])
        for frame in sources[str(int(ids[pixel]))]:
            if frame not in totals:
                totals[frame] = contribution
            totals[frame] += contribution
    labels = list(totals)
    sums = np.asarray([totals[k] for k in labels])
    ratios = sums/sums.sum()
    allocation = [1]*len(labels)
    # n=min(14,k): the upstream leftover-distribution branch is unreachable here.
    if len(labels) > 14:
        keep = set(np.argsort(ratios)[::-1][:14].tolist())
        allocation = [int(i in keep) for i in range(len(labels))]
    return (sorted([[int(k),float(v)] for k,v in zip(labels,ratios)]),
            sorted([[int(k),int(v)] for k,v in zip(labels,allocation)]))


def check_decision_logic(trace, counts, check, tag):
    """Replay comparisons from recorded distances; does not regenerate pose math."""
    candidate = [frame for frame,count in counts for _ in range(count)]
    check.same(tag+'/expanded_candidates', trace['expanded_candidates'], candidate)
    distances = trace['distances_float32']
    check(tag+'/distance_domain', len(distances) == len(candidate) and len(set(distances)) == len(distances))
    ranked = [candidate[i] for i in sorted(range(len(candidate)),key=lambda i:distances[i])]
    check.same(tag+'/sorted_frames', trace['sorted_frames'], ranked)
    check(tag+'/no_distance_ties', trace['expanded_adjacent_pose_ties'] == 0 and trace['nms'] is True)
    selected = [ranked[0]]; threshold = trace['initial_threshold']; steps = trace['steps']; cursor = 0
    while len(selected) < 4 and threshold >= 1e-5:
        for frame in ranked[1:]:
            if len(selected) >= 4:
                break
            item = steps[cursor]; cursor += 1
            check(tag+f'/step{cursor}/frame_threshold', item['frame'] == frame and item['threshold'] == threshold)
            comparisons = item['comparisons']; rejected = False
            check(tag+f'/step{cursor}/comparison_count', 1 <= len(comparisons) <= len(selected))
            for index,(other,distance) in enumerate(comparisons):
                check(tag+f'/step{cursor}/comparison{index}', other == selected[index] and
                      isinstance(distance,float) and distance >= 0)
                if distance < threshold:
                    rejected = True
                    check(tag+f'/step{cursor}/short_circuit', index == len(comparisons)-1)
                    break
            if not rejected:
                check(tag+f'/step{cursor}/all_selected_compared', len(comparisons) == len(selected))
                selected.append(frame)
            check(tag+f'/step{cursor}/acceptance', item['accepted'] is (not rejected))
        if len(selected) < 4:
            check.same(tag+'/relax'+str(cursor), steps[cursor], dict(relax_from=threshold,relax_to=threshold/1.2))
            cursor += 1; threshold /= 1.2
    if len(selected) < 4:
        added = [x for x in ranked if x not in selected][:4-len(selected)]
        check.same(tag+'/fallback', steps[cursor], dict(fallback_added=added)); cursor += 1; selected.extend(added)
    check(tag+'/all_steps_consumed', cursor == len(steps))
    check.same(tag+'/selected_from_steps', trace['selected'], selected)


def audit(args, output, report, check):
    reader = Reader(check); result = args.results.resolve(strict=True)
    meta = reader.json(result/'run_metadata.json')
    check('completed_gate', meta.get('status') == 'completed' and meta.get('phase') == 'complete', 'metadata')
    check('authorship_disclosure', report['same_author_as_runner'] is True, 'metadata')
    freeze_path, protocol = args.freeze.resolve(strict=True), args.protocol.resolve(strict=True)
    reader.hash(freeze_path, FREEZE_SHA); reader.hash(protocol, PROTOCOL_SHA)
    freeze = reader.json(freeze_path)
    check('approved_freeze', freeze['schema'] == 's10-renderer-comparison-freeze-v1' and freeze['status'] == 'approved_for_execution', 'metadata')
    check('frozen_source_domain', set(freeze['execution_source_sha256']) == set(SOURCES), 'integrity')
    check('frozen_input_domain', set(freeze['input_sha256']) == set(expected_input_names()) and len(freeze['input_sha256']) == 52, 'integrity')
    check('known_runner', freeze['execution_source_sha256']['scripts/run_s10_renderer_comparison.py'] == RUNNER_SHA, 'integrity')
    check('metadata_freeze_bindings', meta['protocol_sha256'] == PROTOCOL_SHA and meta['freeze_sha256'] == FREEZE_SHA and
          meta['s9_freeze_sha256'] == freeze['s9_freeze_sha256'] == S9_FREEZE_SHA, 'integrity')
    check.same('metadata_sources', meta['execution_source_sha256'], freeze['execution_source_sha256'], 'integrity')
    check.same('metadata_inputs', meta['input_sha256'], freeze['input_sha256'], 'integrity')
    machine = re.findall(r'```s10-comparison-json\s*\n(.*?)\n```', reader.bytes(protocol).decode(), re.S)
    check('machine_contract_present', len(machine) == 1, 'metadata')
    contract = json_value(machine[0]); check.same('machine_contract', meta['contract'], contract, 'metadata')
    check('frozen_environment', meta['environment']['versions'] ==
          dict(python='3.12.14',numpy='2.3.5',torch='2.7.0',scipy='1.16.2') and
          meta['environment']['torch_threads'] == meta['environment']['torch_interop_threads'] == 8 and
          meta['environment']['torch_default_dtype'] == 'torch.float32', 'metadata')
    for name, value in dict(completed_invocations=336, correctness_invocations=48, warmup_invocations=48,
        measured_invocations=240, measured_pairs=120, distinct_seen_queries=24, maps_per_method=6,
        exact_output_regressions_passed=336).items():
        check('count/'+name, type(meta[name]) is int and meta[name] == value, 'metadata')
    for name in ('original_sources_unchanged','original_inputs_unchanged','in_memory_inputs_unchanged',
                 'all_call_render_arrays_saved','all_call_complete_traces_saved'):
        check('recorded_flag/'+name, meta[name] is True, 'metadata')
    for name in ('raw_pixels_decoded','gt_loaded','model_loaded'):
        check('recorded_flag/'+name, meta[name] is False, 'metadata')
    stamps = [freeze['frozen_utc']] + [meta[k] for k in ('started_utc','inputs_sealed_utc',
        'initialization_completed_utc','all_initial_correctness_passed_utc','measurement_started_utc','completed_utc')]
    times = [datetime.fromisoformat(s) for s in stamps]
    check('recorded_time_order', all(t.tzinfo is not None for t in times) and all(a <= b for a,b in zip(times,times[1:])), 'metadata')
    check('recorded_soft_budgets', 0 < meta['total_elapsed_seconds'] <= 600 and
          0 < meta['process_peak_rss_bytes'] <= 16*1024**3, 'metadata')
    for name, value in freeze['execution_source_sha256'].items():
        reader.hash(below(ROOT,name), value)
    check('frozen_review_evidence_count', len(freeze['review_evidence_sha256']) == 11, 'integrity')
    for name, value in freeze['review_evidence_sha256'].items():
        reader.hash(below(ROOT,name), value)
    for name, value in freeze['input_sha256'].items():
        reader.hash(below(ROOT,name), value)
    old_path = ROOT/'docs/S9_COMPONENT_PROFILE_EXECUTION_FREEZE.json'
    reader.hash(old_path,S9_FREEZE_SHA); old = reader.json(old_path)
    check.same('same_S9_inputs', freeze['input_sha256'], old['input_sha256'], 'integrity')
    check.same('same_S9_sources', {n:freeze['execution_source_sha256'][n] for n in OLD_SOURCES}, old['execution_source_sha256'], 'integrity')
    reader.hash(result/'comparison_source.zip',meta['source_archive_sha256'])
    source_expected = dict(freeze['execution_source_sha256'], **{'frozen_protocol.md':PROTOCOL_SHA,
        'execution_freeze.json':FREEZE_SHA,'S9_execution_freeze.json':S9_FREEZE_SHA})
    sources = validate_archive(result/'comparison_source.zip',source_expected,reader,check)
    reader.hash(result/'sealed_comparison_inputs.zip',meta['input_archive_sha256'])
    validate_archive(result/'sealed_comparison_inputs.zip',freeze['input_sha256'],reader,check)
    reader.hash(result/'renderer_transformation.json',meta['renderer_transformation_sha256'])
    verify_transformation(reader.json(result/'renderer_transformation.json'),sources,freeze,check)
    pairs = planned_pairs(); check.same('full_plan',reader.json(result/'schedule.json'),pairs)
    check.same('metadata_query_order',meta['query_order'],[p['label'] for p in pairs[:24]],'metadata')
    lines = reader.bytes(result/'invocations.jsonl').decode().splitlines()
    check('no_blank_invocations', all(lines) and len(lines) == 336)
    rows = [json_value(line) for line in lines]
    expected_artifacts = set()
    for ordinal,row in enumerate(rows):
        pair_index, position = divmod(ordinal,2); planned = pairs[pair_index]
        want = dict(pair_index=pair_index, position_in_pair=position, method=planned['methods'][position],
                    pair_order='AB' if planned['methods'][0] == 'original' else 'BA')
        want.update({k:planned[k] for k in ('phase','round','query_index','stage','block','query','label')})
        for key,value in want.items():
            check.same(f'row{ordinal}/'+key,row[key],value)
        check(f'row{ordinal}/elapsed_domain', row['elapsed_ns'] is None if row['phase'] == 'correctness' else
              type(row['elapsed_ns']) is int and row['elapsed_ns'] > 0)
        check(f'row{ordinal}/exact_flag',row['exact_regression_passed'] is True,'metadata')
        base = f"calls/{row['phase']}/round{row['round']}/{row['label']}/{row['method']}/"
        check(f'row{ordinal}/artifact_paths',row['render_path'] == base+'render.npz' and row['trace_path'] == base+'trace.json','integrity')
        expected_artifacts.update((row['render_path'],row['trace_path']))
    check('336_unique_call_artifact_pairs',len(expected_artifacts) == 672)
    check('correctness_before_any_timed_call',all(r['elapsed_ns'] is None for r in rows[:48]) and
          all(r['phase'] == 'warmup' for r in rows[48:96]) and all(r['phase'] == 'measured' for r in rows[96:]))
    check('reported_wall_covers_timed_calls',sum(r['elapsed_ns'] or 0 for r in rows) <= meta['total_elapsed_seconds']*1e9,'metadata')
    reader.hash(result/'call_artifact_manifest.json',meta['call_artifact_manifest_sha256'])
    artifact_items = reader.json(result/'call_artifact_manifest.json')
    inventory = {x['path']:x for x in artifact_items}
    current = {str(p.relative_to(result)) for p in (result/'calls').rglob('*') if p.is_file()}
    check('exact_artifact_inventory', len(inventory) == len(artifact_items) == 672 and
          set(inventory) == current == expected_artifacts,'integrity')
    # Only now import NumPy. Neither Torch nor production/validation modules load.
    sys.dont_write_bytecode = True
    for variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[variable] = '1'
    import numpy as np
    check('audit_numpy_semantics', np.__version__ == '2.3.5','metadata')
    def buffers(path):
        reader.hash(path)
        with np.load(path,allow_pickle=False) as z:
            values = {k:z[k] for k in z.files}
        check('buffer_schema/'+str(path),set(values) == BUFFER_NAMES and
              all(a.shape == (160,160) and np.isfinite(a).all() for a in values.values()))
        return values
    reference = {}
    for stage, run_name in RUNS.items():
        run = ROOT/run_name; prior_meta = reader.json(run/'run_metadata.json')
        check(stage+'/prior_complete',prior_meta['status'] == 'completed' and prior_meta['phase'] == 'complete','metadata')
        for name in SOURCES:
            if name.startswith('src/') and name != 'src/s10_vectorized_renderer.py':
                check(stage+'/unchanged_prior_source/'+name, prior_meta['source_sha256'][name] ==
                      freeze['execution_source_sha256'][name], 'integrity')
        records = reader.json(run/'records.json'); record = {(r['block'],r['stride'],r['frame']):r for r in records}
        check(stage+'/unique_prior_records',len(record) == len(records),'metadata')
        for block in range(3):
            base = run/f'block{block}_stride8'; selection = reader.json(base/'prediction_only_selection.json')
            check(stage+f'/block{block}/case', selection['block'] == block and selection['stride'] == 8 and selection['width'] == 160,'metadata')
            check.same(stage+f'/block{block}/query_domain',[q['frame'] for q in selection['queries']],[20,21,22,23],'metadata')
            sources_map = reader.json(base/'A0P0_sources.json')
            sealed = [c for c in prior_meta['cases'] if c['block'] == block and c['stride'] == 8]
            check(stage+f'/block{block}/one_seal',len(sealed) == 1,'integrity')
            for name in expected_input_names():
                if Path(name).parent == Path(run_name)/base.name:
                    check('prior_case_sha/'+name,freeze['input_sha256'][name] == sealed[0]['sealed_files'][Path(name).name],'integrity')
            for item in selection['queries']:
                query = item['frame']; check('reference_query_domain',query in range(20,24),'metadata')
                ref = item['maps']['A0P0']; data = buffers(base/f'query{query}_A0P0_render.npz')
                weights, counts = recompute_votes(data,sources_map,np)
                label = f'{stage}_block{block}_query{query}'
                check.same(label+'/independent_votes', weights, ref['official_trace']['weights'])
                check.same(label+'/independent_counts', counts, ref['official_trace']['candidate_counts'])
                check.same(label+'/prior_record_IDs', ref['official_trace']['selected'],record[(block,8,query)]['readouts']['A0P0']['official']['selected'])
                check_decision_logic(ref['readouts']['official'],counts,check,label+'/logic')
                reference[(stage,block,query)] = dict(render=data,ref=ref,weights=weights,counts=counts)
    check('24_unique_reference_queries',len(reference) == 24)
    for ordinal,row in enumerate(rows):
        render_path = below(result,row['render_path']); trace_path = below(result,row['trace_path'])
        for kind,path in (('render',render_path),('trace',trace_path)):
            entry = inventory[str(path.relative_to(result))]
            reader.hash(path,row[kind+'_sha256'])
            check(f'call{ordinal}/{kind}/manifest',entry['sha256'] == row[kind+'_sha256'] and
                  entry['bytes'] == path.stat().st_size,'integrity')
        actual = buffers(render_path); trace = reader.json(trace_path)
        ref = reference[(row['stage'],row['block'],row['query'])]
        check(f'call{ordinal}/trace_status',trace['status'] == 'passed','metadata')
        for name in sorted(BUFFER_NAMES):
            a,b = actual[name],ref['render'][name]
            check(f'call{ordinal}/{name}/dtype_shape_C_bytes',a.dtype == b.dtype and a.shape == b.shape and
                  a.tobytes(order='C') == b.tobytes(order='C'))
            check.same(f'call{ordinal}/{name}/recorded_identity',trace['render_arrays'][name],
                dict(shape=list(a.shape),dtype=str(a.dtype),sha256=digest_bytes(a.tobytes(order='C'))),'integrity')
        check.same(f'call{ordinal}/full_official_trace',trace['official_trace'],ref['ref']['official_trace'])
        check.same(f'call{ordinal}/full_NMS_trace',trace['official_decision'],ref['ref']['readouts']['official'])
        check.same(f'call{ordinal}/returned_IDs',trace['returned_ordered_ids'],ref['ref']['official_trace']['selected'])
        check.same(f'call{ordinal}/independently_rebuilt_weights',trace['observed_weights'],ref['weights'])
        check.same(f'call{ordinal}/independently_rebuilt_counts',trace['observed_counts'],ref['counts'])
    calculated = recomputed_summary(rows); recorded = reader.json(result/'summary.json')
    check.same('summary/all_fields',recorded,calculated)
    dump(output/'recomputed_summary.json',calculated)
    check('total_order_balance',calculated['groups']['all']['AB_pairs'] == calculated['groups']['all']['BA_pairs'] == 60)
    check('per_query_odd_balance',all(p['AB_pairs'] in (2,3) and p['BA_pairs'] == 5-p['AB_pairs'] for p in calculated['per_query']))
    reader.finish()
    dump(output/'authenticated_input_files.json',reader.seen)
    report.update(status='passed',completed_invocations_checked=336,actual_render_arrays_byte_compared=1008,
        full_official_traces_compared=336,full_NMS_traces_compared=336,distinct_vote_buffers_recomputed=24,
        distinct_NMS_step_sequences_replayed=24,summary_groups_recomputed=5,query_summaries_recomputed=24,
        measured_pairs_recomputed=120,source_input_files_unchanged_during_audit=True,
        original_summary_sha256=reader.seen[str((result/'summary.json').resolve())],
        recomputed_summary_sha256=digest_bytes((output/'recomputed_summary.json').read_bytes()),
        compared_summary_fields_exact=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('results','protocol','freeze','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args(); raw = args.output.absolute()
    if raw.exists() or raw.is_symlink():
        raise ValueError('Use a fresh audit output; failed audits remain')
    output = raw.resolve(); results = args.results.resolve(strict=True)
    if output.is_relative_to(results) or any(output.is_relative_to(ROOT/p) for p in ('src','scripts','docs','data','vendor')):
        raise ValueError('Audit output overlaps protected input material')
    output.mkdir(parents=True,exist_ok=False)
    check = Check()
    report = dict(status='running',started_utc=now(),same_author_as_runner=True,
        methodology='Different-script recomputation and per-call archived-evidence comparison, not independent authorship.',
        parameters={k:str(getattr(args,k)) for k in ('results','protocol','freeze','output')},
        auditor_sha256=digest_bytes(Path(__file__).read_bytes()),checks=check.items,
        limitations=[
            'Same agent authored the comparison runner. A different script and arithmetic route are used; root cross-review remains separate.',
            'No renderer, model, experiment CLI, runner summarize or validate_output is imported/executed.',
            'All 336 actual buffers are compared as dtype/shape/C bytes, including signed zero, to frozen baseline buffers.',
            'Votes are independently rebuilt on 24 distinct buffers; byte identity transfers this to every repeated invocation.',
            'Full NMS numeric traces are compared to frozen previously audited traces; branch logic is replayed from recorded distances, not new camera-distance computation.',
            'Historical timing order/input immutability use records plus fixed source and current hashes, not a recovered OS access trace or new latency measurement.',
            'Candidate AST restoration verifies scope outside the inner loop, not universal all-input equivalence of that replacement.',
            'No full model/GT/renderer replay, unseen-scene evidence, novelty claim or independent-sample speed significance is established.'])
    dump(output/'verification.json',report)
    (output/'auditor_source.py').write_bytes(Path(__file__).read_bytes())
    try:
        audit(args,output,report,check)
    except Exception:
        report.update(status='failed',traceback=traceback.format_exc())
    report.update(completed_utc=now(),checks_count=len(check.items),checks_by_kind=dict(Counter(c['kind'] for c in check.items)))
    dump(output/'verification.json',report)
    print(json.dumps({k:report.get(k) for k in ('status','completed_utc','checks_count','checks_by_kind')},ensure_ascii=False))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
