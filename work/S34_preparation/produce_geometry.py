"""S34 preparation: shared saved old4 -> original eight-image GA consumers.

Import/help are stdlib only. Scientific execution requires a separately reviewed
FROZEN contract with explicit SHA; no GT depth or network entry exists here.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import traceback
from datetime import datetime, timezone

SCHEMA='s34-shared-old4-eight-frame-consumer-v1'
ARMS=('old_fixed_free_400','old_fixed_common_scale_400')
ENDPOINTS=('old_fixed_zero',)+ARMS
FIELDS=('depth','point_cloud','conf','focal','pp','c2w')
OLD_KIND='S29_C2a_saved_MST_zero_step_plus_new_original_clean'

def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,why):
    if not ok:raise RuntimeError(why)
def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def check_identities(c,include_assets=True):
    for p,h in c['identities'].items():require(sha(p)==h,'Changed S34 source/JSON: '+p)
    if include_assets:
        for p,h in c['assets'].items():require(sha(p)==h,'Changed inherited actual input bytes: '+p)

def contract(path,expected):
    require(sha(path)==expected,'Exact S34 contract SHA');c=read(path)
    require(c['schema']==SCHEMA and c['status']=='FROZEN','Preparation candidate cannot execute')
    require(c['arms']==list(ARMS) and c['endpoints']==list(ENDPOINTS) and c['steps']==400,'Three fixed endpoints, only two400 producers')
    require(c['limits']==dict(threads=8,common_seconds=120,common_rss=4*1024**3,arm_seconds=240,arm_rss=8*1024**3,min_disk_bytes=10*1024**3),'Fixed producer resource budget')
    require(c['tolerance']==dict(atol=1e-5,rtol=1e-5,objective_atol=1e-5,objective_rtol=1e-4),'Predetermined numerical gates')
    check_identities(c);m=read(c['parent_manifest'])
    require(c['frames']==m['candidate']['frames'] and len(c['frames'])==8,'Exact existing S26B first8 ordered inputs')
    require(c['eight_heads']==m['candidate']['archives']['cut3r'] and c['old_heads']==m['candidate']['archives']['common_old_depth_original4'],'Explicit distinct old4/eight8 sources')
    old=read(c['old_inputs_seal']);camera=read(c['control_receipt'])
    require(old['saved_heads']==c['old_heads'] and old['parent_manifest_sha256']==c['parent_manifest_sha256'],'S29 actual original4 source and parent')
    require(old['control_sha256']==camera['output_sha256']==c['assets'][c['control_array']],'Identical existing eight-camera file for both sources')
    oldrec=read(c['old_receipt']);require(oldrec['status']=='PASS_INITIALIZATION_EXECUTED' and oldrec['arm']=='C2a','Real saved S29 zero-step source')
    require(oldrec['counts']==dict(MST=1,PnP=3,alignment=1,objective=1,backward=0,Adam=0,clean=0,model=0,GT=0),'Never relabel original400 as common zero')
    gate=read(c['s30_initial_gate']);require(gate['status']=='PASS' and gate['raw_exact'] and gate['objective_exact'] and gate['alignment_exact'] and gate['complete_raw_tensor_count']==33,'Actual S29/S30 saved initialization reference')
    c['_sha']=expected;c['_path']=str(Path(path).resolve());return c

def runtime(c):
    b=module(c['parent_runner'],'s34_original_s26b');m=b.manifest(c['parent_manifest_sha256'])
    np,torch=b.numeric_setup();a=b.adapter();ns,proof=a.configure_original_geometry(m['binding'])
    base=importlib.import_module('cloud_opt.dust3r_opt.base_opt')
    ref=module(m['numerical_reference'],'s34_existing_independent_math')
    b.numeric_setup()  # fixed seed after imports, as in the prior actual runs
    return b,m,np,torch,a,ns,base,ref,proof

def loaded_sources(m):
    loaded={};deps={};embedded=Path(m['binding']['embedded_root']).resolve();overlay=Path(m['binding']['overlay']).resolve()
    for name,obj in list(sys.modules.items()):
        origin=getattr(obj,'__file__',None)
        if not origin:continue
        p=Path(origin).resolve()
        if name.startswith(('cloud_opt.','dust3r.','src.dust3r.','models.','croco.')):
            require(p.is_relative_to(embedded) and m['binding']['source_identities'].get(str(p))==sha(p),'Mixed or changed geometry '+name);loaded[name]=str(p)
        if p.is_relative_to(overlay):
            require(m['dependency_identities'].get(str(p))==sha(p),'Unbound loaded overlay '+name);deps[name]=str(p)
    return dict(geometry=loaded,overlay=deps)

def load_npz(path,np):
    with np.load(path,allow_pickle=False) as z:return {key:z[key].copy() for key in z.files}

def exact(actual,expected,label):
    require(actual.shape==expected.shape and actual.dtype==expected.dtype and actual.tobytes()==expected.tobytes(),'Exact '+label)

def packet_schema(v,n,np):
    shapes=dict(depth=(n,384,512),point_cloud=(n,384,512,3),conf=(n,384,512),focal=(n,1),pp=(n,2),c2w=(n,4,4))
    require(set(v)==set(FIELDS),'Exactly six consumer fields')
    for key,shape in shapes.items():require(v[key].shape==shape and v[key].dtype==np.float32 and np.isfinite(v[key]).all(),'FP32 finite packet '+key)
    require((v['depth']>0).all() and (v['focal']>0).all() and (v['conf']>=0).all(),'Positive metric depth/focal, nonnegative conf')

def backprojection(v,np):
    yy,xx=np.indices((384,512),dtype=np.float64);maximum=0.
    for i,d in enumerate(v['depth'].astype(float)):
        f=float(v['focal'][i,0]);p=v['pp'][i]
        cam=np.stack([(xx-p[0])*d/f,(yy-p[1])*d/f,d],-1)
        world=cam@v['c2w'][i,:3,:3].astype(float).T+v['c2w'][i,:3,3]
        maximum=max(maximum,float(np.abs(world-v['point_cloud'][i]).max()))
        require(np.allclose(world,v['point_cloud'][i],atol=1e-5,rtol=1e-5),'Independent depth-to-world packet')
    return maximum

def clean_copy(v,np,torch,base,ref):
    """One original default clean on copies; never mutate a live optimizer."""
    packet_schema(v,len(v['depth']),np);before={k:x.copy() for k,x in v.items()}
    t=lambda a:torch.from_numpy(a.copy())
    c2w=t(v['c2w']);K=torch.zeros((len(c2w),3,3),dtype=torch.float32)
    K[:,0,0]=t(v['focal'][:,0]);K[:,1,1]=t(v['focal'][:,0]);K[:,:2,2]=t(v['pp']);K[:,2,2]=1
    with torch.no_grad():
        conf=base.clean_pointcloud(list(t(v['conf'])),K,base.inv(c2w),list(t(v['depth'])),list(t(v['point_cloud'])))
    result={k:x.copy() for k,x in v.items()};result['conf']=np.stack([x.detach().numpy().copy() for x in conf])
    for key in v:exact(v[key],before[key],'clean input unchanged '+key)
    expected,visits,margins=ref.clean_reference(v['conf'],v['depth'],v['point_cloud'],v['focal'],v['pp'],v['c2w'][:,:3,:3],v['c2w'][:,:3,3])
    exact(result['conf'],expected,'original clean and independent FP32 reference all pixels')
    del margins
    return result,dict(original_clean_calls=1,independent_clean_mismatch_pixels=0,visits=visits,
        changed_pixels=[int(np.count_nonzero(a!=z)) for a,z in zip(v['conf'],result['conf'])],independent_backprojection_max_abs=backprojection(result,np))

def receipt_outputs(out):return {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'}

def begin(c,name):
    out=Path(c['output_root'])/name;require(not out.exists(),'Never overwrite or repeat '+name);out.mkdir(parents=True)
    rec=dict(status='RUNNING',started_utc=utc(),contract_sha256=c['_sha'],manifest_sha256=c['parent_manifest_sha256'],
        endpoint=name,sensor_GT_read=False,new_model=0,outputs={})
    write(out/'receipt.json',rec);return out,rec

def failure(out,rec,e):
    rec.update(status='FAILED',completed_utc=utc(),error=repr(e),partial_artifacts_retained=True)
    write(out/'receipt.json',rec);(out/'traceback.txt').write_text(traceback.format_exc())

def common_worker(c):
    out,rec=begin(c,'common_old')
    try:
        b,m,np,torch,a,ns,base,ref,proof=runtime(c)
        raw=load_npz(c['old_raw'],np);meta=read(c['old_raw_metadata']);decoded=load_npz(c['old_decoded'],np)
        require(set(raw)==set(meta) and len(raw)==33,'Full actual S29 raw snapshot')
        for key,value in raw.items():
            require(list(value.shape)==meta[key]['shape'] and str(value.dtype)==meta[key]['dtype'] and hashlib.sha256(value.tobytes()).hexdigest()==meta[key]['sha256'],'Old saved raw identity '+key)
        v={k:decoded[k].copy() for k in FIELDS if k!='conf'}
        v['conf']=np.stack([raw['parameter::im_conf.'+str(i)] for i in range(4)])
        packet_schema(v,4,np);cameras=np.load(c['control_array'],allow_pickle=False)
        require(cameras.shape==(8,4,4) and cameras.dtype==np.float32,'Full original control array')
        require(np.allclose(v['c2w'],cameras[:4],atol=1e-5,rtol=1e-5),'Saved old4 and common optical camera prefix')
        for i in range(4):exact(torch.from_numpy(raw['parameter::im_depthmaps.'+str(i)]).exp().numpy(),v['depth'][i],'Old raw log -> original FP32 depth')
        losses=[ref.pair_objective(v['point_cloud'][[0,j]],raw[f'parameter::pred_i.0_{j}'],raw[f'parameter::pred_j.0_{j}'],
            raw[f'parameter::conf_i.0_{j}'],raw[f'parameter::conf_j.0_{j}'],decoded['pw_poses'][j-1],decoded['adaptors'][j-1]) for j in range(1,4)]
        require(np.isclose(np.mean(losses),float(decoded['objective']),atol=1e-5,rtol=1e-4),'Saved zero original objective independent replay, no new objective call')
        np.savez_compressed(out/'preclean_packet.npz',**v)
        packet,clean=clean_copy(v,np,torch,base,ref)
        np.savez_compressed(out/'output.npz',**packet);shutil.copyfile(out/'output.npz',out/'packet.npz')
        seal=dict(contract_sha256=c['_sha'],parent_manifest_sha256=c['parent_manifest_sha256'],provenance_kind=OLD_KIND,
            source_receipt=c['old_receipt'],source_receipt_sha256=sha(c['old_receipt']),saved_old4_heads=c['old_heads'],
            control_c2w_sha256=sha(c['control_array']),sensor_depth_used=False,
            old4_vs_eight_head_equality='NOT_CLAIMED; different original4 and cut3r archives, common external old packet')
        write(out/'inputs_seal.json',seal);write(out/'clean_receipt.json',clean)
        for p,h in m['identities'].items():require(sha(p)==h,'Changed parent identity: '+p)
        check_identities(c)
        rec.update(status='PASS',completed_utc=utc(),producer_kind=OLD_KIND,inputs_seal_sha256=sha(out/'inputs_seal.json'),
            depth_tensor_sha256=a.tensor_sha256(torch.from_numpy(packet['depth'])),control_pose_prefix_tensor_sha256=a.tensor_sha256(torch.from_numpy(cameras[:4].copy())),
            new_MST=0,new_PnP=0,new_Adam=0,new_backward=0,new_clean=1,new_objective=0,
            inherited_S29_objective=float(decoded['objective']),independent_saved_objective=float(np.mean(losses)),
            loaded_modules=loaded_sources(m),original_source_proof=proof,outputs=receipt_outputs(out))
        write(out/'receipt.json',rec)
    except BaseException as e:failure(out,rec,e);raise

def derive_observer(s30,s28_path):
    """Reuse S28/S30 instrumentation, with only explicit mixed-depth routing."""
    _,old,_=s30.derive_observer(s28_path);new=copy.deepcopy(old)
    counts=dict(callback=0,loop=0,gradient_list=0,gradient_check=0)
    labels={'s30_initialization':'s34_initialization','s30_gradient_steps':'s34_gradient_steps',
        's30_objective_forward_counts':'s34_objective_forward_counts','S30_first_step_gate_passed':'S34_first_step_gate_passed'}
    class Adapt(ast.NodeTransformer):
        def visit_Name(self,n):
            if n.id=='verify_s29_initial_state':n.id='initial_gate';counts['callback']+=1
            return n
        def visit_For(self,n):
            if ast.unparse(n.iter)=='self.scene.im_depthmaps':
                require(ast.unparse(n.body[0]).startswith("require((p.grad is None) == False"),'Original all-trainable check')
                counts['loop']+=1
                return ast.parse("for index,p in enumerate(self.scene.im_depthmaps):\n    require((p.grad is None)==(index<4),'Mixed old4 frozen/new4 connected before Adam')").body[0]
            return self.generic_visit(n)
        def visit_Assign(self,n):
            if ast.unparse(n)=="depth_grad = [gs['im_depthmaps.' + str(i)] for i in range(4)]":
                counts['gradient_list']+=1;return ast.parse("depth_grad=[gs['im_depthmaps.'+str(i)] for i in range(8)]").body[0]
            return self.generic_visit(n)
        def visit_Expr(self,n):
            if ast.unparse(n).startswith("require(all((v['grad_is_none'] == False for v in depth_grad))"):
                counts['gradient_check']+=1
                return ast.parse("require(all(v['grad_is_none']==(i<4) for i,v in enumerate(depth_grad)),'All8 mixed-depth gradient route')").body[0]
            return self.generic_visit(n)
        def visit_keyword(self,n):
            if n.arg=='reference_S29_raw_exact':n.arg='matched_current_eight_frame_initial_state'
            if n.arg=='s29_initialization_path_preserved':n.arg='common_C2a_initialization_path'
            return self.generic_visit(n)
        def visit_Constant(self,n):
            if isinstance(n.value,str) and n.value in labels:n.value=labels[n.value]
            return n
    new=Adapt().visit(new);ast.fix_missing_locations(new)
    require(counts==dict(callback=1,loop=1,gradient_list=1,gradient_check=1),'Only mixed4/4 routing and initial reference callback')
    return old,new

def raw_keys(n):
    parameters={'pw_poses','pw_adaptors','im_poses','im_focals','im_pp'}
    parameters|={f'{kind}.0_{j}' for kind in ('pred_i','pred_j','conf_i','conf_j') for j in range(1,n)}
    parameters|={f'{kind}.{i}' for kind in ('im_conf','im_depthmaps') for i in range(n)}
    buffers={'_pp','_grid','_weight_i','_weight_j','_stacked_pred_i','_stacked_pred_j','_ei','_ej'}
    return {'parameter::'+k for k in parameters}|{'buffer::'+k for k in buffers}

def scale_state(o):
    s=o.scene;t=o.T
    require(s.norm_pw_scale is False and s.pw_poses.shape==(7,8),'Original seven edges and normFalse')
    with t.no_grad():
        ell=s.pw_poses[:,-1];effective=s.get_pw_scale();raw=ell.exp();factor=s.get_pw_norm_scale_factor()
        require(effective.shape==(7,) and t.isfinite(effective).all() and (effective>0).all(),'Seven positive effective scales')
        expected=s._get_poses(s.pw_poses).clone();expected[:,:3]*=effective.view(-1,1,1)
        require(t.equal(s.get_pw_poses(),expected),'Original entire3x4 effective scale')
        if o.arm==ARMS[1]:
            require(s.get_pw_norm_scale_factor is o.factor_callable,'Actual constrained instance factor')
            require(abs(float(effective.log().mean()-o.m0))<=1e-5,'Initial effective logmean remains fixed')
            require(t.allclose(effective/effective[0],raw/raw[0],atol=1e-5,rtol=1e-5),'Relative seven edge scales retained')
        else:require(float(factor)==1.0,'Original free normFalse factor')
        return dict(raw_log_mean=float(ell.mean()),effective_log_mean=float(effective.log().mean()),factor=float(factor),
            fixed_initial_log_mean=float(o.m0),effective_scales=effective.tolist(),full_3x4_exact=True)

def initial_gate(o,c,arm,loss_before,np):
    require(o.n==8 and o.old is not None and o.mst_calls==1 and o.steps==o.adam_steps==0,'Mixed8 initial gate before first Adam')
    require(set(o.initial_arrays)==set(o.initial_meta)==raw_keys(8),'Complete exact57 names including consumed heads/weights')
    o.check_fixed(o.scene)
    for name,t in o.params(o.scene).items():require(o.T.equal(t,o.frozen[name]),'MST cannot reset fixed old parameter '+name)
    current=load_npz(o.out/'initial_decoded.npz',np)
    reference='REFERENCE_ARM'
    if arm==ARMS[1]:
        prior=Path(c['output_root'])/ARMS[0];receipt=read(prior/'receipt.json')
        require(receipt['status']=='PASS' and receipt['contract_sha256']==c['_sha'],'Free400 source fully sealed first')
        for filename in ('initial_raw.npz','initial_raw_metadata.json','initial_decoded.npz','controlled_alignment.npz'):
            require(sha(prior/filename)==receipt['outputs'][filename],'First arm full initial seal '+filename)
        require(read(prior/'initial_raw_metadata.json')==o.initial_meta,'All57 names/shape/dtype/flags/rawSHA')
        raw=load_npz(prior/'initial_raw.npz',np);require(set(raw)==set(o.initial_arrays),'Same full raw set')
        for key,v in raw.items():exact(o.initial_arrays[key],v,'Cross-arm raw '+key)
        old=load_npz(prior/'initial_decoded.npz',np);require(set(old)==set(current),'Same decoded field set')
        for key,v in old.items():exact(current[key],v,'Cross-arm decoded '+key)
        oldalign=load_npz(prior/'controlled_alignment.npz',np);require(set(oldalign)==set(o.alignment_values),'Same full alignment set')
        for key,v in oldalign.items():exact(o.alignment_values[key],v,'Cross-arm alignment '+key)
        reference='ALL57_RAW_AND_DECODED_EXACT'
    exact(current['objective'],loss_before,'Same initial objective checkpoint')
    scene=o.scene;torch=o.T;o.m0=scene.pw_poses[:,-1].detach().mean().clone()
    if arm==ARMS[1]:
        require(not scene.pw_adaptors.requires_grad,'Original frozen adaptors')
        before={key:getattr(scene,key)().detach().clone() for key in ('get_pw_scale','get_pw_poses','get_adaptors')}
        def factor():
            answer=(o.m0-scene.pw_poses[:,-1].mean()).exp()
            if torch.is_grad_enabled():require(answer.requires_grad,'Current seven-edge mean stays differentiable')
            return answer
        o.patch(scene,'get_pw_norm_scale_factor',lambda old:factor);o.factor_callable=factor
        require(float(factor().detach())==1.0,'No initial factor jump')
        for key,v in before.items():require(torch.equal(getattr(scene,key)(),v),'Initial factor preserves '+key)
    o.scale_rows=0
    report=dict(status='PASS',contract_sha256=c['_sha'],arm=arm,raw_count=57,
        cross_arm_initialization=reference,zero_source='same-memory free MST checkpoint, not historical S29 scene',
        mixed_flags=[False]*4+[True]*4,scale=scale_state(o))
    write(o.out/'s34_initial_gate.json',report);o.report['s34_initial_gate']=report

def observer_type(b,r,s30,c,arm):
    _,node=derive_observer(s30,c['s28_runner']);namespace=dict(vars(r));namespace['initial_gate']=initial_gate
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__))+'::mixed_observer','exec'),namespace)
    Parent=namespace['observer_type'](b,c,arm)
    class MixedObserver(Parent):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.arm=arm;self.backward_calls=0;self.alignment_calls=0;self.preset_objects=None
        def check_fixed(self,s):
            t=self.T
            require(s.im_poses.requires_grad is False and s.norm_pw_scale is False,'All cameras frozen and normFalse')
            require([p.requires_grad for p in s.im_depthmaps]==[False]*4+[True]*4,'Old4 false/new4 true')
            require(s.im_focals.requires_grad and not s.im_pp.requires_grad,'All8 focal trainable and pp frozen')
            require(t.allclose(s.get_im_poses(),self.cameras,atol=1e-5,rtol=1e-5),'Common optical cameras')
            actual=t.stack(s.get_depthmaps()[:4]);require(t.allclose(actual,self.old,atol=1e-5,rtol=1e-5),'Old metric depth log/exp tolerance')
            keys={'im_poses','im_pp'}|{f'im_depthmaps.{i}' for i in range(4)}
            current={key:value for key,value in s.named_parameters() if key in keys}
            require(set(current)==keys and all(p.grad is None for p in current.values()),'Frozen old/camera/pp gradient None')
            if self.preset_objects is None:
                self.preset_objects=current;self.preset_values={k:v.detach().clone() for k,v in current.items()}
                self.report['old_log_exp_max_abs']=float((actual-self.old).abs().max())
            for key,p in current.items():require(p is self.preset_objects[key] and t.equal(p,self.preset_values[key]),'Preset identity/raw old/camera/pp freeze '+key)
        def install(self):
            super().install();init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses');base=importlib.import_module('cloud_opt.dust3r_opt.base_opt')
            def alignment(old):
                def call(src,target):
                    require(self.alignment_calls==0,'One original Sim3 registration');self.alignment_calls+=1
                    s0,R0,T0=old(src,target);s=1.0 if isinstance(s0,float) else s0.new_tensor(1.0)
                    T=target[:,:3,3].mean(0)-s*(R0@src[:,:3,3].mean(0))
                    self.alignment_values=dict(source_c2w=b.array(src),target_c2w=b.array(target),s0=b.array(s0),R0=b.array(R0),T0=b.array(T0),s_used=b.array(s),R_used=b.array(R0),T_used=b.array(T))
                    np=importlib.import_module('numpy');np.savez_compressed(self.out/'controlled_alignment.npz',**self.alignment_values)
                    return s,R0,T
                return call
            self.patch(init,'align_multiple_poses',alignment)
            def backward(old):
                def call(tensor,*args,**kw):
                    require(self.scene is not None and self.mst_calls==1,'Backward only after real MST')
                    result=old(tensor,*args,**kw);self.backward_calls+=1;return result
                return call
            self.patch(self.T.Tensor,'backward',backward)
            def trace(old):
                def call(scene,index,*args,**kw):
                    before=scale_state(self);result=old(scene,index,*args,**kw);after=scale_state(self)
                    require(index==self.scale_rows and self.backward_calls==self.adam_steps==index+1,'One actual backward/Adam per step')
                    self.scale_rows+=1
                    with (self.out/'s34_scale_trace.jsonl').open('a') as f:f.write(json.dumps(dict(iteration=index,before=before,after=after,utc=utc()),allow_nan=False)+'\n')
                    if index==399:self.report['s34_actual_counts']=dict(backward=self.backward_calls,Adam=self.adam_steps,MST=self.mst_calls,PnP=len(self.report['pnp_calls']),alignment=self.alignment_calls,scale_rows=self.scale_rows)
                    return result
                return call
            self.patch(base,'global_alignment_iter',trace)
    return MixedObserver

def derive_worker(path):
    tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='ga_worker']
    require(len(nodes)==1,'Unique original eight-frame producer');old=nodes[0];new=copy.deepcopy(old)
    require(ast.unparse(new.body[0])=="require(mode in ('cut3r', 'ttt3r', 'filt3r'), 'S26B never reruns common_old GA')",'Original guard')
    new.body[0]=ast.parse("require(mode in ('old_fixed_free_400','old_fixed_common_scale_400'),'S34 two new8 mixed-depth400 arms')").body[0]
    counts=dict(archive=0,ga=0)
    class Route(ast.NodeTransformer):
        def visit_Assign(self,n):
            if any(isinstance(t,ast.Name) and t.id=='name' for t in n.targets):
                require(ast.unparse(n.value)=="'common_old_depth_original4' if mode == 'common_old' else mode",'Original archive route')
                counts['archive']+=1;n.value=ast.Constant('cut3r')
            return self.generic_visit(n)
        def visit_Call(self,n):
            if ast.unparse(n.func)=='a.run_original_ga':
                counts['ga']+=1
                return ast.parse('run_s34_ga(ns,output,control_c2ws=cameras,old_depth=old,output_dir=out)',mode='eval').body
            return self.generic_visit(n)
    new=Route().visit(new);ast.fix_missing_locations(new)
    require(counts==dict(archive=1,ga=1),'Only explicit guard/archive/provenance GA dispatch changes')
    return old,new

def run_ga(c,ns,output,*,control_c2ws,old_depth,output_dir):
    import torch
    prior=read(Path(c['output_root'])/'common_old/receipt.json')
    require(prior['status']=='PASS' and prior['producer_kind']==OLD_KIND and prior['contract_sha256']==c['_sha'],'Explicit S29 zero common packet provenance')
    require(len(output['view2']['idx'])==7 and control_c2ws.shape==(8,4,4) and old_depth.shape==(4,384,512),'Full8 with old4 condition')
    require(control_c2ws.dtype==old_depth.dtype==torch.float32 and control_c2ws.device.type==old_depth.device.type=='cpu','CPU FP32 common conditions')
    require(torch.isfinite(old_depth).all() and (old_depth>0).all(),'Positive common old depth')
    return ns['prepare_output'](output,control_c2ws.detach().clone(),old_depth.detach().clone(),lr=.01,niter=400,
        outdir=str(output_dir),device='cpu',save_flag=False)

def zero_from_free(c,b,m,np,torch):
    out,record=begin(c,ENDPOINTS[0])
    try:
        prior=Path(c['output_root'])/ARMS[0];r=read(prior/'receipt.json')
        require(r['status']=='PASS' and r['contract_sha256']==c['_sha'],'Zero snapshot producer completed without failed constraints')
        for file in ('initial_raw.npz','initial_decoded.npz','initial_raw_metadata.json'):
            require(sha(prior/file)==r['outputs'][file],'Saved zero source seal '+file)
        raw=load_npz(prior/'initial_raw.npz',np);decoded=load_npz(prior/'initial_decoded.npz',np)
        require(set(raw)==raw_keys(8),'All57 raw fields behind zero endpoint')
        v={k:decoded[k].copy() for k in FIELDS if k!='conf'};v['conf']=np.stack([raw[f'parameter::im_conf.{i}'] for i in range(8)])
        base=importlib.import_module('cloud_opt.dust3r_opt.base_opt');ref=module(m['numerical_reference'],'s34_zero_independent_reference')
        np.savez_compressed(out/'preclean_packet.npz',**v)
        packet,clean=clean_copy(v,np,torch,base,ref)
        losses=[ref.pair_objective(v['point_cloud'][[0,j]],raw[f'parameter::pred_i.0_{j}'],raw[f'parameter::pred_j.0_{j}'],
            raw[f'parameter::conf_i.0_{j}'],raw[f'parameter::conf_j.0_{j}'],decoded['pw_poses'][j-1],decoded['adaptors'][j-1]) for j in range(1,8)]
        require(np.isclose(np.mean(losses),float(decoded['objective']),atol=1e-5,rtol=1e-4),'Zero saved original objective independent formula')
        np.savez_compressed(out/'output.npz',**packet);shutil.copyfile(out/'output.npz',out/'packet.npz')
        write(out/'clean_receipt.json',clean)
        write(out/'inputs_seal.json',dict(contract_sha256=c['_sha'],zero_origin='same-memory initial snapshot in actual free400 worker before any update',
            source_receipt_sha256=sha(prior/'receipt.json'),initial_raw_sha256=sha(prior/'initial_raw.npz'),initial_decoded_sha256=sha(prior/'initial_decoded.npz'),
            common_old_receipt_sha256=sha(Path(c['output_root'])/'common_old/receipt.json'),sensor_depth_used=False))
        check_identities(c)
        record.update(status='PASS',completed_utc=utc(),producer_kind='SAME_MEMORY_NEW8_ZERO_COPY_PLUS_NEW_ORIGINAL_CLEAN',
            new_MST=0,new_PnP=0,new_Adam=0,new_backward=0,new_clean=1,new_objective=0,
            inherited_initial_objective=float(decoded['objective']),independent_objective=float(np.mean(losses)),
            loaded_modules=loaded_sources(m),outputs=receipt_outputs(out))
        write(out/'receipt.json',record)
    except BaseException as e:failure(out,record,e);raise

def arm_worker(c,arm):
    require(arm in ARMS,'Only new two400 arms');b=module(c['parent_runner'],'s34_original_eight_producer')
    m=b.manifest(c['parent_manifest_sha256']);r=module(c['s28_runner'],'s34_s28_instrumentation');s30=module(c['s30_runner'],'s34_s30_derivation')
    common=Path(c['output_root'])/'common_old';old=read(common/'receipt.json');old_receipt_sha=sha(common/'receipt.json')
    require(old['status']=='PASS' and old['contract_sha256']==c['_sha'] and old['producer_kind']==OLD_KIND,'Shared S29 old packet must be complete')
    for rel,h in old['outputs'].items():require(sha(common/rel)==h,'Common packet complete output identity '+rel)
    b.OUT=Path(c['output_root']);b.SceneObserver=observer_type(b,r,s30,c,arm)
    b.run_s34_ga=lambda ns,output,**kw:run_ga(c,ns,output,**kw)
    out=b.OUT/arm;original_write=b.write
    def bound_write(path,value):
        path=Path(path)
        if path.parent==out and path.name in ('receipt.json','inputs_seal.json'):
            value=dict(value,contract_sha256=c['_sha'],evidence_scope='S34 known eight-photo saved-head real consumer control; fixed old4/new4 trainable, no novelty/video claim')
            if path.name=='receipt.json' and value.get('status')=='PASS':
                counts=value['observer']['s34_actual_counts']
                require(counts==dict(backward=400,Adam=400,MST=1,PnP=7,alignment=1,scale_rows=400),'Full actual new8 operation budget')
                require(value['observer']['s34_gradient_steps']==400 and value['clean_calls']==1,'All mixed gradients and original once clean')
                require(value['observer']['s34_objective_forward_counts']==dict(optimization=400,patch_boundary_no_update=2,postfinal_no_update=1,total=403),'Fixed objective count')
                check_identities(c)
                for p,h in m['identities'].items():require(sha(p)==h,'Parent changed during S34 '+p)
                require(sha(common/'receipt.json')==old_receipt_sha,'Common receipt unchanged during arm')
                for rel,h in old['outputs'].items():require(sha(common/rel)==h,'Shared old source changed '+rel)
                shutil.copyfile(out/'output.npz',out/'packet.npz');value['outputs']['packet.npz']=sha(out/'packet.npz')
                value.update(endpoint=arm,new_MST=1,new_PnP=7,new_Adam=400,new_backward=400,new_clean=1,new_model=0,new_objective=403,
                    common_old_receipt_sha256=sha(common/'receipt.json'),producer_kind='NEW_EIGHT_IMAGE_GA_FROM_FIXED_S29_OLD_DEPTH',
                    common_scale_constraint=arm==ARMS[1],ordinary_baseline_not_novelty=True)
        return original_write(path,value)
    b.write=bound_write
    _,node=derive_worker(c['parent_runner'])
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__))+'::original_eight_ga','exec'),vars(b))
    b.ga_worker(m,arm)
    if arm==ARMS[0]:zero_from_free(c,b,m,importlib.import_module('numpy'),importlib.import_module('torch'))

def dispatch(c,path):
    b=module(c['parent_runner'],'s34_reused_resource_supervisor');b.WORK=Path(c['execution_root']);b.WORK.mkdir(parents=True,exist_ok=True)
    target=b.WORK/'producer_dispatch_receipt.json';require(not target.exists(),'No repeated S34 producer dispatch')
    rec=dict(status='RUNNING',started_utc=utc(),contract_sha256=c['_sha'],stages=[])
    write(target,rec)
    try:
        stages=[('common',None,c['limits']['common_seconds'],c['limits']['common_rss'])]+[('arm',arm,c['limits']['arm_seconds'],c['limits']['arm_rss']) for arm in ARMS]
        for kind,arm,seconds,rss in stages:
            command=[sys.executable,str(Path(__file__).resolve()),kind,'--contract',str(path),'--sha256',c['_sha']]
            if arm is not None:command+=['--arm',arm]
            b.supervised(command,arm or 'common_old',seconds,rss);rec['stages'].append(arm or 'common_old');write(target,rec)
        seals={}
        for name in ('common_old',)+ENDPOINTS:
            folder=Path(c['output_root'])/name;p=folder/'receipt.json';r=read(p)
            require(r['status']=='PASS' and r['contract_sha256']==c['_sha'],'All four packet producers must finish')
            for rel,h in r['outputs'].items():require(sha(folder/rel)==h,'Final producer barrier '+name+'/'+rel)
            seals[name]=dict(receipt=str(p),receipt_sha256=sha(p),packet=str(folder/'packet.npz'),packet_sha256=r['outputs']['packet.npz'])
        rec.update(status='PASS_ALL_PACKETS_SEALED',completed_utc=utc(),producer_seals=seals,
            new_MST=2,new_PnP=14,new_Adam=800,new_backward=800,new_clean=4,new_model=0,new_objective=806,
            next='Separate original consumer may read all four packets; no GT depth or default latent/NMS context here')
        write(target,rec)
    except BaseException as e:
        rec.update(status='FAILED_PRODUCER_BARRIER',completed_utc=utc(),error=repr(e),partial_producers_preserved=True,consumer_and_scoring_eligible=False)
        write(target,rec);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['common','arm','dispatch'])
    parser.add_argument('--arm',choices=ARMS);parser.add_argument('--contract',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();c=contract(args.contract,args.sha256)
    if args.command=='common':common_worker(c)
    elif args.command=='arm':arm_worker(c,args.arm)
    else:dispatch(c,args.contract)
