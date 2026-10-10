#!/usr/bin/env python3
"""S143 analysis (frozen with PROTOCOL.md before any S143 score existed).
usage: analyze_s143.py <POOL.json> <WARP_SCORES.json> <gen scores (score_s140 output)> <POSE_ARMS.json> <out.json> [B=100000]"""
import json, sys
from pathlib import Path
import numpy as np

POOL, WS, GS, PA, OUT = [json.loads(Path(p).read_text()) if i < 4 else Path(p) for i, p in enumerate(sys.argv[1:6])]
B = int(sys.argv[6]) if len(sys.argv) > 6 else 100000
pair = {r['window_id']: r['pair'] for r in PA['rows']}
SEEDS = [3, 4, 5, 6]; F1, F2 = [0, 1], [2, 3]   # seed positions

# ---- tables (strict completeness) ----
wins = [w['window_id'] for w in POOL['windows']]
sets = {w['window_id']: w['sets'] for w in POOL['windows']}
gen = {}
for r in GS['runs'].values():
    wid, sid = r['ctx_key'].split('__', 1)
    assert (wid, sid, r['seed']) not in gen, ('duplicate', r['ctx_key'], r['seed'])
    gen[(wid, sid, r['seed'])] = (r['psnr_db'], r['ssim'])
cells = []   # (window index, set id, min rule)
QW, QWs, QG, SG = [], [], [], []
for wi, wid in enumerate(wins):
    for s in sets[wid]:
        ws = WS['windows'][wid]['sets'][s['set_id']]
        assert all((wid, s['set_id'], sd) in gen for sd in SEEDS), ('missing cells', wid, s['set_id'])
        cells.append((wi, s['set_id'], min(s['rules']), s['rules']))
        QW.append(ws['warp_psnr']); QWs.append(ws['warp_ssim'])
        QG.append([gen[(wid, s['set_id'], sd)][0] for sd in SEEDS]); SG.append([gen[(wid, s['set_id'], sd)][1] for sd in SEEDS])
assert len(gen) == 4 * len(cells), ('extra cells', len(gen), 4 * len(cells))
QW, QWs, QG, SG = map(np.array, (QW, QWs, QG, SG))
assert np.isfinite(QW).all() and np.isfinite(QG).all()
cw = np.array([c[0] for c in cells]); rule_min = np.array([c[2] for c in cells]); nW = len(wins)
idx = [np.where(cw == wi)[0] for wi in range(nW)]


def argmax_tie(vals, ids):  # max value, ties -> lowest rule index
    best = max(vals); return min((rule_min[i], i) for v, i in zip(vals, ids) if v == best)[1]


cW = [argmax_tie(list(QW[ii]), ii) for ii in idx]


def R_of(Q, cw_sel=cW):
    """Q: (n_cells, 4 seeds). Returns per-window R and per-window global-rule gap."""
    m1, m2 = Q[:, F1].mean(1), Q[:, F2].mean(1)
    r = np.empty(nW); g = np.empty(nW)
    cg1 = [argmax_tie(list(m1[ii]), ii) for ii in idx]; cg2 = [argmax_tie(list(m2[ii]), ii) for ii in idx]
    for wi in range(nW):
        r[wi] = 0.5 * ((m2[cg1[wi]] - m2[cw_sel[wi]]) + (m1[cg2[wi]] - m1[cw_sel[wi]]))
    # global rule: choose rule 1..6 by mean over windows on one fold, evaluate on the other
    def rule_cell(wi, rule): return next(i for i in idx[wi] if rule in cells[i][3])
    def best_rule(m): return max(range(1, 7), key=lambda ru: (np.mean([m[rule_cell(wi, ru)] for wi in range(nW)]), -ru))
    r1, r2 = best_rule(m1), best_rule(m2)
    for wi in range(nW):
        g[wi] = 0.5 * ((m2[cg1[wi]] - m2[rule_cell(wi, r1)]) + (m1[cg2[wi]] - m1[rule_cell(wi, r2)]))
    return r, g, (r1, r2)


def boot(v):
    rng = np.random.default_rng(0); b = [rng.choice(v, len(v)).mean() for _ in range(10000)]
    return [float(x) for x in np.percentile(b, [2.5, 97.5])]


Rw, Gw, rules_sel = R_of(QG)
res = {'n_windows': nW, 'n_unique_sets': len(cells), 'sets_per_window': [len(i) for i in idx]}
res['R_2seed_hindsight'] = {'mean': float(Rw.mean()), 'ci95': boot(Rw), 'per_window': Rw.tolist(),
                            'pair_means': {p: float(np.mean([Rw[i] for i, w in enumerate(wins) if pair[w] == p])) for p in sorted(set(pair.values()))}}
