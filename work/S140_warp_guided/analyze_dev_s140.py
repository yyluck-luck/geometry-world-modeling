#!/usr/bin/env python3
"""S140 stage-1 analysis + pre-registered variant selection.
usage: analyze_dev_s140.py <S140_SCORES_dev.json> <S136 superpod scores> <out.json>
Selection: highest mean PSNR over the 32 window-seed cells; ties (< 0.05 dB) -> higher SSIM. References: B2 warp
(deterministic, scored in the same scorer) and VMem static_gl (S136, seeds 42/7)."""
import json, sys
from pathlib import Path
import numpy as np
S = json.loads(Path(sys.argv[1]).read_text()); S136 = json.loads(Path(sys.argv[2]).read_text())['runs']; OUT = Path(sys.argv[3])
warps = S['warps']; runs = S['runs']
static = {}
for r in S136.values():
    w = r['window_start']; key = f"{r['scene']}__w{w:04d}__gl__" + '-'.join(str(w + o) for o in (0, 15, 30, 45))
    if r['ctx_key'] == key and r['seed'] in (42, 7): static.setdefault(f"{r['scene']}__w{w:04d}", {})[r['seed']] = r['aggregate']['psnr_db']
var = {}
for r in runs.values():
    if r['mode'] in ('ref', 'none'): continue
    var.setdefault(f"{r['mode']}_{r['strength']:.1f}", {})[(r['window_id'], r['seed'])] = (r['psnr_db'], r['ssim'])
def boot(d):
    d = np.array(d); rng = np.random.default_rng(0); b = [rng.choice(d, len(d)).mean() for _ in range(10000)]
    return [float(x) for x in np.percentile(b, [2.5, 97.5])]
res = {'variants': {}}
for v, cells in sorted(var.items()):
    wins = sorted({w for w, _ in cells})
    wm = {w: np.mean([cells[(w, s)][0] for s in (42, 7) if (w, s) in cells]) for w in wins}
    d_b2 = [wm[w] - warps[w]['psnr'] for w in wins]; d_st = [wm[w] - np.mean(list(static[w].values())) for w in wins if w in static]
    res['variants'][v] = {'n_cells': len(cells), 'mean_psnr': float(np.mean([x[0] for x in cells.values()])),
                          'mean_ssim': float(np.mean([x[1] for x in cells.values()])),
                          'minus_B2_db': float(np.mean(d_b2)), 'minus_B2_ci': boot(d_b2), 'minus_B2_wins': int((np.array(d_b2) > 0).sum()),
                          'minus_static_db': float(np.mean(d_st)), 'minus_static_ci': boot(d_st)}
res['B2_mean_psnr'] = float(np.mean([warps[w]['psnr'] for w in warps])); res['B2_mean_ssim'] = float(np.mean([warps[w]['ssim'] for w in warps]))
res['static_gl_mean_psnr_s42_s7'] = float(np.mean([v for d in static.values() for v in d.values()]))
best = sorted(res['variants'].items(), key=lambda kv: -kv[1]['mean_psnr'])
sel = best[0][0]
if len(best) > 1 and best[0][1]['mean_psnr'] - best[1][1]['mean_psnr'] < 0.05 and best[1][1]['mean_ssim'] > best[0][1]['mean_ssim']:
    sel = best[1][0]
res['selected'] = sel
fid = {r['ctx_key']: r['psnr_db'] for r in runs.values() if r['mode'] in ('ref', 'none')}
res['fidelity_psnr'] = fid
OUT.write_text(json.dumps(res, indent=1) + '\n')
print(f"B2 {res['B2_mean_psnr']:.3f} dB / SSIM {res['B2_mean_ssim']:.3f}; VMem static_gl {res['static_gl_mean_psnr_s42_s7']:.3f}")
for v, r in sorted(res['variants'].items(), key=lambda kv: -kv[1]['mean_psnr']):
    print(f"{v:8s} PSNR {r['mean_psnr']:.3f} SSIM {r['mean_ssim']:.3f} | -B2 {r['minus_B2_db']:+.3f} {['%+.2f' % x for x in r['minus_B2_ci']]} wins {r['minus_B2_wins']}/16 | -static {r['minus_static_db']:+.3f}")
print('SELECTED:', sel, '| fidelity', fid)
