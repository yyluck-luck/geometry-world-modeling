"""Artificial verifier checks; fake bytes stand for inputs, no dataset reads."""
from pathlib import Path
import contextlib,copy,datetime,hashlib,importlib.util,io,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_verifier',ROOT/'scripts/verify_s15a_history.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
start=datetime.datetime.now(datetime.timezone.utc).isoformat();checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,j):Path(p).write_text(json.dumps(j,indent=2)+'\n')
def ck(name,ok,**info):
 checks.append(dict(name=name,passed=bool(ok),**info))
 if not ok:raise AssertionError(name)
def aid(a):return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=hashlib.sha256(a.tobytes(order='C')).hexdigest())
base=OUT/'fake_case';base.mkdir(exist_ok=False);repo=base/'repo';repo.mkdir();sdir=base/'scripts';sdir.mkdir();run=base/'run';run.mkdir()
runner=sdir/'fake_runner.py';runner.write_text('# Artificial source, no model\n');adapter=sdir/'cut3r_rope_compat.py';adapter.write_text('# Artificial adapter\n');weight=base/'fake_weight.pth';weight.write_bytes(b'artificial weight bytes; never deserialized');rope=base/'fake_rope.json';save(rope,{'artificial':True});python=str((ROOT/'.venv/bin/python').absolute())
inputs=[runner,adapter,weight,rope];history=[]
for i in range(99):
 f=repo/f'm{i}.py';f.write_text('# synthetic frozen source\n');inputs.append(f)
for i in range(20):
 f=base/f'frame{i}.png';f.write_bytes(b'not an actual image:'+str(i).encode());inputs.append(f);history.append(dict(index=i,path=str(f),sha256=sha(f)))
ids={str(f):sha(f) for f in inputs};manifest=base/'manifest.json';m=dict(schema='s15-history-manifest-v1',commit=v.COMMIT,repo=str(repo),python=python,runner=str(runner),checkpoint=str(weight),rope_check=str(rope),history_images=history,control_files=[],identities=ids,contract=v.CONTRACT);save(manifest,m)
pred={};enc=np.zeros((20,7),np.float32);poses=np.tile(np.eye(4,dtype=np.float32),(20,1,1))
for i in range(20):
 theta=(i+1)*.05;axis=np.array([1.,2.,3.]);axis/=np.linalg.norm(axis)
 enc[i,:3]=np.array([.01*i,-.02*i,1+.1*i],np.float32);enc[i,3:]=np.r_[math.cos(theta/2),axis*math.sin(theta/2)]*2
 cross=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
 poses[i,:3,:3]=(np.eye(3)*math.cos(theta)+(1-math.cos(theta))*np.outer(axis,axis)+math.sin(theta)*cross).astype(np.float32);poses[i,:3,3]=enc[i,:3]
 for key,shape in v.PRED.items():
  a=np.ones(shape,np.float32)
  if key=='camera_pose':a=enc[i:i+1].copy()
  pred[f'frame{i}_{key}']=a
