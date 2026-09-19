#!/usr/bin/env python3
"""Artificial-only S14E control-flow/schema checks; never loads real arrays/model."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Fresh artificial output directory required')
    args.output.mkdir(parents=True)
    path=Path(__file__).with_name('run_s14e_state_reuse_queries.py')
    spec=importlib.util.spec_from_file_location('tested_predictor',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    result=dict(schema='s14e-predictor-artificial-v1',started_utc=datetime.now(timezone.utc).isoformat(),
                status='RUNNING', source_sha256=mod.sha(path), real_npz_decodes=0,
                real_model_calls=0, checkpoint_reads=0, checks=[], runtime_cases=[])
    def check(name, fn, reject=False):
        try: fn()
        except (ValueError,KeyError) as e:
            if not reject: raise
            result['checks'].append(dict(name=name, expected_rejection=True, error=str(e),passed=True))
        else:
            if reject: raise AssertionError('Did not reject: '+name)
            result['checks'].append(dict(name=name,passed=True))
    state={k:np.ones(shape,dtype=dtype) for k,(shape,dtype) in mod.STATE_SCHEMA.items()}
    state_ids={k:mod.tensor_id(v) for k,v in state.items()}
    check('state exact',lambda:mod.validate_state(state,state_ids))
    check('state missing field',lambda:mod.validate_state({k:v for k,v in state.items() if k!='mem'},state_ids),True)
    for k in mod.FIELDS:
        values=state.copy(); values[k]=values[k].copy(); values[k].flat[0]+=1
        check('state byte change '+k,lambda v=values:mod.validate_state(v,state_ids),True)
    output={k:np.ones(shape,np.float32) for k,shape in mod.OUTPUT_SHAPES.items()}
    check('six exact outputs',lambda:mod.compare_exact(output,output))
    for k in mod.OUTPUT_SHAPES:
        changed=output.copy(); changed[k]=changed[k].copy(); changed[k].flat[0]+=0.125
        check('parity changed '+k,lambda c=changed:mod.compare_exact(c,output),True)
    changed=output.copy(); changed['conf']=changed['conf'].astype(np.float64)
    check('parity dtype',lambda:mod.compare_exact(changed,output),True)
    zero={k:np.zeros(shape,np.float32) for k,shape in mod.OUTPUT_SHAPES.items()}
    changed={k:v.copy() for k,v in zero.items()}; changed['conf'].flat[0]=-0.0
    check('signed zero bytes differ',lambda:mod.compare_exact(changed,zero),True)
    for key,value in [('nan',float('nan')),('inf',float('inf'))]:
        changed=output.copy(); changed['rgb']=changed['rgb'].copy(); changed['rgb'].flat[0]=value
        check('nonfinite '+key,lambda c=changed:mod.validate_outputs(c),True)
    changed=output.copy(); changed['extra']=np.zeros(1)
    check('extra tensor',lambda:mod.validate_outputs(changed),True)
    poses=np.tile(np.eye(4,dtype=np.float64)[None],(4,1,1))
    K=np.tile(np.eye(3,dtype=np.float64)[None],(4,1,1))
    rays=np.ones((4,224,224,6),np.float32)
    condition=dict(target_poses=poses,K=K,ray_maps=rays)
    check('condition exact schema',lambda:mod.validate_conditions(condition))
    for key, value in [('target_poses',poses.astype(np.float32)),('K',K[:3]),('ray_maps',rays.astype(np.float64))]:
        changed=condition.copy(); changed[key]=value
        check('condition schema reject '+key,lambda c=changed:mod.validate_conditions(c),True)
    changed={k:v.copy() for k,v in condition.items()}; changed['target_poses'][0,3,0]=1
    check('pose bottom row',lambda:mod.validate_conditions(changed),True)
    changed={k:v.copy() for k,v in condition.items()}; changed['K'][0,0,0]=0
    check('zero focal',lambda:mod.validate_conditions(changed),True)
    identities={}; manifest={'schema':'s14e-state-reuse-manifest-v1','contract':dict(target_count=4,query_count=5,dummy_values=['zero']*5,query_flags=mod.FLAGS.copy(),device='cpu',cpu_threads=8,seed=0,size=[224,224],dtype='float32',wall_seconds=600,monitored_rss_bytes=34359738368,history_rgb_allowed=False,target_rgb_allowed=False,target_depth_allowed=False),'identities':identities}
    for role in mod.INPUT_ROLES+['checkpoint','rope_check','runner']:
        manifest[role]=str((args.output/role).resolve());identities[manifest[role]]='0'*64
    check('fixed manifest contract',lambda:mod.validate_contract(manifest))
    for key,val in [('target_count',5),('query_count',4),('cpu_threads',4),('target_rgb_allowed',True),('target_depth_allowed',True),('dummy_values',['nan']*5)]:
        changed=copy.deepcopy(manifest);changed['contract'][key]=val
        check('contract reject '+key,lambda c=changed:mod.validate_contract(c),True)
    for name in ['fake.png','fake.npz','groundtruth.txt']:
        changed=copy.deepcopy(manifest);changed['identities'][str((args.output/name).resolve())]='0'*64
        check('unpermitted hash '+name,lambda c=changed:mod.validate_contract(c),True)
    for case in ['success','parity_failure','state_mutation','encoder_violation','nonfinite_output','model_exception']:
        out=args.output/case;out.mkdir()
        report=dict(query_runs=[],counters=dict(query_call_attempts=0,query_calls=0,query_image_encoder_batches=0,query_ray_encoder_calls=0))
        anchors=tuple(torch.from_numpy(state[k].copy()) for k in mod.FIELDS)
        def phase(name):
            report['phase']=name;mod.write(out/'run_metadata.json',report)
        def fake_inference(view,anchor,model,device,verbose):
            assert device=='cpu' and verbose is False
            assert set(view['img'].numpy().reshape(-1))=={0.0}
            assert {k:view[k].tolist() for k in mod.FLAGS}=={k:[v] for k,v in mod.FLAGS.items()}
            report['counters']['query_ray_encoder_calls']+=1
            if case=='model_exception':raise ValueError('artificial model failure')
            current={k:torch.from_numpy(v.copy()) for k,v in output.items()}
            if case=='parity_failure':current['conf'].view(-1)[0]+=1
            if case=='state_mutation':anchor[0].view(-1)[0]+=1
            if case=='encoder_violation':report['counters']['query_image_encoder_batches']+=1
            if case=='nonfinite_output':current['conf'].view(-1)[0]=float('nan')
            return {'pred':current}
        error=None
        try:
            arrays=mod.execute_queries(torch,np,fake_inference,None,anchors,state_ids,condition,condition,output,report,out,phase)
        except ValueError as e:error=str(e)
        if case=='success':
            assert error is None and len(arrays)==30 and report['counters']['query_calls']==5
            assert len(list(out.glob('query_call_*.npz')))==5
            assert report['parity_all_six_outputs_exact'] is True
            assert all(r['status']=='PASS' for r in report['query_runs'])
        else:
            assert error is not None and report['counters']['query_call_attempts']==1
            assert len(report['query_runs'])==1
            if case=='model_exception':
                assert report['counters']['query_calls']==0 and not list(out.glob('query_call_*.npz'))
            else:
                assert report['counters']['query_calls']==1 and (out/'query_call_0.npz').exists()
                assert report['query_runs'][0]['status']=='RETURNED'
        report.update(status='EXPECTED_SUCCESS' if error is None else 'EXPECTED_FAILURE',error=error)
        mod.write(out/'run_metadata.json',report)
        result['runtime_cases'].append(dict(name=case, passed=True, query_attempts=report['counters']['query_call_attempts'],
            query_returns=report['counters']['query_calls'],output_npz_count=len(list(out.glob('query_call_*.npz'))),error=error))
    result.update(status='PASS', completed_utc=datetime.now(timezone.utc).isoformat(),
                  scalar_checks=len(result['checks']),runtime_case_count=len(result['runtime_cases']))
    mod.write(args.output/'receipt.json',result)
    print(json.dumps({k:result[k] for k in ['status','scalar_checks','runtime_case_count','real_npz_decodes','real_model_calls']}))

if __name__=='__main__':main()
