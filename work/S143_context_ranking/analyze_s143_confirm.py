#!/usr/bin/env python3
"""S143 fresh-seed block (Amendment 1, corrected by Amendment 2 / codex R261). Descriptive, not formal confirmation.
Selections frozen from discovery seeds 3-6 (c_W from warps; c_G_disc = argmax of the 4-seed discovery mean; r_disc = best
discovery rule), saved with input hashes BEFORE any fresh contrast is computed; then evaluated on fresh seeds 42,7,1,2
with seed panels as replication units.
usage: analyze_s143_confirm.py <POOL.json> <WARP_SCORES.json> <discovery scores> <fresh scores> <POSE_ARMS.json> <out.json>"""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
paths = [Path(p) for p in sys.argv[1:6]]; OUT = Path(sys.argv[6])
POOL, WS, GD, GF, PA = [json.loads(p.read_text()) for p in paths]
pair = {r['window_id']: r['pair'] for r in PA['rows']}; DISC, FRESH = (3, 4, 5, 6), (42, 7, 1, 2)


class InvalidAssay(Exception):
    pass


def check(cond, msg):
    if not cond: raise InvalidAssay(msg)


def table(G, seeds, name):
    expected = {(w['window_id'], s['set_id'], sd) for w in POOL['windows'] for s in w['sets'] for sd in seeds}
    t = {}
    for r in G['runs'].values():
        wid, sid = r['ctx_key'].split('__', 1); k = (wid, sid, r['seed'])
        check(k not in t, f'{name}: duplicate cell {k}')
        check(k in expected, f'{name}: unexpected cell {k}')
        check(r['psnr_db'] is not None and math.isfinite(r['psnr_db']), f'{name}: non-finite {k}')
        t[k] = r['psnr_db']
    check(set(t) == expected, f'{name}: missing {len(expected - set(t))} cells')
    return t


try:
    wids = [w['window_id'] for w in POOL['windows']]; check(len(set(wids)) == len(wids) == 24, 'window ids')
    for w in POOL['windows']:
        for ru in range(1, 7):
            check(sum(ru in s['rules'] for s in w['sets']) == 1, f"rule {ru} not mapped to exactly one set in {w['window_id']}")
        for s in w['sets']:
            check(math.isfinite(WS['windows'][w['window_id']]['sets'][s['set_id']]['warp_psnr']), 'non-finite Q_W')
    td, tf = table(GD, DISC, 'discovery'), table(GF, FRESH, 'fresh')
except InvalidAssay as e:
    OUT.write_text(json.dumps({'status': 'INVALID_ASSAY', 'reason': str(e)}, indent=1) + '\n'); print('INVALID_ASSAY:', e); sys.exit(2)

# ---- 1. frozen selections from discovery only (saved before any fresh contrast) ----
sel = {}
for w in POOL['windows']:
    wid = w['window_id']; S = w['sets']; rmin = {s['set_id']: min(s['rules']) for s in S}
    qw = {s['set_id']: WS['windows'][wid]['sets'][s['set_id']]['warp_psnr'] for s in S}
    qd = {s['set_id']: float(np.mean([td[(wid, s['set_id'], sd)] for sd in DISC])) for s in S}
    pick = lambda q: min((-q[k], rmin[k], k) for k in q)[2]
    sel[wid] = {'c_W': pick(qw), 'c_G_disc': pick(qd), 'rule_to_set': {ru: next(s['set_id'] for s in S if ru in s['rules']) for ru in range(1, 7)}}
