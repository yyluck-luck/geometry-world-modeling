#!/usr/bin/env python3
"""Build S31 candidate from JSON identities only; never read NPZ/PNG bytes."""
import ast
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    target=HERE/'contract_candidate.json';assert not target.exists(),'No candidate overwrite'
    started=datetime.now(timezone.utc).isoformat()
    cp=ROOT/'work/S30_scale_optimization_preparation/contract.json'
    c30sha='000fa5d5b19cc516a581b382e457dcf8e03494da50b220d8f32c0ad0b16224a3'
    assert sha(cp)==c30sha;c30=read(cp);assert c30['status']=='FROZEN'
    sdir=Path(c30['output_root'])/'scoring';srp=sdir/'receipt.json';sr=read(srp)
    irp=ROOT/'work/S30_independent_numeric_review/receipt.json';ir=read(irp)
    assert sr['status']==ir['status']=='PASS' and sr['contract_sha256']==ir['contract_sha256']==c30sha
    assert sr['per_frame_rows']==ir['per_frame_rows']==16 and sr['endpoint_groups']==ir['endpoint_groups']==4
    assert ir['complete_raw_tensor_comparisons']==66 and ir['complete_gradient_records']==800
    source=HERE/'run_s31.py';protocol=HERE/'protocol.md';synthetic=HERE/'synthetic_check_receipt.json'
    test=read(synthetic);assert test['status']=='PASS_SYNTHETIC_ONLY' and test['source_sha256']==sha(source)
    scorer=Path(c30['parent_scorer']);assert sha(scorer)==c30['identities'][str(scorer)]
    for key in ('runner','scorer'):
        assert sha(c30[key])==c30['identities'][c30[key]],'Historical execution source changed'
    sources=[source,protocol,Path(__file__).resolve(),HERE/'synthetic_check.py',synthetic,cp,scorer,
             Path(c30['runner']),Path(c30['scorer']),srp,irp]
    for p in (source,HERE/'synthetic_check.py',Path(__file__).resolve()):ast.parse(p.read_text());compile(p.read_text(),str(p),'exec')
    identities={str(p):sha(p) for p in sources}
    saved={};depth_inputs={};receipts={};metadata_sources={str(srp):sha(srp),str(irp):sha(irp)}
    for arm in ('C2t','C2a'):
        directory=Path(c30['output_root'])/arm;rp=directory/'receipt.json';r=read(rp)
        assert r['status']=='PASS' and r['mode']==arm and r['s30_contract_sha256']==c30sha
        assert r['iterations']==r['adam_steps']==400 and r['clean_calls']==1
        receipts[arm]=str(rp);identities[str(rp)]=sha(rp);metadata_sources[str(rp)]=sha(rp)
        assert sr['input_sha256'][str(rp)]==ir['input_identities_before_after'][str(rp)]==sha(rp)
        for name,h in r['outputs'].items():
            assert Path(name).name==name
            p=str(directory/name);assert sr['input_sha256'][p]==ir['input_identities_before_after'][p]==h;saved[p]=h
        ref=c30['s29_reference'][arm];oldp=Path(ref['receipt']);old=read(oldp)
        assert old['status']=='PASS_INITIALIZATION_EXECUTED' and old['arm']==arm and old['contract_sha256']==c30['s29_contract_sha256']
        identities[str(oldp)]=sha(oldp);metadata_sources[str(oldp)]=sha(oldp)
        assert sr['input_sha256'][str(oldp)]==ir['input_identities_before_after'][str(oldp)]==sha(oldp)
        for name,item in ref['files'].items():
            p=item['path'];h=item['sha256'];assert old['outputs'][name]==sr['input_sha256'][p]==ir['input_identities_before_after'][p]==h;saved[p]=h
        initial=ref['files']['initial_decoded.npz'];finalpath=str(directory/'output.npz')
        depth_inputs[arm]=dict(initial=initial,final=dict(path=finalpath,sha256=saved[finalpath]))
    for name,h in sr['outputs'].items():
        assert Path(name).name==name
        p=str(sdir/name);assert ir['input_identities_before_after'][p]==h;saved[p]=h
    # Only metadata-derived SHA strings and file metadata for saved arrays.
    assert all(Path(p).is_file() for p in saved)
    assert not any(p.endswith(('.npz','.npy','.png')) for p in identities)
    candidate=dict(schema='s31-saved-global-logscale-diagnostic-v1',status='CANDIDATE_NOT_EXECUTABLE',prepared_utc=datetime.now(timezone.utc).isoformat(),
        runner=str(source),protocol=str(protocol),output_root=str(ROOT/'results/S31_scale_shape_diagnostic'),
        s30_contract=str(cp),s30_contract_sha256=c30sha,s30_score_receipt=str(srp),s30_independent_receipt=str(irp),
        s30_producer_receipts=receipts,s30_metrics=str(sdir/'metrics.json'),original_scorer=str(scorer),
        arms=['C2t','C2a'],frame_count=4,depth_shape=[4,384,512],resource=dict(cpu_threads=1,wall_seconds=180,rss_bytes=2*1024**3),
        operation=dict(log_dtype='float64',scale='exp(-mean_all_pixels(log(D400)-log(D0)))',scales_per_arm=1,
            per_frame_scale=False,shift=False,GT_fit=False,filter_pixels=False,output_dtype='float64'),
        sum_squares_tolerance=dict(abs_tol=1e-9,rel_tol=1e-12),log_identity_tolerance=dict(atol=1e-12,rtol=1e-12),
        scoring_policy=c30['scoring_policy'],gt_depth_frames=c30['gt_depth_frames'],depth_inputs=depth_inputs,
        identities=identities,saved_input_sha256=saved,expected_new_score_rows=8,expected_new_mean_groups=2,
        original_endpoint_rows_imported=16,original_endpoint_scores_recomputed=0,
        evidence_scope='Post-hoc prediction-only global output normalization, seen common4; no optimizer/gauge intervention, physical shape destruction inference, or new method claim')
    write(target,candidate)
    write(HERE/'preparation_receipt.json',dict(status='PASS_METADATA_AND_STATIC_PREPARATION_ONLY',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
        candidate_sha256=sha(target),source_sha256=sha(source),protocol_sha256=sha(protocol),metadata_sources_sha256=metadata_sources,
        source_controls_count=len(identities),saved_file_identities_inherited=len(saved),metadata_only_array_existence_check=True,
        actual_checks=['Read S30 frozen contract and PASS producer/scorer/independent receipts','Derive endpoint/whole-product SHA from existing receipts, no saved-array byte reads',
            'Python AST parse and compile, no real run invocation','Existing separately labelled tiny synthetic algebra check'],
        synthetic_receipt_sha256=sha(synthetic),real_NPZ_bytes_read=0,GT_bytes_read=0,new_model=0,new_MST=0,new_GA=0,new_backward=0,
        status_boundary='Preparation success only; no real S31 decomposition or scoring has run'))
    print(json.dumps(dict(status='PREPARED_NOT_EXECUTED',candidate_sha256=sha(target),source_sha256=sha(source),protocol_sha256=sha(protocol),saved_identity_count=len(saved))))


if __name__=='__main__':main()
