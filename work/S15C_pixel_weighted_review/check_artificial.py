"""Independent scalar review plus tests of the newly authored auxiliary aggregate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('score',ROOT/'scripts/s15c_observed_depth.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def scalar_pool(all_gt, all_prediction, which):
    total=hits=own=common=0
    own_errors=[];own_relative=[];common_errors=[];common_relative=[]
    for gt,prediction in zip(all_gt,all_prediction):
        for r in range(gt.shape[0]):
            for c in range(gt.shape[1]):
                truth=float(gt[r,c])
                if not math.isfinite(truth) or truth<=0:continue
                total+=1
                p=float(prediction[which,r,c]);other=float(prediction[1-which,r,c])
                if not math.isfinite(p) or p<=0:continue
                own+=1;hits+=int(max(p/truth,truth/p)<1.25)
                error=abs(p-truth);own_errors.append(error);own_relative.append(error/truth)
                if math.isfinite(other) and other>0:
                    common+=1;common_errors.append(error);common_relative.append(error/truth)
    result={'delta1_all_gt':hits/total,'coverage':own/total,'gt_valid_pixel_visits':total,
            'own_valid_pixel_visits':own,'common_valid_pixel_visits':common,'delta1_success_pixel_visits':hits}
    for domain,e,rel in [('own',own_errors,own_relative),('common',common_errors,common_relative)]:
        result[domain+'_mae_m']=math.fsum(e)/len(e)
        result[domain+'_abs_rel']=math.fsum(rel)/len(rel)
        result[domain+'_rmse_m']=math.sqrt(math.fsum(x*x for x in e)/len(e))
    return result


def main():
    started=datetime.now(timezone.utc).isoformat();cases=[]
    gt=np.arange(1,13,dtype=float).reshape(4,1,3);pred=gt*2
    pred[0,0,0]=np.nan;pred[1,0,0]=-1
    calibration=m.calibration_values(pred,gt)
    assert calibration['s_model_per_meter']==2 and calibration['constant_depth_m']==6.5
    assert calibration['ratio_count']==10 and calibration['positive_gt_count']==12
    assert np.allclose((pred/2)[np.isfinite(pred)&(pred>0)],gt[np.isfinite(pred)&(pred>0)])
    cases.append('Independent tiny calibration: s=pred/GT then pred/s; constant uses all first-four valid GT')
    all_gt=[];all_prediction=[];rows=[]
    for i in range(4,20):
        truth=np.array([[1.,2.,3.,4.]])
        if i%3==0:truth[0,0]=0
        prediction=np.stack([np.array([[1.,2.5,6.,np.nan]]),np.full((1,4),float(1+i%5))])
        if i%2==0:prediction[0,0,2]=3
        all_gt.append(truth);all_prediction.append(prediction)
        r,_=m.compute_metrics(truth,prediction,i);rows.extend(r)
    pooled=m.pixel_weighted_metrics(rows)
    for j in range(2):
        expected=scalar_pool(all_gt,all_prediction,j)
        for key,value in expected.items():
            assert math.isclose(pooled[j][key],value,rel_tol=1e-12,abs_tol=1e-12),(key,pooled[j][key],value)
    primary=m.equal_frame_means(rows)
    assert not math.isclose(primary[0]['means']['delta1_all_gt'],pooled[0]['delta1_all_gt'],rel_tol=1e-12,abs_tol=1e-12)
    weighted_rmse_average=math.fsum(r['own_rmse_m']*r['own_valid_count']/pooled[0]['own_valid_pixel_visits'] for r in rows if r['method']=='model')
    assert not math.isclose(weighted_rmse_average,pooled[0]['own_rmse_m'],rel_tol=1e-12,abs_tol=1e-12)
    cases.append('All sixteen unequal domains: pooled counts/MAE/AbsRel/RMSE match direct scalar pixel lists; primary unchanged')
    missing=[dict(r) for r in rows];missing[0]['own_mae_m']=None
    result=m.pixel_weighted_metrics(missing)[0]
    assert result['own_mae_m'] is None and result['own_mae_m_unavailable_frame_indices']==[4]
    empty=[]
    for i in range(4,20):r,_=m.compute_metrics(np.zeros((1,1)),np.ones((2,1,1)),i);empty.extend(r)
    result=m.pixel_weighted_metrics(empty)
    assert all(r['delta1_all_gt'] is None and r['own_rmse_m'] is None and r['gt_domain_status']=='EMPTY_GT_DOMAIN' for r in result)
    cases.append('Nonempty-domain missing errors invalidate auxiliary error, and all-empty GT stays null')
    p=ROOT/'scripts/s15c_observed_depth.py'
    receipt={'schema':'s15c-pixel-weighted-review-v1','started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
             'status':'PASS','cases':cases,'runner_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
             'check_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'scope':'No real RGB/depth/NPZ read. Existing calibration/scoring reviewed by different author; new pixel_weighted_metrics authored and tested here, awaiting root independent review.'}
    (Path(__file__).parent/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
