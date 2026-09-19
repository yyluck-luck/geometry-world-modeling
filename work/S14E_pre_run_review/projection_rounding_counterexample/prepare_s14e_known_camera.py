#!/usr/bin/env python3
"""Prepare known-camera S14E conditions/baselines, with no image/model/score reads."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import shutil
import sys
import traceback
import numpy as np

K_FIXED = [[245.2734375, 0., 112.], [0., 245., 111.5], [0., 0., 1.]]
ROLES = ['runner','frozen_inputs','s8_metadata','s14d_metadata','s14d_manifest',
         'history_predictions_npz','s14d_probe_npz','trajectory','viewer_path']
CONTRACT = dict(history_count=20,target_indices=[20,21,22,23],history_time='rgb',target_time='depth',
                K=K_FIXED,size=[224,224],max_trajectory_gap_seconds=.1,max_rgb_depth_offset_seconds=.02,
                minimum_alignment_D_metric_squared=1e-12,rotation_atol=1e-5,roundtrip_atol=1e-5,
                roundtrip_rtol=1e-5,history_rgb_allowed=False,target_rgb_allowed=False,target_depth_allowed=False)


def utc():return datetime.now(timezone.utc).isoformat()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def array_id(a):
    return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest())


def validate_manifest(m):
    require(m['schema']=='s14e-known-camera-prepare-manifest-v1','Manifest schema')
    for k,v in CONTRACT.items():require(m['contract'].get(k)==v,'Frozen contract mismatch: '+k)
    require(Path(m['dataset_root']).is_absolute(),'Dataset root absolute')
    for k in ROLES:
        p=m[k];require(Path(p).is_absolute() and str(Path(p).resolve())==p,'Canonical path: '+k)
        require(p in m['identities'],'Missing frozen role: '+k)
    allowed_npz={m['history_predictions_npz'],m['s14d_probe_npz']}
    for p in m['identities']:
        require(Path(p).is_absolute() and str(Path(p).resolve())==p,'Canonical identity path')
        require(Path(p).suffix.lower() not in ['.png','.jpg','.jpeg','.npy','.pth','.pt','.tiff','.exr','.bmp'],
                'No image/depth/weight bytes in prepare identity set: '+p)
        require(Path(p).suffix.lower()!='.npz' or p in allowed_npz,'Unexpected NPZ identity')
        require(Path(p).name not in ['rgb.txt','depth.txt'],'Do not read image association files again')


def validate_poses(poses,atol=1e-5):
    require(poses.ndim==3 and poses.shape[1:]==(4,4) and np.isfinite(poses).all(),'Pose shape/finite')
    require(np.allclose(poses[:,3,:],np.array([0.,0.,0.,1.]),atol=atol,rtol=0),'Pose bottom row')
    rotations=poses[:,:3,:3].astype(np.float64)
    require(np.allclose(rotations@rotations.transpose(0,2,1),np.eye(3),atol=atol,rtol=0),'Nonorthogonal rotation')
    require(np.allclose(np.linalg.det(rotations),1,atol=atol,rtol=0),'Improper rotation')


def quat_matrix(q):
    x,y,z,w=q/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]],dtype=np.float64)


def parse_trajectory(text):
    rows=[]
    for lineno,line in enumerate(text.splitlines(),1):
        body=line.partition('#')[0].strip()
        if not body:continue
        fields=body.split();require(len(fields)==8,'Trajectory columns line '+str(lineno))
        rows.append([float(x) for x in fields])
    a=np.asarray(rows,dtype=np.float64)
    require(a.ndim==2 and a.shape[1]==8 and len(a)>0 and np.isfinite(a).all(),'Trajectory shape/finite')
    require((np.diff(a[:,0])>0).all(),'Trajectory order/duplicate')
    norms=np.linalg.norm(a[:,4:8],axis=1);require((norms>=1e-12).all(),'Zero trajectory quaternion')
    a[:,4:8]/=norms[:,None]
    return a


def interpolate_trajectory(a,t,max_gap=.1):
    require(np.isfinite(t) and a[0,0]<=t<=a[-1,0],'No trajectory extrapolation')
    hi=int(np.searchsorted(a[:,0],t));lo=hi if a[hi,0]==t else hi-1
    gap=float(a[hi,0]-a[lo,0]);require(gap<=max_gap,'Trajectory bracket gap')
    alpha=0. if lo==hi else float((t-a[lo,0])/gap)
    q0=a[lo,4:8];q1=a[hi,4:8].copy();dot=float(q0@q1)
    if dot<0:q1=-q1;dot=-dot
    dot=float(np.clip(dot,-1,1))
    theta=np.arccos(dot)
    denominator=np.sinc(theta/np.pi)
    q=((1-alpha)*np.sinc((1-alpha)*theta/np.pi)*q0+
       alpha*np.sinc(alpha*theta/np.pi)*q1)/denominator
    q=q/np.linalg.norm(q)
    pose=np.eye(4);pose[:3,:3]=quat_matrix(q);pose[:3,3]=(1-alpha)*a[lo,1:4]+alpha*a[hi,1:4]
    return pose,dict(timestamp=float(t),lower_timestamp=float(a[lo,0]),upper_timestamp=float(a[hi,0]),
                     bracket_gap_seconds=gap,alpha=alpha)


def align_history(gt,pred,contract=CONTRACT):
    validate_poses(gt,contract['rotation_atol']);validate_poses(pred,contract['rotation_atol'])
    require(len(gt)==len(pred) and len(gt)>=2,'Alignment history count')
    gt=gt.astype(np.float64);pred=pred.astype(np.float64)
    A=pred[0,:3,:3]@gt[0,:3,:3].T
    a=(gt[:,:3,3]-gt[0,:3,3])@A.T
    b=pred[:,:3,3]-pred[0,:3,3]
    D=float(np.sum(a*a));N=float(np.sum(a*b))
    require(np.isfinite(D) and D>contract['minimum_alignment_D_metric_squared'],'Degenerate metric displacement D')
    s=N/D;require(np.isfinite(s) and s>0,'Nonpositive/nonfinite model-per-metric scale')
    c=pred[0,:3,3]-s*(A@gt[0,:3,3])
    estimated=s*(gt[:,:3,3]@A.T)+c
    residual=pred[:,:3,3]-estimated
    norms=np.linalg.norm(residual,axis=1)
    rms=float(np.sqrt(np.mean(np.sum(residual**2,axis=1))))
    trajectory_rms=float(np.sqrt(np.mean(np.sum(b*b,axis=1))))
    mapped_rot=A[None]@gt[:,:3,:3]
    difference=pred[:,:3,:3].transpose(0,2,1)@mapped_rot
    angles=np.degrees(np.arccos(np.clip((np.trace(difference,axis1=1,axis2=2)-1)/2,-1,1)))
    back=((estimated-c)/s)@A
    require(np.allclose(back,gt[:,:3,3],atol=contract['roundtrip_atol'],rtol=contract['roundtrip_rtol']),
            'Similarity translation roundtrip')
    return dict(schema='s14e-history-alignment-v1',s_model_per_metric=float(s),A=A.tolist(),c=c.tolist(),
                D_metric_squared=D,N_model_metric=N,history_count=len(gt),fit_includes_targets=False,
                residual_vectors_model=residual.tolist(),residual_norms_model=norms.tolist(),
                rms_model=rms,max_residual_model=float(norms.max()),
                predicted_displacement_rms_model=trajectory_rms,
                normalized_rms=None if trajectory_rms==0 else rms/trajectory_rms,
                orientation_residual_degrees=angles.tolist(),
                gt_center_axis_variance_m2=np.var(gt[:,:3,3],axis=0).tolist(),
                predicted_center_axis_variance_model2=np.var(pred[:,:3,3],axis=0).tolist(),
                A_orthogonality_max_error=float(np.max(np.abs(A@A.T-np.eye(3)))),
                translation_roundtrip_max_error_m=float(np.max(np.abs(back-gt[:,:3,3]))))


def map_target_poses(gt,alignment,contract=CONTRACT):
    A=np.array(alignment['A']);c=np.array(alignment['c']);s=alignment['s_model_per_metric']
    result=np.tile(np.eye(4),(len(gt),1,1));result[:,:3,:3]=A[None]@gt[:,:3,:3]
    result[:,:3,3]=s*(gt[:,:3,3]@A.T)+c
    validate_poses(result,contract['rotation_atol'])
    back=(result[:,:3,3]-c)@A/s
    require(np.allclose(back,gt[:,:3,3],atol=contract['roundtrip_atol'],rtol=contract['roundtrip_rtol']),
            'Target translation roundtrip')
    restored=A.T[None]@result[:,:3,:3]
    require(np.allclose(restored,gt[:,:3,:3],atol=contract['roundtrip_atol'],rtol=contract['roundtrip_rtol']),
            'Target rotation roundtrip')
    return result


def extract_ray_factory(path):
    tree=ast.parse(Path(path).read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PointCloudViewer')
    names=['generate_pseudo_intrinsics','get_ray_map']
    methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
    require([n.name for n in methods]==names,'Official ray method domain/order')
    pure=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='OfficialRayFactory',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[]))
    ns={'np':np};exec(compile(pure,str(path),'exec'),ns)
    return ns['OfficialRayFactory'](),ast.unparse(pure)+'\n'


def build_baselines(depths,history_poses,target_poses,K,s,progress=None):
    n,h,w=depths.shape
    require(len(history_poses)==n and s>0 and np.isfinite(s),'Baseline domain')
    valid=np.isfinite(depths)&(depths>0)
    values=depths[valid].astype(np.float64);require(len(values)>0,'No finite positive history depths')
    median=float(np.median(values));constant=median/s
    yy,xx=np.indices((h,w),dtype=np.float64)
    grid=np.stack([xx,yy,np.ones_like(xx)],axis=-1).reshape(-1,3)
    dirs=grid@np.linalg.inv(K).T
    history_diagnostics=[dict(history=i,pixel_count=h*w,finite=int(np.isfinite(d).sum()),positive_finite=int(v.sum()),
                             nonfinite=int((~np.isfinite(d)).sum()),nonpositive_finite=int((np.isfinite(d)&(d<=0)).sum()))
                         for i,(d,v) in enumerate(zip(depths,valid))]
    all_z=[];all_src=[];diags=[]
    for q,target in enumerate(target_poses):
        zbuf=np.full(h*w,np.inf);source=np.full(h*w,-1,dtype=np.int64)
        counts=dict(target=q,history_positive_finite_points=int(valid.sum()),target_nonfinite=0,
                    target_nonpositive_z=0,projection_nonfinite=0,outside_image=0,in_bounds_point_visits=0)
        for i,pose in enumerate(history_poses):
            indices=np.flatnonzero(valid[i].reshape(-1));z=depths[i].reshape(-1)[indices].astype(np.float64)
            points=(dirs[indices]*z[:,None])@pose[:3,:3].astype(np.float64).T+pose[:3,3].astype(np.float64)
            local=(points-target[:3,3])@target[:3,:3]
            finite=np.isfinite(local).all(axis=1);counts['target_nonfinite']+=int((~finite).sum())
            front=finite&(local[:,2]>0);counts['target_nonpositive_z']+=int((finite&~front).sum())
            local=local[front];indices=indices[front]
            homogeneous=local@K.T
            with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
                pixels=homogeneous[:,:2]/homogeneous[:,2,None]
                rounded=np.floor(pixels+.5)
            finite=np.isfinite(rounded).all(axis=1);counts['projection_nonfinite']+=int((~finite).sum())
            inside=finite&(rounded[:,0]>=0)&(rounded[:,0]<w)&(rounded[:,1]>=0)&(rounded[:,1]<h)
            counts['outside_image']+=int((finite&~inside).sum());counts['in_bounds_point_visits']+=int(inside.sum())
            pix=rounded[inside].astype(np.int64);linear=pix[:,1]*w+pix[:,0]
            zq=local[inside,2];src=i*h*w+indices[inside]
            # primary pixel, then positive z, then source index; earlier history wins exact ties.
            order=np.lexsort((src,zq,linear));linear=linear[order];zq=zq[order];src=src[order]
            first=np.r_[True,linear[1:]!=linear[:-1]] if len(linear) else np.zeros(0,dtype=bool)
            linear=linear[first];zq=zq[first];src=src[first]
            take=zq<zbuf[linear];zbuf[linear[take]]=zq[take];source[linear[take]]=src[take]
        covered=np.isfinite(zbuf);zbuf[~covered]=np.nan
        counts.update(covered_pixels=int(covered.sum()),empty_pixels=int((~covered).sum()))
        all_z.append((zbuf/s).reshape(h,w));all_src.append(source.reshape(h,w));diags.append(counts)
        if progress:progress(q,counts)
    warp=np.asarray(all_z,dtype=np.float64);src=np.asarray(all_src,dtype=np.int64)
    baselines=dict(history_zbuffer_m=warp,history_constant_m=np.full(warp.shape,constant,dtype=np.float64))
    provenance=dict(warp_source_index=src,warp_valid=np.isfinite(warp))
    diagnostics=dict(history=history_diagnostics,targets=diags,constant_sample_count=len(values),
                     history_median_model=median,constant_m=constant,confidence_filter_used=False,
                     holes_filled=False,physical_projection='standard pinhole, not official encoded direction')
    return baselines,provenance,diagnostics


def validate_cache_provenance(m,frozen,s8,d,dm):
    require(frozen['schema']=='s8-inputs-v1' and frozen['blocks'][0]['block']==0,'Frozen block0')
    frames=frozen['blocks'][0]['frames'];require(len(frames)==24 and [f['frame'] for f in frames]==list(range(24)),'Frame order')
    require(s8['ok'] and s8['inference_ok'] and d['status']=='SUCCESS','Prior success required')
    require(s8['history_count']==20 and s8['query_count']==4,'S8 history/query count')
    require(s8['predictions_sha256']==m['identities'][m['history_predictions_npz']],'S8 predictions identity')
    require(d['output_sha256']['probe_inputs.npz']==m['identities'][m['s14d_probe_npz']],'S14D probe identity')
    require(d['manifest_sha256']==m['identities'][m['s14d_manifest']],'S14D manifest identity')
    require(frozen['text_file_sha256']['groundtruth.txt']==m['identities'][m['trajectory']],'Frozen trajectory identity')
    for k in ['commit','torch_version','numpy_version','cpu_threads','seed','device']:
        require(s8[k]==d[k],'Cross-run environment: '+k)
    require(s8['cpu_threads']==8 and s8['seed']==0 and s8['device']=='cpu' and s8['dtype']=='float32','CPU8 FP32 seed')
    require(s8['actual_patch_image_size']==[224,224] and s8['actual_head_type']=='linear','S8 architecture/preprocess')
    require(dm['contract']['size']==[224,224] and dm['contract']['history_count']==20,'S14D image contract')
    require(s8['checkpoint']['path']==dm['checkpoint'] and
            s8['checkpoint']['sha256']==dm['identities'][dm['checkpoint']],'Shared checkpoint provenance')
    require(s8['commit']==dm['commit'],'Shared official commit')
    for i,frame in enumerate(frames[:20]):
        expected=dict(path=str(Path(m['dataset_root'])/frame['rgb']['path']),sha256=frame['rgb_sha256'])
        require(s8['images'][i]==expected and dm['history_images'][i]==expected,'History RGB path/order/SHA')
        require(d['decoded_image_paths'][i]==expected['path'],'S14D history decode provenance')
        require(s8['input_tensor_shapes'][i]==[1,3,224,224],'S8 image shape')
        flags=s8['prepared_view_flags'][i]
        require(all(flags[k]==[v] for k,v in dict(img_mask=True,ray_mask=False,update=True,reset=False).items()),'History flags')
    require(len(d['decoded_image_paths'])==len(dm['history_images'])==20,'S14D exactly20 history')
    anchor_checks=s8['query_state_write_audit']['checks']
    for old,new in [('state_feat','state_feat'),('pose_memory','mem')]:
        rows=[r for r in anchor_checks if r['field']==old]
        require(len(rows)==4,'S8 anchor check domain')
        for row in rows:
            require(row['anchor_tensor_sha256']==d['state_before'][new]['sha256'] and
                    row['anchor_shape']==d['state_before'][new]['shape'] and
                    row['anchor_dtype']=='torch.'+d['state_before'][new]['dtype'] and row['exactly_unchanged'],
                    'Cross-run anchor identity: '+old)
    return frames


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'Fresh output directory required');args.output.mkdir(parents=True)
    report=dict(schema='s14e-known-camera-prepare-v1',status='RUNNING',started_utc=utc(),input_reads=[],
                target_rgb_decoded=0,target_depth_decoded=0,history_rgb_decoded=0,model_calls=0,known_camera_gt_allowed=True,
                counters=dict(json_attempts=0,json_decoded=0,npz_open_attempts=0,npz_opened=0,npz_array_attempts=0,npz_arrays_decoded=0,
                              trajectory_read_attempts=0,trajectory_text_read=0,trajectory_rows_decoded=0,identity_hash_attempts=0,identity_hash_successes=0))
    def phase(name):
        report.update(phase=name,updated_utc=utc());write(args.output/'run_metadata.json',report)
        print(json.dumps(dict(utc=utc(),phase=name)),flush=True)
    def read_json(path,role):
        row=dict(path=str(path),role=role,format='json',completed=False);report['input_reads'].append(row);report['counters']['json_attempts']+=1
        value=json.loads(Path(path).read_text());report['counters']['json_decoded']+=1;row['completed']=True;return value
    def identity_check(m):
        for path,digest in m['identities'].items():
            report['counters']['identity_hash_attempts']+=1
            require(sha(path)==digest,'Frozen identity changed: '+path);report['counters']['identity_hash_successes']+=1
    def read_npz(path,keys,role):
        row=dict(path=path,role=role,format='npz',array_reads=[]);report['input_reads'].append(row);report['counters']['npz_open_attempts']+=1
        with np.load(path,allow_pickle=False) as source:
            report['counters']['npz_opened']+=1;values={}
            for k in keys:
                entry=dict(key=k,completed=False);row['array_reads'].append(entry);report['counters']['npz_array_attempts']+=1
                values[k]=source[k].copy();entry['completed']=True;report['counters']['npz_arrays_decoded']+=1
            return values
    try:
        phase('read_manifest');m=read_json(args.manifest,'prepare manifest');validate_manifest(m)
        require(str(Path(__file__).resolve())==m['runner'],'Runner path')
        require(Path(sys.executable).resolve()==Path(m['python']).resolve(),'Python executable')
        report.update(manifest_sha256=sha(args.manifest),python=sys.version,executable=sys.executable,numpy_version=np.__version__)
        phase('pre_run_identity');identity_check(m)
        shutil.copy2(args.manifest,args.output/'frozen_manifest.json');shutil.copy2(__file__,args.output/'source_snapshot.py')
        phase('metadata_cache_provenance')
        f=read_json(m['frozen_inputs'],'fixed S8 block0 frames');s8=read_json(m['s8_metadata'],'old S8 metadata')
        d=read_json(m['s14d_metadata'],'S14D metadata');dm=read_json(m['s14d_manifest'],'S14D original manifest')
        frames=validate_cache_provenance(m,f,s8,d,dm);report['cache_metadata_provenance_pass']=True
        phase('whitelisted_history_array_reads')
        keys=[f'frame{i}_{kind}' for i in range(20) for kind in ['pts3d_in_self_view','camera_c2w']]
        old=read_npz(m['history_predictions_npz'],keys,'history0..19 only, no query decode')
        depth=[];poses=[]
        for i in range(20):
            points=old[f'frame{i}_pts3d_in_self_view'];pose=old[f'frame{i}_camera_c2w']
            require(points.shape==(1,224,224,3) and points.dtype==np.float32,'History self schema')
            require(pose.shape==(1,4,4) and pose.dtype==np.float32,'History camera schema')
            depth.append(points[0,:,:,2].copy());poses.append(pose[0].copy())
        depth=np.stack(depth);poses=np.stack(poses);validate_poses(poses)
        cached=read_npz(m['s14d_probe_npz'],['history_poses'],'S14D history pose parity')['history_poses']
        require(array_id(poses)==array_id(cached),'S8/S14D history pose byte parity')
        report['history_pose_byte_parity_pass']=True;report['history_pose_id']=array_id(poses)
        np.savez_compressed(args.output/'history_inputs.npz',history_self_z=depth,history_poses=poses)
        del old,cached
        phase('allowed_camera_trajectory_read')
        report['counters']['trajectory_read_attempts']+=1
        readrow=dict(path=m['trajectory'],role='shared allowed GT camera trajectory',format='text',completed=False);report['input_reads'].append(readrow)
        text=Path(m['trajectory']).read_text();report['counters']['trajectory_text_read']+=1
        trajectory=parse_trajectory(text);report['counters']['trajectory_rows_decoded']=len(trajectory);readrow['completed']=True
        rgb=np.array([row['rgb']['timestamp'] for row in frames],dtype=np.float64)
        dep=np.array([row['depth']['timestamp'] for row in frames],dtype=np.float64)
        require(np.isfinite(rgb).all() and np.isfinite(dep).all() and np.all(np.abs(rgb-dep)<=.02),'Fixed RGB/depth offset')
        times=np.r_[rgb[:20],dep[20:24]];interpolated=[interpolate_trajectory(trajectory,t,.1) for t in times]
        gt=np.stack([p for p,_ in interpolated]);validate_poses(gt)
        report['camera_interpolations']=[info for _,info in interpolated]
        np.savez_compressed(args.output/'allowed_gt_poses.npz',gt_poses=gt,selected_timestamps=times,rgb_timestamps=rgb,depth_timestamps=dep)
        phase('history_only_alignment')
        alignment=align_history(gt[:20],poses);targets=map_target_poses(gt[20:],alignment)
        write(args.output/'alignment.json',alignment)
        factory,source=extract_ray_factory(m['viewer_path']);(args.output/'extracted_ray_factory.py').write_text(source)
        K=np.array(K_FIXED,dtype=np.float64);rays=np.asarray([factory.get_ray_map(p,224,224,K) for p in targets],dtype=np.float32)
        require(rays.shape==(4,224,224,6) and np.isfinite(rays).all(),'New official ray finite/schema')
        np.savez_compressed(args.output/'condition.npz',target_poses=targets,K=np.repeat(K[None],4,axis=0),ray_maps=rays)
        phase('standard_pinhole_baselines')
        def progress(q,counts):
            report.setdefault('baseline_target_progress',[]).append(counts);phase(f'baseline_target_{q}_complete')
        baseline,provenance,diagnostics=build_baselines(depth,poses,targets,K,alignment['s_model_per_metric'],progress)
        np.savez_compressed(args.output/'baselines.npz',**baseline);np.savez_compressed(args.output/'baseline_provenance.npz',**provenance)
        write(args.output/'baseline_diagnostics.json',diagnostics)
        require(report['counters']['npz_arrays_decoded']==41,'Exact 41 whitelisted array budget')
        phase('post_run_identity');identity_check(m);require(sha(args.manifest)==report['manifest_sha256'],'Manifest changed')
        report.update(before_after_identity_pass=True,output_sha256={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file() and p.name!='run_metadata.json'},
                      peak_rss_native=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,status='SUCCESS',phase='complete',completed_utc=utc())
        write(args.output/'run_metadata.json',report)
        payload={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file()}
        write(args.output/'condition_seal.json',dict(schema='s14e-condition-seal-v1',sealed_utc=utc(),condition_npz_sha256=payload['condition.npz'],
                                                   payload_sha256=payload,prepare_manifest_sha256=report['manifest_sha256']))
        print(json.dumps(dict(status='SUCCESS',s_model_per_metric=alignment['s_model_per_metric'],arrays_decoded=41)),flush=True)
    except BaseException as e:
        report.update(status='FAILED',completed_utc=utc(),error=repr(e),traceback=traceback.format_exc());write(args.output/'run_metadata.json',report)
        print(report['traceback'],file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
