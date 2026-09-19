#!/usr/bin/env python3
"""Independent saved-result audit: SciPy SLERP, scalar sums, scatter z-buffer.

No production module is imported and no model is run. Execute after sealed scoring.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation, Slerp

ATOL, RTOL = 1e-6, 1e-5
METHODS = ['ray', 'history_zbuffer', 'history_constant']


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def save(p, x): Path(p).write_text(json.dumps(x, indent=2, allow_nan=False)+'\n')


def independent_pose(rows, t):
    j = int(np.searchsorted(rows[:, 0], t))
    if j >= len(rows) or t < rows[0, 0]: raise ValueError('Extrapolation')
    i = j if rows[j, 0] == t else j-1
    out = np.eye(4)
    if i == j:
        out[:3, :3] = Rotation.from_quat(rows[i, 4:]).as_matrix()
        out[:3, 3] = rows[i, 1:4]
    else:
        gap = rows[j, 0]-rows[i, 0]
        if gap > .1: raise ValueError('Gap')
        a = (t-rows[i, 0])/gap
        out[:3, :3] = Slerp([0., 1.], Rotation.from_quat(rows[[i,j], 4:]))([a]).as_matrix()[0]
        out[:3, 3] = rows[i, 1:4] + a*(rows[j, 1:4]-rows[i, 1:4])
    return out


def independent_warp(zs, poses, target, K, scale):
    """Scatter min reductions, unlike production per-history lexicographic sort."""
    h,w = zs.shape[1:]
    v,u = np.indices((h,w))
    pix, depths, sources = [], [], []
    for i in range(len(zs)):
        z = zs[i].astype(np.float64)
        good = np.isfinite(z) & (z > 0)
        src = np.flatnonzero(good)
        p = np.stack(((u[good]-K[0,2])*z[good]/K[0,0],
                      (v[good]-K[1,2])*z[good]/K[1,1], z[good]), axis=0)
        world = poses[i,:3,:3].astype(np.float64) @ p + poses[i,:3,3,None]
        q = target[:3,:3].T @ (world-target[:3,3,None])
        keep = np.isfinite(q).all(axis=0) & (q[2] > 0)
        q,src = q[:,keep],src[keep]
        xy = np.stack((K[0,0]*q[0]/q[2]+K[0,2], K[1,1]*q[1]/q[2]+K[1,2]))
        ix = np.floor(xy+.5)
        keep = np.isfinite(ix).all(axis=0) & (ix[0]>=0) & (ix[0]<w) & (ix[1]>=0) & (ix[1]<h)
        ix = ix[:,keep].astype(np.int64)
        pix.append(ix[1]*w+ix[0]); depths.append(q[2,keep]); sources.append(i*h*w+src[keep])
    pix,depths,sources = map(np.concatenate, (pix,depths,sources))
    buf = np.full(h*w, np.inf)
    np.minimum.at(buf, pix, depths)
    winner = depths == buf[pix]
    srcbuf = np.full(h*w, np.iinfo(np.int64).max, dtype=np.int64)
    np.minimum.at(srcbuf, pix[winner], sources[winner])
    hole = ~np.isfinite(buf)
    buf[hole] = np.nan; srcbuf[hole] = -1
    return (buf/scale).reshape(h,w), srcbuf.reshape(h,w)


def independent_errors(p, g, mask):
    pv,gv = p[mask].tolist(),g[mask].tolist()
    n = len(pv)
    if not n: return dict(mae_m=None, abs_rel=None, rmse_m=None)
    err = [abs(a-b) for a,b in zip(pv,gv)]
    return dict(mae_m=math.fsum(err)/n,
                abs_rel=math.fsum(e/b for e,b in zip(err,gv))/n,
                rmse_m=math.sqrt(math.fsum(e*e for e in err)/n))


def main():
    ap=argparse.ArgumentParser()
    for name in ['prepare_manifest','prediction_manifest','score_manifest','prediction_seal','score_result_dir','output']:
        ap.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=ap.parse_args()
    if a.output.exists(): raise ValueError('Fresh output required')
    a.output.mkdir(parents=True)
    report=dict(schema='s14e-independent-v1',status='RUNNING',started_utc=utc(),atol=ATOL,rtol=RTOL,
                model_calls=0,checks=[],npz_arrays_decoded=0,depths_decoded=0,
                methods='SciPy SLERP; math.fsum alignment/errors; component pinhole and np.minimum.at; rational nearest pixel indices')
    def check(name, ok):
        report['checks'].append(dict(name=name,passed=bool(ok)))
        if not ok: raise AssertionError(name)
    def close(name,x,y):
        x,y=np.asarray(x),np.asarray(y)
        check(name+' shape',x.shape==y.shape)
        check(name,np.allclose(x,y,atol=ATOL,rtol=RTOL,equal_nan=True))
    def arrays(p):
        with np.load(p,allow_pickle=False) as f:
            d={k:f[k].copy() for k in f.files}
        report['npz_arrays_decoded']+=len(d)
        return d
    try:
        pm,qm,sm,seal=map(read,[a.prepare_manifest,a.prediction_manifest,a.score_manifest,a.prediction_seal])
        pre,model=Path(sm['prepare_result_dir']),Path(sm['model_result_dir'])
        prec,mc,sc=read(pre/'run_metadata.json'),read(model/'run_metadata.json'),read(a.score_result_dir/'run_metadata.json')
        check('all stages successful',all(m['status']=='SUCCESS' for m in [prec,mc,sc]))
        identities={}
        for source in [pm['identities'],qm['identities'],sm['identities'],seal['identities']]:
            for p,d in source.items():
                check('shared identity agreement '+p,p not in identities or identities[p]==d)
                identities[p]=d
        for p in [a.prepare_manifest,a.prediction_manifest,a.score_manifest,a.prediction_seal,a.score_result_dir/'run_metadata.json']:
            identities[str(p.resolve())]=sha(p)
        for name,d in sc['output_sha256'].items(): identities[str((a.score_result_dir/name).resolve())]=d
        check('independent source frozen',identities[str(Path(__file__).resolve())]==sha(__file__))
        for p,d in identities.items(): check('before bytes '+p,sha(p)==d)
        t=lambda s: datetime.fromisoformat(s)
        check('static before prepare/model',t(sm['frozen_utc'])<min(t(prec['started_utc']),t(mc['started_utc'])))
        check('completed predictions before seal before score',max(t(prec['completed_utc']),t(mc['completed_utc']))<t(seal['sealed_utc'])<t(sc['started_utc']))
        hist=arrays(pre/'history_inputs.npz'); allowed=arrays(pre/'allowed_gt_poses.npz')
        with np.load(pm['history_predictions_npz'],allow_pickle=False) as original:
            for i in range(20):
                z0=original[f'frame{i}_pts3d_in_self_view'][0,:,:,2]
                p0=original[f'frame{i}_camera_c2w'][0]
                report['npz_arrays_decoded']+=2
                for name,x,y in [('z',z0,hist['history_self_z'][i]),('pose',p0,hist['history_poses'][i])]:
                    check('history original byte '+str(i)+' '+name,x.dtype==y.dtype and x.shape==y.shape and x.tobytes()==y.tobytes())
        cond=arrays(pre/'condition.npz'); bases=arrays(pre/'baselines.npz'); provenance=arrays(pre/'baseline_provenance.npz')
        alignment=read(pre/'alignment.json'); scored=arrays(a.score_result_dir/'arrays.npz'); metrics=read(a.score_result_dir/'metrics.json')
        frozen=read(pm['frozen_inputs']); frames=frozen['blocks'][0]['frames']
        times=np.array([x['rgb']['timestamp'] for x in frames[:20]]+[x['depth']['timestamp'] for x in frames[20:24]])
        close('history RGB/target depth timestamps',allowed['selected_timestamps'],times)
        rows=np.loadtxt(pm['trajectory'],comments='#')
        gt=np.stack([independent_pose(rows,float(ti)) for ti in times])
        close('24 independent interpolated cameras',allowed['gt_poses'],gt)
        pred=hist['history_poses'].astype(np.float64)
        A=pred[0,:3,:3]@gt[0,:3,:3].T
        us=[A@(g[:3,3]-gt[0,:3,3]) for g in gt[:20]]
        vs=[p[:3,3]-pred[0,:3,3] for p in pred]
        D=math.fsum(float(x*x) for u in us for x in u)
        N=math.fsum(float(x*y) for u,v in zip(us,vs) for x,y in zip(u,v))
        s=N/D; c=pred[0,:3,3]-s*A@gt[0,:3,3]
        for name,x,y in [('A',A,alignment['A']),('c',c,alignment['c']),('s',s,alignment['s_model_per_metric']),('D',D,alignment['D_metric_squared']),('N',N,alignment['N_model_metric'])]:close(name,x,y)
        target=np.stack([np.eye(4) for _ in range(4)])
        for i,g in enumerate(gt[20:]): target[i,:3,:3]=A@g[:3,:3];target[i,:3,3]=s*A@g[:3,3]+c
        close('target transform',target,cond['target_poses'])
        K=np.array([[245.2734375,0,112],[0,245,111.5],[0,0,1.]])
        close('fixed K',cond['K'],np.broadcast_to(K,(4,3,3)))
        v,u=np.indices((224,224)); dirs=np.stack(((u-112)/K[0,0],(v-111.5)/245,np.ones((224,224))),axis=-1)
        for i,p in enumerate(target):
            raw=np.einsum('ij,hwj->hwi',p[:3,:3],dirs)+p[:3,3]
            rr=np.concatenate((np.broadcast_to(p[:3,3],raw.shape),raw/np.sqrt(np.sum(raw*raw,axis=-1))[...,None]),axis=-1)
            close('official encoded rays '+str(i),rr.astype(np.float32),cond['ray_maps'][i])
        z=hist['history_self_z']; good=np.isfinite(z)&(z>0)
        ordered=np.sort(z[good].astype(np.float64));n=len(ordered)
        median=float(ordered[n//2]) if n%2 else float((ordered[n//2-1]+ordered[n//2])/2)
        close('median constant',bases['history_constant_m'],np.full((4,224,224),median/s))
        for i in range(4):
            warp,src=independent_warp(z,pred,cond['target_poses'][i],K,alignment['s_model_per_metric'])
            close('warp '+str(i),warp,bases['history_zbuffer_m'][i])
            check('warp mask '+str(i),np.array_equal(np.isfinite(warp),provenance['warp_valid'][i]))
            check('warp source '+str(i),np.array_equal(src,provenance['warp_source_index'][i]))
        old=arrays(qm['parity_output_npz']); new=arrays(model/'query_call_0.npz')
        check('parity fields',old.keys()==new.keys())
        for k in old:check('byte parity '+k,old[k].shape==new[k].shape and old[k].dtype==new[k].dtype and old[k].tobytes()==new[k].tobytes())
        before=arrays(qm['state_npz']);after=arrays(model/'state_after.npz')
        for k in before:check('unchanged state '+k,before[k].dtype==after[k].dtype and before[k].shape==after[k].shape and before[k].tobytes()==after[k].tobytes())
        allrows=[]
        xmap=((2*(np.arange(224)+37)+1)*640)//(2*299)
        ymap=((2*np.arange(224)+1)*480)//(2*224)
        for i,item in enumerate(sm['targets']):
            with Image.open(item['depth_path']) as im: native=np.array(im)
            report['depths_decoded']+=1
            gtdepth=native[ymap[:,None],xmap[None,:]].astype(np.float64)/5000
            close('independent rational GT crop '+str(i),gtdepth,scored['gt_depth_m'][i])
            out=arrays(model/f'query_call_{i+1}.npz')
            predictions=np.stack([out['pts3d_in_self_view'][0,:,:,2].astype(np.float64)/alignment['s_model_per_metric'],bases['history_zbuffer_m'][i],bases['history_constant_m'][i]])
            close('primary head and baselines '+str(i),predictions,scored['prediction_depth_m'][i])
            gv=np.isfinite(gtdepth)&(gtdepth>0);pos=np.isfinite(predictions)&(predictions>0)
            own=pos&gv;common=gv&np.logical_and.reduce(pos)
            success=own&(predictions<gtdepth*1.25)&(predictions>gtdepth/1.25)
            for name,x in [('gt_valid_mask',gv),('prediction_positive_finite_mask',pos),('own_valid_mask',own),('common_valid_mask',common),('delta1_success_mask',success)]:check(name+' '+str(i),np.array_equal(x,scored[name][i]))
            for j,method in enumerate(METHODS):
                row=dict(query_index=i+20,target_index=i,model_call=i+1,method=method,gt_valid_count=int(gv.sum()),prediction_positive_finite_count=int(pos[j].sum()),own_valid_count=int(own[j].sum()),common_valid_count=int(common.sum()),delta1_success_count=int(success[j].sum()),delta1_all_gt=float(success[j].sum()/gv.sum()) if gv.any() else None,coverage=float(own[j].sum()/gv.sum()) if gv.any() else None)
                for prefix,mask in [('own_',own[j]),('common_',common)]:row.update({prefix+k:v for k,v in independent_errors(predictions[j],gtdepth,mask).items()})
                given=metrics['rows'][i*3+j]
                for k,vv in row.items():
                    if isinstance(vv,float):check('score '+str(i)+' '+method+' '+k,given[k] is not None and math.isclose(vv,given[k],abs_tol=1e-10,rel_tol=1e-10))
                    else:check('score '+str(i)+' '+method+' '+k,vv==given[k])
                allrows.append(row)
        report['independent_rows']=allrows
        for p,d in identities.items():check('after bytes '+p,sha(p)==d)
        report.update(status='PASS',completed_utc=utc(),checked_identities=len(identities),check_count=len(report['checks']))
    except BaseException as e:
        report.update(status='FAILED',completed_utc=utc(),error=repr(e),traceback=traceback.format_exc(),check_count=len(report['checks']))
    save(a.output/'verification.json',report)
    print(json.dumps({k:report[k] for k in ['status','completed_utc','check_count']},ensure_ascii=False))
    return int(report['status']!='PASS')


if __name__=='__main__':raise SystemExit(main())
