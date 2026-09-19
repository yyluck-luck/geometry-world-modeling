"""Derive S26B source/contracts from frozen S26; stdlib metadata only.

No draft freeze, model, GA, image/NPZ decode, GT file read, or import of the
numerical runner/reference is performed here. --metadata refreshes candidates
after the independently authored recovery receipt becomes available.
"""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD_PREP=ROOT/'work/S26_consumer_baseline_preparation'
OLD_WORK=ROOT/'work/S26_execution'
OLD_BASE=ROOT/'results/S26_consumer_baseline'
OLD_RUNNER=ROOT/'scripts/s26_consumer_baseline.py'
NEW_RUNNER=ROOT/'scripts/s26b_consumer_baseline.py'
OLD_SCORER=ROOT/'scripts/score_s26_consumer.py'
NEW_SCORER=ROOT/'scripts/score_s26b_consumer.py'
OLD_PROTOCOL=ROOT/'docs/S26_CONSUMER_SCORING_PROTOCOL.md'
NEW_PROTOCOL=ROOT/'docs/S26B_CONSUMER_SCORING_PROTOCOL.md'
RECOVERY=ROOT/'work/S26_clean_recovery/recovery_receipt.json'
OLD_EVIDENCE_SCOPE='Scoring previously seen sensor data after four new GA producer seals; not novel-method, memory-mechanism, or video-generation evidence.'
NEW_EVIDENCE_SCOPE='Scoring previously seen sensor data after one IMPORT_VALIDATED saved producer and three newly completed GA producer seals; not novel-method, memory-mechanism, or video-generation evidence.'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def replace_once(s,a,b):
    assert s.count(a)==1,repr(a)
    return s.replace(a,b,1)


def normalized_scorer_ast(text):
    # Only paths and this provenance sentence differ; no metric/gate changes.
    t=ast.parse(text.replace(NEW_EVIDENCE_SCOPE,OLD_EVIDENCE_SCOPE))
    t.body=[n for n in t.body if not (isinstance(n,ast.Assign) and
            any(isinstance(x,ast.Name) and x.id in ('BASE','PROTOCOL') for x in n.targets))]
    return ast.dump(t,include_attributes=False)


