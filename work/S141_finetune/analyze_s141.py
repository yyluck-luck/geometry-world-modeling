#!/usr/bin/env python3
"""S141 analysis (pre-registered in PROTOCOL.md; strict checks and the Amendment-1 exploratory/secondary blocks added
after codex R254, before any evaluation output existed). Window mean over the RTX 3090 seeds 3-6; window-cluster
bootstrap 95% CI (10k, rng 0); verdict as S140 (+-0.2 dB PSNR, +-0.01 SSIM). NO_MATERIAL_CHANGE is the registered
label, not an equivalence claim.
usage: analyze_s141.py <scores_A> <scores_B> <S139_ALL_SSIM_tacc.json> <base_regions> <POSE_ARMS.json> <out.json>
         [--bstatic <scores_Bstatic> <base_static_regions>] [--rgbd <scores_rgbd_A> <scores_rgbd_B> <scores_rgbd_base>]
All score files are score_s140.py outputs (scores_B / scores_Bstatic also carry the B2 warp scores)."""
import json, math, sys
from pathlib import Path
import numpy as np
a = sys.argv[1:]; opt = {}
for flag, n in (('--bstatic', 2), ('--rgbd', 3)):
    if flag in a:
        i = a.index(flag); opt[flag] = [Path(x) for x in a[i + 1:i + 1 + n]]; del a[i:i + 1 + n]
SA, SB, BASE, BREG, POSE, OUT = [Path(x) for x in a[:6]]
J = lambda p: json.loads(p.read_text())
A = J(SA); B = J(SB); base = J(BASE)['runs']; breg = J(BREG)['runs']; pose = {r['window_id']: r for r in J(POSE)['rows']}
SEEDS = (3, 4, 5, 6)


def wm(runs, pick, metric, n_windows):
    d = {}
    for r in runs.values():
        if pick(r) and r['seed'] in SEEDS:
            v = r[metric]; assert v is not None and math.isfinite(v), (r.get('ctx_key'), metric, v)
            assert r['seed'] not in d.setdefault(r['window_id'], {}), ('duplicate cell', r['window_id'], r['seed'])
            d[r['window_id']][r['seed']] = v
    assert len(d) == n_windows and all(sorted(v) == list(SEEDS) for v in d.values()), ('incomplete cells', len(d))
    return {w: float(np.mean(list(v.values()))) for w, v in d.items()}


def summ(a, b, thr, wins=None):
    assert set(a) == set(b), 'unpaired windows'
    ks = sorted(wins & set(a) if wins else a); v = np.array([a[k] - b[k] for k in ks]); rng = np.random.default_rng(0)
    bt = [rng.choice(v, len(v)).mean() for _ in range(10000)]; lo, hi = (float(x) for x in np.percentile(bt, [2.5, 97.5]))
    m = float(v.mean())
    verdict = ('IMPROVES' if m >= thr and lo > 0 else 'WORSENS' if m <= -thr and hi < 0 else
               'NO_MATERIAL_CHANGE' if abs(m) < thr and lo <= 0 <= hi else 'INCONCLUSIVE')
    return {'n': len(v), 'mean': m, 'ci95': [lo, hi], 'wins': int((v > 0).sum()), 'verdict': verdict}


def pairs(arms, x, y):
    return {p: float(np.mean([arms[x][w] - arms[y][w] for w in arms[x] if pose[w]['pair'] == p])) for p in sorted({pose[w]['pair'] for w in pose})}


hf = {w for w in pose if pose[w]['history_favourable']}
res = {'means': {}, 'contrasts': {}, 'exploratory_Bstatic': {}, 'rgbd_secondary': {}}
BS = J(opt['--bstatic'][0]) if '--bstatic' in opt else None
for metric, wk, thr in (('psnr_db', 'psnr', 0.2), ('ssim', 'ssim', 0.01)):
    arms = {'A_static': wm(A['runs'], lambda r: r['mode'] == 'A_static', metric, 24),
            'A_mem': wm(A['runs'], lambda r: r['mode'] == 'A_mem', metric, 24),
            'B_mem': wm(B['runs'], lambda r: r['mode'] == 'B_mem', metric, 24),
            'base_static': wm(base, lambda r: 'static_recent' in r['arms'], metric, 24),
            'base_mem': wm(base, lambda r: 'mem_vmem' in r['arms'], metric, 24),
            'B2_warp_mem': {w: v[wk] for w, v in B['warps'].items()}}
    if BS:
        arms['B_static'] = wm(BS['runs'], lambda r: r['mode'] == 'B_static', metric, 24)
        arms['B2_warp_static'] = {w: v[wk] for w, v in BS['warps'].items()}
    assert all(len(v) == 24 for v in arms.values()), {k: len(v) for k, v in arms.items()}
    res['means'][metric] = {k: float(np.mean(list(v.values()))) for k, v in arms.items()}
    con = {}
    for name, x, y in (('PRIMARY_A: A_mem - base_mem', 'A_mem', 'base_mem'), ('A_mem - A_static', 'A_mem', 'A_static'),
                       ('A_static - base_static', 'A_static', 'base_static'),
                       ('PRIMARY_B: B_mem - B2_warp', 'B_mem', 'B2_warp_mem'), ('B_mem - base_mem', 'B_mem', 'base_mem'),
                       ('B_mem - A_mem (exploratory)', 'B_mem', 'A_mem'), ('base_mem - base_static (S139 replica, seeds 3-6)', 'base_mem', 'base_static')):
        c = summ(arms[x], arms[y], thr); c['history_favourable'] = summ(arms[x], arms[y], thr, hf); c['per_pair'] = pairs(arms, x, y)
        con[name] = c
    res['contrasts'][metric] = con
    if BS:   # Amendment 1, exploratory
        ex = {}
        for name, x, y in (('B_static - B2_warp_static', 'B_static', 'B2_warp_static'), ('B_mem - B_static', 'B_mem', 'B_static'),
                           ('B_static - A_static', 'B_static', 'A_static'), ('B2_warp_mem - B2_warp_static', 'B2_warp_mem', 'B2_warp_static')):
            c = summ(arms[x], arms[y], thr); c['per_pair'] = pairs(arms, x, y); ex[name] = c
        dd = {w: (arms['B_mem'][w] - arms['B_static'][w]) - (arms['A_mem'][w] - arms['A_static'][w]) for w in arms['A_mem']}
        c = summ(dd, {w: 0.0 for w in dd}, thr); c['history_favourable'] = summ(dd, {w: 0.0 for w in dd}, thr, hf)
        ex['(B_mem - B_static) - (A_mem - A_static)'] = c
        res['exploratory_Bstatic'][metric] = ex
