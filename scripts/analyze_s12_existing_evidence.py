#!/usr/bin/env python3
"""Summarize already saved S7/S8 selections; never generate a new selection.

Standard library only. No NPZ, GT, images, model, renderer or selector execution.
The existing support values are averaged; support masks are not recomputed.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import traceback

ROOT = Path(__file__).resolve().parents[1]
FREEZE_SHA = 'd51522ebca03450293e23072b6c6f0a4656d1a7d61f4b8f99a051b1f392a20b3'
RUNS = {'S7':'results/S7_event_replay','S8':'results/S8_event_replay_v2'}
ARMS = ('A0P0','A0P1','A1P0','A1P1')
MODES = ('official','candidate_no_nms','all20_nms','all20_no_nms')
PAIRS = [('geometry_gate_vs_full20_same_NMS','official','all20_nms'),
         ('geometry_gate_vs_full20_both_no_NMS','candidate_no_nms','all20_no_nms'),
         ('remove_NMS_same_geometry_candidates','candidate_no_nms','official'),
         ('remove_NMS_same_full20_candidates','all20_no_nms','all20_nms'),
         ('mixed_geometry_NMS_vs_pose_no_NMS','official','all20_no_nms')]

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def mean(x):return math.fsum(x)/len(x)
def require(value,message):
    if not value:raise ValueError(message)


def analyze(output,report):
    touched = {}
    def read(path):
        data = path.read_bytes();digest = hashlib.sha256(data).hexdigest()
        if str(path) in touched:require(touched[str(path)] == digest,'Source changed while reading')
        touched[str(path)] = digest
        return json.loads(data)
    freeze_path = ROOT/'docs/S11_RENDERER_REGRESSION_EXECUTION_FREEZE.json'
    freeze = read(freeze_path);require(touched[str(freeze_path)] == FREEZE_SHA,'S11 input seal changed')
    def old_json(name):
        path = ROOT/name;result = read(path)
        require(touched[str(path)] == freeze['input_sha256'][name],'Sealed S7/S8 input changed: '+name)
        return result
    flat,control_checks,factor_pairs = [],[],[]
    for stage,run in RUNS.items():
        meta = old_json(run+'/run_metadata.json');records = old_json(run+'/records.json')
        require(meta['status'] == 'completed' and meta['phase'] == 'complete','Old run incomplete')
        require(len(records) == 24,'Expected 3 blocks × 2 strides × 4 queries')
        indexed = {(r['block'],r['stride'],r['frame']):r for r in records}
        require(len(indexed) == 24,'Duplicate old record')
        independent_of_map = {}
        for block in range(3):
            for stride in (8,12):
                base = run+f'/block{block}_stride{stride}'
                selection = old_json(base+'/prediction_only_selection.json')
                seal = next(c for c in meta['cases'] if c['block'] == block and c['stride'] == stride)
                require(seal['sealed_files']['prediction_only_selection.json'] == freeze['input_sha256'][base+'/prediction_only_selection.json'],
                        'Historical case seal differs')
                require([q['frame'] for q in selection['queries']] == [20,21,22,23],'Query domain differs')
                for item in selection['queries']:
                    query = item['frame'];record = indexed[(block,stride,query)]
                    require(record['split'] == ('development' if stage == 'S7' and block == 0 else 'test'),'Split changed')
                    require(record['valid_pixels'] > 0,'Empty original scoring mask')
                    for arm in ARMS:
                        trace = item['maps'][arm];decisions = trace['readouts'];original = trace['official_trace']
                        require(set(decisions) == set(MODES),'Readout domain differs')
                        counts = original['candidate_counts'];weights = original['weights']
                        pool = [frame for frame,count in counts for _ in range(count)]
                        require(all(type(count) is int and count in (0,1) for _,count in counts),'Unexpected repeated candidate allocation')
                        require(decisions['official']['expanded_candidates'] == decisions['candidate_no_nms']['expanded_candidates'] == pool,
                                'NMS ablation changed geometric candidate input')
                        require(decisions['all20_nms']['expanded_candidates'] == decisions['all20_no_nms']['expanded_candidates'] == list(range(20)),
                                'Full20 pool differs')
                        require(decisions['official']['sorted_frames'] == decisions['candidate_no_nms']['sorted_frames'] and
                                decisions['all20_nms']['sorted_frames'] == decisions['all20_no_nms']['sorted_frames'],
                                'Paired NMS ablation changed pose sorting')
                        require(decisions['official']['nms'] is True and decisions['candidate_no_nms']['nms'] is False and
                                decisions['all20_nms']['nms'] is True and decisions['all20_no_nms']['nms'] is False,'NMS flags differ')
                        require(len({d['initial_threshold'] for d in decisions.values()}) == 1,'NMS initial threshold differs')
                        values = record['readouts'][arm]
                        for name in MODES:
                            ids = values[name]['selected']
                            require(ids == decisions[name]['selected'] and len(ids) == len(set(ids)) == 4 and
                                    all(type(i) is int and 0 <= i < 20 for i in ids),'Saved output IDs mismatch/invalid')
                            require(math.isfinite(values[name]['support']) and 0 <= values[name]['support'] <= 1,'Invalid saved support')
                            if name.startswith('all20_'):
                                key=(block,query,name)
                                value=(ids,values[name]['support'],record['valid_pixels'])
                                if key in independent_of_map:require(independent_of_map[key] == value,'Full20 depends on map or stride')
                                independent_of_map[key]=value
                        require(values['official']['selected'] == original['selected'],'Official IDs differ')
                        flat.append(dict(stage=stage,block=block,split=record['split'],stride=stride,query=query,arm=arm,
                            valid_pixels=record['valid_pixels'],visible_source_count=len(weights),candidate_count=len(pool),
                            candidate_ids=pool,weights=weights,readouts=values,all20_support=record['all20_support']))
                        control_checks.append(dict(stage=stage,block=block,stride=stride,query=query,arm=arm,
                            output_count_all_four=True,same_geometric_pool_for_NMS_pair=True,
                            same_all20_pool_for_NMS_pair=True,same_pose_sort_within_each_NMS_pair=True,
                            initial_threshold_shared=True,all20_map_and_stride_invariant=True))
                    for association in (0,1):
                        a,b = f'A{association}P0',f'A{association}P1'
                        x,y = item['maps'][a],item['maps'][b]
                        xp,yp = x['readouts']['official']['expanded_candidates'],y['readouts']['official']['expanded_candidates']
                        xi,yi = x['official_trace']['selected'],y['official_trace']['selected']
                        same_pool = xp == yp
                        if same_pool:require(xi == yi,'Same pool and same downstream rules changed official output')
                        require(seal['sealed_files'][a+'_sources.json'] == seal['sealed_files'][b+'_sources.json'],
                                'Fixed association did not preserve source file identity')
                        factor_pairs.append(dict(stage=stage,block=block,split=record['split'],stride=stride,query=query,
                            association=association,same_source_file_sha256=seal['sealed_files'][a+'_sources.json'],
                            weights_changed=x['official_trace']['weights'] != y['official_trace']['weights'],
                            candidate_pool_changed=not same_pool,ordered_output_changed=xi != yi,
                            support_delta_pp=100*(record['readouts'][b]['official']['support']-record['readouts'][a]['official']['support'])))
    require(len(flat) == len(control_checks) == 192 and len(factor_pairs) == 96,'Incomplete saved condition domain')
    aggregates,paired = [],[]
    for stage,split in (('S7','test'),('S7','development'),('S8','test')):
        for stride in (8,12):
            for arm in ARMS:
                rows=[r for r in flat if (r['stage'],r['split'],r['stride'],r['arm']) == (stage,split,stride,arm)]
                require(len(rows) == (8 if stage == 'S7' and split == 'test' else 4 if split == 'development' else 12),'Stratum size differs')
                aggregates.append(dict(stage=stage,split=split,stride=stride,arm=arm,queries=len(rows),
                    support_percent={name:100*mean([r['readouts'][name]['support'] for r in rows]) for name in MODES},
                    candidate_count_range=[min(r['candidate_count'] for r in rows),max(r['candidate_count'] for r in rows)],
                    visible_sources_range=[min(r['visible_source_count'] for r in rows),max(r['visible_source_count'] for r in rows)],
                    valid_pixels_range=[min(r['valid_pixels'] for r in rows),max(r['valid_pixels'] for r in rows)],
                    all20_support_percent=100*mean([r['all20_support'] for r in rows])))
                for name,left,right in PAIRS:
                    deltas=[100*(r['readouts'][left]['support']-r['readouts'][right]['support']) for r in rows]
                    paired.append(dict(stage=stage,split=split,stride=stride,arm=arm,comparison=name,left=left,right=right,
                        queries=len(rows),delta_pp_mean=mean(deltas),positive=sum(d>0 for d in deltas),
                        negative=sum(d<0 for d in deltas),equal=sum(d==0 for d in deltas),
                        changed_order=sum(r['readouts'][left]['selected'] != r['readouts'][right]['selected'] for r in rows),
                        changed_set=sum(set(r['readouts'][left]['selected']) != set(r['readouts'][right]['selected']) for r in rows),
                        per_query=[dict(block=r['block'],query=r['query'],delta_pp=d) for r,d in zip(rows,deltas)]))
    factor_summary=[]
    for stage,split in (('S7','test'),('S7','development'),('S8','test')):
        for stride in (8,12):
            for association in (0,1):
                rows=[r for r in factor_pairs if (r['stage'],r['split'],r['stride'],r['association']) == (stage,split,stride,association)]
                factor_summary.append(dict(stage=stage,split=split,stride=stride,association=association,queries=len(rows),
                    weights_changed=sum(r['weights_changed'] for r in rows),candidate_pool_changed=sum(r['candidate_pool_changed'] for r in rows),
                    ordered_output_changed=sum(r['ordered_output_changed'] for r in rows),
                    changed_weights_but_same_pool=sum(r['weights_changed'] and not r['candidate_pool_changed'] for r in rows),
                    support_delta_pp_mean=mean([r['support_delta_pp'] for r in rows])))
    numerical=dict(scope='Already saved support and selection records only; no new selection or scoring.',
        aggregates=aggregates,paired_differences=paired,fixed_association_position_pairs=factor_pairs,
        fixed_association_summary=factor_summary,
        all_condition_candidate_counts=dict(Counter(r['candidate_count'] for r in flat)),
        all_condition_visible_source_counts=dict(Counter(r['visible_source_count'] for r in flat)))
    save(output/'saved_condition_records.json',flat);save(output/'control_checks.json',control_checks)
    save(output/'summary.json',numerical)
    for name,digest in touched.items():require(sha(Path(name)) == digest,'Original input changed during analysis')
    save(output/'input_sha256.json',touched)
    report.update(status='completed',saved_map_query_conditions=192,saved_readout_scores=768,
        different_queries={'S7_test':8,'S7_development':4,'S8_test':12},control_pairs_checked=192,
        numerical_summary_sha256=sha(output/'summary.json'),input_files_unchanged=True,
        actual_selector_invocations=0,actual_renderer_invocations=0,NPZ_or_raw_data_reads=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.absolute()
    require(not output.exists() and not output.is_symlink(),'Use a new output; preserve failed attempts')
    output=output.resolve();require(not any(output.is_relative_to(ROOT/n) for n in ('src','scripts','docs','data','vendor','results/S7_event_replay','results/S8_event_replay_v2')),'Output overlaps originals')
    output.mkdir(parents=True,exist_ok=False)
    report=dict(status='running',started_utc=utc(),script_sha256=sha(Path(__file__)),
        role='Retrospective evidence audit after S11, not a preregistered experiment or independent performance replication.')
    save(output/'run_metadata.json',report);(output/'analysis_source.py').write_bytes(Path(__file__).read_bytes())
    try:analyze(output,report)
    except Exception:report.update(status='failed',traceback=traceback.format_exc())
    report['completed_utc']=utc();save(output/'run_metadata.json',report)
    print(json.dumps(report,ensure_ascii=False))
    return 0 if report['status'] == 'completed' else 1

if __name__ == '__main__':raise SystemExit(main())
