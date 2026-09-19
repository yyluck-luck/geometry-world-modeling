#!/usr/bin/env python3
"""Independent saved-output S15B audit: SciPy rotation, scalar sums, component rays.
No producer import, Torch, RGB decoding, sensor depth, trajectory files, or model calls.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, math, sys, traceback
import numpy as np
from scipy.spatial.transform import Rotation
import scipy

SOURCE=[0,3,6,9]
CALLS=[0,2,3,4]
HEADS={'pts3d_in_self_view':(1,224,224,3),'pts3d_in_other_view':(1,224,224,3),
       'conf_self':(1,224,224),'conf':(1,224,224),'camera_pose':(1,7),'rgb':(1,224,224,3)}
STATES={'state_feat':((1,768,768),'float32'),'state_pos':((1,768,2),'int64'),
        'init_state_feat':((1,768,768),'float32'),'mem':((1,256,1536),'float32'),
        'init_mem':((1,256,1536),'float32')}

def now():return datetime.now(timezone.utc).isoformat()
def file_sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def aid(a):
 a=np.ascontiguousarray(a)
 return {'shape':list(a.shape),'dtype':str(a.dtype),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
def write(p,j):p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def date(s):return datetime.fromisoformat(s)


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--manifest-sha256',required=True)
 ap.add_argument('--seal',type=Path,required=True);ap.add_argument('--seal-sha256',required=True)
 ap.add_argument('--run-dir',type=Path,required=True);ap.add_argument('--preparation-receipt',type=Path,required=True)
 ap.add_argument('--caller-receipt',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 a=ap.parse_args()
 if a.output.exists():raise ValueError('Use a new independent verification output directory')
 a.output.mkdir(parents=True)
 report={'schema':'s15b-independent-prefix-verification-v1','status':'RUNNING','started_utc':now(),
     'evidence_kind':'INDEPENDENT_SAVED_MODEL_OUTPUT_AND_ALLOWED_CAMERA_VERIFICATION',
     'python':sys.version,'executable':sys.executable,'numpy_version':np.__version__,'scipy_version':scipy.__version__,
     'checks':[],'reads':[],'file_hashes':[],'counters':{'npz_arrays_decoded':0,'npz_files_opened':0,'json_reads':0,
      'real_rgb_decodes':0,'sensor_depth_decodes':0,'trajectory_reads':0,'model_calls':0},
     'independence':'Different author; no producer or official model math imported. Scalar fsum alignment, SciPy quaternion conversion, component ray derivation.',
     'tolerances':{'arrays_atol':1e-6,'arrays_rtol':1e-5,'scalar_absolute':1e-10,'rotation_atol':1e-5}}
 def check(name,c,**details):
  report['checks'].append(dict(name=name,passed=bool(c),**details))
  if not c:raise AssertionError(name)
 def close(name,x,y,atol=1e-6,rtol=1e-5):
  x=np.asarray(x);y=np.asarray(y)
  check(name+' shape',x.shape==y.shape)
  err=float(np.max(np.abs(x.astype(float)-y.astype(float)))) if x.size else 0.
  check(name+' values',np.allclose(x,y,atol=atol,rtol=rtol),max_abs_error=err,atol=atol,rtol=rtol)
 def exact(name,x,y):check(name,aid(x)==aid(y) and np.array_equal(x,y))
 def hash_check(p,h,role):
  actual=file_sha(p);report['file_hashes'].append(dict(path=str(p),role=role,sha256=actual,utc=now()))
  check(role+': '+str(p),actual==h)
 def read_json(p,role):
  report['reads'].append(dict(path=str(p),role=role,format='json',utc=now()));report['counters']['json_reads']+=1
  return json.loads(Path(p).read_text())
 def read_npz(p,role):
  e=dict(path=str(p),role=role,format='npz',utc=now(),arrays=[]);report['reads'].append(e)
  with np.load(p,allow_pickle=False) as z:
   report['counters']['npz_files_opened']+=1;vals={}
   for k in z.files:
    vals[k]=z[k].copy();e['arrays'].append(dict(key=k,**aid(vals[k])));report['counters']['npz_arrays_decoded']+=1
  return vals
 try:
  # Only metadata is inspected until successful completion and the root seal are authenticated.
  meta=read_json(a.run_dir/'run_metadata.json','completed producer metadata')
  check('Producer completed before independent array access',meta['schema']=='s15b-prefix-proposals-run-v1' and meta['status']=='SUCCESS')
  hash_check(a.manifest,a.manifest_sha256,'externally bound pre-run manifest')
  hash_check(a.seal,a.seal_sha256,'externally bound completed-output seal')
  m=read_json(a.manifest,'fixed prefix manifest');seal=read_json(a.seal,'root proposal seal')
  check('Expected schemas',m['schema']=='s15b-prefix-proposals-manifest-v1' and seal['schema']=='s15b-prefix-proposal-seal-v1')
  check('Metadata frozen manifest hash',meta['manifest_sha256']==a.manifest_sha256)
  allowed_seal={str(p.resolve()) for p in a.run_dir.iterdir() if p.is_file()}|{str(a.manifest.resolve()),str(a.caller_receipt.resolve())}
  check('Root seal complete run files plus manifest and caller receipt',set(seal['identities'])==allowed_seal)
  for p,h in seal['identities'].items():hash_check(p,h,'sealed model output')
  check('Model source snapshot byte identity',seal['identities'][str((a.run_dir/'source_snapshot.py').resolve())]==m['identities'][m['runner']])
  check('Frozen manifest exact byte identity',seal['identities'][str((a.run_dir/'frozen_manifest.json').resolve())]==a.manifest_sha256)
  expected={p.name for p in a.run_dir.iterdir() if p.is_file() and p.name!='run_metadata.json'}
  check('Complete producer output hashes',set(meta['output_sha256'])==expected)
  for n,h in meta['output_sha256'].items():check('Metadata / seal '+n,seal['identities'].get(str((a.run_dir/n).resolve()))==h)
  check('History/input SHA verification recorded before and after',meta['before_after_identity_pass'] is True and meta['counters']['identity_hash_successes']==2*len(m['identities']))
  rgb=[x['path'] for x in m['history_images']]
  check('Fixed twelve RGB ordered indices',len(rgb)==12 and [x['index'] for x in m['history_images']]==list(range(12)) and len(set(rgb))==12)
  # Hashes read RGB/weight bytes, never decode those files.
  for p,h in m['identities'].items():
   check('Canonical input path '+p,Path(p).is_absolute() and str(Path(p).resolve())==p)
   hash_check(p,h,'frozen prefix input/source')
  check('Only declared image allowlist',sorted(p for p in m['identities'] if Path(p).suffix.lower() in {'.png','.jpg','.jpeg'})==sorted(rgb))
  check('No raw trajectory or raw index file input',all(Path(p).name not in {'groundtruth.txt','rgb.txt','depth.txt'} for p in m['identities']))
  check('Frozen checkpoint reused',m['identities'][m['checkpoint']]=='7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d')
  check('Frozen official commit',m['commit']=='8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf')
  for module,v in meta['loaded_upstream_modules'].items():check('Loaded module binding '+module,m['identities'].get(v['path'])==v['sha256'])
  prep=read_json(a.preparation_receipt,'root twelve-camera preparation receipt')
  check('Preparation manifest binding',prep['status']=='PASS' and prep['manifest_sha256']==a.manifest_sha256)
  check('Prepared allowed camera identity binding',prep['output_ids'].get(m['camera_inputs'])==m['identities'][m['camera_inputs']])
  caller=read_json(a.caller_receipt,'external caller resource evidence')
  check('Caller actual successful completion',caller['status']=='PASS' and caller['returncode']==0 and caller['monitor_ok'] and not caller['timed_out'] and not caller['rss_limit_exceeded'])
  check('Caller exact manifest / actual args',caller['manifest_sha256']==a.manifest_sha256 and str(a.run_dir.resolve()) in caller['command'] and m['runner'] in caller['command'])
  check('Actual chronological completion',date(m['frozen_utc'])<date(caller['started_utc'])<=date(meta['started_utc'])<=date(meta['completed_utc'])<=date(caller['completed_utc'])<date(seal['sealed_utc'])<date(report['started_utc']))
  check('Caller recorded resource limits',caller['limits']=={'seconds':600,'rss_bytes':34359738368} and caller['maxrss']<=34359738368 and caller['elapsed_seconds']<=600)
  cams=read_json(m['camera_inputs'],'only twelve permitted GT camera poses')
  check('Camera metadata allowed identity/order',cams['schema']=='s15b-prefix-cameras-v1' and cams['history_rgb_paths']==rgb and cams['history_rgb_sha256']==[x['sha256'] for x in m['history_images']])
  check('Camera conventions',cams['coordinate_frame']=='TUM optical camera-to-world' and cams['units']=='meter' and cams['pose_time']=='rgb' and cams['source_indices']==SOURCE)
  gt=np.asarray(cams['gt_c2w'],float);ts=np.asarray(cams['history_timestamps'],float);K=np.asarray(cams['K'],float)
  check('Allowed twelve poses/times only',gt.shape==(12,4,4) and ts.shape==(12,) and np.isfinite(gt).all() and np.isfinite(ts).all() and np.all(np.diff(ts)>0))
  K_expected=np.array([[525*299/640,0,(319.5+.5)*299/640-.5-37],[0,525*224/480,(239.5+.5)*224/480-.5],[0,0,1.]])
  exact('Native TUM half-pixel intrinsic derivation',K,K_expected)
  h=read_npz(a.run_dir/'predictions.npz','twelve actual prefix six-head model outputs')
  check('All twelve six-head keys',set(h)=={f'frame{i}_{k}' for i in range(12) for k in HEADS})
  for i in range(12):
   for k,shape in HEADS.items():
    key=f'frame{i}_{k}';v=h[key]
    check('History schema finite '+key,v.shape==shape and v.dtype==np.float32 and np.isfinite(v).all())
    check('History producer array digest '+key,aid(v)==meta['history_output_ids'][key])
  poses=read_npz(a.run_dir/'history_poses.npz','saved pose encodings and decoded matrices')
  check('Pose archive key domain',set(poses)=={'history_pose_encodings','history_poses'})
  enc=np.concatenate([h[f'frame{i}_camera_pose'] for i in range(12)])
  exact('History encoding concatenation',poses['history_pose_encodings'],enc)
  independent_poses=np.repeat(np.eye(4)[None],12,axis=0)
  independent_poses[:,:3,3]=enc[:,:3]
  independent_poses[:,:3,:3]=Rotation.from_quat(enc[:,[4,5,6,3]].astype(float)).as_matrix()
  close('SciPy independent wxyz quaternion matrix',poses['history_poses'],independent_poses)
  pred=poses['history_poses'].astype(float)
  for label,v in [('GT',gt),('pred',pred)]:
   close(label+' optical proper orthogonality',np.matmul(v[:,:3,:3].transpose(0,2,1),v[:,:3,:3]),np.repeat(np.eye(3)[None],12,axis=0),1e-5,0)
   close(label+' det one',np.linalg.det(v[:,:3,:3]),np.ones(12),1e-5,0)
   exact(label+' bottom rows',v[:,3,:],np.tile([0.,0.,0.,1.],(12,1)))
  # Independent scalar component construction avoids producer matrix-multiply / np.sum code.
  A=np.array([[math.fsum(pred[0,r,k]*gt[0,c,k] for k in range(3)) for c in range(3)] for r in range(3)])
  u=np.array([[math.fsum(A[r,k]*(gt[i,k,3]-gt[0,k,3]) for k in range(3)) for r in range(3)] for i in range(12)])
  v=np.array([[pred[i,k,3]-pred[0,k,3] for k in range(3)] for i in range(12)])
  D=math.fsum(float(x)*float(x) for x in u.flat);N=math.fsum(float(x)*float(y) for x,y in zip(u.flat,v.flat))
  check('Positive nondegenerate forward OLS domain',D>1e-12 and math.isfinite(D) and N/D>0 and math.isfinite(N/D))
  scale=N/D;c=np.array([pred[0,r,3]-scale*math.fsum(A[r,k]*gt[0,k,3] for k in range(3)) for r in range(3)])
  aligned=np.repeat(np.eye(4)[None],12,axis=0)
  for i in range(12):
   for r in range(3):
    aligned[i,r,3]=scale*math.fsum(A[r,k]*gt[i,k,3] for k in range(3))+c[r]
    for col in range(3):aligned[i,r,col]=math.fsum(A[r,k]*gt[i,k,col] for k in range(3))
  alignment=read_json(a.run_dir/'alignment.json','producer alignment compared with component calculation')
  for key,val in [('D_metric_squared',D),('N_model_metric',N),('s_model_per_metric',scale)]:
   close('Independent scalar '+key,alignment[key],val,1e-10,0)
  close('Independent A',alignment['A'],A,1e-10,0);close('Independent c',alignment['c'],c,1e-10,0)
  residual=pred[:,:3,3]-aligned[:,:3,3]
  norms=np.array([math.sqrt(math.fsum(float(t)*float(t) for t in row)) for row in residual])
  rms=math.sqrt(math.fsum(float(t)*float(t) for t in residual.flat)/12)
  close('Alignment residual vectors',alignment['residual_vectors_model'],residual)
  close('Alignment residual norms',alignment['residual_norms_model'],norms)
  close('Alignment RMS scalar',alignment['rms_model'],rms,1e-10,0)
  inputs=read_npz(a.run_dir/'proposal_inputs.npz','source-camera conditions and old candidate geometry')
  expected_inputs={'source_indices','source_poses','K','ray_maps','old_self_z_model','old_self_z_m','old_conf_self','gt_history_poses','aligned_history_poses','s_model_per_metric'}
  check('Complete source-condition key domain',set(inputs)==expected_inputs)
  exact('Same twelve given GT matrices',inputs['gt_history_poses'],gt)
  close('Independent aligned history matrices',inputs['aligned_history_poses'],aligned)
  exact('Four frozen source indices',inputs['source_indices'],np.array(SOURCE,dtype=np.int64))
  close('Sources use aligned given cameras',inputs['source_poses'],aligned[SOURCE])
  exact('Four identical calibrated K',inputs['K'],np.repeat(K[None],4,axis=0))
  close('Stored condition scale',inputs['s_model_per_metric'],scale,1e-10,0)
  # Derive rays via scalar components, no inv(K), homogeneous matrix, or producer ray factory.
  vv,uu=np.indices((224,224));q=np.stack([(uu-K[0,2])/K[0,0],(vv-K[1,2])/K[1,1],np.ones_like(uu)],axis=-1)
  ray_expected=[];physical_difference=[];projection_error=[]
  for i,pose in enumerate(inputs['source_poses']):
   directional=np.stack([q[...,0]*pose[r,0]+q[...,1]*pose[r,1]+q[...,2]*pose[r,2] for r in range(3)],axis=-1)
   endpoint=directional+pose[:3,3]
   network=endpoint/np.sqrt(endpoint[...,0]**2+endpoint[...,1]**2+endpoint[...,2]**2)[...,None]
   rays=np.concatenate([np.broadcast_to(pose[:3,3],(224,224,3)),network],axis=-1).astype(np.float32)
   ray_expected.append(rays)
   physical=directional/np.sqrt(np.sum(directional**2,axis=-1))[...,None]
   physical_difference.append(float(np.max(np.abs(physical-network))))
   # Artificial 2.0 model-unit optical-depth plane tests pinhole meaning only, not sensor accuracy.
   world=2*directional+pose[:3,3]
   recovered=np.linalg.solve(pose[:3,:3],(world-pose[:3,3]).reshape(-1,3).T).T.reshape(224,224,3)
   projected=np.stack([recovered[...,0]/recovered[...,2]*K[0,0]+K[0,2],recovered[...,1]/recovered[...,2]*K[1,1]+K[1,2]],axis=-1)
   projection_error.append(float(np.max(np.abs(projected-np.stack([uu,vv],axis=-1)))))
   close('Pinhole optical Z preserved '+str(SOURCE[i]),recovered[...,2],np.full((224,224),2.),1e-10,0)
  close('Official conditioning rays derived independently',inputs['ray_maps'],np.stack(ray_expected))
  check('Physical pinhole projection roundtrip',max(projection_error)<1e-10,max_pixel_error=max(projection_error))
  report['ray_semantics']={'network':'ro=t; rd=unit(R*q+t)','physical':'X_world=R*(z*q)+t; physical direction=unit(R*q)',
      'physical_vs_network_max_abs_by_source':physical_difference,'artificial_plane_only':True}
  proposals=read_npz(a.run_dir/'proposals.npz','both frozen geometry candidates and masks')
  check('Complete proposals key domain',set(proposals)=={'source_indices','source_poses','K','old_self_z_model','old_self_z_m','old_conf_self','s_model_per_metric','new_self_z_model','new_self_z_m','new_conf_self','old_positive_mask','new_positive_mask'})
  for key in ('source_indices','source_poses','K','old_self_z_model','old_self_z_m','old_conf_self','s_model_per_metric'):exact('Proposal source-condition passthrough '+key,proposals[key],inputs[key])
  qcalls=[read_npz(a.run_dir/f'query_call_{i}.npz','actual frozen-state query '+str(i)) for i in range(5)]
  for i,one in enumerate(qcalls):
   check('Query '+str(i)+' six-head domain',set(one)==set(HEADS))
   for key,shape in HEADS.items():
    check('Query schema finite '+str(i)+' '+key,one[key].shape==shape and one[key].dtype==np.float32 and np.isfinite(one[key]).all())
    check('Query reported tensor identity '+str(i)+' '+key,aid(one[key])==meta['query_runs'][i]['output_ids'][key])
  for key in HEADS:exact('Repeated source0 all-head byte parity '+key,qcalls[0][key],qcalls[1][key])
  aggregate=read_npz(a.run_dir/'query_outputs.npz','aggregate actual queries')
  check('All five aggregate queries',set(aggregate)=={f'call{i}_{k}' for i in range(5) for k in HEADS})
  for i in range(5):
   for key in HEADS:exact('Aggregate query byte identity '+str(i)+' '+key,aggregate[f'call{i}_{key}'],qcalls[i][key])
  for pos,(source,call) in enumerate(zip(SOURCE,CALLS)):
   old=h[f'frame{source}_pts3d_in_self_view'][0,:,:,2]
   new=qcalls[call]['pts3d_in_self_view'][0,:,:,2]
   exact('Old source self-Z '+str(source),proposals['old_self_z_model'][pos],old)
   exact('Old source confidence '+str(source),proposals['old_conf_self'][pos],h[f'frame{source}_conf_self'][0])
   exact('New source self-Z from call '+str(call),proposals['new_self_z_model'][pos],new)
   exact('New source confidence from call '+str(call),proposals['new_conf_self'][pos],qcalls[call]['conf_self'][0])
   for kind,arr in [('old',old),('new',new)]:
    close('Metric '+kind+' Z source '+str(source),proposals[kind+'_self_z_m'][pos],arr.astype(float)/scale,1e-10,0)
    exact('No replacement of nonpositive '+kind+' mask '+str(source),proposals[kind+'_positive_mask'][pos],arr>0)
    check('Reported nonpositive count '+kind+' '+str(source),meta['nonpositive_source_counts'][kind][pos]==int(np.count_nonzero(arr<=0)))
  before=read_npz(a.run_dir/'state.npz','frozen post-prefix latent state')
  after=read_npz(a.run_dir/'state_after_queries.npz','latent state after all five queries')
  check('All five state fields both archives',set(before)==set(after)==set(STATES))
  for k,(shape,dtype) in STATES.items():
   check('State schema finite '+k,before[k].shape==shape and str(before[k].dtype)==dtype and np.isfinite(before[k]).all())
   exact('State before/after exact bytes '+k,before[k],after[k])
   for key in ('state_final','state_before_queries','state_after_queries'):check('State record '+key+' '+k,meta[key][k]==aid(before[k]))
   for call in meta['query_runs']:check('Intermediate state record '+str(call['call'])+' '+k,call['state_ids_after'][k]==aid(before[k]))
  for group,table in [(inputs,'proposal_input_ids'),(proposals,'proposal_output_ids'),(aggregate,'query_output_ids'),(poses,'history_pose_ids')]:
   for k,arr in group.items():check('Complete recorded tensor digest '+table+' '+k,aid(arr)==meta[table][k])
  check('Exactly five fixed query sources',[r['source_index'] for r in meta['query_runs']]==[0,0,3,6,9])
  for i,r in enumerate(meta['query_runs']):
   check('Query status/flags '+str(i),r['call']==i and r['status']=='PASS' and r['flags']=={'img_mask':[False],'ray_mask':[True],'update':[False],'reset':[False]})
   pos=SOURCE.index(r['source_index'])
   expected={'img':np.zeros((1,3,224,224),np.float32),'ray_map':inputs['ray_maps'][pos][None],
             'camera_pose':inputs['source_poses'][pos][None].astype(np.float32),'true_shape':np.array([[224,224]],np.int64)}
   for key,arr in expected.items():check('Query actual input tensor identity '+str(i)+' '+key,r['input_ids'][key]==aid(arr))
  expected_counters={'history_rgb_decoded':12,'history_forward_calls':1,'history_image_encoder_calls':1,'history_image_encoder_frames':12,'history_ray_encoder_calls':1,'query_calls':5,'query_image_encoder_calls':0,'query_image_encoder_frames':0,'query_ray_encoder_calls':5,'target_rgb_decoded':0,'target_depth_decoded':0,'witness_rgb_decoded':0,'camera_json_reads':1}
  for k,v in expected_counters.items():check('Producer boundary counter '+k,meta['counters'][k]==v)
  check('Image read actual ordered allowlist',meta['image_opened_paths']==rgb and meta['image_open_attempt_paths']==rgb)
  report.update(status='PASS',independent_alignment=dict(A=A.tolist(),s_model_per_metric=scale,c=c.tolist(),D_metric_squared=D,N_model_metric=N,rms_model=rms),
      model_completed_utc=meta['completed_utc'],caller_elapsed_seconds=caller['elapsed_seconds'],source_nonpositive_counts=meta['nonpositive_source_counts'],
      warning='Numerical integrity of proposals and conditioning is not geometric accuracy, innovation, or video quality.')
 except BaseException as e:
  report.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
 finally:
  report.update(completed_utc=now(),check_count=len(report['checks']),passed_check_count=sum(c['passed'] for c in report['checks']),
    verifier_sha256=file_sha(__file__),manifest_sha256=a.manifest_sha256,seal_sha256=a.seal_sha256)
  write(a.output/'verification.json',report)
 print(json.dumps({k:report[k] for k in ('status','check_count','passed_check_count','counters','completed_utc')},indent=2))
 return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
