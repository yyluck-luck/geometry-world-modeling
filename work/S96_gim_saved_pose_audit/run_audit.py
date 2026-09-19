#!/usr/bin/env python3
"""S96 exact official selector on previously saved real TUM poses; no model inference."""
import hashlib,importlib.util,json,platform,resource,sys,time,types
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]
DATA=PROJECT/'work/S93_ALT_TUM01/downloads/freiburg1_xyz-groundtruth.txt'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp():return datetime.now(timezone.utc).isoformat()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 start=stamp();timer=time.perf_counter()
 out=BASE/'run_01';out.mkdir(exist_ok=False)
 n=3000;k=4
 pools={'linspace16':np.rint(np.linspace(0,n-1,16)).astype(int).tolist(),'first16':list(range(16)),'last16':list(range(n-16,n)),'stride60_first16':list(range(0,16*60,60))}
 freeze={'created_utc':start,'data_sha256':sha(DATA),'data_path':str(DATA),'expected_rows':n,'pools':pools,'k':k,'protocol_sha256':sha(BASE/'PROTOCOL.md'),'runner_sha256':sha(__file__),'source_sha256':{x:sha(BASE/'vendor'/x) for x in ['camera.py','pruning.py']},'review_sha256':sha(BASE/'PRE_RUN_REVIEW.md'),'labels':'SAVED_MEASURED_POSE_COMPONENT_ONLY','settings':['official_high_level_defaults','time_disabled_sensitivity']}
 (out/'FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
 data=np.loadtxt(DATA);assert data.shape==(n,8);assert np.isfinite(data).all();assert np.all(np.diff(data[:,0])>0)
 torch.set_num_threads(1)
 for pkg in ['gim','gim.utils']:
  m=types.ModuleType(pkg);m.__path__=[];sys.modules[pkg]=m
 cam=module('gim.utils.camera',BASE/'vendor/camera.py')
 src=module('gim.utils.pruning',BASE/'vendor/pruning.py')
 qnorm=np.linalg.norm(data[:,4:8],axis=1);assert np.all(qnorm>0)
 R=Rotation.from_quat(data[:,4:8]).as_matrix()
 poses=torch.from_numpy(np.concatenate([data[:,1:4]*cam.POSITION_SCALE,R.reshape(n,9)],axis=1))
 rows=[]
 for pool_name,indices in pools.items():
  pos,fwd=src._camera_features(poses,indices)
  dpos=np.linalg.norm(pos[:,None]-pos[None,:],axis=-1)
  dang=np.arccos(np.clip(fwd@fwd.T,-1,1));iu=np.triu_indices(16,1)
  sp=src._median_positive(dpos[iu]);sr=src._median_positive(dang[iu])
  for setting in freeze['settings']:
   st=(max(indices)-min(indices))/k if setting=='official_high_level_defaults' else None
   K=src.pose_time_kernel(poses,indices,sigma_t=st)
   name=pool_name+'__'+setting;np.save(out/(name+'.npy'),K)
   eig=np.linalg.eigvalsh(K);e0=np.linalg.eigvalsh(K-np.eye(len(indices))*1e-4)
   row={'pool':pool_name,'setting':setting,'row_indices':indices,'timestamps':[float(data[i,0]) for i in indices],'sigma_p_metres':sp,'sigma_r_radians':sr,'sigma_t_row_indices':st,'kernel_sha256':sha(out/(name+'.npy')),'eigenvalues_with_jitter':eig.tolist(),'min_eig_without_jitter':float(e0[0]),'min_eig_with_jitter':float(eig[0]),'negative_eigs_with_jitter':int(np.sum(eig < -1e-10)),'uniform_selected':src.uniform_pruning(indices,k)}
   try:
    diag=np.diag(np.linalg.inv(K));row['inverse_diagonal']=diag.tolist();row['conditional_variance_unclipped']=[float(1/x) if x!=0 else None for x in diag]
   except np.linalg.LinAlgError as e:row['inverse_failure']=str(e)
   try:
    row['official_selected']=src.information_guided_pruning(indices,k,poses,time_sigma_scale=1.0 if st is not None else 0.0)
    assert len(row['official_selected'])==k and len(set(row['official_selected']))==k
    assert set(row['official_selected']) <= set(indices)
    row['selector_status']='RETURNED_INDICES_NOT_QUALITY_VALIDATION'
   except Exception as e:row['selector_status']='FAILED';row['selector_failure']=repr(e)
   rows.append(row)
 result={'status':'EXECUTED_COMPONENT_ONLY_PENDING_INDEPENDENT_REVIEW','started_utc':start,'completed_utc':stamp(),'wall_seconds':time.perf_counter()-timer,'ru_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'platform':platform.platform(),'python':sys.version,'numpy':np.__version__,'torch':torch.__version__,'frame_rows':n,'quaternion_norm_range':[float(qnorm.min()),float(qnorm.max())],'rows':rows,'new_model_inferences':0,'rgb_depth_reads':0,'formal_s91_run':False,'claim':'No new method or native MIND replication. Prior source verification does not authorize geometry gains.'}
 (out/'RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'out':str(out),'rows':len(rows),'primary_min_eigs':[r['min_eig_with_jitter'] for r in rows if r['setting']=='official_high_level_defaults'],'sensitivity_min_eigs':[r['min_eig_with_jitter'] for r in rows if r['setting']!='official_high_level_defaults'],'seconds':result['wall_seconds']}))
if __name__=='__main__':main()
