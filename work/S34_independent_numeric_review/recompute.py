#!/usr/bin/env python3
"""Independent S34 saved GA/score review. No model, GA, backward, clean or k."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, csv, hashlib, importlib.util, json, math, os, sys, time, traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'results/S34_geometry_producer'
SCORE=ROOT/'results/S34_depth_scoring'
ENDS=('old_fixed_zero','old_fixed_free_400','old_fixed_common_scale_400')
ARMS=ENDS[1:]
MODES=('common_old',)+ENDS
NEW=[4,5,6,7]
FLOATS=('absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt')
SUMS=('gt_valid_pixels','gt_invalid_pixels','prediction_invalid_all_pixels','prediction_invalid_on_gt_pixels')
H28=ROOT/'work/S28_independent_numeric_review/recompute.py'
H28SHA='2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2'
GRID=384*512

def utc():return datetime.now(timezone.utc).isoformat()
def require(x,label):
    if not x:raise ValueError(label)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(name,v):(HERE/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def module(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def exact(a,b,label):require(a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes(),'Exact '+label)
def near(a,b,label):require(math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,abs_tol=1e-5,rel_tol=1e-5),'Saved statistic/scale '+label)
def raw_domain():
    # Independently enumerated fixed8 star:49 parameters +8 buffers=57.
    p={'pw_poses','pw_adaptors','im_poses','im_focals','im_pp'}
    p|={f'{kind}.0_{j}' for kind in ('pred_i','pred_j','conf_i','conf_j') for j in range(1,8)}
    p|={f'{kind}.{j}' for kind in ('im_conf','im_depthmaps') for j in range(8)}
    b={'_pp','_grid','_weight_i','_weight_j','_stacked_pred_i','_stacked_pred_j','_ei','_ej'}
    return {'parameter::'+x for x in p}|{'buffer::'+x for x in b}
def group(rows):
    require([r['index'] for r in rows]==NEW,'Complete ordered new4')
    g=dict(frame_indices=NEW,frame_count=4,aggregation='equal_frame_mean;no_available_frame_or_pixel_pooled_substitution')
    for k in FLOATS:
        v=[r[k] for r in rows];g[k]=math.fsum(v)/4 if all(x is not None for x in v) else None;g[k+'_defined_frames']=sum(x is not None for x in v)
    for k in SUMS:g[k+'_sum_descriptive']=sum(r[k] for r in rows)
    g['empty_gt_frames']=[r['index'] for r in rows if r['gt_valid_pixels']==0]
    g['invalid_prediction_frames']=[r['index'] for r in rows if r['prediction_invalid_on_gt_pixels']>0]
    return g
def compare(actual,reported,label,h,diffs):
    require(set(actual)==set(reported),'Complete record fields '+label)
    for k,v in actual.items():
        if k in FLOATS:h.metric_match(v,reported[k],label+'/'+k,diffs)
        else:require(v==reported[k],'Exact record '+label+'/'+k)

def saved_arm(arm,packet,common,ids,h,np,producer_sha):
    d=BASE/arm;rec=read(d/'receipt.json');obs=rec['observer']
    require(rec['status']=='PASS' and rec['contract_sha256']==producer_sha and rec['endpoint']==arm,'Actual arm identity')
    require(rec['frame_count']==8 and rec['iterations']==rec['adam_steps']==400 and rec['clean_calls']==1,'Actual original8 counts')
    require(obs['s34_actual_counts']==dict(backward=400,Adam=400,MST=1,PnP=7,alignment=1,scale_rows=400),'Recorded operation counts')
    require(obs['s34_gradient_steps']==400 and obs['s34_objective_forward_counts']==dict(optimization=400,patch_boundary_no_update=2,postfinal_no_update=1,total=403),'Recorded objective path')
    initial=h.load_archive(d/'initial_raw.npz',ids);final=h.load_archive(d/'final_raw_before_clean.npz',ids)
    im=read(d/'initial_raw_metadata.json');fm=read(d/'final_raw_metadata.json')
    h.validate_raw(initial,im,'S34 initial');h.validate_raw(final,fm,'S34 before clean')
    require(set(initial)==set(final)==raw_domain() and len(initial)==57,'Exact complete57 raw domain')
    trainable={'parameter::pw_poses','parameter::im_focals'}|{f'parameter::im_depthmaps.{i}' for i in NEW}
    for k in initial:
        require(all(im[k][f]==fm[k][f] for f in ('shape','dtype','requires_grad')),'Stable metadata '+k)
        require(im[k]['requires_grad']==(k in trainable),'Exact mixed-depth/focal/pair trainability '+k)
        require(np.isfinite(initial[k]).all() and np.isfinite(final[k]).all(),'Finite complete raw '+k)
        if k not in trainable:exact(initial[k],final[k],'frozen raw before clean '+k)
    decoded=h.load_archive(d/'initial_decoded.npz',ids)
    require(set(decoded)=={'depth','point_cloud','focal','pp','c2w','pw_scale','pw_poses','adaptors','objective'},'Complete initial decoded domain')
    output=h.load_archive(d/'output.npz',ids)
    for k in packet:exact(output[k],packet[k],'packet copied from original output '+k)
    require(decoded['depth'].shape==(8,384,512) and decoded['depth'].dtype==np.float32,'Initial depth schema')
    gate=read(d/'s34_initial_gate.json')
    require(gate['status']=='PASS' and gate['contract_sha256']==producer_sha and gate['arm']==arm and gate['raw_count']==57 and gate['mixed_flags']==[False]*4+[True]*4,'Recorded new8 initial gate')
    require(gate['cross_arm_initialization']==('REFERENCE_ARM' if arm==ARMS[0] else 'ALL57_RAW_AND_DECODED_EXACT'),'Correct reference interpretation')
    def lines(name):
        raw=(d/name).read_bytes();require(digest(raw)==ids[str(d/name)],'Trace identity changed');return [json.loads(x) for x in raw.decode().splitlines()]
    ordinary=lines('optimization_trace.jsonl');grad=lines('gradient_depth_trace.jsonl');scale=lines('s34_scale_trace.jsonl')
    require(len(ordinary)==len(grad)==len(scale)==400 and all([x['iteration'] for x in rows]==list(range(400)) for rows in (ordinary,grad,scale)),'All800 paired400 indices')
    names={f'im_depthmaps.{i}' for i in range(8)}|{'im_focals','pw_poses'}
    grad_counts={n:dict(none=0,present=0,zero_l2=0) for n in sorted(names)}
    target=gate['scale']['fixed_initial_log_mean'];max_mean=0.;max_factor=0.;records=[]
    for i,(o,g,s) in enumerate(zip(ordinary,grad,scale)):
        require(g['actual_adam_steps']==i+1 and o['loss_before_step']==g['loss_before_step'] and o['lr']==g['lr'],'Paired original/gradient step')
        require(math.isfinite(o['loss_before_step']) and math.isclose(o['lr'],.01+(1e-6-.01)*i/400,abs_tol=1e-15,rel_tol=0),'Original finite loss and linear LR')
        gs=g['gradients_from_this_step'];require(set(gs)==names,'Complete ten selected gradient records')
        for name,v in gs.items():
            frozen=name in {f'im_depthmaps.{j}' for j in range(4)}
            require(v['requires_grad']==(not frozen) and v['grad_is_none']==frozen,'Mixed recorded gradient route '+name)
            if frozen:
                require(v['finite'] is None and v['l2'] is None,'No invented frozen gradient values');grad_counts[name]['none']+=1
            else:
                require(v['finite'] is True and math.isfinite(v['l2']) and v['l2']>=0,'Finite present recorded gradient, zero permitted')
                grad_counts[name]['present']+=1;grad_counts[name]['zero_l2']+=int(v['l2']==0)
        for when,gkey in [('before','statistics_before_step'),('after','statistics_after_step')]:
            state=g[gkey];frames=state['frames'];z=s[when]
            require([x['index'] for x in frames]==list(range(8)),'All8 depth statistic rows')
            for f in frames:
                require(set(f)=={'index','log_mean','log_min','log_max','depth_mean','depth_min','depth_max','log_change_mean','log_change_max_abs','depth_initial_ratio_mean'} and all(math.isfinite(v) for k,v in f.items() if k!='index'),'Complete finite saved frame statistics')
                require(f['depth_min']>0 and f['log_change_max_abs']>=0 and f['depth_initial_ratio_mean']>0,'Saved depth statistic domain')
                if f['index']<4:require(f==grad[0]['statistics_before_step']['frames'][f['index']] and f['log_change_mean']==f['log_change_max_abs']==0 and f['depth_initial_ratio_mean']==1,'All-step frozen old depth statistics')
            require(len(state['focal'])==8 and all(len(x)==1 and math.isfinite(x[0]) and x[0]>0 for x in state['focal']),'Eight saved focals')
            effective=z['effective_scales'];require(len(effective)==7 and all(math.isfinite(x) and x>0 for x in effective),'Seven saved effective scales')
            require(state['pw_scale']==effective,'Gradient and scale trace boundary agreement')
            require(z['fixed_initial_log_mean']==target and z['full_3x4_exact'] is True,'Fixed target and producer-recorded matrix gate')
            mean=math.fsum(math.log(x) for x in effective)/7;near(mean,z['effective_log_mean'],'effective mean')
            if arm==ARMS[1]:
                require(abs(mean-target)<=1e-5,'Actual saved seven-scale mean constraint')
                expected=math.exp(target-z['raw_log_mean']);near(z['factor'],expected,'common factor')
            else:expected=1.;require(z['factor']==1.,'Original free factor exactly one');near(mean,z['raw_log_mean'],'free effective/raw mean')
            max_mean=max(max_mean,abs(mean-target));max_factor=max(max_factor,abs(z['factor']-expected))
        if i:
            require(grad[i-1]['statistics_after_step']==g['statistics_before_step'] and scale[i-1]['after']==s['before'],'Saved adjacent step continuity')
        records.append(dict(arm=arm,iteration=i,loss_before_step=o['loss_before_step'],lr=o['lr'],actual_adam_steps=g['actual_adam_steps'],
            depth_grad_none=[gs[f'im_depthmaps.{j}']['grad_is_none'] for j in range(8)],depth_grad_l2=[gs[f'im_depthmaps.{j}']['l2'] for j in range(8)]))
    require(scale[0]['before']==gate['scale'] and scale[0]['before']['factor']==1.,'Initial effective scale unchanged')
    require(grad[0]['loss_before_step']==float(decoded['objective']) and grad[-1]['loss_before_step']==obs['returned_pre_last_step_loss'],'Initial and pre-last loss identities')
    require(math.isfinite(obs['postfinal_objective']),'Finite recorded final objective, not recomputed')
    require(decoded['focal'].tolist()==grad[0]['statistics_before_step']['focal'] and packet['focal'].tolist()==grad[-1]['statistics_after_step']['focal'],'All8 saved focal boundary values')
    require(decoded['pw_scale'].tolist()==scale[0]['before']['effective_scales'],'All7 initial decoded effective scales')
    rawpair='parameter::pw_poses';require(initial[rawpair].shape==final[rawpair].shape==(7,8),'Seven complete pair parameters')
    near(target,math.fsum(float(x) for x in initial[rawpair][:,-1])/7,'m0 from initial raw')
    for values,z in [(initial[rawpair][:,-1],scale[0]['before']),(final[rawpair][:,-1],scale[-1]['after'])]:
        near(math.fsum(float(x) for x in values)/7,z['raw_log_mean'],'boundary raw log mean')
        for ell,effective in zip(values,z['effective_scales']):near(math.exp(float(ell))*z['factor'],effective,'boundary raw exp times factor')
    boundary=[]
    for j in range(8):
        k=f'parameter::im_depthmaps.{j}';a,z=initial[k],final[k]
        require(a.shape==z.shape==(384,512) and a.dtype==z.dtype==np.float32,'Two-dimensional raw leaves')
        initial_depth=decoded['depth'][j];final_depth=packet['depth'][j]
        for raw,dep,label,stats in [(a,initial_depth,'initial',grad[0]['statistics_before_step']['frames'][j]),(z,final_depth,'final',grad[-1]['statistics_after_step']['frames'][j])]:
            require(np.allclose(np.exp(raw.astype(np.float64)),dep,atol=1e-6,rtol=1e-6),'Full raw log to decoded depth exp')
            require(stats['log_min']==float(raw.min()) and stats['log_max']==float(raw.max()) and stats['depth_min']==float(dep.min()) and stats['depth_max']==float(dep.max()),'Boundary exact extrema')
            near(math.fsum(float(x) for x in raw.flat)/GRID,stats['log_mean'],'boundary log mean')
            near(math.fsum(float(x) for x in dep.flat)/GRID,stats['depth_mean'],'boundary depth mean')
        delta=z-a;last=grad[-1]['statistics_after_step']['frames'][j]
        require(last['log_change_max_abs']==float(np.abs(delta).max()),'Boundary cumulative log change maximum')
        near(math.fsum(float(x) for x in delta.flat)/GRID,last['log_change_mean'],'boundary cumulative log change mean')
        near(math.fsum(float(x) for x in (final_depth/initial_depth).flat)/GRID,last['depth_initial_ratio_mean'],'boundary saved depth ratio mean')
        if j<4:
            exact(a,z,'old depth frozen raw');require(np.allclose(initial_depth,common['depth'][j],atol=1e-5,rtol=1e-5) and np.allclose(final_depth,common['depth'][j],atol=1e-5,rtol=1e-5),'Common old output roundtrip')
        boundary.append(dict(index=j,raw_initial_sha=digest(a.tobytes()),raw_final_sha=digest(z.tobytes()),raw_frozen=j<4,raw_exp_links=True))
    for k in ('pp','c2w'):exact(decoded[k],packet[k],'Frozen decoded '+k)
    summary=dict(arm=arm,raw_tensors_each_boundary=57,frozen_raw_tensors=57-len(trainable),ordinary_records=400,gradient_records=400,scale_records=400,
        gradient_record_counts=grad_counts,boundary_depth_links=boundary,max_abs_effective_log_mean_from_initial=max_mean,max_abs_factor_arithmetic_difference=max_factor,
        postfinal_objective_from_producer=obs['postfinal_objective'],scope='All saved records and raw boundaries checked, no gradients recomputed. Per-step full3x4 and parameter object identity are producer-recorded checks, not independently reconstructed matrices/objects. No per-step raw_scales are saved.')
    return summary,records,initial,im,decoded

def run(binding_path,expected):
    require(not (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists(),'Never overwrite/repeat attempt')
    require(sha(binding_path)==expected,'Caller frozen binding SHA');b=read(binding_path)
    require(b['schema']=='s34-independent-saved-review-binding-v1' and b['status']=='FROZEN','Preparation cannot execute')
    cp=HERE/'candidate.json';require(sha(cp)==b['candidate_sha256'],'Reviewed candidate SHA');c=read(cp)
    require(c['status']=='CANDIDATE_UNBOUND_DO_NOT_EXECUTE' and c['resource']==dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),'Fixed candidate/resource')
    ids={str(Path(binding_path).resolve()):expected,str(cp):b['candidate_sha256']}
    for p,h in c['source_sha256'].items():require(sha(p)==h,'Reviewed source changed');ids[p]=h
    require(ids[str(H28)]==H28SHA and ids[str(Path(__file__).resolve())]==sha(__file__),'Own/helper identity')
    def bind(ref):
        p=Path(ref['path']);require(p.is_absolute() and sha(p)==ref['sha256'],'Bound JSON identity');ids[str(p)]=ref['sha256'];return read(p)
    pc=bind(b['producer_contract']);sm=bind(b['scoring_manifest']);sr=bind(b['scoring_receipt'])
    require(b['producer_contract']['path']==str(ROOT/'work/S34_preparation/contract.json') and pc['schema']=='s34-shared-old4-eight-frame-consumer-v1' and pc['status']=='FROZEN','Formal producer')
    require(pc['arms']==list(ARMS) and pc['endpoints']==list(ENDS) and pc['steps']==400,'Producer fixed domain')
    producer_source=ROOT/'work/S34_preparation/produce_geometry.py'
    require(sha(producer_source)==b['producer_source_sha256']==pc['identities'][str(producer_source)]==c['source_sha256'][str(producer_source)],'Final producer source agrees with reviewed candidate');ids[str(producer_source)]=b['producer_source_sha256']
    for field in ('parent_runner','s28_runner','s30_runner','optimizer_source'):
        path=pc[field];require(c['source_sha256'][path]==pc['identities'][path]==sha(path),'Actual producer implementation dependency '+field)
    require(b['scoring_manifest']['path']==str(ROOT/'work/S34_scoring_preparation/manifest.json') and sm['status']=='FROZEN' and sm['schema']=='s34-fixed-new4-depth-scoring-v1','Formal scorer')
    require(sm['endpoints']==list(ENDS) and sm['new_indices']==NEW and sm['producer_contract']==b['producer_contract'],'Same three endpoints/new4/producer')
    require(b['scoring_receipt']['path']==str(SCORE/'receipt.json') and sr['status']=='PASS' and sr['inputs_unchanged'] is True and sr['scoring_manifest_sha256']==b['scoring_manifest']['sha256'],'Whole primary scoring PASS first')
    require(sr['per_frame_rows']==12 and sr['endpoint_groups']==3 and sr['sensor_GT_images_decoded']==4,'Primary complete denominator')
    for p,h in sm['control_sha256'].items():require(c['source_sha256'].get(p)==h and sha(p)==h,'Reviewed primary scorer controls');ids[p]=h
    require(sm['gt_depth_frames']==c['gt_depth_frames'],'Exact metadata-only fixed four GT')
    barrier=bind(sm['terminal_barrier']);require(barrier['status']=='SEALED_ALL_GEOMETRY_AND_CONSUMER_TERMINAL' and barrier['producer_contract_sha256']==b['producer_contract']['sha256'],'Terminal barrier identity')
    require(set(barrier['producer_receipts'])==set(MODES),'All four producers present')
    prs={}
    for mode in MODES:
        p=BASE/mode/'receipt.json';require(sha(p)==barrier['producer_receipts'][mode],'Actual producer receipt hash')
        pr=read(p);require(pr['status']=='PASS' and pr['contract_sha256']==b['producer_contract']['sha256'],'All four producer PASS before any archive/GT access');prs[mode]=pr;ids[str(p)]=sha(p)
    started=utc();timer=time.perf_counter();receipt=dict(status='RUNNING',started_utc=started,binding_sha256=expected,candidate_sha256=b['candidate_sha256'],new_models=0,new_GA=0,new_backward=0,new_clean=0,new_k=0)
    write('attempt.json',receipt)
    try:
        for p,h in barrier['sealed_files'].items():require(sha(p)==h==sr['input_sha256'][p],'Complete saved input seal');ids[p]=h
        for mode,pr in prs.items():
            for rel,h in pr['outputs'].items():
                p=BASE/mode/rel;require(not Path(rel).is_absolute() and p.resolve().is_relative_to(BASE/mode),'Producer output scope')
                require(ids[str(p)]==h,'All producer output identities')
            require(pr['outputs']['packet.npz']==ids[str(BASE/mode/'packet.npz')],'Exact packet used for primary score')
        require({'metrics.json','per_frame.csv','pre_score_seal.json','gt_receipt.json','schema_and_old_prefix.json'}<=set(sr['outputs']),'Every consumed scoring product explicitly sealed')
        for name,h in sr['outputs'].items():
            require(Path(name).name==name,'Flat scoring products');p=SCORE/name;require(sha(p)==h,'Complete scorer output identity');ids[str(p)]=h
        consumer=barrier['consumer_terminal'];require(consumer==sr['consumer_terminal'],'Consumer status preserved')
        require(consumer['status'] in ('PASS_ORIGINAL_CONSUMER_COMPONENTS','FAILED_PRESERVED'),'Actual consumer terminal status')
        require(consumer['receipt_path'] in ids,'Consumer terminal receipt belongs to barrier')
        require(read(consumer['receipt_path'])['status']==consumer['status'],'Consumer identity/status only, no independent consumer math claim')
        pre=read(SCORE/'pre_score_seal.json');require(pre['sensor_GT_bytes_read'] is False and pre['prediction_arrays_decoded'] is False,'Main pre-score boundary')
        for p,h in barrier['sealed_files'].items():require(pre['input_sha256'][p]==h,'Pre-score seals all geometry/consumer')
        rawgt={}
        for f in c['gt_depth_frames']:
            raw=Path(f['path']).read_bytes();require(digest(raw)==f['sha256']==sr['input_sha256'][f['path']],'Same four already-scored GT bytes');rawgt[f['index']]=raw;ids[f['path']]=f['sha256']
        require(set(rawgt)==set(NEW),'Exactly four fixed sensor images')
        require(all(ids.get(p)==v for p,v in sr['input_sha256'].items()),'Complete original scoring input identity domain covered')
        write('input_seal.json',dict(status='ALL_SAVED_OUTPUT_AND_FOUR_GT_BYTES_SEALED_BEFORE_DECODE',utc=utc(),identities=ids,GT_images_decoded=0,prediction_arrays_decoded=0,already_seen=True))
        for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
        import numpy as np
        import cv2
        require(np.__version__=='1.26.4','Existing scientific NumPy');cv2.setNumThreads(1)
        h=module(H28,'s34_independent_metric_helper')
        packets={}
        for mode in MODES:
            n=4 if mode=='common_old' else 8;shapes=dict(depth=(n,384,512),point_cloud=(n,384,512,3),conf=(n,384,512),focal=(n,1),pp=(n,2),c2w=(n,4,4))
            packets[mode]=h.load_archive(BASE/mode/'packet.npz',ids,shapes)
        reviews={};steps=[];previous=None
        for arm in ARMS:
            write('progress.json',dict(stage='SAVED_RAW_AND_TRACE_REVIEW',arm=arm,utc=utc(),GT_images_decoded=0))
            summary,records,raw,meta,decoded=saved_arm(arm,packets[arm],packets['common_old'],ids,h,np,b['producer_contract']['sha256'])
            if previous is None:previous=(raw,meta,decoded)
            else:
                first,fmeta,fdecoded=previous;require(meta==fmeta,'All57 cross-arm initial metadata')
                for key in first:exact(raw[key],first[key],'All57 cross-arm initial raw '+key)
                require(set(decoded)==set(fdecoded),'Full cross-arm decoded keys')
                for key in decoded:exact(decoded[key],fdecoded[key],'Full cross-arm decoded/objective '+key)
                aa=h.load_archive(BASE/ARMS[0]/'controlled_alignment.npz',ids);bb=h.load_archive(BASE/ARMS[1]/'controlled_alignment.npz',ids)
                require(set(aa)==set(bb),'Complete alignment domain')
                for key in aa:exact(aa[key],bb[key],'Cross-arm alignment '+key)
            reviews[arm]=summary;steps.extend(records)
        raw,_,decoded=previous
        zero=packets[ENDS[0]];zpre=h.load_archive(BASE/ENDS[0]/'preclean_packet.npz',ids)
        zseal=read(BASE/ENDS[0]/'inputs_seal.json')
        require(zseal['initial_raw_sha256']==ids[str(BASE/ARMS[0]/'initial_raw.npz')] and zseal['initial_decoded_sha256']==ids[str(BASE/ARMS[0]/'initial_decoded.npz')],'Zero exact new free initial provenance')
        for key in ('depth','point_cloud','focal','pp','c2w'):exact(zero[key],decoded[key],'Zero packet unchanged nonconf '+key);exact(zpre[key],decoded[key],'Zero preclean '+key)
        for j in range(8):exact(zpre['conf'][j],raw[f'parameter::im_conf.{j}'],'Zero preclean raw confidence')
        for mode in ENDS:require(np.allclose(packets[mode]['depth'][:4],packets['common_old']['depth'],atol=1e-5,rtol=1e-5),'Every endpoint old prefix retained')
        gt={}
        for j,raw in rawgt.items():
            a=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED);require(a is not None and a.dtype==np.uint16 and a.shape==(480,640),'Exact original sensor schema');gt[j]=a
        metrics=read(SCORE/'metrics.json');require(metrics['prespecified_rows']==12 and metrics['prespecified_groups']==3 and metrics['consumer_terminal']==consumer,'Full current primary table')
        rows=[];groups={};diffs={}
        for mode in ENDS:
            subset=[]
            for j in NEW:
                row=dict(endpoint=mode,index=j,partition='new',**h.independent_frame(packets[mode]['depth'][j],gt[j]))
                compare(row,metrics['per_frame'][len(rows)],mode+'/'+str(j),h,diffs);rows.append(row);subset.append(row)
            groups[mode]=group(subset);compare(groups[mode],metrics['primary_new4'][mode],mode+'/group',h,diffs)
        require(len(metrics['per_frame'])==len(rows)==12 and set(metrics['primary_new4'])==set(ENDS),'No extra/missing primary rows/groups')
        with (SCORE/'per_frame.csv').open(newline='') as f:cr=list(csv.DictReader(f))
        require(len(cr)==12,'Complete12 CSV')
        for row,q in zip(rows,cr):
            require(set(row)==set(q),'Complete CSV columns')
            for k,v in row.items():
                if k in FLOATS:h.metric_match(v,None if q[k]=='' else float(q[k]),'csv/'+k,diffs)
                elif v is None:require(q[k]=='','Null CSV blank')
                elif isinstance(v,int):require(int(q[k])==v,'Exact CSV integer')
                else:require(q[k]==v,'Exact CSV string')
        for p,v in ids.items():require(sha(p)==v,'Input changed during saved review')
        require(time.perf_counter()-timer<=120,'Fixed review wall budget')
        write('recomputed.json',dict(per_frame=rows,primary_new4=groups,trace_reviews=reviews,complete_saved_step_records=steps,
            cross_arm_initial_raw_exact_count=57,matched_initial_decoded_fields=list(decoded),zero_source_exact=True,metric_max_absolute_difference=diffs,
            consumer_status_imported=consumer,consumer_independent_math_review=False,scope='12 new depth scores and saved GA/raw records. No consumer arithmetic review, new GA/backward/clean/k, or old S32/S33 rescoring.'))
        receipt.update(status='PASS_INDEPENDENT_S34_GEOMETRY_SCORE_REVIEW',completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
            rows=12,groups=3,GT_images_decoded=4,cross_arm_initial_raw_tensors=57,validated_arm_boundary_raw_tensors=228,
            saved_optimization_records=800,saved_gradient_records=800,saved_scale_records=800,scale_boundaries=1600,
            metric_max_absolute_difference=diffs,input_sha256=ids,inputs_unchanged=True,consumer_math_independent=False,
            limitations=['Saved gradient norms checked, not recomputed gradients','Parameter object identity and full3x4 per-step gates are producer-recorded','No per-step raw_scales arrays, only raw parameter boundaries and effective-scale logs','Consumer written by this reviewer; its independent numeric review belongs to root'],
            outputs={name:sha(HERE/name) for name in ['attempt.json','input_seal.json','progress.json','recomputed.json']})
        write('receipt.json',receipt);print(json.dumps(dict(status=receipt['status'],rows=12,groups=3)))
    except BaseException:
        receipt.update(status='FAILED_REVIEW_PRESERVED',completed_utc=utc(),error=traceback.format_exc());write('receipt.json',receipt);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binding',required=True);p.add_argument('--sha256',required=True);a=p.parse_args();run(Path(a.binding).resolve(),a.sha256)
