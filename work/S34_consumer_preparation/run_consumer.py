#!/usr/bin/env python3
"""S34 original map/append/render/vote adapter; no inference, GA, GT or final NMS."""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
from datetime import datetime, timezone
import argparse, ast, hashlib, importlib.util, json, os, sys, time, traceback

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=Path(__file__).resolve().parent
ARMS=['old_fixed_zero','old_fixed_free_400','old_fixed_common_scale_400']
ROLES=['common_old']+ARMS
POLICY=dict(cpu_threads=8,wall_seconds=120,rss_bytes=4294967296,shrink_factor=.05,
    radius_scale=.5,conf_thresh=1,depth_quantile=.999,merge_normal_threshold=.6,
    position_threshold=None,max_points_per_node=10,render_width=512,render_height=288,
    render_focal_factor=.65,disk_resolution=16,context_num_frames=4,target_num_frames=4,
    query_frame=7,pose_depth_atol=1e-5,pose_depth_rtol=1e-5,full_context_calls=0)
SOURCE_FILES=['src/s18_original_kernels.py','src/vmem_memory_kernel.py','src/vmem_retrieval_kernel.py',
    'scripts/run_s18_memory_bridge.py','work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py',
    'work/S17C_interface_preparation/isolated_vmem_source/utils/util.py',
    'work/S17C_interface_preparation/isolated_vmem_source/configs/inference/inference.yaml',
    'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/surfel_inference.py']

def utc():return datetime.now(timezone.utc).isoformat()
def require(x,msg):
    if not x:raise ValueError(msg)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def check_hashes(ids):
    for p,h in ids.items():require(sha(p)==h,'Changed identity: '+p)
def observed_call(fn,callback,*args,break_callback=None,**kwargs):
    """Read original function locals only; original objects/results are unchanged."""
    code=getattr(fn,'__func__',fn).__code__
    require(sys.gettrace() is None,'Competing trace')
    def trace(frame,event,arg):
        if frame.f_code is not code:return None
        if event=='return':callback(frame.f_locals,arg)
        elif event=='line' and break_callback:break_callback(frame)
        return trace
    sys.settrace(trace)
    try:return fn(*args,**kwargs)
    finally:sys.settrace(None)

def source_ast_audit():
    """Reuse frozen S18 source-only AST audit, not S18 numerical runner/assertions."""
    p=ROOT/'scripts/run_s18_memory_bridge.py'
    spec=importlib.util.spec_from_file_location('s34_s18_ast_helper',p)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    base=ROOT/'work/S17C_interface_preparation/isolated_vmem_source'
    result=helper.ast_audit(dict(pipeline_source=str(base/'modeling/pipeline.py'),util_source=str(base/'utils/util.py'),
        kernels=str(ROOT/'src/s18_original_kernels.py'),memory_kernel=str(ROOT/'src/vmem_memory_kernel.py'),retrieval_kernel=str(ROOT/'src/vmem_retrieval_kernel.py')))
    def method(p,name):return next(x for x in ast.walk(ast.parse(p.read_text())) if isinstance(x,ast.FunctionDef) and x.name==name)
    for name,original in [('get_transformed_c2ws',base/'modeling/pipeline.py'),('average_camera_pose',base/'utils/util.py')]:
        require(ast.dump(method(ROOT/'src/vmem_retrieval_kernel.py',name),include_attributes=False)==ast.dump(method(original,name),include_attributes=False),'Original query AST '+name)
    result['additional_exact_methods']=['get_transformed_c2ws','average_camera_pose']
    return result

