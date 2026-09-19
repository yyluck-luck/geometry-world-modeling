#!/usr/bin/env python3
"""S6: seal all predicted-geometry selections before opening measured depth or GT."""
import argparse
from datetime import datetime,timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import time
import traceback
import zipfile
import numpy as np
from PIL import Image
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from s6_memory_bridge import crop_intrinsics,normalize_predictions,build_memory,make_selector,memory_digest
from rgbd_retrieval import select,initial_nms_threshold,optical_to_vmem
from learned_pair_metrics import measured_target,first_frame_scale,resize_crop
from rgbd_metrics import project_points
from rgbd_experiment import residual_stats
from tum_rgbd import read_trajectory
from evaluate_cut3r_pair import load_run,sha,compatibility_paths

def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False))


def measured_support(depths,masks,poses,q,K):
    """Fixed measured target-to-history consistency, independent of either memory."""
    fx,fy,cx,cy=K
    target=depths[q][::2,::2];valid=masks[q][::2,::2]
    vv,uu=np.mgrid[0:224:2,0:224:2];z=target[valid]
    camera=np.column_stack(((uu[valid]-cx)*z/fx,(vv[valid]-cy)*z/fy,z))
    world=camera@poses[q][:3,:3].T+poses[q][:3,3]
    support=np.zeros((20,112,112),bool)
    for i in range(20):
        uv,pz,inside=project_points(world,poses[i],K,224,224)
        selected=np.flatnonzero(inside);ij=np.rint(uv[selected]).astype(int)
        bounded=(ij[:,0]>=0)&(ij[:,0]<224)&(ij[:,1]>=0)&(ij[:,1]<224)
        ids=selected[bounded];ij=ij[bounded]
        good=masks[i][ij[:,1],ij[:,0]]&(np.abs(pz[ids]-depths[i][ij[:,1],ij[:,0]])<=.05)
        flat=np.zeros(valid.sum(),bool);flat[ids[good]]=True;support[i][valid]=flat
    return support,valid,target


def project_depth(world,pose,K):
    uv,z,inside=project_points(world,pose,K,224,224)
    ids=np.flatnonzero(inside);grid=np.rint(uv[ids]/2).astype(int)
    good=(grid[:,0]>=0)&(grid[:,0]<112)&(grid[:,1]>=0)&(grid[:,1]<112)
    grid,ids=grid[good],ids[good]
    buffer=np.full(112*112,np.inf)
    np.minimum.at(buffer,grid[:,1]*112+grid[:,0],z[ids])
    buffer=buffer.reshape(112,112);buffer[~np.isfinite(buffer)]=np.nan
    return buffer


