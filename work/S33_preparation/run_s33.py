"""S33 candidate: ordinary fixed effective pair-scale mean, no new network.

Only a separately reviewed FROZEN contract can execute. Import/help is stdlib.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ENDPOINT='common_pair_scale_400'
SCHEMA='s33-initial-pair-scale-mean-control-v1'

def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,why):
    if not ok:raise RuntimeError(why)
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(p)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def load_s32(c):
    sys.path.insert(0,str(Path(c['s32_runner']).parent))
    return module(c['s32_runner'],'s33_frozen_s32')

def contract(path,expected):
    require(sha(path)==expected,'Exact S33 frozen contract SHA');c=read(path)
    require(c['status']=='FROZEN' and c['schema']==SCHEMA,'Candidate cannot execute')
    require(c['limits']==dict(threads=8,seconds_per_window=120,rss_bytes_per_window=4*1024**3),'Fixed local budget')
    require(c['steps']==400 and c['endpoints']==[ENDPOINT],'One new fixed400 condition')
    require(c['tolerances']==dict(scale_mean_atol=1e-5,scale_ratio_atol=1e-5,scale_ratio_rtol=1e-5),'Fixed implementation tolerances')
    for p,h in c['identities'].items():require(sha(p)==h,'Changed S33 source/JSON identity: '+p)
    p=load_s32(c);old=p.contract(c['s32_contract'],c['s32_contract_sha256'])
    for k in ('selection','selection_sha256','windows','A_contract','A_contract_sha256','A_receipts','parent_manifest','parent_runner','s28_runner','s30_runner','optimizer_source','scoring_policy'):
        require(c[k]==old[k],'Inherited S32 field changed: '+k)
    require(c['output_root']!=old['output_root'] and c['execution_root']!=old['execution_root'],'Independent output paths')
    for w in c['windows']:
        ref=c['references'][w['id']];r=read(ref['receipt'])
        require(sha(ref['receipt'])==ref['receipt_sha256'] and r['window_id']==w['id'],'Own S32 reference')
        require(r['contract_sha256']==c['s32_contract_sha256'],'S32 producer contract')
        require(r['status']==('UNAVAILABLE' if any(f['gt_time'] is None for f in w['frames']) else 'PASS'),'Preserve all four eligibility statuses')
    c['_sha']=expected;c['_path']=str(Path(path).resolve());return c

def unique_function(path,name):
    nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name]
    require(len(nodes)==1,'Unique function '+name);return nodes[0]

def derive_observer(s32,s30,s28_path):
    """S32 observer math is unchanged except one pre-getter callback.

    The callback is already between its two no-update boundary objectives.
    """
    _,old=s32.derive_observer(s30,s28_path);new=copy.deepcopy(old);count=0
    for n in ast.walk(new):
        if isinstance(n,ast.Name) and n.id=='verify_window_initial_state':n.id='install_scale_constraint';count+=1
    require(count==1,'One MST-after callback replacement')
    ast.fix_missing_locations(new);return old,new

def same_array(actual,expected,label):
    require(actual.shape==expected.shape and actual.dtype==expected.dtype and actual.tobytes()==expected.tobytes(),'Exact '+label)

def scale_state(observer):
    torch=observer.T;scene=observer.scene
    require(scene.norm_pw_scale is False,'Keep original normalization Boolean False')
    require(scene.get_pw_norm_scale_factor is observer.s33_factor_callable,'Actual instance factor route')
    with torch.no_grad():
        ell=scene.pw_poses[:,-1];effective=scene.get_pw_scale();raw=ell.exp();factor=scene.get_pw_norm_scale_factor()
        require(ell.shape==effective.shape==(3,) and bool(torch.isfinite(effective).all()) and bool((effective>0).all()),'Three finite positive effective scales')
        mean=float(effective.log().mean());target=float(observer.s33_m0)
        require(abs(mean-target)<=1e-5,'Effective mean log-scale is fixed')
        effective_ratios=effective/effective[0];raw_ratios=raw/raw[0]
        require(torch.allclose(effective_ratios,raw_ratios,atol=1e-5,rtol=1e-5),'Relative edge scale ratios retained')
        actual=scene.get_pw_poses();expected=scene._get_poses(scene.pw_poses).clone();expected[:,:3]*=effective.view(-1,1,1)
        require(torch.equal(actual,expected),'Original effective scale acts on whole3x4')
        return dict(raw_log_mean=float(ell.mean()),fixed_initial_log_mean=target,factor=float(factor),effective_log_mean=mean,
            effective_scales=effective.tolist(),raw_scales=raw.tolist(),relative_ratios_max_abs=float((effective_ratios-raw_ratios).abs().max()),full_3x4_exact=True)

def install_scale_constraint(observer,c,arm,loss_before,np):
    require(arm=='C2a' and observer.mst_calls==1 and observer.steps==observer.adam_steps==0,'Only after own MST, before any Adam')
    require(len(observer.initial_meta)==len(observer.initial_arrays)==33,'Complete33 raw entries')
    ref=c['references'][c['_window_id']];r=read(ref['receipt']);base=Path(ref['receipt']).parent
    require(r['status']=='PASS' and sha(ref['receipt'])==ref['receipt_sha256'],'Full historical S32 reference')
    names=('GA/C2a/initial_raw.npz','GA/C2a/initial_raw_metadata.json','GA/C2a/initial_decoded.npz','GA/C2a/controlled_alignment.npz')
    for name in names:require(sha(base/name)==r['outputs'][name]==ref['files'][name],'S32 reference content seal: '+name)
    require(read(base/names[1])==observer.initial_meta,'All33 names/shapes/dtypes/flags/rawSHA identical to own S32')
    with np.load(base/names[0],allow_pickle=False) as z:
        require(set(z.files)==set(observer.initial_arrays),'Complete historical raw set')
        for name,value in observer.initial_arrays.items():same_array(z[name],value,'S32 raw '+name)
    with np.load(base/names[2],allow_pickle=False) as prior, np.load(observer.out/'initial_decoded.npz',allow_pickle=False) as current:
        require(set(prior.files)==set(current.files),'Complete decoded initial fields')
        for name in prior.files:same_array(current[name],prior[name],'S32 decoded '+name)
        same_array(prior['objective'],loss_before,'S32 initial objective')
    with np.load(base/names[3],allow_pickle=False) as z:
        require(set(z.files)==set(observer.alignment_values),'Complete C2a alignment tuple')
        for name,value in observer.alignment_values.items():same_array(z[name],value,'S32 alignment '+name)
    torch=observer.T;scene=observer.scene
    require(scene.norm_pw_scale is False and not scene.pw_adaptors.requires_grad,'Original False normalization/frozen adaptors')
    require(scene.pw_poses.shape==(3,8),'Original 3edge8column parameter')
    before={name:getattr(scene,name)().detach().clone() for name in ('get_pw_scale','get_pw_poses','get_adaptors','get_focals','get_principal_points','get_im_poses')}
    observer.s33_m0=scene.pw_poses[:,-1].detach().mean().clone()
    def factor():
        # Current mean must remain differentiable; only the initial constant is detached.
        result=(observer.s33_m0-scene.pw_poses[:,-1].mean()).exp()
        if torch.is_grad_enabled():require(result.requires_grad,'Live current scale mean gradient')
        return result
    observer.patch(scene,'get_pw_norm_scale_factor',lambda old:factor);observer.s33_factor_callable=factor
    require(float(factor().detach())==1.0,'No initial scale jump')
    for name,value in before.items():require(torch.equal(getattr(scene,name)(),value),'Initial factor changes decoded '+name)
    observer.s33_scale_rows=0
    gate=scale_state(observer)
    observer.report['s33_scale_constraint']=dict(status='ACTIVE_AFTER_MATCHED_MST',initial_mean_log_scale=float(observer.s33_m0),
        current_mean_detached=False,norm_pw_scale=False,raw_checkpoint_count=33,reference_receipt_sha256=ref['receipt_sha256'],initial_gate=gate)
    write(observer.out/'s33_initial_gate.json',dict(status='PASS',window_id=c['_window_id'],contract_sha256=c['_sha'],
        initial_raw_count=33,raw_bytes_exact=True,decoded_exact=True,objective_exact=True,alignment_exact=True,
        initial_factor_exact_one=True,source_receipt_sha256=ref['receipt_sha256'],scale_constraint=gate))

def observer_type(b,r,s30,c,s32):
    _,node=derive_observer(s32,s30,c['s28_runner'])
    # Reuse S32's exact C2a align hook around our callback-derived observer.
    old_derive=s32.derive_observer
    def bound_derive(unused,unused_path):return node,node
    try:
        s32.derive_observer=bound_derive
        # Its factory namespace is vars(r), so expose the new callback locally.
        r.install_scale_constraint=install_scale_constraint
        Base=s32.observer_type(b,r,s30,c)
    finally:s32.derive_observer=old_derive
    class ScaleObserver(Base):
        def install(self):
            super().install();base=sys.modules['cloud_opt.dust3r_opt.base_opt']
            def trace_scale(old):
                def call(scene,cur_iter,*args,**kw):
                    before=scale_state(self);result=old(scene,cur_iter,*args,**kw);after=scale_state(self)
                    require(cur_iter==self.s33_scale_rows,'All400 scale trace rows');self.s33_scale_rows+=1
                    row=dict(iteration=cur_iter,actual_adam_steps=self.adam_steps,before=before,after=after,utc=utc())
                    with (self.out/'s33_scale_trace.jsonl').open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
                    if cur_iter==399:self.report['s33_scale_constraint'].update(trace_rows=self.s33_scale_rows,final=after)
                    return result
                return call
            self.patch(base,'global_alignment_iter',trace_scale)
    return ScaleObserver

def save_candidate(out,b,np,producer):
    p=b.OUT/'C2a/output.npz';require(sha(p)==producer['outputs']['output.npz'],'Full new producer seal')
    require(producer['observer']['s33_scale_constraint']['trace_rows']==400,'Actual400 constrained steps')
    with np.load(p,allow_pickle=False) as z:depth=z['depth'].copy()
    require(depth.shape==(4,384,512) and depth.dtype==np.float32 and np.isfinite(depth).all() and (depth>0).all(),'Complete candidate depth')
    np.savez_compressed(out/(ENDPOINT+'.npz'),depth=depth)

def derive_window_worker(s32_path):
    old=unique_function(s32_path,'worker');new=copy.deepcopy(old)
    handler=next(n for n in new.body if isinstance(n,ast.Try));body=handler.body
    start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and ast.unparse(n)=='endpoints = []')
    end=next(i for i,n in enumerate(body) if isinstance(n,ast.Expr) and ast.unparse(n)=="write(out / 'decomposition.json', decomposition)")
    body[start:end+1]=ast.parse('save_candidate(out,b,np,producer)').body
    rename={'all_three_endpoints_available':'candidate_available'}
    for n in ast.walk(new):
        if isinstance(n,ast.keyword) and n.arg in rename:n.arg=rename[n.arg]
        if isinstance(n,ast.Call) and ast.unparse(n.func)=='record.update' and any(k.arg=='status' and isinstance(k.value,ast.Constant) and k.value.value=='PASS' for k in n.keywords):
            n.keywords=[k for k in n.keywords if k.arg!='normalization']
            for k in n.keywords:
                if k.arg=='evidence_scope':k.value=ast.Constant('One new ordinary common-pair-scale constrained400 producer; old S32 endpoints remain separately sealed')
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            n.value=n.value.replace('All three unavailable to scoring; partial GA files retained without upgrading zero-step to PASS','New candidate unavailable to scoring; old S32 endpoints retain their original seals')
    ast.fix_missing_locations(new);return old,new

def worker(c,window_id):
    s32=load_s32(c)
    namespace=dict(vars(s32));namespace.update(__file__=str(Path(__file__).resolve()),ENDPOINTS=(ENDPOINT,),save_candidate=save_candidate,
        observer_type=lambda b,r,s30,local:observer_type(b,r,s30,local,s32))
    _,node=derive_window_worker(c['s32_runner']);exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__))+'::window','exec'),namespace)
    namespace['worker'](c,window_id)

def derive_dispatch(s32_path):
    old=unique_function(s32_path,'dispatch');new=copy.deepcopy(old)
    for n in ast.walk(new):
        if isinstance(n,ast.keyword) and n.arg=='all_three_endpoints_available':n.arg='candidate_available'
        if isinstance(n,ast.Constant) and isinstance(n.value,str):n.value=n.value.replace('all four windows and all three endpoints retained','all four windows and the one new candidate retained; old48 rows unchanged')
    ast.fix_missing_locations(new);return old,new

def dispatch(c,path):
    s32=load_s32(c);_,new=derive_dispatch(c['s32_runner'])
    namespace=dict(vars(s32));namespace.update(__file__=str(Path(__file__).resolve()))
    exec(compile(ast.Module(body=[new],type_ignores=[]),str(Path(__file__))+'::dispatch','exec'),namespace)
    namespace['dispatch'](c,path)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['worker','dispatch']);p.add_argument('--window')
    p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True);args=p.parse_args();c=contract(args.contract,args.sha256)
    if args.command=='worker':worker(c,args.window)
    else:dispatch(c,args.contract)
