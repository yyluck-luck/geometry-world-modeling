"""Read-only independent source regression audit; invoke only after completion."""
import argparse, ast, copy, hashlib, json, math, textwrap, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

P=Path(__file__).resolve().parents[1]
R=P/'results/S11_source_regression'
VARIANTS=['append_min_missing','drop_last','reverse','only_0','only_0_1_2']
C=Counter()
def ck(v,cat,msg):
    if not v:raise AssertionError(msg)
    C[cat]+=1
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def eq(a,b,cat,msg):
    ck(type(a)is type(b),cat,msg+' type')
    if isinstance(b,dict):
        ck(set(a)==set(b),cat,msg+' keys')
        for k in b:eq(a[k],b[k],cat,msg+'.'+str(k))
    elif isinstance(b,list):
        ck(len(a)==len(b),cat,msg+' length')
        for i,(x,y) in enumerate(zip(a,b)):eq(x,y,cat,msg+f'[{i}]')
    else:ck(a==b,cat,msg+' value')
def aid(a):
    a=np.asarray(a);return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=digest(a.tobytes(order='C')))
def npz(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def arrays_equal(actual,expected,cat):
    ck(set(actual)==set(expected),cat,'array keys')
    for k,a in actual.items():
        b=expected[k]
        ck(a.shape==b.shape,cat,k+' shape');ck(a.dtype==b.dtype,cat,k+' dtype')
        ck(np.isfinite(a).all(),cat,k+' finite')
        ck(a.tobytes(order='C')==b.tobytes(order='C'),cat,k+' exact C bytes')
def memory_hash(a,mapping):
    h=hashlib.sha256(b'S6 normalized memory digest v1\0')
    for i in range(len(a['points'])):
        for v in (a['points'][i],a['normals'][i],[a['radii'][i]]):
            x=np.asarray(v,dtype='<f8');h.update(np.asarray(x.shape,dtype='<i8').tobytes());h.update(x.tobytes())
        h.update(b'color:array\0');x=np.asarray(a['colors'][i],dtype='<f8')
        h.update(np.asarray(x.shape,dtype='<i8').tobytes());h.update(x.tobytes())
    h.update(np.asarray(a['counts'],dtype='<i8').tobytes())
    h.update(json.dumps([[i,mapping[i]] for i in range(len(mapping))],separators=(',',':')).encode())
    return h.hexdigest()
def expected_edit(original,kind):
    result={}
    for i in range(len(original)):
        v=list(original[i])
        if kind=='only_0':v=[0]
        elif kind=='only_0_1_2':v=[0,1,2]
        elif kind=='reverse':v=list(reversed(v))
        elif kind=='drop_last':v=v[:-1] if len(v)>1 else v
        elif kind=='append_min_missing':
            absent=sorted(set(range(20))-set(v))
            if absent:v=v+[absent[0]]
        else:raise ValueError(kind)
        result[i]=v
    return result
def vote_from_buffer(buffer,mapping):
    # Group contributions by first appearance, then fold each source's sequence.
    # The original contributes the first pixel twice; this intentionally retains it.
    contributions={}
    idx=buffer['surfel_index_map'].ravel(order='C')
    cos=buffer['cos_value_map'].ravel(order='C');depth=buffer['depth'].ravel(order='C')
    for i,c,z in zip(idx,cos,depth):
        if i<0 or c<0:continue
        value=c/(1+z)
        for source in mapping[int(i)]:contributions.setdefault(source,[]).append(value)
    ids=list(contributions)
    totals=[]
    for source in ids:
        terms=contributions[source];acc=terms[0]
        for x in terms:acc=acc+x
        totals.append(acc)
    totals=np.asarray(totals);ck(totals.dtype==np.float32,'votes','original accumulator precision')
    weights=totals/np.sum(totals);k=len(ids);n=min(14,k)
    counts=np.zeros(k,dtype=np.int64)
    if k<=14:counts[:]=1
    else:counts[np.argsort(weights)[::-1][:n]]=1
    by_id=sorted(zip(ids,weights,counts))
    return [[int(i),float(w)] for i,w,_ in by_id],[[int(i),int(c)] for i,_,c in by_id]
def replay_nms(decision,counts):
    pool=[i for i,n in counts for _ in range(n)]
    eq(decision['expanded_candidates'],pool,'NMS','expanded candidates')
    distances=decision['distances_float32']
    ck(len(distances)==len(pool) and all(math.isfinite(d) and d>=0 for d in distances),'NMS','recorded distances')
    # Sort only recorded float32 distances; no geometric distance calculation.
    order=torch.argsort(torch.tensor(distances,dtype=torch.float32)).tolist()
    ranked=[pool[i] for i in order];eq(decision['sorted_frames'],ranked,'NMS','ranked saved distances')
    ties=int((np.diff(np.sort(np.asarray(distances,dtype=np.float32)))==0).sum())
    ck(decision['expanded_adjacent_pose_ties']==ties and decision['nms'] is True,'NMS','tie metadata')
    maximum=min(4,len(pool),20);chosen=[ranked[0]];threshold=decision['initial_threshold']
    steps=decision['steps'];cursor=0;pair_values={}
    while len(chosen)<maximum and threshold>=1e-5:
        for frame in ranked[1:]:
            if len(chosen)>=maximum:break
            ck(cursor<len(steps),'NMS','missing comparison step');step=steps[cursor];cursor+=1
            ck(set(step)=={'frame','threshold','comparisons','accepted'} and step['frame']==frame and step['threshold']==threshold,'NMS','comparison step identity')
            comparisons=step['comparisons'];consumed=0;rejected=False
            for previous in chosen:
                ck(consumed<len(comparisons),'NMS','missing pairwise comparison')
                selected,d=comparisons[consumed];consumed+=1
                ck(selected==previous and math.isfinite(d) and d>=0,'NMS','recorded pairwise identity')
                key=(frame,previous)
                if key in pair_values:ck(pair_values[key]==d,'NMS','unchanged repeated pair distance')
                else:pair_values[key]=d
                if d<threshold:rejected=True;break
            ck(consumed==len(comparisons) and step['accepted']==(not rejected),'NMS','accept decision')
            if not rejected:chosen.append(frame)
        if len(chosen)<maximum:
            ck(cursor<len(steps),'NMS','missing relaxation')
            eq(steps[cursor],dict(relax_from=threshold,relax_to=threshold/1.2),'NMS','relaxation')
            cursor+=1;threshold/=1.2
        else:break
    if len(chosen)<maximum:
        additions=[i for i in ranked if i not in chosen][:maximum-len(chosen)]
        ck(cursor<len(steps),'NMS','missing fallback');eq(steps[cursor],dict(fallback_added=additions),'NMS','fallback')
        chosen.extend(additions);cursor+=1
    ck(cursor==len(steps),'NMS','all steps consumed')
    ck(len(chosen)==len(set(chosen))==maximum and all(0<=i<20 for i in chosen),'NMS','native output budget')
    eq(decision['selected'],chosen,'NMS','recorded selected IDs');return chosen
def all_context(selected,c2ws,K):
    return dict(context_c2ws=np.array([c2ws[i] for i in selected],dtype=np.float64),context_latents=np.array([[i] for i in selected],dtype=np.float64),context_encoder_embeddings=np.array([[i+.25] for i in selected],dtype=np.float64),context_Ks=np.array([K for i in selected],dtype=np.float64),context_time_indices=np.array(selected,dtype=np.int64))
def state(a,mapping,poses,c2ws,K,focal,threshold):
    return dict(memory_digest=memory_hash(a,mapping),c2ws=[aid(x) for x in c2ws],Ks=[aid(K)]*20,latents=[aid(np.array([i],dtype=np.float64)) for i in range(20)],encoder_embeddings=[aid(np.array([i+.25],dtype=np.float64)) for i in range(20)],surfel_Ks=[focal]*20,initial_threshold=threshold,target=aid((poses[20]@np.diag([1.,-1.,-1.,1.]))[None]),optical_query=aid(poses[20]))
def signature_from_inputs(a,poses,focal):
    target=poses[20]@np.diag([1.,-1.,-1.,1.])
    # Rebuild the fixed single-pose averaging operation without calling the kernel.
    q=Rotation.from_matrix(target[:3,:3]).as_quat();q=q/np.linalg.norm(q)
    averaged=np.eye(4);averaged[:3,:3]=Rotation.from_quat(q).as_matrix();averaged[:3,3]=target[:3,3]
    averaged[:,[1,2]]*=-1
    raw=dict(positions=a['points'].copy(),normals=a['normals'].copy(),radii=a['radii'].copy(),poses=averaged,focals=np.asarray([np.mean([focal]*20)*.65]*2),principal=np.asarray([80,80]))
    sig={k:aid(v) for k,v in raw.items()};sig.update(width=160,height=160,disk_resolution=16)
    return sig,raw
def check_trace_computation(t,buffer,mapping,expected_threshold):
    weights,counts=vote_from_buffer(buffer,mapping);official=t['official_trace']
    eq(official['weights'],weights,'votes','independent weights');eq(official['candidate_counts'],counts,'votes','independent counts')
    ck(official['visible_sources']==len(weights),'votes','visible sources')
    eq(official['candidates'],[i for i,n in counts if n>0],'votes','official candidates')
    ranked=sorted([np.float32(w) for _,w in weights],reverse=True)
    gap=float(ranked[13]-ranked[14]) if len(ranked)>14 else None
    eq(official['cutoff_gap_14_15'],gap,'votes','cutoff gap')
    ck(official['rendered_coverage']==float((buffer['surfel_index_map']>=0).mean()),'votes','coverage')
    ck(official['nms_initial_threshold']==expected_threshold and t['official_decision']['initial_threshold']==expected_threshold,'NMS','threshold identity')
    selected=replay_nms(t['official_decision'],counts)
    eq(official['selected'],selected,'NMS','official selected');eq(t['returned_ids'],selected,'NMS','actual return')
    return selected
def zip_check(path,expected):
    with zipfile.ZipFile(path) as z:
        ck(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(expected),'archive','exact members')
        ck(z.testzip() is None,'archive','CRC')
        for name,h in expected.items():
            ck(not Path(name).is_absolute() and '..' not in Path(name).parts,'archive','safe path')
            ck(digest(z.read(name))==h,'archive','member SHA '+name)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    args.output.mkdir(exist_ok=False);OUT=args.output;START=datetime.now(timezone.utc).isoformat()
    try:
        meta=read(R/'run_metadata.json');ck(meta['status']=='completed','metadata','source experiment must be completed')
        # Imports below occur only in this explicitly invoked completed-result audit.
        import numpy as np
        import torch
        from scipy.spatial.transform import Rotation
        ck(np.__version__=='2.3.5','metadata','fixed NumPy precision')
        freeze=read(P/'docs/S11_SOURCE_REGRESSION_EXECUTION_FREEZE.json');prior=read(P/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json')
        ck(sha(P/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json')==freeze['s10_freeze_sha256']=='db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204','integrity','fixed predecessor freeze')
        ck(sha(P/'docs/S11_SOURCE_REGRESSION_EXECUTION_FREEZE.json')==meta['freeze_sha256'],'integrity','freeze SHA')
        ck(sha(P/'docs/S11_SOURCE_REGRESSION_PROTOCOL.md')==meta['protocol_sha256']==freeze['protocol_sha256'],'integrity','protocol SHA')
        ck(datetime.fromisoformat(freeze['frozen_utc'])<datetime.fromisoformat(meta['started_utc'])<datetime.fromisoformat(meta['completed_utc']),'metadata','chronology')
        eq(meta['contract'],freeze['contract'],'metadata','contract');eq(freeze['input_sha256'],prior['input_sha256'],'integrity','same52inputs')
        ck(len(freeze['input_sha256'])==52 and len(freeze['execution_source_sha256'])==13,'integrity','input/source counts')
        protected={}
        for key in ['input_sha256','execution_source_sha256','review_evidence_sha256']:
            for name,h in freeze[key].items():
                path=P/name;ck(path.is_file() and not path.is_symlink(),'integrity','regular '+name)
                ck(sha(path)==h,'integrity','SHA '+name);protected[name]=h
        for name,h in prior['execution_source_sha256'].items():ck(freeze['execution_source_sha256'][name]==h,'integrity','old source unchanged')
        for kind in ['input','source']:eq(meta[kind+'_sha256'],freeze['input_sha256' if kind=='input' else 'execution_source_sha256'],'integrity','metadata identity '+kind)
        zip_check(R/'inputs.zip',freeze['input_sha256']);zip_check(R/'review_evidence.zip',freeze['review_evidence_sha256'])
        zip_check(R/'sources.zip',{**freeze['execution_source_sha256'],'execution_freeze.json':meta['freeze_sha256'],'protocol.md':meta['protocol_sha256'],'S10_execution_freeze.json':sha(P/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json')})
        adapter=read(R/'source_trace_adapter.json');original=ast.parse(adapter['original_source']);adapted=ast.parse(adapter['adapted_source'])
        text=(P/'src/s7_event_replay.py').read_text();tree=ast.parse(text);f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='decision_trace')
        expected=ast.parse(textwrap.dedent(''.join(text.splitlines(keepends=True)[f.lineno-1:f.end_lineno])))
        ck(ast.dump(expected)==ast.dump(original),'adapter_AST','original recorder identity')
        guard=adapted.body[0].body[-2]
        ck(isinstance(guard,ast.If),'adapter_AST','terminal guard')
        for comp in guard.test.values[:2]:
            ck(isinstance(comp.comparators[0],ast.Name) and comp.comparators[0].id=='maximum','adapter_AST','replacement name')
            comp.comparators[0]=ast.Constant(value=4)
        ck(ast.dump(adapted)==ast.dump(original) and adapter['changed_terminal_check_constants']==2 and adapter['restored_full_AST_identical'] is True,'adapter_AST','only2constants')
        # The frozen candidate transform has the exact same original/helper identities.
        transform=read(R/'renderer_transformation.json')
        ck(transform['helper_source_sha256']==freeze['execution_source_sha256']['src/s10_vectorized_renderer.py'] and transform['original_source_sha256']==freeze['execution_source_sha256']['src/vmem_retrieval_kernel.py'] and transform['restored_full_method_ast_identical'] is True and transform['replaced_nested_pixel_loops']==1,'adapter_AST','candidate transform')
        conditions=read(R/'conditions.json');negative=read(R/'negative_controls.json')
        ck(len(conditions)==30 and len(negative)==18,'coverage','condition/control counts')
        manifest=read(R/'artifact_manifest.json');actual_names={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and p.name not in ['run_metadata.json','artifact_manifest.json']}
        ck(set(manifest)==actual_names,'integrity','artifact manifest domain')
        for name,item in manifest.items():ck(sha(R/name)==item['sha256'] and (R/name).stat().st_size==item['bytes'],'integrity','artifact '+name)
        expected_names={'sources.zip','inputs.zip','review_evidence.zip','source_trace_adapter.json','renderer_transformation.json','conditions.json','negative_controls.json','summary.json'}
        report_rows=[];nms_traces=0;old_buffers=0
        fx,fy,cx,cy=525.*299/640,525.*224/480,(319.5+.5)*299/640-.5-37,(239.5+.5)*224/480-.5
        scale=160/224.;focal=float((fx+fy)/2*scale);K=np.array([[fx*scale,0,cx*scale],[0,fy*scale,cy*scale],[0,0,1.]])
        for stage,run in [('S7','results/S7_event_replay'),('S8','results/S8_event_replay_v2')]:
            oldmeta=read(P/run/'run_metadata.json')
            for block in range(3):
                base=P/run/f'block{block}_stride8';label=f'{stage}_block{block}_query20';folder=R/label
                a=npz(base/'A0P0.npz');poses=npz(base/'predicted_poses.npz')['poses'];buffer=npz(base/'query20_A0P0_render.npz');old_buffers+=1
                mapping={int(k):v for k,v in read(base/'A0P0_sources.json').items()};sel=read(base/'prediction_only_selection.json');entry=next(q for q in sel['queries'] if q['frame']==20)['maps']['A0P0']
                ck(set(mapping)==set(range(len(a['points']))),'mapping','base source key domain')
                for ids in mapping.values():ck(ids and len(ids)==len(set(ids)) and all(type(x)is int and 0<=x<20 for x in ids),'mapping','source legality')
                ck(memory_hash(a,mapping)==sel['maps']['A0P0']['digest'],'state','original memory')
                seals=next(c for c in oldmeta['cases'] if c['block']==block and c['stride']==8)['sealed_files']
                for file in ['A0P0.npz','A0P0_sources.json','predicted_poses.npz','query20_A0P0_render.npz','prediction_only_selection.json']:ck(sha(base/file)==seals[file],'integrity','old case seal')
                ck(np.any((buffer['surfel_index_map']>=0)&(buffer['cos_value_map']>0)),'votes','positive valid vote pixel')
                c2ws=[p@np.diag([1.,-1.,-1.,1.]) for p in poses[:20]]
                sig,raw=signature_from_inputs(a,poses,focal);eq(read(folder/'render_argument_identity.json'),sig,'guard','reconstructed render argument identity')
                expected_names|={label+'/render_argument_identity.json',label+'/baseline_replay_trace.json'}
                baseline=read(folder/'baseline_replay_trace.json')
                eq(baseline['official_trace'],entry['official_trace'],'baseline','old full official trace');eq(baseline['official_decision'],entry['readouts']['official'],'baseline','old full decision trace')
                base_selected=check_trace_computation(baseline,buffer,mapping,entry['official_trace']['nms_initial_threshold']);nms_traces+=1
                eq(baseline['render_arrays'],{k:aid(v) for k,v in buffer.items()},'baseline','baseline render identities')
                eq(baseline['result_arrays'],{k:aid(v) for k,v in all_context(base_selected,c2ws,K).items()},'baseline','baseline context identities')
                for kind,field,index in [('camera','poses',(0,3)),('geometry','positions',(0,0)),('focal','focals',(0,))]:
                    wrong=raw[field].copy();wrong[index]+=1e-3
                    row=negative[len(report_rows)//5*3+['camera','geometry','focal'].index(kind)]
                    expected_negative=dict(label=label,kind=kind,rejected=True,reason='Historical buffer replay rejected changed renderer inputs',signature_differences={field:dict(expected=sig[field],actual=aid(wrong))})
                    eq(row,expected_negative,'guard_negative','fixed negative identity')
                for variant in VARIANTS:
                    vf=folder/variant;edited=expected_edit(mapping,variant);stored={int(k):v for k,v in read(vf/'mapping.json').items()}
                    eq(stored,edited,'mapping','deterministic source rule')
                    changed=sum(edited[i]!=mapping[i] for i in mapping);ck(changed>0,'mapping','nonvacuous edit')
                    expected_state=state(a,edited,poses,c2ws,K,focal,entry['official_trace']['nms_initial_threshold'])
                    expected_names.add(label+'/'+variant+'/mapping.json');methods={}
                    for method in ['reference_replay','candidate']:
                        mf=vf/method;render=npz(mf/'render.npz');context=npz(mf/'context.npz');tr=read(mf/'trace.json');ident=read(mf/'state_identity.json')
                        expected_names|={label+'/'+variant+'/'+method+'/'+n for n in ['render.npz','context.npz','trace.json','state_identity.json']}
                        arrays_equal(render,buffer,'render_arrays')
                        selected=check_trace_computation(tr,buffer,edited,entry['official_trace']['nms_initial_threshold']);nms_traces+=1
                        arrays_equal(context,all_context(selected,c2ws,K),'context_arrays')
                        eq(tr['render_arrays'],{k:aid(v) for k,v in render.items()},'render_arrays','trace render bytes')
                        eq(tr['result_arrays'],{k:aid(v) for k,v in context.items()},'context_arrays','trace context bytes')
                        eq(ident,dict(before=expected_state,after=expected_state),'state','reconstructed before and after')
                        methods[method]=(render,context,tr)
                    eq(methods['reference_replay'][2],methods['candidate'][2],'pair','complete same-condition trace')
                    arrays_equal(methods['candidate'][1],methods['reference_replay'][1],'pair_context_arrays')
                    tr=methods['candidate'][2];selected=tr['returned_ids']
                    if variant=='only_0':ck(selected==[0],'coverage','one-source result')
                    if variant=='only_0_1_2':ck(len(selected)==3 and set(selected)=={0,1,2},'coverage','three-source result')
                    stale=(tr['official_trace']!=baseline['official_trace'] or tr['official_decision']!=baseline['official_decision'])
                    row=dict(label=label,variant=variant,changed_mapping_rows=changed,selected_ids=selected,visible_sources=tr['official_trace']['visible_sources'],stale_original_mapping_trace_rejected=stale,selected_order_changed_from_original=selected!=base_selected,exact_render_and_full_trace=True,folder=label+'/'+variant)
                    eq(conditions[len(report_rows)],row,'coverage','actual condition summary');report_rows.append(row)
        ck(expected_names==actual_names and len(expected_names)==290,'coverage','exact output inventory')
        expected_summary=dict(conditions=30,new_candidate_renders=30,reference_buffer_replays=36,base_maps=6,base_queries=6,groups={v:dict(conditions=6,exact_pass=6,stale_trace_rejected=sum(r['variant']==v and r['stale_original_mapping_trace_rejected'] for r in report_rows),selected_order_changed=sum(r['variant']==v and r['selected_order_changed_from_original'] for r in report_rows)) for v in VARIANTS},replay_invalid_argument_controls_rejected=18,speed_measurement=False)
        eq(read(R/'summary.json'),expected_summary,'summary','independent summary')
        stale18=sum(r['variant'] in VARIANTS[:3] and r['stale_original_mapping_trace_rejected'] for r in report_rows)
        ck(stale18>=1,'guard_negative','original18 stale gate')
        for key,val in dict(conditions_passed=30,new_candidate_renders=30,reference_buffer_replays=36,frozen_files_unchanged=True,initial_and_final_input_states_equal=True,original_renderer_calls=0,torch_threads=8,torch_interop_threads=8).items():ck(meta[key]==val,'metadata','completed '+key)
        for name,h in protected.items():ck(sha(P/name)==h,'integrity','end unchanged '+name)
        receipt=dict(status='PASS',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=sum(C.values()),checks_by_category=dict(C),conditions=30,actual_render_npz=60,actual_context_npz=60,original_buffers=old_buffers,render_arrays_checked=180,context_arrays_against_rebuilt_expected=300,pair_context_arrays_compared=150,full_trace_pairs=30,baselines_against_old_trace=6,vote_reconstructions_and_recorded_distance_NMS_replays=nms_traces,guard_negatives=18,stale18_rejected=stale18,groups=expected_summary['groups'],adapter_constants_changed=2,full_states_reconstructed=60,before_after_identities_checked=120,output_payload_files=290,source_sha256=freeze['execution_source_sha256'],freeze_sha256=meta['freeze_sha256'],run_metadata_sha256=sha(R/'run_metadata.json'),limitations=['No renderer or actual get_context_info/production verifier invoked. Votes independently folded from original buffer and edited mapping; NMS replays recorded distances, not geometric recomputation.','Baseline replay has saved trace/array identities but no separate baseline NPZ; 60 render/context NPZ apply only to paired30conditions.','Recorded guard expectations and mutations reconstructed; actual per-call render argument tensors/signatures are not separately archived. Guard execution is supported by frozen source and recorded completion.','States are identity summaries, not full runtime tensors independently observed.','Artificial source controls on six seen map/query bases, not actual update trajectories, cache hit rates, timing, video or novelty.'])
        (OUT/'independent_conditions.json').write_text(json.dumps(report_rows,indent=2)+'\n')
    except Exception as e:
        receipt=dict(status='FAIL',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=sum(C.values()),checks_by_category=dict(C),error=repr(e))
    (OUT/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    (OUT/'reviewer_snapshot.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(receipt,ensure_ascii=False,indent=2))
    if receipt['status']!='PASS':raise SystemExit(1)
