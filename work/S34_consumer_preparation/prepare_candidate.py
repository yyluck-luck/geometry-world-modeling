#!/usr/bin/env python3
"""Prepare metadata-only S34 consumer candidate; never hashes/decodes actual arrays."""
from pathlib import Path
import ast, hashlib, importlib.util, json
from datetime import datetime, timezone

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main():
    started=datetime.now(timezone.utc).isoformat()
    require_new=[HERE/'manifest_candidate.json',HERE/'preparation_receipt.json']
    assert not any(p.exists() for p in require_new),'Preserve prior preparation before revision'
    runner=HERE/'run_consumer.py'
    ast.parse(runner.read_text());compile(runner.read_text(),str(runner),'exec')
    spec=importlib.util.spec_from_file_location('s34_consumer_candidate_source',runner)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source_paths=[ROOT/x for x in module.SOURCE_FILES]+[runner,HERE/'protocol.md',Path(__file__).resolve()]
    assert all(p.suffix in {'.py','.md','.yaml'} for p in source_paths)
    sources={str(p):sha(p) for p in source_paths}
    audit=module.source_ast_audit()
    prior_path=ROOT/'work/S26B_preparation/run_manifest.json'
    prior=json.loads(prior_path.read_text())
    pose=prior['continuation']['shared_artifacts']['control_c2w.npy']
    assert pose['sha256']=='c004c415b5bca43ae9a22cf63b542e7171eec29e31bf985c7e36327d1f5c0194'
    packets={role:dict(path=str(ROOT/'results/S34_geometry_producer'/role/'packet.npz'),sha256=None,
        receipt=str(ROOT/'results/S34_geometry_producer'/role/'receipt.json'),receipt_sha256=None) for role in module.ROLES}
    candidate=dict(schema='s34-original-consumer-manifest-v1',status='CANDIDATE_NOT_EXECUTABLE',prepared_utc=started,
        python=str(ROOT/'.venv-cut3r/bin/python'),output=str(ROOT/'results/S34_original_consumer'),policy=module.POLICY,
        producer_contract=dict(path=str(ROOT/'work/S34_preparation/contract.json'),sha256=None),packets=packets,
        given_optical_c2w=pose,source_sha256=sources,
        pending_binding='Root supplies formal producer contract and all4 PASS receipt/packet SHAs after production; freeze status only after source review. No current endpoint bytes inspected.',
        provenance=dict(given_pose_identity_from=str(prior_path),given_pose_metadata_sha256=sha(prior_path)),
        final_context_ids_status='NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY')
    write(HERE/'manifest_candidate.json',candidate)
    receipt=dict(status='PASS_SOURCE_AND_METADATA_PREPARATION_ONLY',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sources,candidate_sha256=sha(HERE/'manifest_candidate.json'),ast_audit=audit,
        compile_only=True,numerical_libraries_imported=False,real_array_bytes=0,RGB_sensor_GT_bytes=0,
        models_GA_clean_render_calls=0,synthetic_array_tests=0,execution_not_authorized_by_this_receipt=True)
    write(HERE/'preparation_receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'runner_sha256':sha(runner),'protocol_sha256':sha(HERE/'protocol.md'),
        'candidate_sha256':sha(HERE/'manifest_candidate.json'),'preparation_receipt_sha256':sha(HERE/'preparation_receipt.json')},indent=2))

if __name__=='__main__':main()
