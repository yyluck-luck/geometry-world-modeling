"""S29 draft: C2t/C2a original common4 initializations, no optimizer or GT.

No work on import. Runtime requires a root-frozen exact contract SHA.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback


def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,why):
    if not ok:raise RuntimeError(why)
def write(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(p)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def load_contract(path,expected):
    require(sha(path)==expected,'Exact frozen S29 contract SHA required')
    c=read(path)
    require(c['status']=='FROZEN' and c['schema']=='s29-init-scale-controls-v1','Candidate cannot execute')
    require(c['arms']==['C2t','C2a'] and c['per_arm_seconds']==60 and c['per_arm_rss_bytes']==4*1024**3,'Frozen two-arm resources')
    require(c['counts_per_arm']==dict(MST=1,PnP=3,alignment=1,objective=1,backward=0,Adam=0,clean=0,model=0,GT=0),'Zero-step count contract')
    require(c['tolerance']==dict(atol=1e-5,rtol=1e-5),'No tolerance change')
    for p,h in c['identities'].items():require(sha(p)==h,'Changed direct identity: '+p)
    c['_sha']=expected;return c


class InitializationComplete(BaseException):
    """Expected sentinel after initialization and exactly one no-grad objective."""


def worker(c,arm):
    require(arm in c['arms'],'Unknown arm')
    out=Path(c['output_root'])/arm;require(not out.exists(),'Never overwrite or repeat initialization')
    out.mkdir(parents=True)
    counts=dict(MST=0,PnP=0,alignment=0,objective=0,backward=0,Adam=0,clean=0,model=0,GT=0)
    receipt=dict(status='RUNNING',started_utc=utc(),contract_sha256=c['_sha'],arm=arm,counts=counts,
                 evidence_scope='New controlled MST initialization only, no optimization or accuracy measurement')
    write(out/'receipt.json',receipt);patches=[]
    try:
        b=module(c['parent_runner'],'s29_original_context')
        r=module(c['s28_runner'],'s29_saved_state_helpers')
        m=b.manifest(c['parent_manifest_sha256'])
        control=read(c['control_receipt'])
        require(control['status']=='PASS' and control['manifest_sha256']==c['parent_manifest_sha256'],'Existing camera control seal')
        require(sha(c['control_camera'])==control['output_sha256'],'Camera bytes unchanged')
        np,torch,a,ns,views,proof=b.original_context(m)
        cameras=torch.from_numpy(np.load(c['control_camera'],allow_pickle=False)[:4].copy())
        records=m['candidate']['archives']['common_old_depth_original4']
        require(len(records)==4 and len(views)==8,'Original common4 with eight-view preparation')
        predictions=a.load_saved_predictions(records);output=a.assemble_saved_output(ns,views[:4],predictions)
        write(out/'inputs_seal.json',dict(contract_sha256=c['_sha'],parent_manifest_sha256=c['parent_manifest_sha256'],
            arm=arm,saved_heads=records,control_sha256=sha(c['control_camera']),sensor_depth_used=False))
        align=importlib.import_module('cloud_opt.dust3r_opt')
        init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses')
        opt=importlib.import_module('cloud_opt.dust3r_opt.optimizer')
        base=importlib.import_module('cloud_opt.dust3r_opt.base_opt')
        state=dict(phase='setup',prelog={},pnp=[],registration_observations=[])
        def patch(obj,name,factory):
            old=getattr(obj,name);patches.append((obj,name,old));setattr(obj,name,factory(old))
        def check_fixed(scene):
            require(scene.edges==[(0,1),(0,2),(0,3)],'Exact common4 directed star')
            require(not scene.im_poses.requires_grad and not scene.im_pp.requires_grad and not scene.norm_pw_scale,'Original frozen poses/pp and no scale normalization')
            require(scene.im_focals.requires_grad and all(p.requires_grad for p in scene.im_depthmaps),'Original common4 trainability')
            require(torch.allclose(scene.get_im_poses(),cameras,atol=1e-5,rtol=1e-6),'Given optical cameras unchanged')
        def capture_scene(old):
            def call(*args,**kw):
                scene=old(*args,**kw);state['scene']=scene;return scene
            return call
        patch(align,'global_aligner',capture_scene)
        def prefix(old):
            def call(scene,pts3d,im_focals,im_poses):
                require(state['phase']=='mst' and 'prefix_meta' not in state,'Unique pre-Sim3 boundary')
                check_fixed(scene)
                arrays,meta,objects=r.snapshot(scene,np)
                state['prefix_meta']=meta;state['prefix_objects']=objects
                state['frozen']={name:p.detach().clone() for name,p in scene.named_parameters() if not p.requires_grad}
                for i,p in enumerate(pts3d):arrays['local::points.'+str(i)]=b.array(p)
                arrays['local::poses']=b.array(im_poses)
                focal_none=[]
                for i,f in enumerate(im_focals):
                    focal_none.append(f is None)
                    if f is not None:arrays['local::focal.'+str(i)]=b.array(f)
                # All values copied immediately: original init_from_pts3d
                # subsequently overwrites point maps and camera translations.
                np.savez_compressed(out/'prefix_raw.npz',**arrays)
                write(out/'prefix_metadata.json',dict(scene=meta,focal_none=focal_none,
                    locals={key:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.tobytes()).hexdigest()) for key,v in arrays.items() if key.startswith('local::')}))
                state['phase']='init_from_pts3d';return old(scene,pts3d,im_focals,im_poses)
            return call
        patch(init,'init_from_pts3d',prefix)
        def observe_registration(old):
            def call(*args,**kw):
                answer=old(*args,**kw)
                if state['phase']=='alignment':
                    raw_s=answer[2]
                    state['registration_observations'].append(dict(raw_scale=b.array(raw_s),
                        raw_type=type(raw_s).__module__+'.'+type(raw_s).__qualname__,
                        branch_condition=bool(abs(raw_s)<1e-6)))
                return answer
            return call
        patch(init.roma,'rigid_points_registration',observe_registration)
        def controlled_alignment(old):
            def call(src,target):
                require(state['phase']=='init_from_pts3d' and counts['alignment']==0,'One original alignment')
                src_copy=b.array(src);target_copy=b.array(target)
                state['phase']='alignment'
                s0,R0,T0=old(src,target);counts['alignment']+=1
                state['phase']='init_from_pts3d'
                require(len(state['registration_observations'])==1,'Observe raw scale without rerunning registration')
                require(np.isfinite(b.array(s0)).all() and float(s0)>0,'Finite positive original scale')
                s=s0 if arm=='C2t' else (1.0 if isinstance(s0,float) else s0.new_tensor(1.0))
                T=target[:,:3,3].mean(0)-s*(R0@src[:,:3,3].mean(0))
                raw=state['registration_observations'][0]
                np.savez_compressed(out/'alignment.npz',source_c2w=src_copy,target_c2w=target_copy,
                    raw_registered_scale=raw['raw_scale'],s0=b.array(s0),R0=b.array(R0),T0=b.array(T0),s_used=b.array(s),R_used=b.array(R0),T_used=b.array(T))
                state['alignment_types']=dict(raw_scale_type=raw['raw_type'],original_return_scale_type=type(s0).__module__+'.'+type(s0).__qualname__,
                    used_scale_type=type(s).__module__+'.'+type(s).__qualname__,original_near_zero_branch_condition=raw['branch_condition'],
                    original_registration_calls=1,center_match='mean only, not every center')
                return s,R0,T
            return call
        patch(init,'align_multiple_poses',controlled_alignment)
        def capture_prelog(old):
            def call(scene,idx,depth,force=False):
                require(state['phase']=='init_from_pts3d' and idx not in state['prelog'],'One original pre-log depth per frame')
                state['prelog'][idx]=b.array(depth)
                return old(scene,idx,depth,force=force)
            return call
        patch(opt.PointCloudOptimizer,'_set_depthmap',capture_prelog)
        def mst(old):
            def call(scene,*args,**kw):
                require(counts['MST']==0 and state['phase']=='setup','One original MST')
                require(kw==dict(niter_PnP=10),'Original PnP budget')
                state['phase']='mst';answer=old(scene,*args,**kw)
                counts['MST']+=1;state['phase']='after_mst';return answer
            return call
        patch(init,'init_minimum_spanning_tree',mst)
        def pnp(old):
            def call(*args,**kw):
                answer=old(*args,**kw);counts['PnP']+=1
                record=dict(success=answer is not None,niter_PnP=kw.get('niter_PnP'))
                if answer is not None:record['focal']=float(answer[0])
                state['pnp'].append(record);return answer
            return call
        patch(init,'fast_pnp',pnp)
        def forbidden(counter):
            def factory(old):
                def call(*args,**kw):counts[counter]+=1;raise RuntimeError('Forbidden S29 operation: '+counter)
                return call
            return factory
        patch(torch.optim.Adam,'step',forbidden('Adam'))
        patch(torch.autograd,'backward',forbidden('backward'))
        patch(base.BasePCOptimizer,'clean_pointcloud',forbidden('clean'))
        def stop_before_optimizer(old):
            def call(scene,*args,**kw):
                require(state['phase']=='after_mst' and kw==dict(niter=400,schedule='linear',lr=.01),'Original wrapper at pre-optimizer boundary')
                require(scene is state['scene'] and set(state['prelog'])==set(range(4)),'Complete actual scene observation')
                check_fixed(scene)
                _,getter=r.derive_getter(c['optimizer_source'])
                namespace=dict(vars(opt));exec(compile(ast.Module(body=[getter],type_ignores=[]),c['s28_runner']+'::getter','exec'),namespace)
                patch(opt.PointCloudOptimizer,'get_depthmaps',lambda old_getter:namespace['get_depthmaps'])
                arrays,meta,objects=r.snapshot(scene,np);r.assert_same_objects(state['prefix_objects'],objects)
                for name,p in scene.named_parameters():
                    require(bool(p.requires_grad)==state['prefix_meta']['parameter::'+name]['requires_grad'],'Original flags unchanged')
                    if not p.requires_grad:require(torch.equal(p,state['frozen'][name]),'MST changed frozen parameter: '+name)
                np.savez_compressed(out/'initial_raw.npz',**arrays);write(out/'initial_raw_metadata.json',meta)
                with torch.no_grad():
                    decoded=dict(prelog_depth=np.stack([state['prelog'][i] for i in range(4)]),
                        depth=np.stack([b.array(x) for x in scene.get_depthmaps()]),point_cloud=np.stack([b.array(x) for x in scene.get_pts3d()]),
                        focal=b.array(scene.get_focals()),pp=b.array(scene.get_principal_points()),c2w=b.array(scene.get_im_poses()),
                        pw_scale=b.array(scene.get_pw_scale()),pw_poses=b.array(scene.get_pw_poses()),adaptors=b.array(scene.get_adaptors()),
                        norm_scale=b.array(scene.get_pw_norm_scale_factor()))
                    loss=scene();counts['objective']+=1;decoded['objective']=b.array(loss)
                np.savez_compressed(out/'initial_decoded.npz',**decoded)
                after_arrays,after_meta,after_objects=r.snapshot(scene,np);r.assert_same_objects(objects,after_objects)
                require(meta==after_meta,'Getter/objective may not alter parameters or buffers')
                require(all(p.grad is None for p in scene.parameters()),'No backward or existing gradients')
                state['domains']={key:dict(nonfinite=int((~np.isfinite(decoded[key])).sum()),nonpositive=int((np.isfinite(decoded[key])&(decoded[key]<=0)).sum())) for key in ['prelog_depth','depth','focal']}
                state['objective_finite']=bool(np.isfinite(decoded['objective']).all())
                state['getter_repair_active']=True;state['phase']='sentinel'
                raise InitializationComplete()
            return call
        patch(base,'global_alignment_loop',stop_before_optimizer)
        b.numeric_setup()  # Same post-import seed boundary as S28.
        sentinel=False
        try:a.run_original_ga(ns,output,control_c2ws=cameras,old_depth=None,output_dir=out)
        except InitializationComplete:sentinel=True
        require(sentinel and counts==c['counts_per_arm'],'Exact expected zero-step execution counts')
        loaded={};loaded_deps={};embedded=Path(m['binding']['embedded_root']).resolve();overlay=Path(m['binding']['overlay']).resolve()
        for name,obj in list(sys.modules.items()):
            origin=getattr(obj,'__file__',None)
            if not origin:continue
            path=Path(origin).resolve()
            if name.startswith(('cloud_opt.','dust3r.','src.dust3r.','models.','croco.')):
                require(path.is_relative_to(embedded) and m['binding']['source_identities'].get(str(path))==sha(path),'Changed loaded geometry: '+name);loaded[name]=str(path)
            if path.is_relative_to(overlay):
                require(m['dependency_identities'].get(str(path))==sha(path),'Changed loaded overlay: '+name);loaded_deps[name]=str(path)
        for p,h in {**m['identities'],**c['identities']}.items():require(sha(p)==h,'Input changed during worker: '+p)
        receipt.update(status='PASS_INITIALIZATION_EXECUTED',completed_utc=utc(),counts=counts,
            domains=state['domains'],objective_finite=state['objective_finite'],alignment_types=state['alignment_types'],pnp=state['pnp'],
            getter_repair_active=state['getter_repair_active'],source_proof=proof,loaded_geometry=loaded,loaded_overlay=loaded_deps,
            pass_meaning='Original controlled initialization and zero-step boundary executed; numerical hypothesis verdict is separate',
            outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'})
        write(out/'receipt.json',receipt)
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=utc(),counts=counts,error=repr(e),traceback=traceback.format_exc());write(out/'receipt.json',receipt);raise
    finally:
        for obj,name,original in reversed(patches):setattr(obj,name,original)


def dispatch(c,path):
    b=module(c['parent_runner'],'s29_original_supervisor');b.WORK=Path(c['execution_root']);b.WORK.mkdir(parents=True,exist_ok=True)
    target=b.WORK/'dispatch_receipt.json';require(not target.exists(),'No repeated dispatch')
    receipt=dict(status='RUNNING',started_utc=utc(),contract_sha256=c['_sha'],phases=[]);write(target,receipt)
    try:
        for arm in c['arms']:
            command=[sys.executable,str(Path(__file__).resolve()),'worker','--arm',arm,'--contract',str(path),'--sha256',c['_sha']]
            b.supervised(command,arm,60,4*1024**3);receipt['phases'].append(arm);write(target,receipt)
        command=[sys.executable,c['validator'],'--contract',str(path),'--sha256',c['_sha']]
        b.supervised(command,'validation',60,4*1024**3)
        receipt.update(status='PASS',completed_utc=utc(),MST=2,PnP=6,backward=0,Adam=0,model=0,GT=0);write(target,receipt)
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=utc(),error=str(e));write(target,receipt);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['worker','dispatch'])
    parser.add_argument('--arm');parser.add_argument('--contract',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();c=load_contract(args.contract,args.sha256)
    if args.command=='worker':worker(c,args.arm)
    else:dispatch(c,args.contract)
