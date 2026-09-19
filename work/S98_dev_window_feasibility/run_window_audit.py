#!/usr/bin/env python3
"""Assess fixed S8-style windows on already exposed local TUM sequences."""
from bisect import bisect_left
from datetime import datetime, timezone
import hashlib, json, math, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from tum_rgbd import read_timestamp_file, associate_rgb_depth

CASES = {
    "fr1_xyz": PROJECT / "data/tum/rgbd_dataset_freiburg1_xyz",
    "fr2_desk_guard": PROJECT / "data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk",
}
LENGTH, GAP, SNAP, COUNT = 8.840, 0.100, 0.050, 24

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def gt_intervals(path):
    ts=[]
    for n,line in enumerate(Path(path).read_text().splitlines(),1):
        if not line.strip() or line.lstrip().startswith('#'): continue
        f=line.split()
        if len(f)!=8: raise ValueError(f"{path}:{n}: expected 8 fields")
        t=float(f[0])
        if not math.isfinite(t): raise ValueError(f"{path}:{n}: nonfinite timestamp")
        ts.append(t)
    ts.sort()
    if not ts or any(b<=a for a,b in zip(ts,ts[1:])): raise ValueError(f"{path}: duplicate/non-increasing GT")
    out=[[ts[0],ts[0]]]
    for a,b in zip(ts,ts[1:]):
        if b-a>GAP: out.append([b,b])
        else: out[-1][1]=b
    return ts,out

def interval_at(t, intervals):
    for i,(lo,hi) in enumerate(intervals):
        if lo<=t<=hi: return i
    return None

def windows(matches, intervals):
    segments=[]; excluded=0
    for m in matches:
        ri=interval_at(m.rgb.timestamp, intervals); di=interval_at(m.depth.timestamp, intervals)
        if ri is None or ri!=di: excluded+=1; continue
        row=(m.rgb.timestamp,m)
        if not segments or segments[-1][0][1] != ri or row[0]-segments[-1][-1][0]>GAP:
            segments.append([])
        segments[-1].append((row[0],ri,m))
    accepted=[]; rejects={"insufficient_duration":0,"snap_error":0,"duplicate_frame":0}
    for seg in segments:
        times=[x[0] for x in seg]; available=-float('inf')
        for start in times:
            if start<=available: continue
            end=start+LENGTH
            if end>times[-1]: rejects['insufficient_duration']+=1; break
            targets=[start+LENGTH*i/(COUNT-1) for i in range(COUNT)]
            pos=[]; errs=[]
            for t in targets:
                r=bisect_left(times,t); choices=[j for j in (r-1,r) if 0<=j<len(times)]
                j=min(choices,key=lambda j:(abs(times[j]-t),times[j])); pos.append(j); errs.append(abs(times[j]-t))
            if max(errs)>SNAP: rejects['snap_error']+=1; continue
            if len(set(pos))!=COUNT: rejects['duplicate_frame']+=1; continue
            accepted.append({'segment':seg[0][1],'nominal_start':start,'nominal_end':end,'max_snap_error':max(errs),'match_indices':[matches.index(seg[j][2]) for j in pos]})
            available=end+GAP
    chosen=[0,(len(accepted)-1)//2,len(accepted)-1] if len(accepted)>=3 else []
    return {'segments':[{'index':i,'size':len(s),'start':s[0][0],'end':s[-1][0],'gt_interval':s[0][1]} for i,s in enumerate(segments)],'excluded_pairs':excluded,'accepted_windows':accepted,'chosen_indices':chosen,'reject_counts':rejects}

def main():
    out={'schema':'S98-development-window-feasibility-v1','status':'RUNNING','started_utc':datetime.now(timezone.utc).isoformat(),'rule':{'duration_seconds':LENGTH,'inter_segment_gap_seconds':GAP,'snap_seconds':SNAP,'frames_per_window':COUNT,'rgb_depth':'associate_rgb_depth strict <0.020s unique greedy','gt':'gap >0.100s splits support'},'formal_s91_run':False,'model_inferences':0,'cases':[]}
    for name,root in CASES.items():
        rgb=read_timestamp_file(root/'rgb.txt'); depth=read_timestamp_file(root/'depth.txt'); gtt,ints=gt_intervals(root/'groundtruth.txt'); matches=associate_rgb_depth(rgb,depth,max_difference=.020)
        plan=windows(matches,ints)
        out['cases'].append({'id':name,'root':str(root),'exposure_state':'DEVELOPMENT_SEEN','source_shas':{f:sha(root/f) for f in ('rgb.txt','depth.txt','groundtruth.txt')},'counts':{'rgb':len(rgb),'depth':len(depth),'gt':len(gtt),'gt_intervals':len(ints),'official_rgb_depth_matches':len(matches)},'plan':plan})
    out['status']='PASS_DEVELOPMENT_WINDOW_AUDIT_NOT_HELDOUT'; out['completed_utc']=datetime.now(timezone.utc).isoformat()
    p=Path(__file__).with_name('RESULTS.json'); p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({'status':out['status'],'cases':[(c['id'],len(c['plan']['accepted_windows']),c['plan']['chosen_indices']) for c in out['cases']]},ensure_ascii=False))
if __name__=='__main__': main()
