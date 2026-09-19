#!/usr/bin/env python3
"""S18: six sealed S17C arrays to original Surfel memory and candidate components."""
from __future__ import annotations
import argparse
from collections import defaultdict
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import platform
import random
import resource
import shutil
import sys
import time
import traceback
from typing import Any

import ast
from types import SimpleNamespace
import subprocess
def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def tensor_id(a):
    import numpy as np
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())


def validate_array(a, shape, dtype, label):
    import numpy as np
    require(list(a.shape) == shape and str(a.dtype) == dtype, 'Array schema: ' + label)
    require(np.isfinite(a).all(), 'Array finite gate: ' + label)


COMMIT='39291e4f272f6b4f270691d930926ab5930f942e'
PRIOR_SHA=dict(s17c_manifest='a9d74acb5d79e81696a7cb2cb665577071f47e5af19292230e768638f311c885',
 s17c_seal='424090fd2e1de5cdcf7cd124ed893b9a1dea380cf772420cbb48e57834f31df8',
 s17c_verification='b783a0343f268c601080d3206e1c49670a1485a074d645925ef60879f026efa8',
 s17c_metadata='1e11d45013cf18d038a58853a11785889c0d522bdc61e6121de61fbb7451693a',
 s17c_final='0062327c2395236c087a3cfc743a3d82d57167450f552b9b29ba379171efdc9d')
SOURCE_SHA=dict(pipeline_source='90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e',
 util_source='0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013',
 config_source='8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3')
INPUT_SHAPES=dict(point_clouds=[2,384,512,3],depths=[2,384,512],confidences=[2,384,512],
 focal=[2,1],R=[2,3,3],t=[2,3])
CONTRACT=dict(device='cpu',cpu_threads=8,seed=0,numpy_version='1.26.4',dtype='float32',camera_dtype='float32',
 history_count=2,query_count=2,shrink_factor=.05,reduced_size=[19,25],radius_scale=.5,
 conf_thresh=1,depth_quantile=.999,merge_normal_threshold=.6,max_points_per_node=10,
 merge_position_threshold=None,render_width=512,render_height=288,render_focal_factor=.65,
 render_principal_point=[256,144],disk_resolution=16,context_num_frames=4,
 wall_seconds=600,monitored_rss_bytes=34359738368,external_monitor_required=True,
 model_calls=0,RGB_decodes=0,GT_reads=0,full_context_calls=0,video_generated=False)


def validate_contract(m):
    require(m['schema']=='s18-memory-bridge-manifest-v1' and m['source_commit']==COMMIT,'S18 manifest/commit')
    for k,v in CONTRACT.items():require(m['contract'].get(k,'MISSING')==v,'Contract '+k)
    ids=m['identities']
    roles=['runner','kernels','memory_kernel','retrieval_kernel']+list(PRIOR_SHA)+list(SOURCE_SHA)
    for role in ['python','source_root']+roles:
        require(Path(m[role]).is_absolute(),'Absolute role '+role)
    for role in roles:require(m[role] in ids,'Frozen role '+role)
    for role,digest in (PRIOR_SHA|SOURCE_SHA).items():require(ids[m[role]]==digest,'Fixed source/prior '+role)
    controls=m['control_files'];require(len(controls)==len(set(controls)),'Distinct controls')
    require(set(ids)=={m[k]for k in roles}|set(controls),'Only six-array archive and explicit controls, no inherited RGB/weights')
    for p,d in ids.items():
        require(str(Path(p).resolve())==p and len(d)==64 and all(c in '0123456789abcdef' for c in d),'Canonical path/SHA')
        require(Path(p).suffix.lower() not in {'.png','.jpg','.jpeg','.pth','.pt'},'RGB and checkpoint byte reads forbidden')
        require(Path(p).name not in {'groundtruth.txt','rgb.txt','depth.txt'},'Raw dataset metadata forbidden')
    return ids