def generate_sources(old):
    assert not any(p.exists() for p in (NEW_RUNNER,NEW_SCORER,NEW_PROTOCOL)), 'Preserve previous draft identities'
    s=OLD_RUNNER.read_text()
    s=replace_once(s,"PREP = ROOT / 'work/S26_consumer_baseline_preparation'",
                     "PREP = ROOT / 'work/S26B_preparation'\nADAPTER_PREP = ROOT / 'work/S26_consumer_baseline_preparation'")
    s=replace_once(s,"WORK = ROOT / 'work/S26_execution'","WORK = ROOT / 'work/S26B_execution'")
    s=replace_once(s,"OUT = ROOT / 'results/S26_consumer_baseline'","OUT = ROOT / 'results/S26B_consumer_baseline'")
    s=replace_once(s,"sys.path.insert(0, str(PREP))","sys.path.insert(0, str(ADAPTER_PREP))")
    s=replace_once(s,'def numeric_setup():', '''def import_worker(m):
    spec=importlib.util.spec_from_file_location('s26b_import_previous', PREP/'import_previous.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.import_previous(m, MANIFEST, WORK, OUT)


def numeric_setup():''')
    checkpoint='''    def checkpoint(self, stage):
        origins={}
        for name,module in list(sys.modules.items()):
            if name.startswith(('cloud_opt.','dust3r.','src.dust3r.','models.','croco.')):
                origin=getattr(module,'__file__',None)
                if origin:origins[name]=str(Path(origin).resolve())
        event=dict(status='OBSERVED_NOT_FINAL_PASS',stage=stage,utc=utc(),
            iterations=self.steps,adam_steps=self.adam_steps,mst_calls=self.mst_calls,
            clean_calls=self.clean_calls,report=self.report,loaded_geometry_modules_observed=origins)
        with (self.out/'observer_events.jsonl').open('a') as handle:
            handle.write(json.dumps(event,ensure_ascii=False,allow_nan=False)+'\\n')
        write(self.out/'observer_checkpoint.json',event)

'''
    s=replace_once(s,'    def restore(self):',checkpoint+'    def restore(self):')
    s=replace_once(s,"self.report['returned_pre_last_step_loss']=float(result)",
                     "self.report['returned_pre_last_step_loss']=float(result)\n                self.checkpoint('post_GA_constraints')")
    s=replace_once(s,"for name,p in self.params(s).items(): require(self.T.equal(p,self.frozen[name]), 'MST changed fixed parameter '+name)",
                     "for name,p in self.params(s).items(): require(self.T.equal(p,self.frozen[name]), 'MST changed fixed parameter '+name)\n                self.checkpoint('post_MST_constraints')")
    s=replace_once(s,'self.snapshot=after; self.clean_calls+=1',
                     "self.snapshot=after; self.clean_calls+=1\n                self.checkpoint('post_clean_constraints')")
    s=replace_once(s,'def ga_worker(m, mode):\n    out=OUT/mode',
                     "def ga_worker(m, mode):\n    require(mode in ('cut3r','ttt3r','filt3r'),'S26B never reruns common_old GA')\n    out=OUT/mode")
    s=replace_once(s,'        finally: observer.restore()',
                     "        finally:\n            observer.restore()\n            observer.checkpoint('GA_call_exit')")
    phases="""        phases=[('control',180,2),*((f'views_{v}',180,2) for v in m['preprocess_repos']),('compat',240,4),
                ('common_old',600,16),('cut3r',1200,16),('ttt3r',1200,16),('filt3r',1200,16)]"""
    s=replace_once(s,phases,"        phases=[('import',120,2),('cut3r',1200,16),('ttt3r',1200,16),('filt3r',1200,16)]")
    s=replace_once(s,"str(ROOT/'scripts/score_s26_consumer.py')","str(ROOT/'scripts/score_s26b_consumer.py')")
    old_routes="""    elif args.phase=='control':control_input(m)
    elif args.phase=='compat':compatibility(m)
    elif args.phase.startswith('views_'):source_views(m,args.phase[6:])
    elif args.phase in MODES:ga_worker(m,args.phase)"""
    s=replace_once(s,old_routes,"""    elif args.phase=='import':import_worker(m)
    elif args.phase in ('cut3r','ttt3r','filt3r'):ga_worker(m,args.phase)""")
    compile(s,str(NEW_RUNNER),'exec')
    NEW_RUNNER.write_text(s)

    old_scoring=OLD_SCORER.read_text()
    sc=replace_once(old_scoring,'PROTOCOL = ROOT / "docs/S26_CONSUMER_SCORING_PROTOCOL.md"',
                   'PROTOCOL = ROOT / "docs/S26B_CONSUMER_SCORING_PROTOCOL.md"')
    sc=replace_once(sc,'BASE = ROOT / "results/S26_consumer_baseline"',
                   'BASE = ROOT / "results/S26B_consumer_baseline"')
    sc=replace_once(sc,OLD_EVIDENCE_SCOPE,NEW_EVIDENCE_SCOPE)
    assert normalized_scorer_ast(sc)==normalized_scorer_ast(old_scoring),'Scorer mathematics/rules must be byte-AST identical'
    compile(sc,str(NEW_SCORER),'exec');NEW_SCORER.write_text(sc)
    prefix='''# S26B continuation：原评分规则不变

本文件继承下文S26固定数学、GT身份、顺序与容差，仅producer/output路径改为S26B。
`common_old` 的新receipt `status:PASS`严格表示 `validation_status:IMPORT_VALIDATED`：
导入S26既有原400步输出，经独立保存后恢复核查；不是新GA、不是原S26整门PASS。
原FAILED及未记录的历史PnP/loaded modules/postfinal标量保持原状。其余三个8图producer
仍须前瞻性完整PASS。执行程序为 `scripts/score_s26b_consumer.py score`；不调用prepare-inputs。
新manifest的scoring对象从旧冻结scoring逐项继承，仅更新producer/output及新scorer/本协议身份。

'''
    inherited=OLD_PROTOCOL.read_text().replace('results/S26_consumer_baseline','results/S26B_consumer_baseline').replace('scripts/score_s26_consumer.py','scripts/score_s26b_consumer.py')
    NEW_PROTOCOL.write_text(prefix+inherited)
    (HERE/'runner.diff').write_text(''.join(difflib.unified_diff(OLD_RUNNER.read_text().splitlines(True),s.splitlines(True),fromfile=str(OLD_RUNNER),tofile=str(NEW_RUNNER))))
    (HERE/'scorer.diff').write_text(''.join(difflib.unified_diff(old_scoring.splitlines(True),sc.splitlines(True),fromfile=str(OLD_SCORER),tofile=str(NEW_SCORER))))
    write(HERE/'derivation_proof.json',dict(status='PASS_SOURCE_DERIVATION_ONLY',
        original_runner_sha256=sha(OLD_RUNNER),derived_runner_sha256=sha(NEW_RUNNER),
        original_scorer_sha256=sha(OLD_SCORER),derived_scorer_sha256=sha(NEW_SCORER),
        scorer_AST_identical_except_BASE_PROTOCOL_and_evidence_scope=True,
        allowed_runner_changes=['output/work/manifest roots','original adapter import root kept',
            'new previously-validated import entry','skip old successful phases and original4 GA',
            'observer persistence without arithmetic changes','new scorer path'],
        numpy_torch_imported=False,model_forwards=0,GA_runs=0,true_arrays_read=0))


