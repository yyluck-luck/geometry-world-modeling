"""Independent post-completion review; never imports either renderer or runner."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
checks=Counter()
def check(value,label,category='metadata'):
    checks[category]+=1
    assert value,label
def digest(p):
    b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def median(v):
    a=sorted(v);m=len(a)//2
    return a[m] if len(a)%2 else (a[m-1]+a[m])/2
def compare(got,expected,path='summary'):
    if isinstance(expected,dict):
        check(set(got)==set(expected),path+' keys','summary')
        for k in expected:compare(got[k],expected[k],path+'/'+k)
    elif isinstance(expected,list):
        check(len(got)==len(expected),path+' length','summary')
        for i,(a,b) in enumerate(zip(got,expected)):compare(a,b,path+'/'+str(i))
    else:check(got==expected,path,'summary')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();out=a.out.resolve()
    metadata=json.loads((run/'run_metadata.json').read_text())
    check(metadata['status']=='completed' and metadata['phase']=='complete','Run must be completed before any scans')
    out.mkdir(parents=True,exist_ok=False)
    began=datetime.now(timezone.utc).isoformat()
    receipt={'status':'running','started_utc':began,'scope':'Independent saved-data and integer-timing audit; no renderer, selector, model, PNG, GT or timer rerun.'}
    try:
        import numpy as np
        freeze_path=ROOT/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json'
        freeze=json.loads(freeze_path.read_text())
        protocol=ROOT/'docs/S10_RENDERER_COMPARISON_PROTOCOL.md'
        priorpath=ROOT/'docs/S9_COMPONENT_PROFILE_EXECUTION_FREEZE.json';prior=json.loads(priorpath.read_text())
        files=[digest(x) for x in [freeze_path,protocol,priorpath,run/'run_metadata.json',run/'summary.json',run/'invocations.jsonl',run/'schedule.json',run/'call_artifact_manifest.json',run/'renderer_transformation.json']]
        check(digest(freeze_path)['sha256']==metadata['freeze_sha256'],'freeze identity')
        check(digest(protocol)['sha256']==freeze['protocol_sha256']==metadata['protocol_sha256'],'protocol identity')
        check(digest(priorpath)['sha256']==freeze['s9_freeze_sha256']==metadata['s9_freeze_sha256'],'prior freeze identity')
        check(freeze['input_sha256']==prior['input_sha256']==metadata['input_sha256'],'same input domain and hashes')
        check(len(freeze['input_sha256'])==52 and len(freeze['execution_source_sha256'])==12,'52 inputs12 sources')
        for k,domain in [('input',freeze['input_sha256']),('source',freeze['execution_source_sha256'])]:
            for name,h in domain.items():
                obj=digest(ROOT/name);check(obj['sha256']==h,name,'integrity');files.append(obj)
        check(metadata['execution_source_sha256']==freeze['execution_source_sha256'],'runtime source identities')
        start=datetime.fromisoformat(metadata['started_utc']);end=datetime.fromisoformat(metadata['completed_utc'])
        check(datetime.fromisoformat(freeze['frozen_utc'])<=start<=end,'freeze/run ordering')
        check(start<=datetime.fromisoformat(metadata['all_initial_correctness_passed_utc'])<=datetime.fromisoformat(metadata['measurement_started_utc'])<=end,'phase time ordering')
        check(metadata['completed_invocations']==metadata['exact_output_regressions_passed']==336,'all invocation metadata')
        check(metadata['correctness_invocations']==48 and metadata['warmup_invocations']==48 and metadata['measured_invocations']==240 and metadata['measured_pairs']==120,'phase metadata counts')
        check(not any(metadata[k] for k in ['raw_pixels_decoded','gt_loaded','model_loaded']),'forbidden data not reported loaded')
        rows=[json.loads(s) for s in (run/'invocations.jsonl').read_text().splitlines()]
        check(len(rows)==336,'336 raw invocation rows')
        queries=[(stage,b,q) for stage in ('S7','S8') for b in range(3) for q in range(20,24)]
        planned=[]
        for phase,rounds in [('correctness',1),('warmup',1),('measured',5)]:
            for rd in range(rounds):
                for qi,(stage,b,q) in enumerate(queries):
                    methods=['original','candidate'] if (qi+rd)%2==0 else ['candidate','original']
                    planned.append(dict(phase=phase,round=rd,query_index=qi,stage=stage,block=b,query=q,label=f'{stage}_block{b}_query{q}',methods=methods))
        check(json.loads((run/'schedule.json').read_text())==planned,'independent fixed schedule')
        source_cases={};references={}
        for qi,(stage,b,q) in enumerate(queries):
            old=ROOT/'results'/('S7_event_replay' if stage=='S7' else 'S8_event_replay_v2')/f'block{b}_stride8'
            sel=json.loads((old/'prediction_only_selection.json').read_text())
            source_cases[qi]=next(x for x in sel['queries'] if x['frame']==q)['maps']['A0P0']
            with np.load(old/f'query{q}_A0P0_render.npz',allow_pickle=False) as z:references[qi]={k:z[k] for k in z.files}
        actual_manifest=json.loads((run/'call_artifact_manifest.json').read_text())
        check(len(actual_manifest)==672,'672 artifact entries')
        manifest={x['path']:x for x in actual_manifest}
        check(len(manifest)==672,'manifest paths unique')
        check(set(manifest)=={str(x.relative_to(run)) for x in (run/'calls').rglob('*') if x.is_file()},'complete actual calls inventory')
        check(Counter(x['phase'] for x in rows)=={'correctness':48,'warmup':48,'measured':240},'all phase row counts')
        trace_leaves=0
        def leaf_count(x):
            if isinstance(x,dict):return sum(leaf_count(v) for v in x.values())
            if isinstance(x,list):return sum(leaf_count(v) for v in x)
            return 1
        for i,row in enumerate(rows):
            pair=planned[i//2];pos=i%2
            for k in ('phase','round','query_index','stage','block','query','label'):check(row[k]==pair[k],f'row{i}/{k}','schedule')
            check(row['pair_index']==i//2 and row['position_in_pair']==pos and row['method']==pair['methods'][pos],'call positions','schedule')
            check(row['pair_order']==('AB' if pair['methods'][0]=='original' else 'BA'),'pair order','schedule')
            check(row['elapsed_ns'] is None if row['phase']=='correctness' else type(row['elapsed_ns']) is int and row['elapsed_ns']>0,'elapsed phase domain','schedule')
            check(row['exact_regression_passed'] is True,'runtime exact flag','trace')
            qi=row['query_index'];expected=source_cases[qi]
            for ext,key in [('render.npz','render'),('trace.json','trace')]:
                rel=f'calls/{row["phase"]}/round{row["round"]}/{row["label"]}/{row["method"]}/{ext}'
                check(row[key+'_path']==rel,'artifact path schedule','integrity')
                obj=digest(run/rel)
                check(obj['sha256']==row[key+'_sha256']==manifest[rel]['sha256'] and obj['bytes']==manifest[rel]['bytes'],'artifact SHA/size','integrity')
                files.append(obj)
            trace=json.loads((run/row['trace_path']).read_text())
            check(trace['status']=='passed','saved trace status','trace')
            check(trace['returned_ordered_ids']==expected['official_trace']['selected'],'actual returned IDs','trace')
            check(trace['official_trace']==expected['official_trace'],'complete official trace','trace')
            check(trace['official_decision']==expected['readouts']['official'],'complete decision trace','trace')
            check(trace['observed_weights']==expected['official_trace']['weights'],'observed weights','trace')
            check(trace['observed_counts']==expected['official_trace']['candidate_counts'],'observed counts','trace')
            trace_leaves+=leaf_count(trace['official_trace'])+leaf_count(trace['official_decision'])
            with np.load(run/row['render_path'],allow_pickle=False) as z:
                check(set(z.files)==set(references[qi]),'three rendered fields','arrays')
                for field,ref in references[qi].items():
                    arr=z[field]
                    check(arr.shape==ref.shape and arr.dtype==ref.dtype,'shape/dtype','arrays')
                    check(arr.tobytes(order='C')==ref.tobytes(order='C'),'exact C-order bytes including zero sign','arrays')
                    check(trace['render_arrays'][field]==dict(shape=list(arr.shape),dtype=str(arr.dtype),sha256=hashlib.sha256(arr.tobytes(order='C')).hexdigest()),'array identity receipt','arrays')
        pairs=[]
        for i,pair in enumerate(planned):
            if pair['phase']!='measured':continue
            arms={r['method']:r for r in rows[2*i:2*i+2]}
            x,y=arms['original']['elapsed_ns'],arms['candidate']['elapsed_ns']
            pairs.append(dict(round=pair['round'],query_index=pair['query_index'],label=pair['label'],stage=pair['stage'],pair_order=arms['original']['pair_order'],original_ns=x,candidate_ns=y,original_over_candidate=x/y))
        def summarize_group(ps):
            def side(name):
                ns=[p[name+'_ns'] for p in ps]
                return dict(total_ns=sum(ns),mean_ms=(sum(ns)/len(ns))/1e6,median_ms=median(ns)/1e6,min_ms=min(ns)/1e6,max_ms=max(ns)/1e6)
            aa,bb=side('original'),side('candidate')
            return dict(pairs=len(ps),distinct_queries=len({p['label'] for p in ps}),original=aa,candidate=bb,ratio_of_total_times=aa['total_ns']/bb['total_ns'],median_paired_ratio=median([p['original_over_candidate'] for p in ps]),AB_pairs=sum(p['pair_order']=='AB' for p in ps),BA_pairs=sum(p['pair_order']=='BA' for p in ps))
        groups={name:summarize_group([p for p in pairs if name=='all' or p['stage']==name or p['pair_order']==name]) for name in ['all','S7','S8','AB','BA']}
        per=[]
        for qi in range(24):
            ps=[p for p in pairs if p['query_index']==qi];x=median([p['original_ns'] for p in ps]);y=median([p['candidate_ns'] for p in ps])
            check(len(ps)==5,'five repetitions/query','summary')
            per.append(dict(query_index=qi,label=ps[0]['label'],repeats=5,original_median_ms=x/1e6,candidate_median_ms=y/1e6,ratio_of_medians=x/y,AB_pairs=sum(p['pair_order']=='AB' for p in ps),BA_pairs=sum(p['pair_order']=='BA' for p in ps)))
        production=json.loads((run/'summary.json').read_text())
        compare(production['groups'],groups,'groups');compare(production['per_query'],per,'per_query');compare(production['pairs'],pairs,'pairs')
        for fname,expected,key in [('sealed_comparison_inputs.zip',freeze['input_sha256'],'input_archive_sha256'),('comparison_source.zip',{**freeze['execution_source_sha256'],'frozen_protocol.md':freeze['protocol_sha256'],'execution_freeze.json':digest(freeze_path)['sha256'],'S9_execution_freeze.json':digest(priorpath)['sha256']},'source_archive_sha256')]:
            zp=run/fname;check(digest(zp)['sha256']==metadata[key],'archive identity','integrity');files.append(digest(zp))
            with zipfile.ZipFile(zp) as z:
                check(z.testzip() is None,'ZIP CRC','integrity');check(set(z.namelist())==set(expected) and len(z.namelist())==len(expected),'archive exact members','integrity')
                for n,h in expected.items():check(hashlib.sha256(z.read(n)).hexdigest()==h,'archived member '+n,'integrity')
        check(digest(run/'renderer_transformation.json')['sha256']==metadata['renderer_transformation_sha256'],'transformation SHA','integrity')
        check(digest(run/'call_artifact_manifest.json')['sha256']==metadata['call_artifact_manifest_sha256'],'call manifest SHA','integrity')
        for obj in files:check(digest(ROOT/obj['path'])==obj,'audit input unchanged '+obj['path'],'integrity')
        independent={'groups':groups,'per_query':per,'pairs':pairs}
        (out/'independent_summary.json').write_text(json.dumps(independent,indent=2)+'\n')
        receipt.update(status='PASS',checks_passed=sum(checks.values()),checks_by_category=dict(checks),groups=groups,
          per_query_ratio_range=[min(x['ratio_of_medians'] for x in per),max(x['ratio_of_medians'] for x in per)],
          actual_render_npz_compared=336,reference_render_npz=24,exact_array_pairs=1008,complete_trace_pairs=336,complete_trace_scalar_leaves_compared=trace_leaves,
          source_arrays_recomputed=False,renderer_or_selection_rerun=False,input_files=files)
    except Exception as e:
        receipt.update(status='failed',error=repr(e),checks_by_category=dict(checks));raise
    finally:
        receipt['completed_utc']=datetime.now(timezone.utc).isoformat()
        (out/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps({k:receipt.get(k) for k in ['status','checks_passed','checks_by_category','per_query_ratio_range','error','completed_utc']},indent=2))

if __name__=='__main__':main()