def ast_audit(m):
    def cls(path,name):return next(x for x in ast.parse(Path(path).read_text()).body if isinstance(x,ast.ClassDef)and x.name==name)
    original=cls(m['pipeline_source'],'VMemPipeline')
    of={x.name:x for x in original.body if isinstance(x,ast.FunctionDef)}
    mine=cls(m['kernels'],'OriginalGeometryKernel');mf={x.name:x for x in mine.body if isinstance(x,ast.FunctionDef)}
    dump=lambda x:ast.dump(x,include_attributes=False)
    checks=[]
    for role,classname,names in [('kernels','OriginalGeometryKernel',['pointmap_to_surfels','estimate_normal_from_pointmap']),
      ('memory_kernel','MemoryKernel',['merge_surfels','render_surfels_to_image']),
      ('retrieval_kernel','RetrievalKernel',['process_retrieved_spatial_information','get_frame_distribution'])]:
        cf={x.name:x for x in cls(m[role],classname).body if isinstance(x,ast.FunctionDef)}
        for name in names:
            require(dump(cf[name])==dump(of[name]),'Original method AST '+name);checks.append(name)
    source_util={x.name:x for x in ast.parse(Path(m['util_source']).read_text()).body if isinstance(x,ast.ClassDef)}
    for name in ['Surfel','Octree']:
        require(dump(cls(m['memory_kernel'],name))==dump(source_util[name]),'Original utility class AST '+name);checks.append(name)
    body=of['construct_and_store_scene'].body
    i=next(i for i,x in enumerate(body)if ast.unparse(x).startswith('pointcloud = pointcloud.permute'))
    j=next(i for i,x in enumerate(body)if ast.unparse(x)=='confs = confs.squeeze(1)')
    require([dump(x)for x in mf['resize_scene_inputs'].body[:-1]]==[dump(x)for x in body[i:j+1]],'Nine original resize statements')
    require(ast.unparse(mf['resize_scene_inputs'].body[-1])=='return (pointcloud, depths, confs)','Transparent resize output only')
    i=next(i for i,x in enumerate(body)if ast.unparse(x).startswith('start_idx ='))
    require([dump(x)for x in mf['store_reduced_scene'].body]==[dump(x)for x in body[i:i+3]],'Original store loop statements')
    return dict(status='PASS',checks=checks+['resize nine statements','store three statements'],count=10)


def arr(v):
    import numpy as np
    if hasattr(v,'detach'):v=v.detach().cpu().numpy()
    return np.array(v,copy=True)


def save_arrays(out,name,arrays,report):
    import numpy as np
    arrays={k:arr(v)for k,v in arrays.items()};np.savez_compressed(out/name,**arrays)
    report.setdefault('array_files',{})[name]={k:tensor_id(v)for k,v in arrays.items()}
    return arrays


def observe_return(fn,callback,*args,**kwargs):
    """Observe locals at original return; do not substitute mathematical functions."""
    code=getattr(fn,'__func__',fn).__code__;old=sys.gettrace()
    require(old is None,'No competing Python trace')
    def trace(frame,event,arg):
        if event=='call' and frame.f_code is code:
            frame.f_trace_lines=False;return trace
        if frame.f_code is code and event=='return':callback(frame.f_locals,arg)
        return trace if frame.f_code is code else None
    sys.settrace(trace)
    try:return fn(*args,**kwargs)
    finally:sys.settrace(old)


