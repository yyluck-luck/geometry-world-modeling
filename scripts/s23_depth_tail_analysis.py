"""Post-score explanation by fixed GT depth bands; not a new benchmark."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,time
import numpy as np
from PIL import Image
from s23_geometry_diagnostic import nearest,BASES

root=Path(__file__).resolve().parents[1]
out=root/'results/S23_depth_tail';out.mkdir(exist_ok=False)
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
start=time.perf_counter();previous=root/'results/S23_geometry_diagnostic'
m=json.loads((root/'work/S23_geometry_preparation/manifest.json').read_text())
gtreceipt=json.loads((previous/'gt_receipt.json').read_text())
scores=json.loads((previous/'metrics.json').read_text());assert scores['passed']
bands=[(0,2),(2,4),(4,8),(8,float('inf'))]
save(out/'analysis_contract.json',dict(utc=utc(),post_score=True,reason='FILT raw AbsRel improves but raw RMSE is worse than TTT; inspect depth-range contributions without excluding any valid GT.',
    bands_m=['(0,2]','(2,4]','(4,8]','(8,infinity)'],method_specific_filter=False,
    input_metrics_sha256=sha(previous/'metrics.json'),gt_receipt_sha256=sha(previous/'gt_receipt.json'),script_sha256=sha(__file__),new_model_runs=0))
gt={}
for item in gtreceipt['files']:
    data=Path(item['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==item['sha256']
    gt[item['index']]=nearest(np.asarray(Image.open(io.BytesIO(data)))).astype(float)/5000
report=dict(started_utc=utc(),methods={},post_score=True)
for name,base in BASES.items():
    n=np.zeros(4,dtype=np.int64);sse=np.zeros(4);sa=np.zeros(4);count_delta=np.zeros(4,dtype=np.int64);frames=[]
    receipt=json.loads((base/'receipt.json').read_text())
    for item in receipt['outputs']:
        i=item['index']
        if i not in gt:continue
        data=(base/item['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==item['sha256']
        with np.load(io.BytesIO(data))as a:z=a['pts3d_in_self_view'][0,:,:,2].astype(float)
        g=gt[i];valid=g>0;assert np.isfinite(z[valid]).all() and (z[valid]>0).all(),'Preserve failed analysis; no invalid pixel dropping'
        row=[]
        for j,(lo,hi)in enumerate(bands):
            use=(g>lo)&(g<=hi);c=int(use.sum());d=z[use]-g[use]
            sq=float(np.sum(d*d));ar=float(np.sum(np.abs(d)/g[use]));de=int((np.maximum(z[use]/g[use],g[use]/z[use])<1.25).sum())
            n[j]+=c;sse[j]+=sq;sa[j]+=ar;count_delta[j]+=de;row.append(dict(n=c,sse=sq,absrel_sum=ar,delta_count=de))
        frames.append(dict(index=i,bands=row))
    original=scores['methods'][name]['aggregate']['raw'];assert int(n.sum())==original['gt_count']
    assert np.allclose([np.sqrt(sse.sum()/n.sum()),sa.sum()/n.sum(),count_delta.sum()/n.sum()],
        [original['pixel_pooled']['rmse'],original['pixel_pooled']['absrel'],original['pixel_pooled']['delta1']],atol=1e-10,rtol=1e-8)
    result=[]
    for j,label in enumerate(['(0,2]','(2,4]','(4,8]','(8,infinity)']):
        result.append(dict(gt_band_m=label,n=int(n[j]),pixel_share=float(n[j]/n.sum()),sse=float(sse[j]),sse_share=float(sse[j]/sse.sum()),
            pooled_rmse_m=float(np.sqrt(sse[j]/n[j])) if n[j] else None,pooled_absrel=float(sa[j]/n[j]) if n[j] else None,delta1=float(count_delta[j]/n[j]) if n[j] else None))
    report['methods'][name]=result;save(out/(name+'_frames.json'),frames)
report.update(completed_utc=utc(),elapsed_seconds=time.perf_counter()-start,passed=True,original_pooled_reconstruction_passed=True)
save(out/'metrics.json',report);print(json.dumps(report,ensure_ascii=False))
