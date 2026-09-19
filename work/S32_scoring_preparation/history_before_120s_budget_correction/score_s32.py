#!/usr/bin/env python3
"""S32 complete 4-window/3-endpoint table, including explicit missing rows.
No model, GA, RGB or optimization imports; uses frozen original depth metrics.
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
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ENDPOINTS=('initial_0step','corrected_getter_400','global_rescaled_400')
WINDOWS=('fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2')
FLOAT_KEYS=('absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt')
COUNTS=('gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels','prediction_invalid_on_gt_pixels','delta1_success_pixels')
SUM_KEYS=('gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels','prediction_invalid_on_gt_pixels')
ORIGINAL=ROOT/'scripts/score_s26b_consumer.py'
ORIGINAL_SHA='02317889281583ae0fd8a12a1148811c9e9a0afb7bcf75275aea9fd1a34f5cc7'
METADATA_SELECTION=ROOT/'work/S32_selection/selected_windows.json'
METADATA_SELECTION_SHA='4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6'
SELECTION=ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json'
SELECTION_SHA='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def require(ok,why):
    if not ok:raise ValueError(why)

def empty_row(window,endpoint,index,reason,status):
    return dict(window_id=window,endpoint=endpoint,index=index,row_status=status,missing_reason=reason,
        grid_pixels=384*512,**{k:None for k in COUNTS},**{k:None for k in FLOAT_KEYS},metric_status=status)

def aggregate_group(rows,original):
    """Original complete-frame math; explicit unknown counts for missing rows."""
    require([r['index'] for r in rows]==list(range(4)),'All four prespecified rows in order')
    complete=all(r['row_status']=='SCORED' for r in rows)
    if complete:
        group=original.aggregate(rows,list(range(4)))
    else:
        group=dict(frame_indices=list(range(4)),frame_count=4,
            aggregation='equal_frame_mean;no_available_frame_or_pixel_pooled_substitution')
        for key in FLOAT_KEYS:
            values=[r[key] for r in rows]
            group[key]=math.fsum(values)/4 if all(v is not None for v in values) else None
            group[key+'_defined_frames']=sum(v is not None for v in values)
        for key in SUM_KEYS:
            values=[r[key] for r in rows]
            group[key+'_sum_descriptive']=sum(values) if all(v is not None for v in values) else None
        group['empty_gt_frames']=[r['index'] for r in rows if r['gt_valid_pixels']==0]
        group['invalid_prediction_frames']=[r['index'] for r in rows if r['prediction_invalid_on_gt_pixels'] is not None and r['prediction_invalid_on_gt_pixels']>0]
    group.update(all_four_rows_scored=complete,scored_frames=sum(r['row_status']=='SCORED' for r in rows),
        unavailable_frames=[r['index'] for r in rows if r['row_status']!='SCORED'],
        missing_reasons={str(r['index']):r['missing_reason'] for r in rows if r['row_status']!='SCORED'})
    for key in SUM_KEYS:
        group[key+'_known_frames']=sum(r[key] is not None for r in rows)
        group[key+'_known_sum_descriptive']=sum(r[key] for r in rows if r[key] is not None)
    return group

def window_summary(groups,window_ids):
    result=dict(prespecified_window_ids=list(window_ids),prespecified_window_count=len(window_ids),
        aggregation='equal_window_mean_only_if_every_prespecified_window_metric_defined',unit='window; no pixel/frame independence claim')
    for key in FLOAT_KEYS:
        values=[g[key] for g in groups]
        result[key]=math.fsum(values)/len(window_ids) if all(v is not None for v in values) else None
        result[key+'_defined_windows']=sum(v is not None for v in values)
    return result

def run(path,expected_sha):
    require(sha(path)==expected_sha,'Explicit frozen scoring manifest SHA')
    c=read(path);require(c['status']=='FROZEN' and c['schema']=='s32-complete-window-scoring-v1','Candidate cannot run')
    require(c['selection_path']==str(SELECTION) and c['selection_sha256']==SELECTION_SHA==sha(SELECTION),'Fixed selection identity')
    require(c['metadata_selection_path']==str(METADATA_SELECTION) and c['metadata_selection_sha256']==METADATA_SELECTION_SHA==sha(METADATA_SELECTION),'Original result-independent metadata selection')
    require(c['endpoints']==list(ENDPOINTS) and [w['id'] for w in c['windows']]==list(WINDOWS),'Complete ordered 4x3 domain')
    require(c['output_root']==str(ROOT/'results/S32_consumer_scoring'),'Fixed scoring output directory')
    require(c['resource']==dict(cpu_threads=1,wall_seconds=180,rss_bytes=2*1024**3),'Fixed caller budget')
    required_controls={str(Path(__file__).resolve()),str(HERE/'protocol.md'),str(ORIGINAL)}
    require(required_controls<=set(c['control_sha256']) and c['control_sha256'][str(ORIGINAL)]==ORIGINAL_SHA,'Original unchanged metric implementation')
    out=Path(c['output_root']);require(not out.exists(),'Never repeat or overwrite scoring');out.mkdir()
    receipt=dict(status='RUNNING',started_utc=utc(),scoring_manifest_sha256=expected_sha,selection_sha256=SELECTION_SHA,
        GT_bytes_started_by_this_scorer=False,new_models=0,new_GA=0,new_MST=0,new_backward=0)
    write(out/'receipt.json',receipt)
    try:
        ids={str(Path(path).resolve()):expected_sha,str(SELECTION):SELECTION_SHA,str(METADATA_SELECTION):METADATA_SELECTION_SHA}
        for p,h in c['control_sha256'].items():require(sha(p)==h,'Changed scoring control');ids[p]=h
        selection=read(SELECTION);metadata=read(METADATA_SELECTION)
        require(selection['parent_selection_sha256']==METADATA_SELECTION_SHA,'RGB seal derives from fixed selection')
        selected={w['id']:w for w in metadata['windows']}
        require([w['id'] for w in selection['windows']]==list(WINDOWS),'Frozen RGB selection window order')
        for w in selection['windows']:
            require(w['source_RGB_indices']==selected[w['id']]['source_RGB_indices'],'RGB sealing never changes window indices')
            require(all(all(a[k]==b[k] for k in ('index','source_rgb_index','path','rgb_time','gt_time','sensor_depth_association'))
                        for a,b in zip(w['frames'],selected[w['id']]['frames'])),'RGB sealing preserves frame/GT association metadata')
        eligible=[w for w in WINDOWS if not selected[w]['required_input_issues']]
        require(eligible==['fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2'],'Fixed three pose-eligible windows')
        owners={};declared_arrays={};GT_needed=[]
        # All available/failed window receipts are terminal before any array/GT bytes.
        for w in c['windows']:
            sid=w['id'];source=selected[sid]
            require(len(w['frames'])==4 and [f['index'] for f in w['frames']]==list(range(4)),'All fixed frame metadata')
            for f,s in zip(w['frames'],source['frames']):
                sensor=s['sensor_depth_association']
                require(f['rgb_time']==s['rgb_time'] and f['depth_path']==sensor['path'] and f['depth_time']==sensor['time'],'No GT or frame reassociation')
            require(set(w['endpoints'])==set(ENDPOINTS),'Every endpoint declared')
            availability=w['availability']
            if sid=='fr2_desk_j1':
                require(availability=='UNAVAILABLE_MISSING_POSE'
                        and all(f['gt_time'] is None for f in source['frames']),'Keep fixed missing-pose window; no substitute')
            else:
                require(availability in ('AVAILABLE','UNAVAILABLE_PRODUCER_FAILED'),'No pending/running window can be finalized as NA')
            ref=w['producer_receipt'];rp=Path(ref['path'])
            require(sha(rp)==ref['sha256'],'All four terminal producer receipt identities');ids[str(rp)]=ref['sha256'];r=read(rp)
            require(r['window_id']==sid and r['selection_sha256']==SELECTION_SHA,'Producer binds same window/RGB-sealed selection')
            expected_status='PASS' if availability=='AVAILABLE' else 'UNAVAILABLE' if availability=='UNAVAILABLE_MISSING_POSE' else 'FAILED'
            require(r['status']==expected_status,'Whole-window PASS, recorded FAILED, or fixed missing-pose UNAVAILABLE')
            owners[sid]=(rp.parent,r)
            require(isinstance(w['reason'],str) and (availability=='AVAILABLE' or bool(w['reason'])),'Explain every unavailable window')
            for endpoint in ENDPOINTS:
                item=w['endpoints'][endpoint];dtype='float64' if endpoint=='global_rescaled_400' else 'float32'
                require(item['depth_key']=='depth' and item['dtype']==dtype,'Exact endpoint dtype/key; never downcast FP64')
                if availability=='AVAILABLE':
                    require(item['status']=='AVAILABLE','Shared PASS makes all three endpoints available')
                    directory,r=owners[sid];ap=Path(item['path'])
                    require(ap.is_absolute() and ap.name==endpoint+'.npz' and ap.resolve().is_relative_to(directory.resolve()),'Exact endpoint filename belongs to its producer')
                    rel=str(ap.relative_to(directory));require(r['outputs'][rel]==item['sha256'],'Producer seals this exact endpoint')
                    declared_arrays[sid,endpoint]=item
                else:
                    require(item['status']=='UNAVAILABLE' and item['path'] is None and item['sha256'] is None,'Never score failed-window partial arrays')
            if availability=='AVAILABLE':
                for f,s in zip(w['frames'],source['frames']):
                    if s['sensor_depth_association']['status']=='MATCHED':
                        require(isinstance(f['depth_sha256'],str) and len(f['depth_sha256'])==64,'Root must bind actual GT bytes after all endpoints seal')
                        GT_needed.append(dict(window_id=sid,index=f['index'],rgb_time=f['rgb_time'],depth_time=f['depth_time'],path=f['depth_path'],sha256=f['depth_sha256']))
                    else:require(f['depth_sha256'] is None,'Unmatched sensor has no invented identity')
        # Bind every output of each PASS producer; failed half-products remain unread.
        for sid,(directory,r) in owners.items():
            if r['status']!='PASS':continue
            for name,h in r['outputs'].items():
                p=directory/name;require(not Path(name).is_absolute() and p.resolve().is_relative_to(directory.resolve()),'No product path escape')
                require(sha(p)==h,'Every complete producer output unchanged');ids[str(p)]=h
        for item in declared_arrays.values():require(ids[item['path']]==item['sha256'],'All endpoint archives sealed')
        for ref in c['upstream_seal_receipts']:
            require(sha(ref['path'])==ref['sha256'],'Root upstream boundary receipt changed');ids[ref['path']]=ref['sha256']
        write(out/'prediction_input_seal.json',dict(status='PASS_ALL_AVAILABLE_ENDPOINTS_SEALED_BEFORE_THIS_SCORER_GT_READ',utc=utc(),
            input_sha256=ids,available_window_ids=[w['id'] for w in c['windows'] if w['availability']=='AVAILABLE'],
            available_endpoint_count=len(declared_arrays),prespecified_endpoint_groups=12,prediction_arrays_decoded=False,
            GT_bytes_read_by_this_scorer=False,prior_global_GT_byte_exposure='Root froze GT SHA after endpoint sealing; historical exposure remains recorded in selection'))
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
        import numpy as np
        require(np.__version__=='1.26.4','Existing NumPy version')
        spec=importlib.util.spec_from_file_location('s32_original_depth_metrics',ORIGINAL)
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        arrays={};schemas={}
        for (sid,endpoint),item in declared_arrays.items():
            raw=Path(item['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==ids[item['path']],'Archive changed after seal')
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:
                require(len(z.files)==len(set(z.files)) and 'depth' in z.files,'Unique numeric archive depth')
                a=z['depth'].copy()
            require(a.shape==(4,384,512) and str(a.dtype)==item['dtype'],'Full endpoint array shape/dtype')
            arrays[sid,endpoint]=a;schemas[sid+'/'+endpoint]=dict(shape=list(a.shape),dtype=str(a.dtype),nonfinite_count=int((~np.isfinite(a)).sum()),nonpositive_finite_count=int((np.isfinite(a)&(a<=0)).sum()))
        write(out/'prediction_schema.json',schemas)
        # Distinct fixed windows and original 1:1 association must give unique GT files.
        require(len({r['path'] for r in GT_needed})==len(GT_needed),'One GT image per prescribed available frame; no duplicates')
        receipt.update(GT_bytes_started_by_this_scorer=bool(GT_needed),GT_byte_read_start_utc=utc());write(out/'receipt.json',receipt)
        for frame in GT_needed:
            require(sha(frame['path'])==frame['sha256'],'Scoring-only GT identity');ids[frame['path']]=frame['sha256']
        write(out/'GT_byte_seal.json',dict(status='PASS',utc=utc(),GT_sha256={r['path']:r['sha256'] for r in GT_needed},GT_images_decoded=0))
        depths,records,gtids=original.load_sensor_depths(GT_needed)
        require(all(ids[p]==h for p,h in gtids.items()),'Original loader used the same sealed GT')
        gt={(r['window_id'],r['index']):depth for r,depth in zip(GT_needed,depths)}
        write(out/'GT_receipt.json',dict(utc=utc(),files=records,GT_images_decoded=len(depths),reuse='Each available frame decoded once and reused by all three endpoints',
            byte_read_note='This scorer pre-hashes each GT then the unchanged loader reads it again; root/history may already have read bytes'))
        rows=[];groups={}
        for w in c['windows']:
            sid=w['id'];groups[sid]={}
            for endpoint in ENDPOINTS:
                subset=[]
                for index in range(4):
                    if w['availability']!='AVAILABLE':row=empty_row(sid,endpoint,index,w['reason'],'UNAVAILABLE_WINDOW')
                    elif (sid,index) not in gt:row=empty_row(sid,endpoint,index,'No frozen sensor-depth association; no replacement','MISSING_SENSOR_ASSOCIATION')
                    else:row=dict(window_id=sid,endpoint=endpoint,index=index,row_status='SCORED',missing_reason=None,
                        **original.depth_metrics(arrays[sid,endpoint][index],gt[sid,index]))
                    subset.append(row);rows.append(row)
                groups[sid][endpoint]=aggregate_group(subset,original)
        require(len(rows)==48 and len({(r['window_id'],r['endpoint'],r['index']) for r in rows})==48,'Complete fixed 48-row table')
        summaries={endpoint:dict(all_four_prespecified=window_summary([groups[sid][endpoint] for sid in WINDOWS],WINDOWS),
            three_preselected_pose_eligible=window_summary([groups[sid][endpoint] for sid in eligible],eligible)) for endpoint in ENDPOINTS}
        with (out/'per_frame.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        write(out/'metrics.json',dict(scoring_manifest_sha256=expected_sha,selection_sha256=SELECTION_SHA,per_frame=rows,window_groups=groups,endpoint_summaries=summaries,
            prespecified_windows=4,pose_eligible_windows=3,prespecified_groups=12,prespecified_rows=48,
            scored_rows=sum(r['row_status']=='SCORED' for r in rows),unavailable_rows=sum(r['row_status']!='SCORED' for r in rows),
            GT_scale_fit=False,confidence_mask=False,far_depth_cut=False,
            evidence_scope='First-four-frame consumer controls, previously exposed scenes. Missing windows remain in the denominator; no frame/pixel significance or full old4-to-new4/generated-video claim'))
        for p,h in ids.items():require(sha(p)==h,'Input changed during scoring')
        receipt.update(status='PASS',completed_utc=utc(),per_frame_rows=48,endpoint_groups=12,prespecified_windows=4,pose_eligible_windows=3,
            available_windows=len(declared_arrays)//3,available_endpoints=len(declared_arrays),GT_images_decoded=len(depths),inputs_unchanged=True,input_sha256=ids,
            output_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'},
            status_meaning='Scoring/table construction completed; does not mean every producer or metric succeeded')
        write(out/'receipt.json',receipt);print(json.dumps(dict(status='PASS_TABLE',rows=48,groups=12,GT_images_decoded=len(depths))))
    except BaseException as exc:
        receipt.update(status='FAILED',failed_utc=utc(),error=repr(exc),failure_policy='Preserve partial scoring; do not silently turn hash/schema violations into scientific NA or retry')
        write(out/'receipt.json',receipt);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();run(Path(args.manifest).resolve(),args.sha256)
