"""Independent artificial numeric cases; never opens real datasets or archives."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math
from unittest.mock import patch
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');OUT=ROOT/'work/S14E_pre_run_review/prepare_numeric_independent_v1';OUT.mkdir()
SRC=ROOT/'scripts/prepare_s14e_known_camera.py';spec=importlib.util.spec_from_file_location('prepare_review',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r={'started_utc':now(),'status':'RUNNING','source_sha256':sha(SRC),'real_npz_decodes':0,'real_trajectory_decodes':0,'real_image_decodes':0,'checkpoint_reads':0,'model_calls':0,'checks':[]}
def ck(name,value,detail=None):
 if not value:raise AssertionError(name)
 r['checks'].append({'name':name,'pass':True,'detail':detail})
def close(name,a,b,tol=1e-11):
 a,b=np.asarray(a),np.asarray(b);difference=float(np.max(np.abs(a-b))) if a.size else 0.
 ck(name,a.shape==b.shape and bool(np.allclose(a,b,atol=tol,rtol=0,equal_nan=True)),difference)
def reject(name,fn):
 try:fn()
 except ValueError:ck(name,True)
 else:raise AssertionError('Did not reject '+name)
with patch.object(np,'load',side_effect=AssertionError('No archive input in numeric review')):
 # Independent SciPy shortest-arc interpolation, including quaternion sign flips.
 qs=Rotation.from_euler('xyz',[[0,0,0],[10,-20,170],[15,-25,-179]],degrees=True).as_quat();qs[1]*=-1
 ts=np.array([0.,.05,.1]);xyz=np.array([[0,0,0],[1,2,3],[2,-1,1]],float)
 lines=[' '.join(map(str,[ts[i],*xyz[i],*qs[i]])) for i in range(3)]
 a=m.parse_trajectory('\n'.join(lines));slerp=Slerp(ts,Rotation.from_quat(qs))
 for t in [0.,.0125,.025,.05,.075,.1]:
  got,meta=m.interpolate_trajectory(a,t)
  expected=np.eye(4);expected[:3,:3]=slerp(t).as_matrix();expected[:3,3]=[np.interp(t,ts,xyz[:,j]) for j in range(3)]
  close('trajectory/scipy/'+str(t),got,expected)
 reject('trajectory/no_extrapolation',lambda:m.interpolate_trajectory(a,.101))
 reject('trajectory/bracket_gap',lambda:m.interpolate_trajectory(a,.075,.01))
 reject('trajectory/duplicate',lambda:m.parse_trajectory(lines[0]+'\n'+lines[0]))
 reject('trajectory/zero_quaternion',lambda:m.parse_trajectory('0 0 0 0 0 0 0 0'))
 # 20 histories with known transform and one noisy center. Positive forward OLS must match.
 g=np.tile(np.eye(4),(20,1,1));g[:,:3,:3]=Rotation.from_euler('z',np.arange(20)*.02).as_matrix()
 g[:,:3,3]=np.array([[i*.1,np.sin(i*.1)*.2,(i%3)*.03] for i in range(20)])+np.array([1.2,-.5,.8])
 A=Rotation.from_euler('xyz',[12,-7,25],degrees=True).as_matrix();s=1.7;c=np.array([.3,.4,-.9])
 p=np.tile(np.eye(4),(20,1,1));p[:,:3,:3]=A[None]@g[:,:3,:3];p[:,:3,3]=s*(g[:,:3,3]@A.T)+c;p[11,0,3]+=.2
 fit=m.align_history(g,p)
 num=[];den=[]
 for i in range(20):
  ai=A@(g[i,:3,3]-g[0,:3,3]);bi=p[i,:3,3]-p[0,:3,3]
  num.extend(float(ai[j]*bi[j]) for j in range(3));den.extend(float(ai[j]*ai[j]) for j in range(3))
 expected_s=math.fsum(num)/math.fsum(den)
 close('alignment/forward_OLS_distinct_from_inverse',fit['s_model_per_metric'],expected_s)
 close('alignment/anchored_rotation',fit['A'],A)
 query=g[[3,6,9,15]].copy();mapped=m.map_target_poses(query,fit)
 for i in range(4):
  expected=np.eye(4);expected[:3,:3]=A@query[i,:3,:3];expected[:3,3]=expected_s*A@query[i,:3,3]+np.asarray(fit['c'])
  close('alignment/target/'+str(i),mapped[i],expected)
 flat=g.copy();flat[:,:3,3]=g[0,:3,3];reject('alignment/no_GT_displacement',lambda:m.align_history(flat,p))
 flipped=p.copy();flipped[:,:3,3]=p[0,:3,3]-(p[:,:3,3]-p[0,:3,3]);reject('alignment/negative_scale',lambda:m.align_history(g,flipped))
 improper=g.copy();improper[1,0,0]*=-1;reject('pose/improper',lambda:m.validate_poses(improper))
 # Tiny scalar per-point pinhole reference, independent of vectorized lexsort implementation.
 depths=np.array([[[2,2,0,2],[3,np.nan,2,2],[2,2,-1,2]],[[2,2,2,2],[3,2,2,2],[2,2,2,2]]],np.float32)
 hp=np.tile(np.eye(4),(2,1,1));targets=np.tile(np.eye(4),(4,1,1));targets[1,0,3]=.5;targets[2,2,3]=10;targets[3,0,3]=-50
 K=np.array([[2.,0,1.5],[0,2.,1],[0,0,1.]])
 baseline,provenance,diag=m.build_baselines(depths,hp,targets,K,2.)
 for q,t in enumerate(targets):
  candidates={}
  for hi in range(2):
   for y in range(3):
    for x in range(4):
     z=float(depths[hi,y,x])
     if not math.isfinite(z) or z<=0:continue
     xc=np.array([(x-1.5)*z/2,(y-1)*z/2,z]);world=hp[hi,:3,:3]@xc+hp[hi,:3,3];local=t[:3,:3].T@(world-t[:3,3])
     if not np.isfinite(local).all() or local[2]<=0:continue
     u=math.floor(2*local[0]/local[2]+1.5+.5);v=math.floor(2*local[1]/local[2]+1+.5)
     if not(0<=u<4 and 0<=v<3):continue
     value=(float(local[2]),hi*12+y*4+x);key=(v,u)
     if key not in candidates or value<candidates[key]:candidates[key]=value
  expect=np.full((3,4),np.nan);src=np.full((3,4),-1,dtype=np.int64)
  for (y,x),(z,who) in candidates.items():expect[y,x]=z/2;src[y,x]=who
  close('baseline/scalar_depth/'+str(q),baseline['history_zbuffer_m'][q],expect)
  ck('baseline/scalar_source/'+str(q),bool(np.array_equal(provenance['warp_source_index'][q],src)))
  ck('baseline/count_partition/'+str(q),sum(diag['targets'][q][k] for k in ['target_nonfinite','target_nonpositive_z','projection_nonfinite','outside_image','in_bounds_point_visits'])==diag['targets'][q]['history_positive_finite_points'])
 allvals=sorted(float(z) for z in depths.ravel() if math.isfinite(float(z)) and z>0);n=len(allvals);median=(allvals[(n-1)//2]+allvals[n//2])/2
 close('baseline/constant_manual_sorted_median',baseline['history_constant_m'],np.full((4,3,4),median/2))
 ck('baseline/tie_earlier_history',provenance['warp_source_index'][0,0,0]==0)
 ck('baseline/all_behind_empty',bool(np.isnan(baseline['history_zbuffer_m'][2]).all()))
 reject('baseline/all_missing',lambda:m.build_baselines(np.zeros((2,3,4),np.float32),hp,targets,K,2.))
ck('source_unchanged',sha(SRC)==r['source_sha256']);r.update(status='PASS',completed_utc=now(),check_count=len(r['checks']),test_source_sha256=sha(__file__))
(OUT/'receipt.json').write_text(json.dumps(r,indent=2,allow_nan=False)+'\n');print(json.dumps({k:r[k] for k in ['status','check_count','completed_utc','source_sha256']}))
