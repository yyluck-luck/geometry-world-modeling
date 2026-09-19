from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'work/S91R_saved_future_error_reanalysis'
P = ROOT / 'results/S15B_prefix_proposals/proposals.npz'
T = ROOT / 'results/S15B_consumer_predictions/target_predictions.npz'
G = ROOT / 'results/S15B_consumer_scores/evaluation_gt.npz'

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def ranks(x):
    order=np.argsort(x, kind='mergesort'); r=np.empty(len(x),float); r[order]=np.arange(len(x),dtype=float)
    # average ties
    vals=x[order]; i=0
    while i<len(x):
        j=i+1
        while j<len(x) and vals[j]==vals[i]: j+=1
        if j-i>1: r[order[i:j]]=0.5*(i+j-1)
        i=j
    return r

def spearman(x,y):
    if len(x)<3: return None
    a=ranks(x); b=ranks(y); a-=a.mean(); b-=b.mean(); den=math.sqrt(float((a*a).sum()*(b*b).sum()))
    return None if den==0 else float((a*b).sum()/den)

def summarize(x,y,risk_name):
    # fixed bins from past-only risk values (not future errors)
    finite=np.isfinite(x)&np.isfinite(y)
    x=x[finite]; y=y[finite]
    if len(x)==0: return {'risk':risk_name,'n':0}
    qs=np.quantile(x,[0,.2,.4,.6,.8,1])
    # deterministic boundary: digitize, last bin included
    b=np.digitize(x,qs[1:-1],right=True)
    means=[]; ns=[]
    for k in range(5):
        z=y[b==k]; means.append(float(z.mean()) if len(z) else None); ns.append(int(len(z)))
    return {'risk':risk_name,'n':int(len(x)),'spearman_risk_error':spearman(x,y),'risk_quantile_edges':[float(v) for v in qs], 'error_mean_by_risk_quintile':means,'count_by_risk_quintile':ns,'high_minus_low':(means[-1]-means[0]) if means[0] is not None and means[-1] is not None else None}

def main():
    prop=np.load(P,allow_pickle=False); pred=np.load(T,allow_pickle=False); gt=np.load(G,allow_pickle=False)['depth_m']
    old=prop['old_self_z_m'].astype(float); new=prop['new_self_z_m'].astype(float); conf=prop['new_conf_self'].astype(float)
    disagreement=np.full(old.shape,np.nan); ok=np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0)
    disagreement[ok]=np.abs(new[ok]-old[ok])/(0.5*(np.abs(new[ok])+np.abs(old[ok])))
    lowconf=np.full(conf.shape,np.nan); cok=np.isfinite(conf)&(conf>0); lowconf[cok]=1.0/conf[cok]
    methods={'never':0,'all_new':1}; rows=[]
    for method,mi in methods.items():
      for ti in range(gt.shape[0]):
        p=pred['depth_m'][mi,ti].astype(float); ids=pred['source_pixel_identity'][mi,ti].astype(int)
        valid=(ids>=0)&np.isfinite(p)&(p>0)&np.isfinite(gt[ti])&(gt[ti]>0)
        src=ids//(224*224); local=ids%(224*224); rr=local//224; cc=local%224
        for si in range(4):
          m=valid&(src==si)
          if not m.any():
            rows.append({'method':method,'target_index':20+ti,'source_ordinal':si,'n':0}); continue
          risk1=disagreement[si,rr[m],cc[m]]; risk2=lowconf[si,rr[m],cc[m]]
          err=np.abs(p[m]-gt[ti][m])/gt[ti][m]
          a=summarize(risk1,err,'old_new_relative_disagreement'); b=summarize(risk2,err,'inverse_new_confidence')
          rows.append({'method':method,'target_index':20+ti,'source_ordinal':si,'n':int(m.sum()),'risk_disagreement':a,'risk_low_confidence':b})
    out={'schema':'s91r-saved-future-error-reanalysis-v1','status':'DESCRIPTIVE_ONLY','protocol_sha256':sha(OUT/'PROTOCOL.md'),'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [P,T,G]},'methods':list(methods),'rows':rows,'limitations':['single already-exposed TUM segment','saved predictions and targets; no new model call','future depth used only for error after fixed risk features','not GRC validation, not cross-scene evidence']}
    (OUT/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'rows':len(rows),'output':str(OUT/'results.json')},ensure_ascii=False))
if __name__=='__main__': main()
