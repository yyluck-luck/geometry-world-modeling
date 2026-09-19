#!/usr/bin/env python3
"""Same-author, different-script audit of completed S11 saved evidence.

No production validation, renderer, Torch, GT, images, models or timing runs.
Uses the authenticated S10 audit's basic checks, archive reader and vote math.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA = 'd51522ebca03450293e23072b6c6f0a4656d1a7d61f4b8f99a051b1f392a20b3'
PROTOCOL_SHA = '0a427ad89df0a642300034f2b78c6e1548d38aba8e9dcffbaf31049c95609926'
RUNNER_SHA = 'a6fa8ee30fd4b72905f0c954b04193dcffb46c6b4cab91b01ed0dc22fc9b53c0'
AUDIT_HELPER_SHA = '4f422c968974a25c4d44f10ea6daea4ee84e13a4f62fbb2f8c07ff4bdf0ca9fe'
helper_path = ROOT/'scripts/verify_s10_renderer_comparison.py'
if hashlib.sha256(helper_path.read_bytes()).hexdigest() != AUDIT_HELPER_SHA:
    raise ValueError('Earlier audit helper changed')
sys.dont_write_bytecode = True
import verify_s10_renderer_comparison as common

RUNS = common.RUNS
OLD = 'results/S10_renderer_comparison'
SOURCES = (*common.SOURCES,'scripts/run_s11_renderer_regression.py')


def plan():
    result = []
    for stage in ('S7','S8'):
        for block in range(3):
            for stride in (8,12):
                for arm in ('A0P0','A0P1','A1P0','A1P1'):
                    for query in range(20,24):
                        result.append(dict(condition_index=len(result),stage=stage,block=block,stride=stride,
                            arm=arm,query=query,label=f'{stage}_block{block}_stride{stride}_{arm}_query{query}',
                            evidence='inherited_S10' if stride == 8 and arm == 'A0P0' else 'new_candidate'))
    return result


def inputs():
    names = []
    for run in RUNS.values():
        names += [run+'/run_metadata.json',run+'/records.json']
        for block in range(3):
            for stride in (8,12):
                base = run+f'/block{block}_stride{stride}/'
                names += [base+'predicted_poses.npz',base+'prediction_only_selection.json']
                for arm in ('A0P0','A0P1','A1P0','A1P1'):
                    names += [base+arm+'.npz',base+arm+'_sources.json']
                    names += [base+f'query{q}_{arm}_render.npz' for q in range(20,24)]
    return names


def old_evidence():
    result = [OLD+'/'+name for name in ('run_metadata.json','invocations.jsonl','schedule.json',
        'call_artifact_manifest.json','renderer_transformation.json','comparison_source.zip',
        'sealed_comparison_inputs.zip','summary.json')]
    for pair in common.planned_pairs():
        for method in pair['methods']:
            base = OLD+f"/calls/{pair['phase']}/round{pair['round']}/{pair['label']}/{method}/"
            result += [base+'render.npz',base+'trace.json']
    return result+['results/S10_renderer_comparison_independent_review/verification.json',
                   'results/S10_renderer_comparison_audit_v2/verification.json']


def identity(a):
    return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=common.digest_bytes(a.tobytes(order='C')))


def map_digest(values, sources, np):
    """Re-encode the documented digest directly, without building Memory objects."""
    h = hashlib.sha256(b'S6 normalized memory digest v1\0')
    for index in range(len(values['points'])):
        for name in ('points','normals','radii','colors'):
            a = np.asarray([values[name][index]] if name == 'radii' else values[name][index],dtype='<f8')
            if name == 'colors':
                h.update(b'color:array\0')
            h.update(np.asarray(a.shape,dtype='<i8').tobytes());h.update(a.tobytes())
    h.update(np.asarray(values['counts'],dtype='<i8').tobytes())
    ordered = [[i,sources[str(i)]] for i in range(len(values['points']))]
    h.update(json.dumps(ordered,separators=(',',':')).encode())
    return h.hexdigest()


def expected_state(poses, query, digest, threshold, np):
    """Independently assemble saved state identities from frozen numeric inputs."""
    axes = np.diag([1.,-1.,-1.,1.])
    fx,fy = 525.*299/640,525.*224/480
    cx,cy = (319.5+.5)*299/640-.5-37,(239.5+.5)*224/480-.5
    scale = 160/224.
    k = np.array([[fx*scale,0,cx*scale],[0,fy*scale,cy*scale],[0,0,1.]])
    return dict(memory_digest=digest,c2ws=[identity(p@axes) for p in poses[:20]],
        Ks=[identity(k)]*20,latents=[identity(np.array([i],dtype=np.float64)) for i in range(20)],
        encoder_embeddings=[identity(np.array([i+.25],dtype=np.float64)) for i in range(20)],
        surfel_Ks=[(fx+fy)/2*scale]*20,initial_threshold=threshold,
        target=identity((poses[query]@axes)[None]),optical_query=identity(poses[query]))


def check_trace(trace, reference, weights, counts, check, tag):
    expected = reference['expected']
    check(tag+'/status',trace['status'] == 'passed','metadata')
    for field,ref in (('official_trace',expected['official_trace']),
                      ('official_decision',expected['readouts']['official']),
                      ('returned_ordered_ids',expected['official_trace']['selected']),
                      ('observed_weights',weights),('observed_counts',counts)):
        check.same(tag+'/'+field,trace[field],ref)


def audit(args, output, report, check):
    reader = common.Reader(check);result = args.results.resolve(strict=True)
    meta = reader.json(result/'run_metadata.json')
    check('completed_gate',meta['status'] == 'completed' and meta['phase'] == 'complete','metadata')
    reader.hash(helper_path,AUDIT_HELPER_SHA)
    reader.hash(args.freeze,FREEZE_SHA);reader.hash(args.protocol,PROTOCOL_SHA)
    freeze = reader.json(args.freeze)
    check('freeze_schema',freeze['schema'] == 's11-renderer-regression-freeze-v1' and
          freeze['status'] == 'approved_for_execution','metadata')
    check('frozen_source_domain',set(freeze['execution_source_sha256']) == set(SOURCES),'integrity')
    check('known_runner',freeze['execution_source_sha256']['scripts/run_s11_renderer_regression.py'] == RUNNER_SHA,'integrity')
    check('frozen_input_domain',len(freeze['input_sha256']) == 316 and set(freeze['input_sha256']) == set(inputs()),'integrity')
    check('inherited_evidence_domain',len(freeze['s10_evidence_sha256']) == 682 and
          set(freeze['s10_evidence_sha256']) == set(old_evidence()),'integrity')
    check('metadata_identity',meta['freeze_sha256'] == FREEZE_SHA and meta['protocol_sha256'] == PROTOCOL_SHA and
          meta['s10_freeze_sha256'] == freeze['s10_freeze_sha256'] == common.FREEZE_SHA,'integrity')
    for field in ('execution_source_sha256','input_sha256','s10_evidence_sha256','review_evidence_sha256'):
        check.same('metadata/'+field,meta[field],freeze[field],'integrity')
        for name,value in freeze[field].items():
            reader.hash(common.below(ROOT,name),value)
    check('review_evidence_nonempty',bool(freeze['review_evidence_sha256']),'integrity')
    machine = re.findall(r'```s11-regression-json\s*\n(.*?)\n```',reader.bytes(args.protocol).decode(),re.S)
    check('one_machine_contract',len(machine) == 1,'metadata')
    contract = common.json_value(machine[0]);check.same('contract',meta['contract'],contract,'metadata')
    check('no_performance_contract',contract['performance_timing'] is False and contract['warmup_calls'] == 0 and
          contract['original_renderer_calls'] == 0,'metadata')
    check('environment',meta['environment']['versions'] == dict(python='3.12.14',numpy='2.3.5',torch='2.7.0',scipy='1.16.2') and
          meta['environment']['torch_threads'] == meta['environment']['torch_interop_threads'] == 8 and
          meta['environment']['torch_default_dtype'] == 'torch.float32','metadata')
    for field,value in dict(planned_conditions=192,new_planned_invocations=168,inherited_planned_conditions=24,
        original_renderer_calls=0,new_candidate_calls_started=168,completed_new_invocations=168,
        inherited_conditions=24,covered_conditions=192,distinct_seen_queries=24,new_candidate_maps=42).items():
        check.same('metadata/'+field,meta[field],value,'metadata')
    for field in ('raw_pixels_decoded','gt_loaded','model_loaded','performance_measured'):
        check('flag/'+field,meta[field] is False,'metadata')
    for field in ('source_inputs_inherited_evidence_unchanged','in_memory_inputs_unchanged','all_actual_arrays_and_complete_traces_saved'):
        check('flag/'+field,meta[field] is True,'metadata')
    stamps = [freeze['frozen_utc']]+[meta[k] for k in ('started_utc','inputs_sealed_utc','inherited_24_verified_utc',
        'initialization_completed_utc','completed_utc')]
    times = [datetime.fromisoformat(s) for s in stamps]
    check('recorded_time_order',all(t.tzinfo is not None for t in times) and all(a <= b for a,b in zip(times,times[1:])),'metadata')
    check('recorded_soft_budget',0 < meta['wall_elapsed_for_budget_seconds'] <= 600 and
          0 < meta['process_peak_rss_bytes'] <= 16*1024**3,'metadata')
    prior_path = ROOT/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json'
    reader.hash(prior_path,common.FREEZE_SHA);prior = reader.json(prior_path)
    check.same('unchanged_S10_sources',{n:freeze['execution_source_sha256'][n] for n in common.SOURCES},
               prior['execution_source_sha256'],'integrity')
    check('S10_inputs_unchanged',all(freeze['input_sha256'][n] == h for n,h in prior['input_sha256'].items()),'integrity')
    source_members = dict(freeze['execution_source_sha256'],**{'frozen_protocol.md':PROTOCOL_SHA,
        'execution_freeze.json':FREEZE_SHA,'S10_execution_freeze.json':common.FREEZE_SHA})
    archives = [('regression_source.zip','source_archive_sha256',source_members),
        ('sealed_regression_inputs.zip','input_archive_sha256',freeze['input_sha256']),
        ('inherited_S10_evidence.zip','s10_evidence_archive_sha256',freeze['s10_evidence_sha256']),
        ('sealed_review_evidence.zip','review_evidence_archive_sha256',freeze['review_evidence_sha256'])]
    source_payloads = None
    for filename,field,members in archives:
        reader.hash(result/filename,meta[field])
        payload = common.validate_archive(result/filename,members,reader,check)
        if filename == 'regression_source.zip':
            source_payloads = payload
        del payload
    reader.hash(result/'renderer_transformation.json',meta['renderer_transformation_sha256'])
    transform = reader.json(result/'renderer_transformation.json')
    check.same('unchanged_transformation',transform,reader.json(ROOT/OLD/'renderer_transformation.json'),'integrity')
    common.verify_transformation(transform,source_payloads,freeze,check)
    tree = ast.parse(source_payloads['scripts/run_s11_renderer_regression.py'].decode())
    calls = [n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    check('source/no_performance_clock',not any(isinstance(n.func,ast.Attribute) and n.func.attr in
          ('perf_counter','perf_counter_ns','process_time','process_time_ns') for n in calls),'source_order')
    check('source/one_context_call_site',sum(isinstance(n.func,ast.Attribute) and n.func.attr == 'get_context_info'
          for n in calls) == 1,'source_order')
    planned = plan();new = [p for p in planned if p['evidence'] == 'new_candidate']
    inherited_plan = [p for p in planned if p['evidence'] == 'inherited_S10']
    check.same('schedule',reader.json(result/'schedule.json'),planned)
    reader.hash(result/'coverage.json',meta['coverage_sha256'])
    coverage = reader.json(result/'coverage.json');inherited = reader.json(result/'inherited_coverage.json')
    lines = reader.bytes(result/'invocations.jsonl').decode().splitlines()
    check('168_actual_invocation_rows',len(lines) == 168 and all(lines))
    rows = [common.json_value(line) for line in lines]
    check.same('192_coverage_union',coverage,sorted([*inherited,*rows],key=lambda x:x['condition_index']))
    check('168_new_24_inherited',len(rows) == 168 and len(inherited) == 24 and len(coverage) == 192)
    for actual,expected in zip(coverage,planned):
        for key,value in expected.items():
            check.same('coverage/'+str(expected['condition_index'])+'/'+key,actual[key],value)
    reader.hash(result/'call_artifact_manifest.json',meta['call_artifact_manifest_sha256'])
    manifest = reader.json(result/'call_artifact_manifest.json');inventory = {p['path']:p for p in manifest}
    expected_names = {f"calls/{p['label']}/{f}" for p in new for f in ('render.npz','trace.json')}
    actual_names = {str(p.relative_to(result)) for p in (result/'calls').rglob('*') if p.is_file()}
    check('336_actual_file_inventory',len(manifest) == len(inventory) == 336 and
          set(inventory) == expected_names == actual_names,'integrity')
    for ordinal,(row,expected) in enumerate(zip(rows,new)):
        for key,value in expected.items():check.same(f'row{ordinal}/'+key,row[key],value)
        check(f'row{ordinal}/status_index',row['status'] == 'passed' and row['method'] == 'candidate' and
              row['invocation_index'] == ordinal and 'elapsed_ns' not in row,'metadata')
        for kind,suffix in (('render','render.npz'),('trace','trace.json')):
            name = f"calls/{row['label']}/{suffix}";path = common.below(result,name)
            check(f'row{ordinal}/'+kind+'_path',row[kind+'_path'] == name,'integrity')
            reader.hash(path,row[kind+'_sha256'])
            check(f'row{ordinal}/'+kind+'_manifest',inventory[name]['sha256'] == row[kind+'_sha256'] and
                  inventory[name]['bytes'] == path.stat().st_size,'integrity')
    # The predecessor's entire 672-file domain is hash-bound; only 24 of its NPZs
    # are decoded here. The completed S10 audits already compared all 336 calls.
    old_meta = reader.json(ROOT/OLD/'run_metadata.json')
    check('S10_completed',old_meta['status'] == 'completed' and old_meta['phase'] == 'complete' and
          old_meta['completed_invocations'] == 336,'metadata')
    old_manifest = reader.json(ROOT/OLD/'call_artifact_manifest.json')
    old_actual = {str(p.relative_to(ROOT/OLD)) for p in (ROOT/OLD/'calls').rglob('*') if p.is_file()}
    check('S10_672_inventory',len(old_manifest) == len(old_actual) == 672 and
          {x['path'] for x in old_manifest} == old_actual,'integrity')
    for item in old_manifest:
        p = common.below(ROOT/OLD,item['path'])
        check('S10_manifest/'+item['path'],freeze['s10_evidence_sha256'][str(p.relative_to(ROOT))] == item['sha256'] and
              p.stat().st_size == item['bytes'],'integrity')
    old_rows = [common.json_value(line) for line in reader.bytes(ROOT/OLD/'invocations.jsonl').decode().splitlines()]
    check('S10_336_records',len(old_rows) == 336,'integrity')
    selected_old = {(r['stage'],r['block'],r['query']):r for r in old_rows if
                    r['phase'] == 'correctness' and r['method'] == 'candidate'}
    check('24_inherited_prior_keys',len(selected_old) == 24)
    for row,expected in zip(inherited,inherited_plan):
        previous = selected_old[(expected['stage'],expected['block'],expected['query'])]
        want = dict(**expected,status='passed',new_renderer_call=False,prior_pair_index=previous['pair_index'],
            prior_method='candidate',prior_phase='correctness',render_path=OLD+'/'+previous['render_path'],
            render_sha256=previous['render_sha256'],trace_path=OLD+'/'+previous['trace_path'],trace_sha256=previous['trace_sha256'])
        check.same('inherited/'+expected['label'],row,want)
    check('S10_different_author_pass',reader.json(ROOT/'results/S10_renderer_comparison_independent_review/verification.json')['status'] == 'PASS','metadata')
    check('S10_different_script_pass',reader.json(ROOT/'results/S10_renderer_comparison_audit_v2/verification.json')['status'] == 'passed','metadata')
    # Numerical work starts only after all of the above completed/identity gates.
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key] = '1'
    import numpy as np
    check('audit_numpy_version',np.__version__ == '2.3.5','metadata')
    def arrays(path):
        reader.hash(path)
        with np.load(path,allow_pickle=False) as z:values = {k:z[k] for k in z.files}
        return values
    def buffers(path):
        values = arrays(path)
        check('render_schema/'+str(path),set(values) == common.BUFFER_NAMES and
              all(a.shape == (160,160) and np.isfinite(a).all() for a in values.values()))
        return values
    refs,poses,maps = {},{},{}
    for stage,run_name in RUNS.items():
        run = ROOT/run_name;prior_meta = reader.json(run/'run_metadata.json')
        check(stage+'/completed',prior_meta['status'] == 'completed' and prior_meta['phase'] == 'complete','metadata')
        records = reader.json(run/'records.json');record_index = {(r['block'],r['stride'],r['frame']):r for r in records}
        check(stage+'/unique_records',len(record_index) == len(records))
        for block in range(3):
            for stride in (8,12):
                base = run/f'block{block}_stride{stride}';key = (stage,block,stride)
                selection = reader.json(base/'prediction_only_selection.json')
                check.same(str(key)+'/query_domain',[q['frame'] for q in selection['queries']],[20,21,22,23])
                case_seals = [x for x in prior_meta['cases'] if x['block'] == block and x['stride'] == stride]
                check(str(key)+'/one_case_seal',len(case_seals) == 1 and case_seals[0]['directory'] == base.name,'integrity')
                for name in inputs():
                    if (ROOT/name).parent == base:
                        check('case_seal/'+name,freeze['input_sha256'][name] == case_seals[0]['sealed_files'][Path(name).name],'integrity')
                pose_values = arrays(base/'predicted_poses.npz')
                check(str(key)+'/pose_schema',set(pose_values) == {'poses'} and pose_values['poses'].shape == (24,4,4) and
                      np.isfinite(pose_values['poses']).all())
                poses[key] = pose_values['poses']
                for arm in ('A0P0','A0P1','A1P0','A1P1'):
                    values = arrays(base/f'{arm}.npz');sources = reader.json(base/f'{arm}_sources.json')
                    n = len(values['points'])
                    check(str(key)+(arm)+'/map_schema',set(values) == {'points','normals','radii','colors','counts'} and
                          all(np.isfinite(a).all() for a in values.values()) and set(sources) == {str(i) for i in range(n)})
                    digest = map_digest(values,sources,np)
                    check(str(key)+arm+'/map_digest',digest == selection['maps'][arm]['digest'])
                    maps[(*key,arm)] = digest
                    for item in selection['queries']:
                        query = item['frame'];expected = item['maps'][arm]
                        render = buffers(base/f'query{query}_{arm}_render.npz')
                        weights,counts = common.recompute_votes(render,sources,np)
                        label = f'{stage}_block{block}_stride{stride}_{arm}_query{query}'
                        check.same(label+'/recomputed_votes',weights,expected['official_trace']['weights'])
                        check.same(label+'/recomputed_counts',counts,expected['official_trace']['candidate_counts'])
                        check.same(label+'/record_IDs',expected['official_trace']['selected'],
                                   record_index[(block,stride,query)]['readouts'][arm]['official']['selected'])
                        common.check_decision_logic(expected['readouts']['official'],counts,check,label+'/NMS_branch')
                        refs[(*key,arm,query)] = dict(expected=expected,render=render,weights=weights,counts=counts)
    check('192_refs_48_digests_12_pose_sets',len(refs) == 192 and len(maps) == 48 and len(poses) == 12)
    reader.hash(result/'initial_state_identities.json',meta['initial_state_identities_sha256'])
    initial = reader.json(result/'initial_state_identities.json')
    check('168_initial_states',set(initial) == {p['label'] for p in new})
    for row in [*inherited,*rows]:
        tag = row['label'];key = (row['stage'],row['block'],row['stride'],row['arm'],row['query'])
        reference = refs[key];parent = ROOT if row['evidence'] == 'inherited_S10' else result
        render_path,trace_path = common.below(parent,row['render_path']),common.below(parent,row['trace_path'])
        reader.hash(render_path,row['render_sha256']);reader.hash(trace_path,row['trace_sha256'])
        actual,trace = buffers(render_path),reader.json(trace_path)
        for name in common.BUFFER_NAMES:
            a,b = actual[name],reference['render'][name]
            check(tag+'/'+name+'/C_bytes',a.dtype == b.dtype and a.shape == b.shape and a.tobytes(order='C') == b.tobytes(order='C'))
            check.same(tag+'/'+name+'/identity',trace['render_arrays'][name],identity(a),'integrity')
        check_trace(trace,reference,reference['weights'],reference['counts'],check,tag)
        if row['evidence'] == 'new_candidate':
            state = expected_state(poses[key[:3]],row['query'],maps[key[:4]],
                                   reference['expected']['official_trace']['nms_initial_threshold'],np)
            check.same(tag+'/independently_built_initial_state',initial[tag],state)
            check.same(tag+'/saved_state_after',trace['state_after'],state)
            check(tag+'/state_before_sha',trace['state_before_sha256'] ==
                  common.digest_bytes(json.dumps(initial[tag],sort_keys=True).encode()),'integrity')
    reader.hash(result/'summary.json',meta['summary_sha256'])
    expected_summary = dict(status='passed',full_conditions=192,new_candidate_invocations=168,inherited_conditions=24,
        distinct_seen_queries=24,physical_scenes=2,original_map_variants=48,new_candidate_maps=42,
        all_exact_output_checks_passed=True,performance_measured=False,limitations=meta['limitations'])
    check.same('summary_all_fields',reader.json(result/'summary.json'),expected_summary)
    common.dump(output/'recomputed_summary.json',expected_summary)
    reader.finish();common.dump(output/'authenticated_input_files.json',reader.seen)
    report.update(status='passed',new_invocations_checked=168,inherited_conditions_checked=24,total_conditions_checked=192,
        actual_arrays_C_byte_compared=576,complete_trace_pairs_checked=192,saved_states_independently_rebuilt=168,
        map_digests_recomputed=48,reference_votes_recomputed=192,NMS_recorded_distance_sequences_replayed=192,
        numerical_modules_imported=['numpy'],renderer_calls=0,performance_runs=0,
        original_files_unchanged_during_audit=True,recomputed_summary_sha256=common.digest_bytes((output/'recomputed_summary.json').read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('results','protocol','freeze','output'):parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args();raw = args.output.absolute()
    if raw.exists() or raw.is_symlink():raise ValueError('Fresh audit output required; preserve failures')
    output = raw.resolve();result = args.results.resolve(strict=True)
    if output.is_relative_to(result) or any(output.is_relative_to(ROOT/p) for p in ('src','scripts','docs','data','vendor')):
        raise ValueError('Audit output overlaps protected material')
    output.mkdir(parents=True,exist_ok=False)
    check = common.Check()
    report = dict(status='running',started_utc=common.now(),same_author_as_runner=True,
        auditor_sha256=common.digest_bytes(Path(__file__).read_bytes()),helper_sha256=AUDIT_HELPER_SHA,
        parameters={k:str(getattr(args,k)) for k in ('results','protocol','freeze','output')},checks=check.items,
        limitations=[
            'Same author as S11 runner; different audit script, with authenticated prior audit utilities, not independent authorship.',
            'No production validation, Torch, renderer, model, GT, raw image or performance execution.',
            '192 conditions remain 24 related seen queries across two scenes; 24 calls are inherited from completed S10.',
            'All 168 saved state_after and initial identities are rebuilt from frozen map/pose inputs and fixed initialization rules.',
            'NMS branch logic replays recorded distances and full traces match prior references; camera distances are not regenerated.',
            'Historical flags and order remain recorded evidence plus fixed source, not an OS trace or complete runtime memory dump.',
            'Finite regression and AST scope checks do not prove universal equivalence, unseen generalization, innovation, or video quality.'])
    common.dump(output/'verification.json',report)
    (output/'auditor_source.py').write_bytes(Path(__file__).read_bytes())
    (output/'prior_audit_helper.py').write_bytes(helper_path.read_bytes())
    try:audit(args,output,report,check)
    except Exception:report.update(status='failed',traceback=traceback.format_exc())
    report.update(completed_utc=common.now(),checks_count=len(check.items),checks_by_kind=dict(Counter(x['kind'] for x in check.items)))
    common.dump(output/'verification.json',report)
    print(json.dumps({k:report.get(k) for k in ('status','started_utc','completed_utc','checks_count','checks_by_kind')},ensure_ascii=False))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':raise SystemExit(main())