def main(manifest_path,expected_sha):
    require(sha(manifest_path)==expected_sha,'Manifest SHA')
    m=read(manifest_path)
    require(m['schema']=='s34-original-consumer-manifest-v1' and m['status']=='FROZEN','Frozen manifest')
    require(m['policy']==POLICY and list(m['packets'])==ROLES,'Fixed domain and policy')
    out=Path(m['output']);require(out==ROOT/'results/S34_original_consumer','Fixed output')
    require(not out.exists(),'Existing output refused');out.mkdir(parents=True)
    started=time.perf_counter();r=dict(status='RUNNING',started_utc=utc(),manifest_sha256=expected_sha,
        new_model=0,new_GA=0,new_clean=0,sensor_GT_bytes=0,RGB_bytes=0,full_context_calls=0,
        query_scope='Same-input self-query camera7, not future/novel-view accuracy',arms={})
    def phase(name):
        r['phase']=name;r['updated_utc']=utc();r['elapsed_seconds']=time.perf_counter()-started
        write(out/'progress.json',r);print(json.dumps(dict(phase=name,utc=utc())),flush=True)
    try:
        phase('all_input_identity_barrier')
        source_ids=m['source_sha256'];expected_sources={str(ROOT/p) for p in SOURCE_FILES}|{str(Path(__file__).resolve()),str(HERE/'protocol.md'),str(HERE/'prepare_candidate.py')}
        require(set(source_ids)==expected_sources,'Exact source domain')
        check_hashes(source_ids)
        require(os.path.realpath(sys.executable)==os.path.realpath(m['python']),'Frozen runtime')
        ids=dict(source_ids);ids[str(Path(manifest_path).resolve())]=expected_sha
        contract=m['producer_contract'];require(sha(contract['path'])==contract['sha256'],'Producer contract SHA');ids[contract['path']]=contract['sha256']
        # ALL four receipt PASS and identities precede packet byte hashes and any decoder.
        for role in ROLES:
            v=m['packets'][role];rp=Path(v['receipt'])
            require(rp==ROOT/'results/S34_geometry_producer'/role/'receipt.json','Fixed receipt path')
            require(sha(rp)==v['receipt_sha256'],'Receipt identity '+role)
            pr=read(rp);require(pr['status']=='PASS','All four packet producers must PASS: '+role)
            require(pr['contract_sha256']==contract['sha256'],'Receipt contract '+role)
            require(Path(v['path'])==rp.parent/'packet.npz' and pr['outputs']['packet.npz']==v['sha256'],'Packet receipt binding '+role)
            ids[str(rp)]=v['receipt_sha256']
        for role in ROLES:
            v=m['packets'][role];require(sha(v['path'])==v['sha256'],'Packet SHA '+role);ids[v['path']]=v['sha256']
        pose=m['given_optical_c2w'];require(Path(pose['path']).suffix=='.npy','Given camera NPY only')
        require(sha(pose['path'])==pose['sha256'],'Given pose identity');ids[pose['path']]=pose['sha256']
        write(out/'input_seal.json',dict(status='ALL_FOUR_PASS_AND_BYTES_SEALED_BEFORE_DECODE',sealed_utc=utc(),sha256=ids,
            sensor_GT_bytes=0,decoded_arrays=0,scope='Camera poses are explicitly given GT-derived controls; no sensor-depth access'))
        r['source_ast_audit']=source_ast_audit()
        for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
        sys.path.insert(0,str(ROOT))
        import numpy as np
        import torch
        import yaml
        from src import s18_original_kernels as geometry, vmem_memory_kernel as memory, vmem_retrieval_kernel as retrieval
        require(np.__version__=='1.26.4' and torch.__version__=='2.7.0','Frozen numpy/torch')
        torch.set_num_threads(8)
        for mod,rel in [(geometry,'src/s18_original_kernels.py'),(memory,'src/vmem_memory_kernel.py'),(retrieval,'src/vmem_retrieval_kernel.py')]:
            require(Path(mod.__file__).resolve()==ROOT/rel and sha(mod.__file__)==source_ids[str(ROOT/rel)],'Loaded kernel identity')
        config=yaml.safe_load((ROOT/SOURCE_FILES[6]).read_text())
        for key in ['shrink_factor','radius_scale','conf_thresh','merge_normal_threshold']:require(config['surfel'][key]==POLICY[key],'Original config '+key)
        require(config['surfel']['width']==512 and config['surfel']['height']==288 and config['model']['context_num_frames']==config['model']['target_num_frames']==4,'Original dimensions')
        def array_id(a):
            a=np.ascontiguousarray(a);return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=hashlib.sha256(a.tobytes()).hexdigest())
        def save(name,arrays):
            p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
            arrays={k:(v.detach().cpu().numpy().copy() if hasattr(v,'detach') else np.array(v,copy=True)) for k,v in arrays.items()}
            np.savez_compressed(p,**arrays)
            r.setdefault('array_schemas',{})[name]={k:array_id(v) for k,v in arrays.items()}
        phase('decode_sealed_packets')
        packets={}
        for role in ROLES:
            n=4 if role=='common_old' else 8
            shapes=dict(depth=(n,384,512),point_cloud=(n,384,512,3),conf=(n,384,512),focal=(n,1),pp=(n,2),c2w=(n,4,4))
            with np.load(m['packets'][role]['path'],allow_pickle=False) as z:
                require(set(z.files)==set(shapes),'Exact packet keys '+role);packet={k:z[k].copy() for k in shapes}
            for key,shape in shapes.items():require(packet[key].shape==shape and packet[key].dtype==np.float32 and np.isfinite(packet[key]).all(),'Packet finite FP32 schema '+role+'/'+key)
            require((packet['depth']>0).all() and (packet['focal']>0).all() and (packet['conf']>=0).all(),'Packet physical domain '+role)
            packets[role]=packet
        given=np.load(pose['path'],allow_pickle=False)
        require(given.shape==(8,4,4) and given.dtype==np.float32 and np.isfinite(given).all(),'Eight FP32 given optical cameras')
        pipeline=given.copy();pipeline[..., :, [1,2]]*=-1
        for role,packet in packets.items():
            require(np.allclose(packet['c2w'],given[:len(packet['c2w'])],atol=1e-5,rtol=1e-5),'Packet camera vs given control '+role)
            if role!='common_old':require(np.allclose(packet['depth'][:4],packets['common_old']['depth'],atol=1e-5,rtol=1e-5),'Frozen old depth roundtrip '+role)
        def map_arrays(k):
            s=k.surfels
            if not s:return dict(positions=np.empty((0,3),np.float32),normals=np.empty((0,3),np.float32),radii=np.empty(0,np.float32))
            arrays=dict(positions=np.stack([x.position for x in s]),normals=np.stack([x.normal for x in s]),radii=np.asarray([x.radius for x in s]))
            require(all(v.dtype==np.float32 for v in arrays.values()),'Map raw dtype, no conversion permitted')
            return arrays
        def geometry_ids(k):return {key:array_id(v) for key,v in map_arrays(k).items()}
        def sources(k):return {str(i):list(k.surfel_to_timestep[i]) for i in range(len(k.surfels))}
        def snapshot(k,name):
            require(set(k.surfel_to_timestep)==set(range(len(k.surfels))),'Contiguous map IDs')
            require(all(len(v)==len(set(v)) and all(0<=i<len(k.c2ws) for i in v) for v in k.surfel_to_timestep.values()),'Valid unique source indices')
            require(all(s.color is None for s in k.surfels),'Original color None')
            save(name+'/map.npz',map_arrays(k));write(out/name/'sources.json',dict(sources=sources(k),color=None))
            save(name+'/cache.npz',dict(pipeline_c2ws=np.asarray(k.c2ws),surfel_Ks=np.asarray(k.surfel_Ks),surfel_depths=np.asarray(k.surfel_depths)))
        merge_method=next(n for n in ast.walk(ast.parse((ROOT/'src/vmem_memory_kernel.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name=='merge_surfels')
        breaks={n.lineno for n in ast.walk(merge_method) if isinstance(n,ast.Break)}
        class StoreObserver:
            def __init__(self,k,tag,indices):
                self.k=k;self.tag=tag;self.indices=list(indices);self.records=[];self.current=None
                self.point_fn=k.pointmap_to_surfels;self.merge_fn=k.merge_surfels
            def point(self,*args,**kwargs):
                frame=self.indices[len(self.records)];captured={}
                surfels=observed_call(self.point_fn,lambda loc,ret:captured.update(loc),*args,**kwargs)
                mask=captured['valid_mask'];flat=torch.nonzero(mask.reshape(-1)).flatten().numpy()
                rec=dict(frame=frame,candidates=len(surfels),reduced_cells=int(mask.numel()),map_before=len(self.k.surfels),
                    depth_threshold=float(captured['depth_threshold']),matched_candidates=0,added_surfels=len(surfels),source_list_additions=0)
                require(len(surfels)==len(flat),'Candidate order')
                self.current=dict(record=rec,objects=surfels,arrays=dict(valid_mask=mask,candidate_reduced_flat_ids=flat,
                    candidate_positions=captured['positions'],candidate_normals=captured['normals'],candidate_radii=captured['radii'],
                    candidate_final_surfel_ids=np.arange(len(self.k.surfels),len(self.k.surfels)+len(surfels),dtype=np.int64)))
                self.records.append(self.current)
                return surfels
            def merge(self,*args,**kwargs):
                require(not args,'Original named merge arguments')
                before_geo=geometry_ids(self.k);before_sources=sources(self.k);new=kwargs['new_surfels'];old_count=len(self.k.surfels)
                require(kwargs['current_timestep']==self.current['record']['frame'],'Absolute appended frame IDs')
                j_by_id={id(x):j for j,x in enumerate(new)};matched={};captured={}
                def on_line(frame):
                    if frame.f_lineno in breaks:matched[j_by_id[id(frame.f_locals['new_surfel'])]]=int(frame.f_locals['idx'])
                returned=observed_call(self.merge_fn,lambda loc,ret:captured.update(loc),*args,break_callback=on_line,**kwargs)
                filtered,_=returned;require(geometry_ids(self.k)==before_geo,'Merge overwrote existing geometry')
                require(int(captured['merge_count'])==len(matched)==len(new)-len(filtered),'Original match counter')
                ids=np.full(len(new),-1,dtype=np.int64)
                for j,i in matched.items():ids[j]=i
                for j,s in enumerate(filtered):ids[j_by_id[id(s)]]=old_count+j
                require((ids>=0).all(),'Complete candidate-to-map correspondence')
                rec=self.current['record'];rec.update(matched_candidates=len(matched),added_surfels=len(filtered),
                    position_threshold=float(captured['position_threshold']),unique_matched_existing_ids=len(set(matched.values())),
                    source_list_additions=sum(len(self.k.surfel_to_timestep[i])-len(before_sources[str(i)]) for i in range(old_count)))
                self.current['arrays']['candidate_final_surfel_ids']=ids
                return returned
            def run(self,point,depth,conf,focal,cameras):
                self.k.pointmap_to_surfels=self.point;self.k.merge_surfels=self.merge
                try:self.k.store_reduced_scene(point,depth,conf,focal,cameras)
                finally:del self.k.pointmap_to_surfels;del self.k.merge_surfels
                require([x['record']['frame'] for x in self.records]==self.indices,'Exact store frame domain')
                for x in self.records:
                    frame=x['record']['frame'];save(self.tag+f'/frame_{frame}_candidates.npz',x['arrays'])
                    for s in x['objects']:require(np.isfinite(s.position).all() and np.isfinite(s.normal).all() and np.isfinite(s.radius).all(),'Original candidate nonfinite, no repair')
                write(out/self.tag/'store_trace.json',dict(frames=[x['record'] for x in self.records],
                    meaning='Counts observe original branches. Multiple candidates can match one existing surfel; source additions are separately counted. Reduced cells represent bilinear input, not one raw pixel.'))
                return [x['record'] for x in self.records]
        def append_packet(k,packet,tag,indices):
            # These cache semantics match pipeline:990-996; old Ks are intentionally retained.
            focal=packet['focal'];k.surfel_Ks.extend([focal[i].copy() for i in range(len(focal))])
            k.surfel_depths=[packet['depth'][i].copy() for i in range(len(packet['depth']))]
            cameras=k.get_transformed_c2ws()
            require(np.array_equal(cameras,given[:len(cameras)]),'Pipeline-to-optical roundtrip')
            point,depth,conf=k.resize_scene_inputs(torch.from_numpy(packet['point_cloud']),torch.from_numpy(packet['depth']),torch.from_numpy(packet['conf']))
            require(tuple(point.shape[1:])==(19,25,3) and tuple(depth.shape[1:])==(19,25),'Original .05 resize')
            save(tag+'/reduced.npz',dict(point_cloud=point,depth=depth,conf=conf,focal=focal,optical_c2w=cameras))
            return StoreObserver(k,tag,indices).run(point,depth,conf,focal,cameras)
        phase('build_common_old_map_once')
        common=geometry.OriginalGeometryKernel();common.device='cpu';common.dtype=torch.float32
        common.config=SimpleNamespace(surfel=SimpleNamespace(**config['surfel']),model=SimpleNamespace(**config['model']))
        common.surfels=[];common.surfel_to_timestep={};common.surfel_Ks=[];common.surfel_depths=[]
        common.c2ws=[x.copy() for x in pipeline[:4]]
        r['common_old_store']=append_packet(common,packets['common_old'],'common_old',range(4))
        require(len(common.surfels)>0,'Common old map empty; cannot preserve new4-only append contract')
        require(len(common.surfel_Ks)==4,'Old focal cache4');snapshot(common,'common_old')
        old_geo=geometry_ids(common);old_sources=sources(common);old_count=len(common.surfels)
        old_arrays=map_arrays(common);query_identity=None
        for arm in ARMS:
            phase(arm+'_deepcopy_append_render')
            k=deepcopy(common)
            require(k.surfels is not common.surfels and k.surfel_to_timestep is not common.surfel_to_timestep,'Deepcopy containers')
            for a,b in zip(k.surfels,common.surfels):require(a is not b and not np.shares_memory(a.position,b.position) and not np.shares_memory(a.normal,b.normal),'Deepcopy old surfel arrays')
            for i in range(old_count):require(k.surfel_to_timestep[i] is not common.surfel_to_timestep[i],'Deepcopy source lists')
            for name in ['c2ws','surfel_Ks','surfel_depths']:
                require(getattr(k,name) is not getattr(common,name) and all(not np.shares_memory(a,b) for a,b in zip(getattr(k,name),getattr(common,name))),'Deepcopy cache '+name)
            require(geometry_ids(k)==old_geo and sources(k)==old_sources,'Exact copied old map')
            k.c2ws.extend([x.copy() for x in pipeline[4:]])
            trace=append_packet(k,packets[arm],arm,range(4,8))
            require(len(k.surfel_Ks)==12 and len(k.surfel_depths)==len(k.c2ws)==8,'Original cache lengths4to12 and depths8')
            current=map_arrays(k)
            require(all(array_id(current[key][:old_count])==array_id(old_arrays[key]) for key in old_arrays),'Old committed geometry unchanged')
            for i in range(old_count):
                require(k.surfel_to_timestep[i][:len(common.surfel_to_timestep[i])]==common.surfel_to_timestep[i] and all(4<=v<8 for v in k.surfel_to_timestep[i][len(common.surfel_to_timestep[i]):]),'Old source prefix only gains new frames')
            snapshot(k,arm)
            target=torch.from_numpy(np.array([k.c2ws[7]])).to('cpu',torch.float32)
            average=retrieval.average_camera_pose(target[-k.config.model.context_num_frames//4:])
            optical=k.get_transformed_c2ws(average);target_K=np.mean(k.surfel_Ks,axis=0)
            if query_identity is None:query_identity=array_id(optical)
            require(array_id(optical)==query_identity,'Same query pose across all arms')
            save(arm+'/query_inputs.npz',dict(target_pipeline_c2w=target,average_pipeline_c2w=average,render_optical_c2w=optical,
                mean_history_focal=target_K,render_focal=np.asarray([target_K*.65]*2),render_pp=np.asarray([256,144],dtype=np.int64)))
            before=(geometry_ids(k),sources(k))
            rendered=k.render_surfels_to_image(k.surfels,optical,[target_K*.65]*2,principal_points=(256,144),image_width=512,image_height=288,disk_resolution=16)
            save(arm+'/render.npz',rendered)
            captured={};weights,quota=observed_call(k.process_retrieved_spatial_information,lambda loc,ret:captured.update(loc),rendered)
            votes=dict(status='SOURCES_PRESENT' if weights else 'NO_VISIBLE_SOURCE',query_frame=7,query_scope=r['query_scope'],
                raw_votes_in_insertion_order=[[int(i),float(v)] for i,v in captured['timestep_count'].items()],
                normalized_weights=[[int(i),float(v)] for i,v in weights],candidate_quotas=[[int(i),int(v)] for i,v in quota],
                requested_candidates=int(captured['num_retrieved_frames']),quota_sum=sum(int(v) for _,v in quota),
                expanded_candidate_source_ids=[int(i) for i,n in quota for _ in range(int(n))],
                visible_pixels=int((rendered['surfel_index_map']>=0).sum()),total_pixels=512*288,
                final_context_ids_status='NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY',final_context_ids=None,
                original_semantics='C-order votes include first-contribution double addition and original quota rounding. Candidate counts are not final context IDs or accuracy labels.')
            write(out/arm/'votes.json',votes)
            require(before==(geometry_ids(k),sources(k)),'Query mutated map')
            require(np.isfinite(rendered['depth']).all() and np.isfinite(rendered['cos_value_map']).all(),'Original render nonfinite')
            require(geometry_ids(common)==old_geo and sources(common)==old_sources and len(common.surfel_Ks)==4,'Shared common map/cache mutated')
            r['arms'][arm]=dict(status='PASS',old_surfel_count=old_count,final_surfel_count=len(k.surfels),
                total_candidates=sum(x['candidates'] for x in trace),matched_candidates=sum(x['matched_candidates'] for x in trace),
                newly_appended_surfels=sum(x['added_surfels'] for x in trace),old_geometry_unchanged=True,
                deepcopy_isolation_pass=True,focal_cache_length_before=4,focal_cache_length_after=12,visible_pixels=votes['visible_pixels'],candidate_source_count=len(weights))
            del k
            require(time.perf_counter()-started<=120,'Frozen consumer wall budget exceeded; no automatic retry')
        check_hashes(ids);require(time.perf_counter()-started<=120,'Frozen total wall budget')
        r.update(status='PASS_ORIGINAL_CONSUMER_COMPONENTS',completed_utc=utc(),elapsed_seconds=time.perf_counter()-started,
            old_map_builds=1,deepcopies=3,append_calls=3,render_calls=3,vote_calls=3,input_sha256=ids,inputs_unchanged=True,
            final_context_ids_status='NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY',scientific_scope='Observed map/render/source changes only; no retrieval-quality or video claim')
        r['outputs']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name not in ['receipt.json','progress.json']}
        write(out/'receipt.json',r)
    except Exception:
        r.update(status='FAILED_PRESERVED',completed_utc=utc(),elapsed_seconds=time.perf_counter()-started,error=traceback.format_exc())
        write(out/'receipt.json',r);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--sha256',required=True);args=p.parse_args()
    main(args.manifest,args.sha256)