state={k:np.zeros(shape,dtype) for k,(shape,dtype) in v.STATE.items()};posearrays=dict(history_pose_encodings=enc,history_poses=poses)
np.savez_compressed(run/'predictions.npz',**pred);np.savez_compressed(run/'state.npz',**state);np.savez_compressed(run/'history_poses.npz',**posearrays)
(run/'source_snapshot.py').write_bytes(runner.read_bytes());(run/'frozen_manifest.json').write_bytes(manifest.read_bytes());(run/'checkpoint_load.txt').write_text('Artificial all keys matched\n')
meta=dict(schema='s15-history-run-v1',status='SUCCESS',phase='complete',started_utc='2026-01-01T00:00:01+00:00',completed_utc='2026-01-01T00:00:02+00:00',manifest_sha256=sha(manifest),video_generated=False,new_model_trained=False,accuracy_evaluated=False,history_images=history,image_open_attempt_paths=[h['path'] for h in history],image_opened_paths=[h['path'] for h in history],identity_hash_attempts=[dict(path=p) for p in list(ids)*2],before_after_identity_pass=True,raw_predictions_saved_before_gates=True,checkpoint_all_keys_matched=True,weights_only=True,device='cpu',cpu_threads=8,seed=0,commit=v.COMMIT,raw_image_properties=[dict(index=i,path=h['path'],size=[640,480],mode='RGB') for i,h in enumerate(history)],input_reads=[dict(role='manifest',path=str(manifest)),dict(role='rope_check',path=str(rope))],loaded_upstream_modules={'fake':dict(path=str(repo/'m0.py'),sha256=sha(repo/'m0.py'))},elapsed_seconds=1,peak_rss_bytes=1000000,output_sha256={n:sha(run/n) for n in v.PAYLOADS},history_output_ids={k:aid(a) for k,a in pred.items()},state_final={k:aid(a) for k,a in state.items()},history_pose_ids={k:aid(a) for k,a in posearrays.items()},counters=dict(history_image_open_attempts=20,history_images_opened=20,history_rgb_decoded=20,target_rgb_decoded=0,target_depth_decoded=0,history_forward_attempts=1,history_forward_calls=1,history_image_encoder_calls=1,history_image_encoder_frames=20,history_ray_encoder_calls=1,history_frames_saved=20,query_calls=0,identity_hash_attempts=2*len(ids),identity_hash_successes=2*len(ids)))
save(run/'run_metadata.json',meta);caller=base/'caller.json';save(caller,dict(schema='s14d-caller-v1',status='PASS',returncode=0,monitor_ok=True,before_after_identity_pass=True,timed_out=False,rss_limit_exceeded=False,manifest_sha256=sha(manifest),limits={'seconds':600,'rss_bytes':34359738368},maxrss=1000000,elapsed_seconds=3,command=[python,str(runner),'--manifest',str(manifest),'--output',str(run)],started_utc='2026-01-01T00:00:00+00:00',completed_utc='2026-01-01T00:00:03+00:00'))
seal=base/'seal.json';sealids=dict(ids);sealids.update({str(run/n):sha(run/n) for n in v.PAYLOADS|{'run_metadata.json'}});sealids.update({str(manifest):sha(manifest),str(caller):sha(caller),str(ROOT/'scripts/verify_s15a_history.py'):sha(ROOT/'scripts/verify_s15a_history.py')})
s=dict(schema='s15a-history-combined-seal-v1',sealed_utc='2026-01-01T00:00:04+00:00',manifest=str(manifest),run_dir=str(run),caller_receipt=str(caller),verifier=str(ROOT/'scripts/verify_s15a_history.py'),identities=sealids);save(seal,s)
original_weight_sha=v.CHECKPOINT_SHA;v.CHECKPOINT_SHA=sha(weight)
with contextlib.redirect_stdout(io.StringIO()):rc=v.verify(seal,sha(seal),OUT/'full_success')
v.CHECKPOINT_SHA=original_weight_sha
r=json.loads((OUT/'full_success/verification.json').read_text());ck('complete fake artifact boundary',rc==0 and r['status']=='PASS' and r['arrays_verified']==127,result_checks=len(r['checks']),quaternion_max_error=r.get('independent_rotation_max_absolute_error'),mock_note='In-memory expected weight digest replaced with fake byte digest only for this artificial call; production source unchanged.')
# Exercise independent pose semantics with explicit perturbations; no Torch formulas.
for name,mut,error in [
 ('translation_bytes',lambda e,p:p.__setitem__((0,0,3),p[0,0,3]+1),'Translation bytes'),
 ('quaternion_order',lambda e,p:e.__setitem__((slice(None),slice(3,7)),e[:,[4,5,6,3]]),'Encoding equals'),
 ('bottom_row',lambda e,p:p.__setitem__((0,3,0),1),'Exact homogeneous'),
 ('rotation_matrix',lambda e,p:p.__setitem__((0,0,0),p[0,0,0]+.01),'Independent SciPy')]:
 e=enc.copy();p=poses.copy();mut(e,p)
 try:v.inspect_poses(pred,e,p,v.Audit());ok=False
 except ValueError as ex:ok=error in str(ex)
 ck(name,ok)
# Reordered quaternion can be internally byte consistent yet must disagree with matrix.
e=enc.copy();e[:,3:]=e[:,[4,5,6,3]];changed=dict(pred)
for i in range(20):changed[f'frame{i}_camera_pose']=e[i:i+1].copy()
try:v.inspect_poses(changed,e,poses,v.Audit());ok=False
except ValueError as ex:ok='Independent SciPy' in str(ex)
ck('consistent_wrong_quaternion_order_rejected',ok)
for name,a,identity,err in [
 ('nonfinite',np.array([np.nan,1],np.float32),None,'Finite'),
 ('wrong_dtype',np.array([1,2],np.float64),None,'Schema'),
 ('wrong_shape',np.array([1,2,3],np.float32),None,'Schema'),
 ('wrong_byte_hash',np.array([1,2],np.float32),dict(shape=[2],dtype='float32',sha256='0'*64),'Contiguous byte SHA')]:
 f=OUT/(name+'.npz');np.savez_compressed(f,a=a)
 try:v.inspect_npz(f,{'a':((2,),'float32')},{'a':identity or aid(a)},v.Audit());ok=False
 except ValueError as ex:ok=err in str(ex)
 ck(name,ok)
# Bind seal before decode; corrupt an artificial array archive after sealing.
with (run/'predictions.npz').open('ab') as f:f.write(b'tamper')
with contextlib.redirect_stdout(io.StringIO()):rc=v.verify(seal,sha(seal),OUT/'sealed_tamper')
r=json.loads((OUT/'sealed_tamper/verification.json').read_text());ck('sealed_file_tamper_before_arrays',rc==1 and r['arrays_verified']==0 and 'File SHA' in r['error'])
result=dict(schema='s15a-verifier-artificial-checks-v1',started_utc=start,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',checks=checks,real_dataset_reads=0,real_model_calls=0,real_checkpoint_reads=0,source_sha256=sha(ROOT/'scripts/verify_s15a_history.py'),artificial_source_sha256=sha(__file__),note='Fake fixture bytes only; full fake success and rejection cases are not actual inference.')
save(OUT/'artificial_checks.json',result);print(json.dumps(result,indent=2))
