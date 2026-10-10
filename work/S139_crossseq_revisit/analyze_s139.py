#!/usr/bin/env python3
"""S139 analysis (PROTOCOL.md). usage: analyze_s139.py <plan.json> <POSE_ARMS.json> <out.json> <scores.json> [...]
Unit: window mean over seeds present for both arms. Window-cluster bootstrap 95% CI (10k, rng 0); pair-cluster bootstrap
(descriptive, 3 clusters); verdict ±0.2 dB rule; strata by the pre-registered pose-only history_favourable flag.
"""
import json, sys
from pathlib import Path
import numpy as np

plan = json.loads(Path(sys.argv[1]).read_text()); pose = {r['window_id']: r for r in json.loads(Path(sys.argv[2]).read_text())['rows']}
OUT = Path(sys.argv[3]); runs = {}
for p in sys.argv[4:]: runs.update(json.loads(Path(p).read_text())['runs'])
bykey = {}
for r in runs.values(): bykey.setdefault(r['ctx_key'], {})[r['seed']] = r['aggregate']['psnr_db']
psnr = {}
for c in plan['contexts']:
    for a in c['arms']: psnr[(c['window_id'], a)] = bykey.get(c['ctx_key'], {})
SITES = {'superpod_h800': {42, 7, 1, 2}, 'tacc_rtx3090': {3, 4, 5, 6}}


def diffs(a, b, wins=None, seeds=None):
    out = {}
    for (w, x), A in psnr.items():
        if x != a or (wins is not None and w not in wins): continue
        B = psnr.get((w, b)); ss = sorted(set(A) & set(B or {}) & (seeds or set(A)))
        if B and ss: out[w] = float(np.mean([A[s] - B[s] for s in ss]))
    return out


def summarise(d):
    if not d: return None
    v = np.array(list(d.values())); rng = np.random.default_rng(0)
    boot = [rng.choice(v, len(v)).mean() for _ in range(10000)]; lo, hi = np.percentile(boot, [2.5, 97.5]); m = float(v.mean())
    pairs = sorted({pose[w]['pair'] for w in d}); pm = {p: float(np.mean([d[w] for w in d if pose[w]['pair'] == p])) for p in pairs}
    pc = [np.mean([pm[p] for p in rng.choice(pairs, len(pairs))]) for _ in range(10000)]
    verdict = ('IMPROVES' if m >= 0.2 and lo > 0 else 'WORSENS' if m <= -0.2 and hi < 0 else
               'NO_MATERIAL_CHANGE' if abs(m) < 0.2 and lo <= 0 <= hi else 'INCONCLUSIVE')
    return {'n_windows': len(v), 'mean_db': m, 'ci95_window': [float(lo), float(hi)],
            'ci95_pair_cluster': [float(x) for x in np.percentile(pc, [2.5, 97.5])], 'windows_positive': int((v > 0).sum()),
            'per_pair': pm, 'verdict': verdict}


HF = {w for w, r in pose.items() if r['history_favourable']}; RF = set(pose) - HF
res = {'n_history_favourable': len(HF), 'contrasts': {}}
for name, (a, b) in {'PRIMARY_mem_vmem_vs_static_recent': ('mem_vmem', 'static_recent'),
                     'mem_vmem_vs_mem_pose': ('mem_vmem', 'mem_pose'),
                     'mem_pose_vs_static_recent': ('mem_pose', 'static_recent')}.items():
    c = summarise(diffs(a, b))
    if c:
        c['history_favourable'] = summarise(diffs(a, b, HF)); c['recent_favourable'] = summarise(diffs(a, b, RF))
        if c['history_favourable'] and c['recent_favourable']:
            c['stratum_difference_db'] = c['history_favourable']['mean_db'] - c['recent_favourable']['mean_db']
        c['per_site'] = {s: (lambda z: z and {k: z[k] for k in ('mean_db', 'ci95_window', 'windows_positive')})(summarise(diffs(a, b, seeds=ss)))
                         for s, ss in SITES.items()}
    res['contrasts'][name] = c
res['arm_means_db'] = {a: float(np.mean([v for (w, x), d in psnr.items() if x == a for v in d.values()]))
                       for a in sorted({x for _, x in psnr}) if any(psnr[k] for k in psnr if k[1] == a)}
res['seeds_per_window'] = sorted({len(d) for d in psnr.values()})
OUT.write_text(json.dumps(res, indent=1) + '\n')
print(json.dumps(res['arm_means_db']), 'seeds', res['seeds_per_window'], 'HF', len(HF))
for n, c in res['contrasts'].items():
    if not c: continue
    print(f"{n:36s} {c['mean_db']:+.3f} CI[{c['ci95_window'][0]:+.3f},{c['ci95_window'][1]:+.3f}] pairCI[{c['ci95_pair_cluster'][0]:+.2f},{c['ci95_pair_cluster'][1]:+.2f}] "
          f"pos {c['windows_positive']}/{c['n_windows']} {c['verdict']} | HF {c['history_favourable'] and round(c['history_favourable']['mean_db'],3)} "
          f"RF {c['recent_favourable'] and round(c['recent_favourable']['mean_db'],3)} | pairs {({k: round(v,2) for k,v in c['per_pair'].items()})}")
