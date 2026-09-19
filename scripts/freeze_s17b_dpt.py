#!/usr/bin/env python3
"""Freeze two actual known RGB inputs only after complete public checkpoint verification."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, zipfile

R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--download-receipt',type=Path,required=True)
    parser.add_argument('--peer-review',type=Path,required=True);parser.add_argument('--root-review',type=Path,required=True)
    args=parser.parse_args()
    out=R/'work/S17B_root_freeze';dest=R/'docs/S17B_EXECUTION_MANIFEST.json'
    assert not out.exists() and not dest.exists()
    receipt=json.loads(args.download_receipt.read_text())
    expected='45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
    weight=R/'data/cut3r/cut3r_512_dpt_4_64.pth'
    assert receipt['status']=='PASS' and receipt['sha256']==expected and receipt['bytes']==3173761006
    assert receipt['path']==str(weight) and weight.stat().st_size==3173761006
    assert sha(weight)==expected
    # Both human-readable code inspections are complete before this command.
    peer=json.loads(args.peer_review.read_text());review=json.loads(args.root_review.read_text())
    assert peer['status']=='READY_FOR_ROOT_FREEZE_AFTER_COMPLETE_CHECKPOINT'
    assert review['status']=='READY_AFTER_DOWNLOAD_PASS'
    for record in [peer,review]:
        assert all(sha(p)==d for p,d in record['identities'].items())
    out.mkdir(parents=True);begin=utc()
    with zipfile.ZipFile(weight) as z:
        members=z.infolist();bad=z.testzip()
        assert bad is None and members and all(not x.is_dir() for x in members)
        assert all(not Path(x.filename).is_absolute() and '..' not in Path(x.filename).parts for x in members)
    zip_receipt=dict(started_utc=begin,completed_utc=utc(),status='PASS',path=str(weight),sha256=expected,
                     bytes=3173761006,members=len(members),member_bytes=sum(x.file_size for x in members),
                     all_crc_pass=True,weight_deserializations=0,model_calls=0)
    write(out/'checkpoint_zip_receipt.json',zip_receipt)
    old=json.loads((R/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json').read_text());repo=Path(old['repo'])
    upstream={p:d for p,d in old['identities'].items() if Path(p).is_relative_to(repo) and Path(p).suffix=='.py'}
    assert len(upstream)==99 and all(sha(p)==d for p,d in upstream.items())
    runner=R/'scripts/run_s17b_dpt_history.py'
    spec=importlib.util.spec_from_file_location('s17b_contract_only',runner);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    controls=[R/'RESEARCH_PRINCIPLES.md',R/'RESEARCH_QUALITY_TARGETS.md',R/'RESEARCH_QUALITY_TARGETS_ERRATA.md',
              R/'docs/S17B_DPT_TWO_FRAME_PROTOCOL.md',R/'scripts/run_s14d_controlled.py',Path(__file__).resolve(),
              args.download_receipt.resolve(),args.peer_review.resolve(),args.root_review.resolve(),
              out/'checkpoint_zip_receipt.json',R/'work/S17B_preparation/artificial_checks.json',
              R/'scripts/verify_s17b_dpt_history.py']
    m=dict(schema='s17b-dpt-two-frame-manifest-v1',frozen_utc=utc(),repo=old['repo'],commit=old['commit'],
           python=old['python'],runner=str(runner),checkpoint=str(weight),rope_check=old['rope_check'],
           history_images=old['history_images'][:2],control_files=[str(p) for p in controls],
           contract=module.EXPECTED_CONTRACT.copy(),identities=upstream.copy())
    for p in controls+[runner,weight,Path(m['rope_check']),R/'scripts/cut3r_rope_compat.py']+[Path(x['path']) for x in m['history_images']]:
        m['identities'][str(p)]=sha(p)
    assert m['identities'][str(weight)]==expected
    module.validate_contract(m)
    write(dest,m)
    final=dict(completed_utc=utc(),status='PASS',manifest=str(dest),manifest_sha256=sha(dest),
               identities=len(m['identities']),upstream_python_files=len(upstream),rgb_files=2,
               image_decodes=0,weight_deserializations=0,model_calls=0)
    write(out/'receipt.json',final);print(json.dumps(final,indent=2))
if __name__=='__main__':main()
