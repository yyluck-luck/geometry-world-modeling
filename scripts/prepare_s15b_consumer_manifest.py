#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,subprocess
R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    w=R/'results/S15B_witness_costs';wm=json.loads((w/'run_metadata.json').read_text());assert wm['status']=='SUCCESS'
    for item in wm['outputs']:assert sha(item['path'])==item['sha256']
    numeric=R/'results/S15B_prefix_independent/attempt_2/verification.json';assert json.loads(numeric.read_text())['status']=='PASS'
    seal=R/'docs/S15B_CONSUMER_INPUT_SEAL.json';assert not seal.exists()
    b=R/'work/S15B_witness_preparation_root';oldseal=R/'docs/S15B_WITNESS_INPUT_SEAL.json';si=json.loads(oldseal.read_text())['identities']
    for p,h in si.items():assert sha(p)==h
    controls=[oldseal,R/'docs/S15B_PREFIX_PROPOSAL_SEAL.json',numeric,R/'docs/S15B_PREFIX_PROTOCOL.md',R/'docs/S15B_CONSUMER_PROTOCOL.md',R/'work/S15B_consumer_review/receipt.json',w/'run_metadata.json',w/'summary.json',Path(__file__).resolve()]
    save(seal,dict(schema='s15b-consumer-input-seal-v1',sealed_utc=datetime.now(timezone.utc).isoformat(),identities={str(p):sha(p) for p in [*controls,*(p for p in w.iterdir() if p.is_file())]}))
    runner=R/'scripts/s15b_memory_consumer.py';assert sha(runner)=='4541af96cfba4a2c7770dd5d9c068f2906e2912794bcb943b39ca15501c4f061'
    spec=importlib.util.spec_from_file_location('c',runner);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    later=json.loads((R/'work/S15B_root_preparation_v2/later_cameras_and_samples.json').read_text());roles=dict(bridge=str(b/'witness_inputs.npz'),proposals=str(R/'results/S15B_prefix_proposals/proposals.npz'),target_cameras=str(b/'target_camera_inputs.npz'),rule_masks=str(w/'rule_masks.npz'))
    targets=[dict(index=i,path=str(Path(later['dataset_root'])/later['frames'][i]['depth']['path']),sha256=later['frames'][i]['depth_sha256'],timestamp=later['frames'][i]['depth']['timestamp']) for i in range(20,24)]
    ids={str(p):sha(p) for p in [runner,seal,*controls,*[Path(p) for p in roles.values()]]}
    m=dict(schema='s15b-consumer-manifest-v1',frozen_utc=datetime.now(timezone.utc).isoformat(),python=str(R/'.venv-cut3r/bin/python'),runner=str(runner),runner_sha256=sha(runner),methods=c.METHODS,target_depths=targets,predict_identities=ids,**roles)
    c.validate_manifest(m);mp=R/'docs/S15B_CONSUMER_EXECUTION_MANIFEST.json';assert not mp.exists();save(mp,m)
    print(json.dumps(dict(manifest=str(mp),sha256=sha(mp),target_depth_pixels_read=0)),flush=True)
    return subprocess.run([m['python'],str(runner),'predict','--manifest',str(mp),'--manifest-sha256',sha(mp),'--output',str(R/'results/S15B_consumer_predictions')]).returncode
if __name__=='__main__':raise SystemExit(main())
