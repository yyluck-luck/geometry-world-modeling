"""Prepare S33 from sealed JSON/source only: never opens real tensors or images."""
import ast
import copy
import difflib
import json
from pathlib import Path
import sys
from run_s33 import utc,read,sha,write,require,module,load_s32,derive_observer,derive_window_worker,derive_dispatch,SCHEMA,ENDPOINT
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');HERE=Path(__file__).resolve().parent
S32_SHA='340c1b7b9e246fb088db8a50194d3003e1e384ecb05a24dc901bda2ff7bdca60'

def main():
    target=HERE/'contract_candidate.json';require(not target.exists(),'Preserve candidate history before changing')
    parent_path=ROOT/'work/S32_preparation/B_contract.json';require(sha(parent_path)==S32_SHA,'Original S32 B frozen contract')
    prior=read(parent_path);require(prior['status']=='FROZEN','S32 frozen')
    c=copy.deepcopy(prior)
    for k in ('frozen_utc','candidate_sha256','independent_review','root_review','s31_normalizer'):
        c.pop(k,None)
    c.update(schema=SCHEMA,status='CANDIDATE_NOT_FROZEN',prepared_utc=utc(),runner=str(HERE/'run_s33.py'),
        s32_runner=str(ROOT/'work/S32_preparation/run_consumer.py'),s32_contract=str(parent_path),s32_contract_sha256=S32_SHA,
        output_root=str(ROOT/'results/S33_pair_scale_control'),execution_root=str(ROOT/'work/S33_execution'),
        endpoints=[ENDPOINT],references={},tolerances=dict(scale_mean_atol=1e-5,scale_ratio_atol=1e-5,scale_ratio_rtol=1e-5),
        initial_checkpoint='Exactly all33 raw/metadata and all decoded/objective/alignment bytes match own S32 before factor installation',
        unavailable_policy='Missing pose or new whole-window failure: new candidate4 rows NA; original S32 old48 rows retained',
        scorer_output_root=str(ROOT/'results/S33_pair_scale_scoring'),
        expected_design=dict(windows=4,old_endpoint_groups=12,old_rows=48,new_endpoint_groups=4,new_rows=16,total_groups=16,total_rows=64,metadata_eligible_windows=3,expected_scored_rows=48,expected_NA_rows=16,missing_pose_windows=['fr2_desk_j1']),
        scoring_barrier='All four new terminal receipts sealed before separate scoring GT reads; old scoring imported unchanged',
        evidence_scope='One ordinary pair-scale geometric-mean constraint control; no novelty/long-memory/video claim')
    s32=load_s32(c);s30=module(c['s30_runner'],'s33_prepare_s30')
    proof={}
    for name,pair in [('observer',derive_observer(s32,s30,c['s28_runner'])),('window_worker',derive_window_worker(c['s32_runner'])),('dispatch',derive_dispatch(c['s32_runner']))]:
        old,new=pair;compile(ast.Module(body=[new],type_ignores=[]),str(HERE/'run_s33.py')+'::'+name,'exec')
        diff=''.join(difflib.unified_diff((ast.unparse(old)+'\n').splitlines(True),(ast.unparse(new)+'\n').splitlines(True),fromfile='frozen_S32_'+name,tofile='S33_'+name))
        (HERE/(name+'.diff')).write_text(diff)
        import hashlib
        proof[name]=dict(old_AST_sha256=hashlib.sha256(ast.dump(old).encode()).hexdigest(),new_AST_sha256=hashlib.sha256(ast.dump(new).encode()).hexdigest(),diff_sha256=sha(HERE/(name+'.diff')))
    c['identities'][str(parent_path)]=S32_SHA
    for window in c['windows']:
        p=Path(prior['output_root'])/window['id']/'receipt.json';r=read(p)
        require(r['contract_sha256']==S32_SHA and r['window_id']==window['id'],'Same S32 producer identity')
        expected='UNAVAILABLE' if any(f['gt_time'] is None for f in window['frames']) else 'PASS'
        require(r['status']==expected,'Preserve4 fixed statuses')
        names=['GA/C2a/initial_raw.npz','GA/C2a/initial_raw_metadata.json','GA/C2a/initial_decoded.npz','GA/C2a/controlled_alignment.npz'] if expected=='PASS' else []
        c['references'][window['id']]=dict(receipt=str(p),receipt_sha256=sha(p),status=expected,
            files={n:r['outputs'][n] for n in names},byte_verification='Runtime before optimization; preparation reads producer JSON only')
        c['identities'][str(p)]=sha(p)
    metric=ROOT/'results/S32_consumer_scoring/metrics.json';mr=ROOT/'results/S32_consumer_scoring/receipt.json';receipt=read(mr)
    require(receipt['status']=='PASS' and receipt['output_sha256']['metrics.json']==sha(metric),'Old48 score seal')
    c['old_scoring']=dict(metrics=str(metric),metrics_sha256=sha(metric),receipt=str(mr),receipt_sha256=sha(mr),manifest_sha256=receipt['scoring_manifest_sha256'])
    write(HERE/'derivation_proof.json',dict(status='PASS_STATIC_ONLY',recorded_utc=utc(),proof=proof,
        changes=['single existing MST boundary callback replaces same-window serialization gate with S32 identity gate plus differentiable factor',
        'same original GA worker; one new endpoint replaces old three-endpoint save/normalization block',
        'dispatch truth labels and S33 CLI source path only'],forward_count=403,
        actual_access=dict(torch_import=0,numpy_import=0,NPZ=0,RGB=0,GT=0,model=0,MST=0,GA=0)))
    binding=read(c['parent_manifest'])['binding'];base=Path(binding['embedded_root'])/'cloud_opt/dust3r_opt/base_opt.py'
    require(binding['source_identities'][str(base)]==sha(base),'Frozen base scale source')
    own=[HERE/'run_s33.py',HERE/'prepare_candidate.py',HERE/'PROTOCOL_CANDIDATE.md',HERE/'derivation_proof.json',
        HERE/'observer.diff',HERE/'window_worker.diff',HERE/'dispatch.diff',metric,mr,base,
        ROOT/'work/S32_next_decision/review.md',ROOT/'work/S32_next_decision/sources.json']
    c['identities'].update({str(p):sha(p) for p in own})
    for p,h in c['identities'].items():require(sha(p)==h,'Source/JSON identity changed while preparing '+p)
    require('torch' not in sys.modules and 'numpy' not in sys.modules,'No scientific library imported in preparation')
    source_manifest=dict(recorded_utc=utc(),read_scope='Bound inherited source/JSON plus S33 AST preparation; no file array/pixel payload opened',identities=c['identities'],source_references=c['references'],
        original_vmem_commit='39291e4f272f6b4f270691d930926ab5930f942e',supervisor_commit='207bc6f7a1aa107e544099c2c7cc86816fba9628')
    write(HERE/'source_read_manifest.json',source_manifest);c['identities'][str(HERE/'source_read_manifest.json')]=sha(HERE/'source_read_manifest.json')
    write(target,c)
    command=[str(ROOT/'.venv-cut3r/bin/python'),str(HERE/'run_s33.py'),'dispatch','--contract',str(HERE/'contract.json'),'--sha256','ROOT_TO_INSERT_ACTUAL_FROZEN_SHA']
    r=dict(status='PASS_PREPARATION_ONLY',completed_utc=utc(),candidate_sha256=sha(target),runner_sha256=sha(HERE/'run_s33.py'),
        inherited_S32_contract_sha256=S32_SHA,identity_count=len(c['identities']),actual_access=dict(torch_import=0,numpy_import=0,real_NPZ=0,RGB=0,GT=0,model=0,MST=0,GA=0),
        future_command_argv=command,execution='Not invoked; candidate cannot execute',required_next='Different-author static review, parent frozen contract; scorer prepared separately')
    write(HERE/'preparation_receipt.json',r);print(json.dumps(r,indent=2))
if __name__=='__main__':main()
