#!/usr/bin/env python3
"""S146 analysis (frozen with the protocol; R265 §6-7). Subcommands (separate invocations enforce sealing):
  primary  <POOL.json> <gen scores (any seeds; evaluation seeds used)> <out.json>
  seal     <POOL.json> <WARP_SCORES.json> <gen scores> <out FROZEN.json>     (reads ONLY discovery seeds 3-6)
  evaluate <POOL.json> <FROZEN.json> <gen scores> <out.json>                (sealed selectors on evaluation seeds)
  prep143  <POOL.json> <WARP_SCORES.json> <gen scores> <out_dir>            (inputs for analyze_s143.py on rules 1-6, seeds 3-6)
Primary: d(r,s) = mean_w[PSNR(rule 4) - PSNR(rule 3 sorted)], evaluation seeds 42,7,1,2; pass iff D >= 0.20, all D_r > 0,
>= 3 of 4 D_s > 0. Same gate vs native-order rule 3 for the broader wording."""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
J = lambda p: json.loads(Path(p).read_text())
ROOMS = ['apt1_kitchen', 'apt2_luke', 'office2_5a']; EVAL, DISC = (42, 7, 1, 2), (3, 4, 5, 6)


def table(G, seeds, POOL, metric='psnr_db', ignore_sets=()):
    expected = {(w['window_id'], s['set_id'], sd) for w in POOL['windows'] for s in w['sets'] for sd in seeds}
    t = {}
    for r in G['runs'].values():
        if r['seed'] not in seeds: continue
        wid, sid = r['ctx_key'].split('__', 1); k = (wid, sid, r['seed'])
        if sid in ignore_sets: continue
        assert k in expected and k not in t, ('unexpected/duplicate', k)
        v = r[metric]; assert v is not None and math.isfinite(v), k; t[k] = v
    assert set(t) == expected, ('missing', len(expected - set(t)))
    return t


def pkg(w, rule=None, native=False):
    if native:
        for s in w['sets']:
            if s.get('native_order_of_rule') == 3: return s['set_id']
        return next(s['set_id'] for s in w['sets'] if 3 in s['rules'] and s.get('also_native_order'))
    return next(s['set_id'] for s in w['sets'] if rule in s['rules'])


def matrix(P, t, a_of, b_of, seeds):
    M = {r: {sd: float(np.mean([t[(w['window_id'], a_of(w), sd)] - t[(w['window_id'], b_of(w), sd)] for w in P['windows'] if w['room'] == r]))
             for sd in seeds} for r in ROOMS}
    D_r = {r: float(np.mean(list(M[r].values()))) for r in ROOMS}; D_s = {sd: float(np.mean([M[r][sd] for r in ROOMS])) for sd in seeds}
    D = float(np.mean(list(D_r.values())))
    per_win = [np.mean([t[(w['window_id'], a_of(w), sd)] - t[(w['window_id'], b_of(w), sd)] for sd in seeds]) for w in P['windows']]
    rng = np.random.default_rng(0); b = [rng.choice(per_win, len(per_win)).mean() for _ in range(10000)]
    return {'D': D, 'D_room': D_r, 'D_seed': {str(k): v for k, v in D_s.items()}, 'matrix': {r: {str(k): v for k, v in M[r].items()} for r in ROOMS},
            'leave_one_room_out': {r: float(np.mean([D_r[x] for x in ROOMS if x != r])) for r in ROOMS},
            'window_bootstrap_ci95_descriptive': [float(x) for x in np.percentile(b, [2.5, 97.5])],
            'gate': bool(D >= 0.20 and all(v > 0 for v in D_r.values()) and sum(v > 0 for v in D_s.values()) >= 3)}


mode = sys.argv[1]
if mode == 'primary':
    P, G, OUT = J(sys.argv[2]), J(sys.argv[3]), Path(sys.argv[4])
    res = {}
    for metric in ('psnr_db', 'ssim'):
        t = table(G, EVAL, P, metric); blk = {}
        blk['PRIMARY nearest4 - mem_vmem(sorted)'] = matrix(P, t, lambda w: pkg(w, 4), lambda w: pkg(w, 3), EVAL)
        blk['nearest4 - mem_vmem(native order)'] = matrix(P, t, lambda w: pkg(w, 4), lambda w: pkg(w, native=True), EVAL)
        blk['nearest4 - static'] = matrix(P, t, lambda w: pkg(w, 4), lambda w: pkg(w, 1), EVAL)
        blk['nearest4 - coverage'] = matrix(P, t, lambda w: pkg(w, 4), lambda w: pkg(w, 5), EVAL)
        blk['coverage - mem_vmem(sorted)'] = matrix(P, t, lambda w: pkg(w, 5), lambda w: pkg(w, 3), EVAL)
        blk['mem_vmem native - sorted'] = matrix(P, t, lambda w: pkg(w, native=True), lambda w: pkg(w, 3), EVAL)
        means = {}
        for w in P['windows']:
            for s in w['sets']:
                for ru in (s['rules'] or ['nat3']):
                    means.setdefault(str(ru), []).append(np.mean([t[(w['window_id'], s['set_id'], sd)] for sd in EVAL]))
        blk['per_rule_means'] = {k: float(np.mean(v)) for k, v in means.items()}
        res[metric] = blk
    p, ps = res['psnr_db']['PRIMARY nearest4 - mem_vmem(sorted)'], res['ssim']['PRIMARY nearest4 - mem_vmem(sorted)']
    res['DECISION'] = {'fixed_panel_pass_sorted': p['gate'], 'fixed_panel_pass_native': res['psnr_db']['nearest4 - mem_vmem(native order)']['gate'],
                       'ssim_quality_block': bool(ps['D'] < -0.01),
                       'history_fraction_mem_vmem': float(np.mean([w['stepA']['frac_history'] for w in P['windows']]))}
    OUT.write_text(json.dumps(res, indent=1) + '\n')
    for k in ('PRIMARY nearest4 - mem_vmem(sorted)', 'nearest4 - mem_vmem(native order)', 'nearest4 - static', 'nearest4 - coverage', 'coverage - mem_vmem(sorted)', 'mem_vmem native - sorted'):
        b = res['psnr_db'][k]; print(f"{k:38s} D {b['D']:+.3f} rooms {({r: round(v, 3) for r, v in b['D_room'].items()})} seeds {({s: round(v, 3) for s, v in b['D_seed'].items()})} gate {b['gate']} | SSIM {res['ssim'][k]['D']:+.4f}")
    print('per-rule PSNR', {k: round(v, 3) for k, v in res['psnr_db']['per_rule_means'].items()}); print('DECISION', res['DECISION'])
