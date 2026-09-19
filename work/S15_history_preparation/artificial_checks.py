"""Artificial-only checks. No images, checkpoint, or real prediction archives are read."""
from pathlib import Path
import copy
import importlib.util
import json
import shutil
import sys
import traceback
from datetime import datetime, timezone
import numpy as np
import torch
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s15', ROOT / 'scripts/run_s15_history.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
started = datetime.now(timezone.utc).isoformat()
checks = []

def record(name, function, fails=False):
    try:
        function()
    except (ValueError, RuntimeError) as e:
        if not fails: raise
        checks.append(dict(name=name, status='PASS', expected_error=str(e)))
    else:
        if fails: raise AssertionError(name + ' did not reject')
        checks.append(dict(name=name, status='PASS'))

base = HERE / 'synthetic_inputs'
repo = str(base / 'repo')
runner = str(base / 'scripts/run_s15_history.py')
ckpt = str(base / 'weights.pth')
rope = str(base / 'rope.json')
identities = {str(Path(repo) / f'module{i}.py'): '0'*64 for i in range(99)}
identities.update({runner:'0'*64, ckpt:r.CHECKPOINT_SHA256, rope:'0'*64, str(Path(runner).parent/'cut3r_rope_compat.py'):'0'*64})
items=[]
for i in range(20):
    p=str(base/f'rgb{i}.png'); identities[p]='0'*64
    items.append(dict(index=i,path=p,sha256='0'*64))
m=dict(schema='s15-history-manifest-v1',repo=repo,commit=r.COMMIT,python=str(base/'bin/python'),runner=runner,checkpoint=ckpt,rope_check=rope,history_images=items,identities=identities,contract=copy.deepcopy(r.EXPECTED_CONTRACT),control_files=[])
record('valid_manifest_artificial_paths_no_file_reads',lambda:r.validate_contract(m))
def mutate(fn):
    x=copy.deepcopy(m);fn(x);r.validate_contract(x)
record('nineteen_histories',lambda:mutate(lambda x:x['history_images'].pop()),True)
record('history_order',lambda:mutate(lambda x:x['history_images'][0].update(index=1)),True)
record('duplicate_path',lambda:mutate(lambda x:x['history_images'][1].update(path=x['history_images'][0]['path'])),True)
record('target_png_identity',lambda:mutate(lambda x:x['identities'].update({str(base/'target.png'):'0'*64})),True)
record('target_npz_identity',lambda:mutate(lambda x:x['identities'].update({str(base/'target.npz'):'0'*64})),True)
record('dataset_gt_identity',lambda:mutate(lambda x:x['identities'].update({str(base/'groundtruth.txt'):'0'*64})),True)
record('image_control_disguised',lambda:mutate(lambda x:x['control_files'].append(x['history_images'][0]['path'])),True)
record('wrong_checkpoint',lambda:mutate(lambda x:x['identities'].update({ckpt:'0'*64})),True)
record('query_enabled',lambda:mutate(lambda x:x['contract'].update(query_count=1)),True)
record('gt_allowed',lambda:mutate(lambda x:x['contract'].update(target_depth_allowed=True)),True)
record('state_update_disabled',lambda:mutate(lambda x:x['contract']['history_flags'].update(update=False)),True)
record('wrong_upstream_count',lambda:mutate(lambda x:x['identities'].pop(str(Path(repo)/'module0.py'))),True)
record('unexpected_architecture_state_dtype',lambda:r.validate_array(np.zeros((1,768,2),np.float32),[1,768,2],'int64','state_pos'),True)
record('nonfinite_gate',lambda:r.validate_array(np.array([np.nan],np.float32),[1],'float32','artificial'),True)
record('tensor_byte_identity_detects_ulp',lambda:r.require(r.tensor_id(np.array([1],np.float32))!=r.tensor_id(np.nextafter(np.array([1],np.float32),np.float32(2))), 'byte sensitivity'))
images=[dict(img=torch.zeros((1,3,224,224)),true_shape=np.array([[224,224]],np.int32),idx=i,instance=str(i)) for i in range(20)]
views=r.make_views(images,torch)
record('twenty_channel_last_masked_ray_views',lambda:r.require(len(views)==20 and all(v['ray_map'].shape==(1,224,224,6) and bool(torch.isnan(v['ray_map']).all()) and all(v[k].item()==val for k,val in r.FLAGS.items()) for v in views),'view masks'))
bad_images=images.copy();bad_images[0]=dict(images[0],idx=4)
record('loader_order_enforced',lambda:r.make_views(bad_images,torch),True)

