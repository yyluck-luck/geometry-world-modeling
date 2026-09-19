#!/usr/bin/env python3
"""Freeze twelve already-seen RGB inputs and reuse certified camera metadata only."""
from pathlib import Path
import hashlib, json, importlib.util
from datetime import datetime, timezone
import numpy as np

R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
    out=R/'work/S15B_root_preparation_v2';assert not out.exists();out.mkdir(parents=True)
    now=lambda:datetime.now(timezone.utc).isoformat()
    receipt={'started_utc':now(),'stage':'metadata preparation','rgb_decodes':0,'sensor_depth_decodes':0,'model_calls':0,'prior_header_inspection':'2026-09-06 10:26 UTC approximate; four allowed camera metadata arrays only, not depth pixels'}
    protocol=R/'docs/S15B_PREFIX_PROTOCOL.md'
    oldseal=R/'docs/S14E_COMBINED_PREDICTION_SEAL.json'
    assert sha(oldseal)=='f26981965b30ebdd7609088eab7a84a509aabcfd03f83bd3eff5c01e8ba671eb'
    oldids=json.loads(oldseal.read_text())['identities']
    poses=R/'results/S14E_known_camera_prepare/allowed_gt_poses.npz'
    samples=R/'results/S8_cut3r_cpu_v2/frozen_inputs.json'
    assert sha(poses)==oldids[str(poses)]
    oldmanifest=R/'results/S14E_known_camera_prepare/frozen_manifest.json'
    assert sha(oldmanifest)==oldids[str(oldmanifest)]
    assert sha(samples)==json.loads(oldmanifest.read_text())['identities'][str(samples)]
    frames=json.loads(samples.read_text())['blocks'][0]['frames']
    dataset=R/'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk'
    with np.load(poses,allow_pickle=False) as z:
        gt=z['gt_poses'];ts=z['selected_timestamps'];rgbts=z['rgb_timestamps'];depthts=z['depth_timestamps']
    assert gt.shape==(24,4,4)
    assert np.array_equal(rgbts,np.array([f['rgb']['timestamp'] for f in frames]))
    assert np.array_equal(depthts,np.array([f['depth']['timestamp'] for f in frames]))
    assert np.array_equal(ts[:20],rgbts[:20]) and np.array_equal(ts[20:],depthts[20:])
    K=[[245.2734375,0,112],[0,245,111.5],[0,0,1]]
    images=[dict(index=i,path=str(dataset/f['rgb']['path']),sha256=f['rgb_sha256']) for i,f in enumerate(frames[:12])]
    cameras=dict(schema='s15b-prefix-cameras-v1',history_rgb_paths=[x['path'] for x in images],history_rgb_sha256=[x['sha256'] for x in images],history_timestamps=rgbts[:12].tolist(),gt_c2w=gt[:12].tolist(),K=K,source_indices=[0,3,6,9],pose_time='rgb',coordinate_frame='TUM optical camera-to-world',units='meter',provenance=dict(path=str(poses),sha256=sha(poses),seal_sha256=sha(oldseal)))
    cp=out/'prefix_cameras.json';save(cp,cameras)
    later=out/'later_cameras_and_samples.json'
    save(later,dict(schema='s15b-later-camera-metadata-v1',witness_indices=list(range(12,20)),witness_gt_c2w=gt[12:20].tolist(),target_indices=list(range(20,24)),target_gt_c2w=gt[20:].tolist(),frames=frames,dataset_root=str(dataset),K=K,source_pose_identity=sha(poses),pose_time_witness='rgb',pose_time_target='depth',sensor_pixels_read=False))
    runner=R/'scripts/run_s15b_prefix_proposals.py'
    spec=importlib.util.spec_from_file_location('s15bp',runner);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    old=json.loads((R/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json').read_text());repo=Path(old['repo'])
    ids={p:h for p,h in old['identities'].items() if Path(p).is_relative_to(repo) and Path(p).suffix=='.py'}
    controls=[protocol,R/'scripts/run_s14d_controlled.py',Path(__file__).resolve(),R/'docs/S15B_PREFIX_RUNNER_INTERFACE.md',R/'RESEARCH_QUALITY_TARGETS.md']
    for p in [runner,cp,Path(old['checkpoint']),Path(old['rope_check']),R/'scripts/cut3r_rope_compat.py',*controls]:ids[str(p)]=sha(p)
    ids.update({x['path']:x['sha256'] for x in images})
    manifest=dict(schema='s15b-prefix-proposals-manifest-v1',frozen_utc=now(),repo=old['repo'],commit=old['commit'],python=old['python'],runner=str(runner),checkpoint=old['checkpoint'],rope_check=old['rope_check'],camera_inputs=str(cp),history_images=images,control_files=[str(p) for p in controls],contract=mod.EXPECTED_CONTRACT,identities=ids)
    mod.validate_contract(manifest);mod.validate_cameras(cameras,manifest)
    mp=R/'docs/S15B_PREFIX_EXECUTION_MANIFEST.json';assert not mp.exists();save(mp,manifest)
    receipt.update(completed_utc=now(),status='PASS',manifest=str(mp),manifest_sha256=sha(mp),identities=len(ids),camera_source_sha256=sha(poses),protocol_sha256=sha(protocol),preparation_source_sha256=sha(__file__),read_array_names=['gt_poses','selected_timestamps','rgb_timestamps','depth_timestamps'],output_ids={str(p):sha(p) for p in [cp,later]},root_review='Read complete runner; verified frozen12 OLS, true physical vs conditioning rays, five queries, shared source cameras, exact six-head parity and immutable state; earlier artificial checks independently reviewed.')
    save(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
