#!/usr/bin/env python3
"""Independent saved S31 check: scalar log-ratios/fsum and raw-moment variance."""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'results/S31_scale_shape_diagnostic'
HELPER = ROOT / 'work/S28_independent_numeric_review/recompute.py'
HELPER_SHA = '2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2'
ARMS = ('C2t','C2a')
METRICS = ('absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt')

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(name, value): (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def require(ok, why):
    if not ok: raise ValueError(why)

def main(args):
    require(not (HERE/'receipt.json').exists(), 'No repeated review')
    require(sha(__file__)==args.script_sha and sha(HERE/'protocol.md')==args.protocol_sha, 'Caller reviewed source/protocol')
    require(sha(HELPER)==HELPER_SHA and sha(args.contract)==args.contract_sha, 'Bound independent helper and frozen contract')
    started=utc(); timer=time.perf_counter()
    write('receipt.json',dict(status='RUNNING',started_utc=started))
    try:
        c=read(args.contract); prod=read(BASE/'receipt.json')
        require(c['status']=='FROZEN' and c['arms']==list(ARMS) and c['depth_shape']==[4,384,512], 'Prespecified domain')
        require(prod['status']=='PASS' and prod['contract_sha256']==args.contract_sha and prod['inputs_unchanged'], 'Producer PASS first')
        require(prod['per_frame_rows']==8 and prod['endpoint_groups']==2 and prod['old_endpoint_scores_recomputed']==0, 'Full producer scope')
        for key in ('new_model','new_MST','new_GA','new_backward','new_Adam'): require(prod[key]==0,'No new optimizer')
        ids={str(Path(args.contract).resolve()):args.contract_sha,str(Path(__file__).resolve()):args.script_sha,
             str(HERE/'protocol.md'):args.protocol_sha,str(HELPER):HELPER_SHA,str(BASE/'receipt.json'):sha(BASE/'receipt.json')}
        for p,s in c['identities'].items(): require(sha(p)==s,'Source identity'); ids[p]=s
        prior_path=c['s30_metrics']; prior_sha=c['saved_input_sha256'][prior_path]
        require(sha(prior_path)==prior_sha==prod['input_sha256'][prior_path], 'Bound original score import source')
        ids[prior_path]=prior_sha
        for arm in ARMS:
            for ep in ('initial','final'):
                item=c['depth_inputs'][arm][ep]; require(sha(item['path'])==item['sha256']==prod['input_sha256'][item['path']], 'Actual original endpoint seal')
                ids[item['path']]=item['sha256']
        for name,s in prod['output_sha256'].items():
            p=BASE/name; require(p.resolve().is_relative_to(BASE) and sha(p)==s, 'Complete new producer output identity')
            ids[str(p)]=s
        normseal=read(BASE/'normalization_seal.json'); gtseal=read(BASE/'pre_GT_decode_seal.json')
        require(normseal['sensor_GT_bytes_read'] is False and gtseal['sensor_GT_images_decoded']==0, 'Recorded stage ordering')
        require(datetime.fromisoformat(normseal['utc'])<=datetime.fromisoformat(prod['sensor_GT_started_utc'])<=datetime.fromisoformat(gtseal['utc']), 'Seal timestamp order')
        for p,s in normseal['output_sha256'].items(): require(ids[p]==s==gtseal['normalized_output_sha256'][p], 'Both normalized outputs sealed')
        gt_bytes=[]
        for row in c['gt_depth_frames']:
            raw=Path(row['path']).read_bytes(); require(hashlib.sha256(raw).hexdigest()==row['sha256']==prod['input_sha256'][row['path']], 'Same GT bytes')
            ids[row['path']]=row['sha256']; gt_bytes.append(raw)
        require(len(gt_bytes)==4, 'All four GT seals')
        write('input_seal.json',dict(status='PASS_ALL_BOUND_BEFORE_DECODE',utc=utc(),ids=ids,arrays_decoded=False))
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[key]='1'
        import numpy as np
        import cv2
        cv2.setNumThreads(1); require(np.__version__=='1.26.4','Local numpy version')
        spec=importlib.util.spec_from_file_location('s31_original_independent_metric',HELPER)
        h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
        def load(p,key):
            p=Path(p); raw=p.read_bytes(); require(hashlib.sha256(raw).hexdigest()==ids[str(p)],'Archive seal before decode')
            with np.load(io.BytesIO(raw),allow_pickle=False) as z: return z[key].copy()
        gt=[cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_UNCHANGED) for raw in gt_bytes]
        require(all(x is not None and x.shape==(480,640) and x.dtype==np.uint16 for x in gt),'Four original uint16 images')
        official=read(BASE/'metrics.json'); lookup={(r['mode'],r['index']):r for r in official['per_frame']}
        require(len(official['per_frame'])==len(lookup)==8 and set(lookup)=={(a,i) for a in ARMS for i in range(4)},'Eight unique rows')
        decomposition={}; rows=[]; means={}; diffs={}; algebra_diffs={}; scalar_checks=0
        def near(value, reported, label):
            nonlocal scalar_checks
            if value is None or reported is None: require(value is None and reported is None,'Null algebra '+label)
            else:
                require(math.isfinite(value) and math.isfinite(reported) and math.isclose(value,reported,abs_tol=1e-9,rel_tol=1e-12),'Algebra '+label)
                algebra_diffs[label]=abs(value-reported)
            scalar_checks+=1
        for arm in ARMS:
            a=load(c['depth_inputs'][arm]['initial']['path'],'depth'); b=load(c['depth_inputs'][arm]['final']['path'],'depth')
            require(a.shape==b.shape==(4,384,512) and a.dtype==b.dtype==np.float32,'Original depth schema')
            require(np.isfinite(a).all() and np.isfinite(b).all() and (a>0).all() and (b>0).all(),'Complete positive domain')
            # An independent scalar log(b/a) path; producer uses vector log(b)-log(a).
            vv=np.fromiter((math.log(float(y)/float(x)) for x,y in zip(a.flat,b.flat)),dtype=np.float64,count=a.size).reshape(a.shape)
            n=a.size; m=384*512; mu=math.fsum(vv.flat)/n; k=math.exp(-mu)
            fm=[math.fsum(x.flat)/m for x in vv]; sq=[math.fsum(float(z)*float(z) for z in x.flat) for x in vv]
            total=math.fsum(sq); common=n*mu*mu
            # Raw-moment identities, not producer's centered-square sums.
            frame_second=m*math.fsum(x*x for x in fm)
            between=frame_second-common; within=math.fsum(s-m*x*x for s,x in zip(sq,fm))
            centered=total-common
            d=read(BASE/arm/'decomposition.json'); archive=BASE/arm/'diagnostic_arrays.npz'
            stored_v=load(archive,'log_change'); stored=load(archive,'depth'); stored_fm=load(archive,'frame_mean_log_change')
            require(stored.dtype==stored_v.dtype==stored_fm.dtype==np.float64 and stored.shape==stored_v.shape==a.shape and stored_fm.shape==(4,),'Full derived array schema')
            require(np.allclose(stored_v,vv,atol=1e-12,rtol=1e-12),'Every log-ratio pixel')
            reference=k*b.astype(np.float64)
            require(np.allclose(stored,reference,atol=1e-12,rtol=1e-12),'Every transformed pixel')
            require(np.allclose(stored_fm,fm,atol=1e-12,rtol=1e-12),'All saved frame means')
            require(load(archive,'mu').shape==load(archive,'k').shape==(),'Scalar archive shape')
            near(float(load(archive,'mu')),mu,arm+'/saved_mu'); near(float(load(archive,'k')),k,arm+'/saved_k')
            near(mu,normseal['scalars'][arm]['mu'],arm+'/pre_GT_mu'); near(k,normseal['scalars'][arm]['k'],arm+'/pre_GT_k')
            for key,value in dict(mu=mu,k=k,geometric_mean_final_to_initial=math.exp(mu),total_sum_squares=total,
                                  centered_sum_squares=centered,nonuniform_rms_log=math.sqrt(max(0,centered)/n)).items(): near(value,d[key],arm+'/'+key)
            require(d['total_pixels']==n and d['frame_count']==4 and d['grid_shape']==[4,384,512] and d['all_pixels_retained'], 'Complete decomposition denominator')
            for name,value in [('common_global_mean',common),('between_frame_means',between),('within_frame',within)]:
                comp=d['components'][name]
                for key,v in dict(sum_squares=value,mean_square=value/n,rms_log=math.sqrt(max(0,value)/n),fraction_of_total=value/total if total else None).items(): near(v,comp[key],arm+'/'+name+'/'+key)
            require([x['index'] for x in d['per_frame']]==list(range(4)),'All decomposition frames')
            for i,rr in enumerate(d['per_frame']):
                require(rr['pixels']==m,'Frame denominator')
                ws=sq[i]-m*fm[i]*fm[i]
                for key,value in dict(mean_log_change=fm[i],deviation_from_global_mean=fm[i]-mu,log_change_min=float(vv[i].min()),log_change_max=float(vv[i].max()),within_frame_sum_squares=ws,within_frame_rms_log=math.sqrt(max(0,ws)/m)).items(): near(value,rr[key],arm+'/frame'+str(i)+'/'+key)
                rr2=dict(mode=arm,index=i,**h.independent_frame(stored[i],gt[i])); rows.append(rr2)
                report=lookup[arm,i]
                for key in h.COUNT_KEYS: require(rr2[key]==report[key],'Full score count '+key)
                require(rr2['metric_status']==report['metric_status'],'Metric status')
                for key in METRICS: h.metric_match(rr2[key],report[key],arm+'/'+str(i)+'/'+key,diffs)
            decomposition[arm]=dict(mu=mu,k=k,total=total,common=common,between=between,within=within,
                full_log_ratio_max_abs_difference=float(np.max(np.abs(vv-stored_v))),full_depth_max_abs_difference=float(np.max(np.abs(reference-stored))))
            selected=[x for x in rows if x['mode']==arm]; reported=official['normalized_common4'][arm]; means[arm]={}
            require(reported['frame_indices']==list(range(4)) and reported['frame_count']==4 and reported['aggregation']=='equal_frame_mean;no_available_frame_or_pixel_pooled_substitution','Same aggregate domain')
            for key in METRICS:
                values=[x[key] for x in selected]; value=math.fsum(values)/4 if all(x is not None for x in values) else None
                means[arm][key]=value; h.metric_match(value,reported[key],arm+'/mean/'+key,diffs)
                require(reported[key+'_defined_frames']==sum(x is not None for x in values),'Defined count')
            for key in ('gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels','prediction_invalid_on_gt_pixels'): require(reported[key+'_sum_descriptive']==sum(x[key] for x in selected),'Aggregate count')
            require(reported['empty_gt_frames']==[x['index'] for x in selected if x['gt_valid_pixels']==0] and reported['invalid_prediction_frames']==[x['index'] for x in selected if x['prediction_invalid_on_gt_pixels']>0],'Full missing lists')
        imported=read(BASE/'imported_S30_scores.json'); old=read(c['s30_metrics'])
        require(imported['metrics']==old and imported['sha256']==prod['input_sha256'][c['s30_metrics']],'Exact original scores import')
        for arm in ARMS:
            for ep in ('initial','final'):
                for key in METRICS:
                    x,y=means[arm][key],old['common4'][arm][ep][key]
                    h.metric_match(x-y if x is not None and y is not None else None,official['normalized_minus_imported_S30'][arm][ep][key],arm+'/difference/'+key,diffs)
        with (BASE/'per_frame.csv').open() as f: csvrows=list(csv.DictReader(f))
        require(len(csvrows)==8 and {(x['mode'],int(x['index'])) for x in csvrows}==set(lookup),'Full CSV')
        for rr in csvrows:
            target=next(x for x in rows if x['mode']==rr['mode'] and x['index']==int(rr['index']))
            for key in h.COUNT_KEYS: require(int(rr[key])==target[key],'CSV count')
            require(rr['metric_status']==target['metric_status'],'CSV status')
            for key in METRICS: h.metric_match(float(rr[key]) if rr[key] else None,target[key],'csv/'+key,diffs)
        for p,s in ids.items(): require(sha(p)==s,'Input unchanged after complete review')
        write('recomputed.json',dict(decomposition=decomposition,per_frame=rows,means=means,metric_differences=diffs,algebra_scalar_differences=algebra_diffs))
        write('receipt.json',dict(status='PASS',started_utc=started,completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
            contract_sha256=args.contract_sha,script_sha256=args.script_sha,protocol_sha256=args.protocol_sha,
            per_frame_score_rows=8,mean_groups=2,mean_float_checks=8,imported_endpoint_differences=16,
            decomposition_pixel_visits=2*4*384*512,score_grid_pixel_visits=8*384*512,algebra_scalar_checks=scalar_checks,
            maximum_metric_difference=diffs,full_arrays=decomposition,GT_images_decoded=4,inputs_unchanged=True,
            scope='Root independent scalar log-ratio/fsum/raw-moment decomposition; unchanged different-author OpenCV rowwise scoring helper. Saved outputs only; no causal or new-method claim.',
            new_model=0,new_GA=0,new_MST=0,new_backward=0,output_sha256={'recomputed.json':sha(HERE/'recomputed.json'),'input_seal.json':sha(HERE/'input_seal.json')}))
        print(json.dumps(dict(status='PASS',scalar_checks=scalar_checks,maximum_metric_difference=diffs,decomposition=decomposition)))
    except BaseException as e:
        write('receipt.json',dict(status='FAILED',started_utc=started,failed_utc=utc(),error=repr(e),policy='Preserve output; no automatic retry/tolerance change'))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('contract','contract-sha','script-sha','protocol-sha'): p.add_argument('--'+key,required=True)
    main(p.parse_args())
