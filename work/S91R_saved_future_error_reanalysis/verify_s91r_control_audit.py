"""Independent arithmetic recheck of S91R-C summary (no model/network)."""
from pathlib import Path
import json, numpy as np
ROOT=Path(__file__).resolve().parents[2]; N=224
p=np.load(ROOT/'results/S15B_consumer_predictions/target_predictions.npz',allow_pickle=False)
g=np.load(ROOT/'results/S15B_consumer_scores/evaluation_gt.npz',allow_pickle=False)['depth_m'].astype(float)
rows=[]
for t in range(4):
    ids0=p['source_pixel_identity'][0,t].astype(int); ids1=p['source_pixel_identity'][1,t].astype(int)
    a=p['depth_m'][0,t].astype(float); b=p['depth_m'][1,t].astype(float)
    m=(ids0>=0)&(ids1>=0)&np.isfinite(a)&(a>0)&np.isfinite(b)&(b>0)&np.isfinite(g[t])&(g[t]>0)
    e0=np.abs(a[m]-g[t][m])/g[t][m]; e1=np.abs(b[m]-g[t][m])/g[t][m]; y=e0-e1
    rows.append({'target_index':20+t,'n':int(m.sum()),'mean_y':float(y.mean()),'median_y':float(np.median(y)),
                 'positive_fraction':float((y>0).mean()),'same_identity_fraction':float((ids0[m]==ids1[m]).mean())})
r=json.loads((ROOT/'work/S91R_saved_future_error_reanalysis/control_audit_results.json').read_text())
expected=[(x['target_index'],x['n'],x['mean_signed_improvement'],x['median_signed_improvement'],x['fraction_all_new_improves'],x['same_source_identity_fraction']) for x in r['stratum_records']]
got=[(x['target_index'],x['n'],x['mean_y'],x['median_y'],x['positive_fraction'],x['same_identity_fraction']) for x in rows]
ok=all(a[0]==b[0] and a[1]==b[1] and max(abs(float(a[i])-float(b[i])) for i in range(2,6))<1e-12 for a,b in zip(expected,got))
out={'schema':'s91r-c-summary-recheck-v1','status':'PASS' if ok else 'FAIL','rows':rows,'checks':'independent direct signed-error and identity arithmetic against control_audit_results.json'}
(ROOT/'work/S91R_saved_future_error_reanalysis/control_audit_recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('S91R_C_SUMMARY_RECHECK',out['status'],len(rows))
if not ok: raise SystemExit(2)
