#!/usr/bin/env python3
"""S145 analysis (frozen with the protocol). usage: analyze_s145.py <S141 SCORES_chess_B.json (B_original)> <S141 SCORES_chess_A.json>
  <scores_off> <scores_target_only> <scores_bias_only> <scores_permuted> <POSE_ARMS.json> <out.json>
Primary: B_off - B_original. Key secondary: B_target_only - B_original. Others: bias_only, permuted vs original; practical
references A (A_mem) and raw B2. Window mean over seeds 3-6; window bootstrap (10k, rng 0); +-0.2 dB / 0.01 SSIM; pair rule."""
import json, math, sys
from pathlib import Path
import numpy as np
J = lambda p: json.loads(Path(p).read_text())
B0, A, OFF, TGT, BIAS, PERM, PA = [J(p) for p in sys.argv[1:8]]; OUT = Path(sys.argv[8])
pair = {r['window_id']: r['pair'] for r in PA['rows']}
def wm(S, mode, metric):
    d = {}
    for r in S['runs'].values():
        if r['mode'] != mode or r['seed'] not in (3, 4, 5, 6): continue
        v = r[metric]; assert v is not None and math.isfinite(v)
        assert r['seed'] not in d.setdefault(r['window_id'], {}); d[r['window_id']][r['seed']] = v
    assert len(d) == 24 and all(sorted(x) == [3, 4, 5, 6] for x in d.values()), (mode, len(d))
    return {w: float(np.mean(list(x.values()))) for w, x in d.items()}
def summ(a, b, thr):
    assert set(a) == set(b); ks = sorted(a); v = np.array([a[k] - b[k] for k in ks]); rng = np.random.default_rng(0)
    bt = [rng.choice(v, len(v)).mean() for _ in range(10000)]; lo, hi = (float(x) for x in np.percentile(bt, [2.5, 97.5])); m = float(v.mean())
    pm = {p: float(np.mean([a[k] - b[k] for k in ks if pair[k] == p])) for p in sorted(set(pair.values()))}
    verdict = ('IMPROVES' if m >= thr and lo > 0 and sum(x < 0 for x in pm.values()) < 2 else 'WORSENS' if m <= -thr and hi < 0 else
               'NO_MATERIAL_CHANGE' if abs(m) < thr and lo <= 0 <= hi else 'INCONCLUSIVE')
    return {'mean': m, 'ci95': [lo, hi], 'wins': int((v > 0).sum()), 'n': len(v), 'pair_means': pm, 'verdict': verdict}
res = {}
for metric, wk, thr in (('psnr_db', 'psnr', 0.2), ('ssim', 'ssim', 0.01), ('psnr_covered', None, 0.2), ('psnr_holes', None, 0.2)):
    arms = {'B_original': wm(B0, 'B_mem', metric), 'B_off': wm(OFF, 'B_mem', metric), 'B_target_only': wm(TGT, 'B_mem', metric),
            'B_bias_only': wm(BIAS, 'B_mem', metric), 'B_permuted': wm(PERM, 'B_mem', metric), 'A': wm(A, 'A_mem', metric)}
    if wk: arms['B2'] = {w: v[wk] for w, v in B0['warps'].items()}
    out = {'means': {k: float(np.mean(list(v.values()))) for k, v in arms.items()}}
    pairs = [('PRIMARY: B_off - B_original', 'B_off', 'B_original'), ('SECONDARY: B_target_only - B_original', 'B_target_only', 'B_original'),
             ('B_bias_only - B_original', 'B_bias_only', 'B_original'), ('B_permuted - B_original', 'B_permuted', 'B_original'),
             ('B_off - A', 'B_off', 'A'), ('B_target_only - A', 'B_target_only', 'A')]
    if wk: pairs += [('B_off - B2', 'B_off', 'B2'), ('B_target_only - B2', 'B_target_only', 'B2')]
    for name, x, y in pairs: out[name] = summ(arms[x], arms[y], thr)
    res[metric] = out
OUT.write_text(json.dumps(res, indent=1) + '\n')
for metric in ('psnr_db', 'ssim'):
    print(metric, {k: round(v, 3) for k, v in res[metric]['means'].items()})
    for k, c in res[metric].items():
        if k != 'means': print(f"  {k:40s} {c['mean']:+.3f} [{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['wins']}/24 {c['verdict']}")
