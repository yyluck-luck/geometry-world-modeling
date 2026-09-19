"""S30 draft: extend each sealed S29 initialization by the original 400 steps."""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


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


def contract(path,expected):
    require(sha(path)==expected,'Exact frozen S30 contract SHA required');c=read(path)
    require(c['status']=='FROZEN' and c['schema']=='s30-s29-initialized-400-v1','Candidate cannot run')
    require(c['arms']==['C2t','C2a'] and c['steps_per_arm']==400,'Only both predefined 400-step arms')
    require(c['seconds_per_arm']==120 and c['rss_bytes_per_arm']==4*1024**3,'Frozen resource budget')
    for p,h in c['identities'].items():require(sha(p)==h,'Changed identity: '+p)
    parent=read(c['parent_manifest'])
    require(c['gt_depth_frames']==parent['scoring']['gt_depth_frames'][:4],'Same four inherited scoring identities')
    require(c['scoring_policy']=={k:parent['scoring'][k] for k in c['scoring_policy']},'Same original scoring rules')
    validation=read(c['s29_validation_receipt'])
    require(validation['status']=='PASS_VALIDATION_EXECUTED' and validation['hypothesis_passed'] is True and validation['contract_sha256']==c['s29_contract_sha256'],'S29 complete numerical/identity verdict')
    c['_sha']=expected;return c


def derive_observer(path):
    old=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='observer_type']
    require(len(old)==1,'One frozen S28 observer factory');old=old[0];counts={k:0 for k in ['reference_block','original_grad_condition','active_condition','reference_report','mst_label']}
    labels={'s28_initialization':'s30_initialization','s28_gradient_steps':'s30_gradient_steps',
            's28_objective_forward_counts':'s30_objective_forward_counts','S28_first_step_gate_passed':'S30_first_step_gate_passed'}
    class Adapt(ast.NodeTransformer):
        def visit_If(self,node):
            if ast.unparse(node.test)=="arm == 'gradient_only'":
                counts['reference_block']+=1
                require(ast.unparse(node.body[-1])=='self.patch(opt.PointCloudOptimizer, \'get_depthmaps\', lambda old_getter: patched_getter)','Original getter installation')
                return [ast.parse('verify_s29_initial_state(self,c,arm,loss_before,np)').body[0],copy.deepcopy(node.body[-1])]
            return self.generic_visit(node)
        def visit_Compare(self,node):
            expression=ast.unparse(node)
            if expression=="arm == 'original'":counts['original_grad_condition']+=1;return ast.copy_location(ast.Constant(False),node)
            if expression=="arm == 'gradient_only'":counts['active_condition']+=1;return ast.copy_location(ast.Constant(True),node)
            return self.generic_visit(node)
        def visit_keyword(self,node):
            if node.arg=='cross_arm_raw_exact':counts['reference_report']+=1;node.arg='reference_S29_raw_exact';node.value=ast.Constant(True);return node
            if node.arg=='original_mst_preserved':counts['mst_label']+=1;node.arg='s29_initialization_path_preserved'
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if isinstance(node.value,str) and node.value in labels:node.value=labels[node.value]
            return node
    new=Adapt().visit(copy.deepcopy(old));ast.fix_missing_locations(new)
    require(counts==dict(reference_block=1,original_grad_condition=2,active_condition=1,reference_report=1,mst_label=1),'Unexpected observer adaptation scope')
    return old,new,counts


def verify_s29_initial_state(observer,c,arm,loss_before,np):
    reference=c['s29_reference'][arm];rec=read(reference['receipt'])
    require(rec['status']=='PASS_INITIALIZATION_EXECUTED' and rec['contract_sha256']==c['s29_contract_sha256'] and rec['arm']==arm,'Own sealed S29 initialization')
    require(rec['counts']==dict(MST=1,PnP=3,alignment=1,objective=1,backward=0,Adam=0,clean=0,model=0,GT=0),'S29 saved source is a zero-step initialization')
    for name,item in reference['files'].items():require(sha(item['path'])==item['sha256']==rec['outputs'][name],'S29 sealed artifact: '+name)
    require(len(observer.initial_meta)==33 and read(reference['files']['initial_raw_metadata.json']['path'])==observer.initial_meta,'Exactly all 33 raw names/shapes/dtypes/flags/hash entries match own S29')
    with np.load(reference['files']['initial_raw.npz']['path'],allow_pickle=False) as z:
        require(set(z.files)==set(observer.initial_arrays),'Complete S29 raw tensor set')
        for name,arr in observer.initial_arrays.items():
            require(z[name].shape==arr.shape and z[name].dtype==arr.dtype and z[name].tobytes()==arr.tobytes(),'Initial raw bytes differ from own S29: '+name)
    with np.load(reference['files']['initial_decoded.npz']['path'],allow_pickle=False) as z:
        require(z['objective'].dtype==loss_before.dtype and z['objective'].shape==loss_before.shape and z['objective'].tobytes()==loss_before.tobytes(),'Own S29 initial objective bytes')
    with np.load(reference['files']['alignment.npz']['path'],allow_pickle=False) as z:
        for name,arr in observer.alignment_values.items():
            require(z[name].shape==arr.shape and z[name].dtype==arr.dtype and z[name].tobytes()==arr.tobytes(),'Own S29 alignment tuple/input identity: '+name)
    write(observer.out/'s29_reference_gate.json',dict(status='PASS',arm=arm,s30_contract_sha256=c['_sha'],
        s29_receipt_sha256=sha(reference['receipt']),complete_raw_tensor_count=33,raw_exact=True,objective_exact=True,alignment_exact=True,
        meaning='New original-path initialization matches its own saved S29, not an identical state across C2t and C2a'))


