#!/usr/bin/env python3
"""Independent S18 saved-array verification; NumPy only, no model/Torch/PIL."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import resource
import signal
import threading
import os
import sys
import time
import traceback
import zipfile
import numpy as np

ATOL = RTOL = 1e-5
PRIOR = {'s17c_manifest':'a9d74acb5d79e81696a7cb2cb665577071f47e5af19292230e768638f311c885',
         's17c_seal':'424090fd2e1de5cdcf7cd124ed893b9a1dea380cf772420cbb48e57834f31df8',
         's17c_verification':'b783a0343f268c601080d3206e1c49670a1485a074d645925ef60879f026efa8',
         's17c_metadata':'1e11d45013cf18d038a58853a11785889c0d522bdc61e6121de61fbb7451693a',
         's17c_final':'0062327c2395236c087a3cfc743a3d82d57167450f552b9b29ba379171efdc9d'}
INPUT = {'point_clouds':((2,384,512,3),'float32'),'depths':((2,384,512),'float32'),
         'confidences':((2,384,512),'float32'),'focal':((2,1),'float32'),
         'R':((2,3,3),'float32'),'t':((2,3),'float32')}
REDUCED = {'pointcloud':((2,19,25,3),'float32'),'depths':((2,19,25),'float32'),
           'confs':((2,19,25),'float32'),'c2ws':((2,4,4),'float32'),
           'focal':((2,1),'float32'),'scaled_focal':((2,1),'float32'),
           'render_focal':((2,1),'float32'),'render_pp':((2,),'int64')}
FOOTPRINT = {'input_xy':((19,25,2),'float64'),'neighbor_yx':((19,25,4,2),'int64'),
             'weights':((19,25,4),'float64')}
RENDER = {'depth':((288,512),'float32'),'surfel_index_map':((288,512),'int32'),
          'cos_value_map':((288,512),'float32')}
EXPECTED_CONTRACT = dict(device='cpu',cpu_threads=8,seed=0,numpy_version='1.26.4',dtype='float32',camera_dtype='float32',
 history_count=2,query_count=2,shrink_factor=.05,reduced_size=[19,25],radius_scale=.5,
 conf_thresh=1,depth_quantile=.999,merge_normal_threshold=.6,max_points_per_node=10,
 merge_position_threshold=None,render_width=512,render_height=288,render_focal_factor=.65,
 render_principal_point=[256,144],disk_resolution=16,context_num_frames=4,
 wall_seconds=600,monitored_rss_bytes=34359738368,external_monitor_required=True,
 model_calls=0,RGB_decodes=0,GT_reads=0,full_context_calls=0,video_generated=False)


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def aid(a):
    a=np.ascontiguousarray(a)
    return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=hashlib.sha256(a.tobytes()).hexdigest())
def require(ok,label):
    if not ok: raise ValueError(label)
def read_json(p): return json.loads(Path(p).read_text())
def write_json(p,d): Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def map_state_digest(m,sources):
    values=[dict(position_hex=p.tobytes().hex(),normal_hex=n.tobytes().hex(),
                 radius_hex=np.asarray(r,dtype=np.float32).tobytes().hex(),sources=s,color=None)
            for p,n,r,s in zip(m['positions'],m['normals'],m['radii'],sources)]
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def geometry_schema(n):
    return {'normal_map':((19,25,3),'float32'),'depth_threshold':((),'float32'),
            'valid_mask':((19,25),'bool'),'depth_pass':((19,25),'bool'),
            'confidence_pass':((19,25),'bool'),'candidate_flat_ids':((n,),'int64'),
            'candidate_positions':((n,3),'float32'),'candidate_normals':((n,3),'float32'),
            'candidate_radii':((n,),'float32'),'preflip_dot':((n,),'float32'),
            'flip_mask':((n,),'bool'),'fullgrid_view_direction_diagnostic':((19,25,3),'float32'),
            'fullgrid_flipped_normal_diagnostic':((19,25,3),'float32'),
            'fullgrid_preflip_dot_diagnostic':((19,25),'float32'),
            'fullgrid_radius_diagnostic':((19,25),'float32')}


def map_schema(n):
    return {'positions':((n,3),'float32'),'normals':((n,3),'float32'),
            'radii':((n,),'float32'),'owner_frame':((n,),'int64'),
            'owner_reduced_flat_id':((n,),'int64')}


def load_arrays(path,schema,recorded,check,report,extra_members=()):
    check(set(recorded)==set(schema),'recorded numeric domain '+path.name)
    with zipfile.ZipFile(path) as archive:
        info=archive.infolist()
        check(len(info)==len(schema)+len(extra_members) and {x.filename for x in info}=={k+'.npy' for k in schema}|{k+'.npy' for k in extra_members},'exact numeric archive members '+path.name)
        for item in info:
            key=item.filename[:-4]
            if key in schema:
                shape,dtype=schema[key]
                check(not item.flag_bits&1 and 0<=item.file_size<=int(np.prod(shape))*np.dtype(dtype).itemsize+16384,'bounded numeric member '+key)
    values={}
    with np.load(path,allow_pickle=False) as z:
        for key,(shape,dtype) in schema.items():
            a=z[key];report['array_decodes']+=1
            check(a.shape==tuple(shape) and a.dtype==np.dtype(dtype),'actual shape/dtype '+path.name+':'+key)
            check(np.isfinite(a).all(),'finite '+path.name+':'+key)
            check(aid(a)==recorded[key],'actual numeric identity '+path.name+':'+key)
            values[key]=a
    return values


def verify_math(manifest,run,meta,output,check,report,ref):
    def equal(label,a,b):
        a,b=np.asarray(a),np.asarray(b)
        same=a.shape==b.shape and np.array_equal(a,b)
        count=int(np.count_nonzero(a!=b)) if a.shape==b.shape else None
        check(same,label,mismatch_count=count)
    def close(label,a,b):
        a,b=np.asarray(a),np.asarray(b)
        check(a.shape==b.shape and np.allclose(a,b,atol=ATOL,rtol=RTOL,equal_nan=False),label,
              max_absolute_error=float(np.max(abs(a.astype(np.float64)-b.astype(np.float64)))) if a.size and a.shape==b.shape else 0.)
    prior_meta=read_json(manifest['s17c_metadata'])
    raw=load_arrays(Path(manifest['s17c_final']),INPUT,
        {k:prior_meta['array_files']['final_result.npz'][k] for k in INPUT},check,report,extra_members=('colors','pp'))
    files=meta['array_files']
    red=load_arrays(run/'reduced_inputs.npz',REDUCED,files['reduced_inputs.npz'],check,report)
    for k,source in [('pointcloud','point_clouds'),('depths','depths'),('confs','confidences')]:
        reduced,footprint=ref.resize_point05(raw[source])
        close('independent given-scale .05 bilinear '+k,red[k],reduced)
    np.savez_compressed(output/'bilinear_footprints.npz',**footprint,weights=np.full((19,25,4),.25,dtype=np.float32))
    report['bilinear_footprints']=dict(path='bilinear_footprints.npz',sha256=sha(output/'bilinear_footprints.npz'),meaning='Each reduced cell has four contributors, no unique original pixel identity.')
    provenance=load_arrays(run/'bilinear_provenance.npz',FOOTPRINT,files['bilinear_provenance.npz'],check,report)
    yy,xx=np.meshgrid(20*np.arange(19,dtype=np.int64)+9,20*np.arange(25,dtype=np.int64)+9,indexing='ij')
    expected_yx=np.stack([np.stack([yy+dy,xx+dx],axis=-1) for dy,dx in [(0,0),(0,1),(1,0),(1,1)]],axis=-2)
    equal('all four bilinear contributor indices',provenance['neighbor_yx'],expected_yx)
    equal('continuous source coordinates are scale-based',provenance['input_xy'],np.stack((xx+.5,yy+.5),axis=-1))
    equal('all four bilinear contributor weights exactly one quarter',provenance['weights'],np.full((19,25,4),.25,dtype=np.float64))
    c2w=np.tile(np.eye(4,dtype=np.float32),(2,1,1));c2w[:,:3,:3]=raw['R'];c2w[:,:3,3]=raw['t']
    equal('optical FP32 c2w assembled from optimized R/t',red['c2ws'],c2w)
    equal('original optimized focal retained',red['focal'],raw['focal'])
    equal('per-frame focal multiplication FP32',red['scaled_focal'],raw['focal']*np.float32(.05))
    rf=np.tile(np.mean(raw['focal'],axis=0,dtype=np.float32)*np.float32(.65),(2,1))
    equal('render mean focal .65 FP32 array path',red['render_focal'],rf)
    equal('fixed wider-view render principal point',red['render_pp'],np.array([256,144],dtype=np.int64))
    check(np.all(raw['depths']>0) and np.all(raw['focal']>0) and np.all(raw['confidences']>=0),'upstream positive depth/focal and nonnegative confidence')
    frames=[]
    for i in range(2):
        name=f'frame{i}_geometry.npz'
        n=files[name]['candidate_flat_ids']['shape'][0]
        check(isinstance(n,int) and 0<=n<=475,'bounded actual candidate count')
        g=load_arrays(run/name,geometry_schema(n),files[name],check,report)
        independent_normal=ref.normal_map(red['pointcloud'][i])
        close(f'frame{i} independently normalized right-cross-down',g['normal_map'],independent_normal)
        equal(f'frame{i} zero last-row normals',g['normal_map'][-1],np.zeros((25,3),dtype=np.float32))
        equal(f'frame{i} zero last-column normals',g['normal_map'][:,-1],np.zeros((19,3),dtype=np.float32))
        # Continuous normal has passed: original normal is now an explicit input
        # to exact downstream sign/mask checks, not a substitute quality oracle.
        expected=ref.candidates(red['pointcloud'][i],red['depths'][i],red['confs'][i],red['scaled_focal'][i],red['c2ws'][i],supplied_normal=g['normal_map'])
        close(f'frame{i} independent FP32 order-statistic interpolation',g['depth_threshold'],expected['depth_threshold'])
        for key in ['valid_mask','candidate_flat_ids','flip_mask']:
            equal(f'frame{i} exact '+key,g[key],expected[key])
        equal(f'frame{i} exact depth pass',g['depth_pass'],red['depths'][i]<=expected['depth_threshold'])
        equal(f'frame{i} exact confidence pass',g['confidence_pass'],red['confs'][i]>=np.float32(1))
        equal(f'frame{i} candidate XYZ is original masked reduced world point',g['candidate_positions'],red['pointcloud'][i][g['valid_mask']])
        for key in ['candidate_normals','candidate_radii','preflip_dot']:
            close(f'frame{i} independently derived '+key,g[key],expected[key])
        p=red['pointcloud'][i].reshape(-1,3);normal=g['normal_map'].reshape(-1,3)
        v=p-red['c2ws'][i,:3,3];v=v/np.maximum(ref.norm32(v),np.float32(1e-12))[:,None]
        dot=np.sum(v*normal,axis=-1,dtype=np.float32);flipped=normal.copy();flipped[dot<0]*=np.float32(-1)
        rad=(np.float32(.5)*red['depths'][i].reshape(-1)/red['scaled_focal'][i,0])/(np.float32(.2)+np.float32(.8)*abs(np.sum(v*flipped,axis=-1,dtype=np.float32)))
        for key,a in [('fullgrid_view_direction_diagnostic',v.reshape(19,25,3)),('fullgrid_flipped_normal_diagnostic',flipped.reshape(19,25,3)),('fullgrid_preflip_dot_diagnostic',dot.reshape(19,25)),('fullgrid_radius_diagnostic',rad.reshape(19,25))]:
            close(f'frame{i} diagnostic only '+key,g[key],a)
        equal(f'frame{i} full-grid diagnostic does not change original selected radius',g['candidate_radii'],g['fullgrid_radius_diagnostic'][g['valid_mask']])
        # All margins are retained, including rejected cells and zero normals.
        np.savez_compressed(output/f'frame{i}_threshold_margins.npz',depth_minus_quantile=red['depths'][i]-g['depth_threshold'],confidence_minus_one=red['confs'][i]-np.float32(1),preflip_dot=g['preflip_dot'])
        frames.append(g)
        counts=meta['frames'][i]
        check(counts['index']==i and counts['total_grid_cells']==475 and counts['candidates']==n and counts['depth_pass']==int(g['depth_pass'].sum()) and counts['confidence_pass']==int(g['confidence_pass'].sum()),f'frame{i} complete grid counts')
        equal(f'frame{i} reported depth threshold',np.asarray(counts['depth_threshold']),np.asarray(float(g['depth_threshold'])))
    maps=[];sources=[]
    for i in range(2):
        name=f'map_after_frame{i}.npz';n=files[name]['radii']['shape'][0]
        check(isinstance(n,int) and 0<=n<=950,'bounded final surfel count')
        maps.append(load_arrays(run/name,map_schema(n),files[name],check,report))
        s=read_json(run/f'map_after_frame{i}_sources.json')
        check(s['color'] is None and set(s['sources'])=={str(j) for j in range(n)},'exact no-color source mapping domain')
        sources.append([s['sources'][str(j)] for j in range(n)])
        check(all(len(v)==len(set(v)) and v and all(x in (0,1) for x in v) for v in sources[-1]),'unique ordered source lists in two-frame domain')
    g0,g1=frames;m0,m1=maps
    expected0={'positions':g0['candidate_positions'],'normals':g0['candidate_normals'],'radii':g0['candidate_radii'],'owner_frame':np.zeros(len(g0['candidate_flat_ids']),dtype=np.int64),'owner_reduced_flat_id':g0['candidate_flat_ids']}
    for key in expected0:equal('frame0 first write '+key,m0[key],expected0[key])
    check(sources[0]==[[0] for _ in range(len(m0['radii']))],'frame0 source lists exact')
    expected_sources=[v.copy() for v in sources[0]];appended=[];links=[]
    if len(m0['radii']):
        trace=read_json(run/'merge_trace.json')
        check(trace['frame']==1 and trace['normal_threshold']==.6 and trace['max_points_per_node']==10,'actual original merge settings')
        threshold,rows,tree=ref.merge_decisions(m0['positions'],m0['normals'],m0['radii'],g1['candidate_positions'],g1['candidate_normals'],g1['candidate_radii'],threshold=trace['position_threshold'])
        close('independent original mixed-precision radius threshold',np.asarray(trace['position_threshold']),np.asarray(threshold))
        records=trace['records'];check(len(records)==len(rows)==len(g1['candidate_flat_ids']),'one exact query record per new candidate')
        actual_nodes=read_json(run/'octree_nodes.json')['nodes']
        postorder=[]
        def node_order(index):
            node=tree.nodes[index]
            for child in node['children']:node_order(child)
            postorder.append(dict(center=node['center'].tolist(),half_size=node['half'],indices=None if node['ids'] is None else node['ids'].tolist(),children=len(node['children']),is_root=index==tree.root))
        node_order(tree.root)
        check(len(actual_nodes)==len(postorder),'complete original default tree node count')
        for j,(actual_node,expected_node) in enumerate(zip(actual_nodes,postorder)):
            check(actual_node['indices']==expected_node['indices'] and actual_node['children']==expected_node['children'] and actual_node['is_root']==expected_node['is_root'],'tree leaf identities and postorder child structure',node=j)
            equal('tree original mixed-precision center',actual_node['center'],expected_node['center'])
            equal('tree original half-size',np.asarray(actual_node['half_size']),np.asarray(expected_node['half_size']))
        diagnostic=[]
        for j,(actual,expected) in enumerate(zip(records,rows)):
            check(actual['candidate_index']==j and actual['reduced_flat_id']==int(g1['candidate_flat_ids'][j]),'merge candidate identity/order')
            check(actual['neighbor_indices']==expected['neighbor_indices'],'original default tree candidate order including duplicates',candidate=j)
            close('ordered original dot products',actual['normal_dots'],expected['normal_dots'])
            check(actual['actual_matched_old_id']==expected['chosen_old_id'],'first passing original ordered neighbor',candidate=j)
            expected_visits=len(expected['neighbor_indices']) if expected['chosen_old_id'] is None else expected['neighbor_indices'].index(expected['chosen_old_id'])+1
            check(actual['actual_normal_visit_count']==expected_visits,'original loop stops at captured first passing break',candidate=j)
            equal('per-query actual radius threshold',np.asarray(actual['position_threshold']),np.asarray(trace['position_threshold']))
            chosen=expected['chosen_old_id']
            if chosen is None:
                chosen=len(m0['radii'])+len(appended);appended.append(j);expected_sources.append([1])
            elif 1 not in expected_sources[chosen]:expected_sources[chosen].append(1)
            links.append(chosen)
            check(actual['final_surfel_id']==chosen and actual['action']==('append' if expected['chosen_old_id'] is None else 'merge_sources_only'),'observed break and appended final ID',candidate=j)
            diagnostic.append(dict(candidate_index=j,visited_nodes=expected['visited'],neighbor_indices=expected['neighbor_indices'],normal_dots=expected['normal_dots'],normal_threshold_margins=[v-.6 for v in expected['normal_dots']],chosen=expected['chosen_old_id']))
        check(trace['merge_count']==len(rows)-len(appended) and trace['filtered_append_count']==len(appended) and trace['old_surfel_count']==len(m0['radii']) and trace['new_candidate_count']==len(g1['candidate_flat_ids']),'complete merge/append counts')
        write_json(output/'independent_tree_queries.json',dict(threshold=threshold,consumed_validated_producer_threshold=trace['position_threshold'],tree_node_count=len(tree.nodes),records=diagnostic,scope='Exact original tree semantics, not brute-force completeness or nearest-neighbor validation.'))
    else:
        appended=list(range(len(g1['candidate_flat_ids'])));links=appended.copy();expected_sources=[[1] for _ in appended]
        check(not (run/'merge_trace.json').exists(),'no original merge if old map empty')
    for key,gkey in [('positions','candidate_positions'),('normals','candidate_normals'),('radii','candidate_radii')]:
        expected=np.concatenate((m0[key],g1[gkey][appended]),axis=0)
        equal('final first-write geometry preserved '+key,m1[key],expected)
    equal('final geometry first-writer frames',m1['owner_frame'],np.concatenate((m0['owner_frame'],np.ones(len(appended),dtype=np.int64))))
    equal('final geometry first-writer reduced identities',m1['owner_reduced_flat_id'],np.concatenate((m0['owner_reduced_flat_id'],g1['candidate_flat_ids'][appended])))
    check(sources[1]==expected_sources,'final ordered source lists from original first match only')
    expected_provenance=[]
    for i,g in enumerate(frames):
        for j,flat in enumerate(g['candidate_flat_ids']):
            expected_provenance.append(dict(frame=i,candidate_index=j,reduced_flat_id=int(flat),reduced_row=int(flat)//25,reduced_col=int(flat)%25,final_surfel_id=j if i==0 else links[j],geometry_retained=i==0 or j in appended))
    check(read_json(run/'candidate_provenance.json')['candidates']==expected_provenance,'every original candidate source cell to final ID and first-writer flag')
    check(meta['map_surfel_count']==len(m1['radii']) and meta['map_source_lists']=={str(j):s for j,s in enumerate(sources[1])},'reported final map/source identities')
    report['map_summary']=dict(frame0_candidates=len(g0['candidate_flat_ids']),frame1_candidates=len(g1['candidate_flat_ids']),final_surfels=len(m1['radii']),frame1_appended=len(appended),frame1_merged=len(g1['candidate_flat_ids'])-len(appended))
    report['queries']=[]
    base_domain={'reduced_inputs.npz','bilinear_provenance.npz','frame0_geometry.npz','frame1_geometry.npz','map_after_frame0.npz','map_after_frame1.npz'}
    if not len(m1['radii']):
        check(set(files)==base_domain and not list(run.glob('render_query*')) and not list(run.glob('votes_query*')),'empty map preserved without renderer/process artifacts')
        check(meta['status']=='NO_SURFELS' and meta.get('queries',[])==[],'empty map terminal label and zero queries')
        return files
    check(set(files)==base_domain|{'render_query0.npz','render_query1.npz'},'complete nonempty-map numeric archive domain')
    query_statuses=[]
    for q in range(2):
        name=f'render_query{q}.npz'
        actual=load_arrays(run/name,RENDER,files[name],check,report)
        expected,diagnostic=ref.render_reference(m1['positions'],m1['normals'],m1['radii'],red['c2ws'][q],red['render_focal'],red['render_pp'])
        mismatch=expected['surfel_index_map']!=actual['surfel_index_map']
        np.savez_compressed(output/f'query{q}_independent_render.npz',**expected,id_mismatch_mask=mismatch,all_id_mismatch_coordinates=np.column_stack(np.nonzero(mismatch)))
        write_json(output/f'query{q}_surfel_projection_diagnostics.json',dict(records=diagnostic))
        equal(f'query{q} full-domain independent original raster provenance',actual['surfel_index_map'],expected['surfel_index_map'])
        for k in ('depth','cos_value_map'):close(f'query{q} independent render '+k,actual[k],expected[k])
        empty=actual['surfel_index_map']<0
        check(np.all(actual['depth'][empty]==0) and np.all(actual['cos_value_map'][empty]==0),'empty pixels exact original defaults')
        check(np.all((actual['surfel_index_map']>=-1)&(actual['surfel_index_map']<len(m1['radii']))),'surfel index domain')
        votes=ref.vote_reference(actual,sources[1]);report['queries'].append(dict(query=q,visible_pixels=int((~empty).sum()),source_count=len(votes['counts']),independent_votes=votes))
        actual_votes=read_json(run/f'votes_query{q}.json')
        check_votes(actual_votes,votes,check,close,q)
        expected_status='SUCCESS' if votes['counts'] else 'NO_VISIBLE_SOURCE';query_statuses.append(expected_status)
        check(actual_votes['query_index']==q and actual_votes['status']==expected_status and actual_votes['visible_pixels']==int((~empty).sum()) and actual_votes['pixel_count']==288*512,'query index/status/full-domain counts')
        digest=map_state_digest(m1,sources[1])
        check(actual_votes['map_state_before_sha256']==actual_votes['map_state_after_sha256']==digest and actual_votes['map_state_unchanged'],'actual per-query before/after map bytes and ordered source digest')
        check(meta['queries'][q]==actual_votes,'metadata query summary identical to saved original voting receipt')
    check(meta['status']==('NO_VISIBLE_SOURCE' if 'NO_VISIBLE_SOURCE' in query_statuses else 'SUCCESS'),'terminal status retains any empty-query condition')
    return files


def check_votes(actual,expected,check,close,q):
    """Producer JSON keys are fixed by the final S18 schema contract."""
    raw=dict(expected['raw'])
    ordered=[[i,raw[i]] for i in expected['insertion_order']]
    close(f'query{q} raw source weights with first contribution twice',actual['raw_timestep_count_in_insertion_order'],ordered)
    check([p[0] for p in actual['raw_timestep_count_in_insertion_order']]==expected['insertion_order'],f'query{q} exact first-seen source insertion order')
    close(f'query{q} normalized source weights',actual['timestep_weights'],expected['weights'])
    check(actual['frame_count']==expected['counts'],f'query{q} exact original source candidate count pairs')
    close(f'query{q} raw weight sum',np.asarray(actual['raw_weight_sum']),np.asarray(np.sum(np.asarray([v for _,v in ordered],dtype=np.float64))))
    check(actual['num_retrieved_frames']==len(expected['counts']) and actual['candidate_source_ids']==[i for i,_ in expected['counts']],f'query{q} exact candidate source domain')


def check_execution(m,meta,caller,manifest_path,run,manifest_sha,check):
    for k,v in EXPECTED_CONTRACT.items():check(m['contract'].get(k,'MISSING')==v,'frozen contract '+k)
    check(meta['schema']=='s18-memory-bridge-run-v1' and meta['contract']==m['contract'],'actual producer schema and complete contract')
    check(meta['manifest_sha256']==manifest_sha and meta['source_commit']==m['source_commit'],'actual run bound to manifest and source commit')
    check(meta['numpy_version']=='1.26.4' and meta['torch_version']=='2.7.0' and meta['cpu_threads']==8 and meta['seed']==0,'actual fixed producer numerical environment')
    check(os.path.realpath(meta['executable'])==os.path.realpath(m['python']),'actual producer interpreter identity')
    check(meta['before_after_identity_pass'] and [(v['when'],v['count'],v['all_match']) for v in meta['identity_checks']]==[('before',len(m['identities']),True),('after',len(m['identities']),True)],'all frozen identities checked before and after original bridge')
    check(meta['ast_audit']['status']=='PASS' and meta['ast_audit']['count']==10,'original kernel AST audit recorded')
    check(meta['runtime_kernel_paths']==dict(memory=m['memory_kernel'],geometry=m['kernels'],retrieval=m['retrieval_kernel']),'actual loaded kernel source paths')
    for key in ('model_calls','RGB_decodes','raw_RGB_file_byte_reads','checkpoint_reads','GT_reads','full_context_calls'):
        check(meta[key]==0,'actual zero forbidden operation '+key)
    for key in ('video_generated','new_method','accuracy_evaluated'):check(meta[key] is False,'component evidence boundary '+key)
    inputs=meta['input_reads']
    check(len(inputs)==1 and inputs[0]['path']==m['s17c_final'] and inputs[0]['keys']==list(INPUT),'actual six-array input access domain')
    check(caller['status']=='PASS' and caller['returncode']==0 and caller['monitor_ok'] and caller['before_after_identity_pass'] and not caller['timed_out'] and not caller['rss_limit_exceeded'],'successful external caller and resource monitor')
    check(caller['manifest_sha256']==manifest_sha and caller['command']==[m['python'],m['runner'],'--manifest',str(manifest_path),'--output',str(run)],'actual caller command and manifest binding')
    check(caller['limits']==dict(seconds=600,rss_bytes=34359738368) and 0<=caller['maxrss']<=34359738368 and 0<=caller['elapsed_seconds']<=600,'external 600 second 32 GiB budget')
    check(0<=meta['elapsed_seconds']<=600 and 0<=meta['peak_rss_bytes']<=34359738368,'worker resource measurements')
    actual_files={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
    check(actual_files==set(meta['output_files'])|{'run_metadata.json'},'complete producer output file accounting')
    for name,identity in meta['output_files'].items():
        p=(run/name).resolve();check(run in p.parents and p.stat().st_size==identity['bytes'] and sha(p)==identity['sha256'],'actual output size and SHA '+name)
    check(set(meta['array_files'])=={p.name for p in run.glob('*.npz')},'all producer numeric archives declared')


def check_counters(meta,report,check):
    s=report['map_summary'];render_calls=2 if s['final_surfels'] else 0
    expected=dict(final_array_decodes=6,resize_calls=1,store_calls=1,pointmap_calls=2,normal_calls=2,
                  merge_calls=int(s['frame0_candidates']>0),octree_root_queries=s['frame1_candidates'] if s['frame0_candidates'] else 0,
                  render_calls=render_calls,process_calls=render_calls)
    check(meta['counters']==expected,'actual exact operator counts including empty-map branches')
    check(len(meta.get('queries',[]))==render_calls and len(meta['frames'])==2,'complete fixed two-frame and conditional query summaries')


def main():
    ap=argparse.ArgumentParser()
    for flag in ('manifest','manifest-sha256','output-seal','output-seal-sha256','model-caller','model-caller-sha256','run','output'):
        ap.add_argument('--'+flag,required=True)
    args=ap.parse_args();out=Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();report=dict(schema='s18-independent-numerical-verification-v1',status='RUNNING',started_utc=utc(),source_sha256=sha(Path(__file__)),checks=[],file_hashes=[],array_decodes=0,model_calls=0,GT_reads=0,RGB_decodes=0,raw_RGB_file_byte_reads=0,checkpoint_reads=0,torch_imports=0,atol=ATOL,rtol=RTOL)
    def check(ok,label,**details):
        report['checks'].append(dict(label=label,passed=bool(ok),**details))
        require(ok,label)
    def alarm(signum,frame):raise TimeoutError('600 second independent computation limit')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(600)
    stop=threading.Event()
    def excess(signum,frame):raise MemoryError('8 GiB independent self-RSS limit')
    signal.signal(signal.SIGUSR1,excess)
    def monitor():
        while not stop.wait(.1):
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>8589934592:
                os.kill(os.getpid(),signal.SIGUSR1);return
    watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
    try:
        check(np.__version__=='2.3.5','fixed independent NumPy2.3.5 environment')
        manifest_path=Path(args.manifest).resolve();seal_path=Path(args.output_seal).resolve();caller_path=Path(args.model_caller).resolve();run=Path(args.run).resolve()
        for role,p,d in [('bound manifest',manifest_path,args.manifest_sha256),('bound output seal',seal_path,args.output_seal_sha256),('bound model caller',caller_path,args.model_caller_sha256)]:
            check(sha(p)==d,'CLI-bound control '+p.name);report['file_hashes'].append(dict(role=role,path=str(p),sha256=d))
        m=read_json(manifest_path);seal=read_json(seal_path);caller=read_json(caller_path)
        check(m['schema']=='s18-memory-bridge-manifest-v1' and m['source_commit']=='39291e4f272f6b4f270691d930926ab5930f942e','S18 manifest schema and fixed source')
        identities=m['identities']
        helper=Path(__file__).resolve().parents[1]/'work/S18_independent/numerical_reference.py'
        for p in (Path(__file__).resolve(),helper):check(str(p) in identities and sha(p)==identities[str(p)],'frozen independent implementation '+p.name)
        report['helper_sha256']=sha(helper)
        independent_python=Path(__file__).resolve().parents[1]/'.venv/bin/python'
        check(os.path.realpath(sys.executable)==os.path.realpath(independent_python),'fixed independent interpreter path')
        for role,expected in PRIOR.items():check(identities[m[role]]==expected,'fixed prior '+role)
        for p,d in identities.items():
            path=Path(p)
            check(path.is_absolute() and path.suffix.lower() not in {'.png','.jpg','.jpeg','.pth','.pt'} and path.name not in {'groundtruth.txt','rgb.txt','depth.txt'},'explicit identity scope excludes raw pictures/weights/GT')
            check(path.suffix.lower()!='.npz' or str(path)==m['s17c_final'],'only selected upstream archive may occur in input identities')
            check(sha(path)==d,'manifest identity '+p)
        check(seal['identities'][str(manifest_path)]==args.manifest_sha256 and seal['identities'][str(caller_path)]==args.model_caller_sha256,'output seal binds manifest and caller')
        for p,d in seal['identities'].items():
            path=Path(p).resolve()
            check(path==manifest_path or path==caller_path or run in path.parents or caller_path.parent in path.parents,'S18 output seal bounded run/caller scope')
            check(path.suffix.lower() not in {'.png','.jpg','.pth','.pt'} and sha(path)==d,'sealed output identity '+str(path))
        check(sha(run/'frozen_manifest.json')==args.manifest_sha256,'saved frozen manifest identical')
        prior_seal=read_json(m['s17c_seal']);prior_ver=read_json(m['s17c_verification'])
        check(prior_ver['status']=='PASS','prior S17C independent success')
        for role in ('s17c_final','s17c_metadata','s17c_manifest'):check(prior_seal['identities'][m[role]]==PRIOR[role],'S17C seal selected member '+role)
        meta=read_json(run/'run_metadata.json')
        check(meta['status'] in ('SUCCESS','NO_SURFELS','NO_VISIBLE_SOURCE'),'producer terminal status allows integrity check')
        check_execution(m,meta,caller,manifest_path,run,args.manifest_sha256,check)
        check({str(p.resolve()) for p in run.rglob('*') if p.is_file()} <= set(seal['identities']),'output seal covers every actual producer file')
        spec=importlib.util.spec_from_file_location('s18_independent_math',helper);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
        verify_math(m,run,meta,out,check,report,ref)
        check_counters(meta,report,check)
        check('torch' not in sys.modules and 'PIL' not in sys.modules,'no producer/model/image libraries imported')
        for p,d in identities.items():check(sha(p)==d,'post-verification input identity '+p)
        check(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=8589934592 and time.monotonic()-started<=600,'independent 600s 8GiB self-monitored limits')
        report['status']='PASS';report['evidence']='Saved outputs of two already-seen model-derived cameras; component integrity, no accuracy, novelty, or complete video claim.'
    except Exception as e:
        report['status']='FAIL';report['error']=repr(e);report['traceback']=traceback.format_exc()
    finally:
        stop.set();watcher.join(timeout=.2);signal.alarm(0);report['completed_utc']=utc();report['elapsed_seconds']=time.monotonic()-started;report['peak_rss_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        report['resource_control']=dict(wall_seconds=600,rss_bytes=8589934592,interval_seconds=.1,method='in-process signal and self-RSS monitoring, not OS hard isolation')
        write_json(out/'verification.json',report)
        print(json.dumps(dict(status=report['status'],array_decodes=report['array_decodes'],checks=len(report['checks']),error=report.get('error'))))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
