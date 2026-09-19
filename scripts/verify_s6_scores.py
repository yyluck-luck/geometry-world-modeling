#!/usr/bin/env python3
"""Independent S6 audit: raw PNG/trajectory/model arrays/maps, no experiment imports.

The measurement mask uses min/max neighbourhood filters, poses use handwritten
quaternion SLERP, and z buffering uses sorted per-cell reduction. Selection
IDs are authenticated and scored; VMem rendering/NMS and model inference are
not rerun. Archived runtime state tensors do not exist, so their equality is
explicitly a metadata check rather than a fresh tensor comparison.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import traceback
import zipfile
import numpy as np
from PIL import Image
from scipy.ndimage import maximum_filter, minimum_filter

ROOT = Path(__file__).resolve().parents[1]
K = np.array([525*299/640, 525*224/480, 112., 111.5])
METHODS = ('first_write', 'frame_mean')

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value): Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def crop_measurement(path):
    raw = np.asarray(Image.open(path), dtype=np.float64)/5000.0
    lo = minimum_filter(raw, size=5, mode='constant', cval=0.)
    hi = maximum_filter(raw, size=5, mode='constant', cval=0.)
    good = (lo > 0) & ((hi-raw) <= .05) & ((raw-lo) <= .05)
    good[:2] = False; good[-2:] = False; good[:, :2] = False; good[:, -2:] = False
    # Match the frozen measurement representation, including its float32 cast.
    z = np.asarray(Image.fromarray(raw.astype('float32')).resize((299,224), Image.Resampling.NEAREST), dtype=np.float64)[:,37:261]
    m = np.asarray(Image.fromarray(good.astype('uint8')).resize((299,224), Image.Resampling.NEAREST), dtype=bool)[:,37:261]
    return z, m

def quaternion_matrix(q):
    x,y,z,w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def pose_at(trajectory, stamp):
    j = int(np.searchsorted(trajectory[:,0], stamp))
    if j == 0 or j == len(trajectory): raise ValueError('GT extrapolation requested')
    a,b = trajectory[j-1], trajectory[j]
    gap = b[0]-a[0]
    if not 0 < gap <= .1: raise ValueError('GT interpolation gap exceeds protocol')
    t = (stamp-a[0])/gap
    qa=a[4:]/np.linalg.norm(a[4:]); qb=b[4:]/np.linalg.norm(b[4:])
    dot=float(np.dot(qa,qb))
    if dot < 0: qb=-qb; dot=-dot
    dot=min(1.,max(-1.,dot))
    if dot > 1.-1e-14: q=(1-t)*qa+t*qb
    else:
        theta=np.arccos(dot)
        q=(np.sin((1-t)*theta)*qa+np.sin(t*theta)*qb)/np.sin(theta)
    T=np.eye(4); T[:3,:3]=quaternion_matrix(q); T[:3,3]=(1-t)*a[1:4]+t*b[1:4]
    return T, float(gap)

def image_coordinates(world, c2w):
    # Homogeneous inverse differs from the production helper's row-vector path.
    camera=(np.linalg.inv(c2w)@np.c_[world,np.ones(len(world))].T).T[:,:3]
    z=camera[:,2]
    with np.errstate(divide='ignore', invalid='ignore'):
        uv=camera[:,:2]/z[:,None]*K[:2]+K[2:]
    visible=np.isfinite(uv).all(axis=1)&np.isfinite(z)&(z>0)&(uv[:,0]>=0)&(uv[:,0]<224)&(uv[:,1]>=0)&(uv[:,1]<224)
    return uv,z,visible

def supports_from_raw(depths, masks, poses, frame):
    valid=masks[frame][::2,::2]; target=depths[frame][::2,::2]
    rows,cols=np.nonzero(valid)
    rays=np.c_[(2*cols-K[2])/K[0], (2*rows-K[3])/K[1], np.ones(len(rows))]
    camera=rays*target[rows,cols,None]
    world=(poses[frame]@np.c_[camera,np.ones(len(camera))].T).T[:,:3]
    result=np.zeros((20,112,112), dtype=bool)
    for h in range(20):
        uv,z,visible=image_coordinates(world,poses[h])
        candidates=np.flatnonzero(visible)
        rounded=np.rint(uv[candidates]).astype(np.int64)
        for p,(x,y) in zip(candidates,rounded):
            if 0<=x<224 and 0<=y<224 and masks[h][y,x] and abs(z[p]-depths[h][y,x])<=.05:
                result[h,rows[p],cols[p]]=True
    return target,valid,result

def rasterize_centres(world,c2w):
    uv,z,visible=image_coordinates(world,c2w)
    ids=np.flatnonzero(visible); cells=np.rint(uv[ids]*.5).astype(np.int64)
    keep=(cells[:,0]>=0)&(cells[:,0]<112)&(cells[:,1]>=0)&(cells[:,1]<112)
    ids=ids[keep]; cells=cells[keep]; flat=cells[:,1]*112+cells[:,0]
    order=np.lexsort((z[ids],flat)); flat=flat[order]; ordered_z=z[ids[order]]
    first=np.r_[True,flat[1:]!=flat[:-1]] if len(flat) else np.zeros(0,bool)
    out=np.full(112*112,np.nan); out[flat[first]]=ordered_z[first]
    return out.reshape(112,112)

def statistics(pred,target,mask):
    differences=pred[mask]-target[mask]; absolute=np.sort(np.abs(differences)); count=len(absolute)
    if count==0: return dict(n=0,mae_mm=None,median_abs_mm=None,p90_abs_mm=None,within_30mm=None,signed_mean_mm=None)
    def percentile(frac):
        at=(count-1)*frac; left=int(np.floor(at)); right=int(np.ceil(at))
        return float(absolute[left]*(right-at)+absolute[right]*(at-left)) if right!=left else float(absolute[left])
    return dict(n=count,mae_mm=float(np.sum(absolute)/count*1000),median_abs_mm=percentile(.5)*1000,
                p90_abs_mm=percentile(.9)*1000,within_30mm=float(np.count_nonzero(absolute<=.03)/count),
                signed_mean_mm=float(np.sum(differences)/count*1000))

def map_hash(arrays, mapping):
    h=hashlib.sha256(b'S6 normalized memory digest v1\0')
    for i in range(len(arrays['points'])):
        for a in (arrays['points'][i],arrays['normals'][i],arrays['radii'][i:i+1]):
            a=np.asarray(a,dtype='<f8'); h.update(np.asarray(a.shape,dtype='<i8').tobytes()); h.update(a.tobytes())
        a=np.asarray(arrays['colors'][i],dtype='<f8'); h.update(b'color:array\0'); h.update(np.asarray(a.shape,dtype='<i8').tobytes()); h.update(a.tobytes())
    h.update(np.asarray(arrays['counts'],dtype='<i8').tobytes())
    h.update(json.dumps([[i,mapping[str(i)]] for i in range(len(arrays['points']))],separators=(',',':')).encode())
    return h.hexdigest()

def aggregate(records, split, stride):
    rows=[r for r in records if r['split']==split and r['stride']==stride]
    mean=lambda f: float(np.mean([f(r) for r in rows]))
    return dict(split=split,stride=stride,actual_queries=len(rows),
        common_pixels_min=min(r['common_pixels'] for r in rows),common_pixels_max=max(r['common_pixels'] for r in rows),
        common_coverage_percent=mean(lambda r:100*r['common_pixels']/r['valid_target_pixels']),
        geometry={m:{k:mean(lambda r:r['geometry'][m][k]) for k in ['mae_mm','median_abs_mm','p90_abs_mm','within_30mm','coverage_of_valid_target']} for m in METHODS},
        retrieval={w:dict(changed_queries=sum(r['retrieval'][w]['selection_set_changed'] for r in rows),support_percent={m:mean(lambda r:100*r['retrieval'][w][m]['support_coverage']) for m in METHODS},delta_pp=mean(lambda r:r['retrieval'][w]['coverage_delta_pp'])) for w in ['160','320']},
        controls_percent={m:mean(lambda r:100*r['controls'][m]['support_coverage']) for m in ['recent4','nearest_pose4']},
        all_history_percent=mean(lambda r:100*r['all_history_support_coverage']))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,default=ROOT/'results/S6_independent_audit')
    args=p.parse_args(); root=args.root; out=args.output
    if (out/'verification.json').exists(): p.error('Preserve existing audit; choose a fresh output directory')
    out.mkdir(parents=True,exist_ok=True); shutil.copy2(__file__,out/'verifier_snapshot.py')
    checks=[]; report=dict(started_utc=now(),status='running',verifier_sha256=sha(__file__),checks=checks,
        tolerance=dict(float_atol=1e-9,float_rtol=1e-10,boolean_arrays='exact',historical_arrays='exact'),
        inference_rerun=False,selection_renderer_rerun=False,state_tensors_recomputed=False,
        limitations=['Latent-state equality is metadata only: original state tensors were not archived.',
                     'VMem rendering/NMS and surfel construction are not independently rerun; archived IDs/maps are authenticated.',
                     'Recorded wall times and sealing order are checked with source structure, not a recovered historical filesystem trace.'])
    save(out/'verification.json',report)
    def check(label,condition,kind='recomputed',detail=None):
        item=dict(name=label,passed=bool(condition),kind=kind)
        if detail is not None:item['detail']=detail
        checks.append(item)
        if not condition:raise AssertionError(label)
    def same(label,a,b):
        if isinstance(a,dict):
            for k,v in a.items():same(label+'/'+k,v,b[k])
        elif isinstance(a,(bool,str,list)) or a is None:check(label,a==b)
        else:check(label,np.isclose(a,b,atol=1e-9,rtol=1e-10),detail=dict(recomputed=float(a),recorded=float(b)))
    def arrays_equal(label,a,b):
        if a.dtype.kind=='b':check(label,np.array_equal(a,b))
        else:
            mask=np.isfinite(a)&np.isfinite(b)
            check(label,np.array_equal(np.isnan(a),np.isnan(b)) and np.allclose(a,b,atol=1e-9,rtol=1e-10,equal_nan=True),detail={'max_absolute_difference':float(np.max(np.abs(a[mask]-b[mask]))) if mask.any() else 0.})
    try:
        base=root/'results/S6_memory_bridge'; meta=read(base/'run_metadata.json'); inputs=read(root/'data/cut3r/S5_inputs.json')
        original=read(base/'records.json'); references={(r['block'],r['stride'],r['frame']):r for r in original}
        check('six_cases',len(meta['cases'])==6); check('24_query_records',len(original)==24)
        same('crop_intrinsics',K.tolist(),meta['crop_intrinsics'])
        with zipfile.ZipFile(base/'experiment_source.zip') as archive:
            for name,digest in meta['source_sha256'].items():
                check('source_current/'+name,sha(root/name)==digest,'integrity')
                check('source_archive/'+name,hashlib.sha256(archive.read(name)).hexdigest()==digest,'integrity')
        report['source_zip_sha256']=sha(base/'experiment_source.zip')
        check('retrieval_kernel_in_source_manifest','src/vmem_retrieval_kernel.py' in meta['source_sha256'],'integrity')
        runner=(root/'scripts/run_s6_memory.py').read_text()
        check('source_seals_before_trajectory_read',runner.index("report['selections_sealed_utc']=utc()") < runner.index("trajectory=read_trajectory"),'source_review')
        check('run_time_order',meta['started_utc']<meta['selections_sealed_utc']<meta['completed_utc'],'metadata')
        seq=read(root/'results/S6_cut3r_cpu/sequence_metadata.json')
        check('model_completed_before_bridge',seq['completed_utc']<meta['started_utc'],'metadata')
        trajectory=np.loadtxt(root/'data/tum/rgbd_dataset_freiburg1_xyz/groundtruth.txt')
        s5=read(root/'results/S5_cut3r_sequence/summary.json'); recomputed=[]; scales=[]; histories=[]
        originals_to_hash=[base/'run_metadata.json',base/'records.json']
        originals_to_hash += list(base.glob('block*/*.npz'))+list(base.glob('block*/*.json'))
        before={str(x.relative_to(root)):sha(x) for x in originals_to_hash}
        for block in inputs['blocks']:
            b=block['block']; frames=block['frames']; d6=root/f'results/S6_cut3r_cpu/block{b}'; d5=root/f'results/CUT3R_S5_cpu/block{b}'
            m6=read(d6/'run_metadata.json'); recorded_comparison=read(d6/'s5_history_comparison.json')
            check(f'B{b}/NPZ_hash',sha(d6/'predictions.npz')==m6['predictions_sha256'],'integrity')
            expected=[dict(frame=i,img_mask=[True],ray_mask=[False],update=[i<20],reset=[False]) for i in range(24)]
            for field in ['requested_view_flags','prepared_view_flags','view_flags_before_inference','view_flags_after_inference']:
                check(f'B{b}/{field}',m6[field]==expected,'metadata')
            state=m6['query_state_write_audit']
            check(f'B{b}/state_record_count',len(state['checks'])==8 and state['anchor_snapshot_index']==20,'metadata')
            for item in state['checks']:
                check(f"B{b}/state/{item['field']}/{item['after_view']}",item['finite'] and item['anchor_finite'] and item['exactly_unchanged'] and item['tensor_sha256']==item['anchor_tensor_sha256'] and item['max_absolute_difference']==0,'metadata')
            with np.load(d6/'predictions.npz') as z6,np.load(d5/'predictions.npz') as z5:
                check(f'B{b}/168_arrays',len(z6.files)==168)
                for key in z6.files:
                    data=z6[key];check(f'B{b}/finite/{key}',np.isfinite(data).all())
                    frame=int(key.split('_')[0][5:])
                    if frame<20:
                        exact=data.shape==z5[key].shape and data.dtype==z5[key].dtype and np.array_equal(data,z5[key])
                        check(f'B{b}/S5_exact/{key}',exact)
                        check(f'B{b}/S5_record/{key}',recorded_comparison['per_array'][key]['exactly_equal'] and recorded_comparison['per_array'][key]['max_absolute_difference']==0,'metadata')
                        histories.append(dict(block=b,frame=frame,key=key,exactly_equal=exact))
                first=z6['frame0_pts3d_in_self_view'][0,:,:,2].astype('float64')
                norm=1/np.median(first[np.isfinite(first)&(first>0)])
                rawposes=np.stack([z6[f'frame{i}_camera_c2w'][0].astype('float64') for i in range(24)])
                relative=np.linalg.solve(rawposes[0],rawposes);relative[:,:3,3]*=norm
                with np.load(base/f'block{b}_normalized_input.npz') as stored:
                    arrays_equal(f'B{b}/normalized_first',first*norm,stored['first_depth'])
                    arrays_equal(f'B{b}/normalized_poses',relative,stored['poses'])
            depths=[];masks=[];poses=[];gaps=[]
            for f in frames:
                raw=root/'data/tum/rgbd_dataset_freiburg1_xyz'/f['depth']['path']
                check(f'B{b}/PNG_hash/{f["frame"]}',sha(raw)==f['depth_sha256'],'integrity')
                depth,mask=crop_measurement(raw);depths.append(depth);masks.append(mask)
                pose,gap=pose_at(trajectory,f['rgb']['timestamp']);poses.append(pose);gaps.append(gap)
                arrays_equal(f'B{b}/GT_pose/{f["frame"]}',pose,np.asarray(s5['blocks'][b]['rgb_pose_provenance'][f['frame']]['rgb_c2w']))
            good=masks[0]&np.isfinite(first)&(first>0)
            c=float(np.median(depths[0][good]/(first[good]*norm)))
            nrec=meta['normalizations'][str(b)]
            same(f'B{b}/firstnorm',norm,nrec['first_prediction_inverse_median'])
            same(f'B{b}/metric_scale',c,nrec['scoring_only_metric_scale'])
            same(f'B{b}/calibration_count',int(good.sum()),nrec['scoring_only_calibration_pixels'])
            same(f'B{b}/scale_product_S5',norm*c,s5['blocks'][b]['scale'])
            scales.append(dict(block=b,firstnorm=float(norm),metric_scale=c,product=float(norm*c),pixels=int(good.sum()),max_GT_gap=max(gaps)))
            for case in [x for x in meta['cases'] if x['block']==b]:
                stride=case['stride'];folder=base/case['directory'];sealed=folder/'prediction_only_selection.json'
                check(f'{case["directory"]}/selection_sha',sha(sealed)==case['selection_sha256'],'integrity')
                selected=read(sealed);maps={}
                for method in METHODS:
                    with np.load(folder/f'{method}.npz') as data: arrays={k:data[k] for k in data.files}
                    mapping=read(folder/f'{method}_provenance.json');count=len(arrays['points'])
                    check(f'{case["directory"]}/{method}/map_digest',map_hash(arrays,mapping)==selected['maps'][method]['digest'],'integrity')
                    check(f'{case["directory"]}/{method}/source_history_only',all(len(v)>0 and len(v)==len(set(v)) and min(v)>=0 and max(v)<20 for v in mapping.values()),'integrity')
                    check(f'{case["directory"]}/{method}/count_source_consistency',np.array_equal(arrays['counts'],[len(mapping[str(i)]) for i in range(count)]),'integrity')
                    same(f'{case["directory"]}/{method}/point_count',count,selected['maps'][method]['points'])
                    maps[method]=(poses[0]@np.c_[arrays['points']*c,np.ones(count)].T).T[:,:3]
                for sel in selected['selected']:
                    q=sel['frame'];label=f'B{b}/stride{stride}/Q{q}';old=references[(b,stride,q)]
                    target,valid,support=supports_from_raw(depths,masks,poses,q)
                    predictions={m:rasterize_centres(maps[m],poses[q]) for m in METHODS}
                    common=valid&np.isfinite(predictions['first_write'])&np.isfinite(predictions['frame_mean'])
                    arrays={'target':target,'valid':valid,'support':support,**predictions,'common':common}
                    with np.load(folder/f'query{q}_scoring.npz') as archived:
                        for key,a in arrays.items():arrays_equal(label+'/'+key,a,archived[key])
                    np.savez_compressed(out/f'block{b}_stride{stride}_query{q}.npz',**arrays)
                    score=dict(block=b,split=block['split'],stride=stride,frame=q,valid_target_pixels=int(valid.sum()),common_pixels=int(common.sum()),geometry={},retrieval={},controls={})
                    for method in METHODS:
                        own=valid&np.isfinite(predictions[method]);s=statistics(predictions[method],target,common)
                        s['own_support']=statistics(predictions[method],target,own);s['coverage_of_valid_target']=float(own.sum()/valid.sum())
                        score['geometry'][method]=s
                    fraction=lambda ids:float(np.count_nonzero(np.logical_or.reduce(support[ids],axis=0)&valid)/valid.sum())
                    for width in ['160','320']:
                        pair={}
                        for method in METHODS:
                            ids=sel['retrieval'][width][method]['selected']
                            check(label+'/'+width+'/'+method+'/IDs',len(ids)==4 and len(set(ids))==4 and all(0<=i<20 for i in ids),'integrity')
                            check(label+'/'+width+'/'+method+'/sealed_record',ids==old['retrieval'][width][method]['selected'],'integrity')
                            pair[method]=dict(selected=ids,support_coverage=fraction(ids))
                        pair['selection_set_changed']=set(pair['first_write']['selected'])!=set(pair['frame_mean']['selected'])
                        pair['coverage_delta_pp']=100*(pair['frame_mean']['support_coverage']-pair['first_write']['support_coverage'])
                        score['retrieval'][width]=pair
                    for control,ids in sel['controls'].items():score['controls'][control]=dict(selected=ids,support_coverage=fraction(ids))
                    check(label+'/recent_ids',sel['controls']['recent4']==[16,17,18,19])
                    distances=[np.arccos(np.clip((np.trace(relative[q,:3,:3].T@relative[h,:3,:3])-1)/2,-1,1))+.1*np.linalg.norm(relative[q,:3,3]-relative[h,:3,3]) for h in range(20)]
                    check(label+'/nearest_pose_ids',np.argsort(distances)[:4].tolist()==sel['controls']['nearest_pose4'])
                    score['all_history_support_coverage']=fraction(list(range(20)))
                    for method in METHODS:check(label+'/'+method+'/all20_bound',score['retrieval']['160'][method]['support_coverage']<=score['all_history_support_coverage'])
                    same(label+'/scores',score,old);recomputed.append(score)
                print(f'Completed block {b}, stride {stride}',flush=True)
        groups=[aggregate(recomputed,s,st) for s in ['development','test'] for st in [8,12]]
        analysis=read(root/'results/S6_memory_analysis/summary.json')
        for group in groups:
            old=next(g for g in analysis['groups'] if g['split']==group['split'] and g['stride']==group['stride'])
            same(f'aggregate/{group["split"]}/{group["stride"]}',group,old)
        check('60_history_frames',len({(x['block'],x['frame']) for x in histories})==60)
        check('420_history_arrays',len(histories)==420)
        check('48_width_pairs',sum(len(r['retrieval']) for r in recomputed)==48)
        for name,digest in before.items():check('preserved/'+name,sha(root/name)==digest,'integrity')
        save(out/'records.json',recomputed);save(out/'aggregate.json',groups);save(out/'normalizations.json',scales);save(out/'history_comparison.json',histories)
        report.update(status='passed',paired_query_conditions=24,actual_distinct_queries=12,main_distinct_queries=8,historical_arrays=420,history_frames=60,groups=groups,
                      normalized_scales=scales,model_outputs_finite=504,source_files=len(meta['source_sha256']),original_sha256=before)
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report['completed_utc']=now();report['checks_count']=len(checks);report['checks_by_kind']=dict(Counter(x['kind'] for x in checks))
    save(out/'verification.json',report)
    print(json.dumps({k:report[k] for k in ['status','checks_count','checks_by_kind','completed_utc']},ensure_ascii=False))
    if report['status']!='passed':print(report['traceback']);return 1
    return 0

if __name__=='__main__':sys.exit(main())
