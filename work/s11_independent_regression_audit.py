"""Different-author saved-evidence audit; no production imports or execution."""
import ast, csv, hashlib, json, re, textwrap, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

P=Path(__file__).resolve().parents[1]
R=P/'results/S11_renderer_regression'
OUT=P/'results/S11_renderer_regression_independent_audit'
OUT.mkdir(exist_ok=False)
START=datetime.now(timezone.utc).isoformat()
C=Counter(); TOTAL_TRACE_LEAVES=0
def ck(value,category,message):
    if not value: raise AssertionError(message)
    C[category]+=1
def j(path): return json.loads(path.read_text())
def digest(data): return hashlib.sha256(data).hexdigest()
def sha(path): return digest(path.read_bytes())
def aid(a): return dict(shape=list(a.shape),dtype=str(a.dtype),sha256=digest(a.tobytes(order='C')))
def leaves(x):
    if isinstance(x,dict): return sum(leaves(v) for v in x.values())
    if isinstance(x,list): return sum(leaves(v) for v in x)
    return 1
def eq(a,b,category,label):
    ck(type(a) is type(b),category,label+' type')
    if isinstance(b,dict):
        ck(set(a)==set(b),category,label+' keys')
        for k in b: eq(a[k],b[k],category,label+'.'+k)
    elif isinstance(b,list):
        ck(len(a)==len(b),category,label+' length')
        for i,(x,y) in enumerate(zip(a,b)):eq(x,y,category,label+f'[{i}]')
    else: ck(a==b,category,label+' value')
def npz(path):
    with np.load(path,allow_pickle=False) as z: return {k:z[k] for k in z.files}
def memory_digest(a,mapping):
    h=hashlib.sha256(b'S6 normalized memory digest v1\0')
    for i in range(len(a['points'])):
        for v in (a['points'][i],a['normals'][i],[a['radii'][i]]):
            x=np.asarray(v,dtype='<f8');h.update(np.asarray(x.shape,dtype='<i8').tobytes());h.update(x.tobytes())
        h.update(b'color:array\0'); x=np.asarray(a['colors'][i],dtype='<f8')
        h.update(np.asarray(x.shape,dtype='<i8').tobytes());h.update(x.tobytes())
    h.update(np.asarray(a['counts'],dtype='<i8').tobytes())
    h.update(json.dumps([[i,mapping[i]] for i in range(len(mapping))],separators=(',',':')).encode())
    return h.hexdigest()
def zip_matches(name,expected):
    with zipfile.ZipFile(R/name) as z:
        names=z.namelist()
        ck(len(names)==len(set(names)) and set(names)==set(expected),'archive',name+' member domain')
        ck(z.testzip() is None,'archive',name+' CRC')
        for n,h in expected.items():
            ck(not Path(n).is_absolute() and '..' not in Path(n).parts,'archive','safe member '+n)
            ck(digest(z.read(n))==h,'archive','member SHA '+n)

