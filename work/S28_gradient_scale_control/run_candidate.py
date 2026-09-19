"""Unexecuted S28 draft: two fresh common4 arms, sole getter gradient repair.

Runtime entry requires a separately frozen contract. No work occurs on import.
The existing S26B producer, observer and numerical gates are reused verbatim.
"""
from __future__ import annotations
import argparse
import ast
import copy
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
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def require(ok, why):
    if not ok: raise RuntimeError(why)
def write(p, data):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n'); tmp.replace(p)
def module(path, name):
    spec=importlib.util.spec_from_file_location(name, path)
    obj=importlib.util.module_from_spec(spec); sys.modules[name]=obj; spec.loader.exec_module(obj)
    return obj


def unique_function(tree, name):
    found=[n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name==name]
    require(len(found)==1, 'Exactly one function: '+name)
    return found[0]


def derive_worker(source):
    """Only mode guard, frame count and archive routing differ from the original."""
    old=unique_function(ast.parse(Path(source).read_text()), 'ga_worker')
    new=copy.deepcopy(old)
    guard=ast.parse("require(mode in ('original', 'gradient_only'), 'S28 paired common4 only')").body[0]
    require(ast.unparse(new.body[0])=="require(mode in ('cut3r', 'ttt3r', 'filt3r'), 'S26B never reruns common_old GA')", 'Worker guard source changed')
    new.body[0]=guard
    matches=[n for n in new.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='n' for t in n.targets)]
    require(len(matches)==1 and ast.unparse(matches[0].value)=="4 if mode == 'common_old' else 8", 'Frame count source changed')
    matches[0].value=ast.Constant(4)
    names=[n for n in ast.walk(new) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='name' for t in n.targets)]
    require(len(names)==1 and ast.unparse(names[0].value)=="'common_old_depth_original4' if mode == 'common_old' else mode", 'Original archive route source changed')
    names[0].value=ast.Constant('common_old_depth_original4')
    ast.fix_missing_locations(new)
    normalized=copy.deepcopy(new);normalized.body[0]=copy.deepcopy(old.body[0])
    for key in ['n','name']:
        original_values=[q.value for q in ast.walk(old) if isinstance(q,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in q.targets)]
        require(len(original_values)==1,'Unique dispatch assignment '+key)
        for n in ast.walk(normalized):
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets):
                n.value=copy.deepcopy(original_values[0])
    require(ast.dump(normalized)==ast.dump(old), 'Worker has an unapproved mathematical change')
    return old,new


def derive_getter(source):
    old=unique_function(ast.parse(Path(source).read_text()), 'get_depthmaps')
    new=copy.deepcopy(old)
    matches=[n for n in new.body if isinstance(n,ast.Assign) and ast.unparse(n)=="res = ParameterStack(self.im_depthmaps, is_param=False).exp()"]
    require(len(matches)==1, 'Getter expression must be unique and unchanged')
    matches[0].value=ast.parse('torch.stack(list(self.im_depthmaps)).float().exp()',mode='eval').body
    ast.fix_missing_locations(new)
    normalized=copy.deepcopy(new)
    for n in normalized.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='res' for t in n.targets):
            n.value=copy.deepcopy(next(q.value for q in old.body if isinstance(q,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='res' for t in q.targets)))
    require(ast.dump(normalized)==ast.dump(old), 'Getter changes beyond one expression')
    return old,new


def contract(path, expected):
    require(sha(path)==expected, 'Exact frozen contract SHA required')
    c=read(path)
    require(c['status']=='FROZEN' and c['schema']=='s28-matched-gradient-only-v1', 'Cannot execute draft')
    require(c['arms']==['original','gradient_only'] and c['steps_per_arm']==400 and c['model_forwards']==0, 'Fixed two-arm budget')
    require(c['seconds_per_arm']==600 and c['rss_bytes_per_arm']==16*1024**3, 'Fixed resource budget')
    for p,h in c['identities'].items():require(sha(p)==h,'Changed caller identity: '+p)
    parent=read(c['parent_manifest'])
    require(sha(c['parent_manifest'])==c['parent_manifest_sha256'],'Parent manifest identity')
    require(c['gt_depth_frames']==parent['scoring']['gt_depth_frames'][:4],'Exactly inherited first four scoring identities')
    require(c['scoring_policy']=={k:parent['scoring'][k] for k in c['scoring_policy_keys']},'Inherited scoring rules')
    return c


