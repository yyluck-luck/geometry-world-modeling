"""S34 source/JSON-only preparation. Does not open arrays/RGB/GT/model bytes."""
import ast
import difflib
from pathlib import Path
import produce_geometry as run

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    parent=ROOT/'work/S26B_preparation/run_manifest.json';m=run.read(parent)
    s28=ROOT/'work/S28_gradient_scale_control/run_candidate.py';s30=ROOT/'work/S30_scale_optimization_preparation/run_s30.py'
    parent_runner=ROOT/'scripts/s26b_consumer_baseline.py';opt=Path(m['binding']['embedded_root'])/'cloud_opt/dust3r_opt/optimizer.py'
    r=run.module(s28,'s34_prepare_s28');p30=run.module(s30,'s34_prepare_s30')
    derivations={}
    for label,(old,new) in {'observer':run.derive_observer(p30,s28),'worker':run.derive_worker(parent_runner),'getter':r.derive_getter(opt)}.items():
        before=ast.unparse(old)+'\n';after=ast.unparse(new)+'\n'
        (HERE/(label+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='previous_'+label,tofile='S34_'+label)))
        compile(ast.fix_missing_locations(ast.Module(body=[new],type_ignores=[])),label,'exec')
        derivations[label]=dict(before_ast_sha256=run.hashlib.sha256(ast.dump(old,include_attributes=False).encode()).hexdigest(),after_ast_sha256=run.hashlib.sha256(ast.dump(new,include_attributes=False).encode()).hexdigest())
    for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
    old_dir=ROOT/'results/S29_scale_control/C2a';old_receipt=old_dir/'receipt.json';rec=run.read(old_receipt)
    control_receipt=ROOT/'work/S26B_execution/control_receipt.json';control=run.read(control_receipt)
    old_input=run.read(old_dir/'inputs_seal.json')
    run.require(old_input['saved_heads']==m['candidate']['archives']['common_old_depth_original4'],'Actual S29 input archive chain')
    run.require(old_input['control_sha256']==control['output_sha256'],'Existing common camera metadata identity')
    assets={str(old_dir/name):rec['outputs'][name] for name in ('initial_raw.npz','initial_decoded.npz')}
    assets[str(ROOT/'work/S26B_execution/control_c2w.npy')]=control['output_sha256']
    for record in m['candidate']['frames']+m['candidate']['archives']['cut3r']+m['candidate']['archives']['common_old_depth_original4']:
        assets[record['path']]=record['sha256']
    paths=[parent,parent_runner,s28,s30,opt,old_receipt,old_dir/'inputs_seal.json',old_dir/'initial_raw_metadata.json',
        control_receipt,ROOT/'work/S26B_execution/compatibility_receipt.json',ROOT/'results/S30_scale_optimization/C2a/s29_reference_gate.json',
        ROOT/'work/S29_scale_control_preparation/contract.json',ROOT/'results/S29_scale_control/validation/receipt.json',
        ROOT/'work/S28_root_getter_semantics/receipt.json',ROOT/'work/S33_preparation/run_s33.py']
    identities={str(p):run.sha(p) for p in paths}
    run.write(HERE/'source_read_manifest.json',dict(recorded_utc=run.utc(),sources=identities,
        read_scope='Source/AST and existing JSON only; scientific array/image SHA inherited but bytes not read',
        selected_original_consumer_commit=m['binding']['source_commit'],derivations=derivations,
        inherited_parent_identities=len(m['identities']),dependency_policy='No new directory walk: frozen parent map, verify actual loaded geometry/overlay at runtime'))
    run.write(HERE/'derivation_proof.json',dict(status='PASS_STATIC_ONLY',derivations=derivations,
        worker_changes=['allowed arm guard','same cut3r 8head archive route','explicit S29 zero old-depth provenance entry'],
        observer_changes=['current mixed8 initial callback','first4 frozen gradNone/last4 grad finite','8leaf gradient diagnostic','truthful stage labels'],
        unchanged=['S26B GA objective/Adam/400/linear/clean/output math/independent numerical gates','S28 one-expression getter repair'],
        raw_expected_names=sorted(run.raw_keys(8)),raw_expected_count=len(run.raw_keys(8)),
        no_arrays_or_GT_read=True,model=0,MST=0,GA=0,numeric_tests=0))
    for p in HERE.iterdir():
        if p.is_file() and p.name not in ('contract_candidate.json','contract.json','preparation_receipt.json'):identities[str(p)]=run.sha(p)
    c=dict(schema=run.SCHEMA,status='CANDIDATE_NOT_EXECUTABLE',prepared_utc=run.utc(),runner=str(HERE/'produce_geometry.py'),
        parent_manifest=str(parent),parent_manifest_sha256=run.sha(parent),parent_runner=str(parent_runner),s28_runner=str(s28),s30_runner=str(s30),optimizer_source=str(opt),
        old_receipt=str(old_receipt),old_inputs_seal=str(old_dir/'inputs_seal.json'),old_raw=str(old_dir/'initial_raw.npz'),old_raw_metadata=str(old_dir/'initial_raw_metadata.json'),old_decoded=str(old_dir/'initial_decoded.npz'),
        s30_initial_gate=str(ROOT/'results/S30_scale_optimization/C2a/s29_reference_gate.json'),control_receipt=str(control_receipt),control_array=str(ROOT/'work/S26B_execution/control_c2w.npy'),
        old_heads=m['candidate']['archives']['common_old_depth_original4'],eight_heads=m['candidate']['archives']['cut3r'],frames=m['candidate']['frames'],
        output_root=str(ROOT/'results/S34_geometry_producer'),execution_root=str(ROOT/'work/S34_producer_execution'),arms=list(run.ARMS),endpoints=list(run.ENDPOINTS),steps=400,
        limits=dict(threads=8,common_seconds=120,common_rss=4*1024**3,arm_seconds=240,arm_rss=8*1024**3,min_disk_bytes=10*1024**3),
        tolerance=dict(atol=1e-5,rtol=1e-5,objective_atol=1e-5,objective_rtol=1e-4),identities=identities,assets=assets,
        asset_identity_evidence='Inherited sealed receipt hashes, not new byte reads; frozen runtime verifies before/after',
        consumer_contract='Separate root-frozen producer/consumer/scorer closure; all four PASS packets before consumer, all three endpoints before GT',
        scope='One known first8 camera-oracle replay with shared predicted old4, ordinary baselines, no default contextIDs or video')
    run.write(HERE/'contract_candidate.json',c)
    run.write(HERE/'preparation_receipt.json',dict(status='PREPARED_NOT_EXECUTED',recorded_utc=run.utc(),candidate_sha256=run.sha(HERE/'contract_candidate.json'),
        runner_sha256=run.sha(HERE/'produce_geometry.py'),source_identity_count=len(identities),inherited_asset_count=len(assets),
        static_compile=True,help_exitcode=0,pre_review_corrections=['Replaced same-path common receipt tautology with captured old_receipt_sha compared at arm completion'],model=0,MST=0,GA=0,scientific_array_byte_reads=0,GT_byte_reads=0,numeric_tests=0,
        CLI=[str(ROOT/'.venv-cut3r/bin/python'),str(HERE/'produce_geometry.py'),'dispatch','--contract',str(HERE/'contract.json'),'--sha256','ROOT_FROZEN_SHA_REQUIRED']))
    print(run.sha(HERE/'contract_candidate.json'))

if __name__=='__main__':main()