try:
    meta=j(R/'run_metadata.json'); freeze=j(P/'docs/S11_RENDERER_REGRESSION_EXECUTION_FREEZE.json')
    prior=j(P/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json')
    ck(meta['status']=='completed' and meta['phase']=='complete','metadata','completed')
    ck(sha(P/'docs/S11_RENDERER_REGRESSION_EXECUTION_FREEZE.json')==meta['freeze_sha256'],'integrity','freeze')
    ck(sha(P/'docs/S11_RENDERER_REGRESSION_PROTOCOL.md')==meta['protocol_sha256']==freeze['protocol_sha256'],'integrity','protocol')
    ck(sha(P/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json')==meta['s10_freeze_sha256']==freeze['s10_freeze_sha256'],'integrity','S10 freeze')
    contract=json.loads(re.findall(r'```s11-regression-json\s*\n(.*?)\n```',(P/'docs/S11_RENDERER_REGRESSION_PROTOCOL.md').read_text(),re.S)[0])
    eq(meta['contract'],contract,'metadata','contract')
    ck(datetime.fromisoformat(freeze['frozen_utc'])<datetime.fromisoformat(meta['started_utc'])<datetime.fromisoformat(meta['completed_utc']),'metadata','chronology')
    planned=[]; input_names=[]
    RUNS={'S7':'results/S7_event_replay','S8':'results/S8_event_replay_v2'}
    for stage,run in RUNS.items():
        input_names += [run+'/run_metadata.json',run+'/records.json']
        for block in range(3):
            for stride in (8,12):
                base=f'{run}/block{block}_stride{stride}'
                input_names += [base+'/predicted_poses.npz',base+'/prediction_only_selection.json']
                for arm in ('A0P0','A0P1','A1P0','A1P1'):
                    input_names += [base+'/'+arm+'.npz',base+'/'+arm+'_sources.json']
                    for query in range(20,24):
                        input_names += [base+f'/query{query}_{arm}_render.npz']
                        planned.append(dict(condition_index=len(planned),stage=stage,block=block,stride=stride,arm=arm,query=query,label=f'{stage}_block{block}_stride{stride}_{arm}_query{query}',evidence='inherited_S10' if stride==8 and arm=='A0P0' else 'new_candidate'))
    ck(len(set(input_names))==len(input_names)==316,'coverage','input domain')
    ck(set(input_names)==set(freeze['input_sha256']),'coverage','frozen input domain')
    eq(j(R/'schedule.json'),planned,'coverage','schedule')
    oldrows=[json.loads(s) for s in (P/'results/S10_renderer_comparison/invocations.jsonl').read_text().splitlines()]
    oldmeta=j(P/'results/S10_renderer_comparison/run_metadata.json')
    ck(len(oldrows)==336 and oldmeta['status']=='completed','inherited','S10 completeness')
    evidence_names=['results/S10_renderer_comparison/'+x for x in ('run_metadata.json','invocations.jsonl','schedule.json','call_artifact_manifest.json','renderer_transformation.json','comparison_source.zip','sealed_comparison_inputs.zip','summary.json')]
    oldchosen={}
    for row in oldrows:
        ck(row['exact_regression_passed'] is True,'inherited','old invocation gate')
        for kind in ('render','trace'): evidence_names.append('results/S10_renderer_comparison/'+row[kind+'_path'])
        if row['phase']=='correctness' and row['method']=='candidate':
            key=(row['stage'],row['block'],row['query']);ck(key not in oldchosen,'inherited','no repeated inherited identity');oldchosen[key]=row
    evidence_names += ['results/S10_renderer_comparison_independent_review/verification.json','results/S10_renderer_comparison_audit_v2/verification.json']
    ck(len(evidence_names)==len(set(evidence_names))==682 and set(evidence_names)==set(freeze['s10_evidence_sha256']),'inherited','full S10 evidence domain')
    ck(j(P/evidence_names[-2])['status']=='PASS' and j(P/evidence_names[-1])['status']=='passed','inherited','prior audits')
    all_frozen={}
    for key,count in [('execution_source_sha256',13),('input_sha256',316),('s10_evidence_sha256',682),('review_evidence_sha256',4)]:
        ck(len(freeze[key])==count,'integrity',key+' count');eq(meta[key],freeze[key],'integrity',key)
        for name,h in freeze[key].items():
            path=P/name
            ck(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(P),'integrity',name+' regular')
            ck(sha(path)==h,'integrity',name+' SHA'); all_frozen[name]=h
    for name,h in prior['input_sha256'].items():ck(freeze['input_sha256'][name]==h,'integrity','old52 '+name)
    for name,h in prior['execution_source_sha256'].items():ck(freeze['execution_source_sha256'][name]==h,'integrity','old12 '+name)
    source_zip={**freeze['execution_source_sha256'],'frozen_protocol.md':meta['protocol_sha256'],'execution_freeze.json':meta['freeze_sha256'],'S10_execution_freeze.json':meta['s10_freeze_sha256']}
    for filename,key,expected in [('regression_source.zip','source_archive_sha256',source_zip),('sealed_regression_inputs.zip','input_archive_sha256',freeze['input_sha256']),('inherited_S10_evidence.zip','s10_evidence_archive_sha256',freeze['s10_evidence_sha256']),('sealed_review_evidence.zip','review_evidence_archive_sha256',freeze['review_evidence_sha256'])]:
        ck(sha(R/filename)==meta[key],'archive',filename+' outer SHA');zip_matches(filename,expected)
    for file,key in [('call_artifact_manifest.json','call_artifact_manifest_sha256'),('coverage.json','coverage_sha256'),('summary.json','summary_sha256'),('renderer_transformation.json','renderer_transformation_sha256'),('initial_state_identities.json','initial_state_identities_sha256')]:
        ck(sha(R/file)==meta[key],'integrity',file)
    transform=j(R/'renderer_transformation.json');eq(transform,j(P/'results/S10_renderer_comparison/renderer_transformation.json'),'source_AST','same frozen transform')
    original_tree=ast.parse(transform['original_method']);candidate_tree=ast.parse(transform['transformed_method'])
    source_lines=(P/'src/vmem_retrieval_kernel.py').read_text().splitlines(keepends=True)
    cl=next(x for x in ast.parse(''.join(source_lines)).body if isinstance(x,ast.ClassDef))
    fn=next(x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name=='render_surfels_to_image')
    exact_source=ast.parse(textwrap.dedent(''.join(source_lines[fn.lineno-1:fn.end_lineno])))
    ck(ast.dump(original_tree)==ast.dump(exact_source),'source_AST','original method identity')
    oldloop=next(x for x in ast.walk(original_tree) if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='py_')
    replaced=[]
    class Restore(ast.NodeTransformer):
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='_s10_raster_patch':
                replaced.append(node);return oldloop
            return self.generic_visit(node)
    restored=Restore().visit(candidate_tree)
    ck(len(replaced)==1 and ast.dump(restored)==ast.dump(original_tree),'source_AST','only pixel loop differs')
    initial=j(R/'initial_state_identities.json'); rows=[json.loads(x) for x in (R/'invocations.jsonl').read_text().splitlines()]
    inherited=j(R/'inherited_coverage.json'); coverage=j(R/'coverage.json')
    newplan=[p for p in planned if p['evidence']=='new_candidate'];oldplan=[p for p in planned if p['evidence']=='inherited_S10']
    ck(len(rows)==168 and len(inherited)==24 and len(coverage)==192,'coverage','192=168+24')
    ck(set(initial)=={x['label'] for x in newplan},'state','initial state domain')
    eq(coverage,sorted(inherited+rows,key=lambda x:x['condition_index']),'coverage','coverage actual records')
    manifest=j(R/'call_artifact_manifest.json');inv={x['path']:x for x in manifest}
    ck(len(manifest)==len(inv)==336,'integrity','new manifest count')
    expected_call_paths={f"calls/{p['label']}/{n}" for p in newplan for n in ('render.npz','trace.json')}
    actual_paths={str(x.relative_to(R)) for x in (R/'calls').rglob('*') if x.is_file()}
    ck(set(inv)==actual_paths==expected_call_paths,'integrity','new actual call inventory')
    for name,item in inv.items():
        ck(sha(R/name)==item['sha256'] and (R/name).stat().st_size==item['bytes'],'integrity','new call artifact '+name)
    case_refs={}; maps={}; map_stats=[]; expected_states={}
    fx,fy,cx,cy=525.*299/640,525.*224/480,(319.5+.5)*299/640-.5-37,(239.5+.5)*224/480-.5
    scale=160/224.; K=np.array([[fx*scale,0,cx*scale],[0,fy*scale,cy*scale],[0,0,1.]])
    for stage,run in RUNS.items():
        old=j(P/run/'run_metadata.json');records=j(P/run/'records.json')
        rec={(r['block'],r['stride'],r['frame']):r for r in records}
        ck(len(rec)==24,'original_maps','old record domain')
        for block in range(3):
            for stride in (8,12):
                base=P/run/f'block{block}_stride{stride}';sel=j(base/'prediction_only_selection.json')
                seals=[x for x in old['cases'] if x['block']==block and x['stride']==stride]
                ck(len(seals)==1,'original_maps','case seal identity')
                for path in base.iterdir():
                    name=str(path.relative_to(P))
                    if name in freeze['input_sha256']:ck(seals[0]['sealed_files'][path.name]==freeze['input_sha256'][name],'original_maps','historical seal '+name)
                pose_archive=npz(base/'predicted_poses.npz');ck(set(pose_archive)=={'poses'},'state','pose schema');poses=pose_archive['poses']
                ck(poses.shape==(24,4,4) and poses.dtype==np.float64 and np.isfinite(poses).all(),'state','original pose arrays')
                c2ws=[np.asarray(a,dtype=np.float64)@np.diag([1.,-1.,-1.,1.]) for a in poses[:20]]
                for arm in ('A0P0','A0P1','A1P0','A1P1'):
                    key=(stage,block,stride,arm);a=npz(base/f'{arm}.npz');mapping={int(k):v for k,v in j(base/f'{arm}_sources.json').items()}
                    ck(set(a)=={'points','normals','radii','colors','counts'},'original_maps','map schema')
                    n=len(a['points']);ck(set(mapping)==set(range(n)),'original_maps','source key domain')
                    ck(a['points'].shape==a['normals'].shape==a['colors'].shape==(n,3) and a['radii'].shape==a['counts'].shape==(n,),'original_maps','map shapes')
                    for value in a.values():ck(np.isfinite(value).all(),'original_maps','map finite')
                    for ids in mapping.values():ck(ids and len(ids)==len(set(ids)) and all(type(t)is int and 0<=t<20 for t in ids),'original_maps','valid sources')
                    mdig=memory_digest(a,mapping);ck(mdig==sel['maps'][arm]['digest'],'original_maps','independent memory digest')
                    maps[key]=a; map_stats.append(dict(stage=stage,block=block,stride=stride,arm=arm,points=n,memory_digest=mdig,inherited_map=(stride==8 and arm=='A0P0')))
                    for q in range(20,24):
                        query=[x for x in sel['queries'] if x['frame']==q];ck(len(query)==1,'coverage','original query unique'); expected=query[0]['maps'][arm]
                        eq(expected['official_trace']['selected'],rec[(block,stride,q)]['readouts'][arm]['official']['selected'],'trace','old record IDs')
                        case_refs[(*key,q)]=(base/f'query{q}_{arm}_render.npz',expected)
                        label=f'{stage}_block{block}_stride{stride}_{arm}_query{q}'
                        if stride==8 and arm=='A0P0':continue
                        expected_states[label]=dict(memory_digest=mdig,c2ws=[aid(v) for v in c2ws],Ks=[aid(K) for _ in range(20)],latents=[aid(np.asarray([i],dtype=np.float64)) for i in range(20)],encoder_embeddings=[aid(np.asarray([i+.25],dtype=np.float64)) for i in range(20)],surfel_Ks=[float((fx+fy)/2*scale)]*20,initial_threshold=expected['official_trace']['nms_initial_threshold'],target=aid((np.asarray(poses[q])@np.diag([1.,-1.,-1.,1.]))[None]),optical_query=aid(poses[q]))
    ck(len(maps)==48 and len(case_refs)==192,'coverage','all maps and old references')
    eq(initial,expected_states,'state','independent initial state reconstruction')
    audit_coverage=[];array_pairs=0
    for cond in planned:
        key=tuple(cond[k] for k in ('stage','block','stride','arm','query'));refpath,expected=case_refs[key]
        if cond['evidence']=='new_candidate':
            i=len([x for x in audit_coverage if x['evidence']=='new_candidate']);row=rows[i]
            for k,v in cond.items():ck(row[k]==v,'coverage','new row '+k)
            ck(row['invocation_index']==i and row['method']=='candidate' and row['status']=='passed','coverage','new call identity')
            ck(not any(k.endswith('_ns') or 'elapsed' in k for k in row),'metadata','no per-call timing')
            actualrender=R/row['render_path'];actualtrace=R/row['trace_path']
        else:
            i=len([x for x in audit_coverage if x['evidence']=='inherited_S10']);row=inherited[i]
            for k,v in cond.items():ck(row[k]==v,'inherited','inherited identity '+k)
            old=oldchosen[(cond['stage'],cond['block'],cond['query'])]
            ck(row['prior_pair_index']==old['pair_index'] and row['new_renderer_call'] is False and row['prior_phase']=='correctness' and row['prior_method']=='candidate','inherited','inherited phase')
            for kind in ('render','trace'):ck(row[kind+'_path']=='results/S10_renderer_comparison/'+old[kind+'_path'] and row[kind+'_sha256']==old[kind+'_sha256'],'inherited','inherited chosen artifact')
            actualrender=P/row['render_path'];actualtrace=P/row['trace_path']
        ck(sha(actualrender)==row['render_sha256'] and sha(actualtrace)==row['trace_sha256'],'integrity','row artifact SHA')
        actual=npz(actualrender);reference=npz(refpath)
        ck(set(actual)==set(reference)=={'depth','surfel_index_map','cos_value_map'},'arrays','render schema')
        for k in reference:
            ck(actual[k].shape==reference[k].shape==(160,160),'arrays','shape')
            ck(actual[k].dtype==reference[k].dtype==np.dtype('int32' if k=='surfel_index_map' else 'float32'),'arrays','dtype')
            ck(np.isfinite(actual[k]).all(),'arrays','finite')
            ck(actual[k].tobytes(order='C')==reference[k].tobytes(order='C'),'arrays','exact C bytes')
            array_pairs+=1
        ck(((actual['surfel_index_map']>=-1)&(actual['surfel_index_map']<len(maps[key[:4]]['points']))).all(),'arrays','valid surfel index')
        t=j(actualtrace)
        ck(t['status']=='passed','trace','trace status')
        eq(t['official_trace'],expected['official_trace'],'trace','full official trace')
        eq(t['official_decision'],expected['readouts']['official'],'trace','full decision trace')
        TOTAL_TRACE_LEAVES+=leaves(expected['official_trace'])+leaves(expected['readouts']['official'])
        eq(t['returned_ordered_ids'],expected['official_trace']['selected'],'trace','actual ordered return')
        eq(t['observed_weights'],expected['official_trace']['weights'],'trace','actual vote weights')
        eq(t['observed_counts'],expected['official_trace']['candidate_counts'],'trace','actual counts')
        eq(t['render_arrays'],{k:aid(a) for k,a in actual.items()},'arrays','trace actual array identities')
        if cond['evidence']=='new_candidate':
            eq(t['state_after'],expected_states[cond['label']],'state','after vs rebuilt initial')
            ck(t['state_before_sha256']==digest(json.dumps(initial[cond['label']],sort_keys=True).encode()),'state','before JSON hash')
        audit_coverage.append(dict(**cond,status='passed',actual_render_sha256=sha(actualrender),reference_render_sha256=sha(refpath),valid_pixels=int((actual['surfel_index_map']>=0).sum()),selected=t['returned_ordered_ids']))
    ck(array_pairs==576,'coverage','168+24 times3 arrays')
    ck(len({(x['stage'],x['block'],x['query']) for x in audit_coverage})==24,'coverage','distinct original queries')
    ck(len({(x['stage'],x['block'],x['stride'],x['arm']) for x in newplan})==42,'coverage','new maps')
    summary=j(R/'summary.json')
    for k,v in dict(status='passed',full_conditions=192,new_candidate_invocations=168,inherited_conditions=24,distinct_seen_queries=24,physical_scenes=2,original_map_variants=48,new_candidate_maps=42,all_exact_output_checks_passed=True,performance_measured=False).items():ck(summary[k]==v,'metadata','summary '+k)
    eq(summary['limitations'],meta['limitations'],'metadata','limitations')
    for k,v in dict(completed_new_invocations=168,inherited_conditions=24,covered_conditions=192,distinct_seen_queries=24,new_candidate_maps=42,original_renderer_calls=0,performance_measured=False,raw_pixels_decoded=False,gt_loaded=False,model_loaded=False,in_memory_inputs_unchanged=True,all_actual_arrays_and_complete_traces_saved=True).items():ck(meta[k]==v,'metadata','run '+k)
    for name,h in all_frozen.items():ck(sha(P/name)==h,'integrity','end unchanged '+name)
    receipt=dict(status='PASS',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=sum(C.values()),checks_by_category=dict(C),new_actual_render_npz=168,inherited_actual_render_npz=24,original_reference_npz=192,exact_array_pairs=array_pairs,new_complete_traces=168,inherited_complete_traces=24,complete_official_and_decision_trace_scalar_leaves=TOTAL_TRACE_LEAVES,original_map_variants_decoded=48,new_state_identities_reconstructed=168,original_input_files=316,inherited_evidence_files=682,execution_sources=13,archive_members_checked=16+316+682+4,scope='Different-author saved-artifact/coverage/state audit; no production verifier import, renderer/selector/vote/NMS/model/timing rerun. Full old trace equality, not fresh algorithmic vote reconstruction. initial_threshold taken from old sealed trace, not recomputed pose distance.',run_started_utc=meta['started_utc'],run_completed_utc=meta['completed_utc'],run_wall_elapsed_for_budget_seconds=meta['wall_elapsed_for_budget_seconds'],run_peak_rss_bytes=meta['process_peak_rss_bytes'],freeze_sha256=meta['freeze_sha256'],run_metadata_sha256=sha(R/'run_metadata.json'),invocations_sha256=sha(R/'invocations.jsonl'),coverage_sha256=sha(R/'coverage.json'),limitations=['States are stored hashes reconstructed against frozen inputs, not full live post-call tensor dumps or independent runtime observation.','S10 24 output buffers/traces reopened; remaining S10 evidence checked for identity, not all 336 arrays rerun or redecode.','No speed ratios inferred from wall budget time.','192 map-query conditions refer to24 related already-seen queries/two scenes; finite correctness evidence, not formal all-input proof or novelty.'])
    (OUT/'independent_coverage.json').write_text(json.dumps(audit_coverage,indent=2)+'\n')
    (OUT/'original_map_inventory.json').write_text(json.dumps(map_stats,indent=2)+'\n')
except Exception as e:
    receipt=dict(status='FAIL',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=sum(C.values()),checks_by_category=dict(C),error=repr(e))
(OUT/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(OUT/'reviewer_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(receipt,ensure_ascii=False,indent=2))
if receipt['status']!='PASS':raise SystemExit(1)
