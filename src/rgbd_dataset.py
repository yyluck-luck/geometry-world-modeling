"""Fixed timestamp selections and a common frame dictionary for experiments."""
from dataclasses import asdict
from pathlib import Path
import numpy as np
from tum_rgbd import read_timestamp_file,read_trajectory,associate_rgb_depth,load_sparse_frame


def dataset_index(root):
    root=Path(root)
    rgb=read_timestamp_file(root/'rgb.txt');depth=read_timestamp_file(root/'depth.txt')
    trajectory=read_trajectory(root/'groundtruth.txt')
    matches=associate_rgb_depth(rgb,depth)
    valid,rejected=[],[]
    for match in sorted(matches,key=lambda m:m.depth.timestamp):
        try: trajectory.interpolate(match.depth.timestamp,max_gap_seconds=.1)
        except ValueError as error:
            rejected.append(dict(match=asdict(match),reason=str(error)))
        else: valid.append(match)
    if len(valid)<72: raise ValueError('Need at least 72 pose-supported RGB-D observations')
    qa_indices=np.linspace(0,len(valid)-1,24,dtype=int).tolist()
    blocks=[]
    stamps=np.asarray([m.depth.timestamp for m in valid])
    boundaries=np.linspace(stamps[0],stamps[-1],4)
    for b in range(3):
        group=np.flatnonzero((stamps>=boundaries[b])&((stamps<boundaries[b+1]) if b<2 else (stamps<=boundaries[b+1])))
        if len(group)<24: raise ValueError('A fixed duration block has fewer than 24 valid observations')
        blocks.append(group[np.linspace(0,len(group)-1,24,dtype=int)].tolist())
    manifest=dict(rgb_frames=len(rgb),depth_frames=len(depth),matched_frames=len(matches),
                  valid_pose_matches=len(valid),rejected_pose_matches=rejected,
                  qa_indices=qa_indices,blocks=blocks,block_time_boundaries=boundaries.tolist(),matches=[asdict(m) for m in valid],
                  intrinsics=[525.,525.,319.5,239.5],depth_scale_divisor=5000,
                  max_rgb_depth_difference_seconds=.02,max_pose_gap_seconds=.1,
                  split='block0 development; blocks1,2 fixed test; same environment')
    return valid,trajectory,manifest


def frame_dict(root,match,trajectory,stride=16):
    f=load_sparse_frame(root,match,trajectory,stride=stride,max_pose_gap_seconds=.1)
    return dict(depth=f.depth_m,rgb=f.rgb_image,c2w_optical=f.c2w_optical,
                intrinsics=f.intrinsics.K,timestamp=f.match.depth_timestamp,
                rgb_timestamp=f.match.rgb_timestamp,offset_seconds=f.match.offset_seconds,
                rgb_path=f.match.rgb.path,depth_path=f.match.depth.path,
                pose_gap_seconds=f.pose.gap_seconds,pixels_uv=f.pixels_uv,
                points_camera=f.points_camera,points_world=f.points_world)
