#!/usr/bin/env python3
"""Independent S17B saved-output verification; no Torch, model or image imports."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, platform, resource, signal, time, traceback, zipfile
import numpy as np
import scipy
from scipy.spatial.transform import Rotation

COMMIT='8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf'
WEIGHT_SHA='45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
HISTORY_SHA=['7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39',
             '77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae']
HEADS={'pts3d_in_self_view':(1,384,512,3),'pts3d_in_other_view':(1,384,512,3),
       'conf_self':(1,384,512),'conf':(1,384,512),'rgb':(1,384,512,3),'camera_pose':(1,7)}
STATE={'state_feat':((1,768,768),'float32'),'state_pos':((1,768,2),'int64'),
       'init_state_feat':((1,768,768),'float32'),'mem':((1,256,1536),'float32'),
       'init_mem':((1,256,1536),'float32')}
POSE={'history_pose_encodings':((2,7),'float32'),'history_poses':((2,4,4),'float32')}
PAYLOAD={'predictions.npz','state.npz','history_poses.npz','frozen_manifest.json',
         'source_snapshot.py','checkpoint_load.txt'}

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def aid(a):
 a=np.ascontiguousarray(a)
 return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=hashlib.sha256(a.tobytes()).hexdigest())
def require(ok,label):
 if not ok:raise ValueError(label)
def validate_array(value,shape,dtype,label):
 require(value.shape==tuple(shape) and value.dtype==np.dtype(dtype),label+' shape/dtype')
 require(np.isfinite(value).all(),label+' finite')
def decode_poses_scipy(encodings):
 validate_array(encodings,(2,7),'float32','pose encodings')
 q=encodings[:,3:7].astype(np.float64)
 require(np.all(np.linalg.norm(q,axis=1)>0),'nonzero quaternion')
 result=np.repeat(np.eye(4)[None],2,axis=0)
 result[:,:3,3]=encodings[:,:3]
 result[:,:3,:3]=Rotation.from_quat(q[:,[1,2,3,0]]).as_matrix()
 return result
def inspect_npz(path,schema,recorded,check):
 check(set(recorded)==set(schema),path.name+' recorded member domain')
 with zipfile.ZipFile(path) as z:
  members=z.infolist()
  check(len(members)==len(schema) and {m.filename for m in members}=={k+'.npy' for k in schema},path.name+' exact bounded members')
  for m in members:
   shape,dtype=schema[m.filename[:-4]]
   check(0<=m.file_size<=int(np.prod(shape))*np.dtype(dtype).itemsize+16384 and not m.flag_bits&1,'bounded NPY '+m.filename)
 result={}
 with np.load(path,allow_pickle=False) as z:
  for key,(shape,dtype) in schema.items():
   value=z[key]
   validate_array(value,shape,dtype,key)
   check(aid(value)==recorded[key],'actual array identity '+key)
   result[key]=value
 return result
def inspect_runtime(meta,check):
 check(meta['schema']=='s17b-dpt-two-frame-run-v1','S17B producer metadata schema')
 check(meta['processed_input_shapes']==[[1,3,384,512]]*2 and meta['processed_true_shapes']==[[[384,512]]]*2,'actual loader dimensions')
 flags=dict(img_mask=True,ray_mask=False,update=True,reset=False)
 check(meta['history_flags']==[flags]*2,'actual history flags')
 architecture=dict(head_type='dpt',output_mode='pts3d+pose',image_patch_class='PatchEmbedDust3R',
                   ray_patch_class='PatchEmbedDust3R',patch_image_size=[512,512],
                   downstream_head_class='DPTPts3dPose',encoder_blocks=24)
 check(all(meta['architecture'].get(k)==v for k,v in architecture.items()),'actual DPT architecture and official patch normalization')
 check(isinstance(meta['architecture']['parameters'],int) and meta['architecture']['parameters']>0,'recorded actual parameter count')
 observations=meta['encoder_observations']
 expected=[('image_patch',[2,3,384,512]),('image_encoder_first_block',[2,768,1024]),
           ('image_encoder_last_block',[2,768,1024]),('dummy_ray_patch',[1,6,384,512])]
 check(len(observations)==4 and [(x['kind'],x['input_shape']) for x in observations]==expected,'four actual encoder boundary observations in order')
 check(all(x['dtype']=='torch.float32' for x in observations),'FP32 encoder observations')
 check(observations[0]['output_token_shape']==[2,768,1024] and observations[3]['output_token_shape']==[1,768,1024]
       and observations[3]['all_zero'] is True,'image token count and zero internal dummy ray')

def verify(manifest,manifest_sha,seal,seal_sha,run,caller,output):
 out=Path(output);require(not out.exists(),'fresh output');out.mkdir(parents=True)
 started=time.monotonic()
 report=dict(schema='s17b-dpt-independent-verification-v1',status='RUNNING',started_utc=utc(),
             numpy=np.__version__,scipy=scipy.__version__,checks=[],file_hashes=[],array_decodes=0,
             checkpoint_deserializations=0,image_decodes=0,sensor_depth_decodes=0,model_calls=0,
             interpretation='Component identity/numerical integrity only; not geometry quality, generalization or video.',
             independence='No producer or official model math imported. SciPy quaternion normalization/rotation and NumPy archive checks.',
             tolerance=dict(rotation_atol=1e-6,rotation_rtol=1e-5))
 def check(ok,label,**detail):
  report['checks'].append(dict(name=label,passed=bool(ok),**detail));require(ok,label)
 def hash_check(p,h,label):
  got=sha(p);report['file_hashes'].append(dict(path=str(p),sha256=got,role=label,utc=utc()));check(got==h,label+' '+str(p))
 def alarm(*unused):raise TimeoutError('600 second verification limit')
 prior=signal.getsignal(signal.SIGALRM);signal.signal(signal.SIGALRM,alarm);signal.alarm(600)
 try:
  manifest,seal,run,caller=map(lambda p:Path(p).resolve(),[manifest,seal,run,caller])
  hash_check(manifest,manifest_sha,'externally bound manifest');hash_check(seal,seal_sha,'externally bound output seal')
  m=json.loads(manifest.read_text());se=json.loads(seal.read_text());ids=se['identities']
  check(m['schema']=='s17b-dpt-two-frame-manifest-v1' and m['commit']==COMMIT,'S17B schema and pinned official commit')
  check(m['identities'][m['checkpoint']]==WEIGHT_SHA,'different pinned 512 DPT checkpoint')
  check(str(manifest) in ids and ids[str(manifest)]==manifest_sha and str(caller) in ids,'manifest and caller sealed')
  files={str(p.resolve()) for p in run.iterdir() if p.is_file()}
  check(files<=(set(ids)),'all saved files included in root seal')
  for p,h in ids.items():
   check(Path(p).is_absolute() and str(Path(p).resolve())==p,'canonical sealed identity')
   hash_check(p,h,'sealed output/control')
  meta=json.loads((run/'run_metadata.json').read_text());cr=json.loads(caller.read_text())
  check(meta['status']=='SUCCESS' and meta['phase']=='complete','actual successful producer before NPZ access')
  check(cr['status']=='PASS' and cr['returncode']==0 and cr['monitor_ok'] and cr['before_after_identity_pass'] and not cr['timed_out'] and not cr['rss_limit_exceeded'],'successful external caller')
  check(cr['limits']==dict(seconds=600,rss_bytes=34359738368) and 0<cr['maxrss']<=34359738368 and cr['elapsed_seconds']<600,'caller 32 GiB/600 second limits')
  check(cr['command']==[m['python'],m['runner'],'--manifest',str(manifest),'--output',str(run)],'exact actual caller command')
  check(meta['manifest_sha256']==cr['manifest_sha256']==manifest_sha,'manifest bound by both receipts')
  check(sha(run/'frozen_manifest.json')==manifest_sha and sha(run/'source_snapshot.py')==m['identities'][m['runner']],'frozen source and manifest copies')
  check({p.name for p in run.iterdir()}==PAYLOAD|{'run_metadata.json'},'exact seven output files')
  check(set(meta['output_sha256'])==PAYLOAD,'complete payload hash list')
  for p,h in meta['output_sha256'].items():check(ids.get(str(run/p))==h,'payload hash bound '+p)
  history=m['history_images']; paths=[x['path'] for x in history]
  check(len(history)==2 and [x['index'] for x in history]==[0,1] and len(set(paths))==2,'two ordered Bonn histories')
  check([x['sha256'] for x in history]==HISTORY_SHA,'original S15A index0/1 photo identities')
  expected=dict(history_count=2,query_count=0,history_flags=dict(img_mask=True,ray_mask=False,update=True,reset=False),
                device='cpu',cpu_threads=8,seed=0,dtype='float32',size=[384,512],loader_size=512,raw_image_size=[640,480],
                head_type='dpt',patch_image_size=[512,512],wall_seconds=600,monitored_rss_bytes=34359738368,
                external_monitor_required=True,history_rgb_allowed=True,target_rgb_allowed=False,target_depth_allowed=False)
  check(all(m['contract'].get(k)==v for k,v in expected.items()),'fixed two-history CPU contract')
  mids=m['identities'];repo=Path(m['repo']);upstream={p for p in mids if Path(p).is_relative_to(repo) and Path(p).suffix=='.py'}
  controls=set(m.get('control_files',[]));adapter=str(Path(m['runner']).parent/'cut3r_rope_compat.py')
  check(len(controls)==len(m.get('control_files',[])) and all(Path(p).suffix in {'.md','.json','.py'} for p in controls),'distinct bounded control types')
  check(len(upstream)==99,'99 frozen official Python sources')
  check(set(mids)==upstream|controls|set(paths)|{m['runner'],m['checkpoint'],m['rope_check'],adapter},'exact no-GT input allowlist')
  check(all(Path(p).name not in {'groundtruth.txt','rgb.txt','depth.txt'} for p in mids),'no raw dataset/trajectory metadata')
  for image in history:check(mids[image['path']]==image['sha256'],'history photo hash binding')
  # Reads bytes of the now-completed sealed checkpoint and photos, never deserializes/decodes them.
  for p,h in mids.items():hash_check(p,h,'frozen input/source')
  check(meta['history_images']==history and meta['image_open_attempt_paths']==meta['image_opened_paths']==paths,'recorded exact photo opens')
  counters=dict(history_image_open_attempts=2,history_images_opened=2,history_rgb_decoded=2,
                target_rgb_decoded=0,target_depth_decoded=0,history_forward_attempts=1,history_forward_calls=1,
                history_image_encoder_calls=1,history_image_encoder_frames=2,history_ray_encoder_calls=1,
                history_frames_saved=2,query_calls=0,history_ray_encoder_frames=1,supplied_ray_frames=0,supplied_image_frames=2,
                history_encoder_first_block_calls=1,history_encoder_last_block_calls=1,
                identity_hash_attempts=2*len(mids),identity_hash_successes=2*len(mids))
  check(all(meta['counters'].get(k)==v for k,v in counters.items()),'one two-image history batch and internal dummy-ray encoder; zero ray queries')
  check([v['path'] for v in meta['identity_hash_attempts']]==list(mids)*2,'recorded full pre/post identity passes')
  check(meta['before_after_identity_pass'] and meta['raw_predictions_saved_before_gates'],'evidence persistence and identity gates')
  check(meta['checkpoint_all_keys_matched'] is True and meta['weights_only'] is True,'safe matched checkpoint load recorded')
  check(meta['checkpoint_identity']==dict(path=m['checkpoint'],sha256=WEIGHT_SHA,bytes=3173761006)
        and Path(m['checkpoint']).stat().st_size==3173761006,'full 512 DPT checkpoint size identity')
  inspect_runtime(meta,check)
  check(all(meta[k] is False for k in ['video_generated','new_model_trained','accuracy_evaluated']),'no scientific quality claim')
  props=meta['raw_image_properties']
  check(len(props)==2 and [v['index'] for v in props]==[0,1] and [v['path'] for v in props]==paths and all(v['size']==[640,480] for v in props),'recorded native Bonn dimensions')
  check(meta['device']=='cpu' and meta['cpu_threads']==8 and meta['seed']==0,'fixed actual runtime')
  check(len(meta['input_reads'])==2 and [(x['role'],x['path']) for x in meta['input_reads']]==
        [('manifest',str(manifest)),('rope_check',m['rope_check'])],'only declared JSON reads')
  for v in meta['loaded_upstream_modules'].values():check(v['path'] in upstream and mids[v['path']]==v['sha256'],'loaded source binding')
  # Full output schema independent of producer constants: 384 rows, 512 columns.
  pred_schema={f'frame{i}_{k}':(shape,'float32') for i in range(2) for k,shape in HEADS.items()}
  pred=inspect_npz(run/'predictions.npz',pred_schema,meta['history_output_ids'],check)
  state=inspect_npz(run/'state.npz',STATE,meta['state_final'],check)
  pose=inspect_npz(run/'history_poses.npz',POSE,meta['history_pose_ids'],check)
  report['array_decodes']=len(pred)+len(state)+len(pose)
  enc=np.concatenate([pred[f'frame{i}_camera_pose'] for i in range(2)])
  check(np.array_equal(enc,pose['history_pose_encodings']),'pose concatenation')
  independent=decode_poses_scipy(enc);saved=pose['history_poses']
  error=float(np.max(np.abs(independent-saved)))
  check(np.allclose(independent,saved,atol=1e-6,rtol=1e-5),'SciPy wxyz quaternion independent pose matrices',max_abs_error=error)
  check(np.array_equal(saved[:,3,:],np.tile([0,0,0,1],(2,1))) and np.array_equal(saved[:,:3,3],enc[:,:3]),'exact homogeneous bottom row and translations')
  rr=saved[:,:3,:3].astype(np.float64)
  check(np.allclose(rr.transpose(0,2,1)@rr,np.eye(3),atol=1e-4,rtol=0) and np.allclose(np.linalg.det(rr),1,atol=1e-4,rtol=0),'proper rotations')
  positions=np.array([[i//27,i%27] for i in range(768)],dtype=np.int64)[None]
  check(np.array_equal(state['state_pos'],positions),'state 2d positions from floor sqrt(768) independently constructed')
  check(0<meta['peak_rss_bytes']<=34359738368 and meta['elapsed_seconds']<600,'producer completion resource bounds')
  check(datetime.fromisoformat(cr['started_utc'])<=datetime.fromisoformat(meta['started_utc'])<=datetime.fromisoformat(meta['completed_utc'])<=datetime.fromisoformat(cr['completed_utc']),'producer/caller chronological order')
  for p,h in ids.items():hash_check(p,h,'post verification sealed identity')
  check(sha(manifest)==manifest_sha and sha(seal)==seal_sha,'externally bound records unchanged')
  report.update(status='PASS',poses_max_absolute_error=error,arrays_verified=19,inputs_unchanged=True)
 except BaseException as exc:report.update(status='FAIL',error=repr(exc),traceback=traceback.format_exc())
 finally:
  signal.alarm(0);signal.signal(signal.SIGALRM,prior)
  report.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started,source_sha256=sha(__file__),
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024))
  (out/'verification.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:report[k] for k in ['status','completed_utc','array_decodes']}))
 return int(report['status']!='PASS')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--manifest-sha256',required=True)
 ap.add_argument('--seal',required=True);ap.add_argument('--seal-sha256',required=True);ap.add_argument('--run-dir',required=True)
 ap.add_argument('--caller-receipt',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 raise SystemExit(verify(a.manifest,a.manifest_sha256,a.seal,a.seal_sha256,a.run_dir,a.caller_receipt,a.output))
