"""Independent synthetic scorer integration/threshold/missingness audit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,subprocess,sys
import numpy as np
from PIL import Image
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');OUT=ROOT/'work/S14E_pre_run_review/score_independent_v1';OUT.mkdir()
SRC=ROOT/'scripts/score_s14e_depth.py';spec=importlib.util.spec_from_file_location('score_review',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
r={'started_utc':now(),'status':'RUNNING','source_sha256':sha(SRC),'real_npz_decodes':0,'real_RGB_or_depth_decodes':0,'real_trajectory_decodes':0,'checkpoint_reads':0,'model_calls':0,'checks':[],'integration':[]}
def ck(name,value):
 if not value:raise AssertionError(name)
 r['checks'].append({'name':name,'pass':True})
def close(name,x,y):ck(name,(x is None and y is None) or (x is not None and y is not None and math.isclose(x,y,abs_tol=1e-12,rel_tol=1e-12)))
# Scalar reference preserves the exact operational max/div threshold, including representational ties.
gt=np.array([[1.,1.,0],[1.,2.,.0054]])
pred=np.array([[[1.,np.nan,1],[1.25,1.6,.00675]],[[.9,1.1,0],[0.,2.5,.0054]],[[1.,1.,0],[1.,2.,.0054]]])
rows,arrays=m.compute_metrics(gt,pred,20,0)
gv=[(y,x) for y in range(2) for x in range(3) if math.isfinite(gt[y,x]) and gt[y,x]>0]
common=[yx for yx in gv if all(math.isfinite(pred[j][yx]) and pred[j][yx]>0 for j in range(3))]
for j,row in enumerate(rows):
 own=[yx for yx in gv if math.isfinite(pred[j][yx]) and pred[j][yx]>0]
 success=[yx for yx in own if max(float(pred[j][yx])/float(gt[yx]),float(gt[yx])/float(pred[j][yx]))<1.25]
 ck('method'+str(j)+'/all_gt_denominator',row['gt_valid_count']==len(gv));ck('method'+str(j)+'/own_count',row['own_valid_count']==len(own));ck('method'+str(j)+'/common_count',row['common_valid_count']==len(common));ck('method'+str(j)+'/exact_success',row['delta1_success_count']==len(success))
 close('method'+str(j)+'/delta1',row['delta1_all_gt'],len(success)/len(gv));close('method'+str(j)+'/coverage',row['coverage'],len(own)/len(gv))
 for prefix,domain in [('own_',own),('common_',common)]:
  errs=[abs(float(pred[j][yx])-float(gt[yx])) for yx in domain];n=len(errs)
  expected={'mae_m':math.fsum(errs)/n if n else None,'abs_rel':math.fsum(e/float(gt[yx]) for e,yx in zip(errs,domain))/n if n else None,'rmse_m':math.sqrt(math.fsum(e*e for e in errs)/n) if n else None}
  for k,v in expected.items():close('method'+str(j)+'/'+prefix+k,row[prefix+k],v)
ck('ratio_boundary_27_units',arrays['delta1_success_mask'][0,1,2]==False)
empty,_=m.compute_metrics(np.zeros((2,3)),np.full((3,2,3),np.nan),20,0)
ck('empty_GT_null_status',all(x['delta1_all_gt'] is None and x['gt_domain_status']=='EMPTY_GT_DOMAIN' and x['own_mae_m'] is None for x in empty))
# Two independent fresh complete fixtures. Only generated arrays/images are read by subprocess scorer.
for case,badtime in [('valid',False),('model_before_condition_seal',True)]:
 base=OUT/case;base.mkdir();pre=base/'prepare';model=base/'model';pre.mkdir();model.mkdir()
 targets=[]
 for i in range(4):
  dp=base/f'artificial_depth{i}.png';Image.fromarray(np.full((480,640),5000,np.uint16)).save(dp);targets.append({'query_index':20+i,'depth_path':str(dp),'depth_sha256':sha(dp)})
 put(pre/'frozen_manifest.json',{'schema':'synthetic-prepare-provenance'})
 put(pre/'alignment.json',{'schema':'s14e-history-alignment-v1','s_model_per_metric':2.})
 np.savez_compressed(pre/'condition.npz',target_poses=np.tile(np.eye(4),(4,1,1)),K=np.tile(np.eye(3),(4,1,1)),ray_maps=np.zeros((4,224,224,6),np.float32))
 warp=np.ones((4,224,224));warp[:,:,:112]=np.nan
 np.savez_compressed(pre/'baselines.npz',history_zbuffer_m=warp,history_constant_m=np.full((4,224,224),2.))
 prepmeta={'schema':'s14e-known-camera-prepare-v1','status':'SUCCESS','started_utc':'2026-01-01T00:01:00+00:00','completed_utc':'2026-01-01T00:02:00+00:00','manifest_sha256':sha(pre/'frozen_manifest.json'),'output_sha256':{p.name:sha(p) for p in pre.iterdir()}}
 put(pre/'run_metadata.json',prepmeta)
 put(pre/'condition_seal.json',{'schema':'s14e-condition-seal-v1','sealed_utc':'2026-01-01T00:03:00+00:00','condition_npz_sha256':sha(pre/'condition.npz'),'prepare_manifest_sha256':prepmeta['manifest_sha256'],'payload_sha256':{p.name:sha(p) for p in pre.iterdir()}})
 qmanifest={'schema':'s14e-state-reuse-manifest-v1','condition_npz':str(pre/'condition.npz'),'condition_seal':str(pre/'condition_seal.json'),'identities':{str(pre/'condition.npz'):sha(pre/'condition.npz'),str(pre/'condition_seal.json'):sha(pre/'condition_seal.json')}}
 put(model/'frozen_manifest.json',qmanifest)
 for i in range(5):np.savez_compressed(model/f'query_call_{i}.npz',pts3d_in_self_view=np.full((1,224,224,3),2.,np.float32))
 modelmeta={'schema':'s14e-state-reuse-queries-v1','status':'SUCCESS','started_utc':'2026-01-01T00:02:30+00:00' if badtime else '2026-01-01T00:04:00+00:00','completed_utc':'2026-01-01T00:05:00+00:00','parity_all_six_outputs_exact':True,'counters':{'query_calls':5,'query_image_encoder_batches':0},'query_runs':[{'call':i,'status':'PASS'} for i in range(5)],'manifest_sha256':sha(model/'frozen_manifest.json'),'output_sha256':{p.name:sha(p) for p in model.iterdir()}}
 put(model/'run_metadata.json',modelmeta)
 seal={'schema':'s14e-combined-prediction-seal-v1','sealed_utc':'2026-01-01T00:06:00+00:00','identities':{str(p):sha(p) for d in [pre,model] for p in d.rglob('*') if p.is_file()}};put(base/'seal.json',seal)
 manifest={'schema':'s14e-score-manifest-v1','frozen_utc':'2026-01-01T00:00:00+00:00','runner':str(SRC),'python':sys.executable,'identities':{str(SRC):sha(SRC),**{x['depth_path']:x['depth_sha256'] for x in targets}},'model_result_dir':str(model),'prepare_result_dir':str(pre),'targets':targets};put(base/'manifest.json',manifest)
 cmd=[sys.executable,str(SRC),'--manifest',str(base/'manifest.json'),'--prediction-seal',str(base/'seal.json'),'--prediction-seal-sha256',sha(base/'seal.json'),'--output',str(base/'result')]
 proc=subprocess.run(cmd,capture_output=True,text=True,timeout=30);(base/'stdout.txt').write_text(proc.stdout);(base/'stderr.txt').write_text(proc.stderr)
 got=json.loads((base/'result/run_metadata.json').read_text())
 if badtime:
  ck(case+'/time_rejected',proc.returncode==1 and got['status']=='FAILED' and 'Prepare / condition seal / model start order' in got['error'])
  ck(case+'/no_depth_hash_open',got['counters']['depth_open_attempts']==0 and 'first_target_depth_hash_utc' not in got)
 else:
  ck(case+'/completed',proc.returncode==0 and got['status']=='SUCCESS')
  ck(case+'/4_images_6_prediction_arrays',got['counters']['depths_decoded']==4 and got['counters']['npz_arrays_decoded']==6)
  metrics=json.loads((base/'result/metrics.json').read_text());ck(case+'/all12',len(metrics['rows'])==12)
  for row in metrics['rows']:
   wanted={'ray':1.,'history_zbuffer':.5,'history_constant':0.}[row['method']]
   close(case+f'/q{row["query_index"]}/{row["method"]}',row['delta1_all_gt'],wanted)
  ck(case+'/seal_before_hash_before_decode',got['seal_verified_utc']<got['first_target_depth_hash_utc']<got['first_depth_open_attempt_utc'])
 r['integration'].append({'case':case,'pass':True,'status':got['status'],'depth_opens':got['counters']['depth_open_attempts'],'prediction_arrays_decoded':got['counters']['npz_arrays_decoded'],'artificial_only':True})
ck('source_unchanged',sha(SRC)==r['source_sha256']);r.update(status='PASS',completed_utc=now(),check_count=len(r['checks']),test_source_sha256=sha(__file__))
put(OUT/'receipt.json',r);print(json.dumps({k:r[k] for k in ['status','check_count','completed_utc','source_sha256']}))