r_disc = max(range(1, 7), key=lambda ru: (np.mean([np.mean([td[(w, sel[w]['rule_to_set'][ru], sd)] for sd in DISC]) for w in wids]), -ru))
frozen = {'selections': sel, 'r_disc': r_disc, 'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths[:3]}}
(OUT.parent / (OUT.stem + '_FROZEN_SELECTIONS.json')).write_text(json.dumps(frozen, indent=1) + '\n')

# ---- 2. fresh evaluation: seed panels are the replication unit ----
def block(alt_of):
    per_seed = {sd: float(np.mean([tf[(w, sel[w]['c_G_disc'], sd)] - tf[(w, alt_of(w), sd)] for w in wids])) for sd in FRESH}
    per_win = np.array([np.mean([tf[(w, sel[w]['c_G_disc'], sd)] - tf[(w, alt_of(w), sd)] for sd in FRESH]) for w in wids])
    pm = {p: float(np.mean([per_win[i] for i, w in enumerate(wids) if pair[w] == p])) for p in sorted(set(pair.values()))}
    rng = np.random.default_rng(0); b = [rng.choice(per_win, len(per_win)).mean() for _ in range(10000)]
    m = float(np.mean(list(per_seed.values())))
    gate = bool(m >= 0.20 and sum(v > 0 for v in per_seed.values()) >= 3 and sum(v < 0 for v in pm.values()) < 2)
    return {'mean': m, 'seed_panel_means': per_seed, 'pair_means': pm,
            'window_bootstrap_ci95_descriptive': [float(x) for x in np.percentile(b, [2.5, 97.5])], 'gate_descriptive': gate}
def block_rule(ru, alt_of):   # Amendment 3: like block(), with the frozen rule's set in place of c_G_disc
    per_seed = {sd: float(np.mean([tf[(w, sel[w]['rule_to_set'][ru], sd)] - tf[(w, alt_of(w), sd)] for w in wids])) for sd in FRESH}
    per_win = np.array([np.mean([tf[(w, sel[w]['rule_to_set'][ru], sd)] - tf[(w, alt_of(w), sd)] for sd in FRESH]) for w in wids])
    pm = {p: float(np.mean([per_win[i] for i, w in enumerate(wids) if pair[w] == p])) for p in sorted(set(pair.values()))}
    rng = np.random.default_rng(0); b = [rng.choice(per_win, len(per_win)).mean() for _ in range(10000)]
    m = float(np.mean(list(per_seed.values())))
    return {'mean': m, 'seed_panel_means': per_seed, 'pair_means': pm, 'wins': int((per_win > 0).sum()),
            'window_bootstrap_ci95_descriptive': [float(x) for x in np.percentile(b, [2.5, 97.5])],
            'gate_descriptive': bool(m >= 0.20 and sum(v > 0 for v in per_seed.values()) >= 3 and sum(v < 0 for v in pm.values()) < 2)}
res = {'status': 'VALID', 'note': 'descriptive fresh-seed block; seed panels are the unit; no formal seed-level inference',
       'C_frozen4_discovery': block(lambda w: sel[w]['c_W']),
       'local_vs_global': dict(block(lambda w: sel[w]['rule_to_set'][r_disc]), rule=r_disc),
       'frac_windows_cG_equals_cW': float(np.mean([sel[w]['c_W'] == sel[w]['c_G_disc'] for w in wids]))}
# Amendment 3: r_disc versus rule 3 (mem_vmem), c_W, rule 1 (static) on fresh seeds (descriptive)
res['rule_contrasts'] = {f'r_disc(rule {r_disc}) - rule 3 (mem_vmem)': block_rule(r_disc, lambda w: sel[w]['rule_to_set'][3]),
                         f'r_disc(rule {r_disc}) - c_W': block_rule(r_disc, lambda w: sel[w]['c_W']),
                         f'r_disc(rule {r_disc}) - rule 1 (static)': block_rule(r_disc, lambda w: sel[w]['rule_to_set'][1])}
res['FRESH_SEED_GATE'] = res['C_frozen4_discovery']['gate_descriptive']
res['FRESH_SEED_GATE_LOCAL'] = res['local_vs_global']['gate_descriptive']
OUT.write_text(json.dumps(res, indent=1, default=str) + '\n')
print(json.dumps(res, indent=1, default=str))
