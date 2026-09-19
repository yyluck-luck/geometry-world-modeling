#!/usr/bin/env python3
"""S4 frozen, measurement-calibrated diagnostic of a completed two-image run."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import traceback
import zipfile

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rgbd_dataset import dataset_index, frame_dict
from learned_pair_metrics import measured_target, first_frame_scale, depth_metrics, relative_pose_metrics, validate_pose, resize_crop


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text())
def write(path,data): Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False))


def compatibility_paths(metadata):
    """Locate archived evidence here; historical absolute paths stay in metadata."""
    return (ROOT/'scripts/cut3r_rope_compat.py',ROOT/'results/CUT3R_signed_rope_compat/check.json')


def load_run(directory, expected_device, inputs, views=2):
    metadata=read(directory/'run_metadata.json')
    compatibility=metadata.get('runtime_compatibility',{})
    if (metadata.get('upstream_source_files_unmodified') is not True or
        metadata.get('upstream_execution_unmodified') is not False or
        compatibility.get('signed_rope_adapter') is not True or
        compatibility.get('blocking_input_staging') is not True):
        raise ValueError('Requires the documented signed-RoPE and blocking-transfer execution adapter')
    for path,path_key,hash_key in zip(compatibility_paths(metadata),('adapter_path','validation_path'),('adapter_sha256','validation_sha256')):
        if sha(path)!=compatibility[hash_key]:
            raise ValueError(f'Runtime compatibility evidence changed: {path_key}')
    if compatibility['adapter_sha256']!='6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e':
        raise ValueError('Unexpected signed-RoPE implementation')
    if sha(directory/'runner_snapshot.py')!=metadata['runner_sha256']:
        raise ValueError('Runner snapshot hash mismatch')
    staging=metadata.get('input_device_staging',{})
    expected_fields={(i,k) for i in range(views) for k in ('img','ray_map','camera_pose','img_mask','ray_mask','update','reset')}
    checks=staging.get('checks',[])
    if (staging.get('all_values_preserved') is not True or len(checks)!=7*views or
        {(v['view'],v['field']) for v in checks}!=expected_fields or
        not all(v.get('values_preserved') is True for v in checks)):
        raise ValueError('Actual device input values were not verified')
    if metadata.get('commit')!='8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf' or metadata.get('dtype')!='float32':
        raise ValueError('Requires the pinned independent CUT3R revision and FP32')
    if metadata.get('tracked_changes') or metadata.get('actual_patch_image_size')!=[224,224] or metadata.get('checkpoint_all_keys_matched') is not True:
        raise ValueError('Architecture, source changes or checkpoint loading differs from protocol')
    if metadata.get('input_tensor_shapes')!=[[1,3,224,224]]*views:
        raise ValueError('Input tensor shape differs from protocol')
    download=read(ROOT/'data/cut3r/download_manifest.json')
    if download.get('status')!='verified_download' or download.get('actual_size')!=2994205002:
        raise ValueError('Official checkpoint download is not verified')
    if metadata['checkpoint']['sha256']!=download.get('sha256') or metadata['checkpoint']['bytes']!=download['actual_size']:
        raise ValueError('Loaded checkpoint differs from verified download')
    if metadata.get('phase')!='complete' or not metadata.get('inference_ok') or metadata['device']!=expected_device:
        raise ValueError(f'{expected_device} has no completed valid inference')
    if expected_device=='cpu' and metadata.get('ok') is not True:
        raise ValueError('Primary CPU inference did not pass')
    if metadata.get('views')!=views or metadata.get('actual_head_type')!='linear':
        raise ValueError('Unexpected number of views or non-linear head')
    if metadata['model_config']['downstream_head_class']!='dust3r.heads.linear_head.LinearPts3dPose':
        raise ValueError('Unexpected concrete downstream head; re-audit semantics before evaluation')
    if [r['sha256'] for r in metadata['images']] != [r['sha256'] for r in inputs['images']]:
        raise ValueError('Inference image order does not match frozen inputs')
    pred_path=directory/'predictions.npz'
    if sha(pred_path)!=metadata['predictions_sha256']:
        raise ValueError('Predictions hash mismatch')
    with np.load(pred_path,allow_pickle=False) as arrays:
        result={key:arrays[key] for key in arrays.files}
    if not all(np.all(np.isfinite(value)) for value in result.values()):
        raise ValueError('Actual prediction arrays contain nonfinite values')
    identities=[]
    for i in range(views):
        a=result[f'frame{i}_pts3d_in_self_view']
        b=result[f'frame{i}_pts3d_in_other_view']
        if a.shape!=(1,224,224,3) or b.shape!=a.shape:
            raise ValueError('Unexpected pointmap shape')
        pose=validate_pose(result[f'frame{i}_camera_c2w'][0])
        transformed=a[0].astype(float)@pose[:3,:3].T+pose[:3,3]
        diff=np.abs(transformed-b[0])
        identities.append(dict(frame=i,algebraic_identity_required=False,
                               explanation='Self pointmap, pose and other pointmap are separately predicted by LinearPts3dPose.',
                               max_abs_difference_model_units=float(diff.max()),
                               mean_abs_difference_model_units=float(diff.mean()),
                               positive_self_z_fraction=float(np.mean(a[0,:,:,2]>0))))
    return metadata,result,identities


def main():
    started=utc()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpu',type=Path,default=ROOT/'results/CUT3R_cpu_2frames')
    p.add_argument('--mps',type=Path,help='Optional completed MPS result, including finite inference with allclose failure')
    p.add_argument('--output',type=Path,default=ROOT/'results/S4_cut3r_pair')
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    args=p.parse_args()
    args.cpu=args.cpu.resolve()
    if args.mps:args.mps=args.mps.resolve()
    args.data=args.data.resolve()
    args.output=args.output.resolve()
    if args.output.exists(): raise ValueError('Use a fresh output directory')
    inputs=read(ROOT/'data/cut3r/inference_inputs.json')
    metadata,arrays,identities=load_run(args.cpu,'cpu',inputs)
    matches,trajectory,selection=dataset_index(args.data)
    frames=[frame_dict(args.data,matches[i],trajectory) for i in inputs['qa_indices']]
    target,mask,transforms=[],[],[]
    poses=[]
    provenance=[]
    for i,(frame,idx) in enumerate(zip(frames,inputs['qa_indices'])):
        match=matches[idx]
        if sha(args.data/match.rgb.path)!=inputs['images'][i]['sha256']:
            raise ValueError('Actual RGB does not match frozen input')
        d,v,g=measured_target(frame['depth'])
        target.append(d);mask.append(v);transforms.append(g)
        pose=trajectory.interpolate(match.rgb.timestamp,max_gap_seconds=.1)
        poses.append(pose.c2w)
        provenance.append(dict(index=idx,rgb=match.rgb.path,depth=match.depth.path,
                               rgb_sha256=sha(args.data/match.rgb.path),depth_sha256=sha(args.data/match.depth.path),
                               rgb_timestamp=match.rgb.timestamp,depth_timestamp=match.depth.timestamp,
                               rgb_minus_depth_seconds=match.rgb.timestamp-match.depth.timestamp,
                               rgb_pose_bracket_gap_seconds=pose.gap_seconds,rgb_c2w=pose.c2w.tolist()))
    pred=[arrays[f'frame{i}_pts3d_in_self_view'][0,:,:,2].astype(float) for i in range(2)]
    scale,n=first_frame_scale(pred[0],target[0],mask[0])
    report=dict(started_utc=started,protocol='docs/S4_TWO_FRAME_PROTOCOL.md',
                pre_run_amendment='docs/S4_PRE_RUN_AMENDMENT.md',status='running',
                evaluation_environment=dict(python=sys.version,packages={name:version(name) for name in ('numpy','scipy','Pillow')}),
                evidence_level='two-frame learned geometry with first-frame measured scale',
                limitations=['One calibrated image and one held-out image, one environment, not a benchmark.',
                             'Only RGB enters model; first depth estimates shared scale, second depth is scoring only.',
                             'Measured depth, camera calibration and time associations retain errors.',
                             'Independent 224 intermediate CUT3R, not VMem fork or full video generation.'],
                scale_fit=dict(source='CPU frame0 only',scale=scale,pixels=n,statistic='median(measured_Z/predicted_Z)'),
                dataset_input_sha256={name:sha(args.data/name) for name in ('rgb.txt','depth.txt','groundtruth.txt')},
                frames=provenance,transforms=transforms,runs={})
    device_outputs=[('cpu',metadata,arrays,identities)]
    if args.mps:
        m,a,identity=load_run(args.mps,'mps',inputs)
        for key in ('commit','model_config','versions','runner_sha256','dtype','seed','runtime_compatibility'):
            if m[key]!=metadata[key]: raise ValueError(f'CPU/MPS provenance differs: {key}')
        if m['checkpoint']['sha256']!=metadata['checkpoint']['sha256']:
            raise ValueError('CPU/MPS checkpoint differs')
        if set(a)!=set(arrays): raise ValueError('CPU/MPS output keys differ')
        comparison=dict(atol=1e-3,rtol=1e-3,reference_cpu_predictions_sha256=metadata['predictions_sha256'],per_array={})
        for key in arrays:
            if arrays[key].shape!=a[key].shape or arrays[key].dtype!=a[key].dtype:
                raise ValueError('CPU/MPS raw shape or dtype differs')
            diff=np.abs(a[key].astype(float)-arrays[key].astype(float))
            comparison['per_array'][key]=dict(max_absolute_difference=float(diff.max()),mean_absolute_difference=float(diff.mean()),
                                              allclose=bool(np.allclose(a[key],arrays[key],atol=1e-3,rtol=1e-3)))
        comparison['all_arrays_close']=all(v['allclose'] for v in comparison['per_array'].values())
        report['independently_recomputed_cpu_mps_comparison']=comparison
        device_outputs.append(('mps',m,a,identity))
    args.output.mkdir(parents=True)
    try:
        for device,m,a,identity in device_outputs:
            depths=[a[f'frame{i}_pts3d_in_self_view'][0,:,:,2].astype(float) for i in range(2)]
            scored=[dict(frame=i,role=('calibration description','held-out measurement')[i],
                         calibrated=depth_metrics(depths[i],target[i],mask[i],scale),
                         unscaled_unit_assumption=depth_metrics(depths[i],target[i],mask[i],1)) for i in range(2)]
            report['runs'][device]=dict(inference_ok=m['inference_ok'],run_ok=m['ok'],
                runtime_compatibility=m['runtime_compatibility'],input_device_staging=m['input_device_staging'],
                checkpoint_sha256=m['checkpoint']['sha256'],predictions_sha256=m['predictions_sha256'],
                inference_seconds=m['inference_seconds'],pointmap_pose_consistency_diagnostic=identity,depth=scored,
                source_cpu_comparison_all_arrays_close=m.get('cpu_comparison_all_arrays_close'),
                relative_pose=relative_pose_metrics(a['frame0_camera_c2w'][0],a['frame1_camera_c2w'][0],poses[0],poses[1],scale))
        source_paths=[Path(__file__),ROOT/'src/learned_pair_metrics.py',ROOT/'src/tum_rgbd.py',ROOT/'src/rgbd_dataset.py',
                      ROOT/'docs/S4_TWO_FRAME_PROTOCOL.md',ROOT/'docs/S4_PRE_RUN_AMENDMENT.md',
                      ROOT/'data/cut3r/inference_inputs.json',ROOT/'data/cut3r/download_manifest.json',args.cpu/'run_metadata.json']
        if args.mps:source_paths.append(args.mps/'run_metadata.json')
        source_paths.extend([args.cpu/'runner_snapshot.py',*compatibility_paths(metadata),
                             ROOT/'docs/S4_RUNTIME_AMENDMENT.md',ROOT/'docs/CUT3R_ROPE_ADAPTER_AUDIT.md',
                             ROOT/'results/CUT3R_mps_transfer_compat/check.json'])
        if args.mps:source_paths.append(args.mps/'runner_snapshot.py')
        source_paths.extend(args.data/name for name in ('rgb.txt','depth.txt','groundtruth.txt'))
        report['source_sha256']={str(f.relative_to(ROOT)):sha(f) for f in source_paths}
        with zipfile.ZipFile(args.output/'evaluation_source.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in source_paths:z.write(f,str(f.relative_to(ROOT)))
        np.savez_compressed(args.output/'measurement_comparison.npz',
            target0=target[0],target1=target[1],valid0=mask[0],valid1=mask[1],
            **{f'{device}_depth{i}_scaled':a[f'frame{i}_pts3d_in_self_view'][0,:,:,2].astype(float)*scale for device,m,a,identity in device_outputs for i in range(2)})
        report['status']='completed'
    except Exception as error:
        report['status']='failed';report['error']=repr(error)
        raise
    finally:
        report['completed_utc']=utc();write(args.output/'summary.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    failure_parser=argparse.ArgumentParser(add_help=False)
    failure_parser.add_argument('--output',type=Path,default=ROOT/'results/S4_cut3r_pair')
    failure_args,_=failure_parser.parse_known_args()
    already_existed=failure_args.output.exists()
    attempted=utc()
    try:
        main()
    except Exception:
        if not already_existed:
            failure_args.output.mkdir(parents=True,exist_ok=True)
            write(failure_args.output/'failure.json',dict(status='failed',started_utc=attempted,completed_utc=utc(),
                  evaluator_sha256=sha(__file__),traceback=traceback.format_exc()))
        raise
