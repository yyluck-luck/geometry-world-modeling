#!/usr/bin/env python3
"""Only tiny declared artificial arrays; never opens any research NPZ or GT."""
import hashlib
import importlib.util
import json
import os
import time
from datetime import datetime,timezone
from pathlib import Path


def main():
    here=Path(__file__).resolve().parent;out=here/'synthetic_check_receipt.json'
    assert not out.exists(),'Do not repeat/overwrite synthetic attempt'
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import numpy as np
    source=here/'run_s31.py';spec=importlib.util.spec_from_file_location('s31_synthetic_only',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    started=datetime.now(timezone.utc).isoformat();timer=time.perf_counter();checks=[]
    receipt=dict(status='RUNNING_SYNTHETIC_ONLY',started_utc=started,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),real_arrays_read=0,GT_bytes_read=0,new_GA=0,new_model=0,new_backward=0)
    def save():out.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    save()
    try:
        a=np.arange(1,17,dtype=np.float64).reshape(4,2,2)
        result,arrays=module.decompose(a,a.copy())
        assert result['mu']==0 and result['k']==1 and result['total_sum_squares']==0
        assert all(x['fraction_of_total'] is None for x in result['components'].values())
        assert np.array_equal(arrays['depth'],a)
        checks.append(dict(name='identity_and_zero_total_null',shape=list(a.shape),status='PASS_SYNTHETIC'))
        result,arrays=module.decompose(a,.5*a)
        assert np.isclose(result['mu'],-np.log(2),atol=1e-14,rtol=0)
        assert np.isclose(result['k'],2,atol=1e-14,rtol=0)
        assert np.allclose(arrays['depth'],a,atol=1e-13,rtol=1e-14)
        assert result['nonuniform_rms_log']<1e-14
        checks.append(dict(name='one_shared_half_scale',shape=list(a.shape),status='PASS_SYNTHETIC',diagnostic=result))
        common=.2;between=np.array([-.3,-.1,.1,.3]);within=np.array([[-.2,.2],[-.2,.2]])
        v=common+between[:,None,None]+within[None,:,:]
        b=a*np.exp(v);result,arrays=module.decompose(a,b)
        expected=dict(common_global_mean=16*common**2,between_frame_means=4*float(np.sum(between**2)),within_frame=16*.2**2)
        for key,value in expected.items():assert np.isclose(result['components'][key]['sum_squares'],value,atol=1e-13,rtol=1e-13)
        assert np.isclose(result['k'],np.exp(-common),atol=1e-14,rtol=1e-14)
        assert np.allclose(arrays['log_change'],v,atol=1e-14,rtol=1e-14)
        assert np.allclose(arrays['depth'],a*np.exp(between[:,None,None]+within[None,:,:]),atol=1e-13,rtol=1e-14)
        checks.append(dict(name='known_three_component_additive_log_example',shape=list(a.shape),status='PASS_SYNTHETIC',expected_sumsquares=expected,diagnostic=result))
        for label,value in [('zero',0.),('negative',-1.),('nan',float('nan')),('infinite',float('inf'))]:
            bad=a.copy();bad.flat[0]=value
            try:module.decompose(a,bad)
            except ValueError:checks.append(dict(name='reject_without_mask_'+label,status='PASS_SYNTHETIC'))
            else:raise AssertionError('Invalid pixel must stop without filtering: '+label)
        receipt.update(status='PASS_SYNTHETIC_ONLY',completed_utc=datetime.now(timezone.utc).isoformat(),wall_seconds=time.perf_counter()-timer,
            numpy_version=np.__version__,checks=checks,check_count=len(checks),
            source_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==receipt['source_sha256'],
            scope='Three 16-element artificial endpoint pairs plus four one-element invalid mutations; no real S29/S30 or sensor data, not a scientific result')
        assert receipt['source_unchanged'];save();print(json.dumps(dict(status=receipt['status'],check_count=len(checks))))
    except BaseException as exc:
        receipt.update(status='FAILED_SYNTHETIC_ONLY',failed_utc=datetime.now(timezone.utc).isoformat(),error=repr(exc),checks=checks);save();raise


if __name__=='__main__':main()
