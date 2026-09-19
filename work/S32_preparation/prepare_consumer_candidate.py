"""Prepare B metadata/source contract after successful A, without opening arrays."""
from pathlib import Path
import ast
import difflib
import sys
from run_inference import read, sha, write, module, require, utc

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=Path(__file__).resolve().parent
A_SHA='1749d83fac56a8c7f50b74d37e2278239df25534318967fa93f4798eb5054124'


def main():
    require(not (HERE/'B_contract_candidate.json').exists(),'Preserve previous candidate before updating')
    A_path=HERE/'contract.json';require(sha(A_path)==A_SHA,'Actual frozen A')
    A=read(A_path);selection=read(A['selection'])
    require(sha(A['selection'])==A['selection_sha256'],'Same fixed four windows')
    source_manifest=ROOT/'work/S26B_preparation/run_manifest.json'
    require(sha(source_manifest)=='147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c','Bound existing source manifest')
    parent=read(source_manifest)
    s28=ROOT/'work/S28_gradient_scale_control/run_candidate.py';s30=ROOT/'work/S30_scale_optimization_preparation/run_s30.py'
    s30_contract=ROOT/'work/S30_scale_optimization_preparation/contract.json'
    require(sha(s30_contract)=='000fa5d5b19cc516a581b382e457dcf8e03494da50b220d8f32c0ad0b16224a3','Frozen original scoring policy source')
    source=ROOT/'scripts/s26b_consumer_baseline.py';normalizer=ROOT/'work/S31_scale_shape_preparation/run_s31.py'
    runner=HERE/'run_consumer.py';r=module(s28,'s32_B_prepare_s28');prior=module(s30,'s32_B_prepare_s30');current=module(runner,'s32_B_prepare_current')
    proof={}
    for name,pair in [('worker',current.derive_worker(r,source)),('observer',current.derive_observer(prior,s28))]:
        old,new=pair
        compile(ast.Module(body=[new],type_ignores=[]),str(runner)+'::'+name,'exec')
        text=''.join(difflib.unified_diff((ast.unparse(old)+'\n').splitlines(True),(ast.unparse(new)+'\n').splitlines(True),fromfile='frozen_parent_'+name,tofile='S32_B_'+name))
        (HERE/('B_'+name+'.diff')).write_text(text)
        proof[name]=dict(old_AST_sha256=__import__('hashlib').sha256(ast.dump(old).encode()).hexdigest(),new_AST_sha256=__import__('hashlib').sha256(ast.dump(new).encode()).hexdigest(),diff_sha256=sha(HERE/('B_'+name+'.diff')))
    require('torch' not in sys.modules and 'numpy' not in sys.modules,'Preparation imports must stay stdlib/source only')
    receipts={};identities={}
    for window in selection['windows']:
        p=Path(A['output_root'])/window['id']/'receipt.json';entry=read(p)
        require(entry['status']=='PASS_INFERENCE_SEALED' and entry['contract_sha256']==A_SHA,'Every A window sealed')
        receipts[window['id']]=dict(path=str(p),sha256=sha(p));identities[str(p)]=sha(p)
        heads=p.parent/'head_archive_records.json';require(sha(heads)==entry['outputs'][heads.name],'A head list identity')
        rows=read(heads);require(len(rows)==4 and [x['index'] for x in rows]==list(range(4)),'A complete ordered archives')
        identities[str(heads)]=sha(heads)
        # Only JSON metadata is inspected here. Head/preprocessing arrays are
        # opened by the separately frozen B worker and checked against A then.
    write(HERE/'B_derivation_proof.json',dict(status='PASS_STATIC_ONLY',recorded_utc=utc(),proof=proof,
        exact_original_GA_math_reused=True,changed='dispatch guard/frame-count/archive-route; historical initial reference callback/report labels only',
        alignment='Same previously fixed C2a unit-scale/center-mean expression',normalization='Unchanged original S31 decompose',
        actual_access=dict(torch_import=0,numpy_import=0,RGB_read=0,GT_read=0,NPZ_read=0,model=0,GA=0)))
    paths=[runner,HERE/'prepare_consumer_candidate.py',HERE/'B_plan_candidate.md',HERE/'B_derivation_proof.json',HERE/'B_worker.diff',HERE/'B_observer.diff',
        HERE/'run_inference.py',A_path,Path(A['selection']),source_manifest,source,s28,s30,s30_contract,normalizer,
        ROOT/'work/S26_consumer_baseline_preparation/saved_heads_adapter.py',Path(parent['numerical_reference']),
        ROOT/'work/S17C_independent_preparation/numerical_reference.py',ROOT/'work/S26_clean_recovery/clean_reference_torch_fp32.py']
    identities.update({str(p):sha(p) for p in paths})
    c=dict(schema='s32-same-window-c2a-consumer-v1',status='CANDIDATE_NOT_FROZEN',prepared_utc=utc(),runner=str(runner),
        selection=A['selection'],selection_sha256=A['selection_sha256'],windows=selection['windows'],
        A_contract=str(A_path),A_contract_sha256=A_SHA,A_receipts=receipts,parent_manifest=str(source_manifest),
        parent_runner=str(source),s28_runner=str(s28),s30_runner=str(s30),s31_normalizer=str(normalizer),
        optimizer_source=str(Path(parent['binding']['embedded_root'])/'cloud_opt/dust3r_opt/optimizer.py'),
        output_root=str(ROOT/'results/S32_consumer_windows'),execution_root=str(ROOT/'work/S32_B_execution'),
        steps=400,endpoints=list(current.ENDPOINTS),limits=dict(threads=8,seconds_per_window=120,rss_bytes_per_window=4*1024**3),
        initial_checkpoint='Own same-memory MST clone; no new historical S29 reference or second MST',
        unavailable_policy='Missing complete given-camera association, or any whole-window GA failure: all three endpoints NA',
        scorer_output_root=str(ROOT/'results/S32_consumer_scoring'),scoring_policy=read(s30_contract)['scoring_policy'],
        expected_design=dict(windows=4,endpoint_groups=12,per_frame_rows=48,metadata_eligible_windows=3,missing_pose_windows=['fr2_desk_j1']),
        scoring_barrier='All four terminal window receipts sealed; separate scorer only then seals/decodes sensor-depth images',
        identities=identities,evidence_scope='Ordinary controlled consumer windows; same-source initial/400/global-output-scalar; no new method or video claim')
    write(HERE/'B_contract_candidate.json',c)
    result=dict(status='PASS_B_PREPARATION_ONLY',completed_utc=utc(),candidate_sha256=sha(HERE/'B_contract_candidate.json'),runner_sha256=sha(runner),
        A_contract_sha256=A_SHA,all_A_receipts_bound=True,real_arrays_read=0,GT_read=0,new_model=0,new_GA=0)
    write(HERE/'B_preparation_receipt.json',result);print(__import__('json').dumps(result,indent=2))


if __name__=='__main__':main()