class BridgeObserver:
    def __init__(self,kernel,memory,torch,np,out,report,phase):
        self.k,self.memory,self.T,self.np=kernel,memory,torch,np
        self.out,self.r,self.phase=out,report,phase
        self.frame=-1;self.owners={};self.candidate_objects={};self.merge_records=[]
        self.tree_nodes=[];self.original_octree=memory.Octree
        self.original_pointmap=kernel.pointmap_to_surfels;self.original_merge=kernel.merge_surfels

    def map_snapshot(self,name):
        np=self.np;s=self.k.surfels
        vals=dict(positions=np.asarray([x.position for x in s],dtype=np.float32).reshape(-1,3),
          normals=np.asarray([x.normal for x in s],dtype=np.float32).reshape(-1,3),radii=np.asarray([x.radius for x in s],dtype=np.float32),
          owner_frame=np.asarray([self.owners[id(x)][0]for x in s],dtype=np.int64),
          owner_reduced_flat_id=np.asarray([self.owners[id(x)][1]for x in s],dtype=np.int64))
        require(all(x.color is None for x in s),'Original no-color surfels')
        save_arrays(self.out,name+'.npz',vals,self.r)
        sources={str(i):list(self.k.surfel_to_timestep[i])for i in range(len(s))}
        write(self.out/(name+'_sources.json'),dict(sources=sources,color=None))
        return vals,sources

    def install(self):
        self.k.pointmap_to_surfels=self.pointmap
        self.k.merge_surfels=self.merge

    def pointmap(self,*args,**kwargs):
        self.frame+=1;frame_id=self.frame
        if frame_id: self.map_snapshot('map_after_frame0')
        self.phase('frame_'+str(frame_id)+'_pointmap_started')
        captured={}
        def callback(loc,result):captured.update(loc)
        surfels=observe_return(self.original_pointmap,callback,*args,**kwargs)
        T,np=self.T,self.np
        normal=captured['normal_map'];mask=captured['valid_mask'];flat_ids=T.nonzero(mask.reshape(-1)).flatten()
        point=captured['pointmap'];camera=captured['poses'][:3,3]
        # Additional full-grid diagnostic only: it never controls any original Surfel.
        directions=T.nn.functional.normalize(point.reshape(-1,3)-camera[None],dim=1)
        normal_flat=normal.reshape(-1,3)
        diag_dot=T.sum(directions*normal_flat,dim=1)
        diag_normals=normal_flat.clone();diag_normals[diag_dot<0]=-diag_normals[diag_dot<0]
        diag_radius=captured['radius_scale']*captured['depths'].reshape(-1)/captured['focal_lengths']/(.2+.8*T.abs(T.sum(directions*diag_normals,dim=1)))
        candidate_preflip=T.sum(captured['view_directions']*normal[mask],dim=1)
        vals=dict(normal_map=normal,depth_threshold=captured['depth_threshold'],valid_mask=mask,
          depth_pass=captured['depths']<=captured['depth_threshold'],confidence_pass=captured['confs']>=1,
          candidate_flat_ids=flat_ids,candidate_positions=captured['positions'],candidate_normals=captured['normals'],
          candidate_radii=captured['radii'],preflip_dot=candidate_preflip,flip_mask=captured['flip_mask'],
          fullgrid_view_direction_diagnostic=directions.reshape(*mask.shape,3),
          fullgrid_flipped_normal_diagnostic=diag_normals.reshape(*mask.shape,3),
          fullgrid_preflip_dot_diagnostic=diag_dot.reshape(mask.shape),fullgrid_radius_diagnostic=diag_radius.reshape(mask.shape))
        arrays=save_arrays(self.out,f'frame{frame_id}_geometry.npz',vals,self.r)
        self.r['counters']['pointmap_calls']+=1;self.r['counters']['normal_calls']+=1
        self.r.setdefault('frames',[]).append(dict(index=frame_id,total_grid_cells=mask.numel(),candidates=len(surfels),
          depth_pass=int(vals['depth_pass'].sum()),confidence_pass=int(vals['confidence_pass'].sum()),
          depth_threshold=float(captured['depth_threshold']),diagnostic_only='fullgrid fields never used by original Surfel'))
        require(len(surfels)==len(flat_ids),'Original candidate count/mask order')
        for name,v in arrays.items():
            require(np.isfinite(v).all(),'Original or full-grid nonfinite: '+name)
        require(np.array_equal(arrays['candidate_positions'],arr(point[mask])),'Original position mask order')
        require(np.array_equal(arrays['candidate_radii'],arr(diag_radius[flat_ids])),'Fullgrid diagnostic matches original selected radius')
        for j,s in enumerate(surfels):
            self.owners[id(s)]=(frame_id,int(flat_ids[j]));self.candidate_objects[(frame_id,j)]=s
            require(np.array_equal(s.position,arrays['candidate_positions'][j])and np.array_equal(s.normal,arrays['candidate_normals'][j])and s.radius==arrays['candidate_radii'][j],'Original Surfel fields')
        self.phase('frame_'+str(frame_id)+'_pointmap_saved')
        return surfels

    def merge(self,*args,**kwargs):
        require(not args,'Original store uses named merge parameters')
        np=self.np;new=kwargs['new_surfels'];old=kwargs['existing_surfels'];before=[(x.position.copy(),x.normal.copy(),x.radius,x.color)for x in old]
        owner_by_object={id(x):j for j,x in enumerate(new)}
        records=[dict(candidate_index=j,reduced_flat_id=self.owners[id(x)][1],neighbor_indices=[],normal_dots=[],actual_matched_old_id=None)for j,x in enumerate(new)]
        root_queries=[];obs=self;Original=self.original_octree
        class ObservedOctree(Original):
            def __init__(self,*aa,**kk):
                self.s18_root=kk.get('bbox') is None
                try:super().__init__(*aa,**kk)
                finally:
                    if hasattr(self,'center'):
                        obs.tree_nodes.append(dict(center=arr(self.center).tolist(),half_size=float(self.half_size),
                           indices=None if self.indices is None else arr(self.indices).tolist(),children=len(self.children),is_root=self.s18_root))
            def query_ball_point(self,point,r):
                result=super().query_ball_point(point,r)
                if self.s18_root:
                    j=len(root_queries);require(j<len(records),'Original query count')
                    rec=records[j];rec['position_threshold']=float(r);rec['neighbor_indices']=[int(x)for x in result]
                    rec['normal_dots']=[float(np.dot(old[int(i)].normal,new[j].normal))for i in result]
                    root_queries.append(rec)
                return result
        self.memory.Octree=ObservedOctree
        code=self.original_merge.__func__.__code__
        module_ast=ast.parse(Path(self.memory.__file__).read_text())
        method=next(n for n in ast.walk(module_ast)if isinstance(n,ast.FunctionDef)and n.name=='merge_surfels')
        breaks={n.lineno for n in ast.walk(method)if isinstance(n,ast.Break)}
        prev_trace=sys.gettrace();require(prev_trace is None,'No competing merge trace')
        captured={}
        def trace(frame,event,arg):
            if frame.f_code is not code:return None
            if event=='line'and frame.f_lineno in breaks:
                loc=frame.f_locals;j=owner_by_object[id(loc['new_surfel'])]
                records[j]['actual_matched_old_id']=int(loc['idx'])
            if event=='return':captured.update(frame.f_locals)
            return trace
        sys.settrace(trace)
        try:result=self.original_merge(**kwargs)
        finally:
            sys.settrace(prev_trace);self.memory.Octree=Original
            write(self.out/'octree_nodes.json',dict(nodes=self.tree_nodes,meaning='Actual original constructor order; child-before-parent; no repair'))
            write(self.out/'merge_trace_partial.json',dict(records=records))
        filtered,sources=result
        require(len(root_queries)==len(new),'One actual root query per new candidate')
        retained={id(x):len(old)+i for i,x in enumerate(filtered)}
        for j,x in enumerate(new):
            rec=records[j];matched=rec['actual_matched_old_id']
            require((matched is None)==(id(x)in retained),'Observed original break agrees filtered objects')
            rec['final_surfel_id']=retained[id(x)]if matched is None else matched
            rec['action']='append'if matched is None else 'merge_sources_only'
        for x,b in zip(old,before):
            require(np.array_equal(x.position,b[0])and np.array_equal(x.normal,b[1])and x.radius==b[2]and x.color==b[3],'Original old geometry first-write unchanged')
        self.r['counters']['merge_calls']+=1;self.r['counters']['octree_root_queries']+=len(root_queries)
        self.merge_records=records
        write(self.out/'merge_trace.json',dict(frame=self.frame,position_threshold=float(captured['position_threshold']),normal_threshold=float(captured['normal_threshold']),
            max_points_per_node=int(captured['max_points_per_node']),merge_count=int(captured['merge_count']),records=records,
            old_surfel_count=len(old),new_candidate_count=len(new),filtered_append_count=len(filtered)))
        return result

    def restore(self):
        self.memory.Octree=self.original_octree;self.k.pointmap_to_surfels=self.original_pointmap;self.k.merge_surfels=self.original_merge


