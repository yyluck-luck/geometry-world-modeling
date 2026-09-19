"""Source/JSON-only S29 preparation. No real arrays or numerical imports."""
import ast
from pathlib import Path
import run_s29 as r

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    parent=ROOT/'work/S26B_preparation/run_manifest.json';m=r.read(parent)
    embedded=Path(m['binding']['embedded_root'])
    init=embedded/'cloud_opt/dust3r_opt/init_im_poses.py'
    opt=embedded/'cloud_opt/dust3r_opt/optimizer.py'
    base=embedded/'cloud_opt/dust3r_opt/base_opt.py'
    s28=ROOT/'work/S28_gradient_scale_control/run_candidate.py'
    helper=r.module(s28,'s29_source_only_s28_helpers')
    old,new=helper.derive_getter(opt)
    import difflib
    (HERE/'getter.diff').write_text(''.join(difflib.unified_diff((ast.unparse(old)+'\n').splitlines(True),(ast.unparse(new)+'\n').splitlines(True),fromfile='original_get_depthmaps',tofile='S28_gradient_get_depthmaps')))
    scope=[(init,['init_minimum_spanning_tree','init_from_pts3d','align_multiple_poses','fast_pnp']),
           (opt,['_set_depthmap','get_depthmaps']), (base,['compute_global_alignment','global_alignment_loop']),
           (s28,['derive_getter','snapshot','assert_same_objects'])]
    records=[]
    for path,names in scope:
        tree=ast.parse(path.read_text());functions=[]
        for name in names:
            found=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
            r.require(len(found)==1,'Unique source hook: '+name)
            functions.append(dict(name=name,start_line=found[0].lineno,end_line=found[0].end_lineno))
        records.append(dict(path=str(path),sha256=r.sha(path),scope='Original source/AST hook inspection, no execution',functions=functions))
    for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
    r.write(HERE/'source_read_manifest.json',dict(utc=r.utc(),status='SOURCE_ONLY',files=records,
        active_change='Original alignment called once then only s/T return replaced; R0 unchanged; existing S28 getter AST repair',
        observer_changes='Immediate copied prefix/prelog/state captures; original loop replaced by pre-optimizer sentinel; forbidden backward/step/clean guards',
        mathematical_source_edits=0,model=0,MST=0,GA=0,real_array_reads=0,GT_byte_reads=0,numeric_tests=0))
    reference_dir=ROOT/'results/S28_gradient_scale_control/gradient_only';reference_receipt=reference_dir/'receipt.json';rec=r.read(reference_receipt)
    r.require(rec['status']=='PASS','Completed historical B required')
    reference=dict(receipt=str(reference_receipt),files={name:dict(path=str(reference_dir/name),sha256=rec['outputs'][name]) for name in ['initial_raw.npz','initial_decoded.npz']})
    runner=ROOT/'scripts/s26b_consumer_baseline.py'
    control=ROOT/'work/S26B_execution/control_receipt.json'
    cr=r.read(control);r.require(cr['status']=='PASS' and cr['manifest_sha256']==r.sha(parent),'Completed camera control')
    identities={str(p):r.sha(p) for p in [parent,runner,s28,init,opt,base,control,reference_receipt,
        ROOT/'work/S28_gradient_scale_control/contract.json',ROOT/'scripts/s27m_mst_gradient_diagnostic.py',
        ROOT/'work/S17C_independent_preparation/numerical_reference.py']}
    # Inherit the existing camera SHA without opening the actual NPY now.
    identities[str(control.parent/'control_c2w.npy')]=cr['output_sha256']
    for p in HERE.iterdir():
        if p.is_file() and p.name not in ['contract_candidate.json','preparation_receipt.json','contract.json']:
            identities[str(p)]=r.sha(p)
    c=dict(schema='s29-init-scale-controls-v1',status='CANDIDATE_NOT_EXECUTABLE',prepared_utc=r.utc(),
        runner=str(HERE/'run_s29.py'),validator=str(HERE/'validate_s29.py'),parent_runner=str(runner),parent_manifest=str(parent),
        parent_manifest_sha256=r.sha(parent),s28_runner=str(s28),s28_contract_sha256=rec['s28_contract_sha256'],optimizer_source=str(opt),
        control_receipt=str(control),control_camera=str(control.parent/'control_c2w.npy'),objective_reference=str(ROOT/'work/S17C_independent_preparation/numerical_reference.py'),
        output_root=str(ROOT/'results/S29_scale_control'),execution_root=str(ROOT/'work/S29_execution'),
        reference_B=reference,arms=['C2t','C2a'],per_arm_seconds=60,per_arm_rss_bytes=4*1024**3,
        validation_seconds=60,validation_rss_bytes=4*1024**3,torch_threads=8,seed=0,frame_count=4,prepared_PIL_count=8,
        tolerance=dict(atol=1e-5,rtol=1e-5),objective_tolerance=dict(atol=1e-5,rtol=1e-4),
        counts_per_arm=dict(MST=1,PnP=3,alignment=1,objective=1,backward=0,Adam=0,clean=0,model=0,GT=0),
        intervention=dict(C2t='s0,R0,mean(target_centers)-s0*R0@mean(source_centers)',C2a='1,R0,mean(target_centers)-R0@mean(source_centers)'),
        identities=identities,evidence_scope='Two zero-step controls on known common4; no sensor-depth or accuracy score, no research novelty claim')
    r.write(HERE/'contract_candidate.json',c)
    r.write(HERE/'preparation_receipt.json',dict(status='PREPARED_NOT_EXECUTED',utc=r.utc(),candidate_sha256=r.sha(HERE/'contract_candidate.json'),
        bound_identity_count=len(identities),real_array_reads=0,GT_byte_reads=0,numeric_tests=0,MST=0,GA=0,model=0,
        next='Root full source review, independent review, separate freeze; no later 400-step implementation'))
    print(r.sha(HERE/'contract_candidate.json'))


if __name__=='__main__':main()
