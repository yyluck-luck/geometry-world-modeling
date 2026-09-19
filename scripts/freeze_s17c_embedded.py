#!/usr/bin/env python3
"""Freeze the original embedded wrapper and isolated dependencies for two known photos."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--peer-review',type=Path,required=True);p.add_argument('--root-review',type=Path,required=True);p.add_argument('--b-verification',type=Path,required=True);a=p.parse_args()
    dest=R/'docs/S17C_EXECUTION_MANIFEST.json';out=R/'work/S17C_root_freeze'
    assert not dest.exists() and not out.exists()
    for path, expected_status in [(a.peer_review,'PRODUCER_REVIEW_PASS_READY_FOR_ROOT_FREEZE_ACTUAL_RUN_PENDING'),(a.root_review,'READY_FOR_FREEZE')]:
        review=json.loads(path.read_text());assert review['status']==expected_status
        assert all(sha(k)==v for k,v in review['identities'].items())
    b=json.loads(a.b_verification.read_text());assert b['status']=='PASS'
    bmeta=json.loads((R/'results/S17B_dpt_two_frames/run_metadata.json').read_text())
    caller=json.loads((R/'work/S17B_execution/model/caller_receipt.json').read_text())
    assert bmeta['status']=='SUCCESS' and caller['status']=='PASS'
    source_plan=R/'work/S17C_interface_preparation/source_plan.json';plan=json.loads(source_plan.read_text())
    environment=R/'work/S17C_environment/environment_ready.json';env=json.loads(environment.read_text())
    assert env['status']=='PASS_IMPORT_ONLY_NO_MODEL' and env['installed_wheel_count']==34 and env['old_environments_unchanged']
    for group in ['artifacts','preparation_artifacts']:
        assert all(sha(v['path'])==v['sha256'] for v in env[group].values())
    overlay_manifest=R/'work/S17C_environment/overlay_files.json';overlay=json.loads(overlay_manifest.read_text())
    assert overlay['count']==len(overlay['files'])==5523
    src=Path(env['source_root']);source_ids={str(src/k):v['sha256'] for k,v in plan['source_files'].items()}
    source_ids.update({str(src/x['path']):x['sha256'] for x in plan['patches']});assert len(source_ids)==199
    dep_ids={p:v['sha256'] for p,v in overlay['files'].items()}
    assert all(sha(k)==v for k,v in (source_ids|dep_ids).items())
    runner=R/'scripts/run_s17c_embedded_geometry.py'
    spec=importlib.util.spec_from_file_location('s17c_contract_only',runner);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    previous=json.loads((R/'docs/S17B_EXECUTION_MANIFEST.json').read_text())
    weight=Path(previous['checkpoint']);assert weight.stat().st_size==3173761006 and sha(weight)==module.CHECKPOINT_SHA256
    controls=[R/'RESEARCH_PRINCIPLES.md',R/'RESEARCH_QUALITY_TARGETS.md',R/'RESEARCH_QUALITY_TARGETS_ERRATA.md',
              R/'docs/S17C_EMBEDDED_GEOMETRY_PROTOCOL.md',R/'docs/S17C_INTERFACE_REVIEW.md',
              R/'docs/S17C_INDEPENDENT_NUMERICAL_CONTRACT.md',R/'scripts/run_s14d_controlled.py',
              Path(__file__).resolve(),R/'scripts/verify_s17c_embedded_geometry.py',
              R/'work/S17C_independent_preparation/numerical_reference.py',a.peer_review.resolve(),a.root_review.resolve(),
              a.b_verification.resolve(),R/'work/S17B_root_freeze/checkpoint_zip_receipt.json',
              R/'work/S17C_preparation/receipt.json',overlay_manifest]
    controls += [Path(v['path']) for group in ['artifacts','preparation_artifacts'] for v in env[group].values()]
    controls=list(dict.fromkeys(controls))
    m=dict(schema='s17c-embedded-two-frame-geometry-manifest-v1',frozen_utc=utc(),source_root=str(src),
           source_commit=module.COMMIT,source_plan=str(source_plan),python=env['python'],overlay=env['overlay'],
           dependency_plan=str(R/'work/S17C_interface_preparation/dependency_plan_v2.json'),
           environment_receipt=str(environment),import_smoke=str(R/'work/S17C_environment/import_smoke_v2.json'),
           runner=str(runner),checkpoint=str(weight),history_images=previous['history_images'],
           contract=module.EXPECTED_CONTRACT.copy(),overlay_files=list(dep_ids),control_files=[str(x) for x in controls],
           identities=source_ids|dep_ids)
    for path in controls+[source_plan,environment,runner,weight,Path(m['dependency_plan']),Path(m['import_smoke'])]+[Path(x['path']) for x in m['history_images']]:
        m['identities'][str(path)]=sha(path)
    module.validate_contract(m)
    out.mkdir();dump(dest,m)
    receipt=dict(completed_utc=utc(),status='PASS',manifest=str(dest),manifest_sha256=sha(dest),identities=len(m['identities']),
                  isolated_source_files=len(source_ids),overlay_files=len(dep_ids),image_decodes=0,checkpoint_deserializations=0,
                  model_calls=0,interpretation='Frozen no-prior embedded geometry component; not the constrained full video pipeline')
    dump(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
