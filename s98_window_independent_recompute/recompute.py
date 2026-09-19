#!/usr/bin/env python3
"""Independent S8 fixed-window qualification audit for local TUM development sequences.

Reimplements timestamp parsing, strict greedy RGB-D association, GT continuous
interval construction, and S8 fixed-duration window selection without importing
production prepare_s8_inputs.py. It does not decode images, read pose values,
or run a model.
"""
from __future__ import annotations
import bisect, hashlib, json, math
from pathlib import Path
from collections import Counter

LENGTH=8.840
GT_GAP=0.100
ASSOC_MAX=0.020
SNAP_MAX=0.050
COUNT=24
WINDOW_GAP=0.100

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
SEQS={
    'fr1_xyz': ROOT/'data/tum/rgbd_dataset_freiburg1_xyz',
    'fr2_desk_timestamp_guard': ROOT/'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk',
}
OUT=ROOT/'work/agents/s98_window_independent_recompute'


def sha(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def parse_ts(path):
    rows=[]
    for ln, raw in enumerate(path.read_text().splitlines(),1):
        line=raw.partition('#')[0].strip()
        if not line: continue
        f=line.split()
        if len(f)!=2: raise ValueError(f'{path}:{ln}: expected 2 fields')
        t=float(f[0])
        if not math.isfinite(t): raise ValueError(f'{path}:{ln}: nonfinite')
        rows.append((t,f[1],ln))
    rows.sort(key=lambda x:x[0])
    if len({x[0] for x in rows})!=len(rows): raise ValueError(f'{path}: duplicate timestamp')
    return rows

def parse_gt_intervals(path):
    times=[]
    for ln,raw in enumerate(path.read_text().splitlines(),1):
        line=raw.partition('#')[0].strip()
        if not line: continue
        f=line.split()
        if len(f)!=8: raise ValueError(f'{path}:{ln}: expected 8 fields')
        t=float(f[0])
        if not math.isfinite(t): raise ValueError(f'{path}:{ln}: nonfinite')
        times.append(t)
    times.sort()
    if not times or any(b<=a for a,b in zip(times,times[1:])):
        raise ValueError(f'{path}: empty/nonincreasing/duplicate GT')
    intervals=[[times[0],times[0]]]
    for a,b in zip(times,times[1:]):
        if b-a>GT_GAP: intervals.append([b,b])
        else: intervals[-1][1]=b
    return times, intervals

def interval_at(t, intervals):
    starts=[x[0] for x in intervals]
    i=bisect.bisect_right(starts,t)-1
    return i if i>=0 and t<=intervals[i][1] else None

def associate(rgb,depth):
    # Same declared rule, independently reimplemented: enumerate strict candidates,
    # deterministic (abs dt, RGB time, depth time) sort, greedy unique acceptance.
    candidates=[]
    dts=[d[0] for d in depth]
    for i,r in enumerate(rgb):
        lo=bisect.bisect_left(dts,r[0]-ASSOC_MAX)
        hi=bisect.bisect_right(dts,r[0]+ASSOC_MAX)
        for j in range(lo,hi):
            dt=abs(r[0]-depth[j][0])
            if dt<ASSOC_MAX:
                candidates.append((dt,r[0],depth[j][0],i,j))
    candidates.sort()
    used_r=set(); used_d=set(); pairs=[]
    for dt,rt,dtstamp,i,j in candidates:
        if i in used_r or j in used_d: continue
        used_r.add(i); used_d.add(j)
        pairs.append({'rgb_index':i,'depth_index':j,'rgb':rgb[i],'depth':depth[j], 'abs_dt':dt})
    pairs.sort(key=lambda x:x['rgb'][0])
    return pairs, len(candidates)

def plan(pairs, intervals):
    valid=[]; excluded=Counter(); excluded_examples=[]
    for idx,p in enumerate(pairs):
        ri=interval_at(p['rgb'][0], intervals); di=interval_at(p['depth'][0], intervals)
        if ri is None or di!=ri:
            reason='both_times_require_same_gt_interval'; excluded[reason]+=1
            if len(excluded_examples)<20: excluded_examples.append({'pair_index':idx,'reason':reason,'rgb_t':p['rgb'][0],'depth_t':p['depth'][0],'rgb_interval':ri,'depth_interval':di})
            continue
        valid.append({'pair_index':idx,'rgb_t':p['rgb'][0],'depth_t':p['depth'][0],'rgb':p['rgb'],'depth':p['depth'],'gt_interval':ri,'abs_dt':p['abs_dt']})
    segments=[]
    for row in valid:
        if not segments or segments[-1][-1]['gt_interval']!=row['gt_interval'] or row['rgb_t']-segments[-1][-1]['rgb_t']>GT_GAP:
            segments.append([])
        segments[-1].append(row)
    attempts=[]; accepted=[]; available_after=-math.inf
    for si,seg in enumerate(segments):
        times=[x['rgb_t'] for x in seg]
        for start in times:
            if start<=available_after: continue
            end=start+LENGTH
            if end>times[-1]:
                attempts.append({'segment':si,'start':start,'reason':'insufficient_remaining_duration','segment_end':times[-1],'remaining':times[-1]-start})
                break
            targets=[start+LENGTH*i/(COUNT-1) for i in range(COUNT)]
            positions=[]; errors=[]
            for t in targets:
                right=bisect.bisect_left(times,t)
                choices=[j for j in (right-1,right) if 0<=j<len(times)]
                j=min(choices,key=lambda x:(abs(times[x]-t),times[x]))
                positions.append(j); errors.append(abs(times[j]-t))
            if max(errors)>SNAP_MAX:
                reason='nearest_rgb_exceeds_50ms'
                attempts.append({'segment':si,'start':start,'reason':reason,'max_snap_error':max(errors),'duplicate_count':COUNT-len(set(positions))})
                continue
            if len(set(positions))!=COUNT:
                reason='duplicate_nearest_frame'
                attempts.append({'segment':si,'start':start,'reason':reason,'max_snap_error':max(errors),'duplicate_count':COUNT-len(set(positions))})
                continue
            selected=[seg[j] for j in positions]
            w={'index':len(accepted),'segment':si,'nominal_start':start,'nominal_end':end,'target_timestamps':targets,'snap_errors_seconds':errors,'pair_indices':[x['pair_index'] for x in selected],'rgb_timestamps':[x['rgb_t'] for x in selected],'depth_timestamps':[x['depth_t'] for x in selected],'gt_interval':selected[0]['gt_interval'],'actual_duration':selected[-1]['rgb_t']-selected[0]['rgb_t']}
            accepted.append(w)
            attempts.append({'segment':si,'start':start,'reason':'accepted','accepted_index':w['index'],'max_snap_error':max(errors)})
            available_after=end+WINDOW_GAP
    chosen=[0,(len(accepted)-1)//2,len(accepted)-1] if len(accepted)>=3 else []
    return {'valid_pairs':len(valid),'excluded_pairs':dict(excluded),'excluded_examples':excluded_examples,'segments':[{'index':i,'size':len(s),'start':s[0]['rgb_t'],'end':s[-1]['rgb_t'],'duration':s[-1]['rgb_t']-s[0]['rgb_t'],'gt_interval':s[0]['gt_interval']} for i,s in enumerate(segments)],'candidate_attempts':attempts,'attempt_reason_counts':dict(Counter(a['reason'] for a in attempts)),'accepted_windows':accepted,'selected_window_indices':chosen}

def audit(name,data):
    rgb=parse_ts(data/'rgb.txt'); depth=parse_ts(data/'depth.txt'); gt,intervals=parse_gt_intervals(data/'groundtruth.txt')
    pairs,candidates=associate(rgb,depth)
    result={'schema':'s98-window-independent-recompute-v1','sequence':name,'data_root':str(data),'scope':'development-data timestamp qualification only; no image decode, no GT pose-value parse, no model inference','rules':{'association':'independently reimplemented unique greedy; strict abs(dt)<0.020 s; sort(abs_dt,rgb_t,depth_t)','gt_intervals':'sorted timestamps; split when adjacent gap >0.100 s; paired RGB and depth must share interval','window':'8.840 s; 24 targets including endpoints; nearest RGB; tie earlier; max snap <=0.050 s; unique frames; next start > previous nominal end +0.100 s; select first/floor((N-1)/2)/last'},'counts':{'rgb_rows':len(rgb),'depth_rows':len(depth),'gt_rows':len(gt),'gt_intervals':len(intervals),'association_candidates':candidates,'paired_rows':len(pairs)},'source_sha256':{x:sha(data/x) for x in ('rgb.txt','depth.txt','groundtruth.txt')},'plan':plan(pairs,intervals)}
    result['status']='PASS_AT_LEAST_THREE_WINDOWS' if result['plan']['selected_window_indices'] else 'FAIL_FEWER_THAN_THREE_WINDOWS'
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    allres={}
    for name,data in SEQS.items():
        out=audit(name,data); allres[name]=out
        (OUT/f'{name}.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    summary={'schema':'s98-window-independent-recompute-summary-v1','generated_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'results':{k:{'status':v['status'],'counts':v['counts'],'valid_pairs':v['plan']['valid_pairs'],'excluded_pairs':v['plan']['excluded_pairs'],'segments':v['plan']['segments'],'attempt_reason_counts':v['plan']['attempt_reason_counts'],'accepted_windows':len(v['plan']['accepted_windows']),'selected_window_indices':v['plan']['selected_window_indices']} for k,v in allres.items()}}
    (OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