# region split (PSNR) vs the warp coverage of each arm's own contexts
reg = {}
src = [('B_mem', B['runs'], lambda r: r['mode'] == 'B_mem'), ('base_mem', breg, lambda r: True)]
if BS: src += [('B_static', BS['runs'], lambda r: r['mode'] == 'B_static'), ('base_static', J(opt['--bstatic'][1])['runs'], lambda r: True)]
for lab, runs, pick in src:
    for k in ('psnr_covered', 'psnr_holes', 'warp_psnr_covered', 'warp_psnr_holes', 'hole_fraction'):
        reg.setdefault(lab, {})[k] = wm(runs, pick, k, 24)
res['regions'] = {'note': 'covered / holes = covered / uncovered by the warp of the same contexts (not certified disocclusion)'}
for lab, other in (('B_mem', 'base_mem'), ('B_static', 'base_static')):
    if lab not in reg: continue
    res['regions'][lab] = {f'{lab}_minus_warp_covered': summ(reg[lab]['psnr_covered'], reg[lab]['warp_psnr_covered'], 0.2),
                           f'{lab}_minus_warp_uncovered': summ(reg[lab]['psnr_holes'], reg[lab]['warp_psnr_holes'], 0.2),
                           f'{lab}_minus_{other}_covered': summ(reg[lab]['psnr_covered'], reg[other]['psnr_covered'], 0.2),
                           f'{lab}_minus_{other}_uncovered': summ(reg[lab]['psnr_holes'], reg[other]['psnr_holes'], 0.2),
                           f'{other}_minus_warp_covered': summ(reg[other]['psnr_covered'], reg[other]['warp_psnr_covered'], 0.2),
                           f'{other}_minus_warp_uncovered': summ(reg[other]['psnr_holes'], reg[other]['warp_psnr_holes'], 0.2),
                           'uncovered_fraction': float(np.mean(list(reg[lab]['hole_fraction'].values())))}
# RGB-D Scenes secondary panel (exposed; static contexts; base = S136 RTX 3090 static_gl outputs, seeds 3-6)
if '--rgbd' in opt:
    RA, RB, RBASE = (J(p) for p in opt['--rgbd'])
    for metric, wk, thr in (('psnr_db', 'psnr', 0.2), ('ssim', 'ssim', 0.01)):
        ar = {'A_static': wm(RA['runs'], lambda r: r['mode'] == 'A_static', metric, 16),
              'B_static': wm(RB['runs'], lambda r: r['mode'] == 'B_static', metric, 16),
              'base_static': wm(RBASE['runs'], lambda r: r['mode'] == 'base_static', metric, 16),
              'B2_warp': {w: v[wk] for w, v in RB['warps'].items()}}
        res['rgbd_secondary'][metric] = {'means': {k: float(np.mean(list(v.values()))) for k, v in ar.items()},
                                         **{n: summ(ar[x], ar[y], thr) for n, x, y in (('A_static - base_static', 'A_static', 'base_static'),
                                                                                    ('B_static - B2_warp', 'B_static', 'B2_warp'),
                                                                                    ('B_static - base_static', 'B_static', 'base_static'),
                                                                                    ('B_static - A_static', 'B_static', 'A_static'))}}
OUT.write_text(json.dumps(res, indent=1) + '\n')
fmt = lambda c: f"{c['mean']:+.3f} [{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['wins']}/{c['n']} {c['verdict']}"
for metric in ('psnr_db', 'ssim'):
    print(metric, {k: round(v, 3) for k, v in res['means'][metric].items()})
    for name, c in res['contrasts'][metric].items(): print(f'  {name:50s} {fmt(c)} | HF {c["history_favourable"]["mean"]:+.3f}')
    for name, c in res['exploratory_Bstatic'].get(metric, {}).items(): print(f'  [expl] {name:43s} {fmt(c)}')
    if metric in res['rgbd_secondary']:
        r = res['rgbd_secondary'][metric]; print('  [rgbd] means', {k: round(v, 3) for k, v in r['means'].items()})
        for name, c in r.items():
            if name != 'means': print(f'  [rgbd] {name:43s} {fmt(c)}')
for lab, d in res['regions'].items():
    if lab == 'note': continue
    for k, c in d.items(): print(f'  [region] {k:36s}', c if isinstance(c, float) else fmt(c))
