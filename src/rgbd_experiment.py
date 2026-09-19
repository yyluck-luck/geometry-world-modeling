"""One predeclared RGB-D comparison case, independent of dataset I/O."""
from pathlib import Path
import time
import numpy as np
import torch
from experiment_io import write_json,utc_now
from rgbd_memory import Memory,make_surfels
from rgbd_retrieval import make_selector,select,initial_nms_threshold,optical_to_vmem
from rgbd_metrics import depth_consistency,measurement_support


def residual_stats(pred,target,mask):
    values=(pred-target)[mask]
    if not len(values): return dict(n=0,mae_mm=None,median_abs_mm=None,p90_abs_mm=None,within_30mm=None,signed_mean_mm=None)
    a=np.abs(values)
    return dict(n=len(a),mae_mm=float(a.mean()*1000),median_abs_mm=float(np.median(a)*1000),
                p90_abs_mm=float(np.quantile(a,.9)*1000),within_30mm=float((a<=.03).mean()),
                signed_mean_mm=float(values.mean()*1000))


def compare_case(frames,block_id,stride,bias_m,directory,resolutions=(160,320)):
    """frames: exactly 24 time-ordered dicts, first 20 history, last 4 held out."""
    if len(frames)!=24: raise ValueError('Expected exactly 24 distinct observations')
    torch.set_num_threads(1)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    history,queries=frames[:20],frames[20:]
    models={method:Memory(method) for method in ('first_write','frame_mean')}
    checkpoints={}
    for t,f in enumerate(history):
        surfels=make_surfels(f['depth'],f['rgb'],f['c2w_optical'],stride=stride,
                             initial_bias_m=bias_m if t==0 else 0.)
        for name,memory in models.items():
            memory.add(surfels,t)
            if t in (0,4,9,19): checkpoints.setdefault(name,{})[t]=memory.points.copy()
    poses=[f['c2w_optical'] for f in history]
    threshold=initial_nms_threshold(poses)
    selectors={(method,width):make_selector(m,poses,width,width*3//4,threshold)
               for method,m in models.items() for width in resolutions}
    records=[]
    for qid,f in enumerate(queries):
        depths={name:depth_consistency(m.points,f,stride=4) for name,m in models.items()}
        baseline,variant=depths['first_write'],depths['frame_mean']
        common=baseline['common_mask']&variant['common_mask']
        support,target_valid=measurement_support(history,f,stride=4,tolerance=.05)
        denominator=int(target_valid.sum())
        all_history_supported=int((support.any(axis=0)&target_valid).sum())
        # Auxiliary baselines are independent of memory and use no target depth
        # for choosing IDs; measured support is evaluated only after selection.
        pose_kernel=selectors[('first_write',resolutions[0])]
        query_pose=torch.tensor(optical_to_vmem(f['c2w_optical']))
        distances=torch.tensor([float(pose_kernel.geodesic_distance(query_pose,torch.tensor(p),.1)) for p in pose_kernel.c2ws])
        controls={'recent4':list(range(16,20)),
                  'nearest_pose4':torch.argsort(distances)[:4].tolist()}
        control_scores={name:dict(selected=ids,
                         fixed_measurement_support_coverage=float(support[ids].any(axis=0)[target_valid].mean()) if denominator else None)
                         for name,ids in controls.items()}
        geometry={}
        for name,d in depths.items():
            geometry[name]=residual_stats(d['pred_depth'],d['target_depth'],common)
            geometry[name]['own_support']=residual_stats(d['pred_depth'],d['target_depth'],d['common_mask'])
            geometry[name]['coverage_of_valid_target']=float(d['common_mask'].sum()/denominator) if denominator else None
        retrieval={}
        for width in resolutions:
            pair={}
            for name in models:
                before=time.perf_counter()
                trace=select(selectors[name,width],f['c2w_optical'])
                selected=trace['selected']
                if len(set(selected))!=4 or any(i<0 or i>=20 for i in selected):
                    raise ValueError(f'Invalid selected history {selected}')
                union=support[selected].any(axis=0)&target_valid
                trace['fixed_measurement_support_coverage']=float(union.sum()/denominator) if denominator else None
                trace['coverage_of_all_history_supported']=float(union.sum()/all_history_supported) if all_history_supported else None
                trace['selection_seconds']=time.perf_counter()-before
                pair[name]=trace
            pair['selection_set_changed']=set(pair['first_write']['selected'])!=set(pair['frame_mean']['selected'])
            pair['coverage_delta']=pair['frame_mean']['fixed_measurement_support_coverage']-pair['first_write']['fixed_measurement_support_coverage'] if denominator else None
            retrieval[str(width)]=pair
        # Recovery checkpoints use the same held-out measurement solely after building.
        recovery={}
        recovery_depths={}
        for name,snapshots in checkpoints.items():
            recovery[name]={}
            for step,points in snapshots.items():
                d=depth_consistency(points,f,stride=4)
                recovery_depths[(name,step)]=d
                recovery[name][str(step)]=residual_stats(d['pred_depth'],d['target_depth'],d['common_mask'])
        recovery_common=np.logical_and.reduce([d['common_mask'] for d in recovery_depths.values()])
        recovery_fixed={name:{str(step):residual_stats(recovery_depths[(name,step)]['pred_depth'],baseline['target_depth'],recovery_common)
                              for step in checkpoints[name]} for name in models}
        record=dict(block=block_id,split='development' if block_id==0 else 'test',stride=stride,
                    first_frame_depth_axis_bias_m=bias_m,query=qid,timestamp=f['timestamp'],
                    valid_target_pixels=denominator,all_history_supported_pixels=all_history_supported,
                    all_history_support_coverage=float(all_history_supported/denominator) if denominator else None,
                    common_prediction_pixels=int(common.sum()),geometry=geometry,retrieval=retrieval,query_controls=control_scores,
                    recovery_own_support=recovery,recovery_fixed_support=recovery_fixed,
                    recovery_fixed_pixels=int(recovery_common.sum()))
        records.append(record)
        np.savez_compressed(directory/f'query_{qid}_depths.npz',target=baseline['target_depth'],
                            first_write=baseline['pred_depth'],frame_mean=variant['pred_depth'],
                            common=common,target_valid=target_valid)
    maps={}
    for name,m in models.items():
        m.save(directory/f'{name}.npz')
        write_json(directory/f'{name}_provenance.json',m.mapping)
        maps[name]=dict(points=len(m.surfels),build_trace=m.records,
                        total_build_seconds=sum(r['elapsed_seconds'] for r in m.records),
                        map_npz_bytes=(directory/f'{name}.npz').stat().st_size,
                        provenance_json_bytes=(directory/f'{name}_provenance.json').stat().st_size)
    result=dict(block=block_id,stride=stride,bias_m=bias_m,completed_utc=utc_now(),
                elapsed_seconds=time.perf_counter()-started,maps=maps,records=records)
    write_json(directory/'result.json',result)
    return result
