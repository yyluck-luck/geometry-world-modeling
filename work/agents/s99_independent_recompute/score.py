#!/usr/bin/env python3
"""Independent S99 score recomputation after pre-GT parity pass.
No consumer.render is imported; GT is read only after pre_gt/PRE_GT_RESULT.json PASS.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, numpy as np
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'); BASE=ROOT/'work/S99_fixed_budget_risk_update'; PRED=BASE/'predict_01'; SCORE=BASE/'score_01'; OUT=ROOT/'work/agents/s99_independent_recompute/score'
FREEZE=BASE/'FREEZE.json'; MANIFEST=ROOT/'results/S15B_consumer_predictions/frozen_manifest.json'; GT=ROOT/'results/S15B_consumer_scores/evaluation_gt.npz'; OLD=ROOT/'results/S15B_consumer_predictions/target_predictions.npz'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def frac_tail(a):
 a=np.sort(np.asarray(a,dtype=float))[::-1]; n=len(a)
 if n==0:return None
 mass=.05*n; k=int(np.floor(mass));
 return float((a[:k].sum()+(mass-k)*a[k])/mass)
def check(c,name,checks): checks.append({'name':name,'passed':bool(c)}); 
# no use check due side effect? define properly
def require(c,name,checks):
 checks.append({'name':name,'passed':bool(c)})
 if not c: raise AssertionError(name)

def main():
 checks=[]; pre=json.load((ROOT/'work/agents/s99_independent_recompute/pre_gt/PRE_GT_RESULT.json').open()); require(pre['status']=='PASS_PRE_GT' and pre['gt_read'] is False,'pre-GT gate',checks)
 f=json.load(FREEZE.open()); pred=load(PRED/'predictions.npz'); ids=pred['source_pixel_identity']; p=pred['depth_m']; g=load(GT)['depth_m'].astype(float)
 require(sha(GT)==f['gt_identity_from_previous_record']['results/S15B_consumer_scores/evaluation_gt.npz'],'GT identity',checks); require(g.shape==(4,224,224),'GT shape',checks)
 require(p.shape==(25,4,224,224) and ids.shape==p.shape,'prediction shapes',checks)
 require(np.isfinite(p).all() and (p>=0).all(),'finite nonnegative prediction',checks)
 pv=np.isfinite(p)&(p>0); methods=f['methods']; rows=[]; common_masks=[]
 for ti in range(4):
  gv=np.isfinite(g[ti])&(g[ti]>0); common=pv[:,ti].all(axis=0)&gv; common_masks.append(common); require(int(common.sum())>0,f'target{20+ti} common nonempty',checks)
  for mi,name in enumerate(methods):
   z=p[mi,ti]; own=gv&pv[mi,ti]; diff=np.abs(z[common]-g[ti][common]); e=diff/g[ti][common]
   correct=int(np.count_nonzero(np.maximum(z[own]/g[ti][own],g[ti][own]/z[own])<1.25)); ownerr=np.abs(z[own]-g[ti][own])/g[ti][own]
   same=own&pv[0,ti]; base_pair=np.abs(p[0,ti][same]-g[ti][same])/g[ti][same]; cond_pair=np.abs(z[same]-g[ti][same])/g[ti][same]
   rows.append({'method':name,'target':20+ti,'gt_valid':int(gv.sum()),'common_count':int(common.sum()),'common_fraction_of_gt':float(common.sum()/gv.sum()),'coverage':float(own.sum()/gv.sum()),'delta1_all_gt':correct/int(gv.sum()),'own_absrel':float(ownerr.mean()) if len(ownerr) else None,'common_absrel':float(e.mean()),'common_mae_m':float(diff.mean()),'common_worst5_absrel':frac_tail(e),'same_source_fraction_vs_never_on_pairwise_own':float(np.mean(ids[mi,ti][same]==ids[0,ti][same])),'pairwise_never_count':int(same.sum()),'pairwise_never_absrel':float(base_pair.mean()),'pairwise_condition_absrel':float(cond_pair.mean()),'pairwise_signed_benefit':float((base_pair-cond_pair).mean()),'lost_vs_never_count':int((gv&pv[0,ti]&~pv[mi,ti]).sum()),'gained_vs_never_count':int((gv&~pv[0,ti]&pv[mi,ti]).sum())})
 keys=['common_absrel','common_worst5_absrel','coverage','delta1_all_gt','common_mae_m','own_absrel']
 avg={name:{k:float(np.mean([r[k] for r in rows if r['method']==name])) for k in keys} for name in methods}; random_avg={k:float(np.mean([avg[name][k] for name in methods[5:]])) for k in keys}
 comparisons=[]
 for ti in range(4):
  tr={r['method']:r for r in rows if r['target']==20+ti}; rand=float(np.mean([tr[name]['common_absrel'] for name in methods[5:]])); low=tr['low_disagreement']['common_absrel']; comparisons.append({'target':20+ti,'low_absrel':low,'random_mean_absrel':rand,'confidence_gain_absrel':tr['confidence_gain']['common_absrel'],'high_absrel':tr['high_disagreement']['common_absrel'],'benefit_vs_random_mean':rand-low,'benefit_vs_confidence':tr['confidence_gain']['common_absrel']-low,'low_better_than_random_seed_count':sum(low<tr[name]['common_absrel'] for name in methods[5:])})
 lo=avg['low_disagreement']; co=avg['confidence_gain']; passed=(sum(c['benefit_vs_random_mean']>0 and c['benefit_vs_confidence']>0 for c in comparisons)>=3 and lo['common_absrel']<random_avg['common_absrel'] and lo['common_absrel']<co['common_absrel'] and lo['delta1_all_gt']>=max(random_avg['delta1_all_gt'],co['delta1_all_gt'])); reversal=(avg['high_disagreement']['common_absrel']<lo['common_absrel'] or sum(c['high_absrel']<c['low_absrel'] for c in comparisons)>=3); expected_status='KEEP_LOCAL_CANDIDATE_ONLY' if (passed and not reversal) else 'STOP_LOW_DISAGREEMENT_ADVANTAGE_IN_THIS_SETTING'
 official=json.load((SCORE/'SCORES.json').open()); require(official['status']==expected_status,'status recomputation',checks); require(official['low_risk_ordering_reversal']==reversal,'reversal recomputation',checks)
 # Compare all rows and scalar aggregates with tolerance.
 num_fields=['gt_valid','common_count','coverage','delta1_all_gt','own_absrel','common_absrel','common_mae_m','common_worst5_absrel','same_source_fraction_vs_never_on_pairwise_own','pairwise_never_count','pairwise_never_absrel','pairwise_condition_absrel','pairwise_signed_benefit','lost_vs_never_count','gained_vs_never_count','common_fraction_of_gt']
 offrows=official['rows']; require(len(offrows)==len(rows)==100,'100 rows',checks)
 maxdiff=0.; diffcount=0
 for a,b in zip(rows,offrows):
  require(a['method']==b['method'] and a['target']==b['target'],f'row identity {a["method"]}/{a["target"]}',checks)
  for k in num_fields:
   if isinstance(a[k],(int,np.integer)): require(int(a[k])==int(b[k]),f'{a["method"]}/{a["target"]}/{k}',checks)
   else:
    dd=abs(float(a[k])-float(b[k])); maxdiff=max(maxdiff,dd); diffcount+=1; require(dd<=1e-12,f'{a["method"]}/{a["target"]}/{k}',checks)
 require(set(official['equal_four_target_means'])==set(avg),'aggregate keys',checks)
 for n in methods:
  for k in keys:
   dd=abs(avg[n][k]-official['equal_four_target_means'][n][k]); maxdiff=max(maxdiff,dd); require(dd<=1e-12,f'aggregate/{n}/{k}',checks)
 for k in keys: require(abs(random_avg[k]-official['random20_equal_seed_means'][k])<=1e-12,f'random aggregate/{k}',checks)
 require(comparisons==official['target_comparisons'],'target comparisons exact',checks)
 # Independently rederive 39 masks and random seed deterministic assignments from score selection.
 sel=load(PRED/'selection.npz'); bm=sel['block_masks']; require(bm.shape==(25,4,196),'selection mask shape',checks); require((bm[2:].sum(2)==39).all(),'39 blocks/source all treatment',checks)
 risk=sel['block_disagreement']; dflat=np.abs(load(ROOT/'results/S15B_prefix_proposals/proposals.npz')['new_self_z_m']-load(ROOT/'results/S15B_prefix_proposals/proposals.npz')['old_self_z_m']);
 # Verify selection block scores agree to direct proposal medians.
 prop=load(ROOT/'results/S15B_prefix_proposals/proposals.npz'); D=np.abs(prop['new_self_z_model'].astype(np.float64)-prop['old_self_z_model'].astype(np.float64))/(.5*(np.abs(prop['new_self_z_model'].astype(np.float64))+np.abs(prop['old_self_z_model'].astype(np.float64)))); direct=D.reshape(4,14,16,14,16).transpose(0,1,3,2,4).reshape(4,196,256); direct=np.median(direct,-1); require(np.array_equal(direct,risk),'block disagreement direct parity',checks)
 conf=(prop['new_conf_self'].astype(float)-prop['old_conf_self'].astype(float)).reshape(4,14,16,14,16).transpose(0,1,3,2,4).reshape(4,196,256).mean(-1)
 low_expected=np.zeros((4,196),bool); high_expected=np.zeros((4,196),bool); conf_expected=np.zeros((4,196),bool)
 for s in range(4):
  low_expected[s,np.lexsort((np.arange(196),direct[s]))[:39]]=True; high_expected[s,np.lexsort((np.arange(196),-direct[s]))[:39]]=True; conf_expected[s,np.lexsort((np.arange(196),-conf[s]))[:39]]=True
 require(np.array_equal(bm[2],low_expected),'low mask direct parity',checks); require(np.array_equal(bm[3],high_expected),'high mask direct parity',checks); require(np.array_equal(bm[4],conf_expected),'confidence mask direct parity',checks)
 for idx,seed in enumerate(range(20260914,20260934),5):
  rng=np.random.default_rng(seed); ex=np.zeros((4,196),bool)
  for s in range(4): ex[s,rng.choice(196,39,replace=False)]=True
  require(np.array_equal(bm[idx],ex),f'random mask seed {seed}',checks)
 # Save independent data and report.
 out={'schema':'s99-independent-score-recompute-v1','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_SCORE_RECOMPUTE','gt_read_after_pre_gt_pass':True,'checks':checks,'check_count':len(checks),'failed':sum(not x['passed'] for x in checks),'rows':rows,'equal_four_target_means':avg,'random20_equal_seed_means':random_avg,'target_comparisons':comparisons,'expected_status':expected_status,'max_float_abs_diff':maxdiff,'prediction_seal_sha256':sha(PRED/'PREDICTION_SEAL.json'),'official_scores_sha256':sha(SCORE/'SCORES.json')}
 (OUT/'SCORE_RECOMPUTE_RESULT.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n'); np.savez_compressed(OUT/'independent_common_masks.npz',common=np.asarray(common_masks))
 print(json.dumps({'status':out['status'],'checks':len(checks),'failed':out['failed'],'rows':len(rows),'max_float_abs_diff':maxdiff,'expected_status':expected_status},ensure_ascii=False))
if __name__=='__main__':main()
