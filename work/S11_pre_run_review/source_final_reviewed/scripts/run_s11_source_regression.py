#!/usr/bin/env python3
"""Source-only controlled regression with guarded sealed-buffer references.

No timing benchmark, model or original renderer execution. The unchanged original
selector consumes a checked historical buffer; S10 candidate renders actual data.
"""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime
import importlib
import inspect
from importlib.metadata import version
import json
import os
from pathlib import Path
import signal
import sys
import textwrap
import time
import traceback
from types import MethodType
import zipfile
import profile_s9_components as s9
import run_s10_renderer_comparison as s10

ROOT=Path(__file__).resolve().parents[1]
SOURCE_NAMES=(*s10.SOURCE_NAMES,'scripts/run_s11_source_regression.py')
S10_FREEZE_SHA='db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204'
VARIANTS=('append_min_missing','drop_last','reverse','only_0','only_0_1_2')
CONTRACT=dict(schema='s11-source-only-regression-v1',stages=['S7','S8'],blocks=[0,1,2],
    query=20,stride=8,arm='A0P0',width=160,history=20,variants=list(VARIANTS),
    controlled_conditions=30,reference_replay_calls=36,candidate_renderer_calls=30,
    speed_measurement=False,model_loading=False,raw_pixels=False,gt=False,
    wall_budget_seconds=600,peak_rss_budget_bytes=16*1024**3,resource_limits='soft',
    versions=dict(python='3.12.14',numpy='2.3.5',torch='2.7.0',scipy='1.16.2'),torch_threads=8)
read,save,sha,require,utc=s9.read,s9.save,s9.sha,s9.require,s9.utc

def edit_mapping(mapping,variant):
    """All rows, original order; never condition edits on visible pixels/results."""
    assert variant in VARIANTS
    out={}
    for key,original in mapping.items():
        values=list(original)
        require(values and len(values)==len(set(values)) and all(type(x) is int and 0<=x<20 for x in values),'Invalid original mapping')
        if variant=='append_min_missing' and len(values)<20:
            values.append(next(x for x in range(20) if x not in values))
        elif variant=='drop_last' and len(values)>1:values=values[:-1]
        elif variant=='reverse':values=values[::-1]
        elif variant=='only_0':values=[0]
        elif variant=='only_0_1_2':values=[0,1,2]
        out[key]=values
    return out

def signature(surfels,poses,focal_lengths,principal_points,image_width,image_height,disk_resolution=16):
    import numpy as np
    require(all(type(x) is int for x in (image_width,image_height,disk_resolution)),
        'Render sizes and resolution must retain built-in integer types')
    def ident(value):
        if hasattr(value,'detach'):value=value.detach().cpu().numpy()
        return s10.array_identity(value,np)
    return dict(positions=ident([s.position for s in surfels]),normals=ident([s.normal for s in surfels]),
        radii=ident([s.radius for s in surfels]),poses=ident(poses),focals=ident(focal_lengths),
        principal=ident(principal_points),width=int(image_width),height=int(image_height),disk_resolution=int(disk_resolution))

