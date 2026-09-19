"""Independent artificial review: no real NPZ/images/trajectory/checkpoint/model."""
import copy,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');OUT=ROOT/'work/S14E_pre_run_review/predictor_independent_v1'
OUT.mkdir()
SRC=ROOT/'scripts/run_s14e_state_reuse_queries.py'
spec=importlib.util.spec_from_file_location('independently_reviewed_predictor',SRC);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def now():return datetime.now(timezone.utc).isoformat()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
result={'started_utc':now(),'status':'RUNNING','source_path':str(SRC),'source_sha256':digest(SRC),'real_npz_decodes':0,'real_rgb_decodes':0,'real_depth_decodes':0,'real_trajectory_decodes':0,'checkpoint_reads':0,'model_calls':0,'checks':[],'runtime_cases':[],'main_early_failure_cases':[]}
def check(name,value):
 if not value:raise AssertionError(name)
 result['checks'].append({'name':name,'pass':True})
def rejected(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError):check(name,True)
 else:raise AssertionError('Expected rejection: '+name)
state={k:np.zeros(shape,dtype=dtype) for k,(shape,dtype) in p.STATE_SCHEMA.items()}
for ix,k in enumerate(p.FIELDS):state[k].flat[-1]=ix+1
ids={k:p.tensor_id(a) for k,a in state.items()}
poses=np.tile(np.eye(4,dtype=np.float64),(4,1,1));poses[:,0,3]=[0.25,0.5,0.75,1.]
K=np.tile(np.diag([245.,245.,1.]),(4,1,1));rays=np.zeros((4,224,224,6),np.float32)
for ix in range(4):rays[ix]=ix+1
conditions={'target_poses':poses,'K':K,'ray_maps':rays}
parity={'target_poses':poses.copy(),'K':K.copy(),'ray_maps':np.full_like(rays,9.)}
reference={k:np.full(shape,.5+(ix/16),np.float32) for ix,(k,shape) in enumerate(p.OUTPUT_SHAPES.items())}
# New control cases target later calls, exercising partial-result preservation.
for case,failcall,mode in [('success',None,None),('second_call_exception',1,'exception'),('fourth_call_nonfinite',3,'nonfinite'),('last_call_state_pos_mutation',4,'state'),('last_call_extra_tensor',4,'extra'),('second_call_missing_ray_encoder',1,'encoder')]:
 out=OUT/case;out.mkdir();report={'query_runs':[],'counters':{'query_call_attempts':0,'query_calls':0,'query_image_encoder_batches':0,'query_ray_encoder_calls':0}}
 anchor=tuple(torch.from_numpy(a.copy()) for a in state.values());phases=[];seen=[]
 def phase(name):
  phases.append(name);p.write(out/'run_metadata.json',report)
 def invoke(view,stored,model,device,verbose):
  ix=report['counters']['query_call_attempts']-1;target=0 if ix==0 else ix-1
  wanted=9. if ix==0 else float(target+1)
  check(case+f'/call{ix}/condition_array_routing',bool(torch.all(view['ray_map']==wanted)))
  check(case+f'/call{ix}/condition_pose_routing',float(view['camera_pose'][0,0,3])==float(poses[target,0,3]))
  check(case+f'/call{ix}/zero_and_flags',not bool(torch.any(view['img'])) and {k:bool(view[k][0]) for k in p.FLAGS}==p.FLAGS)
  check(case+f'/call{ix}/true_shape_dtype',view['true_shape'].dtype==torch.int64)
  seen.append(ix)
  if not(mode=='encoder' and ix==failcall):report['counters']['query_ray_encoder_calls']+=1
  if mode=='exception' and ix==failcall:raise RuntimeError('Independent artificial call exception')
  values={k:torch.from_numpy(a.copy()) for k,a in reference.items()}
  if mode=='nonfinite' and ix==failcall:values['pts3d_in_other_view'][0,100,99,2]=float('inf')
  if mode=='state' and ix==failcall:stored[1][0,100,0]+=1
  if mode=='extra' and ix==failcall:values['unexpected']=torch.ones(1)
  return {'pred':values}
 error=None;outputs=None
 with patch.object(np,'load',side_effect=AssertionError('No NPZ decoding allowed during orchestration checks')):
  try:outputs=p.execute_queries(torch,np,invoke,None,anchor,ids,parity,conditions,reference,report,out,phase)
  except (ValueError,RuntimeError) as e:error=str(e)
 if failcall is None:
  check(case+'/five_calls_all_saved',error is None and len(outputs)==30 and len(list(out.glob('query_call_*.npz')))==5)
  check(case+'/exact_parity',report['parity_all_six_outputs_exact'] is True)
 else:
  check(case+'/stops_at_expected_call',error is not None and seen==list(range(failcall+1)))
  expected_returns=failcall if mode=='exception' else failcall+1
  check(case+'/completed_count_and_files',report['counters']['query_calls']==expected_returns and len(list(out.glob('query_call_*.npz')))==expected_returns)
  check(case+'/old_successes_preserved',all((out/f'query_call_{i}.npz').exists() for i in range(failcall)))
  if mode!='exception':check(case+'/return_saved_before_rejection',f'query_call_{failcall}_saved_before_gates' in phases and report['query_runs'][-1]['status']=='RETURNED')
 result['runtime_cases'].append({'name':case,'expected_failure_call':failcall,'passed':True,'attempts':report['counters']['query_call_attempts'],'returns':report['counters']['query_calls'],'error':error})
