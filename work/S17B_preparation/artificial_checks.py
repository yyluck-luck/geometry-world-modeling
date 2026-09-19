"""Artificial contract/shape/persistence tests; no checkpoint/RGB/GT/model imports."""
from pathlib import Path
import importlib.util,json,copy,datetime,hashlib,sys,tempfile
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s17b',ROOT/'scripts/run_s17b_dpt_history.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
checks=[]
def check(name,fn):
 try:fn();checks.append({'name':name,'status':'PASS'})
 except Exception as e:checks.append({'name':name,'status':'FAIL','error':repr(e)});raise

def fails(fn):
 try:fn()
 except (ValueError,KeyError):return
 raise AssertionError('Expected refusal')
old=json.loads((ROOT/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json').read_text());repo=Path(old['repo'])
m={k:old[k]for k in ['repo','commit','python','rope_check']};m.update(schema='s17b-dpt-two-frame-manifest-v1',runner=str(ROOT/'scripts/run_s17b_dpt_history.py'),checkpoint=str(ROOT/'work/S17B_preparation/artificial_only_512.pth'),history_images=copy.deepcopy(old['history_images'][:2]),control_files=[],contract=copy.deepcopy(mod.EXPECTED_CONTRACT))
ids={p:d for p,d in old['identities'].items()if Path(p).is_relative_to(repo)and Path(p).suffix=='.py'}
ids.update({m['runner']:'0'*64,m['checkpoint']:mod.CHECKPOINT_SHA256,m['rope_check']:'0'*64,str(ROOT/'scripts/cut3r_rope_compat.py'):'0'*64})
ids.update({i['path']:i['sha256']for i in m['history_images']});m['identities']=ids
check('valid abstract 2-frame manifest has exact allowed identity set',lambda:mod.validate_contract(m))
for label,mut in [
 ('old schema rejected',lambda x:x.update(schema='s15-history-manifest-v1')),
 ('224 contract rejected',lambda x:x['contract'].update(size=[224,224])),
 ('linear head rejected',lambda x:x['contract'].update(head_type='linear')),
 ('extra history rejected',lambda x:x['history_images'].append(copy.deepcopy(x['history_images'][1]))),
 ('permuted history rejected',lambda x:x['history_images'].reverse()),
 ('substituted original RGB hash rejected',lambda x:x['history_images'][0].update(sha256='f'*64)),
 ('wrong checkpoint SHA rejected',lambda x:x['identities'].update({x['checkpoint']:'f'*64})),
 ('GT image extra identity rejected',lambda x:x['identities'].update({str(ROOT/'data/forbidden_depth.png'):'0'*64})),
 ('missing upstream rejected',lambda x:x['identities'].pop(next(p for p in x['identities']if Path(p).is_relative_to(repo)))),
 ('CPU ceiling mismatch rejected',lambda x:x['contract'].update(monitored_rss_bytes=64*1024**3)),
 ('noncanonical identity rejected',lambda x:x['identities'].update({str(ROOT)+'/../bad.json':'0'*64})),
 ('unexpected query contract rejected',lambda x:x['contract'].update(query_count=1)),
]:
 mm=copy.deepcopy(m);mut(mm);check(label,lambda mm=mm:fails(lambda:mod.validate_contract(mm)))
images=[{'img':torch.zeros((1,3,384,512)), 'true_shape':np.array([[384,512]],dtype=np.int32),'idx':i,'instance':str(i)}for i in range(2)]
check('correct non-square 512 loader tensors accepted',lambda:mod.make_views(images,torch))
wrong=[dict(i)for i in images];wrong[0]['img']=torch.zeros((1,3,512,384));check('transposed width/height rejected',lambda:fails(lambda:mod.make_views(wrong,torch)))
wrong=[dict(i)for i in images];wrong[0]['true_shape']=np.array([[512,384]],dtype=np.int32);check('wrong true shape rejected',lambda:fails(lambda:mod.make_views(wrong,torch)))
wrong=[dict(i)for i in images];wrong[0]['img']=wrong[0]['img'].clone();wrong[0]['img'][0,0,0,0]=float('nan');check('nonfinite input rejected',lambda:fails(lambda:mod.make_views(wrong,torch)))
check('dtype schema refuses half outputs',lambda:fails(lambda:mod.validate_array(np.zeros((1,7),dtype=np.float16),[1,7],'float32','pose')))

def preds():
 ps=[]
 for i in range(2):
  p={k:torch.ones(tuple(v),dtype=torch.float32)for k,v in mod.OUTPUT_SHAPES.items()}
  p['camera_pose']=torch.tensor([[0.,0.,0.,1.,0.,0.,0.]])
  ps.append(p)
 return ps
state=tuple(torch.zeros(tuple(v[0]),dtype=torch.int64 if v[1]=='int64'else torch.float32)for v in mod.STATE_SCHEMA.values())
views=mod.make_views(images,torch)
def fake_pose(e):return torch.eye(4,dtype=torch.float32).repeat(2,1,1)
def simulate(label,bad=False):
 dest=OUT/label;dest.mkdir(exist_ok=False)
 p=preds()
 if bad:p[1]['conf_self'][0,0,0]=float('nan')
 def fake_inference(v,model,device,verbose=False):return {'pred':p},[state,state,state]
 r={'counters':{'history_forward_attempts':0,'history_forward_calls':0}};ph=[]
 fn=lambda:mod.execute_history(torch,np,fake_inference,fake_pose,None,views,r,dest,ph.append)
 if bad:
  fails(fn);assert(dest/'predictions.npz').exists()and(dest/'state.npz').exists()
  with np.load(dest/'predictions.npz')as z:assert np.isnan(z['frame1_conf_self'][0,0,0])
 else:
  fn()
  with np.load(dest/'predictions.npz')as z:assert len(z.files)==12
  with np.load(dest/'state.npz')as z:assert len(z.files)==5
  with np.load(dest/'history_poses.npz')as z:assert len(z.files)==2 and z['history_poses'].shape==(2,4,4)
  assert r['counters']['history_frames_saved']==2 and r['raw_predictions_saved_before_gates']
 (dest/'artificial_receipt.json').write_text(json.dumps({'label':'ARTIFICIAL_NO_MODEL','report':r,'phases':ph},indent=2)+'\n')
check('artificial six-head plus state plus pose output contract 19 arrays',lambda:simulate('artificial_valid'))
check('artificial NaN failure preserves raw outputs before finite gate',lambda:simulate('artificial_nan_refusal',True))
result={'schema':'s17b-artificial-preparation-checks-v1','status':'PASS'if all(x['status']=='PASS'for x in checks)else'FAIL','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runner_sha256':hashlib.sha256((ROOT/'scripts/run_s17b_dpt_history.py').read_bytes()).hexdigest(),'check_count':len(checks),'checks':checks,'real_rgb_decodes':0,'real_gt_reads':0,'weight_payload_reads':0,'weight_deserializations':0,'real_model_instantiations':0,'real_model_forwards':0,'only_tensor_inputs':'locally created zero/one/NaN tensors with fake inference callable, no external model imports','scope':'software boundary evidence, not 512 checkpoint or video success'}
(OUT/'artificial_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['status','check_count','runner_sha256']},indent=2))
