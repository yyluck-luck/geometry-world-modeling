#!/usr/bin/env python3
"""Different-author S28 saved-output review; no model/GA/MST/backward imports.

Explicit caller contract and script digests required. No polling or auto-execution.
All producer/scorer/GT byte seals precede any numerical archive or PNG decoding.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'results/S28_gradient_scale_control'
ARMS=('original','gradient_only')
FLOAT_KEYS=('absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt')
COUNT_KEYS=('grid_pixels','gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels',
            'prediction_invalid_on_gt_pixels','delta1_success_pixels')
SUM_KEYS=('gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels','prediction_invalid_on_gt_pixels')
TOL=dict(abs_tol=1e-12,rel_tol=1e-10)
REQUIRED_PRODUCTS=('output.npz','initial_raw.npz','initial_raw_metadata.json','initial_decoded.npz',
                   'final_raw_before_clean.npz','final_raw_metadata.json','gradient_depth_trace.jsonl',
                   'optimization_trace.jsonl','inputs_seal.json')


def utc():return datetime.now(timezone.utc).isoformat()


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def digest(raw):return hashlib.sha256(raw).hexdigest()


def read(path):return json.loads(Path(path).read_text())


def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def metric_match(a,b,label,differences):
    if a is None or b is None:
        require(a is None and b is None,'Null mismatch: '+label)
    else:
        require(math.isfinite(a) and math.isfinite(b),'Nonfinite metric: '+label)
        diff=abs(a-b);differences[label.split('/')[-1]]=max(differences.get(label.split('/')[-1],0),diff)
        require(math.isclose(a,b,**TOL),f'Metric mismatch {label}: {a} != {b}')


def load_archive(path,identities,shapes=None):
    import numpy as np
    raw=Path(path).read_bytes();require(digest(raw)==identities[str(path)],'Archive changed since seal')
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        require(len(z.files)==len(set(z.files)),'Duplicate archive members')
        if shapes is not None:require(set(z.files)==set(shapes),'Archive member schema changed')
        arrays={}
        for k in z.files:
            a=z[k]
            require(a.dtype.kind in 'fiub','Numeric arrays only')
            if shapes is not None:
                require(a.shape==shapes[k] and a.dtype==np.float32,'FP32 decoded schema changed: '+k)
            arrays[k]=a.copy()
    return arrays


def validate_raw(arrays,meta,label):
    require(set(arrays)==set(meta),'Complete parameter/buffer set: '+label)
    for k,a in arrays.items():
        r=meta[k]
        require(k.startswith(('parameter::','buffer::')),'Unexpected raw tensor name')
        require(list(a.shape)==r['shape'] and str(a.dtype)==r['dtype'],'Raw tensor schema: '+k)
        require(isinstance(r['requires_grad'],bool),'Trainability flag missing')
        require(digest(a.tobytes())==r['sha256'],'Tensor bytes differ from sealed metadata: '+k)
    require({f'parameter::im_depthmaps.{i}' for i in range(4)}<=set(arrays),'All four registered depth leaves required')


def independent_frame(depth,gt_png):
    """OpenCV integer source map; row-wise scalar accumulation, no scorer import."""
    import numpy as np
    source_x=[(5*(2*x+1))//8 for x in range(512)]
    rel,squared=[],[]
    n=invalid_gt=invalid_all=hits=0
    for y in range(384):
        g=gt_png[(5*(2*y+1))//8,source_x].astype(np.float64)/5000.0
        p=depth[y].astype(np.float64)
        valid=g>0;good=np.isfinite(p)&(p>0)
        n+=int(valid.sum());invalid_gt+=int((valid&~good).sum());invalid_all+=int((~good).sum())
        p,g=p[valid&good],g[valid&good]
        e=p-g
        rel.append(float(np.sum(np.abs(e)/g)))
        squared.append(float(np.dot(e,e)))
        hits+=int(np.count_nonzero((p<1.25*g)&(g<1.25*p)))
    return dict(grid_pixels=384*512,gt_valid_pixels=n,gt_invalid_pixels=384*512-n,
        prediction_invalid_all_pixels=invalid_all,prediction_invalid_on_gt_pixels=invalid_gt,
        prediction_invalid_fraction_on_gt=invalid_gt/n if n else None,
        absrel=math.fsum(rel)/n if n and not invalid_gt else None,
        rmse_m=math.sqrt(math.fsum(squared)/n) if n and not invalid_gt else None,
        delta1=hits/n if n else None,delta1_success_pixels=hits,
        metric_status='EMPTY_GT' if not n else 'INVALID_PREDICTION' if invalid_gt else 'DEFINED')


def trace_review(arm,initial_meta,identities):
    directory=BASE/arm
    def lines(name):
        p=directory/name;raw=p.read_bytes();require(digest(raw)==identities[str(p)],'Trace SHA changed')
        return [json.loads(line) for line in raw.decode().splitlines()]
    ordinary=lines('optimization_trace.jsonl');observed=lines('gradient_depth_trace.jsonl')
    require(len(ordinary)==len(observed)==400,'Complete paired 400 traces')
    require([r['iteration'] for r in ordinary]==[r['iteration'] for r in observed]==list(range(400)),'All step indices once in order')
    names={f'im_depthmaps.{i}' for i in range(4)}|{'im_focals','pw_poses'}
    counts={name:dict(none_steps=0,present_steps=0,zero_norm_steps=0,positive_norm_steps=0) for name in sorted(names)}
    recorded_depth_change_steps=[0]*4
    per_step=[]
    for k,(a,b) in enumerate(zip(ordinary,observed)):
        require(b['actual_adam_steps']==k+1,'Recorded Adam count must follow step index')
        require(a['loss_before_step']==b['loss_before_step'] and a['lr']==b['lr'],'Ordinary/gradient trace coupling mismatch')
        require(math.isfinite(a['loss_before_step']) and math.isfinite(a['lr']),'Finite original trace')
        require(math.isclose(a['lr'],.01+(1e-6-.01)*(k/400),rel_tol=0,abs_tol=1e-15),'Original linear schedule changed')
        gs=b['gradients_from_this_step'];require(set(gs)==names,'All selected registered gradients every step')
        for name,g in gs.items():
            require(g['requires_grad']==initial_meta['parameter::'+name]['requires_grad'],'Recorded trainability changed')
            if g['grad_is_none']:
                require(g['finite'] is None and g['l2'] is None,'Absent gradient cannot have numerical norm')
                counts[name]['none_steps']+=1
            else:
                require(g['finite'] is True and math.isfinite(g['l2']) and g['l2']>=0,'Finite nonnegative recorded gradient norm')
                counts[name]['present_steps']+=1
                counts[name]['zero_norm_steps' if g['l2']==0 else 'positive_norm_steps']+=1
            if name.startswith('im_depthmaps.'):
                require(g['grad_is_none']==(arm=='original'),'Depth connectivity record contradicts arm')
        for when in ('statistics_before_step','statistics_after_step'):
            state=b[when];rows=state['frames']
            require([r['index'] for r in rows]==list(range(4)),'All frame statistics at each boundary')
            for r in rows:
                expected={'index','log_mean','log_min','log_max','depth_mean','depth_min','depth_max',
                          'log_change_mean','log_change_max_abs','depth_initial_ratio_mean'}
                require(set(r)==expected and all(math.isfinite(v) for key,v in r.items() if key!='index'),'Finite complete per-step depth statistics')
                require(r['depth_min']>0 and r['depth_initial_ratio_mean']>0 and r['log_change_max_abs']>=0,'Recorded depth statistics domain')
            require(len(state['focal'])==4 and all(len(x)==1 and math.isfinite(x[0]) and x[0]>0 for x in state['focal']),'Four focal values each step')
            require(len(state['pw_scale'])==3 and all(math.isfinite(x) and x>0 for x in state['pw_scale']),'Three edge scales each step')
        for i,r in enumerate(b['statistics_after_step']['frames']):
            recorded_depth_change_steps[i]+=int(r['log_change_max_abs']>0)
        per_step.append(dict(arm=arm,iteration=k,actual_adam_steps=b['actual_adam_steps'],
            loss_before_step=b['loss_before_step'],lr=b['lr'],
            depth_grad_present=[not gs[f'im_depthmaps.{i}']['grad_is_none'] for i in range(4)],
            depth_grad_l2=[gs[f'im_depthmaps.{i}']['l2'] for i in range(4)]))
    return dict(arm=arm,ordinary_steps=400,gradient_records=400,counts=counts,
                recorded_nonzero_cumulative_log_change_steps_per_frame=recorded_depth_change_steps,
                scope='All saved gradient records checked; no backward re-executed and no independent numerical gradient computation.'),per_step


def main(args):
    require(not (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists(),'Never overwrite/repeat a review attempt')
    require(sha(Path(__file__).resolve())==args.script_sha256,'Caller must bind reviewed numeric script SHA')
    contract_path=Path(args.contract).resolve();require(sha(contract_path)==args.sha256,'Frozen S28 contract SHA required')
    c=read(contract_path)
    require(c['status']=='FROZEN' and c['schema']=='s28-matched-gradient-only-v1','Frozen S28 pair required')
    require(c['arms']==list(ARMS) and c['frame_count']==4 and c['steps_per_arm']==400,'Exact paired common4 domain')
    require(c['output_root']==str(BASE) and c['depth_input'] is None,'Both fresh common4 have no depth input')
    ids={str(contract_path):args.sha256,str(Path(__file__).resolve()):args.script_sha256}
    # Selected execution sources only; do not repeat the large dependency inventory.
    for key in ('runner','scorer','parent_runner','parent_scorer','optimizer_source'):
        p=Path(c[key]);h=c['identities'][str(p)];require(sha(p)==h,'Execution source changed: '+key);ids[str(p)]=h
    parent=Path(c['parent_manifest']);require(sha(parent)==c['parent_manifest_sha256'],'Parent identity')
    ids[str(parent)]=c['parent_manifest_sha256']
    parent_data=read(parent)
    require(c['gt_depth_frames']==parent_data['scoring']['gt_depth_frames'][:4],'Original four scoring GT identities')
    policy=dict(prediction_shape_hw=[384,512],sensor_shape_hw=[480,640],sensor_depth_divisor=5000,
        nearest_mapping='floor((2*target_index+1)*source_size/(2*target_size))',
        gt_valid='finite_and_positive_on_target_grid',prediction_invalid='nonfinite_or_nonpositive',
        invalid_policy='any_invalid_on_valid_gt_makes_frame_absrel_rmse_null;delta1_invalid_is_failure',
        aggregation='equal_frame_mean_only_if_all_prespecified_frames_defined',gt_scale_fit=False,
        confidence_mask=False,far_depth_cut=False,delta1_threshold=1.25,delta1_comparison='strict_less_than')
    require(c['scoring_policy']==policy,'Independent arithmetic must match the frozen complete scoring policy')
    def bind_json(p,expected=None):
        raw=Path(p).read_bytes();h=digest(raw)
        if expected is not None:require(h==expected,'JSON identity mismatch: '+str(p))
        ids[str(p)]=h;return json.loads(raw)
    # Readiness checks only. No polling, archive decode or GT bytes here.
    sr=bind_json(BASE/'scoring/receipt.json')
    require(sr['status']=='PASS' and sr['s28_contract_sha256']==args.sha256 and sr['inputs_unchanged'] is True,'S28 scorer must complete first')
    require(sr['sensor_gt_images_decoded']==4 and sr['per_frame_rows']==8,'Complete existing scoring domain')
    producers={}
    for arm in ARMS:
        d=BASE/arm;r=bind_json(d/'receipt.json');producers[arm]=r
        require(r['status']=='PASS' and r['s28_contract_sha256']==args.sha256 and r['manifest_sha256']==c['parent_manifest_sha256'],'Both producers complete/bound')
        require(r['mode']==arm and r['frame_count']==4 and r['iterations']==r['adam_steps']==400 and r['clean_calls']==1,'Full 400-step producer')
        require(r['parent_identities_rechecked'] is True and r['observer']['s28_gradient_steps']==400,'Original source/observer completion')
        require(set(REQUIRED_PRODUCTS)<=set(r['outputs']),'All raw, decoded and trace products must be sealed')
    started=utc();timer=time.perf_counter();write('attempt.json',dict(status='STARTED',started_utc=started,
        contract_sha256=args.sha256,prediction_arrays_decoded=False,sensor_GT_bytes_read=False))
    try:
        scored=sr['input_sha256_before_after']
        for arm,r in producers.items():
            d=BASE/arm
            for name,h in r['outputs'].items():
                require(Path(name).name==name,'No product path traversal')
                p=d/name;require(sha(p)==h,'Full producer output identity: '+str(p));ids[str(p)]=h
                require(scored[str(p)]==h,'Same complete producer output as official scoring')
            seal=bind_json(d/'inputs_seal.json',r['inputs_seal_sha256'])
            require(seal['s28_contract_sha256']==args.sha256 and seal['manifest_sha256']==c['parent_manifest_sha256'] and seal['sensor_depth_used'] is False,'Producer input condition')
            require(ids[str(d/'receipt.json')]==scored[str(d/'receipt.json')],'Scored producer receipt changed')
        for name,h in sr['outputs'].items():
            require(Path(name).name==name,'No score path traversal');p=BASE/'scoring'/name
            require(sha(p)==h,'Scorer output changed');ids[str(p)]=h
        metrics=read(BASE/'scoring/metrics.json')
        require(metrics['s28_contract_sha256']==args.sha256 and metrics['scale_fit'] is False and metrics['confidence_mask'] is False and metrics['gt_far_cut'] is False,'Official metric policy')
        reported=metrics['per_frame'];expected={(a,i) for a in ARMS for i in range(4)}
        require(len(reported)==8 and {(r['mode'],r['index']) for r in reported}==expected,'All 8 reported frames once')
        require(set(metrics['primary_common4'])==set(ARMS),'Both group means required')
        # Also bind the complete original saved-head byte sources, without decoding them.
        require(len(c['input_heads'])==4,'Four raw source head archives')
        for i,r in enumerate(c['input_heads']):
            require(r['index']==i and sha(r['path'])==r['sha256'],'Original input head identity');ids[r['path']]=r['sha256']
        # Explicit GT byte read/hashing for ALL four occurs before ANY decoding.
        frames=c['gt_depth_frames'];require(len(frames)==4 and [r['index'] for r in frames]==list(range(4)),'Four GT identities')
        gt_bytes=[]
        write('progress.json',dict(stage='GT_BYTE_SEAL_STARTED',utc=utc(),arrays_decoded=False,sensor_depth_decoded=False))
        for r in frames:
            raw=Path(r['path']).read_bytes();h=digest(raw)
            require(h==r['sha256']==scored[r['path']],'Same previously scored GT bytes')
            ids[r['path']]=h;gt_bytes.append(raw)
        write('input_seal.json',dict(status='PASS_ALL_SAVED_AND_GT_BYTES_SEALED_BEFORE_DECODE',utc=utc(),
            s28_contract_sha256=args.sha256,identities=ids,prediction_arrays_decoded=False,
            sensor_GT_byte_images_read=4,sensor_GT_images_decoded=0,
            dependency_scope='Selected source + complete saved producer/scorer files and raw heads; no repeat dependency inventory'))
        import numpy as np
        import cv2
        require(np.__version__=='1.26.4','Expected existing NumPy 1.26.4')
        cv2.setNumThreads(1)
        write('progress.json',dict(stage='SAVED_DATA_DECODING',utc=utc(),input_seal_sha256=sha(HERE/'input_seal.json')))
        gt=[cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED) for raw in gt_bytes]
        require(all(a is not None and a.shape==(480,640) and a.dtype==np.uint16 for a in gt),'OpenCV sensor schema')
        data={};raw_initial={};meta_initial={};decoded_initial={};raw_final={};changes=[]
        final_shapes={'depth':(4,384,512),'point_cloud':(4,384,512,3),'conf':(4,384,512),'focal':(4,1),'pp':(4,2),'c2w':(4,4,4)}
        initial_shapes={k:v for k,v in final_shapes.items() if k!='conf'}
        initial_shapes.update(pw_scale=(3,),pw_poses=(3,4,4),adaptors=(3,3),objective=())
        for arm in ARMS:
            d=BASE/arm;data[arm]=load_archive(d/'output.npz',ids,final_shapes)
            raw_initial[arm]=load_archive(d/'initial_raw.npz',ids);meta_initial[arm]=read(d/'initial_raw_metadata.json')
            raw_final[arm]=load_archive(d/'final_raw_before_clean.npz',ids);mf=read(d/'final_raw_metadata.json')
            validate_raw(raw_initial[arm],meta_initial[arm],arm+'/initial');validate_raw(raw_final[arm],mf,arm+'/final')
            require(set(mf)==set(meta_initial[arm]),'Stable complete raw tensor set')
            for name in mf:
                require(all(mf[name][k]==meta_initial[arm][name][k] for k in ('shape','dtype','requires_grad')),'Stable tensor schema/flags')
            decoded_initial[arm]=load_archive(d/'initial_decoded.npz',ids,initial_shapes)
            for i in range(4):
                key=f'parameter::im_depthmaps.{i}';a=raw_initial[arm][key];b=raw_final[arm][key]
                before=decoded_initial[arm]['depth'][i];after=data[arm]['depth'][i]
                require(a.dtype==b.dtype==np.float32 and a.size==b.size==384*512,'Complete raw FP32 depth leaf')
                raw_exact=a.tobytes()==b.tobytes();depth_exact=before.tobytes()==after.tobytes()
                da=b.astype(np.float64)-a.astype(np.float64);dd=after.astype(np.float64)-before.astype(np.float64)
                require(np.isfinite(da).all() and np.isfinite(dd).all() and (before>0).all() and (after>0).all(),'Finite complete depth changes')
                changes.append(dict(arm=arm,index=i,pixels=int(before.size),registered_log_depth_bitwise_unchanged=raw_exact,
                    decoded_depth_bitwise_unchanged=depth_exact,registered_log_depth_changed_elements=int(np.count_nonzero(a!=b)),
                    decoded_depth_changed_pixels=int(np.count_nonzero(before!=after)),
                    log_change_max_abs=float(np.max(np.abs(da))),log_change_mean=float(da.mean()),
                    depth_change_max_abs_m=float(np.max(np.abs(dd))),depth_change_mean_m=float(dd.mean()),
                    final_to_initial_depth_mean_ratio=float(np.mean(after.astype(np.float64)/before.astype(np.float64)))))
                if arm=='original':require(raw_exact and depth_exact,'Original arm depth must remain bitwise unchanged from its own initialization')
        require(meta_initial['original']==meta_initial['gradient_only'],'All initial schema/flags/content SHA identical')
        raw_comparison=[]
        for key,a in raw_initial['original'].items():
            b=raw_initial['gradient_only'][key]
            same=a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes()
            require(same,'Full initial raw tensor bytes mismatch: '+key)
            raw_comparison.append(dict(name=key,shape=list(a.shape),dtype=str(a.dtype),elements=int(a.size),bitwise_equal=True,sha256=digest(a.tobytes())))
        decoded_comparison={k:decoded_initial['original'][k].tobytes()==decoded_initial['gradient_only'][k].tobytes() for k in initial_shapes}
        require(decoded_comparison['depth'] and decoded_comparison['objective'],'Same initial depth/objective bytes')
        trace_summaries=[];step_rows=[]
        for arm in ARMS:
            result,step=trace_review(arm,meta_initial[arm],ids);trace_summaries.append(result);step_rows.extend(step)
        # Fresh independent pixel arithmetic: 8 full grids, same GT valid denominator.
        rows=[];differences={}
        for arm in ARMS:
            for i in range(4):
                row=dict(mode=arm,index=i,**independent_frame(data[arm]['depth'][i],gt[i]))
                official=next(r for r in reported if r['mode']==arm and r['index']==i)
                for key in COUNT_KEYS+('metric_status',):require(row[key]==official[key],f'Count/status mismatch {arm}/{i}/{key}')
                for key in FLOAT_KEYS:metric_match(row[key],official[key],f'{arm}/{i}/{key}',differences)
                rows.append(row)
        means={};aggregate_checks=0
        for arm in ARMS:
            selected=[r for r in rows if r['mode']==arm];target=metrics['primary_common4'][arm]
            require(target['frame_indices']==list(range(4)) and target['frame_count']==4,'Full group indices')
            mean=dict(frame_indices=list(range(4)),frame_count=4)
            for key in FLOAT_KEYS:
                vals=[r[key] for r in selected];v=math.fsum(vals)/4 if all(x is not None for x in vals) else None
                metric_match(v,target[key],arm+'/mean/'+key,differences);aggregate_checks+=1
                require(target[key+'_defined_frames']==sum(x is not None for x in vals),'Defined-frame count')
                mean[key]=v
            for key in SUM_KEYS:require(target[key+'_sum_descriptive']==sum(r[key] for r in selected),'Group pixel denominator sum')
            require(target['empty_gt_frames']==[r['index'] for r in selected if r['gt_valid_pixels']==0],'Empty GT list')
            require(target['invalid_prediction_frames']==[r['index'] for r in selected if r['prediction_invalid_on_gt_pixels']>0],'Invalid prediction list')
            means[arm]=mean
        # CSV is also an official output: every prescribed scalar/count matches JSON.
        csv_rows=list(csv.DictReader((BASE/'scoring/per_frame.csv').open()))
        require(len(csv_rows)==8 and {(r['mode'],int(r['index'])) for r in csv_rows}==expected,'Complete CSV rows')
        for r in csv_rows:
            official=next(x for x in reported if x['mode']==r['mode'] and x['index']==int(r['index']))
            for key in COUNT_KEYS:require(int(r[key])==official[key],'CSV integer mismatch')
            require(r['metric_status']==official['metric_status'],'CSV status mismatch')
            for key in FLOAT_KEYS:metric_match(float(r[key]) if r[key] else None,official[key],'csv/'+key,differences)
        for p,h in ids.items():require(sha(p)==h,'Input changed during independent review: '+p)
        write('recomputed_metrics.json',dict(per_frame=rows,primary_common4=means,maximum_difference=differences,tolerance=TOL))
        write('initial_and_depth_review.json',dict(all_initial_raw_tensors_exact=True,raw_tensor_count=len(raw_comparison),
            raw_comparison=raw_comparison,initial_decoded_byte_comparison=decoded_comparison,depth_changes=changes,
            boundary='Original means this new matched A arm, compared with its own raw and decoded initial state; no historical S26 values reread. Gradient-only change is descriptive, with no required improvement.'))
        write('trace_review.json',dict(total_actual_step_records=800,arms=trace_summaries,per_step=step_rows))
        write('receipt.json',dict(status='PASS',started_utc=started,completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
            s28_contract_sha256=args.sha256,script_sha256=args.script_sha256,per_frame_rows=8,aggregate_numeric_checks=aggregate_checks,
            full_grid_pixel_visits=8*384*512,valid_GT_pixel_visits=sum(r['gt_valid_pixels'] for r in rows),
            max_metric_difference=differences,all_initial_raw_tensors_exact=True,raw_tensor_count=len(raw_comparison),
            complete_gradient_records=800,GT_images_decoded=4,inputs_unchanged=True,input_identities_before_after=ids,
            new_model_runs=0,new_GA_runs=0,new_MST_runs=0,new_backward_calls=0,
            evidence_scope='Different author, OpenCV and row-wise complete metric recomputation; full saved tensor byte checks and recorded-gradient audit, not numerical gradient replay or external replication.',
            outputs={p.name:sha(p) for p in HERE.iterdir() if p.name in ('recomputed_metrics.json','initial_and_depth_review.json','trace_review.json','input_seal.json')}))
        print(json.dumps({'status':'PASS','per_frame_rows':8,'aggregate_checks':aggregate_checks,'steps':800,'maximum_difference':differences},ensure_ascii=False))
    except BaseException as e:
        write('receipt.json',dict(status='FAILED',started_utc=started,failed_utc=utc(),error=repr(e),s28_contract_sha256=args.sha256,
            evidence_scope='Independent review failed; preserve this attempt, no automatic retry or tolerance change'))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True);p.add_argument('--script-sha256',required=True)
    main(p.parse_args())