# Main-path failures prove durable FAILED records without decoding any actual input.
valid={'schema':'s14e-state-reuse-manifest-v1','contract':{'target_count':4,'query_count':5,'dummy_values':['zero']*5,'query_flags':p.FLAGS.copy(),'device':'cpu','cpu_threads':8,'seed':0,'size':[224,224],'dtype':'float32','wall_seconds':600,'monitored_rss_bytes':34359738368,'history_rgb_allowed':False,'target_rgb_allowed':False,'target_depth_allowed':False},'identities':{}}
for role in p.INPUT_ROLES+['checkpoint','rope_check','runner']:
 valid[role]=str((OUT/('artificial_'+role)).resolve());valid['identities'][valid[role]]='0'*64
valid['runner']=str(SRC.resolve());valid['identities'][str(SRC.resolve())]=digest(SRC);valid['python']=sys.executable
for name,kind in [('malformed_manifest','json'),('raw_depth_identity','depth')]:
 mf=OUT/(name+'.json');out=OUT/(name+'_run')
 if kind=='json':mf.write_text('{ broken JSON')
 else:
  m=copy.deepcopy(valid);m['identities'][str((OUT/'forbidden_target.PNG').resolve())]='0'*64;mf.write_text(json.dumps(m))
 with patch.object(sys,'argv',['review','--manifest',str(mf),'--output',str(out)]),patch.object(np,'load',side_effect=AssertionError('NPZ forbidden')):
  code=p.main()
 metadata=json.loads((out/'run_metadata.json').read_text())
 check(name+'/failed_and_no_arrays',code==1 and metadata['status']=='FAILED' and metadata['counters']['npz_array_decode_attempts']==0 and metadata['counters']['identity_hash_attempts']==0)
 check(name+'/correct_json_counter',metadata['counters']['json_decode_attempts']==1 and metadata['counters']['json_decoded']==(0 if kind=='json' else 1))
 result['main_early_failure_cases'].append({'name':name,'pass':True,'status':metadata['status'],'json_attempts':metadata['counters']['json_decode_attempts'],'json_successes':metadata['counters']['json_decoded']})
# Additional scope probes; rotation checks are explicitly owned by prepare, not falsely attributed here.
wrong=copy.deepcopy(conditions);wrong['target_poses'][0,0,0]=2.
p.validate_conditions(wrong)
result['known_boundary']={'predictor_does_not_check_proper_rotation':True,'resolution':'required prepare independent gate and final manifest; not a predictor-proven geometry claim'}
check('source_identity_unchanged',digest(SRC)==result['source_sha256'])
result.update(status='PASS',completed_utc=now(),check_count=len(result['checks']),runtime_case_count=len(result['runtime_cases']),test_source_sha256=digest(__file__))
(OUT/'receipt.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ['status','check_count','runtime_case_count','completed_utc','source_sha256']}))
