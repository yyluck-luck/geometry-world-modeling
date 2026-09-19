#!/usr/bin/env python3
"""Bind acquired sensor files to the original twenty observed RGB predictions."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util
R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    out=R/'work/S15C_root_freeze';assert not out.exists();out.mkdir(parents=True)
    samples_path=R/'work/S15A_samples_v2/samples.json';need_sha='fdf03dc69ede6e46cf3b9f545c5b6932e8ea6270729bd9f413062b298ff64a6f';assert sha(samples_path)==need_sha
    selected=json.loads(samples_path.read_text())['samples'][:20]
    acquisition=R/'data/bonn_s15c_depth/receipt.json';a=json.loads(acquisition.read_text());assert a['status']=='PASS' and a['image_array_decodes']==0 and len(a['members'])==20
    members={x['name']:x for x in a['members']}
    old=json.loads((R/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json').read_text());samples=[]
    for s,rgb in zip(selected,old['history_images']):
        dep=members[s['depth_member']];assert Path(rgb['path']).name==Path(s['rgb_member']).name and rgb['index']==s['index']
        samples.append(dict(index=s['index'],rgb_path=rgb['path'],rgb_sha256=rgb['sha256'],rgb_timestamp=float(s['rgb_timestamp']),depth_path=dep['path'],depth_sha256=dep['sha256'],depth_timestamp=float(s['depth_timestamp'])))
    runner=R/'scripts/s15c_observed_depth.py';assert sha(runner)=='a67e7dc3691af6d3ea9beb74def2ebaec8c273f43df30d48ad6285061a950653'
    spec=importlib.util.spec_from_file_location('c',runner);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    seal=R/'docs/S15A_HISTORY_COMBINED_SEAL.json';assert sha(seal)=='71ac6a264d1a52909f1f8a0ab44e433afc3bb646aea18adb07fdb36f40c093e0'
    controls=[R/'docs/S15C_OBSERVED_DEPTH_PROTOCOL.md',R/'docs/S15C_OBSERVED_DEPTH_INTERFACE.md',R/'docs/S15B_BONN_POSE_RESOLUTION.md',R/'docs/S15C_CODE_REVIEW_AND_PIXEL_WEIGHTED_UPDATE.md',R/'work/S15C_depth_access/contract.json',acquisition,samples_path,Path(__file__).resolve()]
    ids={str(p):sha(p) for p in [runner,seal,*controls]};ids.update({x['depth_path']:x['depth_sha256'] for x in samples})
    m=dict(schema='s15c-observed-depth-manifest-v1',frozen_utc=datetime.now(timezone.utc).isoformat(),runner=str(runner),python=old['python'],history_seal=str(seal),history_seal_sha256=sha(seal),history_predictions=str(R/'results/S15A_bonn_history/predictions.npz'),history_metadata=str(R/'results/S15A_bonn_history/run_metadata.json'),controls=[str(p) for p in controls],identities=ids,samples=samples,contract=mod.EXPECTED_CONTRACT)
    mod.validate_manifest(m)
    path=R/'docs/S15C_OBSERVED_DEPTH_EXECUTION_MANIFEST.json';assert not path.exists();save(path,m)
    receipt=dict(status='PASS',frozen_utc=m['frozen_utc'],manifest=str(path),manifest_sha256=sha(path),sensor_depth_pixel_decodes=0,gt_hash_scope='Use acquired-file receipt strings; no new depth hashing or decoding in this preparation',independent_root_code_review='Reviewed calibration/metric/read/seal paths plus added pooling function. Pooled RMSE uses squared per-frame RMSE weighted by valid-domain count; this is correct RMS over pooled visits, unlike arithmetic averaging RMSE. Existing main frame means untouched.',control_count=len(controls),depth_files=20)
    save(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
