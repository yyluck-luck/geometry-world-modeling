from pathlib import Path
import json, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'work/S92_tail_risk_decomposition'
P=ROOT/'results/S15B_consumer_predictions/target_predictions.npz'; G=ROOT/'results/S15B_consumer_scores/evaluation_gt.npz'
res=json.load(open(OUT/'results.json')); pred=np.load(P,allow_pickle=False); gt=np.load(G,allow_pickle=False)['depth_m']
checks=[]
for ti,r in enumerate(res['targets']):
 g=gt[ti].astype(float); p0=pred['depth_m'][0,ti].astype(float); p1=pred['depth_m'][1,ti].astype(float)
 m=np.isfinite(g)&(g>0)&np.isfinite(p0)&(p0>0)&np.isfinite(p1)&(p1>0)
 a0=np.abs(p0[m]-g[m]); a1=np.abs(p1[m]-g[m]); e0=a0/g[m]; e1=a1/g[m]; y=e0-e1
 checks += [r['n_pixels']==int(m.sum()),abs(r['mae_never_m']-a0.mean())<1e-12,abs(r['mae_all_new_m']-a1.mean())<1e-12,abs(r['absrel_never']-e0.mean())<1e-12,abs(r['absrel_all_new']-e1.mean())<1e-12,abs(r['improved_fraction']-np.mean(y>0))<1e-12]
print(json.dumps({'status':'PASS' if all(checks) and res['status']=='DESCRIPTIVE_ONLY' else 'FAIL','checks':int(len(checks)),'passed':int(sum(checks)),'results_sha256':hashlib.sha256((OUT/'results.json').read_bytes()).hexdigest()},ensure_ascii=False))
