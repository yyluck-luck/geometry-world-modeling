#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,importlib.util
R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    runner=R/'scripts/s16_source_interference.py';prep=R/'work/S16_preparation/final_monitor_review/receipt.json';review=json.loads(prep.read_text());assert review['status']=='PASS' and sha(runner)==review['runner_sha256_after']
    b=R/'work/S15B_witness_preparation_root';roles=dict(bridge=str(b/'witness_inputs.npz'),proposals=str(R/'results/S15B_prefix_proposals/proposals.npz'),target_cameras=str(b/'target_camera_inputs.npz'),rule_masks=str(R/'results/S15B_witness_costs/rule_masks.npz'),consumer_predictions=str(R/'results/S15B_consumer_predictions/target_predictions.npz'),scored_gt=str(R/'results/S15B_consumer_scores/evaluation_gt.npz'))
    controls=[runner,prep,R/'docs/S16_INTERFERENCE_PROTOCOL.md',R/'docs/S16_CAUSAL_INTERFERENCE_FEASIBILITY.md',R/'docs/S15B_CONSUMER_PREDICTION_SEAL.json',R/'docs/S15B_CONSUMER_EXECUTION_MANIFEST.json',R/'results/S15B_consumer_scores/scores.json',R/'results/S15B_consumer_scores/run_metadata.json',R/'results/S15B_consumer_independent/verification.json',Path(__file__).resolve()]
    for p in [R/'results/S15B_consumer_scores/run_metadata.json',R/'results/S15B_consumer_independent/verification.json']:assert json.loads(p.read_text())['status']=='PASS'
    original=json.loads((R/'docs/S15B_CONSUMER_EXECUTION_MANIFEST.json').read_text());oldseal=json.loads((R/'docs/S15B_CONSUMER_PREDICTION_SEAL.json').read_text())
    for role in ['bridge','proposals','target_cameras','rule_masks']:assert sha(roles[role])==original['predict_identities'][roles[role]]
    assert sha(roles['consumer_predictions'])==oldseal['identities'][roles['consumer_predictions']]
    spec=importlib.util.spec_from_file_location('s16',runner);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    ids={str(p):sha(p) for p in [*controls,*(Path(p) for p in roles.values())]};m=dict(schema='s16-source-interference-v1',frozen_utc=datetime.now(timezone.utc).isoformat(),python=str(R/'.venv-cut3r/bin/python'),runner=str(runner),policies=mod.POLICIES,identities=ids,**roles)
    mp=R/'docs/S16_EXECUTION_MANIFEST.json';assert not mp.exists();mp.write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(manifest=str(mp),sha256=sha(mp),identities=len(ids))),flush=True)
    return subprocess.run([m['python'],str(runner),'--manifest',str(mp),'--manifest-sha256',sha(mp),'--output',str(R/'results/S16_source_interference')]).returncode
if __name__=='__main__':raise SystemExit(main())
