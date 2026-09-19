"""Stdlib-only source/JSON preparation. Never opens NPZ, RGB, or GT bytes."""
from __future__ import annotations
import ast
import difflib
from pathlib import Path
import run_candidate as r


HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PARENT=ROOT/'work/S26B_preparation/run_manifest.json'


def main():
    m=r.read(PARENT)
    runner=ROOT/'scripts/s26b_consumer_baseline.py'
    scorer=ROOT/'scripts/score_s26b_consumer.py'
    optimizer=Path(m['binding']['embedded_root'])/'cloud_opt/dust3r_opt/optimizer.py'
    old_worker,new_worker=r.derive_worker(runner)
    old_getter,new_getter=r.derive_getter(optimizer)
    for label,old,new in [('worker',old_worker,new_worker),('getter',old_getter,new_getter)]:
        before=ast.unparse(old)+'\n';after=ast.unparse(new)+'\n'
        (HERE/(label+'_original.py.txt')).write_text(before)
        (HERE/(label+'_derived.py.txt')).write_text(after)
        (HERE/(label+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=label+'_original',tofile=label+'_derived')))
    checks=[]
    for path in [HERE/'run_candidate.py',HERE/'score_candidate.py',Path(__file__).resolve()]:
        compile(path.read_text(),str(path),'exec');checks.append(str(path))
    proof=dict(status='PASS_STATIC_DERIVATION_ONLY',utc=r.utc(),worker_changes=['mode guard','frame count = 4','archive = common_old_depth_original4'],
        getter_changes=['single res assignment expression'],worker_normalized_AST_exact=True,getter_normalized_AST_exact=True,
        original_observer_and_ga_validation_reused=True,score_math_called_from_original_source=True,
        compiled_sources=checks,model_forwards=0,GA_runs=0,real_array_reads=0,sensor_png_byte_reads=0,numeric_tests=0)
    r.write(HERE/'derivation_proof.json',proof)
    controls={}
    for name in ['control_receipt.json','compatibility_receipt.json']:
        path=ROOT/'work/S26B_execution'/name;rec=r.read(path)
        r.require(rec['status']=='PASS' and rec['manifest_sha256']==r.sha(PARENT),'Existing successful control/compat')
        controls[str(path)]=r.sha(path)
    # Inherit byte identities without reading the actual camera or any archive.
    camera=ROOT/'work/S26B_execution/control_c2w.npy'
    controls[str(camera)]=r.read(ROOT/'work/S26B_execution/control_receipt.json')['output_sha256']
    keys=['prediction_shape_hw','sensor_shape_hw','sensor_depth_divisor','nearest_mapping','gt_valid',
          'prediction_invalid','invalid_policy','aggregation','gt_scale_fit','confidence_mask','far_depth_cut',
          'delta1_threshold','delta1_comparison']
    semantic_receipt=ROOT/'work/S28_root_getter_semantics/receipt.json'
    semantic=r.read(semantic_receipt)
    s27receipt=ROOT/'results/S27M_mst_gradient_diagnostic/receipt.json'
    r.require(r.read(s27receipt)['status']=='PASS_DIAGNOSTIC_EXECUTED','S27M premise is actual execution')
    identities={str(PARENT):r.sha(PARENT),str(runner):r.sha(runner),str(scorer):r.sha(scorer),
        str(optimizer):m['binding']['source_identities'][str(optimizer)],str(s27receipt):r.sha(s27receipt),
        str(semantic_receipt):r.sha(semantic_receipt),**controls}
    # The original semantic check source is bound via all .py files in that small
    # dedicated directory; no arrays or generic outputs are read here.
    for p in semantic_receipt.parent.glob('*.py'):identities[str(p)]=r.sha(p)
    for path in HERE.iterdir():
        if path.is_file() and path.name not in {'contract_candidate.json','preparation_receipt.json','plan_receipt.json','contract.json','execution_pre_review.json'}:
            identities[str(path)]=r.sha(path)
    c=dict(status='CANDIDATE_NOT_EXECUTABLE',schema='s28-matched-gradient-only-v1',prepared_utc=r.utc(),
        parent_runner=str(runner),parent_scorer=str(scorer),parent_manifest=str(PARENT),parent_manifest_sha256=r.sha(PARENT),
        optimizer_source=str(optimizer),runner=str(HERE/'run_candidate.py'),scorer=str(HERE/'score_candidate.py'),
        output_root=str(ROOT/'results/S28_gradient_scale_control'),execution_root=str(ROOT/'work/S28_execution'),
        arms=['original','gradient_only'],steps_per_arm=400,model_forwards=0,seconds_per_arm=600,rss_bytes_per_arm=16*1024**3,
        suggested_output_reserve_bytes=2*1024**3,scoring_seconds=180,scoring_rss_bytes=2*1024**3,
        input_heads=m['candidate']['archives']['common_old_depth_original4'],frame_count=4,prepared_PIL_count=8,
        depth_input=None,camera_role='previously sealed common oracle optical c2w, no second coordinate flip',
        seed=0,torch_threads=8,lr=.01,schedule='linear',init='original MST/PnP; no orientation repair',
        scoring_policy_keys=keys,scoring_policy={k:m['scoring'][k] for k in keys},gt_depth_frames=m['scoring']['gt_depth_frames'][:4],
        s27m_premise_receipt=str(s27receipt),root_synthetic_getter_receipt=str(semantic_receipt),
        identities=identities,evidence_scope='Known common4 component engineering control, not blind/new-method/video evidence')
    r.write(HERE/'contract_candidate.json',c)
    r.write(HERE/'preparation_receipt.json',dict(status='DRAFT_PREPARED_NOT_RUN',utc=r.utc(),
        candidate_sha256=r.sha(HERE/'contract_candidate.json'),identities_count=len(identities),
        model_forwards=0,GA_runs=0,real_array_reads=0,sensor_png_byte_reads=0,numeric_tests=0,
        next='Independent review, root freeze, then future execution only'))
    print(r.sha(HERE/'contract_candidate.json'))


if __name__=='__main__':main()
