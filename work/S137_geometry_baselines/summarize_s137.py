#!/usr/bin/env python3
"""S137 summary: B0/B1 (S137a), B2 (orig/fix/kps) vs VMem static. Window-cluster bootstrap CIs (10k, rng 0).

usage: summarize_s137.py <BASELINES_gtdepth.json> <B2_orig.json> <B2_fix.json> <B2_kps.json> <out.json> [<S136_SCORES...>]
Without S136 scores the VMem reference is C9 (H800, 2 seeds). With them, it is the S136 8-seed static mean per window.
"""
import json, sys
from pathlib import Path
import numpy as np

A, B2o, B2f, B2k, OUT = map(Path, sys.argv[1:6]); S136 = [Path(p) for p in sys.argv[6:]]
base = {(r['scene'], r['window_start']): r for r in json.loads(A.read_text())['windows']}
b2 = {n: {(r['scene'], r['window_start']): r['b2_psnr'] for r in json.loads(p.read_text())['rows']}
      for n, p in (('b2_orig', B2o), ('b2_fix', B2f), ('b2_kps', B2k))}
keys = sorted(base)
table = {k: {'copy': base[k]['copy_psnr'], 'warp_gtdepth': base[k]['warp_psnr'], **{n: b2[n][k] for n in b2},
             'vmem_static_native_c9': base[k]['vmem_static_native'], 'vmem_static_gl_c9': base[k]['vmem_static_gl']}
         for k in keys}
if S136:
    runs = {}
    for p in S136: runs.update(json.loads(p.read_text())['runs'])
    for conv in ('native', 'gl'):
        for k in keys:
            key = f"{k[0]}__w{k[1]:04d}__{conv}__" + '-'.join(str(k[1] + o) for o in (0, 15, 30, 45))
            v = [r['aggregate']['psnr_db'] for r in runs.values() if r['ctx_key'] == key]
            table[k][f'vmem_static_{conv}_s136'] = float(np.mean(v)) if v else None
            table[k][f'n_seeds_{conv}_s136'] = len(v)


def diff(a, b):
    d = np.array([table[k][a] - table[k][b] for k in keys if table[k].get(a) is not None and table[k].get(b) is not None])
    rng = np.random.default_rng(0); boot = [rng.choice(d, len(d)).mean() for _ in range(10000)]
    return {'a': a, 'b': b, 'n': len(d), 'mean_db': float(d.mean()), 'ci95': [float(x) for x in np.percentile(boot, [2.5, 97.5])],
            'a_wins': int((d > 0).sum())}


ref = [c for c in ('vmem_static_native_s136', 'vmem_static_gl_s136') if any(table[k].get(c) is not None for k in keys)] or \
      ['vmem_static_native_c9', 'vmem_static_gl_c9']
res = {'means': {c: float(np.mean([table[k][c] for k in keys if table[k].get(c) is not None])) for c in next(iter(table.values())) if not c.startswith('n_')},
       'contrasts': [diff('b2_kps', 'b2_fix'), diff('b2_fix', 'b2_orig'), diff('b2_kps', 'b2_orig')] +
                    [diff(m, r) for m in ('copy', 'b2_kps', 'warp_gtdepth') for r in ref],
       'windows': {f'{k[0]}_w{k[1]}': table[k] for k in keys}}
OUT.write_text(json.dumps(res, indent=1) + '\n')
for c, v in res['means'].items(): print(f'{c:26s} {v:6.2f} dB')
for c in res['contrasts']:
    print(f"{c['a']:>14s} - {c['b']:<26s} {c['mean_db']:+.2f} dB CI[{c['ci95'][0]:+.2f},{c['ci95'][1]:+.2f}] wins {c['a_wins']}/{c['n']}")
