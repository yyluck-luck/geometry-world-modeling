#!/usr/bin/env python3
"""Exploratory saved-proposal intervention; no learned model is invoked."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, resource, signal, sys, time, traceback
import numpy as np

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s15b_memory_consumer as consumer
METHODS = ['never', 'all_new', 'low_disagreement', 'high_disagreement', 'confidence_gain'] + [f'random_{s}' for s in range(20260914,20260934)]
MANIFEST = ROOT/'results/S15B_consumer_predictions/frozen_manifest.json'
OLD_PRED = ROOT/'results/S15B_consumer_predictions/target_predictions.npz'
GT = ROOT/'results/S15B_consumer_scores/evaluation_gt.npz'

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def load(p):
    with np.load(p,allow_pickle=False) as z: return {k:z[k] for k in z.files}
def check(cond,msg):
    if not cond: raise ValueError(msg)
def assert_hashes(mapping):
    for rel,digest in mapping.items(): check(sha(ROOT/rel)==digest,'changed identity: '+rel)

def freeze(review_path):
    check(not (BASE/'FREEZE.json').exists(),'freeze already exists')
    m=json.loads(MANIFEST.read_text())
    past=json.loads((ROOT/'work/S91R_saved_future_error_reanalysis/control_audit_results.json').read_text())
    paths=[MANIFEST, Path(__file__), BASE/'PROTOCOL.md', Path(review_path)] + [Path(m[k]) for k in ['bridge','proposals','target_cameras','rule_masks']] + [Path(consumer.__file__), OLD_PRED]
    assert_hashes({str(Path(m[k]).relative_to(ROOT)):m['predict_identities'][m[k]] for k in ['bridge','proposals','target_cameras','rule_masks']})
    check(sha(consumer.__file__)==m['runner_sha256'],'original renderer changed')
    write(BASE/'FREEZE.json',{'schema':'s99-freeze-v1','frozen_utc':utc(),'scope':'exploratory previously exposed scene; fixed source rewrite budget, not memory-slot budget','methods':METHODS,'blocks_per_source':39,'seeds':list(range(20260914,20260934)),'identities':{str(p.relative_to(ROOT)):sha(p) for p in paths},'gt_identity_from_previous_record':{str(GT.relative_to(ROOT)):past['inputs'][str(GT.relative_to(ROOT))]},'model_calls':0,'formal_s91':False})

def run_predict(out,f):
    m=json.loads(MANIFEST.read_text())
    b,p,t,legacy=[load(m[k]) for k in ['bridge','proposals','target_cameras','rule_masks']]
    old,new,K,scale,valid=consumer.validate_inputs(b,p,t,legacy)
    check(valid.all(),'this fixed experiment requires all 200704 source pixels valid')
    d=np.abs(new-old)/(0.5*(np.abs(new)+np.abs(old)))
    scores=d.reshape(4,14,16,14,16).transpose(0,1,3,2,4).reshape(4,196,256)
    risk=np.median(scores,axis=-1)
    conf=(p['new_conf_self'].astype(float)-p['old_conf_self'].astype(float)).reshape(4,14,16,14,16).transpose(0,1,3,2,4).reshape(4,196,256).mean(-1)
    block_masks=np.zeros((len(METHODS),4,196),dtype=bool)
    block_masks[1]=True
    for mi,score,sign in [(2,risk,1),(3,risk,-1),(4,conf,-1)]:
        for s in range(4): block_masks[mi,s,np.lexsort((np.arange(196),sign*score[s]))[:39]]=True
    for mi,seed in enumerate(f['seeds'],5):
        rng=np.random.default_rng(seed)
        for s in range(4): block_masks[mi,s,rng.choice(196,39,replace=False)]=True
    check((block_masks[2:].sum(-1)==39).all(),'unequal source rewrite budgets')
    masks=np.repeat(np.repeat(block_masks.reshape(-1,4,14,14),16,axis=2),16,axis=3)
    predictions=[]; identities=[]; runtimes=[]; visits=[]; amplitude=[]
    for name,mask in zip(METHODS,masks):
        start=time.monotonic(); z=np.where(mask,new,old)
        rendered=[consumer.render(z,valid,b['source_c2w'],target,K,scale) for target in t['target_c2w']]
        predictions.append([r[0] for r in rendered]);identities.append([r[1] for r in rendered]);visits.append([r[2] for r in rendered]);runtimes.append(time.monotonic()-start)
        selected=np.abs(new[mask]-old[mask])/scale
        amplitude.append({'method':name,'selected_blocks_per_source':block_masks[METHODS.index(name)].sum(-1).tolist(),'changed_source_pixels':int(np.count_nonzero(z!=old)),'mean_abs_rewrite_m_all_source_pixels':float(np.abs(z-old).mean()/scale),'rms_rewrite_m_all_source_pixels':float(np.sqrt(np.mean(((z-old)/scale)**2))),'selected_absolute_change_quantiles_m':np.quantile(selected,[0,.25,.5,.75,.95,1]).tolist() if len(selected) else None,'selected_disagreement_quantiles':np.quantile(d[mask],[0,.25,.5,.75,.95,1]).tolist() if len(selected) else None,'pixel_mask_raw_bytes_sha256':hashlib.sha256(mask.tobytes()).hexdigest()})
    predictions=np.asarray(predictions);identities=np.asarray(identities)
    check(np.isfinite(predictions).all() and (predictions>=0).all(),'invalid predictions')
    saved=load(OLD_PRED)
    check(np.array_equal(predictions[:2],saved['depth_m'][:2]),'never/all_new depths not identical to saved baseline')
    check(np.array_equal(identities[:2],saved['source_pixel_identity'][:2]),'never/all_new provenance not identical')
    np.savez_compressed(out/'predictions.npz',depth_m=predictions,source_pixel_identity=identities)
    np.savez_compressed(out/'selection.npz',block_masks=block_masks,pixel_masks=masks,block_disagreement=risk,confidence_gain=conf)
    write(out/'description.json',{'methods':METHODS,'target_indices':[20,21,22,23],'sources':[0,3,6,9],'amplitude':amplitude,'render_seconds':runtimes,'projected_source_visits':visits,'endpoint_exact_parity':True,'model_calls':0,'evaluation_gt_read':False,'source_proposals_previously_exposed':True,'source_identity':'source ordinal*224*224+row*224+col','numpy_version':np.__version__,'random_generator':type(np.random.default_rng(0).bit_generator).__name__})

def tail(x):
    if not len(x): return None
    a=np.sort(np.asarray(x,dtype=float))[::-1]; mass=.05*len(a); k=int(np.floor(mass))
    return float((a[:k].sum()+(mass-k)*a[k])/mass)
def run_score(out,f,pred_dir):
    seal=json.loads((pred_dir/'PREDICTION_SEAL.json').read_text())
    check(seal['freeze_sha256']==sha(BASE/'FREEZE.json'),'prediction freeze mismatch')
    for name,h in seal['files'].items(): check(sha(pred_dir/name)==h,'sealed prediction changed')
    check(json.loads((pred_dir/'RUN.json').read_text())['status']=='PASS','prediction did not pass')
    assert_hashes(f['gt_identity_from_previous_record'])
    gt_read_start=utc(); g=load(GT)['depth_m'].astype(float)
    a=load(pred_dir/'predictions.npz');pred=a['depth_m'];ids=a['source_pixel_identity'];pv=np.isfinite(pred)&(pred>0)
    check(g.shape==(4,224,224),'GT shape')
    rows=[];common_masks=[]
    for ti in range(4):
        gv=np.isfinite(g[ti])&(g[ti]>0); common=pv[:,ti].all(axis=0)&gv;common_masks.append(common)
        check(common.sum()>0,'empty common mask')
        for mi,name in enumerate(METHODS):
            own=gv&pv[mi,ti];z=pred[mi,ti];diff=np.abs(z[common]-g[ti][common]);e=diff/g[ti][common]
            correct=int(np.count_nonzero(np.maximum(z[own]/g[ti][own],g[ti][own]/z[own])<1.25))
            ownerr=np.abs(z[own]-g[ti][own])/g[ti][own]
            same=own&pv[0,ti]
            base_pair=np.abs(pred[0,ti][same]-g[ti][same])/g[ti][same]; cond_pair=np.abs(z[same]-g[ti][same])/g[ti][same]
            rows.append({'method':name,'target':20+ti,'gt_valid':int(gv.sum()),'common_count':int(common.sum()),'common_fraction_of_gt':float(common.sum()/gv.sum()),'coverage':float(own.sum()/gv.sum()),'delta1_all_gt':correct/int(gv.sum()),'own_absrel':float(ownerr.mean()) if len(ownerr) else None,'common_absrel':float(e.mean()),'common_mae_m':float(diff.mean()),'common_worst5_absrel':tail(e),'same_source_fraction_vs_never_on_pairwise_own':float(np.mean(ids[mi,ti][same]==ids[0,ti][same])),'pairwise_never_count':int(same.sum()),'pairwise_never_absrel':float(base_pair.mean()),'pairwise_condition_absrel':float(cond_pair.mean()),'pairwise_signed_benefit':float((base_pair-cond_pair).mean()),'lost_vs_never_count':int((gv&pv[0,ti]&~pv[mi,ti]).sum()),'gained_vs_never_count':int((gv&~pv[0,ti]&pv[mi,ti]).sum())})
    keys=['common_absrel','common_worst5_absrel','coverage','delta1_all_gt','common_mae_m','own_absrel']
    avg={name:{k:float(np.mean([r[k] for r in rows if r['method']==name])) for k in keys} for name in METHODS}
    random_avg={k:float(np.mean([avg[name][k] for name in METHODS[5:]])) for k in keys}
    comparisons=[]
    for ti in range(4):
        tr={r['method']:r for r in rows if r['target']==20+ti}
        rand=float(np.mean([tr[name]['common_absrel'] for name in METHODS[5:]]));low=tr['low_disagreement']['common_absrel']
        comparisons.append({'target':20+ti,'low_absrel':low,'random_mean_absrel':rand,'confidence_gain_absrel':tr['confidence_gain']['common_absrel'],'high_absrel':tr['high_disagreement']['common_absrel'],'benefit_vs_random_mean':rand-low,'benefit_vs_confidence':tr['confidence_gain']['common_absrel']-low,'low_better_than_random_seed_count':sum(low<tr[name]['common_absrel'] for name in METHODS[5:])})
    lo=avg['low_disagreement'];co=avg['confidence_gain']; passed=(sum(c['benefit_vs_random_mean']>0 and c['benefit_vs_confidence']>0 for c in comparisons)>=3 and lo['common_absrel']<random_avg['common_absrel'] and lo['common_absrel']<co['common_absrel'] and lo['delta1_all_gt']>=max(random_avg['delta1_all_gt'],co['delta1_all_gt']))
    reversal=(avg['high_disagreement']['common_absrel']<lo['common_absrel'] or sum(c['high_absrel']<c['low_absrel'] for c in comparisons)>=3)
    passed=passed and not reversal
    result={'schema':'s99-scores-v1','status':'KEEP_LOCAL_CANDIDATE_ONLY' if passed else 'STOP_LOW_DISAGREEMENT_ADVANTAGE_IN_THIS_SETTING','low_risk_ordering_reversal':reversal,'rows':rows,'equal_four_target_means':avg,'random20_equal_seed_means':random_avg,'target_comparisons':comparisons,'gt_read_started_utc':gt_read_start,'prediction_seal_sha256':sha(pred_dir/'PREDICTION_SEAL.json'),'independent_scenes':1,'model_calls':0,'formal_s91':False,'new_method_validated':False,'novelty_authorization':'NONE','limits':['previously exposed four correlated targets','un-calibrated discrepancy, not a probabilistic risk bound','source rewrite count fixed, not update magnitude or memory slot budget','geometric consumer rerender, not learned-state update or VMem generation','all-method common mask is fixed to these 25 conditions; coverage and all-GT accuracy separately reported','random seeds are descriptive control variation, not independent scenes']}
    write(out/'SCORES.json',result);np.savez_compressed(out/'evaluation_masks.npz',common=np.asarray(common_masks))
    for name,h in seal['files'].items(): check(sha(pred_dir/name)==h,'post-score prediction changed')
    assert_hashes(f['gt_identity_from_previous_record'])
    print(json.dumps({'status':result['status'],'means':{k:avg[k] for k in METHODS[:5]},'random_mean':random_avg},ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['freeze','predict','score']);ap.add_argument('--review');ap.add_argument('--output');ap.add_argument('--predictions');args=ap.parse_args()
    if args.mode=='freeze': freeze(Path(args.review).resolve());return
    out=Path(args.output).resolve();check(not out.exists(),'use fresh output');out.mkdir(parents=True)
    record={'mode':args.mode,'started_utc':utc(),'status':'RUNNING','model_calls':0};t0=time.monotonic()
    def timeout(*a): raise TimeoutError('600 second stage budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
    try:
        f=json.loads((BASE/'FREEZE.json').read_text());assert_hashes(f['identities']);record['freeze_sha256']=sha(BASE/'FREEZE.json')
        if args.mode=='predict': run_predict(out,f)
        else: run_score(out,f,Path(args.predictions).resolve())
        assert_hashes(f['identities']);record['status']='PASS'
    except BaseException as e: record.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);record.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-t0,peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
        if record['elapsed_seconds']>600 or record['peak_rss_bytes']>8*1024**3: record.update(status='FAIL',budget_exceeded=True)
        write(out/'RUN.json',record)
    if args.mode=='predict' and record['status']=='PASS':
        write(out/'PREDICTION_SEAL.json',{'sealed_utc':utc(),'freeze_sha256':sha(BASE/'FREEZE.json'),'evaluation_gt_read':False,'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()}})
    print(json.dumps(record,ensure_ascii=False),flush=True)
    if record['status']!='PASS': raise SystemExit(1)
if __name__=='__main__':main()
