from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, sys, time, signal, resource, traceback
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import s15b_memory_consumer as consumer
S99=ROOT/'work/S99_fixed_budget_risk_update'
GT=ROOT/'results/S15B_consumer_scores/evaluation_gt.npz'
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def load(p):
    with np.load(p,allow_pickle=False) as a: return {k:a[k] for k in a.files}
def check(c,m):
    if not c: raise ValueError(m)
def identities(d):
    for p,h in d.items(): check(sha(ROOT/p)==h,'identity changed '+p)
def inputs():
    f=json.loads((S99/'FREEZE.json').read_text()); identities(f['identities'])
    m=json.loads((ROOT/'results/S15B_consumer_predictions/frozen_manifest.json').read_text())
    b,p,t,legacy=[load(m[k]) for k in ['bridge','proposals','target_cameras','rule_masks']]
    old,new,K,scale,valid=consumer.validate_inputs(b,p,t,legacy)
    check(valid.all(),'invalid historical source')
    return f,b,p,t,old,new,K,scale,valid
def blocks(a): return a.reshape(4,14,16,14,16).transpose(0,1,3,2,4).reshape(4,196,256)
def pixels(a): return np.repeat(np.repeat(a.reshape(4,14,14),16,axis=1),16,axis=2)
def select(out):
    # Before scanning historical block magnitudes, bind rules and all inherited identities.
    start={'utc':utc(),'code_sha256':sha(__file__),'protocol_sha256':sha(BASE/'PROTOCOL.md'),'s99_freeze_sha256':sha(S99/'FREEZE.json'),'gt_read':False}
    write(out/'BEFORE_SCAN.json',start)
    f,b,p,t,old,new,K,scale,valid=inputs()
    d=np.median(blocks(np.abs(new-old)/(.5*(np.abs(new)+np.abs(old)))),axis=2)
    c=blocks(p['new_conf_self'].astype(float)-p['old_conf_self'].astype(float)).mean(2)
    changes=blocks((new-old)/scale);mean=np.abs(changes).mean(2);rms=np.sqrt((changes**2).mean(2))
    pairlist=[]; qualifications=[]; masks=[]; records=[]
    for s in range(4):
        low=set(np.lexsort((np.arange(196),d[s]))[:39]);conf=set(np.lexsort((np.arange(196),-c[s]))[:39])
        lp=sorted(low-conf);cp=sorted(conf-low);edges=[]
        for l in lp:
            for q in cp:
                if min(mean[s,l],mean[s,q],rms[s,l],rms[s,q])<=0: continue
                mr=max(mean[s,l],mean[s,q])/min(mean[s,l],mean[s,q]);rr=max(rms[s,l],rms[s,q])/min(rms[s,l],rms[s,q])
                if mr<=1.10 and rr<=1.25: edges.append((abs(float(np.log(mean[s,l]/mean[s,q]))),int(l),int(q),float(mr),float(rr)))
        usedl=set();usedc=set();chosen=[]
        for _,l,q,mr,rr in sorted(edges):
            if l in usedl or q in usedc: continue
            usedl.add(l);usedc.add(q);chosen.append((l,q,mr,rr))
            if len(chosen)==4: break
        qualifications.append({'source':s,'low_only':list(map(int,lp)),'confidence_only':list(map(int,cp)),'legal_edges':len(edges),'selected_pair_count':len(chosen),'all_legal_edges':edges})
        for rank,(l,q,mr,rr) in enumerate(chosen):
            pid=len(pairlist);pairlist.append({'pair_id':pid,'source':s,'rank':rank,'low_block':l,'conf_block':q,'mean_ratio':mr,'rms_ratio':rr,'mean_m':[float(mean[s,l]),float(mean[s,q])],'rms_m':[float(rms[s,l]),float(rms[s,q])]})
            for ctx in range(2):
                seed=2026091400+100*s+2*rank+ctx;rng=np.random.default_rng(seed);bg=np.zeros((4,196),bool)
                for si in range(4):
                    candidates=np.array([k for k in range(196) if si!=s or k not in [l,q]])
                    bg[si,rng.choice(candidates,38 if si==s else 39,replace=False)]=True
                for arm,candidate in [('low',l),('conf',q)]:
                    mask=bg.copy();mask[s,candidate]=True;check((mask.sum(1)==39).all(),'budget mismatch')
                    masks.append(mask);records.append({'condition':len(records),'pair_id':pid,'source':s,'context':ctx,'seed':seed,'arm':arm})
    np.savez_compressed(out/'selection.npz',block_masks=np.asarray(masks,dtype=bool).reshape(-1,4,196),disagreement=d,confidence_gain=c,amplitude_mean=mean,amplitude_rms=rms)
    check(start['code_sha256']==sha(__file__) and start['protocol_sha256']==sha(BASE/'PROTOCOL.md'),'rules changed during scan')
    write(out/'SELECTION.json',{'created_utc':utc(),'status':'READY' if pairlist else 'NO_MATCH_STOP','pairs':pairlist,'qualifications':qualifications,'conditions':records,'numpy_version':np.__version__,'rng':'PCG64','gt_read':False})