res['R_2seed_hindsight']['leave_one_pair_out'] = {p: float(np.mean([Rw[i] for i, w in enumerate(wins) if pair[w] != p])) for p in sorted(set(pair.values()))}
res['global_rule_gap'] = {'mean': float(Gw.mean()), 'ci95': boot(Gw), 'rules_selected_fold1_fold2': rules_sel}
spread = [QW[ii].max() - QW[ii].min() for ii in idx]
margin = [np.sort(QW[ii])[-1] - np.sort(QW[ii])[-2] for ii in idx]
res['warp_spread_mean'] = float(np.mean(spread)); res['warp_best_minus_second_mean'] = float(np.mean(margin))

# ---- frozen null simulations (equal means; selection re-run in every draw; c_W fixed) ----
E = QG - QG.mean(1, keepdims=True)          # (n_cells, 4) residuals
rng = np.random.default_rng(143); nulls = {}
for name in ('panel', 'indep'):
    Rn, Gn = np.empty(B), np.empty(B)
    for b in range(B):
        if name == 'panel':
            Z = rng.standard_normal((4, 4))                       # 4 simulated seeds x 4 factors
            Q = (E @ Z.T) / np.sqrt(3)                            # (n_cells, 4 simulated seeds)
        else:
            Q = np.empty_like(E)
            for ii in idx:
                Z = rng.standard_normal((4, 4)); Q[ii] = (E[ii] @ Z.T) / np.sqrt(3)
        r, g, _ = R_of(Q); Rn[b], Gn[b] = r.mean(), g.mean()
    nulls[name] = {'R_null95': float(np.percentile(Rn, 95)), 'R_null_mean': float(Rn.mean()), 'R_null_sd': float(Rn.std()),
                   'R_tail_p': float((1 + (Rn >= Rw.mean()).sum()) / (B + 1)),
                   'G_null95': float(np.percentile(Gn, 95)), 'G_tail_p': float((1 + (Gn >= Gw.mean()).sum()) / (B + 1))}
res['nulls'] = nulls
thr_R = max(0.20, nulls['panel']['R_null95'], nulls['indep']['R_null95'])
thr_G = max(0.20, nulls['panel']['G_null95'], nulls['indep']['G_null95'])
pm = res['R_2seed_hindsight']['pair_means']
res['decision'] = {
    'threshold_R': thr_R, 'a_R_above_threshold': bool(Rw.mean() >= thr_R), 'b_ci_lower_positive': bool(res['R_2seed_hindsight']['ci95'][0] > 0),
    'c_no_negative_pair_in_2_of_3': bool(sum(v < 0 for v in pm.values()) < 2), 'd_warp_spread_ge_1dB': bool(res['warp_spread_mean'] >= 1.0),
    'threshold_G': thr_G, 'window_specific_structure': bool(Gw.mean() >= thr_G and res['global_rule_gap']['ci95'][0] > 0)}
res['decision']['CLAIM_SHORTFALL'] = all(res['decision'][k] for k in ('a_R_above_threshold', 'b_ci_lower_positive', 'c_no_negative_pair_in_2_of_3', 'd_warp_spread_ge_1dB'))

# ---- descriptive ----
def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1]) if len(a) > 2 and ra.std() > 0 and rb.std() > 0 else None
sp = [spearman(QW[ii], QG[ii].mean(1)) for ii in idx]
res['spearman_QW_QG_within_window'] = {'mean': float(np.mean([s for s in sp if s is not None])), 'per_window': sp}
res['per_rule_means'] = {}
for ru in range(1, 7):
    ci = [next(i for i in idx[wi] if ru in cells[i][3]) for wi in range(nW)]
    res['per_rule_means'][ru] = {'Q_W': float(QW[ci].mean()), 'Q_G': float(QG[ci].mean()), 'SSIM_W': float(QWs[ci].mean()), 'SSIM_G': float(SG[ci].mean()),
                                 'times_warp_best': int(sum(cW[wi] == ci[wi] for wi in range(nW)))}
res['ssim_at_psnr_selected'] = {'gen_ssim_at_cW_mean': float(np.mean([SG[cW[wi]].mean() for wi in range(nW)]))}
Rs, _, _ = R_of(SG); res['R_ssim_reselected_exploratory'] = {'mean': float(Rs.mean()), 'ci95': boot(Rs)}
res['copy_nearest'] = {'whole_bank_mean': float(np.mean([WS['windows'][w]['copy_bank_psnr'] for w in wins])),
                       'per_rule_set_mean': {ru: float(np.mean([WS['windows'][wins[wi]]['sets'][cells[next(i for i in idx[wi] if ru in cells[i][3])][1]]['copy_set_psnr'] for wi in range(nW)])) for ru in range(1, 7)}}
OUT.write_text(json.dumps(res, indent=1) + '\n')
print(json.dumps({k: res[k] for k in ('R_2seed_hindsight', 'global_rule_gap', 'nulls', 'decision', 'warp_spread_mean', 'spearman_QW_QG_within_window')}, indent=1, default=str)[:4000])
print('per-rule means', json.dumps(res['per_rule_means']))
