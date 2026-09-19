#!/usr/bin/env python3
"""Read-only independent standard-library audit of saved S9 timing evidence.

No experiment module is imported, and no renderer, model, timing experiment or
production summarizer is executed. Saved traces and recorded execution flags
are distinguished from newly recomputed descriptive statistics.
"""
import argparse
import ast
from collections import Counter
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path,PurePosixPath
import re
import shutil
import textwrap
import traceback
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FIELDS=('renderer_ns','votes_allocation_ns','sort_nms_ns','total_ns','other_ns')
SOURCES=('scripts/profile_s9_components.py','src/s6_memory_bridge.py','src/s7_event_replay.py',
    'src/rgbd_memory.py','src/rgbd_retrieval.py','src/retrieval_diagnostic.py',
    'src/vmem_memory_kernel.py','src/vmem_retrieval_kernel.py','vendor/provenance.json','vendor/VMEM_LICENSE')
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def strict(s):
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Duplicate JSON key: '+k)
            result[k]=v
        return result
    def nonfinite(v):raise ValueError('Nonfinite JSON value: '+v)
    return json.loads(s,object_pairs_hook=unique,parse_constant=nonfinite)
def stat(values):
    ordered=sorted(values);n=len(values)
    middle=ordered[n//2] if n%2 else (ordered[n//2-1]+ordered[n//2])/2
    # Exact rational summation of the input float values, independently from
    # statistics.mean and the production float sum; round only at the output.
    # A naive += loop differs from Python 3.12's sum on these saved inputs.
    exact_sum=sum((Fraction.from_float(x) for x in values),Fraction())
    total=float(exact_sum)
    mean=float(exact_sum/n)
    return dict(mean=mean,median=middle,min=ordered[0],max=ordered[-1],total=total)
def summarize_independently(rows,order):
    groups={}
    for stage in ('all','S7','S8'):
        chosen=[r for r in rows if r['round']>0 and (stage=='all' or r['stage']==stage)]
        g=dict(invocations=len(chosen),distinct_queries=len({r['label'] for r in chosen}))
        for field in FIELDS:g[field[:-3]+'_ms']=stat([r[field]/1000000 for r in chosen])
        denominator=sum(r['total_ns'] for r in chosen)
        g['time_shares']={field[:-3]:sum(r[field] for r in chosen)/denominator for field in (*FIELDS[:3],'other_ns')}
        groups[stage]=g
    queries=[]
    for label in order:
        selected=[r for r in rows if r['round']>0 and r['label']==label]
        item=dict(label=label,repeats=len(selected))
        for field in FIELDS:item[field[:-3]+'_median_ms']=sorted(r[field] for r in selected)[len(selected)//2]/1000000
        queries.append(item)
    return dict(groups=groups,per_query=queries,
        inference='Descriptive repeated-call software timings only; repeats are not independent samples.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('run','protocol','freeze','output'):ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args()
    meta=strict((args.run/'run_metadata.json').read_text())
    if meta.get('status')!='completed' or meta.get('phase')!='complete':ap.error('Completed S9 run required')
    if args.output.exists() or args.output.is_symlink():ap.error('Use a fresh output directory; preserve failures')
    out=args.output.absolute();out.mkdir(parents=True)
    shutil.copy2(__file__,out/Path(__file__).name)
    checks=[];before={};leaves=Counter()
    report=dict(status='running',started_utc=now(),checks=checks,verifier_sha256=sha(__file__),
        numerical_tolerance='None. All saved JSON fields and recomputed summary values must compare exactly.',
        limitations=[
            'No renderer, model, original retrieval invocation or performance experiment is repeated by this auditor.',
            '24 saved warmup official/decision traces can be compared directly. The other 120 calls have per-row success flags, not individually saved traces.',
            'Fresh renderer arrays from the 144 calls are not saved. Their exact historical regression is assessed through flags and frozen validation-source structure, not a new array comparison.',
            'Historical timestamps, peak RSS, thread counts, original memory-digest checks and input/source unchanged flags are recorded/source evidence, not reenacted process observations.',
            'Instrumented CPU component timing includes observer/clock/wrapper overhead and dummy context arrays; not full VMem, model/video latency or an uninstrumented baseline.',
            '24 already-seen queries from two scenes (S7 development block included); 5 repeats do not supply independent queries or a measured B speedup.',
            'Geometry uses FP64 tensors, argsort inputs use default FP32. Recorded native thread environment does not prove every library actually used eight threads.'])
    def check(name,condition,kind='recomputed',detail=None):
        item=dict(name=name,passed=bool(condition),kind=kind)
        if detail is not None:item['detail']=detail
        checks.append(item)
        if not condition:raise AssertionError(name)
    def track(p):
        p=Path(p).resolve(strict=True);h=sha(p)
        if str(p) in before:check('stable_read/'+str(p),before[str(p)]==h,'integrity')
        before[str(p)]=h;return p
    def read(p):return strict(track(p).read_text())
    def equal(name,a,b,kind='recomputed'):
        def compare(x,y):
            if type(x) is not type(y):return False
            if isinstance(x,dict):return set(x)==set(y) and all(compare(x[k],y[k]) for k in x)
            if isinstance(x,list):return len(x)==len(y) and all(compare(u,v) for u,v in zip(x,y))
            leaves[kind]+=1
            return x==y
        check(name,compare(a,b),kind)
    def identity(p,h,label=None):check(label or 'sha/'+str(p),sha(track(p))==h,'integrity')
    try:
        track(args.run/'run_metadata.json');track(__file__)
        freeze=read(args.freeze);protocol=track(args.protocol).read_text();summary=read(args.run/'summary.json')
        check('freeze_approval',freeze['schema']=='s9-component-profile-freeze-v1' and freeze['status']=='approved_for_execution','metadata')
        identity(args.protocol,freeze['protocol_sha256']);identity(args.freeze,meta['freeze_sha256'])
        check('protocol_identity',meta['protocol_sha256']==freeze['protocol_sha256'],'integrity')
        fences=re.findall(r'```s9-profile-json\s*\n(.*?)\n```',protocol,re.S)
        check('single_contract',len(fences)==1,'metadata');equal('recorded_contract',strict(fences[0]),meta['contract'],'metadata')
        expected_contract=dict(schema='s9-component-profile-v1',stages=['S7','S8'],blocks=[0,1,2],queries=[20,21,22,23],
            stride=8,arm='A0P0',width=160,history_count=20,context_count=4,warmup_rounds=1,measured_rounds=5,
            order='stage_then_block_then_query',device='cpu',torch_threads=8,torch_interop_threads=8,
            wall_budget_seconds=300,peak_rss_budget_bytes=17179869184,resource_limit='soft',exact_output_gate=True,
            diagnostic_atol=1e-9,diagnostic_rtol=1e-10,raw_pixels_allowed=False,gt_allowed=False,model_loading_allowed=False)
        equal('fixed_contract',meta['contract'],expected_contract,'metadata')
        times=[datetime.fromisoformat(x) for x in (freeze['frozen_utc'],meta['started_utc'],meta['inputs_sealed_utc'],
            meta['initialization_completed_utc'],meta['completed_utc'])]
        check('freeze_seal_initialization_completion_order',all(t.tzinfo is not None for t in times) and
            all(a<=b for a,b in zip(times,times[1:])),'metadata')
        check('recorded_soft_budgets',0<meta['initialization_elapsed_seconds']<meta['total_elapsed_seconds']<=300 and
            type(meta['process_peak_rss_bytes']) is int and 0<meta['process_peak_rss_bytes']<=16*1024**3,'metadata')
        check('recorded_unchanged_flags',meta['original_inputs_unchanged'] is True and meta['original_sources_unchanged'] is True,'metadata')
        check('recorded_input_scope',meta['data_arrays_decoded']=='saved map/pose/render NPZ only' and
            meta['raw_pixels_decoded'] is False and meta['gt_loaded'] is False and meta['model_loaded'] is False,'metadata')
        env=meta['environment'];check('recorded_torch_environment',env['torch_threads']==env['torch_interop_threads']==8 and
            env['torch_default_dtype']=='torch.float32' and env['numpy']=='2.3.5' and env['torch']=='2.7.0','metadata')
        threads={k:'8' for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')}
        threads.update(OMP_DYNAMIC='FALSE',MKL_DYNAMIC='FALSE');equal('recorded_thread_environment',env['native_thread_environment'],threads,'metadata')
        runs={'S7':ROOT/'results/S7_event_replay','S8':ROOT/'results/S8_event_replay_v2'}
        inputs=[];oldmeta={};choices={};order=[]
        for stage,path in runs.items():
            inputs += [path/'run_metadata.json',path/'records.json'];oldmeta[stage]=read(path/'run_metadata.json')
            check(stage+'/completed',oldmeta[stage]['status']=='completed' and oldmeta[stage]['phase']=='complete','metadata')
            for block in range(3):
                case=path/f'block{block}_stride8'
                inputs += [case/n for n in ('A0P0.npz','A0P0_sources.json','predicted_poses.npz','prediction_only_selection.json')]
                inputs += [case/f'query{q}_A0P0_render.npz' for q in range(20,24)]
                choice=read(case/'prediction_only_selection.json');choices[stage,block]=choice
                equal(f'{stage}/B{block}/query_domain',[q['frame'] for q in choice['queries']],list(range(20,24)),'metadata')
                for q in range(20,24):order.append(f'{stage}_block{block}_query{q}')
        expected={str(p.relative_to(ROOT)) for p in inputs}
        check('52_exact_input_paths',len(inputs)==len(set(inputs))==52 and set(freeze['input_sha256'])==expected,'integrity')
        equal('recorded_input_freeze',meta['input_sha256'],freeze['input_sha256'],'integrity')
        check('10_exact_source_paths',set(freeze['execution_source_sha256'])==set(SOURCES) and len(SOURCES)==10,'integrity')
        equal('recorded_source_freeze',meta['execution_source_sha256'],freeze['execution_source_sha256'],'integrity')
        for name,h in freeze['input_sha256'].items():identity(ROOT/name,h)
        for name,h in freeze['execution_source_sha256'].items():
            identity(ROOT/name,h)
            if name.startswith('src/'):
                for stage in runs:check(stage+'/historical_source/'+name,oldmeta[stage]['source_sha256'][name]==h,'integrity')
        for stage,path in runs.items():
            records=read(path/'records.json');refs={(r['block'],r['stride'],r['frame']):r for r in records}
            check(stage+'/unique_record_keys',len(refs)==len(records),'integrity')
            for b in range(3):
                folder=path/f'block{b}_stride8';case=[r for r in oldmeta[stage]['cases'] if r['block']==b and r['stride']==8]
                check(f'{stage}/B{b}/case_domain',len(case)==1 and case[0]['directory']==folder.name,'integrity')
                for p in inputs:
                    if p.parent==folder:check('historical_seal/'+str(p.relative_to(ROOT)),case[0]['sealed_files'][p.name]==freeze['input_sha256'][str(p.relative_to(ROOT))],'integrity')
                for q in choices[stage,b]['queries']:
                    label=f"{stage}_block{b}_query{q['frame']}";saved=read(args.run/(label+'_regression.json'));item=q['maps']['A0P0']
                    equal(label+'/saved_official_trace',saved['official_trace'],item['official_trace'],'saved_trace_comparison')
                    equal(label+'/saved_complete_decision',saved['official_decision'],item['readouts']['official'],'saved_trace_comparison')
                    equal(label+'/recorded_ordered_IDs',saved['official_trace']['selected'],refs[b,8,q['frame']]['readouts']['A0P0']['official']['selected'],'saved_trace_comparison')
        for archive,digest,entries in [('profile_source.zip',meta['source_archive_sha256'],
            {**freeze['execution_source_sha256'],'frozen_protocol.md':sha(args.protocol),'execution_freeze.json':sha(args.freeze)}),
            ('sealed_profile_inputs.zip',meta['input_archive_sha256'],freeze['input_sha256'])]:
            p=track(args.run/archive);identity(p,digest)
            with zipfile.ZipFile(p) as z:
                names=z.namelist();check(archive+'/unique_exact_inventory',len(names)==len(set(names)) and set(names)==set(entries),'integrity')
                check(archive+'/all_CRC',z.testzip() is None,'integrity')
                for name,h in entries.items():
                    relative=PurePosixPath(name);check(archive+'/safe/'+name,not relative.is_absolute() and '..' not in relative.parts and '\\' not in name,'integrity')
                    check(archive+'/sha/'+name,hashlib.sha256(z.read(name)).hexdigest()==h,'integrity')
        lines=track(args.run/'timings.jsonl').read_text().splitlines()
        check('144_nonempty_JSONL_lines',len(lines)==144 and all(line.strip() for line in lines))
        rows=[strict(line) for line in lines];equal('query_order',meta['query_order'],order,'metadata')
        schema={'stage','block','query','label','round','warmup','map_points','total_ns','other_ns',*FIELDS[:3],'exact_regression_passed'}
        for index,r in enumerate(rows):
            round_id,position=divmod(index,24);stage='S7' if position<12 else 'S8';block=(position%12)//4;q=20+position%4
            tag=f'row{index}'
            check(tag+'/exact_keys',set(r)==schema)
            for key in ('block','query','round','map_points',*FIELDS):check(tag+'/'+key+'/integer_nonnegative',type(r[key]) is int and r[key]>=0)
            check(tag+'/booleans',type(r['warmup']) is bool and type(r['exact_regression_passed']) is bool)
            check(tag+'/fixed_schedule',r['label']==order[position] and r['round']==round_id and r['stage']==stage and r['block']==block and r['query']==q and r['warmup']==(round_id==0))
            check(tag+'/map_points',r['map_points']==choices[stage,block]['maps']['A0P0']['points'])
            check(tag+'/phase_partition',r['total_ns']>0 and r['other_ns']==r['total_ns']-sum(r[f] for f in FIELDS[:3]))
            check(tag+'/recorded_exact_gate',r['exact_regression_passed'] is True,'metadata')
        check('24_warmup_and_120_measured',sum(r['warmup'] for r in rows)==24 and sum(not r['warmup'] for r in rows)==120)
        for label in order:equal(label+'/rounds',[r['round'] for r in rows if r['label']==label],list(range(6)))
        check('recorded_counts',meta['exact_output_regressions_passed']==144 and meta['distinct_previously_seen_queries']==24 and
            meta['warmup_invocations']==24 and meta['measured_invocations']==120,'metadata')
        check('all_recorded_calls_fit_total_budget',sum(r['total_ns'] for r in rows)/1e9 < meta['total_elapsed_seconds'],'metadata')
        rebuilt=summarize_independently(rows,order);save(out/'independent_summary.json',rebuilt)
        summary_start=leaves['recomputed'];equal('all_summary_fields_exact',rebuilt,summary)
        summary_comparisons=leaves['recomputed']-summary_start
        # Independent static inspection of the two saved ASTs and phase anchors.
        original=track(args.run/'original_get_context_info.py.txt').read_text();timed=track(args.run/'timed_get_context_info.py.txt').read_text()
        check('original_method_text_sha',hashlib.sha256(original.encode()).hexdigest()==meta['instrumentation']['original_text_sha256'],'integrity')
        check('timed_method_text_sha',hashlib.sha256(timed.encode()).hexdigest()==meta['instrumentation']['instrumented_text_sha256'],'integrity')
        a=ast.parse(original);b=ast.parse(timed);fn=b.body[0];branch=[n for n in fn.body if isinstance(n,ast.If) and n.orelse][0]
        markers=[];kept=[]
        for node in branch.orelse:
            lhs=ast.unparse(node.targets[0]) if isinstance(node,ast.Assign) else ''
            if lhs=='__s9_begin' or lhs.startswith('self.__s9_times['):markers.append(node)
            else:kept.append(node)
        check('six_timing_markers_and_reads',len(markers)==6 and sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='__s9_clock' for node in markers for n in ast.walk(node))==6,'source_structure')
        phase_names=[ast.literal_eval(n.targets[0].slice) for n in markers if isinstance(n.targets[0],ast.Subscript)]
        equal('three_phase_marker_names',phase_names,list(FIELDS[:3]),'source_structure')
        branch.orelse=kept;check('stripped_timed_AST_exact',ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'source_structure')
        kernel_source=track(ROOT/'src/vmem_retrieval_kernel.py').read_text();kernel_ast=ast.parse(kernel_source)
        klass=next(n for n in kernel_ast.body if isinstance(n,ast.ClassDef) and n.name=='RetrievalKernel')
        method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='get_context_info')
        # inspect.getsource was dedented before the profiler stored the function.
        # Use its source span, not the whole class's differently indented docstring.
        independent_span=textwrap.dedent('\n'.join(kernel_source.splitlines()[method.lineno-1:method.end_lineno]))
        independent_method=ast.parse(independent_span).body[0]
        check('saved_original_method_matches_frozen_kernel',ast.dump(a.body[0],include_attributes=False)==ast.dump(independent_method,include_attributes=False),'source_structure')
        check('instrumentation_record',meta['instrumentation']['original_AST_preserved'] is True and meta['instrumentation']['inserted_statements']==6 and meta['instrumentation']['clock_reads']==6,'metadata')
        # Preserve full input receipts and values; these flags are never promoted
        # into claims that this audit executed the original native calls.
        for p,h in before.items():check('unchanged/'+p,sha(p)==h,'integrity')
        save(out/'independent_summary.json',rebuilt);save(out/'timing_records.json',rows)
        report.update(status='passed',groups=rebuilt['groups'],per_query=rebuilt['per_query'],
            summary_exact=True,summary_value_comparisons=summary_comparisons,saved_trace_scalar_comparisons=leaves['saved_trace_comparison'],
            timing_rows=144,warmup_rows=24,measurement_rows=120,distinct_queries=24,saved_trace_pairs=24,
            input_files=52,execution_sources=10,archived_source_members=12,archived_input_members=52,
            original_run_started_utc=meta['started_utc'],original_run_completed_utc=meta['completed_utc'],
            original_run_elapsed_seconds=meta['total_elapsed_seconds'],sum_all_call_seconds=sum(r['total_ns'] for r in rows)/1e9,
            profiler_source_sha256=freeze['execution_source_sha256']['scripts/profile_s9_components.py'])
    except Exception:
        report.update(status='failed',traceback=traceback.format_exc())
    report.update(completed_utc=now(),checks_count=len(checks),checks_by_kind=dict(Counter(c['kind'] for c in checks)),
        scalar_comparisons_by_kind=dict(leaves),original_file_sha256=before)
    save(out/'verification.json',report)
    print(json.dumps({k:report.get(k) for k in ('status','started_utc','completed_utc','checks_count','checks_by_kind','traceback')},indent=2))
    return 0 if report['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
