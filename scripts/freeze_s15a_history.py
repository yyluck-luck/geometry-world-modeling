#!/usr/bin/env python3
"""Bind verified new RGB members to the reviewed history-only CUT3R runner."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import run_s15_history


ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)


def main():
    p=argparse.ArgumentParser();p.add_argument('--history-fetch-receipt',required=True);p.add_argument('--samples',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);require(not out.exists(),'fresh manifest')
    fetch=json.loads(Path(a.history_fetch_receipt).read_text());samples=json.loads(Path(a.samples).read_text())
    require(fetch['status']=='PASS' and fetch['image_array_decodes']==0,'verified member-only fetch')
    expected=samples['samples'][:20]
    require([x['index'] for x in expected]==list(range(20)) and all(x['role']=='history' for x in expected),'history roles')
    require(len(samples['samples'])==24 and all(x['role']=='future_target' for x in samples['samples'][20:]),'four future slots')
    require([m['name'] for m in fetch['members']]==[s['rgb_member'] for s in expected],'exact twenty selected history members in order')
    old=json.loads((ROOT/'docs/S14E_MODEL_EXECUTION_MANIFEST.json').read_text())
    repo=Path(old['repo'])
    identities={p:h for p,h in old['identities'].items() if Path(p).is_relative_to(repo) and p.endswith('.py')}
    require(len(identities)==99,'reuse 99 pinned sources')
    for key in ('checkpoint','rope_check'):
        identities[old[key]]=old['identities'][old[key]]
    adapter=str(ROOT/'scripts/cut3r_rope_compat.py');identities[adapter]=old['identities'][adapter]
    runner=str(ROOT/'scripts/run_s15_history.py')
    require(sha(runner)=='2a31ca2ee6a9084669ea2ca75fdcb5d40ee727fa7c1a5d64af82f3088c884369','reviewed runner source')
    identities[runner]=sha(runner)
    controls=[str(ROOT/p) for p in ['RESEARCH_PRINCIPLES.md','docs/S15A_NATIVE_HISTORY_PROTOCOL.md','docs/S15A_NATIVE_HISTORY_PROTOCOL_V2.md','docs/S15_HISTORY_RUNNER_INTERFACE.md','docs/S15_BONN_CALIBRATION_AUDIT.md','scripts/run_s14d_controlled.py','scripts/freeze_s15a_history.py','scripts/fetch_s15_zip_members.py','scripts/select_s15_samples_v2.py','work/S15A_access/history_contract.json','work/S15A_root_review/history_source_review.json','work/S15A_access_review/receipt.json','work/S15A_sampling_review/v2_receipt.json']]+[str(Path(a.history_fetch_receipt).resolve()),str(Path(a.samples).resolve())]
    controls += [str(ROOT/p) for p in ['work/S15A_access/history_resume_contract.json','work/S15A_access/history_resume2_contract.json','data/bonn_s15a_history/receipt.json','data/bonn_s15a_history_resume1/receipt.json','data/bonn_s15a_history_resume2/receipt.json','scripts/assemble_s15a_acquisition.py']]
    controls += [str(ROOT/p) for p in ['work/S15A_access/history_curl_contract_v2.json','data/bonn_s15a_history_curl/receipt.json','scripts/fetch_s15_last_two_curl.py','work/S15A_curl_review/receipt.json']]
    controls += [str(ROOT/p) for p in ['work/S15A_access/history_persistent_contract.json','data/bonn_s15a_history_persistent/receipt.json','scripts/fetch_s15_cached_tail.py']]
    require(len(controls)==len(set(controls)),'distinct controls')
    for path in controls:identities[path]=sha(path)
    history=[]
    for index,member in enumerate(fetch['members']):
        path=str(Path(member['path']).resolve());require(sha(path)==member['sha256'],'downloaded member unchanged')
        identities[path]=member['sha256'];history.append(dict(index=index,path=path,sha256=member['sha256']))
    for path,digest in identities.items():require(sha(path)==digest,'frozen existing or new input changed: '+path)
    manifest=dict(schema='s15-history-manifest-v1',frozen_utc=datetime.now(timezone.utc).isoformat(),repo=str(repo),commit=old['commit'],python=old['python'],runner=runner,checkpoint=old['checkpoint'],rope_check=old['rope_check'],history_images=history,control_files=controls,contract=dict(run_s15_history.EXPECTED_CONTRACT),identities=identities)
    run_s15_history.validate_contract(manifest)
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(manifest=str(out.resolve()),sha256=sha(out),identity_count=len(identities),images=20,target_images=0)))


if __name__=='__main__':main()
