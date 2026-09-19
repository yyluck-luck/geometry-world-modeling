"""Frozen saved-real diagnostic. No model, no RGB decode, no parameter search."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, bisect, csv, hashlib, io, json, math, statistics, sys, time
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / 'work/S23_geometry_preparation'
OUT = ROOT / 'results/S23_geometry_diagnostic'
DATA = ROOT / 'data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk'
BASES = {'cut3r': ROOT/'results/S21_baseline/cut3r',
         'ttt3r': ROOT/'results/S21_baseline/ttt3r',
         'filt3r': ROOT/'results/S22_filt_shared_precision/filt3r'}
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, value): Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
def timestamps(p):
    return {float(s.split()[0]): s.split()[1] for s in p.read_text().splitlines() if s.strip() and not s.startswith('#')}
def associate(a,b):
    keys=sorted(b); candidates=[]
    for x in sorted(a):
        for y in keys[bisect.bisect_right(keys,x-.02):bisect.bisect_left(keys,x+.02)]:
            if abs(x-y)<.02: candidates.append((abs(x-y),x,y))
    aa=set();bb=set();matched={}
    for d,x,y in sorted(candidates):
        if x not in aa and y not in bb: matched[x]=y;aa.add(x);bb.add(y)
    return matched
def nearest(a, h=384, w=512):
    y=((2*np.arange(h)+1)*a.shape[0])//(2*h)
    x=((2*np.arange(w)+1)*a.shape[1])//(2*w)
    return a[y[:,None],x[None,:]]
def metrics(p,g):
    valid=g>0; n=int(valid.sum()); good=valid & np.isfinite(p) & (p>0)
    k=int(good.sum()); pv=p[good];gv=g[good]
    ratios=np.maximum(pv/gv,gv/pv); delta=int((ratios<1.25).sum())
    sums=[float(np.sum(np.abs(pv-gv)/gv)),float(np.sum((pv-gv)**2)),float(np.sum(np.log(pv/gv)**2))]
    complete=(n>0 and n==k)
    return dict(gt_count=n,pred_positive_count=k,pred_invalid_count=n-k,delta_count=delta,
                delta1=delta/n if n else None,absrel=sums[0]/n if complete else None,
                rmse=math.sqrt(sums[1]/n) if complete else None,logrmse=math.sqrt(sums[2]/n) if complete else None,
                valid_prediction_absrel=sums[0]/k if k else None,sums_valid=sums)
def scalar_metrics(p,g):
    pairs=[(float(x),float(y)) for x,y in zip(p.ravel(),g.ravel()) if y>0]
    good=[(x,y) for x,y in pairs if math.isfinite(x) and x>0]
    n=len(pairs);k=len(good);d=sum(max(x/y,y/x)<1.25 for x,y in good)
    sums=[math.fsum(abs(x-y)/y for x,y in good),math.fsum((x-y)**2 for x,y in good),math.fsum(math.log(x/y)**2 for x,y in good)]
    return [n,k,d,*sums]
def check_metrics(p,g):
    a=metrics(p,g);b=scalar_metrics(p,g)
    assert [a['gt_count'],a['pred_positive_count'],a['delta_count']]==b[:3]
    assert np.allclose(a['sums_valid'],b[3:],atol=1e-10,rtol=1e-8)
def closure(p,w,pose):
    transformed=p@pose[:3,:3].T+pose[:3,3]
    d=np.linalg.norm(w-transformed,axis=-1);norm=np.linalg.norm(p,axis=-1)
    good=np.isfinite(d)&np.isfinite(norm)&(norm>0)
    return dict(count=int(good.sum()),excluded=int(good.size-good.sum()),
                median=float(np.median(d[good])),p90=float(np.quantile(d[good],.9)),
                relative_median=float(np.median(d[good]/norm[good])))
def check_closure(p,w,pose):
    ds=[];ratios=[]
    for x,y in zip(p.reshape(-1,3),w.reshape(-1,3)):
        moved=[math.fsum(float(pose[i,j])*float(x[j]) for j in range(3))+float(pose[i,3]) for i in range(3)]
        d=math.sqrt(math.fsum((float(y[i])-moved[i])**2 for i in range(3)))
        n=math.sqrt(math.fsum(float(v)**2 for v in x))
        if math.isfinite(d) and math.isfinite(n) and n>0: ds.append(d);ratios.append(d/n)
    a=closure(p,w,pose)
    assert a['count']==len(ds)
    assert np.allclose([a['median'],a['relative_median']],[statistics.median(ds),statistics.median(ratios)],atol=1e-10,rtol=1e-8)
def preflight():
    W.mkdir(parents=True,exist_ok=True);p=W/'preflight.json';assert not p.exists()
    g=np.array([[1.,2.,0.,4.]])
    assert metrics(g,g)['delta1']==1
    assert metrics(g*2,g)['absrel']==1
    assert metrics(g*2,g)['delta1']==0
    assert metrics(np.array([[1.,-2.,9.,np.nan]]),g)['absrel'] is None
    assert metrics(np.array([[1.25,.8]]),np.ones((1,2)))['delta_count']==0
    for v in [g,g*2,np.array([[1.,-2.,9.,np.nan]])]:check_metrics(v,g)
    grid=np.arange(480*640,dtype=np.int32).reshape(480,640)
    assert np.array_equal(nearest(grid),np.asarray(Image.fromarray(grid).resize((512,384),Image.Resampling.NEAREST)))
    pose=np.eye(4);pose[:3,:3]=np.array([[0,-1,0],[1,0,0],[0,0,1]]);pose[:3,3]=[.1,.2,.3]
    x=np.arange(36,dtype=float).reshape(3,4,3)+1;world=x@pose[:3,:3].T+pose[:3,3]
    assert closure(x,world,pose)['median']==0
    world[:,:,0]+=.25
    assert np.isclose(closure(x,world,pose)['median'],.25)
    check_closure(x,world,pose)
    write(p,dict(utc=utc(),passed=True,scope='synthetic metric, grid and nontrivial rigid-closure checks; no real depth read',script_sha256=sha(__file__)))
def prepare():
    assert json.loads((W/'preflight.json').read_text())['passed']
    path=W/'manifest.json';assert not path.exists()
    m=json.loads((ROOT/'work/S21_baseline_preparation/run_manifest.json').read_text())
    rgb=timestamps(DATA/'rgb.txt');depth=timestamps(DATA/'depth.txt');mapping=associate(rgb,depth)
    # Independent candidate enumeration avoids bisect boundary and range indexing.
    candidates=sorted((abs(a-b),a,b) for a in rgb for b in depth if abs(a-b)<.02)
    aa=set();bb=set();reference={}
    for _,a,b in candidates:
        if a not in aa and b not in bb:reference[a]=b;aa.add(a);bb.add(b)
    assert mapping==reference
    scores={}
    for rel in ['results/S21_baseline/scoring/metrics.json','results/S22_filt_shared_precision/scoring/metrics.json']:
        scores.update(json.loads((ROOT/rel).read_text())['methods'])
    frames=[]
    for f in m['frames']:
        t=mapping.get(f['rgb_time']);frames.append(dict(index=f['index'],rgb_time=f['rgb_time'],depth_time=t,depth_file=str(DATA/depth[t]) if t is not None else None))
    identities={str(ROOT/'docs/S23_GEOMETRY_DIAGNOSTIC_PROTOCOL.md'):sha(ROOT/'docs/S23_GEOMETRY_DIAGNOSTIC_PROTOCOL.md'),str(Path(__file__)):sha(__file__),str(DATA/'rgb.txt'):sha(DATA/'rgb.txt'),str(DATA/'depth.txt'):sha(DATA/'depth.txt')}
    for name,b in BASES.items():
        r=json.loads((b/'receipt.json').read_text());assert r['status']=='PASS' and r['frames_completed']==300
        identities[str(b/'receipt.json')]=sha(b/'receipt.json');identities[str(b/'poses.npy')]=r['poses_sha256']
    write(path,dict(frozen_utc=utc(),frames=frames,identities=identities,pose_scales={n:v['alignment']['scale'] for n,v in scores.items()},
                    total_rgb_depth_pairs=len(mapping),selected_matches=sum(f['depth_file'] is not None for f in frames),
                    gt_png_read=False,prior_trajectory_scores_seen=True,scope='seen scene exploratory diagnostic'))
def aggregate(rows):
    result={}
    for mode in ['raw','pose_scaled','frame_oracle']:
        vals=[r[mode] for r in rows if mode in r];n=sum(r['gt_count']for r in vals);k=sum(r['pred_positive_count']for r in vals)
        full=len(vals)==len(rows) and all(r['gt_count']>0 for r in vals)
        av={}
        for key in ['delta1','absrel','rmse','logrmse']:
            good=[r[key]for r in vals if r[key] is not None]
            av[key]=dict(full_frame_equal=float(np.mean(good)) if full and len(good)==len(rows) else None,available_frame_equal=float(np.mean(good)) if good else None,frames=len(good))
        sums=np.sum([r['sums_valid']for r in vals],axis=0) if vals else np.zeros(3)
        pooled=dict(delta1=sum(r['delta_count']for r in vals)/n if n else None,absrel=float(sums[0]/n) if n and n==k else None,rmse=float(np.sqrt(sums[1]/n)) if n and n==k else None,logrmse=float(np.sqrt(sums[2]/n)) if n and n==k else None)
        result[mode]=dict(frame_equal=av,pixel_pooled=pooled,gt_count=n,pred_positive_count=k)
    return result
def run():
    manifest=W/'manifest.json';m=json.loads(manifest.read_text());assert not OUT.exists()
    for p,h in m['identities'].items():assert sha(p)==h,p
    OUT.mkdir();started=time.perf_counter()
    write(OUT/'receipt.json',dict(status='RUNNING',started_utc=utc(),manifest_sha256=sha(manifest),gt_png_read=False))
    # This record precedes every new GT PNG read. Predictions already exist and are immutable.
    gt={};gt_ids=[]
    for f in m['frames']:
        if f['depth_file'] is None:continue
        p=Path(f['depth_file']);data=p.read_bytes();im=np.asarray(Image.open(io.BytesIO(data)))
        assert im.shape==(480,640) and np.issubdtype(im.dtype,np.integer)
        gt[f['index']]=nearest(im).astype(np.float64)/5000
        gt_ids.append(dict(index=f['index'],path=str(p),sha256=hashlib.sha256(data).hexdigest()))
    write(OUT/'gt_receipt.json',dict(utc=utc(),images=len(gt_ids),files=gt_ids))
    report=dict(started_utc=utc(),manifest_sha256=sha(manifest),methods={},new_method=False,independent_author_review=False)
    for name,base in BASES.items():
        receipt=json.loads((base/'receipt.json').read_text());poses=np.load(base/'poses.npy').astype(float);rows=[]
        for f in receipt['outputs']:
            i=f['index'];data=(base/f['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==f['sha256']
            with np.load(io.BytesIO(data))as arrays:
                p=arrays['pts3d_in_self_view'][0].astype(float);world=arrays['pts3d_in_other_view'][0].astype(float)
            assert p.shape==world.shape==(384,512,3)
            row=dict(index=i,closure=closure(p,world,poses[i]))
            check_closure(p[::32,::32],world[::32,::32],poses[i])
            if i in gt:
                g=gt[i];z=p[:,:,2];good=(g>0)&np.isfinite(z)&(z>0)
                oracle=float(np.median(g[good]/z[good])) if good.any() else None
                row['oracle_scale']=oracle
                scales={'raw':1.,'pose_scaled':m['pose_scales'][name]}
                if oracle is not None:scales['frame_oracle']=oracle
                for mode,s in scales.items():row[mode]=metrics(z*s,g);check_metrics((z*s)[::32,::32],g[::32,::32])
            rows.append(row)
            if (i+1)%25==0:
                write(OUT/'receipt.json',dict(status='RUNNING',method=name,frames_completed=i+1,utc=utc(),elapsed_seconds=time.perf_counter()-started))
                print(json.dumps(dict(method=name,frames=i+1,seconds=time.perf_counter()-started)),flush=True)
        write(OUT/(name+'_frames.json'),rows)
        report['methods'][name]=dict(aggregate=aggregate(rows),blocks=[dict(start=k,end_exclusive=k+60,aggregate=aggregate(rows[k:k+60])) for k in range(0,300,60)],
            closure_median_mean=float(np.mean([r['closure']['median']for r in rows])),closure_relative_median_mean=float(np.mean([r['closure']['relative_median']for r in rows])),frames=len(rows),scalar_grid_checks=300)
    report.update(completed_utc=utc(),passed=True,elapsed_seconds=time.perf_counter()-started)
    write(OUT/'metrics.json',report);write(OUT/'receipt.json',dict(status='PASS',completed_utc=utc(),elapsed_seconds=report['elapsed_seconds'],methods=list(BASES),frames_per_method=300,manifest_sha256=sha(manifest),metrics_sha256=sha(OUT/'metrics.json')))
    print(json.dumps({n:r['aggregate']['raw']['frame_equal']for n,r in report['methods'].items()}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['preflight','prepare','run']);args=ap.parse_args()
    {'preflight':preflight,'prepare':prepare,'run':run}[args.action]()
