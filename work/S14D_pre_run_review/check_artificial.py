from pathlib import Path
import ast, importlib.util, json, hashlib, datetime, math, sys
import numpy as np
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
C=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local')
p=Path(sys.argv[1]); out=Path(sys.argv[2]);source=p.read_bytes()
spec=importlib.util.spec_from_file_location('reviewed_ray_probe',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def ck(name,ok,**detail):
 checks.append(dict(name=name,ok=bool(ok),**detail))
 if not ok: raise AssertionError(name)
factory,code=m.extract_ray_factory(C/'viser_utils.py',np)
for h,w in [(4,6),(8,8),(224,224)]:
 K=factory.generate_pseudo_intrinsics(h,w)
 ck(f'K_shape_{h}_{w}',K.shape==(3,3) and K.dtype==np.float32)
 ck(f'K_rule_{h}_{w}',float(K[0,0])==float(np.float32(math.sqrt(h*h+w*w))) and K[0,2]==w//2 and K[1,2]==h//2 and K[2,2]==1)
 for case,(theta,t) in enumerate([(0,[0,0,0]),(.3,[.2,-.5,.7]),(-.8,[-2,0,1])]):
  c,s=math.cos(theta),math.sin(theta);rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
  pose=np.eye(4);pose[:3,:3]=rot;pose[:3,3]=t
  actual=factory.get_ray_map(pose,h,w,K)
  ck(f'ray_shape_{h}_{w}_{case}',actual.shape==(h,w,6) and np.isfinite(actual).all())
  for u,v in [(0,0),(w-1,h-1),(w//2,h//2)]:
   camera=[(u-float(K[0,2]))/float(K[0,0]),(v-float(K[1,2]))/float(K[1,1]),1.0]
   xyz=[sum(float(rot[j,k])*camera[k] for k in range(3))+t[j] for j in range(3)]
   norm=math.sqrt(sum(x*x for x in xyz));expected=np.array(t+[x/norm for x in xyz])
   diff=float(np.max(np.abs(actual[v,u]-expected)))
   ck(f'scalar_ray_{h}_{w}_{case}_{u}_{v}',diff<=1e-7,max_abs_difference=diff)
 # Official K inv is FP32, scalar direct division FP64, hence frozen tol1e-7.
history=np.repeat(np.eye(4)[None],20,axis=0);history[:,0,3]=np.arange(20)
rot=np.array([[0,0,1],[0,1,0],[-1,0,0]],dtype=float);history[-1,:3,:3]=rot
poses,d,dist=m.target_poses_from_history(history,np)
ck('history_scale',d==.5 and np.array_equal(dist,np.arange(20)))
ck('four_targets',poses.shape==(4,4,4))
for i,expected in enumerate([[19,0,0],[19,0,-.5],[19,0,.5],[19.5,0,0]]):ck(f'local_axis_target_{i}',np.array_equal(poses[i,:3,3],expected) and np.array_equal(poses[i,:3,:3],rot))
try:m.target_poses_from_history(np.repeat(np.eye(4)[None],20,axis=0),np);ok=False
except ValueError:ok=True
ck('zero_scale_fails',ok)
ck('no_torch_imported','torch' not in sys.modules)
receipt=dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',source=str(p),source_sha256=hashlib.sha256(source).hexdigest(),official_ray_file=str(C/'viser_utils.py'),official_ray_sha256=hashlib.sha256((C/'viser_utils.py').read_bytes()).hexdigest(),check_count=len(checks),checks=checks,scope='artificial arrays only; no model or real NPZ/image/GT; independent scalar algebra vs official vector implementation',real_data_array_reads=0,model_runs=0,ray_tolerance=1e-7,ray_tolerance_reason='official np.linalg.inv on FP32 K vs direct scalar inverse FP64')
out.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','source_sha256','check_count','completed_utc']}))
