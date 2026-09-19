#!/usr/bin/env python3
"""Source and JSON metadata preparation only; never imports the review module."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    started=utc();timer=time.perf_counter()
    if any((HERE/n).exists() for n in ('candidate.json','preparation_receipt.json','attempt.json','receipt.json')):
        raise RuntimeError('Never overwrite a preparation or execution receipt')
    scorer_path=ROOT/'work/S34_scoring_preparation/manifest_candidate.json'
    producer_path=ROOT/'work/S34_preparation/contract_candidate.json'
    scorer=read(scorer_path);producer=read(producer_path)
    assert scorer['status']=='CANDIDATE_NOT_EXECUTABLE'
    assert producer['schema']=='s34-shared-old4-eight-frame-consumer-v1'
    paths=[HERE/'recompute.py',HERE/'protocol.md',Path(__file__).resolve(),ROOT/'work/S28_independent_numeric_review/recompute.py']
    paths += [Path(p) for p in scorer['control_sha256']]
    paths += [Path(producer[k]) for k in ('runner','parent_runner','s28_runner','s30_runner','optimizer_source')]
    paths += [ROOT/'work/S34_preparation/protocol_candidate.md']
    ids={str(p):sha(p) for p in paths}
    for p,h in scorer['control_sha256'].items():assert ids[p]==h
    for k in ('runner','parent_runner','s28_runner','s30_runner','optimizer_source'):
        p=producer[k];assert ids[p]==producer['identities'][p]
    helper=ROOT/'work/S28_independent_numeric_review/recompute.py'
    assert ids[str(helper)]=='2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2'
    checks=[]
    for p in (HERE/'recompute.py',Path(__file__).resolve()):
        source=p.read_text();tree=ast.parse(source);compile(tree,str(p),'exec')
        checks.append(dict(path=str(p),sha256=ids[str(p)],AST_compile=True,module_executed=False))
    inherited=read(ROOT/'work/S26_scoring_preparation/candidate_scoring_inputs.json')['gt_depth_frames'][4:8]
    assert scorer['gt_depth_frames']==inherited and [x['index'] for x in inherited]==[4,5,6,7]
    c=dict(schema='s34-independent-saved-review-candidate-v1',status='CANDIDATE_UNBOUND_DO_NOT_EXECUTE',prepared_utc=utc(),
        resource=dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),source_sha256=ids,gt_depth_frames=inherited,
        observed_metadata_sha256={str(scorer_path):sha(scorer_path),str(producer_path):sha(producer_path)},
        required_future_binding=dict(schema='s34-independent-saved-review-binding-v1',status='FROZEN',
            candidate_sha256='ROOT_FILLS_AFTER_SOURCE_REVIEW',producer_contract=dict(path=str(ROOT/'work/S34_preparation/contract.json'),sha256=None),
            scoring_manifest=dict(path=str(ROOT/'work/S34_scoring_preparation/manifest.json'),sha256=None),
            scoring_receipt=dict(path=str(ROOT/'results/S34_depth_scoring/receipt.json'),sha256=None),producer_source_sha256=ids[producer['runner']]),
        scope=dict(new_score_rows=12,new_score_groups=3,actual_GT_images_after_freeze=4,raw_boundary_tensors=228,cross_arm_initial_raw=57,
            saved_steps_per_arm=400,scale_edges=7,consumer_math_independent=False,new_model=0,new_GA=0,new_backward=0,new_clean=0,new_k=0),
        preparation_scope='Only source/text/metadata; no array or sensor bytes; no scientific imports/execution; metric and trace checks not yet run')
    write(HERE/'candidate.json',c)
    receipt=dict(status='PASS_SOURCE_PREPARATION_ONLY',started_utc=started,completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
        command='python3 work/S34_independent_numeric_review/prepare_candidate.py',cwd=str(ROOT),
        checks=checks,source_sha256=ids,metadata_sha256=c['observed_metadata_sha256'],candidate_sha256=sha(HERE/'candidate.json'),
        real_arrays_read=0,RGB_bytes_read=0,sensor_GT_bytes_read=0,scientific_modules_imported=0,scientific_runs=0,synthetic_tests=0,
        next='Root static source review, formal binding, actual scoring PASS, then root single bounded execution; no automatic execution')
    write(HERE/'preparation_receipt.json',receipt)
    print(json.dumps(dict(status=receipt['status'],candidate_sha256=receipt['candidate_sha256'],source_sha256=ids[str(HERE/'recompute.py')],
        protocol_sha256=ids[str(HERE/'protocol.md')],receipt_sha256=sha(HERE/'preparation_receipt.json'))))

if __name__=='__main__':main()
