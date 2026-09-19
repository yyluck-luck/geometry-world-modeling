"""Build a reviewable S26 manifest candidate; freeze only after bound review."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import json
import hashlib
import ast

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'work/S26_consumer_baseline_preparation'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def require(x,msg):
    if not x:raise ValueError(msg)

def candidate():
    target=PREP/'manifest_candidate.json';require(not target.exists(),'Preserve previous candidate')
    inputs=read(PREP/'candidate_inputs.json');binding=read(PREP/'source_binding.json')
    scoring=read(ROOT/'work/S26_scoring_preparation/candidate_scoring_inputs.json')
    p21=ROOT/'work/S21_baseline_preparation/run_manifest.json'
    p22=ROOT/'work/S22_filt_shared_precision/run_manifest.json'
    p17=ROOT/'docs/S17C_EXECUTION_MANIFEST.json'
    m21,m22,m17=map(read,(p21,p22,p17))
    repos=dict(original=inputs['producer_receipts']['common_old_depth_original4']['source'],
               ttt=inputs['producer_receipts']['ttt3r']['source'],filt=inputs['producer_receipts']['filt3r']['source'])
    fn=Path(repos['ttt'])/'eval/relpose/launch.py'
    ref=ROOT/'work/S17C_independent_preparation/numerical_reference.py'
    controls=[Path(__file__).resolve(),ROOT/'scripts/s26_consumer_baseline.py',ROOT/'scripts/score_s26_consumer.py',
        ROOT/'docs/S26_CONSUMER_EXECUTION_PROTOCOL.md',ROOT/'docs/S26_CONSUMER_SCORING_PROTOCOL.md',
        PREP/'saved_heads_adapter.py',PREP/'plan.md',PREP/'candidate_inputs.json',PREP/'source_binding.json',
        PREP/'preparation_receipt.json',ROOT/'work/S26_scoring_preparation/candidate_scoring_inputs.json',
        ROOT/'work/S26_scoring_preparation/preparation_receipt.json',p21,p22,p17,fn,ref]
    ids=dict(binding['source_identities'])
    for m in (m21,m22):
        ids.update({p:h for p,h in m['identities'].items() if any(Path(p).is_relative_to(Path(repo)) for repo in repos.values())})
    ids.update({str(p):sha(p) for p in controls})
    ids.update({x['path']:x['sha256'] for x in inputs['producer_receipts'].values()})
    for p,h in ids.items():require(sha(p)==h,'Preparation changed bound source: '+p)
    for key in ('scripts/s26_consumer_baseline.py','scripts/score_s26_consumer.py'):ast.parse((ROOT/key).read_text())
    deps={p:h for p,h in m17['identities'].items() if Path(p).is_relative_to(Path(m17['overlay']))}
    m=dict(schema='s26-original-consumer-pilot-v1',candidate_utc=datetime.now(timezone.utc).isoformat(),
        status='CANDIDATE_PENDING_INDEPENDENT_REVIEW',candidate=inputs,binding=binding,scoring=scoring,
        identities=ids,dependency_identities=deps,preprocess_repos=repos,preprocess_function=str(fn),
        numerical_reference=str(ref),model_forwards=0,ga_runs=4,ga_steps_per_run=400,
        given_cameras='explicit oracle input',sensor_depth='scoring only, previously exposed S23',
        core_versions={'numpy':'1.26.4','torch':'2.7.0','scipy':'1.16.2'})
    write(target,m);print(json.dumps(dict(candidate=str(target),sha256=sha(target),source_control_files=len(ids),dependency_files_bound=len(deps),true_array_decodes=0)))

def freeze(review_path):
    target=PREP/'run_manifest.json';require(not target.exists(),'Never overwrite frozen manifest')
    cp=PREP/'manifest_candidate.json';m=read(cp);review=read(review_path)
    require(review.get('passed') is True,'Independent execution review required')
    bound=review['identities'];require(bound.get(str(cp))==sha(cp),'Review must bind exact candidate')
    for p,h in bound.items():require(sha(p)==h,'Review became stale: '+p)
    for p,h in m['identities'].items():require(sha(p)==h,'Candidate source became stale: '+p)
    m['identities'][str(Path(review_path).resolve())]=sha(review_path)
    m.update(status='FROZEN',frozen_utc=datetime.now(timezone.utc).isoformat())
    write(target,m);print(json.dumps(dict(path=str(target),sha256=sha(target),frozen_utc=m['frozen_utc'])))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['candidate','freeze']);p.add_argument('--review')
    a=p.parse_args()
    if a.command=='candidate':candidate()
    else:freeze(a.review)
