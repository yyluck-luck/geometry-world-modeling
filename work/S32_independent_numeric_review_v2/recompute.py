#!/usr/bin/env python3
"""Independent S32 saved-output arithmetic. Candidate preparation is not execution.

No polling, model, GA, MST, backward, original scorer imports or image display.
Root must bind completed results explicitly before this entry point can run.
"""
from __future__ import annotations
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WINDOWS=('fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2')
ENDPOINTS=('initial_0step','corrected_getter_400','global_rescaled_400')
FLOATS=('absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt')
COUNTS=('grid_pixels','gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels',
        'prediction_invalid_on_gt_pixels','delta1_success_pixels')
SUMS=COUNTS[1:5]
HELPER=ROOT/'work/S28_independent_numeric_review/recompute.py'
HELPER_SHA='2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2'
SELECTION_SHA='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
METADATA_SHA='4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6'
GRID=384*512

def utc():return datetime.now(timezone.utc).isoformat()
def require(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def unavailable(sid,endpoint,index,reason,status='UNAVAILABLE_WINDOW'):
    return dict(window_id=sid,endpoint=endpoint,index=index,row_status=status,missing_reason=reason,
        grid_pixels=GRID,**{k:None for k in COUNTS if k!='grid_pixels'},
        **{k:None for k in FLOATS},metric_status=status)

def group_of(rows):
    """Independent fixed-denominator aggregation; no call to official aggregate."""
    require(len(rows)==4 and [r['index'] for r in rows]==list(range(4)),'Fixed four-frame group')
    g=dict(frame_indices=list(range(4)),frame_count=4,
        aggregation='equal_frame_mean;no_available_frame_or_pixel_pooled_substitution')
    for key in FLOATS:
        v=[r[key] for r in rows];known=[x for x in v if x is not None]
        g[key]=math.fsum(known)/4 if len(known)==4 else None
        g[key+'_defined_frames']=len(known)
    for key in SUMS:
        v=[r[key] for r in rows];known=[x for x in v if x is not None]
        g[key+'_sum_descriptive']=sum(known) if len(known)==4 else None
        g[key+'_known_frames']=len(known);g[key+'_known_sum_descriptive']=sum(known)
    g.update(empty_gt_frames=[r['index'] for r in rows if r['gt_valid_pixels']==0],
        invalid_prediction_frames=[r['index'] for r in rows if r['prediction_invalid_on_gt_pixels'] is not None and r['prediction_invalid_on_gt_pixels']>0],
        all_four_rows_scored=all(r['row_status']=='SCORED' for r in rows),
        scored_frames=sum(r['row_status']=='SCORED' for r in rows),
        unavailable_frames=[r['index'] for r in rows if r['row_status']!='SCORED'],
        missing_reasons={str(r['index']):r['missing_reason'] for r in rows if r['row_status']!='SCORED'})
    return g

def window_mean(groups,window_ids,endpoint):
    g=dict(prespecified_window_ids=list(window_ids),prespecified_window_count=len(window_ids),
        aggregation='equal_window_mean_only_if_every_prespecified_window_metric_defined',
        unit='window; no pixel/frame independence claim')
    for key in FLOATS:
        v=[groups[sid][endpoint][key] for sid in window_ids];known=[x for x in v if x is not None]
        g[key]=math.fsum(known)/len(window_ids) if len(known)==len(window_ids) else None
        g[key+'_defined_windows']=len(known)
    return g

def compare_record(actual,reported,label,helper,differences):
    require(set(actual)==set(reported),'Complete record schema: '+label)
    for key,value in actual.items():
        if key in FLOATS:helper.metric_match(value,reported[key],label+'/'+key,differences)
        else:require(value==reported[key],'Exact record field: '+label+'/'+key)

def saved_trace_review(directory,initial_depth,final_depth,ids,helper,np,B_sha):
    """All saved records plus raw/endpoint boundary links; never recompute gradients."""
    ga=directory/'GA/C2a';producer=read(ga/'receipt.json')
    require(producer['status']=='PASS' and producer['manifest_sha256']==B_sha and producer['mode']=='C2a','Bound complete original inner GA')
    require(producer['frame_count']==4 and producer['iterations']==producer['adam_steps']==400 and producer['clean_calls']==1,'Original observed400/clean')
    observer=producer['observer']
    require(observer['s32_gradient_steps']==400 and observer['s32_alignment_calls']==1 and len(observer['pnp_calls'])==3,'Actual original source call counts')
    require(observer['s32_objective_forward_counts']==dict(optimization=400,patch_boundary_no_update=2,postfinal_no_update=1,total=403),'403 recorded objective path')
    for name,h in producer['outputs'].items():require(ids[str(ga/name)]==h,'Outer PASS seals actual inner GA output')
    initial=helper.load_archive(ga/'initial_raw.npz',ids);final=helper.load_archive(ga/'final_raw_before_clean.npz',ids)
    im=read(ga/'initial_raw_metadata.json');fm=read(ga/'final_raw_metadata.json')
    helper.validate_raw(initial,im,'initial');helper.validate_raw(final,fm,'final')
    require(len(initial)==len(final)==33 and set(initial)==set(final),'All 33 registered tensors/buffers at both boundaries')
    for key in im:require(all(im[key][field]==fm[key][field] for field in ('shape','dtype','requires_grad')),'Raw schema/flags stable')
    first=helper.load_archive(ga/'initial_decoded.npz',ids);last=helper.load_archive(ga/'output.npz',ids)
    for endpoint,expected in ((first,initial_depth),(last,final_depth)):
        require(endpoint['depth'].dtype==np.float32 and endpoint['depth'].shape==expected.shape and endpoint['depth'].tobytes()==expected.tobytes(),'Exact inner/outer endpoint depth bytes')
    gate=read(ga/'same_window_initial_gate.json')
    require(gate['status']=='PASS' and gate['contract_sha256']==B_sha and gate['window_id']==directory.name and gate['raw_count']==33 and gate['raw_and_objective_serialization_exact'] is True,'Same-window initial gate record')
    previous_base=helper.BASE
    try:
        helper.BASE=directory/'GA'  # Explicit saved-path adaptation only, no helper math change.
        summary,steps=helper.trace_review('C2a',im,ids)
    finally:helper.BASE=previous_base
    records=[json.loads(line) for line in (ga/'gradient_depth_trace.jsonl').read_text().splitlines()]
    require(records[0]['loss_before_step']==float(first['objective']),'Initial decoded objective equals first actual optimization loss')
    require(records[-1]['loss_before_step']==observer['returned_pre_last_step_loss'],'Last trace is returned pre-last-step loss, not postfinal objective')
    links=[]
    for i in range(4):
        key='parameter::im_depthmaps.'+str(i);a=initial[key];z=final[key]
        require(a.shape==z.shape==(384,512) and a.dtype==z.dtype==np.float32 and im[key]['requires_grad'] is True,'All four raw registered depth leaves')
        for values,depth in ((a,initial_depth[i]),(z,final_depth[i])):
            reference=np.exp(values.astype(np.float64)).reshape(384,512)
            require(np.allclose(reference,depth,atol=1e-6,rtol=1e-6),'All raw log-depth pixels match decoded endpoint via independent FP64 exp')
        change=z-a
        for label,raw,depth,record in (
            ('first_before',a,initial_depth[i],records[0]['statistics_before_step']['frames'][i]),
            ('last_after',z,final_depth[i],records[-1]['statistics_after_step']['frames'][i])):
            require(record['log_min']==float(raw.min()) and record['log_max']==float(raw.max()),'Exact saved log extrema '+label)
            require(record['depth_min']==float(depth.min()) and record['depth_max']==float(depth.max()),'Exact saved depth extrema '+label)
            require(math.isclose(record['log_mean'],math.fsum(raw.flat)/GRID,abs_tol=1e-5,rel_tol=1e-5),'Independent boundary log mean '+label)
            require(math.isclose(record['depth_mean'],math.fsum(depth.flat)/GRID,abs_tol=1e-5,rel_tol=1e-5),'Independent boundary depth mean '+label)
        first_row=records[0]['statistics_before_step']['frames'][i];last_row=records[-1]['statistics_after_step']['frames'][i]
        require(first_row['log_change_mean']==first_row['log_change_max_abs']==0 and first_row['depth_initial_ratio_mean']==1,'First trace unchanged initial state')
        require(last_row['log_change_max_abs']==float(np.max(np.abs(change))),'Last raw cumulative-change maximum')
        require(math.isclose(last_row['log_change_mean'],math.fsum(change.flat)/GRID,abs_tol=1e-5,rel_tol=1e-5),'Last raw cumulative-change mean')
        ratio=(final_depth[i]/initial_depth[i]).astype(np.float32)
        require(math.isclose(last_row['depth_initial_ratio_mean'],math.fsum(ratio.flat)/GRID,abs_tol=1e-5,rel_tol=1e-5),'Last trace endpoint ratio mean')
        links.append(dict(index=i,registered_initial_log_sha256=digest(a.tobytes()),registered_final_log_sha256=digest(z.tobytes()),
            raw_log_bytes_changed=a.tobytes()!=z.tobytes(),decoded_depth_bytes_changed=initial_depth[i].tobytes()!=final_depth[i].tobytes(),
            initial_and_final_full_pixel_exp_links=True,first_before_and_last_after_statistics_agree=True))
    summary.update(window_id=directory.name,boundary_links=links,raw_tensor_count_each_boundary=33,
        initial_objective=float(first['objective']),last_trace_pre_step_objective=records[-1]['loss_before_step'],
        separately_recorded_postfinal_objective=observer['postfinal_objective'],
        boundary_mean_tolerance=dict(abs_tol=1e-5,rel_tol=1e-5),raw_exp_tolerance=dict(atol=1e-6,rtol=1e-6),
        scope='Saved 400-step records and endpoint/raw consistency only; gradients were not recomputed or independently proved numerically correct')
    for r in steps:r['window_id']=directory.name
    return summary,steps

def run(binding_path,binding_sha):
    require(not (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists(),'Do not repeat or overwrite an attempt')
    require(sha(binding_path)==binding_sha,'Explicit final root binding SHA')
    b=read(binding_path);require(b['schema']=='s32-independent-numeric-binding-v1' and b['status']=='FROZEN','Unbound candidate cannot execute')
    candidate_path=HERE/'candidate.json';require(sha(candidate_path)==b['candidate_sha256'],'Reviewed candidate identity')
    c=read(candidate_path);require(c['schema']=='s32-independent-numeric-candidate-v1','Candidate schema')
    require(c['status']=='CANDIDATE_UNBOUND_DO_NOT_EXECUTE','Preserve original candidate')
    ids={str(Path(binding_path).resolve()):binding_sha,str(candidate_path):b['candidate_sha256']}
    for p,h in c['source_sha256'].items():require(sha(p)==h,'Reviewed source/metadata changed: '+p);ids[p]=h
    require(c['source_sha256'][str(Path(__file__).resolve())]==sha(__file__) and c['source_sha256'][str(HELPER)]==HELPER_SHA,'Own runner and independent helper bound')
    require(c['resource']==dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),'Fixed external budget')
    def bind_json(ref):
        p=Path(ref['path']);require(p.is_absolute() and sha(p)==ref['sha256'],'Bound JSON identity')
        ids[str(p)]=ref['sha256'];return read(p)
    # Root binds both actual execution contracts and the final completed scorer.
    ac=bind_json(c['A_contract']);require(ac['status']=='FROZEN','Frozen A source contract')
    require(b['B_contract']==c['B_contract'],'Bind the actual already frozen B contract')
    bc=bind_json(b['B_contract'])
    require(bc['status']=='FROZEN' and bc['schema']=='s32-same-window-c2a-consumer-v1','Frozen B source contract')
    require(bc['A_contract_sha256']==c['A_contract']['sha256'] and bc['selection_sha256']==SELECTION_SHA,'Same A source and B window selection')
    require(bc['steps']==400 and bc['endpoints']==list(ENDPOINTS),'Original B three-control condition')
    for p in c['B_execution_sources']:
        require(bc['identities'].get(p)==c['source_sha256'][p],'Same reviewed B execution wrapper')
    sm=bind_json(b['scoring_manifest']);sr=bind_json(b['scoring_receipt'])
    require(sm['status']=='FROZEN' and sm['schema']=='s32-complete-window-scoring-v1','Completed frozen scoring contract')
    require(sm['selection_sha256']==SELECTION_SHA and sm['metadata_selection_sha256']==METADATA_SHA,'Exact original selection')
    require(sm['selection_path']==str(ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json') and
        sm['metadata_selection_path']==str(ROOT/'work/S32_selection/selected_windows.json'),'Exact selection paths')
    require(sm['endpoints']==list(ENDPOINTS) and [w['id'] for w in sm['windows']]==list(WINDOWS),'Fixed 4x3 domain')
    require(sm['output_root']==str(ROOT/'results/S32_consumer_scoring'),'Fixed official output root')
    require(Path(b['scoring_receipt']['path'])==Path(sm['output_root'])/'receipt.json','Official scorer receipt location')
    require(sr['status']=='PASS' and sr['inputs_unchanged'] is True and sr['scoring_manifest_sha256']==b['scoring_manifest']['sha256'],'Official complete scoring first')
    require(sr['per_frame_rows']==48 and sr['endpoint_groups']==12 and sr['selection_sha256']==SELECTION_SHA,'Complete table denominator')
    for p,h in sm['control_sha256'].items():
        require(c['source_sha256'].get(p)==h and sha(p)==h,'Same reviewed scoring source');ids[p]=h
    require(sm['upstream_seal_receipts'] and b['root_seal_receipts']==sm['upstream_seal_receipts'],'Bind actual root prediction/GT ordering evidence')
    for ref in b['root_seal_receipts']:bind_json(ref)
    started=utc();timer=time.perf_counter()
    receipt=dict(status='RUNNING',started_utc=started,binding_sha256=binding_sha,
        candidate_sha256=b['candidate_sha256'],new_model=0,new_GA=0,new_MST=0,new_backward=0,
        sensor_GT_bytes_started=False,prediction_arrays_decoded=False)
    write('attempt.json',receipt)
    try:
        scored_ids=sr['input_sha256'];owners={};GT_needed=[];endpoints={}
        metadata=read(sm['metadata_selection_path']);selected={w['id']:w for w in metadata['windows']}
        require([w['id'] for w in metadata['windows']]==list(WINDOWS),'Original ordered four windows')
        # Terminal producer JSON only, before any archive or sensor-byte reads.
        for w in sm['windows']:
            sid=w['id'];ref=w['producer_receipt'];r=bind_json(ref);directory=Path(ref['path']).parent
            require(scored_ids[ref['path']]==ref['sha256'],'Official scoring used this producer receipt')
            require(r['window_id']==sid and r['selection_sha256']==SELECTION_SHA,'Whole-window identity')
            require(r['contract_sha256']==b['B_contract']['sha256'],'Actual producer uses this frozen B')
            availability=w['availability'];expected='PASS' if availability=='AVAILABLE' else 'UNAVAILABLE' if sid==WINDOWS[0] else 'FAILED'
            require(r['status']==expected,'All four producers terminal; no partial or running window')
            if sid==WINDOWS[0]:require(availability=='UNAVAILABLE_MISSING_POSE','Keep missing pose window')
            else:require(availability in ('AVAILABLE','UNAVAILABLE_PRODUCER_FAILED'),'No result-dependent eligibility')
            require(set(w['endpoints'])==set(ENDPOINTS) and len(w['frames'])==4,'Whole-window endpoint/frame schema')
            require([f['index'] for f in w['frames']]==list(range(4)),'All four original frame indices')
            owners[sid]=(directory,r)
            for f,s in zip(w['frames'],selected[sid]['frames']):
                q=s['sensor_depth_association']
                require(f['rgb_time']==s['rgb_time'] and f['depth_time']==q['time'] and f['depth_path']==q['path'],'No reassociation')
                if availability=='AVAILABLE' and q['status']=='MATCHED':
                    require(scored_ids[f['depth_path']]==f['depth_sha256'],'Exact already-scored sensor identity')
                    GT_needed.append(dict(window_id=sid,index=f['index'],path=f['depth_path'],sha256=f['depth_sha256']))
            for endpoint,item in w['endpoints'].items():
                dtype='float64' if endpoint==ENDPOINTS[2] else 'float32'
                require(item['depth_key']=='depth' and item['dtype']==dtype,'Depth key and FP32/FP32/FP64')
                if availability=='AVAILABLE':
                    p=directory/(endpoint+'.npz')
                    require(item['status']=='AVAILABLE' and item['path']==str(p) and r['outputs'][p.name]==item['sha256'],'Shared PASS endpoint')
                    endpoints[sid,endpoint]=item
                else:require(item['status']=='UNAVAILABLE' and item['path'] is None and item['sha256'] is None,'Do not read failed partial endpoints')
        # Bind ALL PASS outputs and official output files, without decoding arrays.
        for sid,(directory,r) in owners.items():
            if r['status']!='PASS':continue
            required={'decomposition.json','normalization_arrays.npz','GA/C2a/receipt.json',
                'GA/C2a/initial_raw.npz','GA/C2a/final_raw_before_clean.npz','GA/C2a/initial_raw_metadata.json',
                'GA/C2a/final_raw_metadata.json','GA/C2a/initial_decoded.npz','GA/C2a/output.npz',
                'GA/C2a/optimization_trace.jsonl','GA/C2a/gradient_depth_trace.jsonl','GA/C2a/same_window_initial_gate.json'}
            require(required<=set(r['outputs']),'Complete saved trace, raw boundary and normalization artifacts')
            for name,h in r['outputs'].items():
                p=directory/name;require(not Path(name).is_absolute() and p.resolve().is_relative_to(directory.resolve()),'No output path escape')
                require(scored_ids[str(p)]==h and sha(p)==h,'Complete producer output seal');ids[str(p)]=h
        out=Path(sm['output_root'])
        for name,h in sr['output_sha256'].items():
            require(Path(name).name==name,'Flat official scoring outputs')
            p=out/name;require(sha(p)==h,'Unchanged official scoring output');ids[str(p)]=h
        require({'metrics.json','per_frame.csv','prediction_input_seal.json','GT_byte_seal.json','GT_receipt.json'}<=set(sr['output_sha256']),'Complete official output evidence')
        pre=read(out/'prediction_input_seal.json');gs=read(out/'GT_byte_seal.json');gr=read(out/'GT_receipt.json')
        require(pre['prediction_arrays_decoded'] is False and pre['GT_bytes_read_by_this_scorer'] is False and gs['status']=='PASS' and gs['GT_images_decoded']==0,'Scorer phase evidence')
        require(datetime.fromisoformat(pre['utc'])<=datetime.fromisoformat(gs['utc'])<=datetime.fromisoformat(gr['utc'])<=datetime.fromisoformat(sr['completed_utc']),'Existing scorer seal order')
        require(len({x['path'] for x in GT_needed})==len(GT_needed),'All paired sensor identities distinct')
        require(gs['GT_sha256']=={x['path']:x['sha256'] for x in GT_needed},'Complete sensor byte seal')
        require(gr['GT_images_decoded']==sr['GT_images_decoded']==len(GT_needed),'No unavailable-window sensor decoding')
        for item in endpoints.values():require(pre['input_sha256'][item['path']]==item['sha256']==ids[item['path']],'All endpoints sealed before scorer GT')
        metrics=read(out/'metrics.json')
        require(metrics['scoring_manifest_sha256']==b['scoring_manifest']['sha256'] and metrics['selection_sha256']==SELECTION_SHA,'Metrics source identity')
        require(metrics['GT_scale_fit'] is False and metrics['confidence_mask'] is False and metrics['far_depth_cut'] is False,'Original unfit full-mask metric policy')
        expected_keys=[(sid,e,i) for sid in WINDOWS for e in ENDPOINTS for i in range(4)]
        reported=metrics['per_frame']
        require([(r['window_id'],r['endpoint'],r['index']) for r in reported]==expected_keys,'Exact complete ordered 48 rows')
        require(metrics['prespecified_windows']==4 and metrics['pose_eligible_windows']==3 and metrics['prespecified_groups']==12 and metrics['prespecified_rows']==48,'Unchanged all-window denominator')
        require(set(metrics['window_groups'])==set(WINDOWS) and all(set(v)==set(ENDPOINTS) for v in metrics['window_groups'].values()),'All 12 group records')
        require(set(metrics['endpoint_summaries'])==set(ENDPOINTS),'All three endpoint summaries')
        # ALL GT bytes re-sealed before ANY arrays or PNG decoding in this review.
        receipt.update(sensor_GT_bytes_started=bool(GT_needed),sensor_GT_byte_start_utc=utc());write('progress.json',receipt)
        gtbytes={}
        for f in GT_needed:
            raw=Path(f['path']).read_bytes();require(digest(raw)==f['sha256'],'Same previously scored sensor bytes')
            ids[f['path']]=f['sha256'];gtbytes[f['window_id'],f['index']]=raw
        write('input_seal.json',dict(status='PASS_ALL_SAVED_OUTPUT_AND_GT_BYTES_SEALED_BEFORE_ANY_DECODE',utc=utc(),identities=ids,
            prediction_arrays_decoded=False,sensor_GT_images_decoded=0,sensor_GT_images_hashed=len(gtbytes),
            root_ordering_evidence=[dict(path=r['path'],sha256=r['sha256']) for r in b['root_seal_receipts']],
            history_note='Reverification of completed sealed data; no new blindness claim. Root historical seal content is bound, not invented.',
            dependency_scope='Selected reviewed source and complete producer/scorer outputs; no repeated full environment inventory'))
        for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
        import numpy as np
        import cv2
        require(np.__version__=='1.26.4','Existing NumPy 1.26.4');cv2.setNumThreads(1)
        spec=importlib.util.spec_from_file_location('s32_independent_s28_arithmetic',HELPER)
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        receipt.update(prediction_arrays_decoded=True,array_decode_start_utc=utc());write('progress.json',receipt)
        arrays={}
        for key,item in endpoints.items():
            raw=Path(item['path']).read_bytes();require(digest(raw)==ids[item['path']],'Archive changed after seal')
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:
                require(len(z.files)==len(set(z.files)) and 'depth' in z.files,'Unique archive depth member')
                a=z['depth'].copy()
            require(a.shape==(4,384,512) and str(a.dtype)==item['dtype'],'Complete endpoint depth shape/dtype');arrays[key]=a
        scales={};trace_summaries={};trace_steps=[]
        for sid in WINDOWS:
            if (sid,ENDPOINTS[0]) not in arrays:continue
            initial,final,scaled=[arrays[sid,e] for e in ENDPOINTS]
            require(all(np.isfinite(x).all() and (x>0).all() for x in (initial,final,scaled)),'All scale pixels finite positive; no subset filtering')
            n=initial.size
            # Different algebra: scalar log(ratio) + compensated scalar summation.
            v=np.fromiter((math.log(float(y)/float(x)) for x,y in zip(initial.flat,final.flat)),dtype=np.float64,count=n).reshape(initial.shape)
            mu=math.fsum(v.flat)/n
            k=math.exp(-mu);reference=final.astype(np.float64)*k
            delta=np.abs(reference-scaled)
            require(np.all(delta<=1e-12+1e-12*np.abs(reference)),'Every scaled pixel matches the independent no-GT global k')
            directory,producer=owners[sid]
            meta=read(directory/'decomposition.json')
            require(meta['frame_count']==4 and meta['grid_shape']==[4,384,512] and meta['total_pixels']==n and
                meta['all_pixels_retained'] is True and meta['invalid_initial_pixels']==meta['invalid_final_pixels']==0,'Saved normalization full domain')
            for key,value in [('mu',mu),('k',k),('geometric_mean_final_to_initial',math.exp(mu))]:
                require(math.isclose(meta[key],value,abs_tol=1e-12,rel_tol=1e-12),'Independent normalization metadata scalar '+key)
            require(math.isclose(producer['normalization']['k'],k,abs_tol=1e-12,rel_tol=1e-12),'Producer receipt same k')
            ap=directory/'normalization_arrays.npz';raw=ap.read_bytes();require(digest(raw)==ids[str(ap)],'Normalization archive seal')
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:
                require(len(z.files)==len(set(z.files)) and set(z.files)=={'depth','log_change','frame_mean_log_change','mu','k'},'Complete saved normalization array schema')
                reference_values={'depth':scaled,'log_change':v,'frame_mean_log_change':np.asarray([math.fsum(q.flat)/GRID for q in v]),
                    'mu':np.asarray(mu),'k':np.asarray(k)}
                for key,value in reference_values.items():
                    actual=z[key]
                    require(actual.dtype==np.float64 and actual.shape==value.shape,'Normalization array dtype/shape '+key)
                    require(np.allclose(actual,value,atol=1e-12,rtol=1e-12),'Every normalization array element '+key)
            scales[sid]=dict(scale_pixels=n,mu_log_final_over_initial=mu,k=k,
                saved_scaled_max_abs_difference=float(delta.max()),saved_scaled_all_pixels_agree=True,
                input_dtype='float32',scaled_dtype='float64',GT_used_for_k=False,
                formula='exp(-fsum(math.log(float(final)/float(initial)))/all_pixels)',
                saved_log_change_and_frame_mean_all_elements_agree=True,
                decomposition_scope='Domain, mu, k and geometric-mean scalars checked; component SS/RMS shares are outside this scale-and-depth-metric review',
                interpretation='Ordinary saved-depth normalization only; no camera, point-cloud, or optimizer gauge repair')
            trace_summaries[sid],steps=saved_trace_review(directory,initial,final,ids,helper,np,b['B_contract']['sha256'])
            trace_steps.extend(steps)
        gt={}
        for key,raw in gtbytes.items():
            a=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED)
            require(a is not None and a.dtype==np.uint16 and a.shape==(480,640),'Original integer sensor PNG schema');gt[key]=a
        rows=[];groups={};differences={}
        for w in sm['windows']:
            sid=w['id'];groups[sid]={}
            for endpoint in ENDPOINTS:
                subset=[]
                for i in range(4):
                    if w['availability']!='AVAILABLE':row=unavailable(sid,endpoint,i,w['reason'])
                    elif (sid,i) not in gt:row=unavailable(sid,endpoint,i,'No frozen sensor-depth association; no replacement','MISSING_SENSOR_ASSOCIATION')
                    else:row=dict(window_id=sid,endpoint=endpoint,index=i,row_status='SCORED',missing_reason=None,
                        **helper.independent_frame(arrays[sid,endpoint][i],gt[sid,i]))
                    compare_record(row,reported[len(rows)],sid+'/'+endpoint+'/'+str(i),helper,differences)
                    rows.append(row);subset.append(row)
                groups[sid][endpoint]=group_of(subset)
                compare_record(groups[sid][endpoint],metrics['window_groups'][sid][endpoint],sid+'/'+endpoint+'/group',helper,differences)
        summaries={}
        for endpoint in ENDPOINTS:
            summaries[endpoint]={}
            require(set(metrics['endpoint_summaries'][endpoint])=={'all_four_prespecified','three_preselected_pose_eligible'},'Both fixed window summary domains')
            for label,domain in (('all_four_prespecified',WINDOWS),('three_preselected_pose_eligible',WINDOWS[1:])):
                g=window_mean(groups,domain,endpoint);summaries[endpoint][label]=g
                compare_record(g,metrics['endpoint_summaries'][endpoint][label],endpoint+'/'+label,helper,differences)
        with (out/'per_frame.csv').open(newline='') as f:csv_rows=list(csv.DictReader(f))
        require(len(csv_rows)==48,'Complete CSV denominator')
        for row,raw in zip(rows,csv_rows):
            require(set(row)==set(raw),'CSV full schema')
            for key,value in row.items():
                if key in FLOATS:helper.metric_match(value,None if raw[key]=='' else float(raw[key]),'csv/'+key,differences)
                elif value is None:require(raw[key]=='','CSV unknown count or reason remains blank')
                elif isinstance(value,int):require(int(raw[key])==value,'CSV exact integer')
                else:require(raw[key]==value,'CSV exact text')
        scored=sum(r['row_status']=='SCORED' for r in rows);available=len(scales)
        require(scored==3*len(gt) and metrics['scored_rows']==scored and metrics['unavailable_rows']==48-scored,'Complete actual and NA counts')
        require(sr['available_windows']==available and sr['available_endpoints']==3*available,'Actual availability count')
        require(all(r['row_status']=='UNAVAILABLE_WINDOW' for r in rows[:12]),'Preserve all 12 missing-pose NA rows')
        require(all(summaries[e]['all_four_prespecified'][k] is None for e in ENDPOINTS for k in FLOATS),'No available-case four-window mean')
        for p,h in ids.items():require(sha(p)==h,'Bound input changed during independent review')
        write('recomputed.json',dict(per_frame=rows,window_groups=groups,endpoint_summaries=summaries,scale_checks=scales,
            trace_reviews=trace_summaries,complete_saved_step_records=trace_steps,
            metric_max_absolute_difference=differences,all_rows=48,scored_rows=scored,NA_rows=48-scored,
            all_groups=12,available_groups=available*3,GT_images_decoded=len(gt),scale_pixels=sum(x['scale_pixels'] for x in scales.values())))
        receipt.update(status='PASS_INDEPENDENT_SAVED_NUMERIC_REVIEW',completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
            all_rows=48,scored_rows=scored,NA_rows=48-scored,all_groups=12,available_groups=available*3,
            sensor_GT_images_decoded=len(gt),scale_pixels=sum(x['scale_pixels'] for x in scales.values()),
            complete_saved_optimization_steps=len(trace_steps),complete_saved_gradient_records=len(trace_steps),
            input_unchanged=True,input_sha256=ids,metric_max_absolute_difference=differences,
            numerical_scope='Complete saved-depth metrics, all-pixel k and saved trace/raw-boundary audit. No recomputed GA, gradient, model or physical reconstruction validation.',
            status_meaning='Arithmetic matches complete official table; not proof of improvement, independent samples or novelty',
            output_sha256={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name in ('attempt.json','progress.json','input_seal.json','recomputed.json')})
        write('receipt.json',receipt);print(json.dumps(dict(status=receipt['status'],scored_rows=scored,NA_rows=48-scored)))
    except BaseException as exc:
        receipt.update(status='FAILED',failed_utc=utc(),error=repr(exc));write('receipt.json',receipt);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--binding',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();run(Path(args.binding).resolve(),args.sha256)
