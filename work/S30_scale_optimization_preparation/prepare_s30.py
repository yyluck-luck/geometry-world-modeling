"""Prepare S30 using source and existing receipt metadata only."""
import ast
import difflib
from pathlib import Path
import run_s30 as run

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def diff(name,old,new):
    before=ast.unparse(old)+'\n';after=ast.unparse(new)+'\n'
    (HERE/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original_'+name,tofile='S30_'+name)))


def main():
    parent=ROOT/'work/S26B_preparation/run_manifest.json';m=run.read(parent)
    parent_runner=ROOT/'scripts/s26b_consumer_baseline.py';parent_scorer=ROOT/'scripts/score_s26b_consumer.py'
    s28=ROOT/'work/S28_gradient_scale_control/run_candidate.py';s29=ROOT/'work/S29_scale_control_preparation/run_s29.py'
    s29_contract=ROOT/'work/S29_scale_control_preparation/contract.json';s29_sha=run.sha(s29_contract)
    helper=run.module(s28,'s30_source_only_s28')
    old,observer,counts=run.derive_observer(s28);diff('observer',old,observer)
    old,worker=helper.derive_worker(parent_runner);worker.body[0]=ast.parse("require(mode in ('C2t','C2a'),'S30 two common4 scale controls')").body[0]
    ast.fix_missing_locations(worker);diff('worker',old,worker)
    optimizer=Path(m['binding']['embedded_root'])/'cloud_opt/dust3r_opt/optimizer.py'
    old,getter=helper.derive_getter(optimizer);diff('getter',old,getter)
    def unique(path,name):
        found=[n for n in ast.walk(ast.parse(Path(path).read_text())) if isinstance(n,ast.FunctionDef) and n.name==name]
        run.require(len(found)==1,'Unique function '+name);return found[0]
    old_control=unique(s29,'controlled_alignment');new_control=unique(HERE/'run_s30.py','control')
    for target in ['s','T']:
        values=[]
        for function in [old_control,new_control]:
            found=[n.value for n in ast.walk(function) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id==target]
            run.require(len(found)==1,'Unique scale-family expression '+target);values.append(ast.dump(found[0]))
        run.require(values[0]==values[1],'Exact existing S29 scale-family expression: '+target)
    for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
    refs={};identities={str(p):run.sha(p) for p in [parent,parent_runner,parent_scorer,s28,s29,s29_contract,optimizer,
        ROOT/'results/S29_scale_control/validation/receipt.json',ROOT/'work/S29_root_numeric_review/receipt.json']}
    validation=run.read(ROOT/'results/S29_scale_control/validation/receipt.json')
    run.require(validation['status']=='PASS_VALIDATION_EXECUTED' and validation['hypothesis_passed'] is True,'S29 algebra and identity gates completed')
    for arm in ['C2t','C2a']:
        directory=ROOT/'results/S29_scale_control'/arm;receipt=directory/'receipt.json';rec=run.read(receipt)
        run.require(rec['status']=='PASS_INITIALIZATION_EXECUTED' and rec['contract_sha256']==s29_sha,'Both saved S29 conditions')
        refs[arm]=dict(receipt=str(receipt),files={name:dict(path=str(directory/name),sha256=rec['outputs'][name])
            for name in ['initial_raw.npz','initial_raw_metadata.json','initial_decoded.npz','alignment.npz']})
        identities[str(receipt)]=run.sha(receipt)
    records=[]
    for path,names in [(s28,['observer_type','derive_worker','derive_getter','snapshot']),
                       (s29,['controlled_alignment']), (parent_runner,['ga_worker','original_context']),
                       (parent_scorer,['seal_producers','decode_outputs','depth_metrics','aggregate','load_sensor_depths'])]:
        entries=[]
        for name in names:
            node=unique(path,name);entries.append(dict(name=name,start_line=node.lineno,end_line=node.end_lineno))
        records.append(dict(path=str(path),sha256=run.sha(path),functions=entries))
    run.write(HERE/'source_read_manifest.json',dict(utc=run.utc(),files=records,scope='Source/AST inspection; no numerical execution'))
    run.write(HERE/'derivation_proof.json',dict(utc=run.utc(),status='PASS_STATIC_ONLY',observer_edit_counts=counts,
        original_worker_changes=['arm guard','n=4','archive=common_old_depth_original4'],
        s29_scale_and_translation_expressions_AST_exact=True,existing_single_getter_expression_reused=True,
        optimizer_objective_Adam_clean_statements_unchanged=True,score_math_calls_original_functions=True,
        model=0,MST=0,GA=0,real_array_reads=0,GT_byte_reads=0,numeric_tests=0))
    for p in HERE.iterdir():
        if p.is_file() and p.name not in ['contract_candidate.json','preparation_receipt.json','contract.json']:identities[str(p)]=run.sha(p)
    keys=['prediction_shape_hw','sensor_shape_hw','sensor_depth_divisor','nearest_mapping','gt_valid','prediction_invalid',
          'invalid_policy','aggregation','gt_scale_fit','confidence_mask','far_depth_cut','delta1_threshold','delta1_comparison']
    c=dict(schema='s30-s29-initialized-400-v1',status='CANDIDATE_NOT_EXECUTABLE',prepared_utc=run.utc(),
        runner=str(HERE/'run_s30.py'),scorer=str(HERE/'score_s30.py'),parent_runner=str(parent_runner),parent_scorer=str(parent_scorer),
        parent_manifest=str(parent),parent_manifest_sha256=run.sha(parent),s28_runner=str(s28),s29_runner=str(s29),
        s29_contract_sha256=s29_sha,s29_reference=refs,s29_validation_receipt=str(ROOT/'results/S29_scale_control/validation/receipt.json'),optimizer_source=str(optimizer),
        output_root=str(ROOT/'results/S30_scale_optimization'),execution_root=str(ROOT/'work/S30_execution'),
        arms=['C2t','C2a'],steps_per_arm=400,seconds_per_arm=120,rss_bytes_per_arm=4*1024**3,
        scoring_seconds=120,scoring_rss_bytes=2*1024**3,torch_threads=8,seed=0,lr=.01,schedule='linear',
        complete_raw_reference_count=33,scoring_endpoints=['initial','final'],endpoint_frame_count=4,per_frame_score_rows=16,
        scoring_policy={k:m['scoring'][k] for k in keys},gt_depth_frames=m['scoring']['gt_depth_frames'][:4],identities=identities,
        evidence_scope='Ordinary scale-initialization engineering control; saved initial and fixed 400-step final endpoints, known oracle-camera pilot')
    run.write(HERE/'contract_candidate.json',c)
    run.write(HERE/'preparation_receipt.json',dict(status='PREPARED_NOT_EXECUTED',utc=run.utc(),candidate_sha256=run.sha(HERE/'contract_candidate.json'),
        model=0,MST=0,GA=0,real_array_reads=0,GT_byte_reads=0,numeric_tests=0,bound_identity_count=len(identities),
        next='Root full source review, independent review, exact separate freeze, then possible execution'))
    print(run.sha(HERE/'contract_candidate.json'))


if __name__=='__main__':main()