def snapshot(scene, np):
    arrays={}; meta={}; objects={}
    for kind, entries in [('parameter',scene.named_parameters()),('buffer',scene.named_buffers())]:
        for name,tensor in entries:
            key=kind+'::'+name
            value=tensor.detach().cpu().contiguous().numpy().copy()
            arrays[key]=value;objects[key]=tensor
            meta[key]=dict(shape=list(value.shape), dtype=str(value.dtype), requires_grad=bool(tensor.requires_grad),
                           sha256=hashlib.sha256(value.tobytes()).hexdigest())
    return arrays,meta,objects


def assert_same_objects(before, after):
    require(set(before)==set(after),'Parameter/buffer name set changed')
    for name,t in before.items():require(after[name] is t,'Parameter/buffer object replaced: '+name)


def observer_type(b,c,arm):
    class GradientObserver(b.SceneObserver):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.initial_arrays=None;self.initial_meta=None;self.initial_objects=None
            self.extra_forwards=0;self.gradient_steps=0

        def install(self):
            super().install()
            np=importlib.import_module('numpy');torch=self.T
            init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses')
            base=importlib.import_module('cloud_opt.dust3r_opt.base_opt')
            opt=importlib.import_module('cloud_opt.dust3r_opt.optimizer')
            _,getter=derive_getter(c['optimizer_source'])
            namespace=dict(vars(opt));exec(compile(ast.Module(body=[getter],type_ignores=[]),str(Path(__file__).resolve())+'::getter','exec'),namespace)
            patched_getter=namespace['get_depthmaps']

            def initial_after_mst(old):
                def call(scene,*args,**kw):
                    answer=old(scene,*args,**kw)
                    require(self.mst_calls==1 and self.steps==self.adam_steps==0,'Patch strictly after original MST, before Adam')
                    self.initial_arrays,self.initial_meta,self.initial_objects=snapshot(scene,np)
                    np.savez_compressed(self.out/'initial_raw.npz',**self.initial_arrays)
                    write(self.out/'initial_raw_metadata.json',self.initial_meta)
                    with torch.no_grad():
                        depth_before=b.array(scene.get_depthmaps(raw=True))
                        list_before=[b.array(x) for x in scene.get_depthmaps()]
                        loss_before=b.array(scene());self.extra_forwards+=1
                        decoded=dict(depth=np.stack(list_before),point_cloud=np.stack([b.array(x) for x in scene.get_pts3d()]),
                                     focal=b.array(scene.get_focals()),pp=b.array(scene.get_principal_points()),c2w=b.array(scene.get_im_poses()),
                                     pw_scale=b.array(scene.get_pw_scale()),pw_poses=b.array(scene.get_pw_poses()),adaptors=b.array(scene.get_adaptors()),objective=loss_before)
                    np.savez_compressed(self.out/'initial_decoded.npz',**decoded)
                    if arm=='gradient_only':
                        prior=Path(c['output_root'])/'original'
                        receipt=read(prior/'receipt.json')
                        require(receipt['status']=='PASS' and receipt['s28_contract_sha256']==c['_sha'],'A must be fully sealed before B')
                        for name in ['initial_raw.npz','initial_raw_metadata.json','initial_decoded.npz']:
                            require(sha(prior/name)==receipt['outputs'][name],'A initialization seal: '+name)
                        require(read(prior/'initial_raw_metadata.json')==self.initial_meta,'Cross-arm names/shapes/dtypes/flags/raw tensor SHA exact')
                        with np.load(prior/'initial_raw.npz',allow_pickle=False) as z:
                            require(set(z.files)==set(self.initial_arrays),'Complete cross-arm initial tensor set')
                            for name,a in self.initial_arrays.items():
                                require(z[name].dtype==a.dtype and z[name].shape==a.shape and z[name].tobytes()==a.tobytes(),'Cross-arm tensor raw bytes: '+name)
                        with np.load(prior/'initial_decoded.npz',allow_pickle=False) as z:
                            require(z['objective'].tobytes()==loss_before.tobytes(),'Cross-arm initial objective bytes')
                        self.patch(opt.PointCloudOptimizer,'get_depthmaps',lambda old_getter:patched_getter)
                    with torch.no_grad():
                        depth_after=b.array(scene.get_depthmaps(raw=True))
                        list_after=[b.array(x) for x in scene.get_depthmaps()]
                        loss_after=b.array(scene());self.extra_forwards+=1
                    require(depth_before.tobytes()==depth_after.tobytes(),'Getter raw forward values exact')
                    require(len(list_before)==len(list_after) and all(x.tobytes()==y.tobytes() for x,y in zip(list_before,list_after)),'Getter reshaped forward values exact')
                    require(loss_before.tobytes()==loss_after.tobytes(),'Original objective unchanged at patch boundary')
                    after_arrays,after_meta,after_objects=snapshot(scene,np)
                    assert_same_objects(self.initial_objects,after_objects)
                    require(after_meta==self.initial_meta,'Getter must not change raw parameters/buffers/flags')
                    self.report['s28_initialization']=dict(arm=arm,original_mst_preserved=True,
                        initial_metadata_sha256=sha(self.out/'initial_raw_metadata.json'),
                        cross_arm_raw_exact=True if arm=='gradient_only' else 'REFERENCE_ARM',
                        getter_forward_bytes_exact=True,initial_objective=float(loss_before),
                        getter_repair_active=arm=='gradient_only',extra_no_update_objective_forwards=self.extra_forwards)
                    self.checkpoint('S28_first_step_gate_passed')
                    return answer
                return call
            self.patch(init,'init_minimum_spanning_tree',initial_after_mst)

            def validate_before_step(old):
                def call(optimizer,*args,**kw):
                    require(optimizer is self.optimizer and self.scene is not None,'Only the original observed Adam may step')
                    for name,p in self.scene.named_parameters():
                        if p.grad is not None:require(bool(torch.isfinite(p.grad).all()),'Nonfinite gradient before Adam: '+name)
                    for p in self.scene.im_depthmaps:
                        require((p.grad is None)==(arm=='original'),'Depth gradient route must hold before Adam')
                    return old(optimizer,*args,**kw)
                return call
            self.patch(torch.optim.Adam,'step',validate_before_step)

            def stats(scene):
                with torch.no_grad():
                    rows=[]
                    for i,(log,depth) in enumerate(zip(scene.im_depthmaps,scene.get_depthmaps())):
                        before=torch.from_numpy(self.initial_arrays[f'parameter::im_depthmaps.{i}'])
                        change=log.detach()-before
                        initial_depth=before.exp();ratio=depth.detach().reshape(-1)/initial_depth.reshape(-1)
                        rows.append(dict(index=i,log_mean=float(log.detach().mean()),log_min=float(log.detach().min()),log_max=float(log.detach().max()),
                            depth_mean=float(depth.detach().mean()),depth_min=float(depth.detach().min()),depth_max=float(depth.detach().max()),
                            log_change_mean=float(change.mean()),log_change_max_abs=float(change.abs().max()),
                            depth_initial_ratio_mean=float(ratio.mean())))
                    return dict(frames=rows,focal=b.array(scene.get_focals()).tolist(),pw_scale=b.array(scene.get_pw_scale()).tolist())

            def grad(p):
                g=p.grad
                return dict(grad_is_none=g is None,requires_grad=bool(p.requires_grad),
                            finite=None if g is None else bool(torch.isfinite(g).all()),
                            l2=None if g is None else float(g.detach().norm()))

            def trace_iter(old):
                def call(scene,cur_iter,*args,**kw):
                    require(self.initial_objects is not None,'MST gate precedes iteration')
                    before=stats(scene)
                    result=old(scene,cur_iter,*args,**kw)
                    # The original backward and Adam step already occurred once.
                    current={**{'parameter::'+n:p for n,p in scene.named_parameters()},**{'buffer::'+n:p for n,p in scene.named_buffers()}}
                    assert_same_objects(self.initial_objects,current)
                    for name,p in current.items():
                        require(p.requires_grad==self.initial_meta[name]['requires_grad'],'Trainability changed: '+name)
                        require(bool(torch.isfinite(p).all()),'Nonfinite tensor: '+name)
                    self.check_fixed(scene)
                    for name,p in self.params(scene).items():require(torch.equal(p,self.frozen[name]),'Frozen parameter changed: '+name)
                    gs={n:grad(p) for n,p in scene.named_parameters() if n.startswith('im_depthmaps.') or n in ('im_focals','pw_poses')}
                    require(all(v['finite'] is not False for v in gs.values()),'Nonfinite diagnostic gradient')
                    depth_grad=[gs['im_depthmaps.'+str(i)] for i in range(4)]
                    require(all(v['grad_is_none']==(arm=='original') for v in depth_grad),'Registered depth connectivity differs from arm contract')
                    optimizer_ids={id(p) for group in self.optimizer.param_groups for p in group['params']}
                    require(optimizer_ids=={id(p) for p in scene.parameters() if p.requires_grad},'Original optimizer parameter membership')
                    self.gradient_steps+=1
                    after=stats(scene)
                    record=dict(iteration=cur_iter,actual_adam_steps=self.adam_steps,loss_before_step=float(result[0]),
                        lr=float(result[1]),statistics_before_step=before,statistics_after_step=after,gradients_from_this_step=gs,utc=utc())
                    with (self.out/'gradient_depth_trace.jsonl').open('a') as f:f.write(json.dumps(record,allow_nan=False)+'\n')
                    if cur_iter==399:
                        final_arrays,final_meta,_=snapshot(scene,np)
                        np.savez_compressed(self.out/'final_raw_before_clean.npz',**final_arrays)
                        write(self.out/'final_raw_metadata.json',final_meta)
                        self.report['s28_gradient_steps']=self.gradient_steps
                        self.report['s28_objective_forward_counts']=dict(optimization=400,patch_boundary_no_update=self.extra_forwards,postfinal_no_update=1,total=403)
                    return result
                return call
            self.patch(base,'global_alignment_iter',trace_iter)
    return GradientObserver


