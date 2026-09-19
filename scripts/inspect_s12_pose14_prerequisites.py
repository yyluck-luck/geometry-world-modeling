#!/usr/bin/env python3
"""Inspect saved all20 trace structure and ties; do not form or run pose14."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
RUNS={'S7':'results/S7_event_replay','S8':'results/S8_event_replay_v2'}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.absolute()
    require(not out.exists() and not out.is_symlink(),'New output required')
    out=out.resolve();require(not any(out.is_relative_to(ROOT/p) for p in ('src','scripts','docs','data','vendor','results/S7_event_replay','results/S8_event_replay_v2')),'Output overlaps originals')
    out.mkdir(parents=True,exist_ok=False);started=utc();sources={};unique={};geometry=[]
    for stage,run in RUNS.items():
        for block in range(3):
            for stride in (8,12):
                p=ROOT/run/f'block{block}_stride{stride}/prediction_only_selection.json'
                x=json.loads(p.read_text());sources[str(p)]=sha(p)
                for q in x['queries']:
                    key=(stage,block,q['frame'])
                    for arm,entry in q['maps'].items():
                        t=entry['readouts']['all20_nms'];plain=entry['readouts']['all20_no_nms']
                        require(t['expanded_candidates']==list(range(20)),'Missing full20 frame list')
                        require(len(t['distances_float32'])==20 and len(t['sorted_frames'])==20 and set(t['sorted_frames'])==set(range(20)),'Missing full20 rank/distance')
                        require(t['sorted_frames']==plain['sorted_frames'] and t['distances_float32']==plain['distances_float32'],'NMS control rank mismatch')
                        require(all(math.isfinite(v) and v==struct.unpack('f',struct.pack('f',v))[0] for v in t['distances_float32']),'Distance is not stored finite FP32')
                        require(math.isfinite(t['initial_threshold']) and t['initial_threshold']>=0,'Invalid threshold')
                        if key in unique:require(unique[key]==t,'Full20 trace differs by arm or stride')
                        else:unique[key]=t
                        geometry.append(dict(stage=stage,block=block,stride=stride,query=q['frame'],arm=arm,
                            saved_geometry14_cutoff_gap=entry['official_trace']['cutoff_gap_14_15']))
    rows=[]
    for (stage,block,query),trace in unique.items():
        d=trace['distances_float32'];rank=trace['sorted_frames'];ordered=[d[f] for f in rank]
        require(all(a<=b for a,b in zip(ordered,ordered[1:])),'Stored ranks not nondecreasing')
        compared=set();directions=set();self_count=0;relax=0;fallback=0
        for step in trace['steps']:
            if 'comparisons' in step:
                for other,distance in step['comparisons']:
                    require(math.isfinite(distance),'Nonfinite recorded NMS distance')
                    directions.add((step['frame'],other))
                    if step['frame']==other:self_count+=1
                    else:compared.add(tuple(sorted((step['frame'],other))))
            relax+=int('relax_from' in step);fallback+=int('fallback_added' in step)
        rows.append(dict(stage=stage,block=block,query=query,split='development' if stage=='S7' and block==0 else 'test',
            saved_query_distances=20,saved_full_sorted_candidates=20,
            query_distance_ties=20-len(set(d)),pose_rank14_15_gap=ordered[14]-ordered[13],
            recorded_unique_unordered_history_pairs=len(compared),all_unordered_history_pairs=190,
            has_all_unordered_history_pair_distances=len(compared)==190,
            recorded_unique_directed_pairs=len(directions),recorded_self_comparisons=self_count,
            initial_threshold=trace['initial_threshold'],recorded_relaxations=relax,recorded_fallbacks=fallback))
    require(len(rows)==24 and len(geometry)==192,'Incomplete static domain')
    for p,h in sources.items():require(sha(Path(p))==h,'Source changed')
    result=dict(status='completed',started_utc=started,completed_utc=utc(),script_sha256=sha(Path(__file__)),
        input_sha256=sources,scope='Saved JSON field/rank/tie audit only. No candidate14 pool or new selected IDs generated, no NPZ opened, no selector/renderer run.',
        queries=rows,geometry_cutoff_fields=geometry,
        summary=dict(distinct_queries=24,full_trace_identical_across_8_variants=True,
            query_distance_tie_queries=sum(r['query_distance_ties']>0 for r in rows),
            zero_pose14_boundary_queries=sum(r['pose_rank14_15_gap']==0 for r in rows),
            pose14_boundary_gap_range=[min(r['pose_rank14_15_gap'] for r in rows),max(r['pose_rank14_15_gap'] for r in rows)],
            recorded_pair_distance_count_range=[min(r['recorded_unique_unordered_history_pairs'] for r in rows),max(r['recorded_unique_unordered_history_pairs'] for r in rows)],
            full_pairwise_distance_tables=sum(r['has_all_unordered_history_pair_distances'] for r in rows),
            geometry14_zero_boundary_conditions=sum(r['saved_geometry14_cutoff_gap']==0 for r in geometry),
            geometry14_boundary_gap_range=[min(r['saved_geometry14_cutoff_gap'] for r in geometry),max(r['saved_geometry14_cutoff_gap'] for r in geometry)],
            actual_new_selections=0))
    (out/'inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (out/'inspection_source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'status':result['status'],'started_utc':started,'completed_utc':result['completed_utc'],'summary':result['summary']},ensure_ascii=False))
if __name__=='__main__':main()
