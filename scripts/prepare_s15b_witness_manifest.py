#!/usr/bin/env python3
"""Seal completed proposals, then adapt known cameras without opening witness pixels."""
from pathlib import Path
import hashlib,json,importlib.util
from datetime import datetime,timezone
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def utc():return datetime.now(timezone.utc).isoformat()
def main():
    out=R/'work/S15B_witness_preparation_root';assert not out.exists();out.mkdir(parents=True)
    run=R/'results/S15B_prefix_proposals';meta=json.loads((run/'run_metadata.json').read_text());assert meta['status']=='SUCCESS'
    caller=R/'work/S15B_execution/prefix/caller_receipt.json';assert json.loads(caller.read_text())['status']=='PASS'
    mp=R/'docs/S15B_PREFIX_EXECUTION_MANIFEST.json';m=json.loads(mp.read_text());assert sha(mp)==meta['manifest_sha256']
    for name,h in meta['output_sha256'].items():assert sha(run/name)==h
    ids={str(p):sha(p) for p in sorted(run.iterdir()) if p.is_file()}
    ids.update({str(mp):sha(mp),str(caller):sha(caller)})
    seal=R/'docs/S15B_PREFIX_PROPOSAL_SEAL.json';assert not seal.exists()
    save(seal,dict(schema='s15b-prefix-proposal-seal-v1',sealed_utc=utc(),identities=ids,independent_numeric_review='pending separately; producer complete with root pre-run code review'))
    prep=R/'work/S15B_root_preparation_v2';receipt=json.loads((prep/'receipt.json').read_text());lp=prep/'later_cameras_and_samples.json'
    assert sha(lp)==receipt['output_ids'][str(lp)];later=json.loads(lp.read_text())
    alignment=json.loads((run/'alignment.json').read_text());A=np.array(alignment['A']);c=np.array(alignment['c']);s=alignment['s_model_per_metric']
    with np.load(run/'proposals.npz',allow_pickle=False) as z:
        old=z['old_self_z_model'];new=z['new_self_z_model'];src=z['source_poses'];K=z['K'];assert np.array_equal(K,np.tile(np.array(later['K']),(4,1,1)))
    def mapped(key):
        poses=np.array(later[key]);q=poses.copy();q[:,:3,:3]=A[None]@poses[:,:3,:3];q[:,:3,3]=s*(poses[:,:3,3]@A.T)+c;return q
    bridge=out/'witness_inputs.npz';np.savez_compressed(bridge,old_self_z=old,new_self_z=new,source_c2w=src,witness_c2w=mapped('witness_gt_c2w'),K=K[0],scale_model_per_meter=np.asarray(s))
    target=out/'target_camera_inputs.npz';np.savez_compressed(target,target_c2w=mapped('target_gt_c2w'),K=K[0],scale_model_per_meter=np.asarray(s))
    bs=R/'docs/S15B_WITNESS_INPUT_SEAL.json';assert not bs.exists();save(bs,dict(schema='s15b-witness-input-seal-v1',sealed_utc=utc(),identities={str(p):sha(p) for p in [seal,run/'proposals.npz',run/'alignment.json',lp,bridge,target,Path(__file__).resolve()]},witness_pixels_decoded=0,target_pixels_decoded=0))
    def im(i,key):
        f=later['frames'][i];return {key:i,'path':str(Path(later['dataset_root'])/f['rgb']['path']),'sha256':f['rgb_sha256']}
    runner=R/'scripts/s15b_witness_costs.py';spec=importlib.util.spec_from_file_location('w',runner);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
    sources=[im(i,'source_id') for i in [0,3,6,9]];witness=[im(i,'frame_id') for i in range(12,20)]
    ids={str(p):sha(p) for p in [bs,bridge,runner,R/'scripts/run_s14d_controlled.py',R/'docs/S15B_PREFIX_PROTOCOL.md',Path(__file__).resolve()]};ids.update({x['path']:x['sha256'] for x in sources+witness})
    wm=dict(schema='s15b-witness-costs-v1',frozen_utc=utc(),python=m['python'],runner=str(runner),contract=w.CONTRACT,proposal_seal={'path':str(bs),'sha256':sha(bs)},proposal_npz={'path':str(bridge),'sha256':sha(bridge)},source_images=sources,witness_images=witness,identities=ids)
    wp=R/'docs/S15B_WITNESS_EXECUTION_MANIFEST.json';assert not wp.exists();save(wp,wm)
    save(out/'receipt.json',dict(status='PASS',completed_utc=utc(),manifest=str(wp),manifest_sha256=sha(wp),seal_sha256=sha(seal),bridge_seal_sha256=sha(bs),rgb_decodes=0,sensor_depth_decodes=0,model_calls=0,root_review='Complete witness math reviewed: physical inverse projection, shared support, integer Hamming sums, exact matched Fractions, all784 rows and masks. Seal bindings independently root-controlled.'))
    print(json.dumps(json.loads((out/'receipt.json').read_text()),indent=2))
if __name__=='__main__':main()