def render_arguments(case,module,np):
    kernel=case['kernel']
    pose=module.average_camera_pose(case['target'][-kernel.config.model.context_num_frames//4:])
    return dict(surfels=kernel.surfels,poses=kernel.get_transformed_c2ws(pose),
        focal_lengths=[np.mean(kernel.surfel_Ks,axis=0)*.65]*2,
        principal_points=(80,80),image_width=160,image_height=160,disk_resolution=16)

def replay_function(expected,arrays):
    def render(self,surfels,poses,focal_lengths,principal_points,image_width,image_height,disk_resolution=16):
        actual=signature(surfels,poses,focal_lengths,principal_points,image_width,image_height,disk_resolution)
        require(actual==expected,'Historical buffer replay rejected changed renderer inputs')
        self.replay_guard_calls=getattr(self,'replay_guard_calls',0)+1
        self.last_replay_signature=actual
        self.last_render={k:v.copy() for k,v in arrays.items()}
        return self.last_render
    return render

def source_decision_recorder(module):
    """Only generalize the old record-only terminal check from 4 to maximum.

    The real selector already uses maximum=min(4,candidates,history). All
    computation/branch recording stays byte-for-byte AST-identical otherwise.
    """
    source=textwrap.dedent(inspect.getsource(module.decision_trace))
    original=ast.parse(source);tree=copy.deepcopy(original)
    guard=tree.body[0].body[-2]
    expected=ast.parse('len(chosen) != 4 or len(set(chosen)) != 4 or any(not 0 <= f < 20 for f in chosen)',mode='eval').body
    require(isinstance(guard,ast.If) and ast.dump(guard.test)==ast.dump(expected),'Old terminal recorder check changed')
    for comp in guard.test.values[:2]:comp.comparators[0]=ast.Name(id='maximum',ctx=ast.Load())
    restored=copy.deepcopy(tree);restored.body[0].body[-2].test=copy.deepcopy(original.body[0].body[-2].test)
    require(ast.dump(restored)==ast.dump(original),'Unexpected trace adaptation outside terminal check')
    ast.fix_missing_locations(tree);namespace=dict(vars(module))
    exec(compile(tree,'<S11 recording-only variable-budget terminal check>','exec'),namespace)
    return namespace['decision_trace'],dict(original_source=source,adapted_source=ast.unparse(tree),
        changed_terminal_check_constants=2,restored_full_AST_identical=True,
        scope='Only record validation changed; actual original get_context_info unchanged. Error message inherited verbatim.')

def trace(case,result,modules,np):
    kernel=case['kernel'];old=kernel.get_context_info
    try:
        kernel.get_context_info=lambda *a,**k:result
        official=modules['rgbd_retrieval'].select(kernel,case['pose'])
    finally:kernel.get_context_info=old
    decision=modules['_s11_decision_recorder'](kernel,case['pose'],kernel.last_counts,nms=True)
    require(decision['selected']==result['context_time_indices'].detach().cpu().tolist(),'Recorded NMS differs from actual selector IDs')
    return dict(official_trace=official,official_decision=decision,
        returned_ids=result['context_time_indices'].detach().cpu().tolist(),
        result_arrays={k:s10.array_identity(v.detach().cpu().numpy(),np) for k,v in result.items()},
        render_arrays={k:s10.array_identity(v,np) for k,v in kernel.last_render.items()})

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['freeze','protocol','output']:ap.add_argument('--'+key,type=Path,required=True)
    args=ap.parse_args();out=args.output.absolute()
    require(not out.exists() and not out.is_symlink(),'A new output directory is required')
    require(out.parent.resolve()==ROOT/'results','Output must be a fresh direct child of results')
    out.mkdir();started=time.monotonic()
    report=dict(status='running',started_utc=utc(),contract=CONTRACT,limitations=[
        'Artificial source mapping edits on six existing maps and six seen queries, not new real scene evidence.',
        'Reference is unchanged selector plus guarded original saved buffer replay, not original renderer execution.',
        'Only source association changes; no observed model update, timing benchmark, video, novelty or universal equivalence proof.',
        'All historical poses/latents remain 20; one/three source cases exercise visible-source budgets only.',
        'Shared historical buffers and trace helper provide bounded regression evidence, not an independent geometric oracle.'])
    save(out/'run_metadata.json',report)
    def budget():
        require(time.monotonic()-started<600 and s9.peak_rss_bytes()<16*1024**3,'S11 source soft resource guard exceeded')
    def alarm(*_):raise TimeoutError('S11 source 600-second soft alarm')
    prev=signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,600)
    try:
        frozen=read(args.freeze);old_path=ROOT/'docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE.json';old=read(old_path)
        require(sha(old_path)==S10_FREEZE_SHA,'S10 freeze changed')
        require(frozen['schema']=='s11-source-only-execution-freeze-v1' and frozen['status']=='approved_for_execution','Explicit execution freeze required')
        require(datetime.fromisoformat(frozen['frozen_utc'])<=datetime.fromisoformat(report['started_utc']),'Freeze must predate run')
        require(frozen['contract']==CONTRACT and frozen['s10_freeze_sha256']==S10_FREEZE_SHA,'Frozen contract changed')
        controls={args.freeze.resolve():sha(args.freeze),args.protocol.resolve():sha(args.protocol),old_path:sha(old_path)}
        require(sha(args.protocol)==frozen['protocol_sha256'],'Protocol changed')
        require(set(frozen['execution_source_sha256'])==set(SOURCE_NAMES),'Source domain changed')
        for p,h in old['execution_source_sha256'].items():require(frozen['execution_source_sha256'][p]==h,'Old source identity changed')
        require(frozen['input_sha256']==old['input_sha256'] and len(frozen['input_sha256'])==52,'Reuse exact S10 inputs')
        require(isinstance(frozen.get('review_evidence_sha256'),dict) and frozen['review_evidence_sha256'],'Nonempty pre-run review evidence required')
        protected={ROOT/p:h for group in ['execution_source_sha256','input_sha256','review_evidence_sha256'] for p,h in frozen[group].items()}
        for p,h in protected.items():require(sha(p)==h,'Frozen input/source/review changed: '+str(p))
        for name,items in [('sources.zip',frozen['execution_source_sha256']),('inputs.zip',frozen['input_sha256']),('review_evidence.zip',frozen['review_evidence_sha256'])]:
            with zipfile.ZipFile(out/name,'x',zipfile.ZIP_DEFLATED) as z:
                for p in items:z.write(ROOT/p,p)
                if name=='sources.zip':
                    z.write(args.freeze,'execution_freeze.json');z.write(args.protocol,'protocol.md');z.write(old_path,'S10_execution_freeze.json')
        s9.install_io_guard([ROOT/p for p in frozen['input_sha256']]+[ROOT/p for p in frozen['review_evidence_sha256']],out)
        sys.dont_write_bytecode=True
        for key in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
        os.environ['OMP_DYNAMIC']=os.environ['MKL_DYNAMIC']='FALSE'
        require('numpy' not in sys.modules and 'torch' not in sys.modules,'Set threads before numerical imports')
        import numpy as np
        import torch
        torch.set_num_threads(8);torch.set_num_interop_threads(8)
        versions=dict(python=sys.version.split()[0],**{k:version(k) for k in ['numpy','torch','scipy']})
        require(versions==CONTRACT['versions'] and torch.get_default_dtype()==torch.float32,'Environment changed')
        sys.path.insert(0,str(ROOT/'src'))
        modules={n:importlib.import_module(n) for n in ['s6_memory_bridge','s7_event_replay','rgbd_memory','rgbd_retrieval','retrieval_diagnostic','vmem_memory_kernel','vmem_retrieval_kernel']}
        candidate=importlib.import_module('s10_vectorized_renderer')
        for n,m in {**modules,'s10_vectorized_renderer':candidate}.items():require(Path(m.__file__).resolve()==ROOT/'src'/f'{n}.py','Module location changed')
        recorder,recorder_receipt=source_decision_recorder(modules['s7_event_replay'])
        modules['_s11_decision_recorder']=recorder;save(out/'source_trace_adapter.json',recorder_receipt)
        function=candidate.renderer_function();save(out/'renderer_transformation.json',function.s10_transformation)
        require(function.s10_transformation['helper_source_sha256']==old['execution_source_sha256']['src/s10_vectorized_renderer.py'],'Candidate identity mismatch')
        runs=dict(S7=ROOT/'results/S7_event_replay',S8=ROOT/'results/S8_event_replay_v2')
        cases=[x for x in s9.load_cases(runs,np,torch,modules,[ROOT/p for p in frozen['input_sha256']]) if x['query']==20]
        require(len(cases)==6,'Expected six fixed blocks')
        rows=[];baselines=[];negative=[]
        for case in cases:
            budget();arguments=render_arguments(case,modules['vmem_retrieval_kernel'],np)
            require(np.any((case['render']['surfel_index_map']>=0)&(case['render']['cos_value_map']>0)),'Fixed source fixture needs at least one positive valid vote pixel')
            identity=signature(**arguments)
            folder=out/case['label'];folder.mkdir()
            save(folder/'render_argument_identity.json',identity)
            baseline=copy.deepcopy(case)
            replay=replay_function(identity,case['render'])
            baseline['kernel'].render_surfels_to_image=MethodType(replay,baseline['kernel'])
            result=baseline['kernel'].get_context_info(baseline['target'])
            original_trace=trace(baseline,result,modules,np)
            require(original_trace['official_trace']==case['expected']['official_trace'] and original_trace['official_decision']==case['expected']['readouts']['official'],'Baseline replay differs from original saved selector')
            require(baseline['kernel'].replay_guard_calls==1,'Baseline must replay exactly once')
            save(folder/'baseline_replay_trace.json',original_trace);baselines.append(case['label'])
            # Both guards run before candidate calls. Deliberate invalid references
            # must fail; no geometry or camera mutation leaks to positive cases.
            for kind in ['camera','geometry','focal']:
                wrong=copy.deepcopy(arguments)
                if kind=='camera':wrong['poses'][0,3]+=1e-3
                elif kind=='geometry':wrong['surfels'][0].position[0]+=1e-3
                else:wrong['focal_lengths'][0]+=1e-3
                wrong_identity=signature(**wrong)
                differences={key:dict(expected=identity[key],actual=wrong_identity[key]) for key in identity if identity[key]!=wrong_identity[key]}
                require(set(differences)=={{'camera':'poses','geometry':'positions','focal':'focals'}[kind]},'Negative control changed unexpected renderer fields')
                rejected=False;reason=None
                try:replay(baseline['kernel'],**wrong)
                except ValueError as exc:
                    reason=str(exc);rejected='Historical buffer replay rejected' in reason
                negative.append(dict(label=case['label'],kind=kind,rejected=rejected,reason=reason,signature_differences=differences))
                save(out/'negative_controls.json',negative)
                require(rejected,'Replay guard negative control failed: '+kind)
            for variant in VARIANTS:
                budget();mapping=edit_mapping(case['memory'].mapping,variant)
                changed=sum(mapping[k]!=v for k,v in case['memory'].mapping.items())
                require(changed>0,'Configured mapping edit changed no rows')
                vf=folder/variant;vf.mkdir();save(vf/'mapping.json',mapping)
                arms={};states={};results={};traces={}
                for method in ['reference_replay','candidate']:
                    c=copy.deepcopy(case);c['memory'].mapping=copy.deepcopy(mapping);c['kernel'].surfel_to_timestep=c['memory'].mapping
                    require(c['kernel'].get_context_info.__func__ is modules['vmem_retrieval_kernel'].RetrievalKernel.get_context_info,'Changed context method')
                    fn=replay if method=='reference_replay' else s10.observed_renderer(function)
                    c['kernel'].render_surfels_to_image=MethodType(fn,c['kernel'])
                    arms[method]=c;states[method]=s10.state_identity(c,np,modules['s6_memory_bridge'])
                require(states['reference_replay']==states['candidate'],'Different initial arm inputs')
                for method,c in arms.items():
                    mf=vf/method;mf.mkdir()
                    report.update(active_case=case['label'],active_variant=variant,active_method=method)
                    save(out/'run_metadata.json',report)
                    c['kernel'].last_render=None
                    try:result=c['kernel'].get_context_info(c['target'])
                    except Exception:
                        if c['kernel'].last_render is not None:np.savez_compressed(mf/'render.npz',**c['kernel'].last_render)
                        raise
                    results[method]=result
                    np.savez_compressed(mf/'render.npz',**c['kernel'].last_render)
                    np.savez_compressed(mf/'context.npz',**{k:v.detach().cpu().numpy() for k,v in result.items()})
                    tr=trace(c,result,modules,np);traces[method]=tr;save(mf/'trace.json',tr)
                    for name,value in c['kernel'].last_render.items():
                        expected=case['render'][name]
                        require(value.shape==expected.shape and value.dtype==expected.dtype and value.tobytes(order='C')==expected.tobytes(order='C'),'Render differs from sealed buffer: '+name)
                    after=s10.state_identity(c,np,modules['s6_memory_bridge'])
                    require(after==states[method],'Positive call mutated inputs')
                    if method=='reference_replay':require(c['kernel'].replay_guard_calls==1,'Each controlled reference must replay once')
                    save(mf/'state_identity.json',dict(before=states[method],after=after))
                require(traces['reference_replay']==traces['candidate'],'Full trace/context identity differs')
                for key,value in results['reference_replay'].items():
                    other=results['candidate'][key]
                    require(value.shape==other.shape and value.dtype==other.dtype and torch.equal(value,other),'Actual context differs: '+key)
                selected=traces['candidate']['returned_ids']
                if variant=='only_0':require(selected==[0],'One visible source must yield exactly [0]')
                if variant=='only_0_1_2':require(len(selected)==3 and set(selected)=={0,1,2},'Three visible sources must yield exactly those three')
                stale_rejected=(original_trace['official_trace']!=traces['reference_replay']['official_trace'] or original_trace['official_decision']!=traces['reference_replay']['official_decision'])
                row=dict(label=case['label'],variant=variant,changed_mapping_rows=changed,
                    selected_ids=selected,visible_sources=traces['candidate']['official_trace']['visible_sources'],
                    stale_original_mapping_trace_rejected=stale_rejected,
                    selected_order_changed_from_original=selected!=original_trace['returned_ids'],
                    exact_render_and_full_trace=True,folder=str(vf.relative_to(out)))
                rows.append(row);save(out/'conditions.json',rows)
        require(len(rows)==30 and len(baselines)==6 and len(negative)==18,'Incomplete fixed schedule')
        require(sum(r['stale_original_mapping_trace_rejected'] for r in rows if r['variant'] in VARIANTS[:3])>=1,'Stale-mapping negative control undetected among 18 edits')
        for p,h in {**protected,**controls}.items():require(sha(p)==h,'Frozen file changed during execution: '+str(p))
        budget();save(out/'negative_controls.json',negative)
        save(out/'summary.json',dict(conditions=30,new_candidate_renders=30,reference_buffer_replays=36,base_maps=6,base_queries=6,
            groups={v:dict(conditions=sum(r['variant']==v for r in rows),exact_pass=sum(r['variant']==v and r['exact_render_and_full_trace'] for r in rows),
                stale_trace_rejected=sum(r['variant']==v and r['stale_original_mapping_trace_rejected'] for r in rows),
                selected_order_changed=sum(r['variant']==v and r['selected_order_changed_from_original'] for r in rows)) for v in VARIANTS},
            replay_invalid_argument_controls_rejected=18,speed_measurement=False))
        manifest={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='run_metadata.json'}
        save(out/'artifact_manifest.json',manifest)
        report.update(status='completed',conditions_passed=30,new_candidate_renders=30,reference_buffer_replays=36,
            frozen_files_unchanged=True,initial_and_final_input_states_equal=True,versions=versions,
            torch_threads=torch.get_num_threads(),torch_interop_threads=torch.get_num_interop_threads(),
            freeze_sha256=sha(args.freeze),protocol_sha256=sha(args.protocol),original_renderer_calls=0,
            source_sha256=frozen['execution_source_sha256'],input_sha256=frozen['input_sha256'])
    except Exception:
        report.update(status='failed',traceback=traceback.format_exc(),partial_results_valid_as_complete=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prev)
        report.update(completed_utc=utc(),total_elapsed_seconds=time.monotonic()-started,process_peak_rss_bytes=s9.peak_rss_bytes())
        save(out/'run_metadata.json',report);print(json.dumps({k:v for k,v in report.items() if k in ['status','conditions_passed','completed_utc','traceback']},ensure_ascii=False))
    if report['status']!='completed':raise SystemExit(1)

if __name__=='__main__':main()