def observer_type(b,r,c,arm):
    _,node,_=derive_observer(c['s28_runner']);namespace=dict(vars(r));namespace['verify_s29_initial_state']=verify_s29_initial_state
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__).resolve())+'::observer','exec'),namespace)
    Parent=namespace['observer_type'](b,c,arm)
    class ScaleObserver(Parent):
        def install(self):
            super().install();init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses');calls=0
            def control(old):
                def call(src,target):
                    nonlocal calls
                    require(calls==0,'Exactly one original scale alignment');calls+=1
                    source=b.array(src);given=b.array(target);s0,R0,T0=old(src,target)
                    s=s0 if arm=='C2t' else (1.0 if isinstance(s0,float) else s0.new_tensor(1.0))
                    T=target[:,:3,3].mean(0)-s*(R0@src[:,:3,3].mean(0))
                    self.alignment_values=dict(source_c2w=source,target_c2w=given,s0=b.array(s0),R0=b.array(R0),T0=b.array(T0),s_used=b.array(s),R_used=b.array(R0),T_used=b.array(T))
                    import numpy as np
                    np.savez_compressed(self.out/'controlled_alignment.npz',**self.alignment_values)
                    self.report['s30_alignment_calls']=calls
                    return s,R0,T
                return call
            self.patch(init,'align_multiple_poses',control)
    return ScaleObserver


def worker(c,arm):
    require(arm in c['arms'],'Unknown arm');b=module(c['parent_runner'],'s30_original_producer');r=module(c['s28_runner'],'s30_s28_observation')
    m=b.manifest(c['parent_manifest_sha256']);out=Path(c['output_root'])/arm
    require(not out.exists(),'No repeated arm');b.OUT=Path(c['output_root']);b.SceneObserver=observer_type(b,r,c,arm)
    original_write=b.write
    def bound_write(path,value):
        path=Path(path)
        if path.parent==out and path.name in ['receipt.json','inputs_seal.json']:
            value=dict(value,s30_contract_sha256=c['_sha'],evidence_scope='400 original steps from own byte-matched S29 scale initialization, ordinary engineering control')
            if path.name=='receipt.json' and value.get('status')=='PASS':
                require(value['observer']['s30_alignment_calls']==1 and len(value['observer']['pnp_calls'])==3,'Exact original initialization counts')
                for p,h in {**m['identities'],**c['identities']}.items():require(sha(p)==h,'Identity changed during producer: '+p)
                value['parent_identities_rechecked']=True
        return original_write(path,value)
    b.write=bound_write
    _,node=r.derive_worker(c['parent_runner'])
    node.body[0]=ast.parse("require(mode in ('C2t','C2a'),'S30 two common4 scale controls')").body[0];ast.fix_missing_locations(node)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__).resolve())+'::producer','exec'),vars(b));b.ga_worker(m,arm)


def dispatch(c,path):
    b=module(c['parent_runner'],'s30_original_supervisor');b.WORK=Path(c['execution_root']);b.WORK.mkdir(parents=True,exist_ok=True)
    target=b.WORK/'dispatch_receipt.json';require(not target.exists(),'No repeated dispatch')
    receipt=dict(status='RUNNING',started_utc=utc(),contract_sha256=c['_sha'],phases=[]);write(target,receipt)
    try:
        for arm in c['arms']:
            command=[sys.executable,str(Path(__file__).resolve()),'worker','--arm',arm,'--contract',str(path),'--sha256',c['_sha']]
            b.supervised(command,arm,120,4*1024**3);receipt['phases'].append(arm);write(target,receipt)
        command=[sys.executable,c['scorer'],'--contract',str(path),'--sha256',c['_sha']]
        b.supervised(command,'scoring',120,2*1024**3)
        receipt.update(status='PASS',completed_utc=utc(),new_Adam_steps=800,new_MST=2,new_PnP=6,new_model_forwards=0);write(target,receipt)
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=utc(),error=str(e));write(target,receipt);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['dispatch','worker']);p.add_argument('--arm')
    p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True);args=p.parse_args();c=contract(args.contract,args.sha256)
    if args.command=='worker':worker(c,args.arm)
    else:dispatch(c,args.contract)