def worker(c,arm):
    require(arm in c['arms'],'Unknown arm')
    b=module(c['parent_runner'],'s28_parent_runner')
    m=b.manifest(c['parent_manifest_sha256'])
    out=Path(c['output_root'])/arm
    require(not out.exists(),'Never overwrite or automatically repeat an arm')
    b.OUT=Path(c['output_root'])
    b.SceneObserver=observer_type(b,c,arm)
    original_write=b.write
    def bound_write(path,value):
        path=Path(path)
        if path.parent==out and path.name in ('receipt.json','inputs_seal.json'):
            value=dict(value,s28_contract_sha256=c['_sha'],evidence_scope='Fresh matched common4 engineering control; no novelty or video claim')
            if path.name=='receipt.json' and value.get('status')=='PASS':
                for p,h in m['identities'].items():require(sha(p)==h,'Changed parent identity at finish: '+p)
                for p,h in c['identities'].items():require(sha(p)==h,'Changed caller identity at finish: '+p)
                value['parent_identities_rechecked']=True
        return original_write(path,value)
    b.write=bound_write
    _,fn=derive_worker(c['parent_runner'])
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(Path(__file__).resolve())+'::worker','exec'),vars(b))
    b.ga_worker(m,arm)


def dispatch(c,contract_path):
    b=module(c['parent_runner'],'s28_supervision_parent')
    b.WORK=Path(c['execution_root']);b.WORK.mkdir(parents=True,exist_ok=True)
    target=b.WORK/'dispatch_receipt.json'
    require(not target.exists(),'No repeat dispatch')
    receipt=dict(status='RUNNING',started_utc=utc(),s28_contract_sha256=c['_sha'],phases=[])
    write(target,receipt)
    try:
        for arm in c['arms']:
            command=[sys.executable,str(Path(__file__).resolve()),'worker','--arm',arm,'--contract',str(contract_path),'--sha256',c['_sha']]
            b.supervised(command,arm,c['seconds_per_arm'],c['rss_bytes_per_arm'])
            receipt['phases'].append(arm);write(target,receipt)
        command=[sys.executable,c['scorer'],'--contract',str(contract_path),'--sha256',c['_sha']]
        b.supervised(command,'scoring',180,2*1024**3)
        receipt.update(status='PASS',completed_utc=utc(),new_adam_steps=800,model_forwards=0)
        write(target,receipt)
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=utc(),error=str(e));write(target,receipt);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['worker','dispatch']);p.add_argument('--arm')
    p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True)
    args=p.parse_args();c=contract(args.contract,args.sha256);c['_sha']=args.sha256
    if args.command=='worker':worker(c,args.arm)
    else:dispatch(c,args.contract)


if __name__=='__main__':main()
