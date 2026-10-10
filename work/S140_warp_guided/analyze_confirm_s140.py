#!/usr/bin/env python3
"""S140 stage-2 analysis. usage: analyze_confirm_s140.py <out.json> --wgs <S140 confirm scores...> --vmem <S140-scored S139 mem_vmem...> --pose <POSE_ARMS.json>
Primary: WGS - B2(mem_vmem) [PSNR]; secondary: WGS - VMem(mem_vmem); SSIM versions; per pair; history-favourable."""
import json, sys
from pathlib import Path
import numpy as np
OUT = Path(sys.argv[1]); g = {'--wgs': [], '--vmem': [], '--pose': []}; cur = None
for a in sys.argv[2:]:
    if a in g: cur = a
    else: g[cur].append(Path(a))
def load(paths):
    runs, warps = {}, {}
    for p in paths:
        d = json.loads(p.read_text()); runs.update(d['runs']); warps.update(d['warps'])
    return runs, warps
W, warps = load(g['--wgs']); V, _ = load(g['--vmem']); pose = {r['window_id']: r for r in json.loads(g['--pose'][0].read_text())['rows']}
def per_window(runs, metric):
    d = {}
    for r in runs.values(): d.setdefault(r['window_id'], {})[r['seed']] = r[metric]
    return d
def summ(a, b, wins=None):
    ks = sorted(set(a) & set(b) & (wins or set(a))); v = np.array([a[k] - b[k] for k in ks]); rng = np.random.default_rng(0)
    bt = [rng.choice(v, len(v)).mean() for _ in range(10000)]; lo, hi = np.percentile(bt, [2.5, 97.5]); return {'n': len(v), 'mean': float(v.mean()), 'ci95': [float(lo), float(hi)], 'wins': int((v > 0).sum())}
res = {}
for metric, wk, thr in (('psnr_db', 'psnr', 0.2), ('ssim', 'ssim', 0.01)):
    wg = per_window(W, metric); vm = per_window(V, metric)
    seeds_ok = all(len(x) == 8 for x in wg.values()) and all(len(x) == 8 for x in vm.values())
    wgm = {w: float(np.mean(list(x.values()))) for w, x in wg.items()}
    vmm = {w: float(np.mean([x[s] for s in wg[w]])) for w, x in vm.items() if w in wg}
    b2 = {w: warps[w][wk] for w in warps}
    hf = {w for w in pose if pose[w]['history_favourable']}
    out = {'seeds_complete_8': seeds_ok, 'means': {'WGS': float(np.mean(list(wgm.values()))), 'B2': float(np.mean(list(b2.values()))), 'VMem': float(np.mean(list(vmm.values())))}}
    for name, (a, b) in {'WGS_minus_B2': (wgm, b2), 'WGS_minus_VMem': (wgm, vmm), 'B2_minus_VMem': (b2, vmm)}.items():
        c = summ(a, b); c['history_favourable'] = summ(a, b, hf); m, (lo, hi) = c['mean'], c['ci95']
        c['verdict'] = 'IMPROVES' if m >= thr and lo > 0 else 'WORSENS' if m <= -thr and hi < 0 else 'NO_MATERIAL_CHANGE' if abs(m) < thr and lo <= 0 <= hi else 'INCONCLUSIVE'
        c['per_pair'] = {p: float(np.mean([a[w] - b[w] for w in a if w in b and pose[w]['pair'] == p])) for p in sorted({pose[w]['pair'] for w in a})}
        out[name] = c
    res[metric] = out
OUT.write_text(json.dumps(res, indent=1) + '\n')
for metric, out in res.items():
    print(metric, {k: round(v, 3) for k, v in out['means'].items()}, 'seeds8', out['seeds_complete_8'])
    for name in ('WGS_minus_B2', 'WGS_minus_VMem', 'B2_minus_VMem'):
        c = out[name]; print(f"  {name:15s} {c['mean']:+.3f} [{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['wins']}/{c['n']} {c['verdict']} | HF {c['history_favourable']['mean']:+.3f} | pairs {({k: round(v, 2) for k, v in c['per_pair'].items()})}")
