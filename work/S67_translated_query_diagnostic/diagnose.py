"""One fixed translated query, two radial-depth geometries; saved numeric data only."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import argparse
import ast
import hashlib
import json
import math
import struct
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ARCHIVE=ROOT/'results/S47B_C2_confirmation_generation_v9/archive'
PARENT=ROOT/'work/S63_c2_context_integration/replay_context.py'
PARENT_SHA='b36e788d486bd3d15126f8c2d40fffef9f9e5dee4dcb91cbc31fd2553104e1a5'
PROVENANCE={
 'work/S66_s64_camera_scoring/NEXT_SCIENTIFIC_DECISION_REVIEW.md':'62f3ee5fad654b3a2438585e42af2594cefb7021857b8f38635cf96e89ef02ae',
 'work/S65_observability_triage/S65_BEGINNER_RESEARCH_NOTE.md':'d40bb2783dd987d15aa0951bb92cafebe875b230c3c68fadc97bca8c84062879',
 'work/S63_c2_context_integration/PROTOCOL.md':'9b5786167cd457f028e44fa2c486312d61a217f35eeb9e35dd0323125145b5a2',
 'work/S63_c2_context_integration/execution_01/receipt.json':'2f103d6330bc1276f41d1dbdc66e4ad65c99945d02210008f7fd80b56dee341a',
}
HELPERS={'require','sha','field','Decoder','fingerprint','original_numeric_class','exact','load_inputs','check_maps'}
CONSTANTS={'PIPELINE','UTIL','ADAPTER','PINS','METHODS','CACHE_OUTPUTS'}
HISTORY_ATOL=1e-10  # Native stored-K image coordinates, not scene-length units.
QUERY_EFFECT_ATOL_PX=1e-6

def utc():return datetime.now(timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
class IncompatibleInput(ValueError):pass
def compatible(ok,message,detail=None):
    if not ok:
        error=IncompatibleInput(message);error.detail=detail
        raise error
def write_new(path,obj):
    with path.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def reuse_code():
    raw=PARENT.read_bytes();require(sha(raw)==PARENT_SHA,'S63 parent changed')
    tree=ast.parse(raw,filename=str(PARENT))
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in HELPERS
           or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in CONSTANTS for t in n.targets)]
    require(len(nodes)==len(HELPERS)+len(CONSTANTS),'Unexpected S63 extraction coverage')
    return compile(ast.Module(body=nodes,type_ignores=[]),str(PARENT)+'[S67 unchanged helpers]','exec')

def project(points,pose,K):
    R=pose[:3,:3]
    compatible(np.isfinite(pose).all() and np.allclose(pose[3],[0,0,0,1],atol=1e-12,rtol=0)
               and np.allclose(R.T@R,np.eye(3),atol=1e-6,rtol=0)
               and abs(np.linalg.det(R)-1)<=1e-6,'Invalid stored camera rotation/row')
    xyz=np.linalg.solve(R,(points-pose[:3,3]).T).T
    compatible(np.isfinite(xyz).all() and (xyz[:,2]>0).all(),'Nonpositive/nonfinite point depth in a required camera',
               dict(nonpositive_indices=np.flatnonzero(xyz[:,2]<=0).tolist(),
                    nonfinite_rows=np.flatnonzero(~np.isfinite(xyz).all(axis=1)).tolist(),
                    positive_count=int((xyz[:,2]>0).sum()),camera_pose=pose.tolist()))
    compatible(K.shape==(3,3) and np.isfinite(K).all() and K[0,0]>0 and K[1,1]>0
               and np.array_equal(K[2],[0,0,1]),'Invalid actual intrinsic matrix')
    homogeneous=(K@xyz.T).T
    uv=homogeneous[:,:2]/homogeneous[:,2,None]
    compatible(np.isfinite(uv).all(),'Projection is nonfinite')
    return uv,xyz[:,2]

def prepare_pair(ns,cls,inputs,expected,out):
    base=np.asarray(expected['render_args'][0],dtype=np.float64).copy()
    center=np.asarray(inputs['cache']['c2ws'][0],dtype=np.float64)[:3,3].copy()
    # A scene-length tolerance would be misleading at this tiny scale.
    compatible(all(np.array_equal(np.asarray(c,dtype=np.float64)[:3,3],center)
                   for c in inputs['cache']['c2ws']) and np.array_equal(base[:3,3],center),
               'Historical/query centers are not exactly shared; no radial-equivalence claim',
               dict(historical_centers=[np.asarray(c,dtype=np.float64)[:3,3].tolist() for c in inputs['cache']['c2ws']],
                    original_raw_query_center=base[:3,3].tolist()))
    probe=cls();average=cls.get_context_info.__globals__['average_camera_pose']
    reconstructed=probe.get_transformed_c2ws(average(torch.from_numpy(inputs['target'][-1:])))
    ns['exact'](reconstructed,expected['render_args'][0])
    points=np.stack([s.position for s in inputs['surfels']]).astype(np.float64)
    radii=np.array([float(s.radius) for s in inputs['surfels']],dtype=np.float64)
    _,depth=project(points,base,np.eye(3))
    m0=float(np.median(depth));compatible(math.isfinite(m0) and m0>0,'No positive reference median')
    factors=m0/depth
    changed=center+(points-center)*factors[:,None]
    changed_radii=radii*factors
    compatible(np.isfinite(changed).all() and np.isfinite(changed_radii).all()
               and (changed_radii>=0).all(),'Radial intervention is invalid')
    _,flat_depth=project(changed,base,np.eye(3))
    flat_relative_error=float(np.max(np.abs(flat_depth/m0-1)))
    compatible(flat_relative_error<=1e-10,'Computed B depths do not satisfy the fixed radial rule',
               dict(max_relative_depth_error=flat_relative_error,tolerance=1e-10))
    delta=.1*m0*base[:3,0]
    desired=base.copy();desired[:3,3]+=delta
    # Both arms use this same float64 target array. Existing FP32 rotation values
    # are represented exactly; only the planned translation changes numerically.
    target=inputs['target'].astype(np.float64)
    compatible(all(np.array_equal(t[:3,3],center) for t in target),'Targets do not share historical center')
    promoted_query=probe.get_transformed_c2ws(average(torch.from_numpy(target[-1:])))
    target[:,:3,3]+=delta
    fixed_query=probe.get_transformed_c2ws(average(torch.from_numpy(target[-1:])))
    # The same original SciPy rotation/quaternion construction defines the
    # promoted common query. Report any common dtype rounding versus old query.
    ns['exact'](fixed_query[:3,:3],promoted_query[:3,:3])
    ns['exact'](fixed_query[:3,3],desired[:3,3])
    old_projected=[];new_projected=[];residuals=[];positive=[]
    for camera_index,(pose,K) in enumerate(zip(inputs['cache']['c2ws'],inputs['cache']['Ks'],strict=True)):
        cv=probe.get_transformed_c2ws(np.asarray(pose,dtype=np.float64))
        u,z=project(points,cv,np.asarray(K,dtype=np.float64))
        v,zz=project(changed,cv,np.asarray(K,dtype=np.float64))
        residual=float(np.max(np.abs(u-v)))
        compatible(residual<=HISTORY_ATOL,'Historical point projection compatibility failed',
                   dict(camera_index=camera_index,max_abs_native_K_coordinates=residual,tolerance=HISTORY_ATOL))
        old_projected.append(u);new_projected.append(v);residuals.append(residual)
        positive.append([int((z>0).sum()),int((zz>0).sum())])
    focal=expected['render_args'][1];cx,cy=expected['render_kwargs']['principal_points']
    query_K=np.array([[float(np.asarray(focal[0]).item()),0,cx],
                      [0,float(np.asarray(focal[1]).item()),cy],[0,0,1]],dtype=np.float64)
    qa,qza=project(points,fixed_query,query_K);qb,qzb=project(changed,fixed_query,query_K)
    displacement=np.linalg.norm(qa-qb,axis=1)
    arms={'A':deepcopy(inputs),'B':deepcopy(inputs)}
    for arm in arms.values():arm['target']=target.copy()
    for i,s in enumerate(arms['B']['surfels']):
        s.position=changed[i].copy();s.radius=float(changed_radii[i])
    require(ns['fingerprint'](arms['A']['surfels'])==ns['fingerprint'](inputs['surfels']),'A geometry changed')
    for i,s in enumerate(arms['B']['surfels']):
        require(ns['fingerprint']((s.normal,s.source_ids))==ns['fingerprint']((inputs['surfels'][i].normal,inputs['surfels'][i].source_ids)),
                'Intervention changed normal/source IDs')
    for arm in arms.values():
        require(ns['fingerprint'](arm['cache'])==ns['fingerprint'](inputs['cache']),'Intervention changed real cache')
    with (out/'fixed_geometry_and_projections.npz').open('xb') as f:
        np.savez_compressed(f,positions_A=points,positions_B=changed,radii_A=radii,radii_B=changed_radii,
                            radial_factors=factors,reference_depths=depth,common_center=center,
                            original_query=base,promoted_untranslated_query=promoted_query,
                            fixed_query=fixed_query,target_c2ws=target,
                            historical_projection_A=np.array(old_projected),historical_projection_B=np.array(new_projected),
                            query_projection_A=qa,query_projection_B=qb,query_depth_A=qza,query_depth_B=qzb)
    report=dict(shared_centers_exact=True,surfel_count=515,history_camera_count=5,
                m0_original_positive_depth_median=m0,reference_depth_min=float(depth.min()),reference_depth_max=float(depth.max()),
                world_translation=delta.tolist(),translation_rule='0.1*m0*original_raw_query_x_axis',
                fixed_raw_query=fixed_query.tolist(),target_dtype='float64_exact_old_rotation_values_plus_fixed_translation',
                promoted_vs_original_rotation_max_abs=float(np.max(np.abs(promoted_query[:3,:3]-base[:3,:3]))),
                promoted_vs_original_rotation_exact=bool(np.array_equal(promoted_query[:3,:3],base[:3,:3])),
                radial_factor_min=float(factors.min()),radial_factor_max=float(factors.max()),
                B_reference_depth_max_relative_error=flat_relative_error,
                B_depth_rule='positive original raw-query z compressed to m0 along shared-center rays',
                historical_projection_max_abs_by_camera=residuals,historical_projection_tolerance=HISTORY_ATOL,
                historical_projection_units='native coordinates of each actual stored K; no guessed calibration',
                historical_positive_counts=positive,query_projection_units='actual renderer pixel coordinates',
                query_displacement_max_px=float(displacement.max()),query_displacement_median_px=float(np.median(displacement)),
                query_displacement_above_1e_6_px=int((displacement>QUERY_EFFECT_ATOL_PX).sum()),
                equivalence_scope='Only these 515 point projections in five stored cameras; not normal estimation, occlusion or complete images')
    write_new(out/'prepared_pair.json',report)
    return arms,fixed_query,report

def run_arm(label,ns,cls,inputs,expected,fixed_query,adapter,out,result):
    before=ns['fingerprint'](inputs);scratch=deepcopy(inputs);scratch_before=ns['fingerprint'](scratch)
    kernel=cls();kernel.device,kernel.dtype=torch.device('cpu'),torch.float32
    kernel.config=SimpleNamespace(model=SimpleNamespace(context_num_frames=4,translation_distance_weight=.1),
                    surfel=SimpleNamespace(width=512,height=288),inference=SimpleNamespace(visualize=False))
    kernel.use_non_maximum_suppression=True;kernel.pil_frames=[None]*5
    for key,value in scratch['cache'].items():setattr(kernel,key,value)
    kernel.surfels,kernel.surfel_to_timestep=scratch['surfels'],scratch['surfel_to_timestep']
    result.update(arm=label,status='RUNNING',renderer_calls=0,retrieval_calls=0)
    def original_renderer(surfels,pose,focal,**kwargs):
        result['renderer_calls']+=1;require(result['renderer_calls']==1,'Extra renderer call')
        return cls.render_surfels_to_image(kernel,surfels,pose,focal,**kwargs)
    def render(surfels,pose,focal,**kwargs):
        ns['exact'](pose,fixed_query)
        for actual,reference in zip(focal,expected['render_args'][1],strict=True):ns['exact'](np.asarray(actual),reference)
        require(kwargs==expected['render_kwargs'],'Original renderer kwargs changed')
        result['raw_query_sha256']=ns['fingerprint']((pose,focal,kwargs))
        maps,result['unit_receipt']=adapter(original_renderer,surfels,pose,focal,**kwargs)
        with (out/(label+'_maps.npz')).open('xb') as f:np.savez_compressed(f,**maps)
        result['map_support']=ns['check_maps'](maps)
        valid=(maps['surfel_index_map']>=0)&(maps['cos_value_map']>=0)
        indices=np.unique(maps['surfel_index_map'][valid])
        members=sorted({int(i) for point in indices for i in kernel.surfel_to_timestep[int(point)]})
        result['participating_sources_from_map']=members
        result['nonnegative_cos_support_pixels']=int(valid.sum())
        result['participating_surfel_count']=int(indices.size)
        return maps
    def retrieve(maps):
        result['retrieval_calls']+=1;require(result['retrieval_calls']==1,'Extra retrieval call')
        weights,counts=cls.process_retrieved_spatial_information(kernel,maps)
        result['weights']=[[int(i),float(w) if np.isfinite(w) else repr(float(w))] for i,w in weights]
        result['quotas']=[[int(i),int(n)] for i,n in counts]
        result['participating_sources']=[int(i) for i,w in weights]
        require(result['participating_sources']==result['participating_sources_from_map'],'Member-set interpretation differs')
        require(all(np.isfinite(w) for i,w in weights),'Nonfinite original retrieval weights')
        if counts:
            require(all(int(n)==1 for i,n in counts),'Unexpected quota in fixed five-source pool')
        return weights,counts
    kernel.render_surfels_to_image,kernel.process_retrieved_spatial_information=render,retrieve
    try:
        context=kernel.get_context_info(torch.from_numpy(scratch['target']),None)
        arrays={key:value.detach().cpu().numpy() for key,value in context.items()}
        with (out/(label+'_context.npz')).open('xb') as f:np.savez_compressed(f,**arrays)
        require(set(arrays)==set(ns['CACHE_OUTPUTS'])|{'context_time_indices'},'Unexpected context fields')
        ids=arrays['context_time_indices'];count=min(4,sum(n for i,n in result['quotas']),5)
        require(ids.dtype==np.int64 and ids.shape==(count,) and 0<count<=4
                and ((ids>=0)&(ids<5)).all() and np.unique(ids).size==count,'Invalid returned IDs/count')
        result['ordered_ids']=ids.tolist();result['context_slot_identities']={}
        for key,cache_key in ns['CACHE_OUTPUTS'].items():
            reference=np.stack([inputs['cache'][cache_key][int(i)] for i in ids]).astype(np.float32)
            require(np.isfinite(arrays[key]).all(),'Nonfinite actual context')
            ns['exact'](arrays[key],reference)
            result['context_slot_identities'][key]=[dict(slot=slot,source_id=int(i),dtype=arrays[key][slot].dtype.str,
                    shape=list(arrays[key][slot].shape),actual_bytes_sha256=sha(arrays[key][slot].tobytes()),
                    expected_FP32_cache_bytes_sha256=sha(reference[slot].tobytes())) for slot,i in enumerate(ids)]
        require(result['renderer_calls']==result['retrieval_calls']==1,'Missing original stage call')
        result.update(status='VALID_CONTEXT_RETURN',initial_threshold=float(kernel.initial_threshold))
    except Exception as error:
        result.update(status='INVALID_OR_FAILED_ARM',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        if hasattr(kernel,'initial_threshold'):result['initial_threshold']=float(kernel.initial_threshold)
        attached=dict(cache={key:getattr(kernel,key) for key in scratch['cache']},surfels=kernel.surfels,
                      target=scratch['target'],surfel_to_timestep=kernel.surfel_to_timestep)
        result['input_sha256_before']=before;result['input_sha256_after']=ns['fingerprint'](inputs)
        result['scratch_sha256_before']=scratch_before;result['scratch_sha256_after']=ns['fingerprint'](scratch)
        result['attached_sha256_after']=ns['fingerprint'](attached)
        require(before==result['input_sha256_after'] and scratch_before==result['scratch_sha256_after']==result['attached_sha256_after'],
                'Arm mutated geometry/target/real cache')
        write_new(out/(label+'_arm.json'),result)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--compile-only',action='store_true')
    args=parser.parse_args();code=reuse_code()
    if args.compile_only:
        print(json.dumps(dict(status='PASS_SOURCE_COMPILE_ONLY',parent_sha256=PARENT_SHA,
                              old_main_or_run_arm_extracted=False,scientific_body_reads=0,renderer_calls=0)));return 0
    global np,torch
    import numpy as np
    import torch
    import scipy
    out=HERE/'execution_01';out.mkdir(exist_ok=False)
    started,t0=utc(),time.monotonic();decoder=None
    result=dict(status='RUNNING',started_utc=started,source_sha256=sha(Path(__file__).read_bytes()),
                parent_sha256=PARENT_SHA,conditions=[],model_calls=0,RGB_body_reads=0,get_cond_calls=0,
                evidence_kind='artificial_radial_intervention_on_existing_saved_numeric_data',new_method_validated=False)
    try:
        require(sys.byteorder=='little' and np.__version__=='1.26.4' and torch.__version__.split('+')[0]=='2.7.0','Frozen numeric environment required')
        torch.set_num_threads(8);ns=dict(globals());exec(code,ns)
        pins=dict(ns['PINS'],**PROVENANCE)
        sources={path:(ROOT/path).read_bytes() for path in pins}
        for path,raw in sources.items():require(sha(raw)==pins[path],'Pinned source/metadata changed: '+path)
        result['source_and_metadata_sha256']=pins
        result['runtime']=dict(python=sys.version,numpy=np.__version__,torch=torch.__version__,scipy=scipy.__version__,threads=torch.get_num_threads())
        with (out/'readlist.jsonl').open('x') as f:
            decoder=ns['Decoder'](ARCHIVE,f);inputs,expected=ns['load_inputs'](decoder)
        original_before=ns['fingerprint'](inputs);cls=ns['original_numeric_class'](sources)
        arms,query,result['prepared_pair']=prepare_pair(ns,cls,inputs,expected,out)
        require(ns['fingerprint'](inputs)==original_before,'Preparation changed original saved inputs')
        adapter_ns={'__name__':'_s67_exact_s61_adapter'}
        exec(compile(sources[ns['ADAPTER']],ns['ADAPTER'],'exec'),adapter_ns)
        for name in ('A','B'):
            require(time.monotonic()-t0<110,'110-second diagnostic budget exceeded')
            item={};result['conditions'].append(item)
            run_arm(name,ns,cls,arms[name],expected,query,adapter_ns['render_in_canonical_units'],out,item)
        require(time.monotonic()-t0<=110,'110-second diagnostic budget exceeded')
        a,b=result['conditions'];valid=all(x['status']=='VALID_CONTEXT_RETURN' for x in (a,b))
        if valid:
            require(a['raw_query_sha256']==b['raw_query_sha256'],'Actual raw queries differ')
            require(a['initial_threshold']==b['initial_threshold'],'Historical NMS state differs')
            same_ids=a['ordered_ids']==b['ordered_ids']
            effective=result['prepared_pair']['query_displacement_above_1e_6_px']>0
            result['comparison']=dict(same_participating_members=a['participating_sources']==b['participating_sources'],
                same_quotas=a['quotas']==b['quotas'],same_ordered_ids=same_ids,effective_query_projection_difference=effective,
                conclusion=('SELECTED_ID_SENSITIVITY_ONLY' if not same_ids else
                            'NO_SELECTED_ID_EFFECT_IN_THIS_FIXED_CASE' if effective else 'UNINFORMATIVE_NO_EFFECTIVE_PROJECTION_CHANGE'))
            result['status']='COMPLETE_FIXED_PAIR_DIAGNOSTIC'
        else:result['status']='INVALID_OR_FAILED_FIXED_PAIR'
    except Exception as error:
        result.update(status='INCOMPATIBLE_SAVED_INPUT' if isinstance(error,IncompatibleInput) else 'FAILED_DIAGNOSTIC',
                      error_type=type(error).__name__,error=str(error),incompatibility_detail=getattr(error,'detail',None),
                      traceback=traceback.format_exc())
    finally:
        result.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-t0,
                      numeric_unique_blob_count=len(decoder.reads) if decoder else 0,
                      numeric_unique_bytes_read=sum(r['nbytes'] for r in decoder.reads) if decoder else 0,
                      limitations=['No true translated observation, RGB, model or generation.',
                                   'Point-projection compatibility does not establish normal/occlusion/full-image equivalence.',
                                   'Different IDs show sensitivity, not error or benefit; same IDs reject only this fixed selected-ID explanation.',
                                   'No parameter, scene or geometry retry after observing either arm.'])
        result['artifact_sha256']={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}
        write_new(out/'receipt.json',result)
        for p in out.iterdir():
            if p.is_file():p.chmod(0o444)
    return 0 if result['status']=='COMPLETE_FIXED_PAIR_DIAGNOSTIC' else 2

if __name__=='__main__':raise SystemExit(main())
