from pathlib import Path
import json, math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
R=json.loads((ROOT/'work/S91R_saved_future_error_reanalysis/results.json').read_text())
prop=np.load(ROOT/'results/S15B_prefix_proposals/proposals.npz',allow_pickle=False)
pred=np.load(ROOT/'results/S15B_consumer_predictions/target_predictions.npz',allow_pickle=False)
gt=np.load(ROOT/'results/S15B_consumer_scores/evaluation_gt.npz',allow_pickle=False)['depth_m']
old=prop['old_self_z_m'].astype(float); new=prop['new_self_z_m'].astype(float); conf=prop['new_conf_self'].astype(float)
d=np.full(old.shape,np.nan); ok=np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0); d[ok]=np.abs(new[ok]-old[ok])/(0.5*(np.abs(new[ok])+np.abs(old[ok])))
l=np.full(conf.shape,np.nan); ok=np.isfinite(conf)&(conf>0); l[ok]=1/conf[ok]
def spearman(a,b):
 ra=np.argsort(np.argsort(a,kind='mergesort'),kind='mergesort').astype(float); rb=np.argsort(np.argsort(b,kind='mergesort'),kind='mergesort').astype(float)
 ra-=ra.mean(); rb-=rb.mean(); den=np.sqrt((ra*ra).sum()*(rb*rb).sum()); return None if den==0 else float((ra*rb).sum()/den)
checks=[]
for method,mi in [('never',0),('all_new',1)]:
 for ti in range(4):
  p=pred['depth_m'][mi,ti].astype(float); ids=pred['source_pixel_identity'][mi,ti].astype(int); src=ids//(224*224); loc=ids%(224*224); rr=loc//224; cc=loc%224; valid=(ids>=0)&np.isfinite(p)&(p>0)&np.isfinite(gt[ti])&(gt[ti]>0)
  for si in range(4):
   m=valid&(src==si)
   if not m.any(): continue
   x=d[si,rr[m],cc[m]]; y=np.abs(p[m]-gt[ti][m])/gt[ti][m]; z=np.isfinite(x)&np.isfinite(y); x=x[z]; y=y[z]
   got=next(row for row in R['rows'] if row['method']==method and row['target_index']==20+ti and row['source_ordinal']==si)
   exp=got['risk_disagreement']['spearman_risk_error']
   val=spearman(x,y)
   checks.append(abs(val-exp)<1e-12)
print('S91R_INDEPENDENT_RECOMPUTE_PASS',len(checks),all(checks))
if not all(checks): raise SystemExit(2)
