#!/usr/bin/env python3
"""S137c analysis (Amendment 1). usage:
  analyze_s137c.py <B2_kps.json> <out.json> --s136 <scores...> --warp4 <scores...> --hybrid <hybrid jsons...>
Window unit; seeds averaged within window; window-cluster bootstrap 95% CI (10k, rng 0); verdict ±0.2 dB rule.
"""
import json, sys
from pathlib import Path
import numpy as np

b2 = {(r['scene'], r['window_start']): r['b2_psnr'] for r in json.loads(Path(sys.argv[1]).read_text())['rows']}
OUT = Path(sys.argv[2]); groups, cur = {'--s136': [], '--warp4': [], '--hybrid': []}, None
for a in sys.argv[3:]:
    if a in groups: cur = a
    else: groups[cur].append(Path(a))


def load_runs(paths):
    r = {}
    for p in paths: r.update(json.loads(p.read_text())['runs'])
    return r


def per_window(runs, match):
    d = {}
    for r in runs.values():
        if match(r['ctx_key'], r['window_start']):
            d.setdefault((r['scene'], r['window_start']), []).append(r['aggregate']['psnr_db'])
    return {k: float(np.mean(v)) for k, v in d.items()}, {k: len(v) for k, v in d.items()}


s136, w4 = load_runs(groups['--s136']), load_runs(groups['--warp4'])
static = lambda conv: (lambda key, w: key.endswith(f'__{conv}__' + '-'.join(str(w + o) for o in (0, 15, 30, 45))))
arms = {'b2_kps': b2}
arms['static_gl'], n_sg = per_window(s136, static('gl'))
arms['static_native'], n_sn = per_window(s136, static('native'))
arms['warp4_fill_gl'], n_wf = per_window(w4, lambda k, w: k.endswith('__gl__warp4fill'))
arms['warp4_hole_gl'], n_wh = per_window(w4, lambda k, w: k.endswith('__gl__warp4hole'))
hyb = [r for p in groups['--hybrid'] for r in json.loads(p.read_text())['rows']]
for conv in ('gl', 'native'):
    d = {}
    for r in hyb:
        if r['ctx_key'].endswith(f"__{conv}__" + '-'.join(str(r['window_start'] + o) for o in (0, 15, 30, 45))):
            d.setdefault((r['scene'], r['window_start']), []).append(r)
    arms[f'hybrid_static_{conv}'] = {k: float(np.mean([x['psnr_hybrid'] for x in v])) for k, v in d.items()}
    arms[f'ssim_static_{conv}'] = {k: float(np.mean([x['ssim_vmem'] for x in v])) for k, v in d.items()}
    arms[f'ssim_hybrid_{conv}'] = {k: float(np.mean([x['ssim_hybrid'] for x in v])) for k, v in d.items()}
    arms['ssim_warp'] = {k: float(np.mean([x['ssim_warp'] for x in v])) for k, v in d.items()}


def contrast(a, b):
    ks = sorted(set(arms.get(a, {})) & set(arms.get(b, {})))
    if not ks: return None
    v = np.array([arms[a][k] - arms[b][k] for k in ks]); rng = np.random.default_rng(0)
    boot = [rng.choice(v, len(v)).mean() for _ in range(10000)]; lo, hi = np.percentile(boot, [2.5, 97.5]); m = float(v.mean())
    thr = 0.2 if not a.startswith('ssim') else 0.01
    verdict = ('IMPROVES' if m >= thr and lo > 0 else 'WORSENS' if m <= -thr and hi < 0 else
               'NO_MATERIAL_CHANGE' if abs(m) < thr and lo <= 0 <= hi else 'INCONCLUSIVE')
    return {'a': a, 'b': b, 'n_windows': len(v), 'mean': m, 'ci95': [float(lo), float(hi)], 'a_wins': int((v > 0).sum()), 'verdict': verdict}


spec = [('warp4_fill_gl', 'b2_kps'), ('warp4_hole_gl', 'b2_kps'), ('warp4_fill_gl', 'static_gl'), ('warp4_hole_gl', 'static_gl'),
        ('hybrid_static_gl', 'b2_kps'), ('hybrid_static_native', 'b2_kps'), ('b2_kps', 'static_gl'), ('b2_kps', 'static_native'),
        ('ssim_warp', 'ssim_static_gl'), ('ssim_warp', 'ssim_static_native'), ('ssim_hybrid_gl', 'ssim_warp')]
res = {'means': {a: float(np.mean(list(v.values()))) for a, v in arms.items() if v},
       'seeds_per_window': {'static_gl': sorted(set(n_sg.values())), 'static_native': sorted(set(n_sn.values())),
                            'warp4_fill_gl': sorted(set(n_wf.values())), 'warp4_hole_gl': sorted(set(n_wh.values()))},
       'contrasts': [c for c in (contrast(a, b) for a, b in spec) if c]}
OUT.write_text(json.dumps(res, indent=1) + '\n')
for a, v in res['means'].items(): print(f'{a:22s} {v:7.3f}')
print(res['seeds_per_window'])
for c in res['contrasts']:
    print(f"{c['a']:>20s} - {c['b']:<18s} {c['mean']:+.3f} CI[{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['a_wins']}/{c['n_windows']} {c['verdict']}")
