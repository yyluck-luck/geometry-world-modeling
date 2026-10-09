#!/usr/bin/env python3
"""S134 analysis (CPU). usage: analyze_s134.py <plan.json> <S134_SCORES.json> <orig_retrieval_receipt.json> <out.json>

Affected windows (fixed in PROTOCOL.md): orig stage-1 construct had at least one PnP failure on gpu13.
Primary: mem_on_fix - mem_on_orig over affected windows. Secondary: memory - static (orig and fixed, NMS on/off),
all windows and affected windows. Uncertainty: window-cluster bootstrap (10k, seed 0) of the window means
(each window mean = mean over seeds); seed-level spread reported separately.
"""
import json, sys
from pathlib import Path
import numpy as np

PLAN, SCORES, ORIG, OUT = map(Path, sys.argv[1:5])
plan = json.loads(PLAN.read_text()); runs = json.loads(SCORES.read_text())['runs']
orig = {(r['scene'], int(r['window_start'])): r for r in json.loads(ORIG.read_text())['records']}
psnr = {}  # (scene, start, arm, seed) -> dB
for c in plan['contexts']:
    for arm in c['arms']:
        for k, r in runs.items():
            if r['ctx_key'] == c['ctx_key']:
                psnr[(c['scene'], c['window_start'], arm, r['seed'])] = r['aggregate']['psnr_db']
windows = sorted({(s, w) for s, w, _, _ in psnr})
seeds = sorted({sd for *_, sd in psnr})


def affected(key):
    p = orig[key].get('construct_probes') or []
    return bool(p) and p[0].get('pnp_ok', 0) < p[0].get('pnp_calls', 0)


AFF = [w for w in windows if affected(w)]


def contrast(a, b, wins):
    wm, labels, per_seed = [], [], {sd: [] for sd in seeds}
    for w in wins:
        d = [psnr[(*w, a, sd)] - psnr[(*w, b, sd)] for sd in seeds if (*w, a, sd) in psnr and (*w, b, sd) in psnr]
        if len(d) == len(seeds):
            wm.append(float(np.mean(d))); labels.append(f'{w[0]}_w{w[1]}')
            for sd, x in zip(seeds, d): per_seed[sd].append(x)
    if not wm: return None
    rng = np.random.default_rng(0); wm_a = np.array(wm)
    boot = [rng.choice(wm_a, len(wm_a), replace=True).mean() for _ in range(10000)]
    return {'a': a, 'b': b, 'n_windows': len(wm), 'n_seeds': len(seeds), 'mean_db': float(wm_a.mean()),
            'ci95_window_bootstrap': [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            'windows_positive': int((wm_a > 0).sum()), 'windows_zero': int((wm_a == 0).sum()),
            'per_seed_mean_db': {str(sd): float(np.mean(v)) for sd, v in per_seed.items() if v},
            'window_means_db': dict(zip(labels, [round(x, 4) for x in wm]))}


def verdict(c):
    if c is None: return 'NO_DATA'
    lo, hi = c['ci95_window_bootstrap']
    if c['mean_db'] >= 0.2 and lo > 0: return 'IMPROVES'
    if c['mean_db'] <= -0.2 and hi < 0: return 'WORSENS'
    if abs(c['mean_db']) < 0.2 and lo <= 0 <= hi: return 'NO_MATERIAL_CHANGE'
    return 'INCONCLUSIVE'


res = {'affected_windows': [f'{s}_w{w}' for s, w in AFF], 'seeds': seeds, 'contrasts': {}}
spec = {'PRIMARY_mem_on_fix_vs_orig__affected': ('mem_on_fix', 'mem_on_orig', AFF),
        'mem_off_fix_vs_orig__affected': ('mem_off_fix', 'mem_off_orig', AFF)}
for arm in ('mem_on_orig', 'mem_on_fix', 'mem_off_orig', 'mem_off_fix'):
    spec[f'{arm}_vs_static__all'] = (arm, 'static', windows)
    spec[f'{arm}_vs_static__affected'] = (arm, 'static', AFF)
for arm in ('mem_on_orig_gl', 'mem_on_fix_gl'):  # Amendment 1, only present if the gl gate passed
    spec[f'{arm}_vs_static_gl__all'] = (arm, 'static_gl', windows)
    spec[f'{arm}_vs_static_gl__affected'] = (arm, 'static_gl', AFF)
spec['mem_on_fix_gl_vs_orig_gl__affected'] = ('mem_on_fix_gl', 'mem_on_orig_gl', AFF)
SITES = {'superpod_h800': [42, 7, 1, 2], 'tacc_rtx3090': [3, 4, 5, 6]}
all_seeds = list(seeds)
for name, (a, b, wins) in spec.items():
    seeds = all_seeds
    c = contrast(a, b, wins); res['contrasts'][name] = c
    if c:
        c['verdict'] = verdict(c); c['per_site'] = {}
        for site, ss in SITES.items():
            seeds = [x for x in all_seeds if x in ss]
            cs = contrast(a, b, wins) if seeds else None
            if cs: c['per_site'][site] = {'mean_db': cs['mean_db'], 'ci95_window_bootstrap': cs['ci95_window_bootstrap'], 'n_seeds': len(seeds)}
seeds = all_seeds
res['arm_means_db'] = {arm: float(np.mean([v for (s, w, a, sd), v in psnr.items() if a == arm]))
                       for arm in sorted({k[2] for k in psnr})}
OUT.write_text(json.dumps(res, indent=1) + '\n')
for name, c in res['contrasts'].items():
    if c: print(f"{name:42s} {c['mean_db']:+.3f} dB  CI[{c['ci95_window_bootstrap'][0]:+.3f},{c['ci95_window_bootstrap'][1]:+.3f}]  "
                f"pos {c['windows_positive']}/{c['n_windows']}  {c['verdict']}")