def freeze(review):
    check(not (BASE/'FREEZE.json').exists(),'already frozen')
    sel=BASE/'select_01';old=json.loads((S99/'FREEZE.json').read_text());identities(old['identities'])
    before=json.loads((sel/'BEFORE_SCAN.json').read_text())
    check(json.loads((sel/'RUN.json').read_text())['status']=='PASS','selection stage failed')
    check(json.loads((sel/'SELECTION.json').read_text())['status']=='READY','no matched candidates')
    check(before['s99_freeze_sha256']==sha(S99/'FREEZE.json'),'S99 binding changed')
    check(before['code_sha256']==sha(__file__) and before['protocol_sha256']==sha(BASE/'PROTOCOL.md'),'selection rules changed')
    files=[Path(__file__),BASE/'PROTOCOL.md',Path(review).resolve(),S99/'FREEZE.json']+[p for p in sel.iterdir() if p.is_file()]
    write(BASE/'FREEZE.json',{'created_utc':utc(),'identities':{**old['identities'],**{str(p.relative_to(ROOT)):sha(p) for p in files}},'gt_identity':old['gt_identity_from_previous_record'],'new_method_validated':False})
def predict(out):
    f=json.loads((BASE/'FREEZE.json').read_text());identities(f['identities'])
    a=load(BASE/'select_01/selection.npz');meta=json.loads((BASE/'select_01/SELECTION.json').read_text());check(meta['status']=='READY','no candidate matches')
    _,b,p,t,old,new,K,scale,valid=inputs();pred=[];ids=[];visits=[];z0=None
    for mask in a['block_masks']:
        z=np.where(pixels(mask),new,old)
        if z0 is None:z0=z.copy()
        rows=[consumer.render(z,valid,b['source_c2w'],q,K,scale) for q in t['target_c2w']]
        pred.append([r[0] for r in rows]);ids.append([r[1] for r in rows]);visits.append([r[2] for r in rows])
    replay=consumer.render(z0,valid,b['source_c2w'],t['target_c2w'][0],K,scale)
    check(np.array_equal(replay[0],pred[0][0]) and np.array_equal(replay[1],ids[0][0]),'replay differs')
    pred=np.asarray(pred);ids=np.asarray(ids);check(np.isfinite(pred).all() and (pred>=0).all(),'prediction invalid')
    check(np.array_equal(pred>0,ids>=0),'source validity mismatch')
    np.savez_compressed(out/'predictions.npz',depth_m=pred,source_pixel_identity=ids)
    write(out/'DESCRIPTION.json',{'completed_utc':utc(),'render_count':len(pred)*4,'replay_count':1,'replay_exact':True,'visits':visits,'gt_read':False,'model_calls':0,'freeze_sha256':sha(BASE/'FREEZE.json')})
    identities(f['identities'])
def tail(a):
    a=np.sort(a)[::-1];mass=.05*len(a);k=int(mass)
    return float((a[:k].sum()+(mass-k)*a[k])/mass)