pred={k:torch.ones(shape,dtype=torch.float32) for k,shape in r.OUTPUT_SHAPES.items()}
pred['camera_pose']=torch.tensor([[0,0,0,1,0,0,0]],dtype=torch.float32)
state=tuple(torch.zeros(shape,dtype=torch.int64 if dtype=='int64' else torch.float32) for shape,dtype in r.STATE_SCHEMA.values())
# Correct explicit field order, independent of dictionary insertion assumptions.
state=tuple(torch.zeros(r.STATE_SCHEMA[k][0],dtype=torch.int64 if r.STATE_SCHEMA[k][1]=='int64' else torch.float32) for k in r.FIELDS)
def decoder(enc):
    r.require(list(enc.shape)==[20,7], 'decoder received all history encodings')
    return torch.eye(4).repeat(20,1,1)
def fake_result(mode):
    def f(views,model,device,verbose=False):
        if mode=='raise': raise RuntimeError('artificial model exception')
        histories=[{k:v.clone() for k,v in pred.items()} for i in range(20)]
        if mode=='nonfinite': histories[7]['pts3d_in_self_view'][0,0,0,0]=torch.nan
        if mode=='missing_output': histories[7].pop('conf')
        if mode=='short_history': histories=histories[:19]
        return dict(pred=histories), [state]*21
    return f
for mode in ['success','raise','nonfinite','missing_output','short_history']:
    out=HERE/f'artificial_{mode}'
    if out.exists(): raise ValueError('Artificial result directory already exists: '+str(out))
    out.mkdir()
    report=dict(counters=dict(history_forward_attempts=0,history_forward_calls=0,history_frames_saved=0))
    phases=[]
    def run(mode=mode,out=out,report=report,phases=phases):
        r.execute_history(torch,np,fake_result(mode),decoder,None,views,report,out,phases.append)
    record('runtime_'+mode,run,mode!='success')
    if mode=='success':
        with np.load(out/'predictions.npz',allow_pickle=False) as a:
            r.require(len(a.files)==120,'All six tensors across twenty histories saved')
        with np.load(out/'history_poses.npz',allow_pickle=False) as a:
            r.require(set(a.files)=={'history_pose_encodings','history_poses'},'Pose key domain')
        with np.load(out/'state.npz',allow_pickle=False) as a:
            r.require(set(a.files)==set(r.FIELDS),'Five state domain')
        r.require(report['counters']==dict(history_forward_attempts=1,history_forward_calls=1,history_frames_saved=20),'Call/save counters')
        checks.append(dict(name='runtime_success_payload_domains_and_counters',status='PASS'))
    if mode in ['nonfinite','missing_output']:
        r.require((out/'predictions.npz').exists() and (out/'state.npz').exists() and not (out/'history_poses.npz').exists(),'Invalid result persisted before gates')
        checks.append(dict(name='runtime_'+mode+'_evidence_preserved',status='PASS'))
    (out/'artificial_call_receipt.json').write_text(json.dumps(dict(mode=mode,phases=phases,counters=report['counters']),indent=2)+'\n')

# No source import or model load: complete main failure must retain failed metadata.
invalid=HERE/'artificial_invalid_manifest.json'
invalid.write_text(json.dumps(dict(schema='wrong'))+'\n')
argv=sys.argv
sys.argv=['run_s15_history.py','--manifest',str(invalid),'--output',str(HERE/'artificial_main_failure')]
try:
    result=r.main()
finally:
    sys.argv=argv
failed=json.loads((HERE/'artificial_main_failure/run_metadata.json').read_text())
r.require(result==1 and failed['status']=='FAILED' and failed['counters']['history_forward_calls']==0,'Main failure persistence')
checks.append(dict(name='main_failure_metadata_no_model',status='PASS'))
receipt=dict(schema='s15-history-artificial-checks-v1',status='PASS',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),checks=checks,check_count=len(checks),real_image_decodes=0,real_model_runs=0,checkpoint_reads=0,real_npz_array_reads=0,artificial_runtime_cases=5,python=sys.executable,torch=torch.__version__,numpy=np.__version__)
r.write(HERE/'artificial_checks.json',receipt)
print(json.dumps(dict(status='PASS',checks=len(checks))))
