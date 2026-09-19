#!/usr/bin/env python3
"""S99 independent pre-GT audit; does not import consumer.render or read GT."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, numpy as np
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
BASE=ROOT/'work/S99_fixed_budget_risk_update'; PRED=BASE/'predict_01'; OUT=ROOT/'work/agents/s99_independent_recompute/pre_gt'
FREEZE=BASE/'FREEZE.json'; MANIFEST=ROOT/'results/S15B_consumer_predictions/frozen_manifest.json'; OLD=ROOT/'results/S15B_consumer_predictions/target_predictions.npz'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def check(c,m,checks):
 checks.append({'name':m,'passed':bool(c)}); 
 if not c: raise AssertionError(m)
def render_independent(z,valid,source,target,K,scale):
 # Independent vectorized projection and lexicographic z-buffer; no consumer.render import.
 h,w=z.shape[1:]; yy,xx=np.indices((h,w),dtype=np.float64)
 rays=np.empty((h,w,3),dtype=np.float64); rays[...,0]=xx; rays[...,1]=yy; rays[...,2]=1.0
 invK=np.linalg.inv(K); rays=rays@invK.T
 points=[]
 for si in range(z.shape[0]):
  points.append((rays*z[si][...,None])@source[si,:3,:3].T+source[si,:3,3])
 world=np.asarray(points).reshape(-1,3)
 camera=(world-target[:3,3])@target[:3,:3]
 proj=camera@K.T
 with np.errstate(divide='ignore',invalid='ignore'):
  u=np.floor(proj[:,0]/proj[:,2]+.5); v=np.floor(proj[:,1]/proj[:,2]+.5)
 keep=valid.reshape(-1)&np.isfinite(camera).all(axis=1)&(camera[:,2]>0)&np.isfinite(u)&np.isfinite(v)&(u>=0)&(u<w)&(v>=0)&(v<h)
 flatids=np.flatnonzero(keep); pix=(v[keep].astype(np.int64)*w+u[keep].astype(np.int64))
 dep=camera[keep,2]
 order=np.lexsort((flatids,dep,pix)); ordered=pix[order]; first=np.r_[True,ordered[1:]!=ordered[:-1]] if len(order) else np.zeros(0,bool)
 chosen=order[first]; out=np.zeros(h*w,dtype=np.float64); ids=np.full(h*w,-1,dtype=np.int64)
 out[pix[chosen]]=dep[chosen]/scale; ids[pix[chosen]]=flatids[chosen]
 return out.reshape(h,w),ids.reshape(h,w),int(keep.sum())

def main():
 checks=[]
 # Identity checks are before any GT read.
 f=json.loads(FREEZE.read_text()); check(f['schema']=='s99-freeze-v1','freeze schema',checks)
 for rel,h in {**f['identities']}.items(): check(sha(ROOT/rel)==h,'freeze identity '+rel,checks)
 run=json.load((PRED/'RUN.json').open()); seal=json.load((PRED/'PREDICTION_SEAL.json').open())
 check(run['status']=='PASS' and run['mode']=='predict','prediction run pass',checks)
 check(seal['freeze_sha256']==sha(FREEZE) and seal['evaluation_gt_read'] is False,'prediction seal GT false',checks)
 for n,h in seal['files'].items(): check(sha(PRED/n)==h,'prediction seal file '+n,checks)
 # Load only old/proposals/cameras/selection/prediction; GT never touched.
 m=json.load(MANIFEST.open()); b=load(ROOT/m['bridge']); p=load(ROOT/m['proposals']); t=load(ROOT/m['target_cameras']); sel=load(PRED/'selection.npz'); saved=load(OLD); pred=load(PRED/'predictions.npz')
 check(pred['depth_m'].shape==(25,4,224,224),'prediction shape',checks); check(pred['source_pixel_identity'].shape==(25,4,224,224),'ID shape',checks)
 check(np.array_equal(pred['depth_m'][:2],saved['depth_m'][:2]),'sealed endpoint depth parity',checks); check(np.array_equal(pred['source_pixel_identity'][:2],saved['source_pixel_identity'][:2]),'sealed endpoint ID parity',checks)
 check(sel['block_masks'].shape==(25,4,196),'block mask shape',checks); check((sel['block_masks'][2:].sum(axis=2)==39).all(),'all treatment 39 blocks/source',checks)
 check(np.array_equal(sel['pixel_masks'].shape,(25,4,224,224)), 'pixel mask shape',checks)
 old=p['old_self_z_model'].astype(np.float64); new=p['new_self_z_model'].astype(np.float64); valid=np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0)
 check(valid.all(),'all source pixels valid',checks)
 low=sel['pixel_masks'][2]
 z=np.where(low,new,old)
 out,ids,vis=render_independent(z,valid,b['source_c2w'],t['target_c2w'][0],t['K'],float(t['scale_model_per_meter']))
 check(np.array_equal(out,pred['depth_m'][2,0]),'target20 low depth exact parity',checks)
 check(np.array_equal(ids,pred['source_pixel_identity'][2,0]),'target20 low ID exact parity',checks)
 np.savez_compressed(OUT/'target20_low_independent.npz',depth_m=out,source_pixel_identity=ids)
 result={'schema':'s99-independent-pre-gt-v1','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_PRE_GT','scope':'freeze/seal identity and target20 low-disagreement independent z-buffer; no GT read','gt_read':False,'checks':checks,'check_count':len(checks),'failed':sum(not x['passed'] for x in checks),'target20_low_projected_source_visits':vis,'target20_low_depth_sha256':sha(OUT/'target20_low_independent.npz'),'freeze_sha256':sha(FREEZE),'prediction_seal_sha256':sha(PRED/'PREDICTION_SEAL.json')}
 (OUT/'PRE_GT_RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'status':result['status'],'checks':len(checks),'failed':result['failed'],'target20_visits':vis},ensure_ascii=False))
if __name__=='__main__':main()
