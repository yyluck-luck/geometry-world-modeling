#!/usr/bin/env python3
"""S5: fixed 3 x 24 RGB sequences; depth scale from each block's first image only."""
import argparse
import csv
from datetime import datetime,timezone
from importlib.metadata import version
import json
from pathlib import Path
import sys
import traceback
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from learned_pair_metrics import measured_target,first_frame_scale,depth_metrics,relative_pose_metrics
from tum_rgbd import read_trajectory
from PIL import Image
from evaluate_cut3r_pair import load_run,sha,compatibility_paths

METRICS=('mae_mm','median_abs_mm','p90_abs_mm','signed_mean_mm','within_30mm','abs_rel','prediction_coverage')
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False))


def aggregate(rows):
    return dict(frames=len(rows),blocks=sorted({r['block'] for r in rows}),
        mean_per_frame={k:float(np.mean([r['calibrated'][k] for r in rows])) for k in METRICS},
        mean_relative_rotation_error_deg=float(np.mean([r['relative_pose']['rotation_error_deg'] for r in rows])),
        mean_relative_translation_vector_error_mm=float(np.mean([r['relative_pose']['translation_vector_error_mm'] for r in rows])))


def main(args):
    if args.output.exists():raise ValueError('Preserve previous results: use a fresh output')
    args.output.mkdir(parents=True)
    report=dict(status='running',started_utc=utc(),protocol='docs/S5_SEQUENCE_PROTOCOL.md',
        evidence_level='one-environment causal learned RGB geometry with one depth scale per block',
        environment=dict(python=sys.version,packages={n:version(n) for n in ('numpy','scipy','Pillow')}),blocks=[])
    write(args.output/'summary.json',report)
    try:
        frozen_path=ROOT/'data/cut3r/S5_inputs.json';frozen=read(frozen_path)
        frozen_sha=sha(frozen_path)
        if frozen_sha!='7ffa1467f5640bee2013a1ed1d30313be14da339ab28f7c364cfc2790f16f126':raise ValueError('Frozen 72-image manifest changed')
        sequence=read(args.runs/'sequence_metadata.json')
        if (sequence.get('ok') is not True or sequence.get('phase')!='complete' or
            [b['block'] for b in sequence['blocks']]!=[0,1,2] or not all(b.get('ok') is True and b.get('returncode')==0 for b in sequence['blocks'])):
            raise ValueError('Sequence controller has not completed all three blocks within the resource policy')
        if sequence['manifest_sha256']!=frozen_sha:raise ValueError('Sequence controller used different inputs')
        if sha(args.runs/'sequence_runner_snapshot.py')!=sequence['sequence_runner_sha256']:raise ValueError('Sequence runner snapshot hash mismatch')
        if any(b['process_peak_rss_bytes']>16*1024**3 for b in sequence['blocks']):raise ValueError('Observed process peak exceeded frozen 16 GiB soft budget')
        report['sequence_metadata_sha256']=sha(args.runs/'sequence_metadata.json')
        report['precision_semantics']=sequence['precision_semantics']
        if sha(ROOT/'docs/S5_SEQUENCE_PROTOCOL.md')!=frozen['protocol_sha256']:raise ValueError('Frozen protocol changed')
        if sha(ROOT/'results/S3_rgbd_memory/selection_manifest.json')!=frozen['source_selection_sha256']:raise ValueError('S3 selection changed')
        report['input_manifest_sha256']=sha(frozen_path)
        trajectory=read_trajectory(args.data/'groundtruth.txt')
        records=[];saved={};sources=[Path(__file__),ROOT/'scripts/evaluate_cut3r_pair.py',ROOT/'src/learned_pair_metrics.py',
            ROOT/'src/tum_rgbd.py',ROOT/'docs/S5_SEQUENCE_PROTOCOL.md',ROOT/'docs/S5_PRECISION_CLARIFICATION.md',frozen_path,ROOT/'data/cut3r/download_manifest.json',
            ROOT/'results/S3_rgbd_memory/selection_manifest.json',args.data/'groundtruth.txt']
        sources.extend([args.runs/'sequence_metadata.json',args.runs/'sequence_runner_snapshot.py'])
        reference=None
        for block in frozen['blocks']:
            b=block['block'];out=args.runs/f'block{b}'
            m,a,diagnostics=load_run(out,'cpu',{'images':[{'sha256':f['rgb_sha256']} for f in block['frames']]},views=24)
            if m['runner_sha256']!=sequence['runner_sha256'] or m['predictions_sha256']!=sequence['blocks'][b]['predictions_sha256']:
                raise ValueError('Block and sequence provenance disagree')
            identity={k:m[k] for k in ('commit','model_config','versions','runner_sha256','runtime_compatibility','dtype','seed','cpu_threads')}
            if reference is not None and identity!=reference:raise ValueError('Blocks have different model/runtime identity')
            reference=identity
            if len(block['frames'])!=24:raise ValueError('Expected 24 frames in each block')
            target=[];mask=[];truth=[];provenance=[]
            for f in block['frames']:
                rp=args.data/f['rgb']['path'];dp=args.data/f['depth']['path']
                if sha(rp)!=f['rgb_sha256'] or sha(dp)!=f['depth_sha256']:raise ValueError('Frozen input hash changed')
                d,v,g=measured_target(np.asarray(Image.open(dp),dtype=np.float64)/5000)
                target.append(d);mask.append(v)
                pose=trajectory.interpolate(f['rgb']['timestamp'],max_gap_seconds=.1);truth.append(pose.c2w)
                provenance.append(dict(frame=f['frame'],rgb_pose_gap_seconds=pose.gap_seconds,rgb_c2w=pose.c2w.tolist(),crop=g))
            pred=[a[f'frame{i}_pts3d_in_self_view'][0,:,:,2].astype(float) for i in range(24)]
            scale,n=first_frame_scale(pred[0],target[0],mask[0])
            br=[]
            for i in range(24):
                frame=block['frames'][i]
                role='calibration_description' if i==0 else ('primary_test' if b in (1,2) and i>=20 else ('development_tail' if b==0 and i>=20 else 'sequence_description'))
                r=dict(block=b,split=block['split'],frame=i,role=role,match_index=frame['match_index'],
                    rgb_timestamp=frame['rgb']['timestamp'],seconds_from_first=frame['rgb']['timestamp']-block['frames'][0]['rgb']['timestamp'],
                    rgb_minus_depth_seconds=frame['rgb']['timestamp']-frame['depth']['timestamp'],
                    calibrated=depth_metrics(pred[i],target[i],mask[i],scale),unscaled_unit_assumption=depth_metrics(pred[i],target[i],mask[i],1),
                    relative_pose=relative_pose_metrics(a['frame0_camera_c2w'][0],a[f'frame{i}_camera_c2w'][0],truth[0],truth[i],scale))
                br.append(r);records.append(r)
            saved.update({f'block{b}_target':np.stack(target),f'block{b}_valid':np.stack(mask),f'block{b}_depth_scaled':np.stack(pred)*scale})
            report['blocks'].append(dict(block=b,scale=scale,calibration_pixels=n,run_metadata_sha256=sha(out/'run_metadata.json'),
                predictions_sha256=m['predictions_sha256'],inference_seconds=m['inference_seconds'],peak_process_rss_bytes=m['peak_process_rss_bytes'],
                input_device_values_preserved=m['input_device_staging']['all_values_preserved'],rgb_pose_provenance=provenance,
                diagnostic_pointmap_pose_consistency=diagnostics,tail_summary=aggregate(br[20:]),noncalibration_summary=aggregate(br[1:])))
            sources.extend([out/'run_metadata.json',out/'runner_snapshot.py'])
        if len(records)!=72 or [b['block'] for b in report['blocks']]!=[0,1,2]:raise ValueError('Incomplete frozen sequence set')
        report['runtime_identity']=reference
        report['primary_test']=aggregate([r for r in records if r['role']=='primary_test'])
        report['development_tail']=aggregate([r for r in records if r['role']=='development_tail'])
        report['all_noncalibration_descriptive']=aggregate([r for r in records if r['frame']>0])
        report['limitations']=['Three temporal blocks, one environment, eight primary test images.',
            'Three measured calibration depths, one per block; not uncalibrated metric RGB-only estimation.',
            'Earlier evaluation RGB may update causal state; no measured evaluation depth enters inference.',
            'No VMem cleaning/retrieval/video generation and no independent-scene or significance claim.',
            'Shared scale between separately predicted pointmaps and poses is an explicit diagnostic assumption.']
        write(args.output/'records.json',records)
        fields=['block','split','frame','role','seconds_from_first',*METRICS,'rotation_error_deg','translation_vector_error_mm']
        with (args.output/'per_frame.csv').open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
            for r in records:w.writerow({**{k:r[k] for k in fields[:5]},**{k:r['calibrated'][k] for k in METRICS},**{k:r['relative_pose'][k] for k in fields[-2:]}})
        np.savez_compressed(args.output/'measurement_comparison.npz',**saved)
        report['measurement_comparison_sha256']=sha(args.output/'measurement_comparison.npz')
        sources.extend(compatibility_paths(m))
        report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in sources}
        with zipfile.ZipFile(args.output/'evaluation_source.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sources:z.write(p,str(p.relative_to(ROOT)))
        report['status']='completed'
    except Exception:
        report['status']='failed';report['traceback']=traceback.format_exc();raise
    finally:
        report['completed_utc']=utc();write(args.output/'summary.json',report)
    print(json.dumps(dict(status=report['status'],primary_test=report['primary_test'],completed_utc=report['completed_utc']),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,default=ROOT/'results/CUT3R_S5_cpu')
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    p.add_argument('--output',type=Path,default=ROOT/'results/S5_cut3r_sequence')
    args=p.parse_args()
    args.runs=args.runs.resolve();args.data=args.data.resolve();args.output=args.output.resolve()
    main(args)