def bilinear_provenance(np):
    ys=(np.arange(19,dtype=np.float64)+.5)/.05-.5
    xs=(np.arange(25,dtype=np.float64)+.5)/.05-.5
    y,x=np.meshgrid(ys,xs,indexing='ij');y0=np.floor(y).astype(np.int64);x0=np.floor(x).astype(np.int64)
    wy=y-y0;wx=x-x0
    return dict(input_xy=np.stack([x,y],-1),neighbor_yx=np.stack([np.stack([y0,x0],-1),np.stack([y0,x0+1],-1),
      np.stack([y0+1,x0],-1),np.stack([y0+1,x0+1],-1)],axis=-2),
      weights=np.stack([(1-wy)*(1-wx),(1-wy)*wx,wy*(1-wx),wy*wx],-1))


def consume_query(k,np,out,index,pose,render_focal,report):
    before=repr([(s.position.tobytes(),s.normal.tobytes(),s.radius,list(k.surfel_to_timestep[i]))for i,s in enumerate(k.surfels)])
    start=time.perf_counter()
    result=k.render_surfels_to_image(k.surfels,pose,[render_focal[0],render_focal[1]],
        principal_points=(256,144),image_width=512,image_height=288,disk_resolution=16)
    report['counters']['render_calls']+=1
    save_arrays(out,f'render_query{index}.npz',result,report)
    captured={}
    def callback(loc,ret):captured.update(loc)
    weights,counts=observe_return(k.process_retrieved_spatial_information,callback,result)
    report['counters']['process_calls']+=1
    raw=[(int(i),float(v))for i,v in captured['timestep_count'].items()]
    weights=[(int(i),float(v))for i,v in weights];counts=[(int(i),int(v))for i,v in counts]
    total=float(np.sum(captured['timestep_count_values']))
    visible=int((result['surfel_index_map']>=0).sum())
    status='NO_VISIBLE_SOURCE'if not weights else 'SUCCESS'
    vote=dict(query_index=index,status=status,raw_timestep_count_in_insertion_order=raw,
      raw_weight_sum=total,timestep_weights=weights,frame_count=counts,
      num_retrieved_frames=int(captured['num_retrieved_frames']),visible_pixels=visible,
      pixel_count=int(result['depth'].size),candidate_source_ids=[i for i,n in counts if n>0],
      elapsed_seconds=time.perf_counter()-start,semantics='Original C-order voting including first-item double addition; only up to 2 sources, each supported source gets 1')
    write(out/f'votes_query{index}.json',vote)
    if weights:require(np.isfinite(total)and total>0 and all(np.isfinite(x[1])for x in weights),'Nonempty degenerate weights')
    require(all(n==1 for _,n in counts),'Original two-source candidate quota')
    require(np.isfinite(result['depth']).all()and np.isfinite(result['cos_value_map']).all(),'Finite original render')
    require(repr([(s.position.tobytes(),s.normal.tobytes(),s.radius,list(k.surfel_to_timestep[i]))for i,s in enumerate(k.surfels)])==before,'Render/process mutated map')
    report.setdefault('queries',[]).append(vote)
    return status


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(not a.output.exists(),'Fresh S18 output directory required');a.output.mkdir(parents=True)
    start=time.perf_counter();r=dict(schema='s18-memory-bridge-run-v1',status='RUNNING',started_utc=utc(),
      model_calls=0,RGB_decodes=0,RGB_byte_reads=0,checkpoint_reads=0,GT_reads=0,video_generated=False,
      new_method=False,accuracy_evaluated=False,full_context_calls=0,
      counters=dict(final_array_decodes=0,resize_calls=0,store_calls=0,pointmap_calls=0,normal_calls=0,
        merge_calls=0,octree_root_queries=0,render_calls=0,process_calls=0),input_reads=[])
    def phase(name):
        r.update(phase=name,updated_utc=utc(),elapsed_seconds=time.perf_counter()-start,
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin'else 1024))
        write(a.output/'run_metadata.json',r);print(json.dumps(dict(utc=utc(),phase=name)),flush=True)
    def check(ids,when):
        for path,digest in ids.items():require(sha(path)==digest,'Input identity changed '+path)
        r.setdefault('identity_checks',[]).append(dict(when=when,utc=utc(),count=len(ids),all_match=True))
    observer=None
    try:
        phase('manifest_validation');m=json.loads(a.manifest.read_text());ids=validate_contract(m)
        require(str(Path(__file__).resolve())==m['runner'],'Runner path')
        require(os.path.realpath(sys.executable)==os.path.realpath(m['python']),'Python path')
        check(ids,'before');r['ast_audit']=ast_audit(m)
        require(subprocess.check_output(['/usr/bin/git','-C',m['source_root'],'rev-parse','HEAD'],text=True).strip()==COMMIT,'Original commit')
        require(not subprocess.check_output(['/usr/bin/git','-C',m['source_root'],'status','--porcelain','--untracked-files=no'],text=True).strip(),'Original checkout unchanged')
        prior_meta=json.loads(Path(m['s17c_metadata']).read_text());prior_seal=json.loads(Path(m['s17c_seal']).read_text());prior_verify=json.loads(Path(m['s17c_verification']).read_text())
        require(prior_meta['status']=='SUCCESS'and prior_verify['status']=='PASS','Completed S17C evidence')
        require(prior_meta['manifest_sha256']==PRIOR_SHA['s17c_manifest'],'Prior manifest binding')
        for role in ['s17c_metadata','s17c_final']:require(prior_seal['identities'].get(m[role])==PRIOR_SHA[role],'Prior sealed selected output')
        for role,source in [('bound manifest','s17c_manifest'),('bound output seal','s17c_seal')]:
            require(any(x.get('role')==role and x.get('path')==m[source]and x.get('sha256')==PRIOR_SHA[source]for x in prior_verify['file_hashes']),'Prior verification binding')
        shutil.copy2(a.manifest,a.output/'frozen_manifest.json');shutil.copy2(__file__,a.output/'source_snapshot.py');shutil.copy2(m['kernels'],a.output/'kernel_snapshot.py')
        r.update(manifest_sha256=sha(a.manifest),source_commit=COMMIT,contract=m['contract'],prior_control_scope='Only five fixed files; no recursive prior input reads')
        root=Path(m['runner']).resolve().parents[1];sys.path.insert(0,str(root))
        import numpy as np
        import torch
        from src import vmem_memory_kernel as memory
        from src.s18_original_kernels import OriginalGeometryKernel
        import yaml
        require(np.__version__=='1.26.4'and torch.__version__=='2.7.0','Fixed numerical environment')
        require(str(Path(memory.__file__).resolve())==m['memory_kernel'],'Memory kernel identity')
        random.seed(0);np.random.seed(0);torch.manual_seed(0);torch.set_num_threads(8)
        config=yaml.safe_load(Path(m['config_source']).read_text())
        for key,value in dict(shrink_factor=.05,radius_scale=.5,conf_thresh=1,merge_normal_threshold=.6,width=512,height=288).items():require(config['surfel'][key]==value,'Original YAML '+key)
        k=OriginalGeometryKernel();k.device='cpu';k.surfels=[];k.surfel_to_timestep={}
        k.config=SimpleNamespace(surfel=SimpleNamespace(**config['surfel']),model=SimpleNamespace(**config['model']))
        r.update(numpy_version=np.__version__,torch_version=torch.__version__,python=sys.version,executable=sys.executable,
          seed=0,cpu_threads=8,runtime_kernel_paths=dict(memory=memory.__file__,geometry=m['kernels'],retrieval=m['retrieval_kernel']))
        phase('decode_six_sealed_arrays')
        with np.load(m['s17c_final'],allow_pickle=False)as data:inputs={key:data[key].copy()for key in INPUT_SHAPES}
        r['counters']['final_array_decodes']=6
        r['input_reads'].append(dict(path=m['s17c_final'],role='Whole archive SHA bytes; only six named arrays decoded; pp/colors not decoded',keys=list(INPUT_SHAPES),utc=utc()))
        for key,shape in INPUT_SHAPES.items():
            validate_array(inputs[key],shape,'float32',key)
            require(tensor_id(inputs[key])==prior_meta['array_files']['final_result.npz'][key],'Prior array identity '+key)
        require((inputs['depths']>0).all()and(inputs['focal']>0).all()and(inputs['confidences']>=0).all(),'Prior numeric validity')
        c2ws=np.tile(np.eye(4,dtype=np.float32),(2,1,1));c2ws[:,:3,:3]=inputs['R'];c2ws[:,:3,3]=inputs['t']
        point,depth,conf=k.resize_scene_inputs(torch.from_numpy(inputs['point_clouds']),torch.from_numpy(inputs['depths']),torch.from_numpy(inputs['confidences']))
        r['counters']['resize_calls']=1
        require(list(point.shape)==[2,19,25,3]and list(depth.shape)==list(conf.shape)==[2,19,25],'Exact native reduction')
        focal=inputs['focal'];target_K=np.mean(focal,axis=0);render_focal=np.asarray([target_K*.65]*2)
        require(render_focal.shape==(2,1)and render_focal.dtype==np.float32,'Original FP32 array focal route')
        save_arrays(a.output,'reduced_inputs.npz',dict(pointcloud=point,depths=depth,confs=conf,c2ws=c2ws,focal=focal,
          scaled_focal=focal*.05,render_focal=render_focal,render_pp=np.asarray([256,144],dtype=np.int64)),r)
        save_arrays(a.output,'bilinear_provenance.npz',bilinear_provenance(np),r)
        observer=BridgeObserver(k,memory,torch,np,a.output,r,phase);observer.install()
        phase('original_store_loop_started');r['counters']['store_calls']+=1
        k.store_reduced_scene(point,depth,conf,focal,c2ws)
        final_map,sources=observer.map_snapshot('map_after_frame1')
        r['map_surfel_count']=len(k.surfels);r['map_source_lists']=sources
        mapping=[]
        final_obj={id(s):i for i,s in enumerate(k.surfels)}
        records={x['candidate_index']:x for x in observer.merge_records}
        for (frame,j),s in observer.candidate_objects.items():
            final_id=final_obj.get(id(s))
            if final_id is None:final_id=records[j]['final_surfel_id']
            flat=observer.owners[id(s)][1]
            mapping.append(dict(frame=frame,candidate_index=j,reduced_flat_id=flat,reduced_row=flat//25,reduced_col=flat%25,final_surfel_id=final_id,geometry_retained=id(s)in final_obj))
        write(a.output/'candidate_provenance.json',dict(candidates=mapping,meaning='Source is reduced bilinear cell, not one original pixel'))
        observer.restore();observer=None
        phase('original_memory_saved')
        if not k.surfels:r['status']='NO_SURFELS'
        else:
            statuses=[]
            for i in range(2):
                phase('query_'+str(i)+'_started');statuses.append(consume_query(k,np,a.output,i,c2ws[i],render_focal,r))
            r['status']='NO_VISIBLE_SOURCE'if 'NO_VISIBLE_SOURCE'in statuses else 'SUCCESS'
        require(r['counters']['pointmap_calls']==2,'Two frames consumed')
        check(ids,'after');r['before_after_identity_pass']=True
        require(time.perf_counter()-start<=600,'Internal wall bound')
        phase('complete');require(r['peak_rss_bytes']<=34359738368,'Internal RSS bound')
    except BaseException as ex:
        r.update(status='FAILED',error_type=type(ex).__name__,error=str(ex),traceback=traceback.format_exc())
        if observer is not None:
            try:observer.map_snapshot('map_failure')
            except BaseException as error:r['failure_snapshot_error']=repr(error)
    finally:
        if observer is not None:observer.restore()
        r['completed_utc']=utc()
        r['output_files']={str(p.relative_to(a.output)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(a.output.rglob('*'))if p.is_file()and p.name!='run_metadata.json'}
        phase('finished')
    return 0 if r['status']in {'SUCCESS','NO_SURFELS','NO_VISIBLE_SOURCE'}else 1


if __name__=='__main__':raise SystemExit(main())