def score(out):
    f=json.loads((BASE/'FREEZE.json').read_text());identities(f['identities']);pd=BASE/'predict_01';seal=json.loads((pd/'SEAL.json').read_text())
    check(seal['freeze_sha256']==sha(BASE/'FREEZE.json'),'seal freeze')
    for n,h in seal['files'].items():check(sha(pd/n)==h,'prediction changed')
    check(json.loads((pd/'RUN.json').read_text())['status']=='PASS','prediction failure')
    gt_begin=utc();identities(f['gt_identity']);g=load(GT)['depth_m'].astype(float)
    preds=load(pd/'predictions.npz')['depth_m'];selection=json.loads((BASE/'select_01/SELECTION.json').read_text());rows=[];pairs=[]
    for rec,zs in zip(selection['conditions'],preds):
        for ti,z in enumerate(zs):
            gv=np.isfinite(g[ti])&(g[ti]>0);v=gv&(z>0)&np.isfinite(z);n=int(gv.sum());check(n>0,'GT empty')
            e=np.abs(z[v]-g[ti][v])/g[ti][v];caps={}
            for cap in [.5,1.,2.]:
                loss=np.full(n,cap);loss[v[gv]]=np.minimum(e,cap);caps[str(cap)]={'mean':float(loss.mean()),'worst5':tail(loss),'clipped_valid_count':int((e>cap).sum())}
            delta=int((np.maximum(z[v]/g[ti][v],g[ti][v]/z[v])<1.25).sum())/n
            rows.append({**rec,'target':20+ti,'gt_valid':n,'missing':n-int(v.sum()),'coverage':float(v.sum()/n),'delta1_all_gt':delta,'valid_only_absrel':float(e.mean()) if len(e) else None,'caps':caps})
    by={(r['pair_id'],r['context'],r['target'],r['arm']):r for r in rows}
    for pair in selection['pairs']:
        for ctx in range(2):
            for ti in range(20,24):
                l=by[pair['pair_id'],ctx,ti,'low'];c=by[pair['pair_id'],ctx,ti,'conf']
                pairs.append({'pair_id':pair['pair_id'],'source':pair['source'],'context':ctx,'target':ti,'benefit':{cap:l['caps'][cap]['mean']-c['caps'][cap]['mean'] for cap in ['0.5','1.0','2.0']},'delta1_gain':c['delta1_all_gt']-l['delta1_all_gt'],'coverage_gain':c['coverage']-l['coverage']})
    sources=sorted(set(p['source'] for p in selection['pairs']));by_source={str(s):{cap:float(np.mean([p['benefit'][cap] for p in pairs if p['source']==s])) for cap in ['0.5','1.0','2.0']} for s in sources}
    means={cap:float(np.mean([by_source[str(s)][cap] for s in sources])) for cap in ['0.5','1.0','2.0']}
    flips=[]
    for pair in selection['pairs']:
        for ti in range(20,24):
            vals=[p for p in pairs if p['pair_id']==pair['pair_id'] and p['target']==ti]
            flips.append({'pair_id':pair['pair_id'],'source':pair['source'],'target':ti,'context_sign_reversal':{cap:min(v['benefit'][cap] for v in vals)<-1e-10 and max(v['benefit'][cap] for v in vals)>1e-10 for cap in ['0.5','1.0','2.0']}})
    write(out/'SCORES.json',{'completed_utc':utc(),'gt_read_begin_utc':gt_begin,'rows':rows,'paired_benefits':pairs,'source_equal_means':means,'by_source':by_source,'context_sign_reversals':flips,'reversal_counts':{cap:sum(p['context_sign_reversal'][cap] for p in flips) for cap in ['0.5','1.0','2.0']},'status':'LOCAL_MATCHED_CONF_SWAP_POSITIVE' if means['1.0']>1e-10 else 'NO_POSITIVE_MEAN_CONF_SWAP','matched_sources':sources,'new_method_validated':False,'novelty_authorization':'NONE','scope':'previously exposed geometric consumer; approximate amplitude match; no independent scenes'})
    identities(f['identities']);identities(f['gt_identity'])
    print(json.dumps({'mean_benefit':means,'sources':sources,'pairs':len(selection['pairs'])}),flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['select','freeze','predict','score']);ap.add_argument('--review');a=ap.parse_args()
    if a.mode=='freeze':freeze(a.review);return
    out=BASE/(a.mode+'_01');check(not out.exists(),'fresh output required');out.mkdir()
    rec={'started_utc':utc(),'mode':a.mode,'status':'RUNNING','model_calls':0};begin=time.monotonic()
    def timeout(*args):raise TimeoutError('stage 600 seconds')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
    try:
        {'select':select,'predict':predict,'score':score}[a.mode](out);rec['status']='PASS'
    except BaseException as e:rec.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);rec.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-begin,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if rec['peak_rss_bytes']>8*1024**3:rec.update(status='FAIL',error='RSS limit')
        write(out/'RUN.json',rec)
    if a.mode=='predict' and rec['status']=='PASS':write(out/'SEAL.json',{'created_utc':utc(),'freeze_sha256':sha(BASE/'FREEZE.json'),'files':{p.name:sha(p) for p in out.iterdir() if p.is_file()}})
    print(json.dumps(rec),flush=True)
    if rec['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
