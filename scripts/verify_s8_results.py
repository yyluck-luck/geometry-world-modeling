#!/usr/bin/env python3
"""Independent S8 audit, gated on completed replay before reading new data.

Rebuild measurements from raw RGB/depth PNGs and GT, then replay saved events,
recompute saved-render voting and decisions, and score independent projections.
Only older independent S6/S7 audit math is imported; no production experiment
or scoring module, model inference, or surfel renderer is executed. State and
historical sealing claims remain authenticated metadata/source-order evidence.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime
import hashlib
from importlib.metadata import version
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import traceback
import zipfile
import numpy as np
from PIL import Image
import torch
from verify_s6_scores import (crop_measurement, pose_at, quaternion_matrix,
    supports_from_raw, rasterize_centres, statistics, map_hash, K)
from verify_s7_replay import (reconstruct_paths, votes_from_render, independently_select,
    Checks, ARMS, READOUTS, ATOL, RTOL, contrasts, aggregate, now, sha, save)

ROOT = Path(__file__).resolve().parents[1]
S6_HELPER_SHA = 'bd6bd1d88c3297e89cd556fd6d6c4b3517f2828562aea272f23ce0069ce159a2'
S7_HELPER_SHA = '506ad1e33a053b2d9d0fabe69fd2a611f48ce4b7201e860fa98c2f60e5fd42e0'
RUNNER_SHA = 'cc3ae6fd6243ce3531e540dc8c70ef61af0e868c919c7232a16616cf750ba292'
BASE_RUNNER_SHA = 'efb3c8b72ada668818d4211e6d5bb4aa357a3404778cf29d849f8551160bf923'
CHECKPOINT_SHA = '7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d'
COMMIT = '8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf'
ADAPTER_SHA = '6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e'
PRECISION = ('Parameters, inputs and saved outputs FP32; official encoder internally '
             'casts Q/K to FP16 for RoPE and restores the original dtype')
SHAPES = {'pts3d_in_self_view':[1,224,224,3], 'pts3d_in_other_view':[1,224,224,3],
    'conf_self':[1,224,224], 'conf':[1,224,224], 'rgb':[1,224,224,3],
    'camera_pose':[1,7], 'camera_c2w':[1,4,4]}
REQUIRED_SOURCES = ('scripts/run_s8_replay.py','scripts/run_s8_sequence.py',
    'scripts/run_s6_cut3r.py','scripts/run_cut3r_local.py','scripts/cut3r_rope_compat.py',
    'scripts/run_s6_memory.py','scripts/evaluate_cut3r_pair.py','src/s7_event_replay.py',
    'src/s6_memory_bridge.py','src/rgbd_memory.py','src/rgbd_metrics.py','src/rgbd_retrieval.py',
    'src/rgbd_experiment.py','src/rgbd_dataset.py','src/experiment_io.py',
    'src/learned_pair_metrics.py','src/tum_rgbd.py','src/retrieval_diagnostic.py',
    'src/vmem_memory_kernel.py','src/vmem_retrieval_kernel.py')


def strict_json(text):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('Duplicate JSON key: '+key)
            result[key]=value
        return result
    def bad(value): raise ValueError('Nonfinite JSON token: '+value)
    return json.loads(text, object_pairs_hook=unique, parse_constant=bad)


def safe_under(root, name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name or '\0' in name:
        raise ValueError('Unsafe relative path')
    relative=PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or str(relative)!=name:
        raise ValueError('Noncanonical relative path')
    root=Path(root).resolve(strict=True); path=(root/name).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file(): raise ValueError('Path escapes root')
    return path


def source_path(name):
    path=Path(name)
    return (path if path.is_absolute() else ROOT/path).resolve(strict=True)


def valid_sha(value): return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def pose_at_closed(trajectory, stamp):
    """Exact samples, including isolated/end samples, have zero interpolation gap.

    S6's handwritten SLERP remains unchanged for non-exact timestamps.
    """
    i=int(np.searchsorted(trajectory[:,0],stamp))
    if i<len(trajectory) and trajectory[i,0]==stamp:
        row=trajectory[i]; result=np.eye(4)
        result[:3,:3]=quaternion_matrix(row[4:]); result[:3,3]=row[1:4]
        return result,0.
    return pose_at(trajectory,stamp)


def normalized_from_raw(raw):
    first=raw['frame0_pts3d_in_self_view'][0,:,:,2].astype(np.float64)
    good=np.isfinite(first)&(first>0)
    if not good.any(): raise ValueError('No positive first prediction')
    normalization=1./float(np.median(first[good]))
    depths=[raw[f'frame{i}_pts3d_in_self_view'][0,:,:,2].astype(np.float64)*normalization for i in range(24)]
    absolute=np.stack([raw[f'frame{i}_camera_c2w'][0].astype(np.float64) for i in range(24)])
    # Independent linear solve rather than the production inverse-multiply path.
    poses=np.linalg.solve(absolute[0],absolute); poses[:,:3,3]*=normalization
    return depths,poses,normalization


def rebuilt_observations(depths, confs, rgbs, poses, stride):
    """Independent pixel-grid acceptance and ray geometry, no Surfel/Memory class.

    Every grid location is classified in order, with scalar rejection decisions.
    Geometry is then vectorized over accepted rays. Attribute floats use the
    inherited 1e-9/1e-10 tolerance; identities/colors/counts are exact.
    """
    ids=[]; points=[]; normals=[]; radii=[]; colors=[]; offsets=[0]; filters=[]
    fx,fy,cx,cy=K
    for frame,(z,conf,rgb,pose) in enumerate(zip(depths[:20],confs,rgbs[:20],poses[:20])):
        positive=np.isfinite(z)&(z>0); confidence=np.isfinite(conf)&(conf>=1.)
        cutoff=float(np.quantile(z[positive],.999)) if positive.any() else None
        near=z<=cutoff if cutoff is not None else np.zeros(z.shape,bool)
        eligible=positive&confidence&near
        record=dict(total_pixels=z.size,positive_finite_depth_pixels=int(positive.sum()),
            rejected_pixel_depth=int((~positive).sum()),
            rejected_pixel_confidence_after_depth=int((positive&~confidence).sum()),
            rejected_pixel_far_after_depth_confidence=int((positive&confidence&~near).sum()),
            eligible_pixels=int(eligible.sum()),far_cutoff_normalized=cutoff,
            sampled_grid_points=len(range(0,224,stride))**2,stride=stride,
            neighbor_jump_threshold_normalized=.05,rejected_sample_boundary=0,
            rejected_sample_center=0,rejected_sample_neighbor=0,
            rejected_sample_neighbor_jump=0,rejected_sample_degenerate_normal=0)
        accepted=[]
        for v in range(0,224,stride):
            for u in range(0,224,stride):
                rejection=None
                if u>=223 or v>=223: rejection='boundary'
                elif not eligible[v,u]: rejection='center'
                elif not (eligible[v,u+1] and eligible[v+1,u]): rejection='neighbor'
                elif abs(z[v,u+1]-z[v,u])>.05 or abs(z[v+1,u]-z[v,u])>.05: rejection='neighbor_jump'
                if rejection: record['rejected_sample_'+rejection]+=1
                else: accepted.append((u,v))
        uv=np.asarray(accepted,dtype=np.int64).reshape(-1,2); u,v=uv.T
        def ray(x,y):
            zz=z[y,x]
            return np.column_stack(((x-cx)*zz/fx,(y-cy)*zz/fy,zz))
        p=ray(u,v); n=np.cross(ray(u+1,v)-p,ray(u,v+1)-p)
        lengths=np.linalg.norm(n,axis=1); keep=np.isfinite(lengths)&(lengths>1e-12)
        record['rejected_sample_degenerate_normal']=int((~keep).sum())
        p,n,u,v,lengths=p[keep],n[keep],u[keep],v[keep],lengths[keep]
        n=n/lengths[:,None]; cosine=np.sum(n*(p/np.linalg.norm(p,axis=1)[:,None]),axis=1)
        n[cosine<0]*=-1
        r=.5*z[v,u]/((fx+fy)/2/stride)/(.2+.8*np.abs(cosine))
        ids.extend((frame,int(x),int(y)) for x,y in zip(u,v))
        points.extend(p@pose[:3,:3].T+pose[:3,3]); normals.extend(n@pose[:3,:3].T)
        radii.extend(r); colors.extend(rgb[v,u].astype(np.float64)/255.)
        offsets.append(len(ids)); record['accepted_surfels']=len(u); filters.append(record)
    return dict(ids=np.asarray(ids,dtype=np.int64).reshape(-1,3),
        points=np.asarray(points).reshape(-1,3),normals=np.asarray(normals).reshape(-1,3),
        radii=np.asarray(radii),colors=np.asarray(colors).reshape(-1,3),offsets=np.asarray(offsets)),filters


def sampling_from_timestamps(rgb, depth, trajectory):
    """Independently enumerate greedy pairs and fixed-duration window choices."""
    # Exhaustive differences to each depth table, then global lexicographic order.
    dt=np.array([x[0] for x in depth]); candidates=[]
    for i,(t,_) in enumerate(rgb):
        for j in np.flatnonzero(np.abs(dt-t)<.020):
            candidates.append((abs(t-dt[j]),t,float(dt[j]),i,int(j)))
    used_r=set(); used_d=set(); matches=[]
    for _,_,_,i,j in sorted(candidates):
        if i not in used_r and j not in used_d:
            matches.append((rgb[i],depth[j])); used_r.add(i); used_d.add(j)
    matches.sort(key=lambda pair:pair[0][0])
    ts=trajectory[:,0]; cuts=np.flatnonzero(np.diff(ts)>.1)+1
    intervals=[(part[0],part[-1]) for part in np.split(ts,cuts)]
    segments=[]; last_interval=None; last_time=None
    for index,(r,d) in enumerate(matches):
        interval=next((k for k,(a,b) in enumerate(intervals) if a<=r[0]<=b and a<=d[0]<=b),None)
        if interval is None: continue
        if last_interval!=interval or last_time is None or r[0]-last_time>.1: segments.append([])
        segments[-1].append((index,r,d)); last_interval=interval; last_time=r[0]
    accepted=[]; available=-np.inf
    for segment in segments:
        stamps=np.asarray([x[1][0] for x in segment])
        for start in stamps:
            if start<=available: continue
            end=float(start)+8.840
            if end>stamps[-1]: break
            targets=[float(start)+8.840*i/23 for i in range(24)]
            # First argmin is the earlier timestamp, including exact distance ties.
            positions=[int(np.argmin(np.abs(stamps-t))) for t in targets]
            errors=[abs(float(stamps[i])-t) for i,t in zip(positions,targets)]
            if max(errors)>.050 or len(set(positions))!=24: continue
            accepted.append(dict(nominal_start=float(start),nominal_end=end,
                target_timestamps=targets,snap_errors=errors,rows=[segment[i] for i in positions]))
            available=end+.1
    if len(accepted)<3: raise ValueError('Independent sampling finds fewer than three windows')
    indices=[0,(len(accepted)-1)//2,len(accepted)-1]
    return accepted,indices,len(matches)


class Reader:
    def __init__(self, check): self.check=check; self.before={}
    def track(self,p):
        p=Path(p).resolve(strict=True); digest=sha(p)
        if str(p) in self.before: self.check('read_stable/'+str(p),self.before[str(p)]==digest,'integrity')
        self.before[str(p)]=digest; return p
    def integrity(self,p,digest,label=None):
        p=self.track(p); self.check(label or 'sha/'+str(p),valid_sha(digest) and self.before[str(p)]==digest,'integrity')
    def json(self,p): return strict_json(self.track(p).read_text())
    def arrays(self,p):
        with np.load(self.track(p),allow_pickle=False) as z: return {k:z[k] for k in z.files}
    def text(self,p): return self.track(p).read_text()


def fixed_metadata(check,prefix,actual,expected):
    for key,value in expected.items():
        check(prefix+'/'+key,key in actual and type(actual[key]) is type(value) and actual[key]==value,'metadata')


def verify_state(raw,check,prefix):
    flags=[dict(frame=i,img_mask=[True],ray_mask=[False],update=[i<20],reset=[False]) for i in range(24)]
    for name in ('requested_view_flags','prepared_view_flags','view_flags_before_inference','view_flags_after_inference'):
        check(prefix+'/'+name,raw.get(name)==flags,'metadata')
    fixed_metadata(check,prefix,raw,dict(history_count=20,query_count=4,view_policy_preserved=True,history_only_memory_ok=True))
    state=raw['query_state_write_audit']
    fixed_metadata(check,prefix+'/state',state,dict(ok=True,expected_snapshots=25,actual_snapshots=25,
        anchor_snapshot_index=20,history_count=20,query_count=4,fields={'state_feat':0,'pose_memory':3}))
    rows=state['checks']; domains={(f,i) for f in ('state_feat','pose_memory') for i in range(21,25)}
    check(prefix+'/state/coverage',len(rows)==8 and {(r['field'],r['snapshot_index']) for r in rows}==domains,'metadata')
    anchors={}; shapes={'state_feat':[1,768,768],'pose_memory':[1,256,1536]}
    for r in rows:
        tag=prefix+f"/state/{r['field']}/{r['snapshot_index']}"
        fixed_metadata(check,tag,r,dict(exactly_unchanged=True,finite=True,anchor_finite=True,
            same_shape_and_dtype=True,after_view=r['snapshot_index']-1,
            shape=shapes[r['field']],anchor_shape=shapes[r['field']],dtype='torch.float32',anchor_dtype='torch.float32'))
        check(tag+'/difference_and_hash',r['max_absolute_difference']==0 and valid_sha(r['tensor_sha256']) and
              r['tensor_sha256']==r['anchor_tensor_sha256'],'metadata')
        anchors.setdefault(r['field'],r['anchor_tensor_sha256'])
        check(tag+'/same_history_anchor',anchors[r['field']]==r['anchor_tensor_sha256'],'metadata')
    staging=raw['input_device_staging']; rows=staging['checks']
    fields=('img','ray_map','camera_pose','img_mask','ray_mask','update','reset')
    check(prefix+'/staging',staging['all_values_preserved'] is True and len(rows)==168 and
          {(r['view'],r['field']) for r in rows}=={(i,f) for i in range(24) for f in fields} and
          all(r['values_preserved'] is True for r in rows) and
          staging['mode']=='blocking_before_official_inference','metadata')


def verify_model(directory,block,sequence,entry,reader,check,meta):
    b=block['block']; tag=f'B{b}/model'; raw=reader.json(directory/'run_metadata.json')
    reader.integrity(directory/'run_metadata.json',entry['metadata_sha256'])
    fixed_metadata(check,tag,raw,dict(ok=True,phase='complete',inference_ok=True,device='cpu',dtype='float32',
        cpu_threads=8,seed=0,views=24,runner_sha256=RUNNER_SHA,base_runner_sha256=BASE_RUNNER_SHA,
        commit=COMMIT,tracked_changes='',actual_head_type='linear',actual_patch_image_size=[224,224],
        parameters=748443655,checkpoint_all_keys_matched=True,upstream_source_files_unmodified=True,
        upstream_execution_unmodified=False,precision_semantics=PRECISION,input_tensor_shapes=[[1,3,224,224]]*24,
        all_outputs_finite=True,required_outputs_present=True,vmem_complete_pipeline=False,
        video_generated=False,accuracy_evaluated=False,resolution_model='224_linear_intermediate'))
    check(tag+'/checkpoint_identity',raw['checkpoint']==sequence['checkpoint'] and
        raw['checkpoint']['sha256']==CHECKPOINT_SHA and raw['checkpoint']['bytes']==2994205002,'metadata')
    check(tag+'/loading_and_head',raw['checkpoint_serialization']['weights_only'] is True and
        raw['model_config']['downstream_head_class']=='dust3r.heads.linear_head.LinearPts3dPose','metadata')
    reader.integrity(directory/'runner_snapshot.py',RUNNER_SHA)
    expected_images=[dict(path=x['rgb']['path'],sha256=x['rgb']['sha256'])
        for x in sequence['input_identities'] if x['block']==b]
    check(tag+'/RGB_order',raw['images']==expected_images,'metadata')
    check(tag+'/process_identity',raw['repo']==sequence['repo'] and
        raw['python_executable']==sequence['python_executable'],'metadata')
    modules=raw['loaded_modules']; repo=Path(sequence['repo']).resolve(strict=True)
    check(tag+'/loaded_module_coverage',set(modules)=={'dust3r.model','dust3r.inference','dust3r.utils.image','models.pos_embed'},'metadata')
    for name,path in modules.items():
        path=Path(path).resolve(strict=True)
        check(tag+'/loaded_module_path/'+name,path.is_relative_to(repo),'integrity')
        reader.integrity(path,sequence['upstream_python_sha256'][str(path.relative_to(repo))])
    compat=raw['runtime_compatibility']
    fixed_metadata(check,tag+'/compat',compat,dict(signed_rope_adapter=True,blocking_input_staging=True,adapter_sha256=ADAPTER_SHA))
    check(tag+'/signed_validation',compat['validation_sha256']==sequence['signed_rope_check_sha256']==
          sha(directory.parent/'signed_rope_check.json'),'integrity')
    verify_state(raw,check,tag)
    reader.integrity(directory/'s8_output_verification.json',entry['verification_sha256'])
    verified=reader.json(directory/'s8_output_verification.json')
    fixed_metadata(check,tag+'/controller_array_audit',verified,dict(ok=True,arrays_verified=168,input_identity_verified=True,
        metadata_sha256=entry['metadata_sha256'],runner_sha256=RUNNER_SHA))
    check(tag+'/state_audit_copy',verified['query_state_write_audit']==raw['query_state_write_audit'],'metadata')
    reader.integrity(directory/'predictions.npz',entry['predictions_sha256'])
    check(tag+'/prediction_references',entry['predictions_sha256']==raw['predictions_sha256']==
          verified['predictions_sha256']==meta['model_prediction_sha256'][str(b)],'integrity')
    arrays=reader.arrays(directory/'predictions.npz')
    expected={f'frame{i}_{key}':shape for i in range(24) for key,shape in SHAPES.items()}
    check(tag+'/168_array_keys',set(arrays)==set(expected)==set(verified['arrays'])==set(raw['outputs']))
    for key,shape in expected.items():
        value=arrays[key]; t=tag+'/'+key
        check(t+'/shape_dtype_finite',list(value.shape)==shape and value.dtype==np.float32 and np.isfinite(value).all())
        check(t+'/tensor_record',verified['arrays'][key]==dict(shape=shape,dtype='float32',all_finite=True,
            tensor_sha256=hashlib.sha256(value.tobytes()).hexdigest()))
        item=raw['outputs'][key]
        check(t+'/output_record',item['shape']==shape and item['dtype']=='float32' and item['all_finite'] is True and
            item['finite_fraction']==1. and item['min']==float(value.min()) and item['max']==float(value.max()))
    fixed_metadata(check,tag+'/controller',entry,dict(block=b,split='test',ok=True,arrays_verified=168,
        history_only_memory_ok=True,returncode=0))
    check(tag+'/resources',type(entry['process_peak_rss_bytes']) is int and
        0<entry['process_peak_rss_bytes']<=16*1024**3 and entry['monitored_seconds']<=900 and
        raw['peak_process_rss_bytes']==entry['process_peak_rss_bytes'] and not entry.get('stop_reason'),'metadata')
    expected_command=[sequence['python_executable'],str(ROOT/'scripts/run_s6_cut3r.py'),
        '--repo',sequence['repo'],'--checkpoint',sequence['checkpoint']['path'],
        '--images',*[x['path'] for x in expected_images], '--device','cpu','--threads','8',
        '--history-count','20','--output',str(directory),'--input-source',
        f"S8 block{b}; RGB only; history20/query4; manifest {sequence['manifest_sha256']}",
        '--signed-rope-check']
    command=entry['command']
    check(tag+'/RGB_only_model_command',len(command)==len(expected_command)+1 and
        command[:-1]==expected_command,'metadata')
    reader.integrity(Path(command[-1]),sequence['signed_rope_check_sha256'])
    times=[datetime.fromisoformat(x) for x in (entry['started_utc'],raw['started_utc'],
        raw['completed_utc'],entry['completed_utc'],sequence['completed_utc'])]
    check(tag+'/model_time_order',all(a<=b for a,b in zip(times,times[1:])) and
        entry['model_completed_utc']==raw['completed_utc'],'metadata')
    rss=reader.json(directory.parent/f'block{b}.rss.json')
    check(tag+'/RSS_samples',rss['sample_interval_seconds']==.5 and len(rss['samples'])>0 and
        max(r['rss_bytes'] for r in rss['samples'])==entry['observed_peak_rss_bytes'] and
        entry['observed_peak_rss_bytes']<=16*1024**3,'metadata')
    return raw,arrays


def source_order_and_integrity(args,meta,freeze,reader,check):
    reader.integrity(args.protocol,freeze['protocol_sha256'])
    reader.integrity(args.manifest,freeze['manifest_sha256'])
    check('freeze_metadata_copy',freeze==meta['freeze'],'metadata')
    check('input_references',meta['protocol_sha256']==sha(args.protocol) and
        meta['manifest_sha256']==sha(args.manifest) and meta['freeze_sha256']==sha(args.freeze),'integrity')
    sources={source_path(k):v for k,v in freeze['execution_source_sha256'].items()}
    check('freeze_execution_paths',len(sources)==len(freeze['execution_source_sha256']) and
        {(ROOT/n).resolve() for n in REQUIRED_SOURCES}<=set(sources),'integrity')
    for p,digest in sources.items(): reader.integrity(p,digest)
    measurements={source_path(k):v for k,v in freeze['measurement_file_sha256'].items()}
    check('freeze_measurement_paths',len(measurements)==len(freeze['measurement_file_sha256']) and
        safe_under(args.data,'groundtruth.txt') in measurements,'integrity')
    for p,digest in measurements.items(): reader.integrity(p,digest)
    time_names=('started_utc','selections_sealed_utc','first_gt_pose_decode_utc','first_depth_decode_utc','completed_utc')
    times=[datetime.fromisoformat(freeze['frozen_utc'])]+[datetime.fromisoformat(meta[k]) for k in time_names]
    check('freeze_start_seal_decode_completion_order',all(a<=b for a,b in zip(times,times[1:])),'metadata',
          detail=[t.isoformat() for t in times])
    for b,norm in meta['normalizations'].items():
        t=datetime.fromisoformat(norm['scale_fitted_utc'])
        check(f'B{b}/scale_after_measurement_decode',times[4]<=t<=times[-1],'metadata')
    reader.integrity(args.results/'experiment_source.zip',meta['experiment_source_sha256'])
    with zipfile.ZipFile(args.results/'experiment_source.zip') as archive:
        check('source_archive_members',len(archive.namelist())==len(set(archive.namelist())) and
              set(archive.namelist())==set(meta['source_sha256'])==set(meta['source_original_paths']),'integrity')
        for name,digest in meta['source_sha256'].items():
            original=Path(meta['source_original_paths'][name]).resolve(strict=True)
            reader.integrity(original,digest,'original/'+name)
            check('archived/'+name,hashlib.sha256(archive.read(name)).hexdigest()==digest,'integrity')
        reverse={str(Path(p).resolve()):name for name,p in meta['source_original_paths'].items()}
        check('all_frozen_sources_archived',all(str(p) in reverse for p in sources),'integrity')
        code=archive.read(reverse[str((ROOT/'scripts/run_s8_replay.py').resolve())]).decode()
    tree=ast.parse(code); assignments={}
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign):
            for target in node.targets: assignments[ast.unparse(target)]=node.lineno
    seal=assignments["meta['selections_sealed_utc']"]
    calls={name:[n.lineno for n in ast.walk(tree) if isinstance(n,ast.Call) and
        isinstance(n.func,ast.Name) and n.func.id==name] for name in ('read_trajectory','measured_target','first_frame_scale','measured_support')}
    check('archived_source_measurements_after_seal',all(v and all(n>seal for n in v) for v in calls.values()),'source_order',detail=calls)
    check('archived_source_depth_decoding_after_seal',assignments['native']>seal,'source_order')
    imported={n.module for n in ast.walk(ast.parse(Path(__file__).read_text())) if isinstance(n,ast.ImportFrom)}
    check('independent_import_boundary',not any(x and (x.startswith('run_') or x.startswith('s8_') or
        x in ('s7_event_replay','s6_memory_bridge','learned_pair_metrics','rgbd_experiment','tum_rgbd')) for x in imported),'source_order')


def audit(args,meta):
    out=args.output; out.mkdir(parents=True,exist_ok=False)
    check=Checks(); reader=Reader(check); records=[]; scales=[]
    for name in ('verify_s8_results.py','verify_s6_scores.py','verify_s7_replay.py'):
        shutil.copy2(Path(__file__).with_name(name),out/name)
    report=dict(status='running',started_utc=now(),checks=check.items,verifier_sha256=sha(__file__),
        parameters={k:str(getattr(args,k)) for k in ('manifest','protocol','freeze','runs','data','results','output')},
        independent_s6_helper_sha256=sha(Path(__file__).with_name('verify_s6_scores.py')),
        independent_s7_helper_sha256=sha(Path(__file__).with_name('verify_s7_replay.py')),
        tolerance=dict(float_atol=ATOL,float_rtol=RTOL,
            exact='depth target/masks/support/IDs/counts/events/maps/sources/readout traces; RGB colors'),
        environment=dict(python=sys.version,packages={n:version(n) for n in ('numpy','scipy','torch','Pillow')},
            torch_default_dtype=str(torch.get_default_dtype())),
        limitations=[
            'No model inference is repeated; 504 saved model arrays are authenticated and checked, not regenerated.',
            'Raw latent-state tensors are absent. Query-state isolation is a complete schema/hash/flag metadata audit, not a fresh tensor comparison.',
            'Surfel polygon rendering is not rerun. Votes, allocation, float32 sorting and NMS are independently recomputed conditional on authenticated saved render buffers.',
            'Timing/sealing order is authenticated metadata plus static executed-source order, not a recovered historical file-access trace.',
            'Model numerical precision and resource use remain recorded implementation/runtime evidence; the controller process is not reenacted.',
            'Three blocks belong to one external scene. Strides/readouts and adjacent queries are repeated conditions, not independent scenes or statistical replicates.',
            'Depth supports and centre-projection errors are component geometric diagnostics, not generated-video quality.'])
    save(out/'verification.json',report)
    try:
        torch.set_num_threads(1)
        check('S6_independent_helper_pinned',report['independent_s6_helper_sha256']==S6_HELPER_SHA,'integrity')
        check('S7_independent_helper_pinned',report['independent_s7_helper_sha256']==S7_HELPER_SHA,'integrity')
        reader.track(__file__); reader.track(Path(__file__).with_name('verify_s6_scores.py')); reader.track(Path(__file__).with_name('verify_s7_replay.py'))
        reader.track(args.results/'run_metadata.json')
        check('completed_replay',meta['status']=='completed' and meta['phase']=='complete','metadata')
        check('replay_environment',report['environment']['packages']==meta['environment']['packages'] and
            report['environment']['torch_default_dtype']==meta['environment']['torch_default_dtype'],'metadata')
        freeze=reader.json(args.freeze); manifest=reader.json(args.manifest)
        source_order_and_integrity(args,meta,freeze,reader,check)
        protocol=reader.text(args.protocol)
        contracts={}
        for name in ('controller','replay'):
            fences=re.findall(r'^```s8-'+name+r'-json\s*\n(.*?)^```\s*$',protocol,re.M|re.S)
            check('protocol/'+name+'_single_fence',len(fences)==1,'metadata'); contracts[name]=strict_json(fences[0])
        fixed_metadata(check,'replay_contract',contracts['replay'],dict(schema='s8-replay-v1',strides=[8,12],width=160,
            maps=list(ARMS),readouts=list(READOUTS),block_count=3,frames_per_block=24,history_count=20,query_count=4,
            splits=['test']*3,native_size=[640,480],native_intrinsics=[525.,525.,319.5,239.5],depth_divisor=5000.,
            extra_depth_scale=1.,gt_pose_timestamp='rgb',max_gt_gap_seconds=.1,measurement_after_all_selections_sealed=True))
        check('replay_contract_record',contracts['replay']==meta['replay_contract'],'metadata')
        fixed_metadata(check,'controller_contract',contracts['controller'],dict(schema='s8-controller-v1',stage='S8',
            block_count=3,frames_per_block=24,history_count=20,query_count=4,splits=['test']*3,device='cpu',
            cpu_threads=8,seed=0,dtype='float32',runner_sha256=RUNNER_SHA,base_runner_sha256=BASE_RUNNER_SHA,
            checkpoint_sha256=CHECKPOINT_SHA,checkpoint_bytes=2994205002,commit=COMMIT,adapter_sha256=ADAPTER_SHA,
            timeout_seconds_per_block=900,max_rss_bytes=16*1024**3,depth_sent_to_model=False,query_updates_state=False))
        check('manifest_identity',manifest['schema']=='s8-inputs-v1' and manifest['dataset']=='rgbd_dataset_freiburg2_desk' and
            manifest['protocol_sha256']==sha(args.protocol) and manifest['runner_sha256']==RUNNER_SHA,'metadata')
        check('three_all_test_blocks',[b['block'] for b in manifest['blocks']]==[0,1,2] and
            [b['split'] for b in manifest['blocks']]==['test']*3,'metadata')
        check.exact('crop_intrinsics',K,meta['crop_intrinsics'])
        sequence=reader.json(args.runs/'sequence_metadata.json')
        fixed_metadata(check,'sequence',sequence,dict(schema='s8-sequence-metadata-v1',stage='S8',ok=True,phase='complete',
            arrays_verified=504,runner_sha256=RUNNER_SHA,base_runner_sha256=BASE_RUNNER_SHA,commit=COMMIT,
            depth_files_decoded_by_controller=False,s5_history_comparison_performed=False,
            vmem_complete_pipeline=False,video_generated=False,accuracy_evaluated=False,precision_semantics=PRECISION))
        fixed_metadata(check,'sequence/view_policy',sequence['view_policy'],dict(reset=False,
            update=[True]*20+[False]*4,img_mask=True,ray_mask=False,history_count=20,query_count=4,
            new_process_per_block=True,depth_sent_to_model=False))
        fixed_metadata(check,'sequence/resource_policy',sequence['resource_policy'],dict(
            timeout_seconds_per_block=900,observed_rss_limit_bytes=16*1024**3,rss_sample_interval_seconds=.5))
        expected_flags=[dict(frame=i,img_mask=[True],ray_mask=[False],update=[i<20],reset=[False]) for i in range(24)]
        check('sequence/expected_flags',sequence['expected_view_flags']==expected_flags,'metadata')
        check('sequence_contract_record',sequence['protocol_contract']==contracts['controller'],'metadata')
        check('sequence_before_replay',datetime.fromisoformat(freeze['frozen_utc'])<=datetime.fromisoformat(sequence['started_utc'])<=
            datetime.fromisoformat(sequence['completed_utc'])<=datetime.fromisoformat(meta['started_utc']),'metadata')
        for file,digest in (('frozen_inputs.json',sha(args.manifest)),('frozen_protocol.md',sha(args.protocol)),
            ('sequence_runner_snapshot.py',sequence['sequence_runner_sha256'])): reader.integrity(args.runs/file,digest)
        check('sequence_input_references',sequence['manifest_sha256']==sha(args.manifest) and
            sequence['protocol_sha256']==sha(args.protocol) and
            sequence['sequence_runner_sha256']==sha(ROOT/'scripts/run_s8_sequence.py'),'integrity')
        download=reader.json(args.runs/'checkpoint_download_manifest.json')
        fixed_metadata(check,'checkpoint_download',download,dict(status='verified_download',sha256=CHECKPOINT_SHA,actual_size=2994205002))
        rope=reader.json(args.runs/'signed_rope_check.json')
        fixed_metadata(check,'signed_rope',rope,dict(ok=True,commit=COMMIT,adapter_sha256=ADAPTER_SHA))
        reader.integrity(args.runs/'signed_rope_check.json',sequence['signed_rope_check_sha256'])
        snapshot=reader.json(args.runs/'source_snapshot/manifest.json')
        check('controller_source_manifest',snapshot==sequence['source_snapshot'],'metadata')
        for name,item in snapshot.items(): reader.integrity(safe_under(args.runs/'source_snapshot',name),item['sha256'])
        with tarfile.open(args.runs/'source_snapshot/upstream_source.tar') as archive:
            members={m.name:m for m in archive.getmembers() if m.isfile()}
            for name,digest in sequence['upstream_python_sha256'].items():
                check('pinned_upstream_archive/'+name,name in members and
                    hashlib.sha256(archive.extractfile(members[name]).read()).hexdigest()==digest,'integrity')
        check('three_controller_blocks',[b['block'] for b in sequence['blocks']]==[0,1,2],'metadata')
        time_keys=('started_utc','frozen_utc','preflight_completed_utc','completed_utc')
        sequence_times=[datetime.fromisoformat(sequence[k]) for k in time_keys]
        check('controller_freeze_preflight_time_order',all(a<=b for a,b in zip(sequence_times,sequence_times[1:])),'metadata')
        for i,entry in enumerate(sequence['blocks']):
            after=sequence['preflight_completed_utc'] if i==0 else sequence['blocks'][i-1]['completed_utc']
            check(f'controller/B{i}/sequential_processes',datetime.fromisoformat(after)<=datetime.fromisoformat(entry['started_utc']),'metadata')
        events=[strict_json(line) for line in reader.text(args.runs/'events.jsonl').splitlines() if line.strip()]
        check('controller_event_order',[e['event'] for e in events]==
            ['preflight_verified','block_starting','block_verified','block_starting','block_verified',
             'block_starting','block_verified','complete'] and
            [e['block'] for e in events if e['event']=='block_starting']==[0,1,2] and
            [e['block'] for e in events if e['event']=='block_verified']==[0,1,2],'metadata')
        event_times=[datetime.fromisoformat(e['utc']) for e in events]
        check('controller_event_times',all(a<=b for a,b in zip(event_times,event_times[1:])) and
            event_times[-1]<=datetime.fromisoformat(meta['started_utc']),'metadata')
        expected_cases={(b,s) for b in range(3) for s in (8,12)}
        check('six_cases',len(meta['cases'])==6 and {(c['block'],c['stride']) for c in meta['cases']}==expected_cases,'metadata')
        check('three_normalized_seals',set(meta['sealed_root_files'])=={f'block{b}_normalized_input.npz' for b in range(3)},'integrity')
        for name,digest in meta['sealed_root_files'].items(): reader.integrity(safe_under(args.results,name),digest)
        originals=reader.json(args.results/'records.json'); references={(r['block'],r['stride'],r['frame']):r for r in originals}
        check('24_record_domain',len(originals)==len(references)==24 and set(references)==
            {(b,s,q) for b in range(3) for s in (8,12) for q in range(20,24)},'metadata')
        # All following new raw-file content is behind the completed replay gate.
        text_tables={}
        for kind in ('rgb','depth'):
            path=safe_under(args.data,kind+'.txt'); reader.integrity(path,manifest['text_file_sha256'][kind+'.txt'])
            rows=[]
            for line in reader.text(path).splitlines():
                if not line.strip() or line.lstrip().startswith('#'): continue
                fields=line.split()
                if len(fields)!=2: raise ValueError('Invalid timestamp table row')
                rows.append((float(fields[0]),fields[1]))
            rows.sort(); check(kind+'/timestamp_table',bool(rows) and np.isfinite([r[0] for r in rows]).all() and
                len({r[0] for r in rows})==len(rows))
            text_tables[kind]=rows
        gt_path=safe_under(args.data,'groundtruth.txt'); reader.integrity(gt_path,manifest['text_file_sha256']['groundtruth.txt'])
        trajectory=np.loadtxt(gt_path,ndmin=2); trajectory=trajectory[np.argsort(trajectory[:,0])]
        check('GT_rows',trajectory.shape[1]==8 and len(trajectory)>0 and np.isfinite(trajectory).all() and
            np.all(np.diff(trajectory[:,0])>0) and np.all(np.linalg.norm(trajectory[:,4:],axis=1)>0))
        accepted,window_indices,paired_count=sampling_from_timestamps(text_tables['rgb'],text_tables['depth'],trajectory)
        check('sampling_first_middle_last',[b['accepted_window_index'] for b in manifest['blocks']]==window_indices)
        sampling_summary=dict(accepted_windows=len(accepted),paired_count=paired_count,selected_indices=window_indices)
        identities=[]; seen={kind:{key:set() for key in ('path','inode','sha','time')} for kind in ('rgb','depth')}
        normalized={}; measurements={}; rgbs={}; raws={}; model_identity=None
        for block in manifest['blocks']:
            b=block['block']; tag=f'B{b}'; window=accepted[block['accepted_window_index']]
            check(tag+'/24_frames',[f['frame'] for f in block['frames']]==list(range(24)))
            check(tag+'/sampling_bounds',block['nominal_start']==window['nominal_start'] and block['nominal_end']==window['nominal_end'])
            target_list=[]; mask_list=[]; gt_list=[]; gap_list=[]; rgb_list=[]
            for f,(mi,r,d),target_stamp,snap_error in zip(block['frames'],window['rows'],window['target_timestamps'],window['snap_errors']):
                q=f['frame']; qtag=tag+f'/raw{q}'
                check(qtag+'/sample_identity',f['match_index']==mi and f['rgb']==dict(timestamp=r[0],path=r[1]) and
                    f['depth']==dict(timestamp=d[0],path=d[1]) and f['target_timestamp']==target_stamp and f['snap_error_seconds']==snap_error)
                identity=dict(block=b,split='test',frame=q)
                for kind in ('rgb','depth'):
                    path=safe_under(args.data,f[kind]['path']); digest=f[kind+'_sha256']; reader.integrity(path,digest)
                    stat=path.stat(); facts=dict(path=str(path),inode=(stat.st_dev,stat.st_ino),sha=digest,time=f[kind]['timestamp'])
                    for key,value in facts.items():
                        check(qtag+'/'+kind+'/unique_'+key,value not in seen[kind][key],'integrity'); seen[kind][key].add(value)
                    identity[kind]=dict(path=str(path),relative_path=f[kind]['path'],timestamp=f[kind]['timestamp'],sha256=digest,bytes=stat.st_size)
                identities.append(identity)
                with Image.open(safe_under(args.data,f['rgb']['path'])) as image:
                    check(qtag+'/RGB_native_shape',image.size==(640,480))
                    rgb_list.append(np.asarray(image.convert('RGB').resize((299,224),Image.Resampling.LANCZOS).crop((37,0,261,224))))
                depth_path=safe_under(args.data,f['depth']['path'])
                with Image.open(depth_path) as image:
                    values=np.asarray(image); check(qtag+'/depth_native_shape',values.shape==(480,640) and values.dtype.kind in 'ui')
                target,mask=crop_measurement(depth_path); target_list.append(target); mask_list.append(mask)
                pose,gap=pose_at_closed(trajectory,f['rgb']['timestamp']); gt_list.append(pose); gap_list.append(gap)
                _,depth_gap=pose_at_closed(trajectory,f['depth']['timestamp'])
                check(qtag+'/both_GT_gaps',0<=gap<=.1 and 0<=depth_gap<=.1)
            stamps=[f['rgb']['timestamp'] for f in block['frames']]
            check(tag+'/cadence_record',block['actual_duration_seconds']==stamps[-1]-stamps[0] and
                block['rgb_intervals_seconds']==[y-x for x,y in zip(stamps,stamps[1:])] and
                block['rgb_minus_depth_seconds']==[f['rgb']['timestamp']-f['depth']['timestamp'] for f in block['frames']])
            rgbs[b]=rgb_list
            rebuilt=dict(targets=np.stack(target_list),masks=np.stack(mask_list),gt_poses=np.stack(gt_list),
                rgb_pose_bracket_gap_seconds=np.array(gap_list),rgb_timestamps=np.array(stamps),
                depth_timestamps=np.array([f['depth']['timestamp'] for f in block['frames']]))
            stored=reader.arrays(args.results/f'block{b}_measurements.npz')
            check(tag+'/measurement_keys',set(stored)==set(rebuilt))
            for key,value in rebuilt.items():
                (check.floating if key=='gt_poses' else check.exact)(tag+'/measurements/'+key,value,stored[key])
            geometry=reader.json(args.results/f'block{b}_measurement_geometry.json')
            check(tag+'/measurement_crop_geometry',geometry==[dict(original=[640,480],resized=[299,224],crop=[37,0,261,224])]*24)
            measurements[b]=rebuilt
            entry=sequence['blocks'][b]
            model,raw=verify_model(args.runs/f'block{b}',block,sequence,entry,reader,check,meta); raws[b]=raw
            identity={k:model[k] for k in ('commit','model_config','versions','runner_sha256','runtime_compatibility',
                'dtype','seed','cpu_threads','checkpoint','precision_semantics')}
            check(tag+'/same_model_identity',identity==meta['model_identity'] and (model_identity is None or model_identity==identity),'metadata')
            model_identity=identity
            depths,poses,norm=normalized_from_raw(raw); normalized[b]=(depths,poses,norm)
            frozen=reader.arrays(args.results/f'block{b}_normalized_input.npz')
            check.exact(tag+'/normalized_first_depth',depths[0],frozen['first_depth'])
            check.floating(tag+'/normalized_poses',poses,frozen['poses'])
            nrec=meta['normalizations'][str(b)]; check(tag+'/normalization_factor',norm==nrec['first_prediction_inverse_median'])
            good=mask_list[0]&np.isfinite(depths[0])&(depths[0]>0)&np.isfinite(target_list[0])&(target_list[0]>0)
            check(tag+'/calibration_eligible',int(good.sum())>=100)
            scale=float(np.median(target_list[0][good]/depths[0][good]))
            check(tag+'/first_frame_metric_scale',np.isfinite(scale) and scale>0 and scale==nrec['scoring_only_metric_scale'] and
                int(good.sum())==nrec['scoring_only_calibration_pixels'])
            scales.append(dict(block=b,normalization=norm,metric_scale=scale,pixels=int(good.sum()),
                max_rgb_GT_gap=max(gap_list),scale_product=norm*scale))
            np.savez_compressed(out/f'block{b}_measurements.npz',**rebuilt)
        check('controller_input_identities',identities==sequence['input_identities']==meta['input_identities'],'integrity')
        check('RGB_depth_distinct_files',not seen['rgb']['path']&seen['depth']['path'] and not seen['rgb']['inode']&seen['depth']['inode'],'integrity')
        # Every measurement hash must resolve to an authenticated raw PNG/text file.
        expected_measurement_paths={source_path(p):d for p,d in freeze['measurement_file_sha256'].items()}
        for block in manifest['blocks']:
            for f in block['frames']: expected_measurement_paths[safe_under(args.data,f['depth']['path'])]=f['depth_sha256']
        def archived_name(path):
            return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else 'external/'+hashlib.sha256(str(path.parent).encode()).hexdigest()[:16]+'/'+path.name
        check('measurement_hash_manifest',meta['measurement_source_sha256']=={archived_name(p):d for p,d in expected_measurement_paths.items()},'integrity')
        for entry in meta['cases']:
            b,stride=entry['block'],entry['stride']; label=f'block{b}_stride{stride}'
            check(label+'/directory',entry['directory']==label,'metadata'); folder=safe_under(args.results,label+'/prediction_only_selection.json').parent
            names={'observations.npz','predicted_poses.npz','prediction_only_selection.json'}
            names.update(f'A{a}_{suffix}' for a in range(2) for suffix in ('events.json','recorded_build_trace.json','recorded_map.npz','recorded_sources.json'))
            names.update(f'{arm}{suffix}' for arm in ARMS for suffix in ('.npz','_sources.json'))
            names.update(f'query{q}_{arm}_render.npz' for q in range(20,24) for arm in ARMS)
            check(label+'/complete_case_seal',set(entry['sealed_files'])==names,'integrity')
            for name,digest in entry['sealed_files'].items(): reader.integrity(safe_under(folder,name),digest)
            case=reader.json(folder/'prediction_only_selection.json')
            fixed_metadata(check,label,case,dict(block=b,split='test',stride=stride,width=160))
            depths,ind_poses,norm=normalized[b]; check(label+'/normalization',case['prediction_normalization']==norm)
            poses=reader.arrays(folder/'predicted_poses.npz')['poses']
            check.exact(label+'/sealed_poses',poses,reader.arrays(args.results/f'block{b}_normalized_input.npz')['poses'])
            check.floating(label+'/independent_poses',ind_poses,poses)
            obs=reader.arrays(folder/'observations.npz')
            rebuilt,filters=rebuilt_observations(depths,[raws[b][f'frame{i}_conf_self'][0] for i in range(20)],rgbs[b],ind_poses,stride)
            check(label+'/observation_keys',set(obs)==set(rebuilt))
            for key,value in rebuilt.items():
                (check.floating if key in ('points','normals','radii') else check.exact)(label+'/raw_observations/'+key,value,obs[key])
            check(label+'/independent_filters',filters==case['filters'])
            ids=obs['ids']; check(label+'/identity_uniqueness',len(ids)>0 and len({tuple(x) for x in ids.tolist()})==len(ids))
            maps={}; mappings={}
            for a in range(2):
                replayed,mapping,logic=reconstruct_paths(obs,reader.json(folder/f'A{a}_events.json'),a,check,label+f'/A{a}')
                trace=reader.json(folder/f'A{a}_recorded_build_trace.json'); stripped=[]
                for row in trace:
                    value={k:v for k,v in row.items() if k!='elapsed_seconds'}
                    value['position_threshold_normalized']=value.pop('position_threshold_m')
                    value['radius_normalized_quantiles']=value.pop('radius_m_quantiles'); stripped.append(value)
                check(label+f'/A{a}/logical_trace',stripped==logic)
                for p in range(2):
                    arm=f'A{a}P{p}'; maps[arm]=replayed[p]; mappings[arm]=mapping
                    stored=reader.arrays(folder/f'{arm}.npz'); check(label+'/'+arm+'/array_keys',set(stored)==set(maps[arm]))
                    for key,value in maps[arm].items(): check.exact(label+'/'+arm+'/'+key,value,stored[key])
                    check(label+'/'+arm+'/sources',mapping==reader.json(folder/f'{arm}_sources.json'))
                    check(label+'/'+arm+'/point_count',len(maps[arm]['points'])==case['maps'][arm]['points'])
                    check(label+'/'+arm+'/digest',map_hash(maps[arm],mapping)==case['maps'][arm]['digest'])
                    check(label+'/'+arm+'/counts_sources',maps[arm]['counts'].tolist()==[len(mapping[str(i)]) for i in range(len(mapping))] and
                        all(v==sorted(set(v)) and 0<=min(v)<=max(v)<20 for v in mapping.values()))
                    if a==p:
                        direct=reader.arrays(folder/f'A{a}_recorded_map.npz')
                        for key,value in maps[arm].items(): check.exact(label+'/'+arm+'/direct_'+key,value,direct[key])
                        check(label+'/'+arm+'/direct_sources',mapping==reader.json(folder/f'A{a}_recorded_sources.json'))
                    np.savez_compressed(out/f'{label}_{arm}.npz',**maps[arm]); save(out/f'{label}_{arm}_sources.json',mapping)
                for key in ('normals','radii','colors','counts'): check.exact(label+f'/A{a}/fixed_'+key,maps[f'A{a}P0'][key],maps[f'A{a}P1'][key])
                check(label+f'/A{a}/fixed_sources',mappings[f'A{a}P0']==mappings[f'A{a}P1'])
            measured=measurements[b]; gt=measured['gt_poses']; scale=scales[b]['metric_scale']
            world={arm:(gt[0]@np.c_[maps[arm]['points']*scale,np.ones(len(maps[arm]['points']))].T).T[:,:3] for arm in ARMS}
            check(label+'/query_order',[q['frame'] for q in case['queries']]==list(range(20,24)))
            for query in case['queries']:
                q=query['frame']; qtag=label+f'/Q{q}'; current=references[b,stride,q]
                z=reader.arrays(folder/f'query{q}_scoring.npz')
                target,valid,support=supports_from_raw(measured['targets'],measured['masks'],gt,q)
                for key,value in dict(target=target,valid=valid,support=support).items(): check.exact(qtag+'/'+key,value,z[key])
                check(qtag+'/positive_valid',int(valid.sum())>0)
                projected={arm:rasterize_centres(world[arm],gt[q]) for arm in ARMS}
                common=valid&np.logical_and.reduce([np.isfinite(v) for v in projected.values()])
                diagonal=valid&np.isfinite(projected['A0P0'])&np.isfinite(projected['A1P1'])
                check.exact(qtag+'/common_four',common,z['common_four']); check.exact(qtag+'/common_diagonal',diagonal,z['common_diagonal'])
                scores={}; geometry={}; decisions={}
                for arm in ARMS:
                    check.floating(qtag+'/'+arm+'/projection',projected[arm],z[arm])
                    own=valid&np.isfinite(projected[arm])
                    geometry[arm]=dict(common_four=statistics(projected[arm],target,common),
                        own=statistics(projected[arm],target,own),coverage=float(own.sum()/valid.sum()))
                    if arm in ('A0P0','A1P1'): geometry[arm]['common_diagonal']=statistics(projected[arm],target,diagonal)
                    render=reader.arrays(folder/f'query{q}_{arm}_render.npz'); indices=render['surfel_index_map']
                    check(qtag+'/'+arm+'/render_domain',indices.shape==(160,160) and indices.dtype.kind in 'iu' and
                        np.all((indices==-1)|((indices>=0)&(indices<len(maps[arm]['points'])))))
                    check(qtag+'/'+arm+'/render_shapes',render['cos_value_map'].shape==indices.shape==render['depth'].shape)
                    weights,counts=votes_from_render(render,mappings[arm]); trace=query['maps'][arm]['official_trace']
                    check(qtag+'/'+arm+'/weights',weights==trace['weights'])
                    check(qtag+'/'+arm+'/candidate_counts',counts==trace['candidate_counts'])
                    check(qtag+'/'+arm+'/rendered_coverage',float(np.mean(indices>=0))==trace['rendered_coverage'])
                    decisions[arm]={}; scores[arm]={}
                    for mode in READOUTS:
                        pool=[[i,1] for i in range(20)] if mode.startswith('all20') else counts
                        decision=independently_select(poses,poses[q],pool,not mode.endswith('no_nms'))
                        check(qtag+'/'+arm+'/'+mode+'/full_decision',decision==query['maps'][arm]['readouts'][mode])
                        chosen=decision['selected']; check(qtag+'/'+arm+'/'+mode+'/IDs',len(chosen)==len(set(chosen))==4 and all(0<=f<20 for f in chosen))
                        n=int((support[chosen].any(axis=0)&valid).sum())
                        scores[arm][mode]=dict(selected=chosen,supported_pixels=n,support=n/int(valid.sum()))
                        check(qtag+'/'+arm+'/'+mode+'/exact_integer_fraction',scores[arm][mode]==current['readouts'][arm][mode])
                        decisions[arm][mode]=decision
                    check(qtag+'/'+arm+'/official_ordered_IDs',trace['selected']==decisions[arm]['official']['selected'])
                for mode in ('all20_nms','all20_no_nms'):
                    check(qtag+'/'+mode+'/map_invariant',len({tuple(scores[a][mode]['selected']) for a in ARMS})==1)
                n=int((support.any(axis=0)&valid).sum())
                row=dict(block=b,split='test',stride=stride,frame=q,valid_pixels=int(valid.sum()),
                    common_four_pixels=int(common.sum()),common_diagonal_pixels=int(diagonal.sum()),
                    all20_supported_pixels=n,all20_support=n/int(valid.sum()),readouts=scores,geometry=geometry)
                check.nested(qtag+'/records',row,current); row['contrasts']=contrasts(scores); records.append(row)
                save(out/f'{label}_query{q}_decisions.json',decisions)
                np.savez_compressed(out/f'{label}_query{q}_scoring.npz',target=target,valid=valid,support=support,
                    common_four=common,common_diagonal=diagonal,**projected)
            print(json.dumps(dict(case=label,phase='independent_recomputed',utc=now())),flush=True)
        groups=[aggregate(records,'test',stride) for stride in (8,12)]
        by_block=[dict(aggregate([r for r in records if r['block']==b],'test',stride),block=b) for b in range(3) for stride in (8,12)]
        check('384_conditions_12_actual_queries',len(records)==24 and
            sum(sum(len(v) for v in r['readouts'].values()) for r in records)==384 and
            len({(r['block'],r['frame']) for r in records})==12)
        fixed_metadata(check,'recorded_counts',meta,dict(distinct_queries=12,primary_test_queries=12,
            query_conditions=24,readout_conditions=384,official_ordered_selection_checks=96))
        for path,digest in reader.before.items(): check('unchanged/'+path,sha(path)==digest,'integrity')
        save(out/'records.json',records); save(out/'aggregate.json',groups); save(out/'aggregate_by_block.json',by_block)
        save(out/'scales.json',scales); save(out/'sampling.json',sampling_summary)
        report.update(status='passed',groups=groups,groups_by_block=by_block,scales=scales,
            query_conditions=24,readout_conditions=384,unique_queries=12,main_unique_queries=12,
            maps_recomputed=24,association_paths_recomputed=12,render_vote_recomputations=96,
            decision_recomputations=384,measurement_depth_PNGs_reread=72,RGB_PNGs_reread=72,
            GT_rgb_poses_recomputed=72,GT_depth_timestamps_checked=72,
            accepted_observation_cases_rebuilt=6,normalized_blocks_recomputed=3,sampling=sampling_summary)
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report.update(completed_utc=now(),checks_count=len(check.items),
        checks_by_kind=dict(Counter(c['kind'] for c in check.items)),original_sha256=reader.before)
    save(out/'verification.json',report)
    print(json.dumps({k:report[k] for k in ('status','checks_count','checks_by_kind','completed_utc')},ensure_ascii=False))
    if report['status']!='passed': print(report['traceback']); return 1
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','protocol','freeze','runs','data','results','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    # Check ONLY completion metadata first; a failed/running/missing run cannot
    # trigger manifest, PNG, GT, prediction, or scoring reads, nor create output.
    try: meta=strict_json((args.results/'run_metadata.json').read_text())
    except Exception as exc: parser.error('Cannot verify completion: '+str(exc))
    if meta.get('status')!='completed' or meta.get('phase')!='complete':
        parser.error('S8 replay is not completed; new data and scores remain unread')
    if args.output.exists() or args.output.is_symlink(): parser.error('Preserve prior attempts; use a fresh --output')
    for name in ('manifest','protocol','freeze','runs','data','results'): setattr(args,name,getattr(args,name).resolve(strict=True))
    args.output=args.output.absolute()
    return audit(args,meta)


if __name__=='__main__': sys.exit(main())