def run(args):
    if args.output.exists():raise ValueError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    report=dict(started_utc=utc(),status='running',phase='prediction_only',protocol='docs/S6_MEMORY_BRIDGE_PROTOCOL.md',
        evaluation_environment=dict(python=sys.version,packages={n:version(n) for n in ('numpy','scipy','Pillow','torch')}),
        evidence_level='learned depth and pose to memory/context component; no full VMem generation',
        config=dict(blocks=[0,1,2],strides=[8,12],widths=[160,320],history=20,queries=4,units='first_predicted_depth_median_normalized'),cases=[])
    def checkpoint():write(args.output/'run_metadata.json',report)
    checkpoint()
    try:
        torch.set_num_threads(1)
        frozen_path=ROOT/'data/cut3r/S5_inputs.json';frozen=read(frozen_path)
        if sha(frozen_path)!='7ffa1467f5640bee2013a1ed1d30313be14da339ab28f7c364cfc2790f16f126':raise ValueError('Input manifest changed')
        sequence=read(args.runs/'sequence_metadata.json')
        if (sequence.get('ok') is not True or sequence.get('phase')!='complete' or
            sequence['manifest_sha256']!=sha(frozen_path) or sequence['protocol_sha256']!=sha(ROOT/'docs/S6_MEMORY_BRIDGE_PROTOCOL.md')):
            raise ValueError('Frozen S6 inference controller did not complete')
        if [b['block'] for b in sequence['blocks']]!=[0,1,2] or not all(b.get('ok') and b.get('s5_history_allclose') for b in sequence['blocks']):
            raise ValueError('Missing block or history comparison')
        if any(b['process_peak_rss_bytes']>16*1024**3 for b in sequence['blocks']):raise ValueError('Memory budget exceeded')
        if sha(args.runs/'sequence_runner_snapshot.py')!=sequence['sequence_runner_sha256']:raise ValueError('Controller snapshot changed')
        K=crop_intrinsics();report['crop_intrinsics']=list(K);report['normalizations']={}
        sources=[Path(__file__),ROOT/'src/s6_memory_bridge.py',ROOT/'src/rgbd_memory.py',ROOT/'src/rgbd_metrics.py',
            ROOT/'src/rgbd_retrieval.py',ROOT/'src/rgbd_experiment.py',ROOT/'src/retrieval_diagnostic.py',ROOT/'src/vmem_memory_kernel.py',ROOT/'src/vmem_retrieval_kernel.py',
            ROOT/'src/learned_pair_metrics.py',ROOT/'src/tum_rgbd.py',ROOT/'scripts/evaluate_cut3r_pair.py',
            ROOT/'docs/S6_MEMORY_BRIDGE_PROTOCOL.md',ROOT/'vendor/provenance.json',ROOT/'vendor/VMEM_LICENSE',frozen_path,args.runs/'sequence_metadata.json',args.runs/'sequence_runner_snapshot.py']
        reference=None
        for block in frozen['blocks']:
            b=block['block'];directory=args.runs/f'block{b}'
            meta,raw,_=load_run(directory,'cpu',{'images':[{'sha256':f['rgb_sha256']} for f in block['frames']]},views=24)
            if meta.get('history_only_memory_ok') is not True or meta.get('query_state_write_audit',{}).get('ok') is not True:
                raise ValueError('Query latent state was not verified unchanged')
            audit=meta['query_state_write_audit']
            if audit['anchor_snapshot_index']!=20 or len(audit['checks'])!=8 or not all(x['exactly_unchanged'] and x['finite'] for x in audit['checks']):
                raise ValueError('Incomplete actual latent state checks')
            if meta['runner_sha256']!=sequence['runner_sha256'] or meta['predictions_sha256']!=sequence['blocks'][b]['predictions_sha256']:
                raise ValueError('Inference block/controller identity mismatch')
            identity={k:meta[k] for k in ('commit','model_config','versions','runner_sha256','runtime_compatibility','dtype','seed')}
            if reference is not None and identity!=reference:raise ValueError('Different model between blocks')
            reference=identity
            depths,poses,norm=normalize_predictions(raw)
            if len(depths)!=24:raise ValueError('Missing prediction frames')
            report['normalizations'][str(b)]=dict(first_prediction_inverse_median=norm)
            np.savez_compressed(args.output/f'block{b}_normalized_input.npz',first_depth=depths[0],poses=np.stack(poses))
            rgbs=[]
            for f in block['frames'][:20]:
                rgbpath=args.data/f['rgb']['path']
                if sha(rgbpath)!=f['rgb_sha256']:raise ValueError('RGB input changed')
                image,_=resize_crop(Image.open(rgbpath).convert('RGB'),Image.Resampling.LANCZOS);rgbs.append(np.asarray(image))
            confs=[raw[f'frame{i}_conf_self'][0] for i in range(20)]
            threshold=initial_nms_threshold(poses[:20])
            for stride in (8,12):
                case_dir=args.output/f'block{b}_stride{stride}';case_dir.mkdir()
                selected=[];models={};maps={};selectors={}
                for method in ('first_write','frame_mean'):
                    start=time.perf_counter()
                    memory,filters=build_memory(depths[:20],confs,rgbs,poses[:20],stride=stride,method=method)
                    elapsed=time.perf_counter()-start
                    models[method]=memory
                    np.savez_compressed(case_dir/f'{method}.npz',points=memory.points,
                        normals=np.array([s.normal for s in memory.surfels]),radii=np.array([s.radius for s in memory.surfels]),
                        colors=np.array([s.color for s in memory.surfels]),counts=np.array(memory.counts))
                    write(case_dir/f'{method}_provenance.json',memory.mapping)
                    maps[method]=dict(points=len(memory.surfels),digest=memory_digest(memory),build_seconds=elapsed,build_trace=memory.records,filters=filters)
                    for width in (160,320):selectors[(method,width)]=make_selector(memory,poses[:20],width=width,threshold=threshold)
                control_kernel=selectors[('first_write',160)]
                for q in range(20,24):
                    query=torch.tensor(optical_to_vmem(poses[q]),dtype=torch.float64)
                    ds=torch.tensor([float(control_kernel.geodesic_distance(query,torch.tensor(p),.1)) for p in control_kernel.c2ws])
                    item=dict(frame=q,controls={'recent4':[16,17,18,19],'nearest_pose4':torch.argsort(ds)[:4].tolist()},retrieval={})
                    for width in (160,320):
                        pair={}
                        for method,memory in models.items():
                            if memory_digest(memory)!=maps[method]['digest']:raise ValueError('Memory changed before query')
                            start=time.perf_counter();trace=select(selectors[(method,width)],poses[q]);trace['seconds']=time.perf_counter()-start
                            if memory_digest(memory)!=maps[method]['digest']:raise ValueError('Query wrote to explicit memory')
                            if len(set(trace['selected']))!=4 or any(i<0 or i>=20 for i in trace['selected']):raise ValueError('Invalid context IDs')
                            pair[method]=trace
                        pair['selection_set_changed']=set(pair['first_write']['selected'])!=set(pair['frame_mean']['selected'])
                        item['retrieval'][str(width)]=pair
                    selected.append(item)
                case=dict(block=b,split=block['split'],stride=stride,maps=maps,selected=selected)
                write(case_dir/'prediction_only_selection.json',case)
                report['cases'].append(dict(block=b,stride=stride,directory=case_dir.name,selection_sha256=sha(case_dir/'prediction_only_selection.json')))
            sources.extend([directory/'run_metadata.json',directory/'runner_snapshot.py',directory/'s5_history_comparison.json'])
        # All six predicted-data selections are sealed before reading any depth or mocap.
        report['selections_sealed_utc']=utc();report['phase']='measurement_scoring';checkpoint()
        trajectory=read_trajectory(args.data/'groundtruth.txt')
        sources.append(args.data/'groundtruth.txt');records=[]
        for block in frozen['blocks']:
            b=block['block'];targets=[];masks=[];poses=[]
            for f in block['frames']:
                path=args.data/f['depth']['path']
                if sha(path)!=f['depth_sha256']:raise ValueError('Scoring depth changed')
                depth,mask,_=measured_target(np.asarray(Image.open(path),dtype=np.float64)/5000)
                targets.append(depth);masks.append(mask);poses.append(trajectory.interpolate(f['rgb']['timestamp'],max_gap_seconds=.1).c2w)
            with np.load(args.output/f'block{b}_normalized_input.npz') as n:scale,count=first_frame_scale(n['first_depth'],targets[0],masks[0])
            report['normalizations'][str(b)].update(scoring_only_metric_scale=scale,scoring_only_calibration_pixels=count)
            for entry in [c for c in report['cases'] if c['block']==b]:
                case_dir=args.output/entry['directory'];sealed=case_dir/'prediction_only_selection.json'
                if sha(sealed)!=entry['selection_sha256']:raise ValueError('Sealed selections changed')
                case=read(sealed);maps={}
                for method in ('first_write','frame_mean'):
                    with np.load(case_dir/f'{method}.npz') as m:maps[method]=(m['points']*scale)@poses[0][:3,:3].T+poses[0][:3,3]
                case_records=[]
                for choice in case['selected']:
                    q=choice['frame'];support,valid,target=measured_support(targets,masks,poses,q,K)
                    denominator=int(valid.sum())
                    if denominator==0:raise ValueError('No valid scoring target')
                    pred={method:project_depth(points,poses[q],K) for method,points in maps.items()}
                    common=valid&np.isfinite(pred['first_write'])&np.isfinite(pred['frame_mean'])
                    geometry={}
                    for method in pred:
                        own=valid&np.isfinite(pred[method]);g=residual_stats(pred[method],target,common)
                        g.update(own_support=residual_stats(pred[method],target,own),coverage_of_valid_target=float(own.sum()/denominator));geometry[method]=g
                    retrieval=choice['retrieval']
                    for pair in retrieval.values():
                        for method in ('first_write','frame_mean'):
                            ids=pair[method]['selected'];pair[method]['support_coverage']=float(support[ids].any(axis=0)[valid].mean())
                        pair['coverage_delta_pp']=100*(pair['frame_mean']['support_coverage']-pair['first_write']['support_coverage'])
                    controls={name:dict(selected=ids,support_coverage=float(support[ids].any(axis=0)[valid].mean())) for name,ids in choice['controls'].items()}
                    record=dict(block=b,split=block['split'],stride=case['stride'],frame=q,valid_target_pixels=denominator,
                        common_pixels=int(common.sum()),geometry=geometry,retrieval=retrieval,controls=controls,
                        all_history_support_coverage=float(support.any(axis=0)[valid].mean()))
                    np.savez_compressed(case_dir/f'query{q}_scoring.npz',target=target,valid=valid,support=support,
                        first_write=pred['first_write'],frame_mean=pred['frame_mean'],common=common)
                    records.append(record);case_records.append(record)
                write(case_dir/'result.json',dict(block=b,stride=case['stride'],records=case_records,maps=case['maps']))
        write(args.output/'records.json',records)
        report['paired_query_conditions']=len(records);report['query_width_pairs']=sum(len(r['retrieval']) for r in records)
        if len(records)!=24 or report['query_width_pairs']!=48:raise ValueError('Incomplete fixed cases')
        sources.extend(compatibility_paths(meta));report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in sources}
        with zipfile.ZipFile(args.output/'experiment_source.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sources:z.write(p,str(p.relative_to(ROOT)))
        report['status']='completed';report['phase']='complete'
    except Exception:
        report['status']='failed';report['traceback']=traceback.format_exc();raise
    finally:
        report['completed_utc']=utc();checkpoint()
    print(json.dumps(dict(status=report['status'],paired_query_conditions=len(records),completed_utc=report['completed_utc'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,default=ROOT/'results/S6_cut3r_cpu')
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    p.add_argument('--output',type=Path,default=ROOT/'results/S6_memory_bridge')
    args=p.parse_args();args.runs=args.runs.resolve();args.data=args.data.resolve();args.output=args.output.resolve()
    run(args)
