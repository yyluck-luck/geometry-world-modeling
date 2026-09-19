#!/usr/bin/env python3
"""S33 saved-result review: 12 new depth rows, 48 imported rows, saved traces.

No model/MST/GA/backward, no new k or SS/RMS, no polling. Root must bind PASS
results explicitly. All selected archives and GT bytes are sealed before decode.
"""
from __future__ import annotations
import argparse,ast,copy,csv,hashlib,importlib.util,io,json,math,os,time
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WINDOWS=('fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2')
OLD_ENDS=('initial_0step','corrected_getter_400','global_rescaled_400')
NEW='common_pair_scale_400'
S32=ROOT/'results/S32_consumer_scoring'
S33=ROOT/'results/S33_pair_scale_control'
SCORING=ROOT/'results/S33_pair_scale_scoring'
H28=ROOT/'work/S28_independent_numeric_review/recompute.py'
H32=ROOT/'work/S32_independent_numeric_review_v2/recompute.py'
S33_CONTRACT=ROOT/'work/S33_preparation/contract.json'
S33_SHA='44a817a74afe10a16b758cc8fa6f7a17781d34d41ac575dd24e73b1ac1101400'
SELSHA='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
FLOATS=('absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt')

def utc():return datetime.now(timezone.utc).isoformat()
def require(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(x).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(name,x):(HERE/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def module(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def near(a,b,label):require(math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,abs_tol=1e-5,rel_tol=1e-5),'Scale trace arithmetic: '+label)

def trace_function(h32):
    """Only the named initial-gate file and its two renamed fields differ."""
    nodes=[n for n in ast.parse(H32.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='saved_trace_review']
    require(len(nodes)==1,'Exactly one frozen saved-trace function');node=copy.deepcopy(nodes[0])
    names={'same_window_initial_gate.json':'s33_initial_gate.json','raw_count':'initial_raw_count','raw_and_objective_serialization_exact':'raw_bytes_exact'}
    counts=dict.fromkeys(names,0)
    for n in ast.walk(node):
        if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in names:
            old=n.value;n.value=names[old];counts[old]+=1
    require(all(n==1 for n in counts.values()),'Only three exact saved-gate schema replacements')
    ast.fix_missing_locations(node);ns=dict(vars(h32));exec(compile(ast.Module(body=[node],type_ignores=[]),str(HERE/'recompute.py')+'::saved_trace','exec'),ns)
    return ns['saved_trace_review']

def review_window(wid,depth,pc,ids,h28,h32,np,review_trace):
    d=S33/wid;ga=d/'GA/C2a';ref=pc['references'][wid];prior=Path(ref['receipt']).parent
    initial=h28.load_archive(ga/'initial_raw.npz',ids);final=h28.load_archive(ga/'final_raw_before_clean.npz',ids)
    prior_raw=h28.load_archive(prior/'GA/C2a/initial_raw.npz',ids)
    meta=read(ga/'initial_raw_metadata.json');prior_meta=read(prior/'GA/C2a/initial_raw_metadata.json')
    require(meta==prior_meta and len(initial)==len(prior_raw)==33 and set(initial)==set(prior_raw),'Complete same-S32 initial raw metadata')
    for key in initial:
        a,b=initial[key],prior_raw[key];require(a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes(),'All same-S32 raw bytes: '+key)
    decoded=h28.load_archive(ga/'initial_decoded.npz',ids);old_decoded=h28.load_archive(prior/'GA/C2a/initial_decoded.npz',ids)
    require(set(decoded)==set(old_decoded),'Complete initial decoded fields')
    for key,a in decoded.items():
        b=old_decoded[key];require(a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes(),'All initial decoded/objective bytes: '+key)
    current_align=h28.load_archive(ga/'controlled_alignment.npz',ids);old_align=h28.load_archive(prior/'GA/C2a/controlled_alignment.npz',ids)
    require(set(current_align)==set(old_align),'Complete alignment fields')
    for key,a in current_align.items():
        b=old_align[key];require(a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes(),'All initial alignment bytes: '+key)
    gate=read(ga/'s33_initial_gate.json');pr=read(ga/'receipt.json');constraint=pr['observer']['s33_scale_constraint']
    require(all(gate[k] is True for k in ('raw_bytes_exact','decoded_exact','objective_exact','alignment_exact','initial_factor_exact_one')),'Actual S33 initial identity gate')
    require(gate['source_receipt_sha256']==ref['receipt_sha256'] and constraint['current_mean_detached'] is False and constraint['norm_pw_scale'] is False,'Source-bound factor condition')
    summary,gradient_records=review_trace(d,decoded['depth'],depth,ids,h28,np,S33_SHA)
    rows=[json.loads(line) for line in (ga/'s33_scale_trace.jsonl').read_text().splitlines()]
    require(len(rows)==400 and [r['iteration'] for r in rows]==list(range(400)),'All400 new scale records')
    target=constraint['initial_mean_log_scale'];require(math.isfinite(target),'Finite fixed initial target')
    raw_key='parameter::pw_poses'
    require(initial[raw_key].shape==final[raw_key].shape==(3,8),'Three original eight-column pair parameters')
    near(target,math.fsum(float(x) for x in initial[raw_key][:,-1])/3,'initial m0 from raw leaves')
    maximum_mean_error=0.;maximum_factor_error=0.;maximum_product_error=0.
    for i,row in enumerate(rows):
        require(row['actual_adam_steps']==i+1==gradient_records[i]['actual_adam_steps'],'Same actual Adam step in both traces')
        for when in ('before','after'):
            z=row[when]
            require(z['fixed_initial_log_mean']==target and z['full_3x4_exact'] is True,'Fixed target/recorded original3x4 check')
            raw=z['raw_scales'];effective=z['effective_scales'];factor=z['factor']
            require(len(raw)==len(effective)==3 and all(math.isfinite(x) and x>0 for x in raw+effective+[factor]),'Three positive finite scales/factor')
            rawmean=math.fsum(math.log(x) for x in raw)/3;mean=math.fsum(math.log(x) for x in effective)/3
            near(z['raw_log_mean'],rawmean,'all-step raw mean');near(z['effective_log_mean'],mean,'all-step effective mean')
            require(abs(mean-target)<=1e-5,'Independent effective mean constraint, every step boundary')
            expected_factor=math.exp(target-z['raw_log_mean']);near(factor,expected_factor,'all-step current factor')
            maximum_mean_error=max(maximum_mean_error,abs(mean-target));maximum_factor_error=max(maximum_factor_error,abs(factor-expected_factor))
            for j in range(3):
                near(effective[j],raw[j]*factor,'full-step scale product');near(effective[j]/effective[0],raw[j]/raw[0],'relative-scale ratio')
                maximum_product_error=max(maximum_product_error,abs(effective[j]-raw[j]*factor))
            require(math.isfinite(z['relative_ratios_max_abs']) and z['relative_ratios_max_abs']>=0,'Recorded finite ratio diagnostic')
    require(rows[0]['before']['factor']==1.0 and gate['scale_constraint']==rows[0]['before'],'Exact unchanged first effective scale state')
    require(constraint['trace_rows']==400 and constraint['final']==rows[-1]['after'],'Full final trace receipt identity')
    for raw_values,z,label in ((initial[raw_key][:,-1],rows[0]['before'],'initial'),(final[raw_key][:,-1],rows[-1]['after'],'final')):
        near(math.fsum(float(x) for x in raw_values)/3,z['raw_log_mean'],label+' raw parameter mean')
        for x,y in zip(raw_values,z['raw_scales']):near(math.exp(float(x)),y,label+' raw parameter exp')
    initial_depth=decoded['depth'];require(initial_depth.shape==depth.shape==(4,384,512),'Complete common-depth-change domain')
    require(np.isfinite(initial_depth).all() and np.isfinite(depth).all() and (initial_depth>0).all() and (depth>0).all(),'No filtered depth-log-change subset')
    mu=math.fsum(math.log(float(y)/float(x)) for x,y in zip(initial_depth.flat,depth.flat))/depth.size
    old_decomposition=read(prior/'decomposition.json')
    require(old_decomposition['all_pixels_retained'] is True and old_decomposition['total_pixels']==depth.size and math.isfinite(old_decomposition['mu']),'Sealed old full-pixel mu')
    old_mu=old_decomposition['mu']
    summary.update(scale_trace_records=400,scale_boundaries_checked=800,matched_S32_initial_raw_tensors=33,
        matched_S32_decoded_fields=list(decoded),matched_S32_alignment_fields=list(current_align),
        independent_scale_mean_max_abs_error=maximum_mean_error,independent_factor_max_abs_error=maximum_factor_error,
        independent_effective_product_max_abs_error=maximum_product_error,
        depth_log_change=dict(pixel_count=int(depth.size),new_mu=mu,S32_free400_mu=old_mu,
            abs_new_mu=abs(mu),abs_S32_free400_mu=abs(old_mu),absolute_common_shift_reduced=abs(mu)<abs(old_mu),
            source='Original S33 protocol falsifier: full-stack math.log(new/initial)+fsum, oldmu from sealed S32 decomposition; no new k or GT input',
            interpretation='Saved-prediction descriptive comparison; not an accuracy, significance or novelty verdict'),
        scope='Saved original/gradient/scale records and raw boundary consistency. No backward or new k; full3x4 truth is producer recorded, not independently recomputed at every step.')
    return summary,gradient_records

def run(path,expected):
    require(not (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists(),'Never repeat/overwrite attempt')
    require(sha(path)==expected,'Explicit root result binding SHA');b=read(path)
    require(b['schema']=='s33-independent-saved-review-binding-v1' and b['status']=='FROZEN','Unbound candidate cannot execute')
    cp=HERE/'candidate.json';require(sha(cp)==b['candidate_sha256'],'Reviewed candidate identity');c=read(cp)
    require(c['status']=='CANDIDATE_UNBOUND_DO_NOT_EXECUTE','Preserve source candidate')
    require(b['scoring_manifest']==c['expected_scoring_manifest'] and b['scoring_receipt']==c['expected_scoring_receipt'],'Exact reviewed completed scoring references')
    require(c['resource']==dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),'Fixed external budget')
    ids={str(Path(path).resolve()):expected,str(cp):b['candidate_sha256']}
    for p,h in c['source_sha256'].items():require(sha(p)==h,'Reviewed source/JSON changed');ids[p]=h
    require(ids[str(Path(__file__).resolve())]==sha(__file__),'Executing reviewer bound')
    def bind(ref):
        p=Path(ref['path']);require(p.is_absolute() and sha(p)==ref['sha256'],'Explicit JSON result identity');ids[str(p)]=ref['sha256'];return read(p)
    pc=read(S33_CONTRACT);require(ids[str(S33_CONTRACT)]==S33_SHA and pc['status']=='FROZEN','Actual frozen S33 producer')
    sm=bind(b['scoring_manifest']);sr=bind(b['scoring_receipt'])
    require(b['scoring_receipt']['path']==str(SCORING/'receipt.json'),'Exact official scoring receipt')
    require(sm['schema']=='s33-import48-score16-v1' and sm['status']=='FROZEN' and sm['producer_contract']==dict(path=str(S33_CONTRACT),sha256=S33_SHA),'Exact new scoring contract')
    require(sm['output_root']==str(SCORING) and sm['selection_sha256']==SELSHA and [w['id'] for w in sm['windows']]==list(WINDOWS),'Fixed S33 scoring domain')
    require(sr['status']=='PASS' and sr['inputs_unchanged'] is True and sr['scoring_manifest_sha256']==b['scoring_manifest']['sha256'],'Actual whole-table PASS first')
    require(sr['per_frame_rows']==64 and sr['imported_S32_rows']==48 and sr['new_candidate_rows']==16 and sr['endpoint_groups']==16,'Full old48 plusnew16')
    for p,h in sm['control_sha256'].items():require(c['source_sha256'].get(p)==h and sha(p)==h,'Exact reviewed scorer control');ids[p]=h
    barrier=bind(sm['terminal_barrier']);require(barrier['status']=='COMPLETE_FIXED_WINDOW_MATRIX_SEALED' and barrier['contract_sha256']==S33_SHA,'All4 new windows terminal')
    old=read(S32/'metrics.json');oldraw=(S32/'metrics.json').read_bytes();oldcsv=(S32/'per_frame.csv').read_bytes()
    prior_manifest=read(ROOT/'work/S32_scoring_preparation/manifest.json');old_windows={w['id']:w for w in prior_manifest['windows']}
    for p,h in sm['old_scoring_sha256'].items():require(ids.get(p)==h and sha(p)==h,'All original table source identities')
    require(len(old['per_frame'])==48,'Full old48 rows')
    scored_ids=sr['input_sha256'];owners={};gt_needed=[];endpoint={}
    for w in sm['windows']:
        sid=w['id'];r=bind(w['producer_receipt']);directory=Path(w['producer_receipt']['path']).parent;owners[sid]=(directory,r)
        require(w['frames']==old_windows[sid]['frames'] and [f['index'] for f in w['frames']]==list(range(4)),'Complete unchanged frame and sensor associations')
        require(directory==S33/sid and r['window_id']==sid and r['contract_sha256']==S33_SHA and r['selection_sha256']==SELSHA,'Same producer/window')
        require(barrier['windows'][sid]==dict(status=r['status'],receipt_sha256=w['producer_receipt']['sha256']),'Terminal barrier binds all4')
        require(scored_ids[w['producer_receipt']['path']]==w['producer_receipt']['sha256'],'Scored same terminal receipt')
        available=w['availability']=='AVAILABLE'
        require(r['status']==('UNAVAILABLE' if sid==WINDOWS[0] else 'PASS' if available else 'FAILED'),'Preserve actual statuses')
        if sid==WINDOWS[0]:require(w['availability']=='UNAVAILABLE_MISSING_POSE','Original missing window')
        else:require(w['availability'] in ('AVAILABLE','UNAVAILABLE_PRODUCER_FAILED'),'No running window declared NA')
        if available:
            item=w['endpoint'];require(item['status']=='AVAILABLE' and item['name']==NEW and item['path']==str(directory/(NEW+'.npz')) and item['dtype']=='float32' and item['depth_key']=='depth','Complete new FP32 endpoint')
            endpoint[sid]=item
            for f in w['frames']:gt_needed.append(dict(window_id=sid,index=f['index'],path=f['depth_path'],sha256=f['depth_sha256']))
        else:require(w['endpoint']['path'] is None and w['endpoint']['sha256'] is None,'No failed partial endpoint read')
    started=utc();timer=time.perf_counter();receipt=dict(status='RUNNING',started_utc=started,binding_sha256=expected,candidate_sha256=b['candidate_sha256'],new_models=0,new_GA=0,new_MST=0,new_backward=0,new_k=0,new_SS_RMS=0)
    write('attempt.json',receipt)
    try:
        # All PASS products and old raw-reference bytes are bound before decode.
        for sid,(directory,r) in owners.items():
            if r['status']!='PASS':continue
            required={'GA/C2a/'+x for x in ('receipt.json','initial_raw.npz','final_raw_before_clean.npz',
                'initial_raw_metadata.json','final_raw_metadata.json','initial_decoded.npz','output.npz',
                'controlled_alignment.npz','s33_initial_gate.json','s33_scale_trace.jsonl',
                'optimization_trace.jsonl','gradient_depth_trace.jsonl')}
            require(required<=set(r['outputs']),'Complete raw, decoded and saved trace artifact set')
            for name,h in r['outputs'].items():
                p=directory/name;require(not Path(name).is_absolute() and p.resolve().is_relative_to(directory),'No output escape')
                require(sha(p)==h==scored_ids[str(p)],'Complete new producer output seal');ids[str(p)]=h
            require(ids[endpoint[sid]['path']]==endpoint[sid]['sha256'],'Same scored candidate')
            ref=pc['references'][sid];pr=bind(dict(path=ref['receipt'],sha256=ref['receipt_sha256']));prior=Path(ref['receipt']).parent
            require(pr['status']=='PASS' and pr['contract_sha256']==pc['s32_contract_sha256'],'Same historical S32 initialization')
            for name,h in ref['files'].items():
                p=prior/name;require(sha(p)==h==pr['outputs'][name],'Complete prior raw/decoded/alignment reference');ids[str(p)]=h
            p=prior/'decomposition.json';require(sha(p)==pr['outputs']['decomposition.json'],'Original free400 mu source byte seal');ids[str(p)]=pr['outputs']['decomposition.json']
        for name,h in sr['output_sha256'].items():
            require(Path(name).name==name,'Flat scored output');p=SCORING/name;require(sha(p)==h,'Complete scorer output seal');ids[str(p)]=h
        metrics=read(SCORING/'metrics.json');newmetrics=read(SCORING/'new_candidate_metrics.json')
        require(metrics['per_frame'][:48]==old['per_frame'] and len(metrics['per_frame'])==64 and metrics['imported_rows']==48 and metrics['new_rows']==16,'Full old/new row domain')
        require((SCORING/'imported_s32_metrics.json').read_bytes()==oldraw and (SCORING/'imported_s32_per_frame.csv').read_bytes()==oldcsv,'Full original JSON and CSV bytes imported intact')
        merged_csv=(SCORING/'per_frame.csv').read_bytes();require(merged_csv.startswith(oldcsv),'Original48 CSV literal byte prefix')
        for sid in WINDOWS:
            require(set(metrics['window_groups'][sid])==set(OLD_ENDS+(NEW,)),'All four conditions per window')
            for e in OLD_ENDS:require(metrics['window_groups'][sid][e]==old['window_groups'][sid][e],'Original group unchanged')
        for e in OLD_ENDS:require(metrics['endpoint_summaries'][e]==old['endpoint_summaries'][e],'Original window summaries unchanged')
        pre=read(SCORING/'prediction_input_seal.json');gs=read(SCORING/'GT_byte_seal.json');gr=read(SCORING/'GT_receipt.json')
        require(pre['GT_bytes_read_by_this_scorer'] is False and gs['status']=='PASS' and gs['GT_images_decoded']==0,'Existing phase seals')
        require(datetime.fromisoformat(pre['utc'])<=datetime.fromisoformat(gs['utc'])<=datetime.fromisoformat(gr['utc'])<=datetime.fromisoformat(sr['completed_utc']),'Original scorer ordering')
        require(len({f['path'] for f in gt_needed})==len(gt_needed),'Distinct prescribed sensors')
        require(gs['GT_sha256']=={f['path']:f['sha256'] for f in gt_needed} and sr['GT_images_decoded']==gr['GT_images_decoded']==len(gt_needed),'All and only new available GT')
        for item in endpoint.values():require(pre['input_sha256'][item['path']]==item['sha256'],'Candidate sealed before original scorer GT')
        gtbytes={}
        write('progress.json',dict(stage='GT_BYTE_SEAL_BEFORE_ANY_ARRAY_DECODE',utc=utc(),prediction_arrays_decoded=False))
        for f in gt_needed:
            raw=Path(f['path']).read_bytes();require(digest(raw)==f['sha256']==scored_ids[f['path']],'Same previously scored GT bytes');ids[f['path']]=f['sha256'];gtbytes[f['window_id'],f['index']]=raw
        write('input_seal.json',dict(status='PASS_COMPLETE_SAVED_AND_GT_BYTE_SEAL_BEFORE_ANY_DECODE',utc=utc(),identities=ids,prediction_arrays_decoded=False,GT_images_decoded=0,GT_images_hashed=len(gtbytes),blind_test=False))
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
        import numpy as np
        import cv2
        require(np.__version__=='1.26.4','Existing NumPy');cv2.setNumThreads(1)
        h28=module(H28,'s33_independent_metric');h32=module(H32,'s33_prior_independent_logic');review_trace=trace_function(h32)
        data={};traces={};steps=[]
        for sid,item in endpoint.items():
            a=h28.load_archive(item['path'],ids,{'depth':(4,384,512)})['depth'];data[sid]=a
            traces[sid],records=review_window(sid,a,pc,ids,h28,h32,np,review_trace);steps.extend(records)
        gt={}
        for key,raw in gtbytes.items():
            a=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED);require(a is not None and a.dtype==np.uint16 and a.shape==(480,640),'Original sensor schema');gt[key]=a
        rows=[];groups={};diff={}
        for w in sm['windows']:
            sid=w['id'];subset=[]
            for i in range(4):
                row=h32.unavailable(sid,NEW,i,w['reason']) if w['availability']!='AVAILABLE' else dict(window_id=sid,endpoint=NEW,index=i,row_status='SCORED',missing_reason=None,**h28.independent_frame(data[sid][i],gt[sid,i]))
                h32.compare_record(row,metrics['per_frame'][48+len(rows)],sid+'/'+str(i),h28,diff);rows.append(row);subset.append(row)
            groups[sid]={NEW:h32.group_of(subset)};h32.compare_record(groups[sid][NEW],metrics['window_groups'][sid][NEW],sid+'/group',h28,diff)
        require(newmetrics['endpoint']==NEW and newmetrics['per_frame']==metrics['per_frame'][48:],'Separate new16 table is same rows')
        summaries={}
        for label,domain in (('all_four_prespecified',WINDOWS),('three_preselected_pose_eligible',WINDOWS[1:])):
            g=h32.window_mean(groups,domain,NEW);summaries[label]=g;h32.compare_record(g,metrics['endpoint_summaries'][NEW][label],label,h28,diff)
        require(newmetrics['window_groups']=={sid:metrics['window_groups'][sid][NEW] for sid in WINDOWS} and newmetrics['endpoint_summary']==metrics['endpoint_summaries'][NEW],'Separate new group/summary equality')
        for name,count,offset in (('per_frame.csv',64,48),('new_candidate_per_frame.csv',16,0)):
            with (SCORING/name).open(newline='') as f:cr=list(csv.DictReader(f))
            require(len(cr)==count,'Complete CSV rows '+name)
            for row,raw in zip(rows,cr[offset:]):
                require(set(row)==set(raw),'Complete new CSV fields')
                for key,value in row.items():
                    if key in FLOATS:h28.metric_match(value,None if raw[key]=='' else float(raw[key]),'csv/'+key,diff)
                    elif value is None:require(raw[key]=='','Unknown CSV remains blank')
                    elif isinstance(value,int):require(int(raw[key])==value,'CSV exact integer')
                    else:require(raw[key]==value,'CSV exact string')
        require(len(rows)==16 and len(steps)==400*len(endpoint),'All new rows and actual saved steps')
        newscored=sum(r['row_status']=='SCORED' for r in rows)
        require(newscored==len(gt)==sr['new_scored_rows'] and sr['new_NA_rows']==16-newscored,'Complete new scored/NA counts')
        require(metrics['scored_rows']==old['scored_rows']+newscored and metrics['unavailable_rows']==old['unavailable_rows']+16-newscored,'Full64 counts')
        require(all(summaries['all_four_prespecified'][k] is None for k in FLOATS),'Keep unavailable all-four summary')
        for p,h in ids.items():require(sha(p)==h,'Bound input changed during review')
        write('recomputed.json',dict(new_per_frame=rows,new_window_groups={sid:g[NEW] for sid,g in groups.items()},new_summaries=summaries,trace_reviews=traces,complete_saved_step_records=steps,
            imported_old_rows=48,full_rows=64,full_groups=16,new_scored_rows=newscored,new_NA_rows=16-newscored,metric_max_absolute_difference=diff,
            import_proof=dict(old_metrics_byte_copy=True,old_CSV_byte_copy=True,old48_CSV_literal_prefix=True,old_rows_groups_summaries_equal=True)))
        receipt.update(status='PASS_INDEPENDENT_S33_SAVED_REVIEW',completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
            imported_rows=48,new_rows=16,full_rows=64,full_groups=16,new_scored_rows=newscored,new_NA_rows=16-newscored,GT_images_decoded=len(gt),
            saved_optimization_records=len(steps),saved_gradient_records=len(steps),saved_scale_records=len(steps),
            matched_prior_initial_raw_tensors=33*len(endpoint),validated_new_boundary_raw_tensors=66*len(endpoint),
            prediction_only_depth_log_change_pixels=4*384*512*len(endpoint),
            metric_max_absolute_difference=diff,input_unchanged=True,input_sha256=ids,
            scope='Saved arithmetic/trace audit; not recomputed gradients or new physical-world validation. No new k or SS/RMS. Existing S32 score rows imported byte-backed unchanged.',
            output_sha256={p.name:sha(p) for p in HERE.iterdir() if p.name in ('attempt.json','progress.json','input_seal.json','recomputed.json')})
        write('receipt.json',receipt);print(json.dumps(dict(status=receipt['status'],new_scored_rows=newscored)))
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=utc(),error=repr(e));write('receipt.json',receipt);raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binding',required=True);p.add_argument('--sha256',required=True);a=p.parse_args();run(Path(a.binding).resolve(),a.sha256)
