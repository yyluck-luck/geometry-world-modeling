#!/usr/bin/env python3
"""Artificial geometry + full CLI preparation test. Never reads real research arrays."""
from pathlib import Path
import importlib.util
from datetime import datetime,timezone
import json,sys,subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('prepare',ROOT/'scripts/prepare_s14e_known_camera.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
OUT=Path(__file__).resolve().parent/'artificial_v1'
if OUT.exists():raise ValueError('Fresh artificial directory required')
OUT.mkdir()
checks=[]
def check(name,fn,reject=False):
 try:fn()
 except ValueError as e:
  if not reject:raise
  checks.append(dict(name=name,passed=True,error=str(e)))
 else:
  if reject:raise AssertionError('Did not reject '+name)
  checks.append(dict(name=name,passed=True))
def close(a,b,tol=1e-12):
 if not np.allclose(a,b,atol=tol,rtol=0,equal_nan=True):raise ValueError('Artificial expected value differs')
I=np.eye(4)
gt=np.tile(I,(3,1,1));gt[:,0,3]=[0,1,2]
pred=gt.copy();pred[:,0,3]=[0,1,3]
a=p.align_history(gt,pred)
check('forward OLS is 7/5',lambda:close(a['s_model_per_metric'],7/5))
check('reverse OLS differs',lambda:close(a['s_model_per_metric']*.7,.98))
check('zero metric baseline rejected',lambda:p.align_history(np.tile(I,(3,1,1)),pred),True)
check('negative scale rejected',lambda:p.align_history(gt,np.concatenate([pred[:,:,:3],-pred[:,:,3:]],axis=2)),True)
rot=np.array([[0.,-1,0],[1,0,0],[0,0,1]])
model=np.tile(I,(3,1,1));model[:,:3,:3]=rot;model[:,:3,3]=2*(gt[:,:3,3]@rot.T)+np.array([4,5,6])
a=p.align_history(gt,model)
check('rotation scale translation recovery',lambda:(close(a['A'],rot),close(a['s_model_per_metric'],2),close(a['c'],[4,5,6])))
check('target transform',lambda:close(p.map_target_poses(gt,a),model))
reflection=gt.copy();reflection[0,0,0]=-1
check('reflection rejected',lambda:p.validate_poses(reflection),True)
bad=gt.copy();bad[0,0,0]=1.01
check('nonorthogonal rejected',lambda:p.validate_poses(bad),True)
trajectory=p.parse_trajectory('0 0 0 0 0 0 0 2\n0.1 1 0 0 0 0 -2 0\n')
check('quaternion normalized',lambda:close(np.linalg.norm(trajectory[:,4:],axis=1),[1,1]))
mid,info=p.interpolate_trajectory(trajectory,.05)
check('translation lerp',lambda:close(mid[:3,3],[.5,0,0]))
check('SLERP quarter turn',lambda:close(mid[:3,:3],[[0,1,0],[-1,0,0],[0,0,1]]))
check('exact final endpoint',lambda:close(p.interpolate_trajectory(trajectory,.1)[0][:3,3],[1,0,0]))
check('no extrapolation',lambda:p.interpolate_trajectory(trajectory,.2),True)
check('gap rejected',lambda:p.interpolate_trajectory(trajectory,.05,.01),True)
check('duplicate time rejected',lambda:p.parse_trajectory('0 0 0 0 0 0 0 1\n0 0 0 0 0 0 0 1'),True)
check('zero quaternion rejected',lambda:p.parse_trajectory('0 0 0 0 0 0 0 0'),True)
qsmall=p.parse_trajectory('0 0 0 0 0 0 0 1\n0.1 0 0 0 0 0 0.00001 0.99999999995')
small,_=p.interpolate_trajectory(qsmall,.05)
check('small-angle SLERP stable',lambda:close(np.arctan2(small[1,0],small[0,0]),1e-5,1e-12))
z=np.full((2,2,2),2.,dtype=np.float32);poses=np.tile(I,(2,1,1));targets=np.tile(I,(1,1,1));K=np.eye(3)
b,prov,diag=p.build_baselines(z,poses,targets,K,2)
check('identity warp scale',lambda:close(b['history_zbuffer_m'],np.ones((1,2,2))))
check('constant same scale',lambda:close(b['history_constant_m'],np.ones((1,2,2))))
check('equal-z tie history then raster',lambda:close(prov['warp_source_index'],np.arange(4).reshape(1,2,2)))
z[1]=1
b,prov,diag=p.build_baselines(z,poses,targets,K,1)
check('nearest positive z wins',lambda:close(b['history_zbuffer_m'],np.ones((1,2,2))))
check('nearest source index',lambda:close(prov['warp_source_index'],np.arange(4,8).reshape(1,2,2)))
check('even constant median',lambda:close(diag['constant_m'],1.5))
far=targets.copy();far[0,0,3]=100
b,prov,diag=p.build_baselines(z,poses,far,K,1)
check('empty warp preserves NaN',lambda:close(b['history_zbuffer_m'],np.full((1,2,2),np.nan)))
check('empty source minus1',lambda:close(prov['warp_source_index'],np.full((1,2,2),-1)))
behind=targets.copy();behind[0,2,3]=10
b,prov,diag=p.build_baselines(z,poses,behind,K,1)
check('behind-camera counts',lambda:close(diag['targets'][0]['target_nonpositive_z'],8))
zh=np.ones((1,1,2),np.float32);ph=I[None].copy();ph[0,0,3]=.5
b,prov,diag=p.build_baselines(zh,ph,targets,K,1)
check('positive half rounds upward',lambda:close(prov['warp_source_index'],np.array([[[-1,0]]])))
check('no valid history rejects',lambda:p.build_baselines(np.full((1,1,1),np.nan),I[None],I[None],K,1),True)
# Full CLI fixture: every NPZ/trajectory is fabricated in this directory; sentinel
# query/object arrays would fail if decoded with allow_pickle=False.
fixture=OUT/'fixture';fixture.mkdir();image_root=fixture/'unread_images'
frames=[];images=[]
for i in range(24):
 t=i*.05;rel=f'rgb/{i}.png';digest=f'{i:064x}'
 frames.append(dict(frame=i,rgb=dict(timestamp=t,path=rel),depth=dict(timestamp=t,path=f'depth/{i}.png'),rgb_sha256=digest,depth_sha256='f'*64))
 images.append(dict(path=str(image_root/rel),sha256=digest))
ground=fixture/'groundtruth.txt';ground.write_text('\n'.join(f'{i*.05!r} {i*.05!r} 0 0 0 0 0 1' for i in range(24)))
cp=fixture/'checkpoint_never_created.pth';cpsha='a'*64
H=np.tile(np.eye(4,dtype=np.float32),(20,1,1));H[:,0,3]=np.arange(20,dtype=np.float32)*np.float32(.1)
arrays={}
for i in range(20):
 pts=np.zeros((1,224,224,3),np.float32);pts[...,2]=2
 arrays[f'frame{i}_pts3d_in_self_view']=pts;arrays[f'frame{i}_camera_c2w']=H[i:i+1]
arrays['frame20_pts3d_in_self_view']=np.array([{'must_not_decode':True}],dtype=object)
old=fixture/'predictions.npz';np.savez_compressed(old,**arrays)
probe=fixture/'probe_inputs.npz';np.savez_compressed(probe,history_poses=H,target_poses=np.array([{'must_not_decode':True}],dtype=object))
state=dict(state_feat=dict(shape=[1,768,768],dtype='float32',sha256='b'*64),mem=dict(shape=[1,256,1536],dtype='float32',sha256='c'*64))
frozen=dict(schema='s8-inputs-v1',text_file_sha256={'groundtruth.txt':p.sha(ground)},blocks=[dict(block=0,frames=frames)])
dm=dict(contract=dict(size=[224,224],history_count=20),checkpoint=str(cp),identities={str(cp):cpsha},commit='synthetic',history_images=images[:20])
dmp=fixture/'s14d_manifest.json';p.write(dmp,dm)
common=dict(commit='synthetic',torch_version='synthetic',numpy_version='synthetic',cpu_threads=8,seed=0,device='cpu')
d=dict(status='SUCCESS',output_sha256={'probe_inputs.npz':p.sha(probe)},manifest_sha256=p.sha(dmp),decoded_image_paths=[x['path'] for x in images[:20]],state_before=state,**common)
checks_anchor=[]
for oldname,new in [('state_feat','state_feat'),('pose_memory','mem')]:
 for i in range(4):checks_anchor.append(dict(field=oldname,anchor_tensor_sha256=state[new]['sha256'],anchor_shape=state[new]['shape'],anchor_dtype='torch.float32',exactly_unchanged=True))
s8=dict(ok=True,inference_ok=True,history_count=20,query_count=4,predictions_sha256=p.sha(old),dtype='float32',actual_patch_image_size=[224,224],actual_head_type='linear',checkpoint=dict(path=str(cp),sha256=cpsha),images=images,input_tensor_shapes=[[1,3,224,224]]*24,prepared_view_flags=[dict(img_mask=[True],ray_mask=[False],update=[True],reset=[False])]*20,query_state_write_audit=dict(checks=checks_anchor),**common)
paths={'frozen_inputs':fixture/'frozen_inputs.json','s8_metadata':fixture/'s8_metadata.json','s14d_metadata':fixture/'s14d_metadata.json','s14d_manifest':dmp,'history_predictions_npz':old,'s14d_probe_npz':probe,'trajectory':ground,'runner':ROOT/'scripts/prepare_s14e_known_camera.py','viewer_path':fixture/'viser_utils.py'}
# Read only official Python source as allowed preparation evidence.
viewer=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/viser_utils.py')
paths['viewer_path'].write_bytes(viewer.read_bytes())
for role,value in [('frozen_inputs',frozen),('s8_metadata',s8),('s14d_metadata',d)]:p.write(paths[role],value)
manifest=dict(schema='s14e-known-camera-prepare-manifest-v1',contract=p.CONTRACT,python=sys.executable,dataset_root=str(image_root),identities={str(v.resolve()):p.sha(v) for v in paths.values()},**{k:str(v.resolve()) for k,v in paths.items()})
mp=fixture/'manifest.json';p.write(mp,manifest)
proc=subprocess.run([sys.executable,str(paths['runner']),'--manifest',str(mp),'--output',str(OUT/'full_cli')],capture_output=True,text=True)
(OUT/'full_cli_stdout.txt').write_text(proc.stdout);(OUT/'full_cli_stderr.txt').write_text(proc.stderr)
if proc.returncode:raise RuntimeError(proc.stderr)
meta=json.loads((OUT/'full_cli/run_metadata.json').read_text())
check('full CLI SUCCESS',lambda:p.require(meta['status']=='SUCCESS','Full CLI status'))
check('41 exact array reads',lambda:close(meta['counters']['npz_arrays_decoded'],41))
check('target/history object sentinels never decoded',lambda:p.require(all(not(r['key'].startswith('frame20') or r['key']=='target_poses') for row in meta['input_reads'] for r in row.get('array_reads',[])),'Forbidden key read'))
check('unread image directory absent',lambda:p.require(not image_root.exists(),'Image fixture accidentally accessed/created'))
check('checkpoint absent',lambda:p.require(not cp.exists(),'Weight fixture unexpectedly created'))
seal=json.loads((OUT/'full_cli/condition_seal.json').read_text())
check('condition seal complete',lambda:p.require(all(p.sha(OUT/'full_cli'/name)==digest for name,digest in seal['payload_sha256'].items()),'Seal hash mismatch'))
with np.load(OUT/'full_cli/condition.npz',allow_pickle=False) as values:
 check('condition strict3keys',lambda:p.require(set(values.files)=={'target_poses','K','ray_maps'},'Condition keys'))
 check('condition K fixed',lambda:close(values['K'][0],p.K_FIXED))
receipt=dict(schema='s14e-prepare-artificial-v1',status='PASS',completed_utc=datetime.now(timezone.utc).isoformat(),checks=checks,check_count=len(checks),real_npz_reads=0,real_trajectory_reads=0,real_image_reads=0,real_checkpoint_reads=0,real_model_calls=0,full_cli_arrays_decoded=41,production_source_sha256=p.sha(paths['runner']))
p.write(OUT/'receipt.json',receipt)
print(json.dumps({k:receipt[k] for k in ['status','check_count','full_cli_arrays_decoded','real_npz_reads']}))
