"""Frozen equal-window analysis; independently checked after execution."""
import json
import sys
from pathlib import Path
import numpy as np

def analyze(root):
    plan=json.loads((root/'PLAN.json').read_text())['contexts'];windows=[c['window_id'] for c in plan]
    arms=['native','real','zero','permuted','low_cfg'];metrics={};rows={}
    for arm in arms:
        data=json.loads((root/'results'/f'SCORES_{arm}.json').read_text())['runs']
        assert len(data)==12 and len({(r['window_id'],r['seed']) for r in data.values()})==12
        assert {(r['window_id'],r['seed']) for r in data.values()}=={(w,s) for w in windows for s in [3,4]}
        rows[arm]=data;metrics[arm]={}
        for metric in ['psnr_db','ssim']:
            a=np.array([np.mean([r[metric] for r in data.values() if r['window_id']==w]) for w in windows])
            assert np.isfinite(a).all();metrics[arm][metric]=a
    ix=np.random.default_rng(0).integers(0,6,(10000,6));contrasts={}
    for arm in ['native','zero','permuted','low_cfg']:
        d=metrics['real']['psnr_db']-metrics[arm]['psnr_db'];ss=metrics['real']['ssim']-metrics[arm]['ssim']
        ci=np.quantile(d[ix].mean(1),[.025,.975]);order=np.argsort(-d,kind='stable');remaining=float(d[order[2:]].mean())
        pairs={p:float(np.mean([d[i] for i,w in enumerate(windows) if w.rsplit('_s',1)[0]==p])) for p in sorted({w.rsplit('_s',1)[0] for w in windows})}
        gates={'mean_psnr':float(d.mean())>=.2,'ci_lower':float(ci[0])>0,'ssim':float(ss.mean())>=0,
               'each_pair':all(x>0 for x in pairs.values()),'leave_top2':remaining>=.1}
        positive=np.maximum(d,0);share=float(positive[order[:2]].sum()/positive.sum()) if positive.sum()>0 else None
        contrasts[arm]={'mean_psnr':float(d.mean()),'ci95':ci.tolist(),'mean_ssim':float(ss.mean()),
            'per_window':dict(zip(windows,d.tolist())),'per_pair':pairs,'leave_top2_psnr':remaining,
            'top2_positive_gain_share':share,'gates':gates,'pass':all(gates.values())}
    return {'status':'GO_TO_REPLICATION_DIAGNOSTIC' if all(v['pass'] for v in contrasts.values()) else 'STOP_TESTED_POLICY',
        'claim_scope':'Exposed-panel fixed UC-input substitution; no novelty, generalization or drift-causation claim.',
        'arm_means':{arm:{m:float(v.mean()) for m,v in ms.items()} for arm,ms in metrics.items()},
        'contrasts':contrasts,'new_method_validated':False,'novelty_authorization':'NONE'}

if __name__=='__main__':
    root=Path(sys.argv[1]);result=analyze(root);(root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
