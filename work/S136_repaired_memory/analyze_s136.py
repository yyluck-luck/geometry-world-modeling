#!/usr/bin/env python3
"""S136 analysis (CPU). usage: analyze_s136.py <plan.json> <out.json> <scores.json> [<scores.json> ...]

Contrasts (PROTOCOL.md): Q1 static_gl - static_native (16 windows, C9 rule + S134 rule); Q2 mem_rep_gl - static_gl;
Q3 mem_rep_gl - mem_orig_gl; Q4 mem_orig_native - static_native. Unit: window mean over all seeds present for both arms;
95% CI by window-cluster bootstrap (10k, rng 0). Per-site breakdown by seed block.
"""
import json, sys
from pathlib import Path
import numpy as np

plan = json.loads(Path(sys.argv[1]).read_text()); OUT = Path(sys.argv[2])
runs = {}
for p in sys.argv[3:]:
    runs.update(json.loads(Path(p).read_text())['runs'])
by_key = {}
for r in runs.values():
    by_key.setdefault(r['ctx_key'], {})[r['seed']] = r['aggregate']['psnr_db']
psnr = {}  # (scene, start, arm) -> {seed: dB}
for c in plan['contexts']:
    for arm in c['arms']:
        psnr[(c['scene'], c['window_start'], arm)] = by_key.get(c['ctx_key'], {})
SITES = {'superpod_h800': {42, 7, 1, 2}, 'tacc_rtx3090': {3, 4, 5, 6}}


def contrast(a, b, seeds=None):
    wins = sorted({(s, w) for s, w, x in psnr if x == a} & {(s, w) for s, w, x in psnr if x == b})
    wm, lab, nseed = [], [], []
    for s, w in wins:
        A, B = psnr[(s, w, a)], psnr[(s, w, b)]
        ss = sorted(set(A) & set(B) & (seeds if seeds else set(A)))
        if not ss: continue
        wm.append(float(np.mean([A[x] - B[x] for x in ss]))); lab.append(f'{s}_w{w}'); nseed.append(len(ss))
    if not wm: return None
    v = np.array(wm); rng = np.random.default_rng(0)
    boot = [rng.choice(v, len(v), replace=True).mean() for _ in range(10000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    m = float(v.mean())
    verdict = ('IMPROVES' if m >= 0.2 and lo > 0 else 'WORSENS' if m <= -0.2 and hi < 0 else
               'NO_MATERIAL_CHANGE' if abs(m) < 0.2 and lo <= 0 <= hi else 'INCONCLUSIVE')
    return {'a': a, 'b': b, 'n_windows': len(v), 'seeds_per_window': sorted(set(nseed)), 'mean_db': m,
            'ci95': [float(lo), float(hi)], 'windows_positive': int((v > 0).sum()), 'verdict': verdict,
            'window_means_db': dict(zip(lab, [round(x, 4) for x in wm]))}


spec = {'Q1_static_gl_vs_native': ('static_gl', 'static_native'),
        'Q2_mem_rep_gl_vs_static_gl': ('mem_rep_gl', 'static_gl'),
        'Q3_mem_rep_gl_vs_mem_orig_gl': ('mem_rep_gl', 'mem_orig_gl'),
        'Q4_mem_orig_native_vs_static_native': ('mem_orig_native', 'static_native'),
        'X_mem_orig_gl_vs_static_gl': ('mem_orig_gl', 'static_gl'),
        'S134gl_mem_fix_gl_vs_mem_orig_gl': ('mem_fix_gl', 'mem_orig_gl'),      # S134 Amendment 1 (gl gate passed)
        'S134gl_mem_fix_gl_vs_static_gl': ('mem_fix_gl', 'static_gl'),
        'X_mem_rep_gl_vs_mem_fix_gl': ('mem_rep_gl', 'mem_fix_gl')}
res = {'contrasts': {}}
for name, (a, b) in spec.items():
    c = contrast(a, b)
    if c:
        c['per_site'] = {site: contrast(a, b, ss) for site, ss in SITES.items()}
        c['per_site'] = {k: (None if v is None else {'mean_db': v['mean_db'], 'ci95': v['ci95'],
                                                    'windows_positive': v['windows_positive'], 'n_windows': v['n_windows']})
                         for k, v in c['per_site'].items()}
    res['contrasts'][name] = c
q1 = res['contrasts'].get('Q1_static_gl_vs_native')
if q1:
    q1['C9_rule'] = 'MISMATCH_CONFIRMED' if q1['mean_db'] >= 1.0 and q1['windows_positive'] >= 12 else 'NOT_CONFIRMED'
res['arm_means_db'] = {arm: float(np.mean([v for (s, w, x), d in psnr.items() if x == arm for v in d.values()]))
                       for arm in sorted({x for _, _, x in psnr}) if any(psnr[k] for k in psnr if k[2] == arm)}
OUT.write_text(json.dumps(res, indent=1) + '\n')
for name, c in res['contrasts'].items():
    if c: print(f"{name:38s} {c['mean_db']:+.3f} dB CI[{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] pos {c['windows_positive']}/{c['n_windows']} "
                f"seeds {c['seeds_per_window']} {c['verdict']}" + (f" C9:{c.get('C9_rule')}" if 'C9_rule' in c else ''))
