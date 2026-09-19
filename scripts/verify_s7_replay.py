#!/usr/bin/env python3
"""Independent S7 verification from archived observations/events/render buffers.

No S7 production module is imported. No model or surfel renderer is rerun.
The older independent S6 verifier supplies handwritten GT interpolation,
independent point rasterization/statistics, and the documented map digest.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
from pathlib import Path
import shutil
import sys
import traceback
import zipfile
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from verify_s6_scores import pose_at, rasterize_centres, statistics, map_hash

ROOT = Path(__file__).resolve().parents[1]
ARMS = ('A0P0', 'A0P1', 'A1P0', 'A1P1')
READOUTS = ('official', 'candidate_no_nms', 'all20_nms', 'all20_no_nms')
ATOL, RTOL = 1e-9, 1e-10  # Inherited S6 independent scoring tolerance, fixed before execution.

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def save(p, value): Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
def load(p):
    with np.load(p, allow_pickle=False) as z: return {k:z[k] for k in z.files}


class Checks:
    def __init__(self): self.items=[]
    def __call__(self, name, condition, kind='recomputed', detail=None):
        row=dict(name=name, passed=bool(condition), kind=kind)
        if detail is not None: row['detail']=detail
        self.items.append(row)
        if not condition: raise AssertionError(name)
    def exact(self, name, a, b, kind='recomputed'):
        a,b=np.asarray(a),np.asarray(b)
        self(name, a.shape==b.shape and np.array_equal(a,b,equal_nan=True),kind)
    def floating(self, name, a, b):
        a,b=np.asarray(a),np.asarray(b)
        same_shape=a.shape==b.shape
        finite=np.isfinite(a)&np.isfinite(b) if same_shape else np.zeros(0,bool)
        difference=float(np.max(np.abs(a[finite]-b[finite]))) if finite.any() else 0.
        self(name,same_shape and np.array_equal(np.isnan(a),np.isnan(b)) and
             np.allclose(a,b,atol=ATOL,rtol=RTOL,equal_nan=True),detail={'max_absolute_difference':difference})
    def nested(self, name, actual, expected):
        if isinstance(actual,dict):
            self(name+'/keys',set(actual)<=set(expected))
            for k,v in actual.items(): self.nested(name+'/'+str(k),v,expected[k])
        elif isinstance(actual,list):
            self(name+'/length',len(actual)==len(expected))
            for i,(a,b) in enumerate(zip(actual,expected)): self.nested(name+'/'+str(i),a,b)
        elif isinstance(actual,(str,bool,int)) or actual is None:
            self(name,actual==expected)
        else:
            self(name,np.isclose(actual,expected,atol=ATOL,rtol=RTOL),
                 detail=dict(recomputed=float(actual),recorded=float(expected)))


def reconstruct_paths(obs, events, association, check, prefix):
    """Replay events twice; also brute-force-check original assignments per frame.

    No kd-tree or Memory object. Candidate filtering is only an accelerator;
    final match predicates use scalar norm/dot in ascending point-ID order.
    """
    offsets=obs['offsets']; p0=[]; p1=[]; birth=[]; sources=[]; counts=[]; logic=[]
    check(prefix+'/20_events',len(events)==20 and len(offsets)==21)
    check(prefix+'/offset_bounds',int(offsets[0])==0 and int(offsets[-1])==len(obs['ids']) and np.all(np.diff(offsets)>=0))
    for frame,event in enumerate(events):
        lo,hi=map(int,offsets[frame:frame+2]); n=len(birth)
        ids=np.arange(lo,hi); targets=np.asarray(event['targets'],dtype=np.int64)
        matches=np.asarray(event['matches'],dtype=np.int64)
        tag=f'{prefix}/frame{frame}'
        check(tag+'/event_boundary',event['frame']==frame and event['old_n']==n and len(targets)==len(ids)==len(matches))
        check.exact(tag+'/observation_frame',obs['ids'][lo:hi,0],np.full(hi-lo,frame))
        radii=np.r_[obs['radii'][birth],obs['radii'][lo:hi]]
        threshold=float(radii.mean()+.5*radii.std()) if len(radii) else .025
        check(tag+'/threshold',threshold==event['threshold'])
        old=np.asarray(p1 if association else p0,dtype=np.float64).reshape(-1,3)
        normals=obs['normals'][birth]
        expected_matches=[]
        for i in ids:
            match=-1
            if n:
                delta=old-obs['points'][i]
                possible=np.flatnonzero(np.sqrt(np.sum(delta*delta,axis=1))<=threshold+1e-12)
                for j in possible:
                    if np.linalg.norm(old[j]-obs['points'][i])<=threshold and np.dot(normals[j],obs['normals'][i])>.6:
                        match=int(j); break
            expected_matches.append(match)
        check.exact(tag+'/independent_first_compatible_matches',matches,expected_matches)
        check(tag+'/matched_targets',np.all((matches<0)|((matches>=0)&(matches<n)&(targets==matches))))
        groups={}; births=[]; expected_targets=[]
        for i,t,m in zip(ids,targets,matches):
            if m<0:
                expected_targets.append(n+len(births)); births.append(int(i))
            else:
                expected_targets.append(int(m)); groups.setdefault(int(m),[]).append(int(i))
        check.exact(tag+'/target_birth_order',targets,expected_targets)
        check(tag+'/new_frame_contributions',all(frame not in sources[point] for point in groups))
        for point,members in groups.items():
            mean=np.mean(obs['points'][members],axis=0)
            p1[point]=(p1[point]*counts[point]+mean)/(counts[point]+1)
            counts[point]+=1; sources[point].append(frame)
        for i in births:
            birth.append(i); p0.append(obs['points'][i].copy()); p1.append(obs['points'][i].copy())
            counts.append(1); sources.append([frame])
        check(tag+'/new_count',event['new_n']==len(birth))
        logic.append(dict(frame_id=frame,input_points=hi-lo,old_points=n,merged_points=int(np.count_nonzero(matches>=0)),
            new_points=len(births),total_points=len(birth),position_threshold_normalized=threshold,
            radius_normalized_quantiles=np.quantile(radii,[0,.5,.9,1]).tolist() if len(radii) else [],
            updated_existing_points=len(groups) if association else 0))
    attributes={k:obs[k][birth] for k in ('normals','radii','colors')}
    attributes['counts']=np.asarray(counts,dtype=np.int64)
    maps=[dict(points=np.asarray(p0).reshape(-1,3),**attributes),dict(points=np.asarray(p1).reshape(-1,3),**attributes)]
    return maps,{str(i):v for i,v in enumerate(sources)},logic


def votes_from_render(render, mapping):
    """Independent accumulation retains the upstream first-contribution doubling."""
    ix=render['surfel_index_map'].ravel(); cos=render['cos_value_map'].ravel(); depth=render['depth'].ravel()
    mass={}
    for pixel in np.flatnonzero(ix>=0):
        if cos[pixel]<0: continue
        amount=cos[pixel]/(1+depth[pixel])
        for frame in mapping[str(int(ix[pixel]))]:
            mass[frame]=mass[frame]+amount if frame in mass else amount+amount
    values=np.array(list(mass.values())); ratios=values/values.sum()
    frames=list(mass); k=len(frames); budget=min(14,k)
    allocation=np.ones(k,dtype=np.int64)
    if k>budget:
        allocation[:]=0; allocation[np.argsort(ratios)[::-1][:budget]]=1
    elif budget>k:
        scaled=ratios*(budget-k); floors=np.asarray([int(v//1) for v in scaled]); allocation+=floors
        ranking=sorted(range(k),key=lambda i:float(scaled[i]-floors[i]),reverse=True)
        for i in ranking[:int(budget-k-floors.sum())]: allocation[i]=1
    weights=sorted([[int(f),float(r)] for f,r in zip(frames,ratios)])
    counts=sorted([[int(f),int(n)] for f,n in zip(frames,allocation)])
    return weights,counts


def optical_pose(p): return np.asarray(p)@np.diag([1.,-1.,-1.,1.])
def query_average(p):
    p=optical_pose(p); q=Rotation.from_matrix(p[:3,:3]).as_quat(); q=q/np.linalg.norm(q)
    result=np.eye(4); result[:3,:3]=Rotation.from_quat(q).as_matrix(); result[:3,3]=p[:3,3]
    return result
def distance(a,b):
    a=torch.as_tensor(a,dtype=torch.float64); b=torch.as_tensor(b,dtype=torch.float64)
    angle=torch.acos((torch.clamp(torch.trace(a[:3,:3].T@b[:3,:3]),-1.,3.)-1)/2)
    return float(torch.norm(a[:3,3]-b[:3,3])*.1+angle)


def independently_select(poses, query, counts, nms):
    history=[optical_pose(p) for p in poses[:20]]; q=query_average(query)
    expanded=[f for f,n in counts for i in range(n)]
    distances=torch.tensor([distance(q,history[f]) for f in expanded],dtype=torch.float32)
    order=torch.argsort(distances).tolist(); ranked=[expanded[i] for i in order]
    pairs=sorted(distance(history[i],history[j]) for i in range(5) for j in range(i+1,5))
    threshold=pairs[len(pairs)//2]; initial=threshold; selected=[ranked[0]]; steps=[]
    maximum=min(4,len(expanded),20)
    if nms:
        pairwise={(i,j):distance(history[i],history[j]) for i in set(ranked) for j in set(ranked)}
        while len(selected)<maximum and threshold>=1e-5:
            for f in ranked[1:]:
                if len(selected)==maximum: break
                comparisons=[]
                for old in selected:
                    d=pairwise[f,old]; comparisons.append([old,d])
                    if d<threshold: break
                rejected=any(d<threshold for _,d in comparisons)
                steps.append(dict(frame=f,threshold=threshold,comparisons=comparisons,accepted=not rejected))
                if not rejected: selected.append(f)
            if len(selected)<maximum:
                steps.append(dict(relax_from=threshold,relax_to=threshold/1.2)); threshold/=1.2
        if len(selected)<maximum:
            extra=[i for i in ranked if i not in selected][:maximum-len(selected)]
            selected.extend(extra); steps.append(dict(fallback_added=extra))
    else:
        for f in ranked[1:]:
            if f not in selected: selected.append(f)
            if len(selected)==maximum: break
    return dict(selected=selected,expanded_candidates=expanded,sorted_frames=ranked,
        distances_float32=distances.tolist(),nms=nms,
        expanded_adjacent_pose_ties=int((np.diff(np.sort(distances.numpy()))==0).sum()),
        initial_threshold=initial,steps=steps)


def contrasts(scores):
    output={}
    for readout in READOUTS:
        v={a:scores[a][readout]['support'] for a in ARMS}
        output[readout]=dict(position_A0_pp=100*(v['A0P1']-v['A0P0']),position_A1_pp=100*(v['A1P1']-v['A1P0']),
            association_P0_pp=100*(v['A1P0']-v['A0P0']),association_P1_pp=100*(v['A1P1']-v['A0P1']),
            interaction_pp=100*((v['A1P1']-v['A1P0'])-(v['A0P1']-v['A0P0'])))
    return output


def aggregate(rows, split, stride):
    rows=[r for r in rows if r['split']==split and r['stride']==stride]
    def mean(values):
        values=[v for v in values if v is not None]
        return float(np.mean(values)) if values else None
    support={a:{r:mean([100*x['readouts'][a][r]['support'] for x in rows]) for r in READOUTS} for a in ARMS}
    effects={r:{k:mean([x['contrasts'][r][k] for x in rows]) for k in rows[0]['contrasts'][r]} for r in READOUTS}
    geometry={a:{k:mean([x['geometry'][a]['common_four'][k] for x in rows]) for k in ('mae_mm','median_abs_mm','p90_abs_mm')} for a in ARMS}
    for a in ARMS: geometry[a]['mean_own_coverage_percent']=mean([100*x['geometry'][a]['coverage'] for x in rows])
    changes={}
    for readout in READOUTS:
        changes[readout]={}
        for label,left,right in [('position_A0','A0P0','A0P1'),('position_A1','A1P0','A1P1'),
                                 ('association_P0','A0P0','A1P0'),('association_P1','A0P1','A1P1')]:
            changes[readout][label]=sum(set(x['readouts'][left][readout]['selected'])!=set(x['readouts'][right][readout]['selected']) for x in rows)
    return dict(split=split,stride=stride,unique_queries=len(rows),support_percent=support,
        contrasts_pp=effects,set_changed_queries=changes,geometry=geometry,
        common_four_pixels_min=min(x['common_four_pixels'] for x in rows),common_four_pixels_max=max(x['common_four_pixels'] for x in rows),
        common_four_mean_coverage_percent=mean([100*x['common_four_pixels']/x['valid_pixels'] for x in rows]),
        empty_common_queries=sum(x['common_four_pixels']==0 for x in rows))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--run',type=Path,default=ROOT/'results/S7_event_replay')
    parser.add_argument('--output',type=Path,default=ROOT/'results/S7_independent_audit')
    args=parser.parse_args(); root=args.root; run=args.run; out=args.output
    meta=read(run/'run_metadata.json')
    if meta.get('status')!='completed': parser.error('S7 is not completed; do not inspect final scoring or create a final audit yet')
    if out.exists(): parser.error('Preserve all prior audit attempts; select a fresh output directory')
    out.mkdir(parents=True); shutil.copy2(__file__,out/'verifier_snapshot.py')
    helper=Path(__file__).with_name('verify_s6_scores.py'); shutil.copy2(helper,out/'s6_independent_helpers_snapshot.py')
    check=Checks(); report=dict(started_utc=now(),status='running',verifier_sha256=sha(__file__),
        independent_s6_helper_sha256=sha(helper),checks=check.items,
        tolerance=dict(float_atol=ATOL,float_rtol=RTOL,maps_counts_sources='exact',IDs_sort_NMS='exact',target_valid_support_masks='exact'),
        environment=dict(python=sys.version,packages={n:version(n) for n in ('numpy','scipy','torch','Pillow')}),
        limitations=['Accepted surfel construction is not repeated from model depth/confidence/RGB; archived observation IDs/arrays are verified and replayed.',
            'Surfel polygon rasterization is not rerun; saved render buffers are authenticated and votes/candidates/sort/NMS are recomputed from them.',
            'Measured support/target arrays are reused and compared exactly to the independent S6 audit; this run does not reread depth PNGs.',
            'Geometry uses the prior independent S6 handwritten pose/raster/statistics helpers, not the S7 production scorer.',
            'Latent CUT3R state tensors are not archived; state isolation remains metadata/source evidence.',
            'Timing and sealing order are authenticated metadata plus source-order checks, not a recovered historical file-access trace.',
            'S6 has no per-observation event archive; S7 events are independently checked against saved observations and original matching predicates, with S6 terminal states/logical traces compared.'])
    save(out/'verification.json',report); before={}; records=[]
    def integrity(path,digest,label=None):
        actual=sha(path); before[str(path)]=actual
        check(label or str(path.relative_to(root)),actual==digest,'integrity')
    try:
        torch.set_num_threads(1)
        freeze=read(root/'docs/S7_PROTOCOL_FREEZE.json')
        check('frozen_metadata_copy',freeze==meta['freeze'],'metadata')
        times=[datetime.fromisoformat(t) for t in [freeze['frozen_utc'],meta['started_utc'],meta['selections_sealed_utc'],meta['completed_utc']]]
        check('freeze_start_seal_complete_order',all(a<=b for a,b in zip(times,times[1:])),'metadata',detail=[t.isoformat() for t in times])
        check('phase_complete',meta['phase']=='complete','metadata')
        integrity(root/'docs/S7_EVENT_REPLAY_PROTOCOL.md',freeze['protocol_sha256'])
        integrity(root/'docs/S7_PRE_RUN_REVIEW.md',freeze['pre_run_review_sha256'])
        integrity(root/'results/pre_S7_unittest.txt',freeze['tests_sha256'])
        for name,digest in freeze['execution_source_sha256'].items(): integrity(root/name,digest)
        for name,digest in freeze['measurement_file_sha256'].items(): integrity(root/name,digest)
        for name,digest in meta['measurement_source_sha256'].items(): integrity(root/name,digest,'used_measurement/'+name)
        for name,digest in meta['source_sha256'].items(): integrity(root/name,digest,'used_source/'+name)
        with zipfile.ZipFile(run/'experiment_source.zip') as archive:
            for name,digest in meta['source_sha256'].items():
                check('source_archive/'+name,hashlib.sha256(archive.read(name)).hexdigest()==digest,'integrity')
        source=(root/'scripts/run_s7_replay.py').read_text(); tree=ast.parse(source)
        assignments={}
        for node in ast.walk(tree):
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    assignments[ast.unparse(target)]=node.lineno
        seal=assignments["meta['selections_sealed_utc']"]
        check('source_measurement_order',all(assignments[k]>seal for k in ('old_meta','audit','trajectory','scale','(target, valid, support)')),'source_order')
        imported={n.module for n in ast.walk(ast.parse(Path(__file__).read_text())) if isinstance(n,ast.ImportFrom)}
        check('verifier_no_production_S7_imports',not {'s7_event_replay','run_s7_replay'}&imported,'source_order')
        check('environment_packages',report['environment']['packages']==meta['environment']['packages'],'metadata')
        check('torch_default_dtype',str(torch.get_default_dtype())==meta['environment']['torch_default_dtype'],'metadata')
        check('six_cases',len(meta['cases'])==6,'metadata')
        originals=read(run/'records.json'); before[str(run/'records.json')]=sha(run/'records.json')
        before[str(run/'run_metadata.json')]=sha(run/'run_metadata.json')
        references={(r['block'],r['stride'],r['frame']):r for r in originals}
        check('24_unique_query_conditions',len(references)==len(originals)==24,'metadata')
        manifest=read(root/'data/cut3r/S5_inputs.json')
        oldmeta=read(root/'results/S6_memory_bridge/run_metadata.json')
        oldaudit=read(root/'results/S6_independent_audit/verification.json')
        check('independent_S6_pass',oldaudit['status']=='passed','metadata')
        check('S6_helper_verified_version',sha(helper)==oldaudit['verifier_sha256'],'integrity')
        gtdata=np.loadtxt(root/'data/tum/rgbd_dataset_freiburg1_xyz/groundtruth.txt')
        for block in manifest['blocks']:
            b=block['block']; model=root/f'results/S6_cut3r_cpu/block{b}'
            modelmeta=read(model/'run_metadata.json')
            check(f'B{b}/model_prediction_reference',modelmeta['predictions_sha256']==meta['model_prediction_sha256'][str(b)],'metadata')
            integrity(model/'predictions.npz',meta['model_prediction_sha256'][str(b)],f'B{b}/model_prediction_bytes')
            check(f'B{b}/archived_model_state_contract',modelmeta['history_only_memory_ok'] and modelmeta['query_state_write_audit']['ok'],'metadata')
        for entry in meta['cases']:
            folder=run/entry['directory']; b=entry['block']; stride=entry['stride']; label=entry['directory']
            for name,digest in entry['sealed_files'].items(): integrity(folder/name,digest,label+'/'+name)
            case=read(folder/'prediction_only_selection.json'); oldfolder=root/'results/S6_memory_bridge'/label
            oldcase=read(oldfolder/'prediction_only_selection.json')
            integrity(oldfolder/'prediction_only_selection.json',case['s6_prediction_selection_sha256'],label+'/S6_selection_hash')
            expected_names={'observations.npz','predicted_poses.npz','prediction_only_selection.json'}
            expected_names.update(f'A{a}_{suffix}' for a in range(2) for suffix in ('events.json','recorded_build_trace.json'))
            expected_names.update(f'{a}{suffix}' for a in ARMS for suffix in ('.npz','_sources.json'))
            expected_names.update(f'query{q}_{a}_render.npz' for q in range(20,24) for a in ARMS)
            check(label+'/complete_seal',set(entry['sealed_files'])==expected_names,'integrity')
            obs=load(folder/'observations.npz'); identity=obs['ids']; poses=load(folder/'predicted_poses.npz')['poses']
            check(label+'/identity_shape',identity.ndim==2 and identity.shape[1]==3 and identity.dtype.kind=='i')
            check(label+'/identity_unique',len({tuple(row) for row in identity.tolist()})==len(identity))
            check(label+'/identity_domain',np.all((identity[:,0]>=0)&(identity[:,0]<20)) and np.all((identity[:,1:]>=0)&(identity[:,1:]<224)) and np.all(identity[:,1:]%stride==0))
            check(label+'/identity_order',identity.tolist()==sorted(identity.tolist(),key=lambda row:(row[0],row[2],row[1])))
            for k in ('points','normals','radii','colors'): check(label+'/observations_'+k,np.isfinite(obs[k]).all() and len(obs[k])==len(identity))
            check(label+'/24_poses',poses.shape==(24,4,4) and np.isfinite(poses).all())
            maps={}; mappings={}
            for a,method in enumerate(('first_write','frame_mean')):
                replayed,mapping,logic=reconstruct_paths(obs,read(folder/f'A{a}_events.json'),a,check,label+f'/A{a}')
                recorded=read(folder/f'A{a}_recorded_build_trace.json')
                stripped=[]
                for row in recorded:
                    value={k:v for k,v in row.items() if k!='elapsed_seconds'}
                    value['position_threshold_normalized']=value.pop('position_threshold_m')
                    value['radius_normalized_quantiles']=value.pop('radius_m_quantiles'); stripped.append(value)
                oldlogic=[{k:v for k,v in row.items() if k!='elapsed_seconds'} for row in oldcase['maps'][method]['build_trace']]
                check(label+f'/A{a}/logical_trace',logic==stripped==oldlogic)
                # S6 build_memory adds frame_id; S7 stores ordered constructor records.
                numbered_filters=[dict(row,frame_id=i) for i,row in enumerate(case['filters'])]
                check(label+f'/A{a}/filters',numbered_filters==oldcase['maps'][method]['filters'])
                for p in range(2):
                    arm=f'A{a}P{p}'; saved=load(folder/f'{arm}.npz'); maps[arm]=replayed[p]; mappings[arm]=mapping
                    for k,value in maps[arm].items(): check.exact(label+'/'+arm+'/'+k,value,saved[k])
                    check(label+'/'+arm+'/sources',mapping==read(folder/f'{arm}_sources.json'))
                    check(label+'/'+arm+'/digest',map_hash(maps[arm],mapping)==case['maps'][arm]['digest'])
                    check(label+'/'+arm+'/counts_provenance',maps[arm]['counts'].tolist()==[len(mapping[str(i)]) for i in range(len(mapping))])
                    if a==p:
                        old=load(oldfolder/f'{method}.npz')
                        for k in maps[arm]: check.exact(label+'/'+arm+'/S6_'+k,maps[arm][k],old[k])
                        check(label+'/'+arm+'/S6_sources',mapping==read(oldfolder/f'{method}_provenance.json'))
                        check(label+'/'+arm+'/S6_digest',map_hash(maps[arm],mapping)==oldcase['maps'][method]['digest'])
                    np.savez_compressed(out/f'{label}_{arm}.npz',**maps[arm])
                for k in ('normals','radii','colors','counts'): check.exact(label+f'/A{a}/fixed_'+k,maps[f'A{a}P0'][k],maps[f'A{a}P1'][k])
            block=next(x for x in manifest['blocks'] if x['block']==b)
            gt=[pose_at(gtdata,f['rgb']['timestamp'])[0] for f in block['frames']]
            scale=oldmeta['normalizations'][str(b)]['scoring_only_metric_scale']
            world={a:(gt[0]@np.c_[maps[a]['points']*scale,np.ones(len(maps[a]['points']))].T).T[:,:3] for a in ARMS}
            check(label+'/four_query_frames',[x['frame'] for x in case['queries']]==list(range(20,24)))
            for query in case['queries']:
                q=query['frame']; qtag=label+f'/Q{q}'; current=references[b,stride,q]
                z=load(folder/f'query{q}_scoring.npz'); s6=load(oldfolder/f'query{q}_scoring.npz')
                independent=load(root/'results/S6_independent_audit'/f'block{b}_stride{stride}_query{q}.npz')
                before[str(folder/f'query{q}_scoring.npz')]=sha(folder/f'query{q}_scoring.npz')
                for k in ('target','valid','support'):
                    check.exact(qtag+'/'+k,z[k],s6[k]); check.exact(qtag+'/independent_'+k,z[k],independent[k])
                target,valid,support=z['target'],z['valid'],z['support']
                check(qtag+'/positive_valid',int(valid.sum())>0)
                predicted={a:rasterize_centres(world[a],gt[q]) for a in ARMS}
                common=valid&np.logical_and.reduce([np.isfinite(predicted[a]) for a in ARMS])
                diagonal=valid&np.isfinite(predicted['A0P0'])&np.isfinite(predicted['A1P1'])
                check.exact(qtag+'/common_four',common,z['common_four'])
                for value in (z['common_diagonal'],s6['common'],independent['common']): check.exact(qtag+'/common_diagonal',diagonal,value)
                scores={}; geometry={}; decisions={}
                for arm in ARMS:
                    check.floating(qtag+'/'+arm+'/projected',predicted[arm],z[arm])
                    own=valid&np.isfinite(predicted[arm])
                    geometry[arm]=dict(common_four=statistics(predicted[arm],target,common),own=statistics(predicted[arm],target,own),coverage=float(own.sum()/valid.sum()))
                    render=load(folder/f'query{q}_{arm}_render.npz'); indices=render['surfel_index_map']
                    check(qtag+'/'+arm+'/render_domain',indices.shape==(160,160) and np.all((indices==-1)|((indices>=0)&(indices<len(maps[arm]['points'])))))
                    weights,counts=votes_from_render(render,mappings[arm]); trace=query['maps'][arm]['official_trace']
                    check(qtag+'/'+arm+'/weights',weights==trace['weights'])
                    check(qtag+'/'+arm+'/candidate_counts',counts==trace['candidate_counts'])
                    check(qtag+'/'+arm+'/render_coverage',float(np.mean(indices>=0))==trace['rendered_coverage'])
                    decisions[arm]={}; scores[arm]={}
                    for mode in READOUTS:
                        pool=[[i,1] for i in range(20)] if mode.startswith('all20') else counts
                        decision=independently_select(poses,poses[q],pool,not mode.endswith('no_nms'))
                        stored=query['maps'][arm]['readouts'][mode]
                        check(qtag+'/'+arm+'/'+mode+'/full_decision_trace',decision==stored)
                        ids=decision['selected']; check(qtag+'/'+arm+'/'+mode+'/IDs',len(ids)==len(set(ids))==4 and all(0<=x<20 for x in ids))
                        coverage=float(np.count_nonzero(np.logical_or.reduce(support[ids],axis=0)&valid)/np.count_nonzero(valid))
                        scores[arm][mode]=dict(selected=ids,support=coverage); decisions[arm][mode]=decision
                        check(qtag+'/'+arm+'/'+mode+'/support_exact',scores[arm][mode]==current['readouts'][arm][mode])
                    check(qtag+'/'+arm+'/official_IDs',decisions[arm]['official']['selected']==trace['selected'])
                    if arm in ('A0P0','A1P1'):
                        method='first_write' if arm=='A0P0' else 'frame_mean'
                        oldtrace=oldcase['selected'][q-20]['retrieval']['160'][method]
                        for k in ('selected','candidate_counts','weights'): check(qtag+'/'+arm+'/S6_trace_'+k,trace[k]==oldtrace[k])
                        check.floating(qtag+'/'+arm+'/S6_projection',predicted[arm],s6[method])
                for mode in ('all20_nms','all20_no_nms'):
                    check(qtag+'/'+mode+'/map_invariant',len({tuple(scores[a][mode]['selected']) for a in ARMS})==1)
                row=dict(block=b,split=case['split'],stride=stride,frame=q,valid_pixels=int(valid.sum()),common_four_pixels=int(common.sum()),
                    all20_support=float(np.count_nonzero(np.logical_or.reduce(support,axis=0)&valid)/valid.sum()),readouts=scores,geometry=geometry)
                check.nested(qtag+'/records',row,current)
                row['contrasts']=contrasts(scores); records.append(row)
                save(out/f'{label}_query{q}_decisions.json',decisions)
                np.savez_compressed(out/f'{label}_query{q}_scoring.npz',common_four=common,common_diagonal=diagonal,**predicted)
            print(json.dumps(dict(case=label,phase='independent_recomputed',utc=now())),flush=True)
        groups=[aggregate(records,s,t) for s in ('development','test') for t in (8,12)]
        check('12_unique_queries',len({(r['block'],r['frame']) for r in records})==12)
        check('8_primary_test_queries',len({(r['block'],r['frame']) for r in records if r['split']=='test'})==8)
        check('384_readout_conditions',sum(len(r['readouts'])*len(READOUTS) for r in records)==384)
        check('metadata_condition_counts',meta['query_conditions']==24 and meta['readout_conditions']==384,'metadata')
        for path,digest in before.items(): check('unchanged/'+str(Path(path).relative_to(root)),sha(path)==digest,'integrity')
        save(out/'records.json',records); save(out/'aggregate.json',groups)
        report.update(status='passed',groups=groups,query_conditions=24,readout_conditions=384,
            unique_queries=12,main_unique_queries=8,maps_recomputed=24,association_paths_recomputed=12,
            render_vote_recomputations=96,decision_recomputations=384,measurement_PNGs_reread=0,
            original_sha256=before,source_zip_sha256=sha(run/'experiment_source.zip'))
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report['completed_utc']=now(); report['checks_count']=len(check.items)
    report['checks_by_kind']=dict(Counter(c['kind'] for c in check.items))
    save(out/'verification.json',report)
    print(json.dumps({k:report[k] for k in ('status','checks_count','checks_by_kind','completed_utc')},ensure_ascii=False))
    if report['status']!='passed': print(report['traceback']); return 1
    return 0


if __name__=='__main__': sys.exit(main())
