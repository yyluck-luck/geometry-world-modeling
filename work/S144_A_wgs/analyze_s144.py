#!/usr/bin/env python3
"""S144 analysis (frozen with the protocol; R263 §3.4-3.5).
  analyze_s144.py dev-fit  <dev FIT scores> <alpha.json>
  analyze_s144.py dev-gate <dev scores with frozen alpha> <out.json>
  analyze_s144.py case     <chess scores> <rgbd scores> <POSE_ARMS.json> <out.json>
Mandatory practical controls: B2, V, P_V, P_FC, P_AC, BL_V, BL_FC, BL_AC. Reported references: A_none, REV_AC, F_C."""
import json, math, sys
from pathlib import Path
import numpy as np
MAND = ['B2', 'V', 'P_V', 'P_FC', 'P_AC', 'BL_V', 'BL_FC', 'BL_AC']
J = lambda p: json.loads(Path(p).read_text())


def by_window(runs, f):  # seed-mean per window of f(rec); strict finiteness
    d = {}
    for r in runs.values():
        v = f(r); assert v is not None and math.isfinite(v), r['window_id']
        d.setdefault(r['window_id'], []).append(v)
    n = {len(v) for v in d.values()}; assert len(n) == 1, 'unequal seed counts'
    return {w: float(np.mean(v)) for w, v in d.items()}


def boot(v):
    v = np.array(v); rng = np.random.default_rng(0); b = [rng.choice(v, len(v)).mean() for _ in range(10000)]
    return [float(x) for x in np.percentile(b, [2.5, 97.5])]


def contrasts(runs, group=None):
    P = lambda arm: (lambda r: r[arm]['psnr_db']); S = lambda arm: (lambda r: r[arm]['ssim'])
    I = by_window(runs, lambda r: (r['A_R']['psnr_db'] - r['A_C']['psnr_db']) - (r['F_R']['psnr_db'] - r['F_C']['psnr_db']))
    out = {'I': I}
    for ctl in ['A_C'] + MAND + [k for k in ('A_none', 'REV_AC', 'F_C') if all(k in r for r in runs.values())]:
        out[f'A_R-{ctl}'] = by_window(runs, lambda r, c=ctl: r['A_R']['psnr_db'] - r[c]['psnr_db'])
        out[f'SSIM A_R-{ctl}'] = by_window(runs, lambda r, c=ctl: r['A_R']['ssim'] - r[c]['ssim'])
    for a, b in (('A_C', 'F_C'), ('A_C', 'B2'), ('F_C', 'B2'), ('F_C', 'V'), ('A_R', 'F_R')):
        out[f'{a}-{b}'] = by_window(runs, lambda r, x=a, y=b: r[x]['psnr_db'] - r[y]['psnr_db'])
    return out


mode = sys.argv[1]
if mode == 'dev-fit':
    S = J(sys.argv[2])['runs']; alpha = {}
    for g in ('V', 'FC', 'AC'):
        grid = sorted(next(iter(S.values()))[f'BLgrid_{g}'], key=float)
        score = {a: np.mean(list(by_window(S, lambda r, a=a, g=g: r[f'BLgrid_{g}'][a]).values())) for a in grid}
        best = max(score.values()); alpha[g] = float(min(float(a) for a in grid if score[a] == best))   # ties -> smaller alpha
        print(g, 'alpha', alpha[g], 'dev mean PSNR', round(best, 3))
    Path(sys.argv[3]).write_text(json.dumps({'alpha': alpha, 'fitted_on': 'S144 development (32 monitor clips, seeds 3,4)'}, indent=1) + '\n')
