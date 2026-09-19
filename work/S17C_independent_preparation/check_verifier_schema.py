#!/usr/bin/env python3
"""Artificial full-shape output packet, not real data or a model simulation result."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    start=datetime.now(timezone.utc).isoformat()
    root=Path(__file__).resolve().parents[2]
    vp=root/'scripts/verify_s17c_embedded_geometry.py';rp=Path(__file__).with_name('numerical_reference.py')
    v=load('verifier',vp);ref=load('numeric',rp)
    run=a.output/'invented_packet';run.mkdir()
    (run/'checkpoint_load.txt').write_text("instantiating : ARCroco3DStereo(ARCroco3DStereoConfig(state_size=768,state_pe='2d'))\n")
    meta={'array_files':{},'counters':{'pnp_calls':1},'pnp_results':[{'index':0,'success':False,'kwargs':{'niter_PnP':10}}],
          'clean_changed_pixels':[0,0],'clean_zero_pixels':[0,0]}
    depth=np.full((2,384,512),2.,dtype=np.float32);focal=np.full((2,1),512.,dtype=np.float32)
    pp=np.array([[256,192]]*2,dtype=np.float32);rot=np.repeat(np.eye(3,dtype=np.float32)[None],2,axis=0);trans=np.zeros((2,3),dtype=np.float32)
    pts=ref.reconstruct_world(depth,focal,pp,rot,trans).astype(np.float32);poses=ref.camera_matrices(rot,trans).astype(np.float32)
    conf=np.full_like(depth,2.);colors=np.full_like(pts,.5)
    k=np.array([[[512,0,256],[0,512,192],[0,0,1]]]*2,dtype=np.float32)
    scene=dict(world_points=pts,depths=depth,confidence=conf,poses=poses,focal=focal,pp=pp,intrinsics=k,
               pw_poses=np.eye(4,dtype=np.float32)[None],adaptors=np.ones((1,3),dtype=np.float32),colors=colors)
    def write(name,arrays):
        np.savez_compressed(run/name,**arrays)
        meta['array_files'][name]={key:v.aid(value) for key,value in arrays.items()}
    raw={}
    enc=np.array([[0,0,0,1,0,0,0]]*2,dtype=np.float32)
    for i in range(2):
        raw.update({f'frame{i}_pts3d_in_self_view':pts[[i]].copy(),f'frame{i}_pts3d_in_other_view':pts[[i]].copy(),
                    f'frame{i}_conf_self':conf[[i]].copy(),f'frame{i}_conf':conf[[i]].copy(),
                    f'frame{i}_rgb':np.full((1,384,512,3),-1,dtype=np.float32),f'frame{i}_camera_pose':enc[[i]].copy()})
    # Hand 3-4-5 Euclidean residual at one pixel differentiates Manhattan weighting.
    raw['frame0_pts3d_in_self_view'][0,0,0,:2]+=np.array([3,4],dtype=np.float32)
    meta['postfinal_objective']=5*np.log(2)/(384*512)
    write('predictions.npz',raw)
    state={name:np.zeros(shape,dtype=dtype) for name,(shape,dtype) in v.STATE.items()}
    state['state_pos']=np.array([[i//28,i%28] for i in range(768)],dtype=np.int64)[None]
    write('state.npz',state);write('history_poses.npz',dict(history_pose_encodings=enc,history_poses=poses))
    write('processed_inputs.npz',{f'frame{i}_img':np.zeros((1,3,384,512),dtype=np.float32) for i in range(2)})
    for name in v.SCENE_FILES:write(name,scene)
    write('final_result.npz',dict(point_clouds=pts,colors=colors,depths=depth,confidences=conf,focal=focal,pp=pp,R=rot,t=trans))
    calls=[]
    def check(ok,label,**detail):
        calls.append(dict(name=label,passed=bool(ok),**detail))
        if not ok:raise ValueError(label)
    good=a.output/'valid_packet_check';good.mkdir();report={'array_decodes':0}
    v.verify_saved_math(run,meta,check,report,good,ref)
    assert report['arrays_verified']==69
    # Fresh mutation case retains original packet in its archive files except single
    # after-clean confidence overwrite; the updated tensor identity alone must not hide it.
    changed={key:value.copy() for key,value in scene.items()};changed['confidence'][0,1,2]=1.
    original=(run/'scene_after_clean.npz').read_bytes()
    (a.output/'original_scene_after_clean.npz').write_bytes(original)
    write('scene_after_clean.npz',changed)
    bad=a.output/'intentional_clean_corruption';bad.mkdir();badreport={'array_decodes':0}
    error=None
    try:v.verify_saved_math(run,meta,check,badreport,bad,ref)
    except ValueError as e:error=str(e)
    assert error=='all clean confidence pixels exact in independent FP32 path',error
    with np.load(bad/'clean_full_diagnostics.npz',allow_pickle=False) as z:
        assert np.array_equal(z['all_mismatch_indices'],[[0,1,2]])
    receipt=dict(schema='s17c-artificial-verifier-schema-v1',status='PASS_ARTIFICIAL_ONLY',started_utc=start,
                 completed_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),
                 numerical_reference_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 valid_arrays_verified=69,intentional_corruption_rejected=error,all_mismatch_indices_preserved=[[0,1,2]],
                 real_image_reads=0,checkpoint_reads=0,gt_reads=0,model_calls=0,optimizer_runs=0,
                 note='Invented full-size arrays exercise schemas and independent arithmetic only, not a real reconstruction experiment.')
    (a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['status','valid_arrays_verified','intentional_corruption_rejected']}))

if __name__=='__main__':main()
