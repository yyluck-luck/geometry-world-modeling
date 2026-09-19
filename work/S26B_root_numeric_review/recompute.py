"""Different-author saved-output score recomputation, after original scoring PASS.

No model or GA imports. OpenCV decoding and per-row scalar accumulation with
integer center mapping, rather than the producer scorer's PIL/full-grid path.
Not a blind experiment, external replication, or independent scene sample.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'results/S26B_consumer_baseline'
PARENT=ROOT/'work/S26B_preparation/run_manifest.json'
MODES={'common_old':4,'cut3r':8,'ttt3r':8,'filt3r':8}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def utc():return datetime.now(timezone.utc).isoformat()

def main():
    assert not (HERE/'attempt.json').exists(),'No repeat or overwrite'
    contract=read(HERE/'contract.json')
    assert set(contract['identities'])=={str(Path(__file__).resolve()),str(PARENT)},'Only self and parent in pre-seal contract'
    for p,h in contract['identities'].items():assert sha(p)==h,p
    start=utc();timer=time.perf_counter();ids=dict(contract['identities'])
    write(HERE/'attempt.json',dict(started_utc=start,status='STARTED_NOT_FINAL_PASS'))
    def bind(p):ids[str(p)]=sha(p);return read(p)
    parent=read(PARENT);parent_sha=sha(PARENT)
    score_receipt=bind(BASE/'scoring/receipt.json')
    assert score_receipt['status']=='PASS' and score_receipt['manifest_sha256']==parent_sha
    metrics_path=BASE/'scoring/metrics.json'
    assert sha(metrics_path)==score_receipt['outputs']['metrics.json']
    metrics=bind(metrics_path)
    assert {(r['mode'],r['index']) for r in metrics['per_frame']}=={(m,i) for m,n in MODES.items() for i in range(n)}
    assert len(metrics['per_frame'])==28
    scored_inputs=score_receipt['input_sha256_before_after']
    common_scope={}
    for mode,count in MODES.items():
        d=BASE/mode;r=bind(d/'receipt.json')
        assert r['status']=='PASS' and r['manifest_sha256']==parent_sha and r['frame_count']==count
        if mode=='common_old':
            assert r['validation_status']=='IMPORT_VALIDATED' and r['new_GA_runs']==0
            assert r['producer_kind']=='IMPORT_VALIDATED_SAVED_ORIGINAL_GA' and r['historical_observations_not_recorded']
            common_scope={k:r[k] for k in ['producer_kind','validation_status','historical_observations_not_recorded','recovery_receipt_sha256','new_GA_runs','historical_GA_steps']}
            common_scope['original_S26_status']='FAILED_PRESERVED'
        assert sha(d/'inputs_seal.json')==r['inputs_seal_sha256']
        assert sha(d/'output.npz')==r['outputs']['output.npz']
        ids[str(d/'inputs_seal.json')]=r['inputs_seal_sha256']
        ids[str(d/'output.npz')]=r['outputs']['output.npz']
        for p in [d/'receipt.json',d/'inputs_seal.json',d/'output.npz']:
            assert ids[str(p)]==scored_inputs[str(p)],'Must recompute the exact originally scored inputs'
    write(HERE/'input_seal.json',{'utc':utc(),'identities':ids,'arrays_decoded':False,'new_sensor_GT_bytes_read':False})

    import numpy as np
    import cv2
    cv2.setNumThreads(1)
    gt=[]
    for row in parent['scoring']['gt_depth_frames']:
        p=Path(row['path']);raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==row['sha256']
        ids[str(p)]=h
        assert h==scored_inputs[str(p)]
        a=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED)
        assert a.shape==(480,640) and a.dtype==np.uint16
        gt.append(a)
    rows=[];maxdiff={'absrel':0.,'rmse_m':0.,'delta1':0.,'prediction_invalid_fraction_on_gt':0.}
    for mode,count in MODES.items():
        with np.load(BASE/mode/'output.npz',allow_pickle=False) as z:depth=z['depth'].copy()
        assert depth.shape==(count,384,512)
        for i in range(count):
            rel=[];sq=[];hits=0;valid=0;invalid=0
            for y in range(384):
                source_y=(5*(2*y+1))//8
                source_x=[(5*(2*x+1))//8 for x in range(512)]
                g=gt[i][source_y,source_x].astype(np.float64)/5000
                p=depth[i,y].astype(np.float64)
                mask=g>0;good=np.isfinite(p)&(p>0)
                valid+=int(mask.sum());invalid+=int((mask&~good).sum())
                p,g=p[mask&good],g[mask&good]
                e=p-g
                rel.append(float(np.sum(np.abs(e)/g)))
                sq.append(float(np.dot(e,e)))
                # Strict ratio threshold expressed as two inequalities.
                hits+=int(np.count_nonzero((p<1.25*g)&(g<1.25*p)))
            row=dict(mode=mode,index=i,gt_valid_pixels=valid,prediction_invalid_on_gt_pixels=invalid,
                absrel=math.fsum(rel)/valid if valid and not invalid else None,
                rmse_m=math.sqrt(math.fsum(sq)/valid) if valid and not invalid else None,
                delta1=hits/valid if valid else None,delta1_success_pixels=hits,
                prediction_invalid_fraction_on_gt=invalid/valid if valid else None)
            reported=next(x for x in metrics['per_frame'] if x['mode']==mode and x['index']==i)
            for key in ['gt_valid_pixels','prediction_invalid_on_gt_pixels','delta1_success_pixels']:
                assert row[key]==reported[key],(mode,i,key,row[key],reported[key])
            for key in maxdiff:
                if row[key] is None:assert reported[key] is None
                else:
                    d=abs(row[key]-reported[key]);maxdiff[key]=max(maxdiff[key],d)
                    assert math.isclose(row[key],reported[key],abs_tol=1e-12,rel_tol=1e-10),(mode,i,key,d)
            rows.append(row)
    aggregate_checks=0
    for partition,indices in [('primary_new4',range(4,8)),('diagnostic_all8',range(8)),('diagnostic_old4',range(4))]:
        assert set(metrics[partition])==(set(MODES) if partition=='diagnostic_old4' else set(MODES)-{'common_old'})
        for mode,target in metrics[partition].items():
            selected=[r for r in rows if r['mode']==mode and r['index'] in indices]
            assert len(selected)==len(indices)
            for key in maxdiff:
                values=[r[key] for r in selected]
                average=math.fsum(values)/len(values) if all(x is not None for x in values) else None
                if average is None:assert target[key] is None
                else:assert math.isclose(average,target[key],abs_tol=1e-12,rel_tol=1e-10)
                aggregate_checks+=1
    for p,h in ids.items():assert sha(p)==h,p
    write(HERE/'recomputed_rows.json',rows)
    write(HERE/'receipt.json',dict(status='PASS',started_utc=start,completed_utc=utc(),
        wall_seconds=time.perf_counter()-timer,manifest_sha256=parent_sha,
        per_frame_rows=len(rows),full_grid_pixel_visits=sum(MODES.values())*384*512,
        valid_GT_pixel_visits=sum(r['gt_valid_pixels'] for r in rows),
        aggregate_checks=aggregate_checks,maximum_metric_difference=maxdiff,
        identities_before_after=ids,inputs_unchanged=True,GT_images_decoded=8,
        common_old_import_scope=common_scope,
        new_model_runs=0,new_GA_runs=0,evidence_scope='Different author, OpenCV and row-wise full-grid mathematical recomputation of already scored data; not external replication or unseen data'))
    print(json.dumps(read(HERE/'receipt.json')|{'identities_before_after':'saved in receipt'},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists():
            write(HERE/'receipt.json',dict(status='FAIL',failed_utc=utc(),error=repr(exc),evidence_scope='Failed independent recomputation attempt, no rerun permitted'))
        raise
