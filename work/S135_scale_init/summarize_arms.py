#!/usr/bin/env python3
"""S135: summarize CPU stage-1 arms (pixel-aligned depth ratio vs dataset depth). usage: summarize_arms.py ARM_*.json"""
import json, sys
import numpy as np
arms = {}
for p in sys.argv[1:]:
    rows = json.load(open(p))['rows']; name = p.split('ARM_')[-1][:-5]
    arms[name] = {(r['scene'], r['window_start']): r for r in rows}
keys = sorted(set.intersection(*[set(a) for a in arms.values()]))
print(f"{'window':12s}" + ''.join(f'{n:>14s}' for n in arms))
for k in keys:
    print(f"{k[0][-2:]} w{k[1]:<8d}" + ''.join(f"{arms[n][k]['pix_ratio_median']:14.3f}" for n in arms))
print('\nsummary (pixel-aligned depth ratio, median over 5 bank frames per window)')
for n, a in arms.items():
    r = np.array([a[k]['pix_ratio_median'] for k in keys]); c = np.array([a[k]['pix_corr_median'] for k in keys])
    print(f"{n:14s} n={len(r):2d} in[0.5,2]={int(((r>=.5)&(r<=2)).sum()):2d} in[0.8,1.25]={int(((r>=.8)&(r<=1.25)).sum()):2d} "
          f">10={int((r>10).sum())} median_ratio={np.median(r):.3f} median|log r|={np.median(np.abs(np.log(r))):.3f} median_corr={np.median(c):.3f}")