elif mode == 'dev-gate':
    S = J(sys.argv[2])['runs']; c = contrasts(S)
    seq = {}
    for r in S.values(): seq[r['window_id']] = r['seq']
    res = {'means': {k: float(np.mean(list(v.values()))) for k, v in c.items()}}
    per_seq = {q: {k: float(np.mean([v[w] for w in v if seq[w] == q])) for k, v in c.items()} for q in sorted(set(seq.values()))}
    res['per_sequence'] = per_seq
    need = ['I', 'A_R-A_C'] + [f'A_R-{m}' for m in MAND]
    ok_mean = all(res['means'][k] >= 0.20 for k in need)
    ok_ssim = all(res['means'][f'SSIM A_R-{m}'] >= -0.01 for m in ['A_C'] + MAND)
    ok_seq = all(per_seq[q][k] >= 0 for q in per_seq for k in need)
    res['PERFORMANCE_GO'] = bool(ok_mean and ok_ssim and ok_seq)
    res['checks'] = {'means_ge_0.20': ok_mean, 'ssim_ge_-0.01': ok_ssim, 'nonnegative_both_sequences': ok_seq}
    Path(sys.argv[3]).write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({'checks': res['checks'], 'PERFORMANCE_GO': res['PERFORMANCE_GO']}, indent=1))
    for k in need + ['A_C-F_C', 'A_C-B2', 'F_C-B2', 'F_C-V']: print(f'  {k:14s} {res["means"][k]:+.3f}  per-seq', {q: round(per_seq[q][k], 3) for q in per_seq})
elif mode == 'case':
    CH, RG, PA = J(sys.argv[2])['runs'], J(sys.argv[3])['runs'], J(sys.argv[4]); OUT = Path(sys.argv[5])
    pair = {r['window_id']: r['pair'] for r in PA['rows']}
    c = contrasts(CH); res = {'chess': {}, 'rgbd': {}}
    for k, v in c.items():
        vals = [v[w] for w in sorted(v)]; pm = {p: float(np.mean([v[w] for w in v if pair[w] == p])) for p in sorted(set(pair.values()))}
        thr = 0.01 if k.startswith('SSIM') else 0.20
        res['chess'][k] = {'mean': float(np.mean(vals)), 'ci95': boot(vals), 'wins': int(sum(x > 0 for x in vals)), 'n': len(vals), 'pair_means': pm}
    def passes(k):
        r = res['chess'][k]; return r['mean'] >= 0.20 and r['ci95'][0] > 0 and sum(x < 0 for x in r['pair_means'].values()) < 2
    res['PRIMARY'] = {'I_passes': passes('I'), 'A_R_beats_A_C': passes('A_R-A_C'),
                      'A_R_beats_all_mandatory': all(passes(f'A_R-{m}') for m in MAND),
                      'ssim_ok': all(res['chess'][f'SSIM A_R-{m}']['mean'] >= -0.01 for m in ['A_C'] + MAND)}
    res['PRIMARY']['PASS'] = all(res['PRIMARY'].values())
    cr = contrasts(RG)
    res['rgbd'] = {k: {'mean': float(np.mean(list(v.values()))), 'ci95': boot(list(v.values())), 'wins': int(sum(x > 0 for x in v.values())), 'n': len(v)} for k, v in cr.items()}
    res['means_psnr'] = {pan: {arm: float(np.mean([r[arm]['psnr_db'] for r in R.values()])) for arm in next(iter(R.values())) if isinstance(next(iter(R.values()))[arm], dict) and 'psnr_db' in next(iter(R.values()))[arm]}
                         for pan, R in (('chess', CH), ('rgbd', RG))}
    OUT.write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res['PRIMARY'], indent=1)); print('chess means', {k: round(v, 3) for k, v in res['means_psnr']['chess'].items()})
    for k in ['I', 'A_R-A_C', 'A_C-F_C', 'A_C-B2'] + [f'A_R-{m}' for m in MAND]:
        r = res['chess'][k]; print(f"  {k:12s} {r['mean']:+.3f} [{r['ci95'][0]:+.3f},{r['ci95'][1]:+.3f}] wins {r['wins']}/{r['n']} | rgbd {res['rgbd'][k]['mean']:+.3f}")
