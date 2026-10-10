#!/usr/bin/env python3
"""S141 analysis (pre-registered in PROTOCOL.md). Window mean over the RTX 3090 seeds 3-6; window-cluster bootstrap
95% CI (10k, rng 0); verdict as S140 (+-0.2 dB PSNR, +-0.01 SSIM).
usage: analyze_s141.py <scores_A.json> <scores_B.json> <S139_ALL_SSIM_tacc.json> <base_regions.json> <POSE_ARMS.json> <out.json>
scores_A/B: score_s140.py output on plan_eval_A/B (B also gives the B2 warp scores); base_regions: score_s140.py on the base
mem_vmem outputs (plan_base_regions.json)."""
import json, sys
from pathlib import Path
import numpy as np
SA, SB, BASE, BREG, POSE, OUT = [Path(a) for a in sys.argv[1:7]]
A = json.loads(SA.read_text()); B = json.loads(SB.read_text()); base = json.loads(BASE.read_text())['runs']
breg = json.loads(BREG.read_text())['runs']; pose = {r['window_id']: r for r in json.loads(POSE.read_text())['rows']}
SEEDS = (3, 4, 5, 6)


def wm(runs, pick, metric):
    d = {}
    for r in runs.values():
        if pick(r) and r['seed'] in SEEDS: d.setdefault(r['window_id'], {})[r['seed']] = r[metric]
    assert all(len(v) == 4 for v in d.values()), 'missing seeds'
    return {w: float(np.mean(list(v.values()))) for w, v in d.items()}


def summ(a, b, thr, wins=None):
    ks = sorted(set(a) & set(b) & (wins or set(a))); v = np.array([a[k] - b[k] for k in ks]); rng = np.random.default_rng(0)
    bt = [rng.choice(v, len(v)).mean() for _ in range(10000)]; lo, hi = (float(x) for x in np.percentile(bt, [2.5, 97.5]))
    m = float(v.mean())
    verdict = ('IMPROVES' if m >= thr and lo > 0 else 'WORSENS' if m <= -thr and hi < 0 else
               'NO_MATERIAL_CHANGE' if abs(m) < thr and lo <= 0 <= hi else 'INCONCLUSIVE')
    return {'n': len(v), 'mean': m, 'ci95': [lo, hi], 'wins': int((v > 0).sum()), 'verdict': verdict}


hf = {w for w in pose if pose[w]['history_favourable']}
res = {'means': {}, 'contrasts': {}}
for metric, wk, thr in (('psnr_db', 'psnr', 0.2), ('ssim', 'ssim', 0.01)):
    arms = {'A_static': wm(A['runs'], lambda r: r['mode'] == 'A_static', metric),
            'A_mem': wm(A['runs'], lambda r: r['mode'] == 'A_mem', metric),
            'B_mem': wm(B['runs'], lambda r: r['mode'] == 'B_mem', metric),
            'base_static': wm(base, lambda r: 'static_recent' in r['arms'], metric),
            'base_mem': wm(base, lambda r: 'mem_vmem' in r['arms'], metric),
            'B2_warp': {w: v[wk] for w, v in B['warps'].items()}}
    assert all(len(v) == 24 for v in arms.values()), {k: len(v) for k, v in arms.items()}
    res['means'][metric] = {k: float(np.mean(list(v.values()))) for k, v in arms.items()}
    con = {}
    for name, a, b in (('PRIMARY_A: A_mem - base_mem', 'A_mem', 'base_mem'), ('A_mem - A_static', 'A_mem', 'A_static'),
                       ('A_static - base_static', 'A_static', 'base_static'),
                       ('PRIMARY_B: B_mem - B2_warp', 'B_mem', 'B2_warp'), ('B_mem - base_mem', 'B_mem', 'base_mem'),
                       ('B_mem - A_mem (exploratory)', 'B_mem', 'A_mem'), ('base_mem - base_static (S139 replica, seeds 3-6)', 'base_mem', 'base_static')):
        c = summ(arms[a], arms[b], thr); c['history_favourable'] = summ(arms[a], arms[b], thr, hf)
        c['per_pair'] = {p: float(np.mean([arms[a][w] - arms[b][w] for w in arms[a] if pose[w]['pair'] == p])) for p in sorted({pose[w]['pair'] for w in pose})}
        con[name] = c
    res['contrasts'][metric] = con
# region split (PSNR) for B and base vs the mem_vmem warp coverage
reg = {}
for lab, runs, pick in (('B_mem', B['runs'], lambda r: r['mode'] == 'B_mem'), ('base_mem', breg, lambda r: True)):
    for k in ('psnr_covered', 'psnr_holes', 'warp_psnr_covered', 'warp_psnr_holes', 'hole_fraction'):
        reg.setdefault(lab, {})[k] = wm(runs, pick, k)
res['regions'] = {
    'B_minus_warp_covered': summ(reg['B_mem']['psnr_covered'], reg['B_mem']['warp_psnr_covered'], 0.2),
    'B_minus_warp_holes': summ(reg['B_mem']['psnr_holes'], reg['B_mem']['warp_psnr_holes'], 0.2),
    'B_minus_base_covered': summ(reg['B_mem']['psnr_covered'], reg['base_mem']['psnr_covered'], 0.2),
    'B_minus_base_holes': summ(reg['B_mem']['psnr_holes'], reg['base_mem']['psnr_holes'], 0.2),
    'base_minus_warp_covered': summ(reg['base_mem']['psnr_covered'], reg['base_mem']['warp_psnr_covered'], 0.2),
    'base_minus_warp_holes': summ(reg['base_mem']['psnr_holes'], reg['base_mem']['warp_psnr_holes'], 0.2),
    'hole_fraction': float(np.mean(list(reg['B_mem']['hole_fraction'].values())))}
OUT.write_text(json.dumps(res, indent=1) + '\n')
for metric in ('psnr_db', 'ssim'):
    print(metric, {k: round(v, 3) for k, v in res['means'][metric].items()})
    for name, c in res['contrasts'][metric].items():
        print(f"  {name:48s} {c['mean']:+.3f} [{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['wins']}/{c['n']} {c['verdict']}"
              f" | HF {c['history_favourable']['mean']:+.3f}")
for k, c in res['regions'].items():
    print(f'  {k:28s}', c if isinstance(c, float) else f"{c['mean']:+.3f} [{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['wins']}/{c['n']}")
