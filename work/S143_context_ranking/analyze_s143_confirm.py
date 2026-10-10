#!/usr/bin/env python3
"""S143 Amendment-1 confirmation: selections frozen on discovery seeds 3-6, evaluated on fresh seeds 42,7,1,2.
usage: analyze_s143_confirm.py <POOL.json> <WARP_SCORES.json> <discovery gen scores> <fresh gen scores> <POSE_ARMS.json> <out.json>"""
import json, sys
from pathlib import Path
import numpy as np
POOL, WS, GD, GF, PA = [json.loads(Path(p).read_text()) for p in sys.argv[1:6]]; OUT = Path(sys.argv[6])
pair = {r['window_id']: r['pair'] for r in PA['rows']}; DISC, FRESH = (3, 4, 5, 6), (42, 7, 1, 2)
def table(G, seeds):
    t = {}
    for r in G['runs'].values():
        wid, sid = r['ctx_key'].split('__', 1)
        if r['seed'] in seeds:
            assert (wid, sid, r['seed']) not in t; t[(wid, sid, r['seed'])] = r['psnr_db']
    return t
td, tf = table(GD, DISC), table(GF, FRESH)
rows, panel = [], {s: [] for s in FRESH}
for w in POOL['windows']:
    wid = w['window_id']; S = w['sets']; rmin = {s['set_id']: min(s['rules']) for s in S}
    assert all((wid, s['set_id'], sd) in td for s in S for sd in DISC) and all((wid, s['set_id'], sd) in tf for s in S for sd in FRESH)
    qw = {s['set_id']: WS['windows'][wid]['sets'][s['set_id']]['warp_psnr'] for s in S}
    qd = {s['set_id']: np.mean([td[(wid, s['set_id'], sd)] for sd in DISC]) for s in S}
    pick = lambda q: min((-q[k], rmin[k], k) for k in q)[2]
    cw, cg = pick(qw), pick(qd)
    rows.append({'window_id': wid, 'c_W': cw, 'c_G_disc': cg, 'sets': S,
                 'C': float(np.mean([tf[(wid, cg, sd)] - tf[(wid, cw, sd)] for sd in FRESH]))})
    for sd in FRESH: panel[sd].append(tf[(wid, cg, sd)] - tf[(wid, cw, sd)])
# discovery global rule
def set_of(row, rule): return next(s['set_id'] for s in row['sets'] if rule in s['rules'])
r_disc = max(range(1, 7), key=lambda ru: (np.mean([np.mean([td[(r['window_id'], set_of(r, ru), sd)] for sd in DISC]) for r in rows]), -ru))
for r in rows:
    r['Gc'] = float(np.mean([tf[(r['window_id'], r['c_G_disc'], sd)] - tf[(r['window_id'], set_of(r, r_disc), sd)] for sd in FRESH]))
def boot(v):
    rng = np.random.default_rng(0); b = [rng.choice(v, len(v)).mean() for _ in range(10000)]; return [float(x) for x in np.percentile(b, [2.5, 97.5])]
C = np.array([r['C'] for r in rows]); Gc = np.array([r['Gc'] for r in rows])
pm = {p: float(np.mean([r['C'] for r in rows if pair[r['window_id']] == p])) for p in sorted(set(pair.values()))}
seed_means = {sd: float(np.mean(v)) for sd, v in panel.items()}
res = {'C': {'mean': float(C.mean()), 'ci95': boot(C), 'pair_means': pm, 'fresh_seed_panel_means': seed_means},
       'window_specific_vs_disc_rule': {'rule': r_disc, 'mean': float(Gc.mean()), 'ci95': boot(Gc)},
       'frac_windows_cG_equals_cW': float(np.mean([r['c_W'] == r['c_G_disc'] for r in rows])), 'rows': rows}
res['CONFIRMED'] = bool(C.mean() >= 0.20 and res['C']['ci95'][0] > 0 and sum(v > 0 for v in seed_means.values()) >= 3 and sum(v < 0 for v in pm.values()) < 2)
OUT.write_text(json.dumps(res, indent=1, default=str) + '\n')
print(json.dumps({k: v for k, v in res.items() if k != 'rows'}, indent=1, default=str))
