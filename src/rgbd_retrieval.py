"""Package measured RGB-D memory for the unchanged VMem context selector."""
from types import SimpleNamespace as NS
import numpy as np
import torch
from retrieval_diagnostic import ObservedKernel


def optical_to_vmem(pose):
    return np.asarray(pose)@np.diag([1.,-1.,-1.,1.])


def initial_nms_threshold(optical_poses,weight=.1):
    obj=ObservedKernel()
    poses=[optical_to_vmem(p) for p in optical_poses[:5]]
    values=[float(obj.geodesic_distance(torch.tensor(poses[i]),torch.tensor(poses[j]),weight))
            for i in range(len(poses)) for j in range(i+1,len(poses))]
    values.sort()
    return values[int(len(values)*.5)] if values else 1.


def make_selector(memory,optical_poses,width=160,height=120,threshold=None):
    obj=ObservedKernel()
    obj.config=NS(model=NS(context_num_frames=4,translation_distance_weight=.1),
                  surfel=NS(width=width,height=height),inference=NS(visualize=False))
    obj.device,obj.dtype='cpu',torch.float64
    obj.use_non_maximum_suppression=True
    obj.initial_threshold=initial_nms_threshold(optical_poses) if threshold is None else threshold
    obj.c2ws=[optical_to_vmem(p) for p in optical_poses]
    n=len(obj.c2ws)
    obj.pil_frames=[None]*n
    obj.latents=[np.asarray([i],dtype=np.float64) for i in range(n)]
    obj.encoder_embeddings=[np.asarray([i+.25],dtype=np.float64) for i in range(n)]
    scale=width/640.
    obj.Ks=[np.array([[525*scale,0,319.5*scale],[0,525*scale,239.5*scale],[0,0,1.]]) for _ in range(n)]
    obj.surfel_Ks=[525*scale]*n
    obj.surfels=memory.surfels
    obj.surfel_to_timestep=memory.mapping
    return obj


def select(obj,optical_query):
    query=optical_to_vmem(optical_query)
    output=obj.get_context_info(torch.tensor(query[None],dtype=torch.float64))
    selected=[int(x) for x in output['context_time_indices']]
    candidates=[int(k) for k,n in obj.last_counts if n>0]
    ranked=sorted(obj.last_weights,key=lambda x:x[1],reverse=True)
    distances=[float(obj.geodesic_distance(torch.tensor(query),torch.tensor(obj.c2ws[k]),.1)) for k in candidates]
    gaps=np.diff(np.sort(np.asarray(distances,dtype=np.float32)))
    return dict(selected=selected,candidates=candidates,visible_sources=len(obj.last_weights),
                weights=[[int(k),float(v)] for k,v in obj.last_weights],
                candidate_counts=[[int(k),int(v)] for k,v in obj.last_counts],
                cutoff_gap_14_15=float(ranked[13][1]-ranked[14][1]) if len(ranked)>14 else None,
                candidate_pose_ties=int((gaps==0).sum()),
                rendered_coverage=float(np.mean(obj.last_render['surfel_index_map']>=0)),
                nms_initial_threshold=float(obj.initial_threshold))
