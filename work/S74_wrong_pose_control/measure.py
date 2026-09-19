"""One fixed wrong-pose-label control on accepted real correspondences."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import time
import traceback

D = Path(__file__).absolute().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def save(p, r):
    with p.open('x') as f:
        json.dump(r, f, indent=2, allow_nan=False)
        f.write('\n')
    p.chmod(0o444)

def main():
    cb = (D/'CONTRACT.json').read_bytes()
    assert len(sys.argv)==2 and sha(cb)==sys.argv[1]
    c = json.loads(cb)
    E = D/'execution_01'
    E.mkdir(exist_ok=False)
    start = time.monotonic()
    r = dict(started_utc=utc(), status='RUNNING', contract_sha256=sha(cb),
             source_sha256=sha(Path(__file__).read_bytes()), reads=[], pairs=[],
             model_calls=0, weight_bytes=0, new_method_validated=False)
    try:
        import numpy as np
        assert np.__version__ == c['numpy_version']
        def read(item):
            b=Path(item['path']).read_bytes()
            r['reads'].append(dict(path=item['path'],bytes=len(b),sha256=sha(b)))
            assert sha(b)==item['sha256']
            return json.loads(b)
        accepted = read(c['real_acceptance'])
        assert accepted['status']=='ACCEPTED_S72_REAL_CONTROL_ARITHMETIC_ONLY'
        assert accepted['files_sha256']['execution_01/receipt.json']==c['real_receipt']['sha256']
        old = read(c['real_receipt'])
        assert old['status']=='COMPLETE_REAL_CONTROL_DIAGNOSTIC'
        real = {p['target_id']:p for p in old['pairs']}
        assert sorted(real)==c['target_ids'] and len(real)==len(old['pairs'])
        assert c['swap']=={'20':23,'21':22,'22':21,'23':20}
        Fs={}
        for j,p in real.items():
            F=np.array(p['F_unit_frobenius'], dtype=np.float64)
            assert F.shape==(3,3) and np.isfinite(F).all()
            norm=float(np.linalg.norm(F));assert norm>0
            Fs[j]=F/norm
        separations=[]
        for j in c['target_ids']:
            k=c['swap'][str(j)]
            minus=float(np.linalg.norm(Fs[j]-Fs[k]))
            plus=float(np.linalg.norm(Fs[j]+Fs[k]))
            d=min(minus,plus)
            separations.append(dict(target_id=j,wrong_pose_label=k,
                normalized_F_correct=Fs[j].tolist(),normalized_F_wrong=Fs[k].tolist(),
                difference_norm=minus,sum_norm=plus,separation=d,float_exact_zero=(d==0.0)))
        save(E/'geometry_separation.json',dict(recorded_before_residuals_utc=utc(),
            contract_sha256=sha(cb),scope=c['geometry'],pairs=separations))
        r['separations']=separations
        r['anchor_population']=old['anchor_keypoints']
        def q(v):return np.quantile(v,c['quantiles']).tolist() if len(v) else None
        def stats(res):
            valid=[v[2] for v in res if v is not None]
            M=len(res);V=len(valid)
            counts={str(cut):sum(x<=cut for x in valid) for cut in c['cutoffs_px']}
            return dict(valid_count=V,invalid_count=M-V,quantiles_px=q(valid),
                maximum_px=max(valid) if valid else None,threshold_counts=counts,
                fractions_of_matches={k:v/M if M else None for k,v in counts.items()},
                fractions_of_valid={k:v/V if V else None for k,v in counts.items()})
        for j in c['target_ids']:
            oldrow=real[j]; k=c['swap'][str(j)]; F=Fs[k]
            M=oldrow['match_count']
            x=np.array(oldrow['source_xy'],dtype=np.float64).reshape(-1,2)
            y=np.array(oldrow['target_xy'],dtype=np.float64).reshape(-1,2)
            assert len(x)==len(y)==len(oldrow['residuals'])==len(oldrow['match_keypoint_ids'])==M
            xh=np.column_stack([x,np.ones(M)]);yh=np.column_stack([y,np.ones(M)])
            lt=xh@F.T;ls=yh@F
            nt=np.linalg.norm(lt[:,:2],axis=1);ns=np.linalg.norm(ls[:,:2],axis=1)
            numerator=np.sum(yh*lt,axis=1)
            mask=np.isfinite(numerator)&np.isfinite(nt)&np.isfinite(ns)&(nt>c['line_epsilon'])&(ns>c['line_epsilon'])
            wrong=[]
            for i, good in enumerate(mask):
                if good:
                    dt=float(abs(numerator[i])/nt[i]);ds=float(abs(numerator[i])/ns[i])
                    wrong.append([dt,ds,(dt+ds)/2])
                else:wrong.append(None)
            correct=oldrow['residuals']
            common=[i for i in range(M) if correct[i] is not None and wrong[i] is not None]
            delta=[wrong[i][2]-correct[i][2] for i in common]
            cells=set(tuple(v) for v in np.clip(np.floor(x[common]/144),0,3).astype(int).tolist())
            row=dict(target_id=j,wrong_pose_label=k,match_count=M,
                match_keypoint_ids=oldrow['match_keypoint_ids'],source_xy=x.tolist(),target_xy=y.tolist(),
                source_coverage=oldrow['source_coverage'],target_coverage=oldrow['target_coverage'],
                matched_anchor_fraction=M/r['anchor_population'],
                correct_residuals_reused=correct,wrong_residuals=wrong,
                correct=stats(correct),wrong=stats(wrong),common_valid_indices=common,
                common_valid_count=len(common),invalid_in_either_count=M-len(common),
                common_source_cells=len(cells),deltas_wrong_minus_correct_px=delta,
                delta_quantiles_px=q(delta),positive_count=sum(v>0 for v in delta),
                negative_count=sum(v<0 for v in delta),zero_count=sum(v==0 for v in delta))
            r['pairs'].append(row)
        med=[p['delta_quantiles_px'][1] if p['delta_quantiles_px'] else None for p in r['pairs']]
        r['event']=dict(all4_paired_medians_positive=None if any(v is None for v in med) else all(v>0 for v in med),
            paired_medians_px=med,scope=c['event'])
        r['limits']=c['limits']
        r['status']='COMPLETE_FIXED_WRONG_LABEL_DIAGNOSTIC'
    except BaseException as exc:
        r.update(status='FAILED_PRESERVED',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
    r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-start)
    save(E/'receipt.json',r)
    print(json.dumps({k:r[k] for k in ['status','completed_utc','elapsed_seconds']}))
    return 0 if r['status']=='COMPLETE_FIXED_WRONG_LABEL_DIAGNOSTIC' else 1

if __name__=='__main__':raise SystemExit(main())
