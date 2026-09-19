#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from experiment_io import begin_run,complete_run,write_json,sha256
from rgbd_dataset import dataset_index,frame_dict
from rgbd_metrics import depth_consistency,project_points

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    p.add_argument('--output',type=Path,default=ROOT/'results/S2_rgbd_qa')
    args=p.parse_args()
    meta=begin_run(args.output,'docs/S2_S3_PROTOCOL.md',dict(sequence='freiburg1_xyz',qa_frames=24))
    matches,trajectory,manifest=dataset_index(args.data)
    write_json(args.output/'selection_manifest.json',manifest)
    frames=[frame_dict(args.data,matches[i],trajectory) for i in manifest['qa_indices']]
    qa=[]
    for i,f in enumerate(frames):
        uv,z,_=project_points(f['points_world'],f['c2w_optical'],f['intrinsics'])
        uverror=float(np.max(np.abs(uv-f['pixels_uv'])))
        zerror=float(np.max(np.abs(z-f['points_camera'][:,2])))
        if uverror>1e-6 or zerror>1e-9: raise AssertionError('Coordinate roundtrip failure')
        valid=f['depth']>0
        row=dict(sample=i,timestamp=f['timestamp'],rgb_timestamp=f['rgb_timestamp'],
                 rgb_path=f['rgb_path'],depth_path=f['depth_path'],rgb_sha256=sha256(args.data/f['rgb_path']),
                 depth_sha256=sha256(args.data/f['depth_path']),offset_seconds=f['offset_seconds'],
                 pose_gap_seconds=f['pose_gap_seconds'],valid_depth_fraction=float(valid.mean()),
                 valid_depth_m_quantiles=np.quantile(f['depth'][valid],[0,.1,.5,.9,1]).tolist(),
                 roundtrip_max_pixel_error=uverror,roundtrip_max_depth_error_m=zerror,
                 sampled_points=len(f['points_world']))
        if i:
            projected=depth_consistency(frames[i-1]['points_world'],f,stride=4)
            mask=projected['common_mask']
            residual=np.abs(projected['pred_depth'][mask]-projected['target_depth'][mask])
            row['previous_sample_projection']=dict(n=int(mask.sum()),median_abs_difference_mm=float(np.median(residual)*1000) if len(residual) else None)
        qa.append(row)
    write_json(args.output/'frame_qa.json',qa)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(4,6,figsize=(15,9))
    for ax,f in zip(axs.ravel(),frames):
        ax.imshow(f['rgb']);ax.set_title(f"t = {f['timestamp']-frames[0]['timestamp']:.2f} s",fontsize=9);ax.axis('off')
    fig.suptitle('TUM fr1_xyz: 24 timestamp-matched observations (real RGB)',fontsize=15)
    fig.tight_layout();fig.savefig(args.output/'rgb_contact_sheet.png',dpi=140);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    traj=trajectory.translations
    axs[0].plot(traj[:,0],traj[:,1],lw=1,c='#777777')
    for b,indices in enumerate(manifest['blocks']):
        poses=np.array([trajectory.pose_at(matches[i].depth.timestamp)[:3,3] for i in indices])
        axs[0].scatter(poses[:20,0],poses[:20,1],s=12,label=f'block {b}: history')
        axs[0].scatter(poses[20:,0],poses[20:,1],s=35,marker='x',label=f'block {b}: held out')
    axs[0].set(xlabel='world x (m)',ylabel='world y (m)',title='Mocap camera path (XY projection)')
    axs[0].axis('equal');axs[0].legend(fontsize=7)
    axs[1].plot([r['timestamp']-qa[0]['timestamp'] for r in qa],[r['valid_depth_fraction']*100 for r in qa],marker='o')
    axs[1].set(xlabel='time (s)',ylabel='valid depth (%)',ylim=(0,100),title='Measured depth availability')
    fig.tight_layout();fig.savefig(args.output/'trajectory_and_depth.png',dpi=160);plt.close(fig)
    complete_run(args.output,meta,qa_frames=len(qa),coordinate_checks_passed=True,
                 dataset_archive_manifest_sha256=sha256(args.data.parent/'download_manifest.json'))
    print(args.output)

if __name__=='__main__': main()