elif mode == 'seal':
    P, WS, G, OUT = J(sys.argv[2]), J(sys.argv[3]), J(sys.argv[4]), Path(sys.argv[5])
    td = table(G, DISC, {'windows': [dict(w, sets=[s for s in w['sets'] if s['rules']]) for w in P['windows']]}, ignore_sets=('nat3',))
    sel = {}
    for w in P['windows']:
        S = [s for s in w['sets'] if s['rules']]; rmin = {s['set_id']: min(s['rules']) for s in S}
        qw = {s['set_id']: WS['windows'][w['window_id']]['sets'][s['set_id']]['warp_psnr'] for s in S}
        qd = {s['set_id']: float(np.mean([td[(w['window_id'], s['set_id'], sd)] for sd in DISC])) for s in S}
        pick = lambda q: min((-q[k], rmin[k], k) for k in q)[2]
        sel[w['window_id']] = {'c_W': pick(qw), 'c_G_disc': pick(qd), 'rule_to_set': {str(ru): pkg(w, ru) for ru in range(1, 7)}}
    r_disc = max(range(1, 7), key=lambda ru: (np.mean([np.mean([td[(w, sel[w]['rule_to_set'][str(ru)], sd)] for sd in DISC]) for w in sel]), -ru))
    frozen = {'selections': sel, 'r_disc': r_disc, 'input_sha256': {Path(a).name: hashlib.sha256(Path(a).read_bytes()).hexdigest() for a in sys.argv[2:5]}}
    OUT.write_text(json.dumps(frozen, indent=1) + '\n'); print('sealed; r_disc', r_disc, 'cG==cW', sum(v['c_W'] == v['c_G_disc'] for v in sel.values()), '/', len(sel))
elif mode == 'evaluate':
    P, FR, G, OUT = J(sys.argv[2]), J(sys.argv[3]), J(sys.argv[4]), Path(sys.argv[5])
    t = table(G, EVAL, P); sel = FR['selections']; rd = str(FR['r_disc'])
    res = {'C_frozen4_discovery (c_G_disc - c_W)': matrix(P, t, lambda w: sel[w['window_id']]['c_G_disc'], lambda w: sel[w['window_id']]['c_W'], EVAL),
           'local_vs_global (c_G_disc - r_disc)': matrix(P, t, lambda w: sel[w['window_id']]['c_G_disc'], lambda w: sel[w['window_id']]['rule_to_set'][rd], EVAL),
           'r_disc': FR['r_disc']}
    OUT.write_text(json.dumps(res, indent=1) + '\n')
    for k in list(res)[:2]: print(k, round(res[k]['D'], 3), {r: round(v, 3) for r, v in res[k]['D_room'].items()}, 'gate(descriptive)', res[k]['gate'])
elif mode == 'prep143':
    P, WS, G, OD = J(sys.argv[2]), J(sys.argv[3]), J(sys.argv[4]), Path(sys.argv[5]); OD.mkdir(parents=True, exist_ok=True)
    pool = {'windows': [{'window_id': w['window_id'], 'sets': [s for s in w['sets'] if s['rules']]} for w in P['windows']]}
    keep = {(w['window_id'], s['set_id']) for w in pool['windows'] for s in w['sets']}
    gen = {'runs': {k: r for k, r in G['runs'].items() if r['seed'] in DISC and tuple(r['ctx_key'].split('__', 1)) in keep}}
    pa = {'rows': [{'window_id': w['window_id'], 'pair': w['room'], 'history_favourable': w['history_favourable']} for w in P['windows']]}
    for name, obj in (('POOL143.json', pool), ('GEN143.json', gen), ('PAIRS143.json', pa), ('WARPS143.json', WS)):
        (OD / name).write_text(json.dumps(obj) + '\n')
    print('prepared', len(gen['runs']), 'discovery runs')