def metadata(old):
    # Refresh derivation identities after an explicitly allowed provenance-text correction.
    assert normalized_scorer_ast(NEW_SCORER.read_text())==normalized_scorer_ast(OLD_SCORER.read_text())
    proof=read(HERE/'derivation_proof.json')
    proof.pop('scorer_AST_identical_except_BASE_PROTOCOL',None)
    proof.update(derived_scorer_sha256=sha(NEW_SCORER),
        scorer_AST_identical_except_BASE_PROTOCOL_and_evidence_scope=True,
        scorer_extra_text_change='evidence_scope: one IMPORT_VALIDATED saved producer plus three newly completed GA producers')
    write(HERE/'derivation_proof.json',proof)
    (HERE/'scorer.diff').write_text(''.join(difflib.unified_diff(OLD_SCORER.read_text().splitlines(True),NEW_SCORER.read_text().splitlines(True),fromfile=str(OLD_SCORER),tofile=str(NEW_SCORER))))
    preseal=read(ROOT/'work/S26_clean_recovery/pre_read_seal.json')
    common={}
    for name in ('output.npz','preclean_conf.npz','pairwise_state.npz','preset_parameters.npz',
                 'consumed_inputs.npz','input_colors.npz','optimization_trace.jsonl'):
        p=OLD_BASE/'common_old'/name
        common[name]=dict(path=str(p),sha256=preseal['identities'][str(p)])
    shared={}
    for name in ('control_receipt.json','compatibility_receipt.json',
                 'original_views_receipt.json','ttt_views_receipt.json','filt_views_receipt.json'):
        p=OLD_WORK/name;r=read(p)
        assert r['status']=='PASS' and r['manifest_sha256']==sha(OLD_PREP/'run_manifest.json')
        shared[name]=dict(path=str(p),sha256=sha(p))
        if name=='control_receipt.json':
            shared['control_c2w.npy']=dict(path=str(OLD_WORK/'control_c2w.npy'),sha256=r['output_sha256'])
        for output,h in r.get('outputs',{}).items():shared[output]=dict(path=str(OLD_WORK/output),sha256=h)
    continuation=dict(original_manifest_path=str(OLD_PREP/'run_manifest.json'),
        original_manifest_sha256=sha(OLD_PREP/'run_manifest.json'),
        original_common_receipt_path=str(OLD_BASE/'common_old/receipt.json'),
        recovery_receipt_path=str(RECOVERY),recovery_receipt_sha256=sha(RECOVERY) if RECOVERY.exists() else None,
        recovery_required_status='IMPORT_VALIDATED',
        revised_clean_sha256=sha(ROOT/'work/S26_clean_recovery/clean_reference_torch_fp32.py'),
        shared_artifacts=shared,common_files=common,
        original_failure_policy='Preserve FAILED; imported PASS means narrow IMPORT_VALIDATED only',
        new_GA_runs=3,new_GA_steps=1200,new_model_forwards=0,imported_original_GA_steps=400,
        historical_observations_policy='Explicit NOT_RECORDED; never reconstruct original runtime inventory/scalar')
    candidate=copy.deepcopy(old)
    candidate.pop('frozen_utc',None)
    candidate.update(schema='s26b-saved-output-continuation-v1',status='DRAFT_REQUIRES_INDEPENDENT_REVIEW_AND_ROOT_FREEZE',
        candidate_utc=datetime.now(timezone.utc).isoformat(),continuation=continuation,
        ga_runs=3,ga_steps_per_run=400,numerical_reference=str(HERE/'numerical_reference.py'))
    scoring=candidate['scoring']
    scoring['producer_dirs']={name:str(ROOT/'results/S26B_consumer_baseline'/name) for name in scoring['producer_dirs']}
    scoring['scoring_output']=str(ROOT/'results/S26B_consumer_baseline/scoring')
    scoring['control_sha256']={str(p.relative_to(ROOT)):sha(p) for p in (NEW_SCORER,NEW_PROTOCOL)}
    # Keep every original source identity; add new code/contracts and imported artifacts.
    ids=candidate['identities']
    ids[str(OLD_PREP/'run_manifest.json')]=sha(OLD_PREP/'run_manifest.json')
    ids[str(ROOT/'work/S26_clean_recovery/pre_read_seal.json')]=sha(ROOT/'work/S26_clean_recovery/pre_read_seal.json')
    ids[str(OLD_BASE/'common_old/receipt.json')]=sha(OLD_BASE/'common_old/receipt.json')
    for entry in list(shared.values())+list(common.values()):ids[entry['path']]=entry['sha256']
    for p in (NEW_RUNNER,NEW_SCORER,NEW_PROTOCOL,HERE/'import_previous.py',HERE/'numerical_reference.py',
              HERE/'plan.md',HERE/'derivation_proof.json',Path(__file__),
              ROOT/'work/S26_clean_recovery/clean_reference_torch_fp32.py'):
        ids[str(p)]=sha(p)
    ready=False
    if RECOVERY.exists():
        r=read(RECOVERY);ids[str(RECOVERY)]=sha(RECOVERY)
        ids.update(r.get('input_identities_before_after',{}))
        ids.update(r.get('control_identities',{}))
        ready=r.get('status')=='IMPORT_VALIDATED' and r.get('passed') is True
    write(HERE/'manifest_candidate.json',candidate)
    write(HERE/'preparation_receipt.json',dict(status='PASS_DRAFT_METADATA_ONLY',
        recorded_utc=datetime.now(timezone.utc).isoformat(),independent_recovery_available=ready,
        executable_or_frozen=False,manifest_candidate_sha256=sha(HERE/'manifest_candidate.json'),
        source_proof_sha256=sha(HERE/'derivation_proof.json'),
        metadata_shared_artifact_count=len(shared),common_artifact_count=len(common),
        true_array_decodes=0,RGB_PNG_NPZ_bytes_read=0,GT_file_reads=0,model_forwards=0,GA_runs=0,
        source_and_old_frozen_files_modified=False,
        note='Only metadata/source read. Existing recovery diagnostic JSON contains derived-camera numerical fields; this preparation uses pre-read seal identities, not those values.',
        next_gate='Independent reviewer must inspect import scope, recovery identities, runner diff and reference before root freeze'))
    print(json.dumps(dict(status='DRAFT_READY_NOT_FROZEN',recovery_available=ready,
        new_GA_runs_if_executed=3,new_model_forwards=0,manifest_candidate_sha256=sha(HERE/'manifest_candidate.json'))))


def main():
    old=read(OLD_PREP/'run_manifest.json')
    assert old['status']=='FROZEN'
    assert old['identities'][str(OLD_RUNNER)]==sha(OLD_RUNNER)
    assert old['identities'][str(OLD_SCORER)]==sha(OLD_SCORER)
    if sys.argv[1:]!=['--metadata']:generate_sources(old)
    metadata(old)
    assert 'numpy' not in sys.modules and 'torch' not in sys.modules


if __name__=='__main__':main()
